"""Synthetic hardware/import check, never a medical inference result."""
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

import torch
import torchvision

assert Path(sys.prefix).resolve().is_relative_to(Path(os.environ["COOD_STORAGE_ROOT"]).resolve()), "Environment is off data disk"
assert torch.cuda.is_available(), "CUDA unavailable; CPU fallback forbidden"
assert torch.cuda.mem_get_info()[0] > 2 * 1024**3, "Less than 2 GiB free"
with torch.inference_mode():
    x = torch.arange(256, dtype=torch.float32, device="cuda").reshape(16, 16)
    assert torch.equal(x @ torch.eye(16, device="cuda"), x)
    image = torch.ones((1, 1, 16, 16), device="cuda")
    kernel = torch.ones((1, 1, 3, 3), device="cuda")
    assert torch.equal(torch.nn.functional.conv2d(image, kernel),
                       torch.full((1, 1, 14, 14), 9.0, device="cuda"))
    boxes = torch.tensor([[0, 0, 5, 5], [0, 0, 5, 5]], device="cuda", dtype=torch.float32)
    scores = torch.tensor([0.9, 0.8], device="cuda")
    assert torchvision.ops.nms(boxes, scores, 0.5).tolist() == [0]
    torch.cuda.synchronize()

gpu_processes = subprocess.check_output(
    ["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"], text=True
)
report = {
    "test_kind": "synthetic_hardware_and_import_check",
    "is_real_run": False, "model_loaded": False,
    "torch": torch.__version__, "torchvision": torchvision.__version__,
    "cuda_runtime": torch.version.cuda,
    "environment": sys.prefix,
    "device": torch.cuda.get_device_name(),
    "capability": torch.cuda.get_device_capability(),
    "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
    "matmul_conv_nms": "PASS",
    "process_command": subprocess.check_output(
        ["ps", "-p", str(os.getpid()), "-o", "args="], text=True).strip(),
    "gpu_process": [line for line in gpu_processes.splitlines()
                    if line.split(",", 1)[0].strip() == str(os.getpid())],
}
sys.path.insert(0, str(Path("third_party/R2Seg").resolve()))
try:
    import tta_pipeline.biomedparse_inference
    report["backend_import"] = "PASS"
    from detectron2 import _C
    box = torch.tensor([[0.0, 0.0, 4.0, 4.0, 0.0]])
    assert torch.allclose(torch.ops.detectron2.box_iou_rotated(box, box), torch.ones((1, 1)))
    report["detectron2_cpu_extension"] = "PASS"
    report["environment_check"] = "PASS"
except Exception:
    report["environment_check"] = "FAILED"
    report["environment_check_error"] = traceback.format_exc()
Path("reports/hardware-check.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
sys.exit(0 if report["environment_check"] == "PASS" else 1)
