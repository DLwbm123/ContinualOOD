"""Bounded real-data run: P2 gates P3; exits before stream/probe or memory."""
import json
import os
from pathlib import Path
import sys
import time
import traceback

import nibabel as nib
import numpy as np
import torch

from native_adapter import make_pipeline,run_slice,seed_all
from volume_io import load_study,rgb_slice,save_native
from reference_methods import local_controls,research_candidates


def write(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2,default=str,allow_nan=False));tmp.replace(path)


def main():
    root=Path(os.environ['COOD_ROOT']);out=root/'outputs/p1_p3_v1';out.mkdir(parents=True,exist_ok=True)
    status={'stop_after':'P3','stage':'P2','completed_studies':[],'failures':[]}
    write(out/'status.json',status)
    records=[json.loads(x) for x in (root/'manifests_local/runtime_dev.jsonl').read_text().splitlines()]
    smoke=json.loads((root/'manifests_local/smoke_ids.json').read_text())
    by_id={r['study_uid']:r for r in records}
    pipeline,plan=make_pipeline(out)
    assert not pipeline.config.mitigation.enabled
    model=pipeline.segmenter.model
    # Warm every fixed prompt before taking the immutable network-state snapshot.
    image,volume,spacing=load_study(by_id[smoke[0]])
    run_slice(pipeline,plan,rgb_slice(volume,len(volume)//2),spacing[1:],out/'warmup',42)
    frozen={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
    def check_frozen():
        changed=[k for k,v in model.state_dict().items() if not torch.equal(v.detach().cpu(),frozen[k])]
        if changed:raise RuntimeError('Network state changed: '+repr(changed))
        return {'state_items':len(frozen),'changed':[]}
    def scan(record):
        uid=record['study_uid'];folder=out/uid;folder.mkdir(exist_ok=True)
        image,volume,spacing=load_study(record)
        probability=np.empty(volume.shape,np.float32);anchor=np.zeros(volume.shape,np.uint8);final=np.zeros(volume.shape,np.uint8)
        metas=[];start=time.monotonic()
        for z in range(len(volume)):
            result,meta=run_slice(pipeline,plan,rgb_slice(volume,z),spacing[1:],folder/f'z{z:04d}',42+z)
            probability[z]=result.probability_maps['bladder tumor'];final[z]=result.final_mask
            if not meta['anchor_fallback']:anchor[z]=result.anchor_masks.get('urinary bladder',np.zeros(volume.shape[1:],np.uint8))
            metas.append(meta)
        save_native(final,image,folder/'B0_R2_NATIVE.nii.gz')
        np.savez_compressed(folder/'volume.npz',probability=probability,anchor=anchor,native=final)
        write(folder/'scan.json',{'slices':len(volume),'seconds':time.monotonic()-start,'trace':metas})
        status['completed_studies'].append(uid);write(out/'status.json',status)
        print(json.dumps({'event':'scan_completed','study_uid':uid,'slices':len(volume),'seconds':time.monotonic()-start}),flush=True)
    for uid in smoke:
        try:scan(by_id[uid])
        except Exception as exc:
            status['failures'].append({'study_uid':uid,'stage':'smoke','error':repr(exc)});write(out/'status.json',status);raise
    parity=[]
    # Fixed central indices chosen without consulting labels or model outputs.
    cases=[]
    for uid in smoke:
        image,volume,spacing=load_study(by_id[uid])
        zs=np.linspace(0,len(volume)-1,4,dtype=int)
        cases.extend((uid,int(z)) for z in zs)
    for i,(uid,z) in enumerate(cases[:10]):
        image,volume,spacing=load_study(by_id[uid]);rgb=rgb_slice(volume,z)
        a,_=run_slice(pipeline,plan,rgb,spacing[1:],out/'parity'/f'{i}_native',4242+i,False)
        b,meta=run_slice(pipeline,plan,rgb,spacing[1:],out/'parity'/f'{i}_trace',4242+i,True)
        stats=lambda result:[(r.candidate.label,r.test_statistic,r.p_value,r.q_value) for r in result.candidate_results]
        probability_delta=float(np.max(np.abs(a.probability_maps['bladder tumor']-b.probability_maps['bladder tumor'])))
        from tta_pipeline.postprocessing import extract_candidates
        ca=extract_candidates(a.probability_maps,min_pixels=1,threshold=.4);cb=extract_candidates(b.probability_maps,min_pixels=1,threshold=.4)
        same_candidates=len(ca)==len(cb) and all(np.array_equal(x.mask,y.mask) for x,y in zip(ca,cb))
        item=dict(index=i,probability_max_abs=probability_delta,mask_equal=bool(np.array_equal(a.final_mask,b.final_mask)),retained_statistics_equal=stats(a)==stats(b),all_candidates_equal=same_candidates)
        parity.append(item);write(out/'parity.json',parity)
        assert probability_delta==0 and item['mask_equal'] and item['retained_statistics_equal'] and same_candidates,'Parity failure'
    write(out/'network_invariance.json',check_frozen())
    status['P2_passed']=True;status['stage']='P3';write(out/'status.json',status)
    print('P2_PASSED',flush=True)
    for record in records:
        uid=record['study_uid']
        try:
            if uid not in smoke:scan(record)
            folder=out/uid;image,volume,spacing=load_study(record)
            with np.load(folder/'volume.npz') as cached:
                probability=cached['probability'];anchor=cached['anchor'];native=cached['native']
            meta=json.loads((folder/'scan.json').read_text())
            controls={v:np.zeros(volume.shape,np.uint8) for v in ['all_candidates','physical_margin','compartment']};control_meta=[]
            for z in range(len(volume)):
                masks,trace=local_controls(rgb_slice(volume,z),probability[z],anchor[z],spacing[1:],meta['trace'][z]['anchor_fallback'],pipeline.config.stats,native[z],42+z)
                for variant,mask in masks.items():controls[variant][z]=mask
                control_meta.append(trace)
            for variant,mask in controls.items():save_native(mask,image,folder/f'B1_{variant}.nii.gz')
            labels,c0,c1,candidates=research_candidates(volume,probability,anchor,spacing,uid)
            save_native(c0,image,folder/'C0_CONFIDENCE_ONLY.nii.gz');save_native(c1,image,folder/'C1_CURRENT_CALIBRATION.nii.gz')
            np.savez_compressed(folder/'research_candidates.npz',labels=labels)
            write(folder/'research_candidates.json',candidates);write(folder/'local_controls.json',control_meta)
        except Exception as exc:
            status['failures'].append({'study_uid':uid,'stage':'P3','error':repr(exc)});write(out/'status.json',status)
            traceback.print_exc()
    write(out/'network_invariance_final.json',check_frozen())
    status['stage']='P3_INFERENCE_COMPLETE';status['peak_gpu_bytes']=torch.cuda.max_memory_allocated();write(out/'status.json',status)
    print('P3_INFERENCE_COMPLETE',flush=True)


if __name__=='__main__':
    try:main()
    except Exception:
        root=Path(os.environ['COOD_ROOT'])/'outputs/p1_p3_v1'
        (root/'fatal_error.txt').write_text(traceback.format_exc());raise
