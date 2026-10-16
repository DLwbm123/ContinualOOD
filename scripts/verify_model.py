"""Load the locked native architecture, audit every checkpoint key, require CUDA."""
import json
import os
from pathlib import Path
import sys
import time

import torch


def load_verified():
    root = Path(os.environ['COOD_ROOT'])
    source = root/'repo/third_party/R2Seg'
    sys.path.insert(0, str(source))
    from modeling import build_model
    from modeling.BaseModel import BaseModel
    from utilities.arguments import load_opt_from_config_files
    from utilities.distributed import init_distributed
    from utilities.constants import BIOMED_CLASSES
    assert torch.cuda.is_available(), 'CUDA required; CPU fallback forbidden'
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    opt = init_distributed(load_opt_from_config_files([str(root/'models/biomedparse_v1/config.yaml')]))
    model = BaseModel(opt, build_model(opt))
    ckpt = torch.load(root/'models/biomedparse_v1/biomedparse_v1.pt', map_location='cpu', weights_only=True)
    state = model.model.state_dict()
    missing = sorted(set(state)-set(ckpt))
    unexpected = sorted(set(ckpt)-set(state))
    mismatched = {k: [list(state[k].shape), list(ckpt[k].shape)] for k in set(state)&set(ckpt) if state[k].shape != ckpt[k].shape}
    report = dict(missing=missing, unexpected=unexpected, shape_mismatch=mismatched,
                  model_keys=len(state), checkpoint_keys=len(ckpt),
                  matched_numel=sum(v.numel() for k,v in state.items() if k in ckpt and k not in mismatched),
                  total_numel=sum(v.numel() for v in state.values()), device='cuda:0', physical_gpu=os.environ.get('CUDA_VISIBLE_DEVICES'))
    (root/'private/model_load.json').write_text(json.dumps(report, indent=2))
    assert not missing and not mismatched, 'Checkpoint coverage failure; inspect model_load.json'
    model.model.load_state_dict({k:v for k,v in ckpt.items() if k in state}, strict=True)
    model.eval().requires_grad_(False).cuda()
    with torch.inference_mode():
        model.model.sem_seg_head.predictor.lang_encoder.get_text_embeddings(BIOMED_CLASSES+['background'], is_eval=True)
    assert all(p.device.type == 'cuda' and not p.requires_grad for p in model.parameters())
    report['loaded'] = True
    report['peak_gpu_bytes'] = torch.cuda.max_memory_allocated()
    (root/'private/model_load.json').write_text(json.dumps(report, indent=2))
    return model


if __name__ == '__main__':
    start = time.monotonic()
    load_verified()
    print(json.dumps({'model_loaded': True, 'seconds': time.monotonic()-start}), flush=True)
