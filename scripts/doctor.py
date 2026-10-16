"""Preparation checks only: no model import, download, or GPU allocation.

On pro5000: source scripts/env.sh; python - < scripts/doctor.py
The stdin entry keeps project names out of the process command line.
"""
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone

import jsonschema
import yaml


def main():
    root = Path(os.environ["COOD_ROOT"]).resolve(strict=True)
    data_mount = Path("/data")
    assert data_mount.is_mount(), "/data is not mounted"
    paths = {}
    for key in (
        "COOD_ROOT", "COOD_DATA_ROOT", "COOD_CACHE_ROOT", "COOD_OUTPUT_ROOT",
        "COOD_MODEL_ROOT", "COOD_MANIFEST_ROOT", "TMPDIR", "HF_HOME",
        "HF_HUB_CACHE", "TORCH_HOME", "XDG_CACHE_HOME", "PIP_CACHE_DIR",
        "CUDA_CACHE_PATH", "TRITON_CACHE_DIR", "CONDA_PKGS_DIRS", "VIRTUAL_ENV",
    ):
        path = Path(os.environ[key]).resolve()
        assert path.is_relative_to(Path(os.environ["COOD_STORAGE_ROOT"]).resolve()), f"Off-data path: {key}"
        path.mkdir(parents=True, exist_ok=True)
        assert path.stat().st_dev == data_mount.stat().st_dev, f"Wrong mount: {key}"
        paths[key] = str(path)
    with tempfile.TemporaryFile(dir=root / "tmp") as probe:
        probe.write(b"ready")
        probe.seek(0)
        assert probe.read() == b"ready", "Storage read/write check failed"
    checked = []
    for path in sorted(Path("configs").glob("*.yaml")):
        assert isinstance(yaml.safe_load(path.read_text()), dict), str(path)
        checked.append(str(path))
    for path in sorted(Path("schemas").glob("*.json")):
        schema = json.loads(path.read_text())
        jsonschema.validators.validator_for(schema).check_schema(schema)
        checked.append(str(path))
    lock = json.loads(Path("sources.lock.json").read_text())
    upstream = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd="third_party/R2Seg", text=True
    ).strip()
    assert upstream == lock["r2seg"]["commit"], "Upstream source commit mismatch"
    gpu = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,name,driver_version,memory.total,memory.free",
         "--format=csv"], capture_output=True, text=True, check=False,
    )
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PREPARATION_CHECKS_PASSED",
        "real_inference_run": False,
        "inference_environment_checked": False,
        "python": platform.python_version(), "platform": platform.platform(),
        "preparation_packages": {name: importlib.metadata.version(name)
                                 for name in ("PyYAML", "jsonschema")},
        "paths": paths, "disk_free_bytes": shutil.disk_usage(root).free,
        "validated_files": checked, "r2seg_commit": upstream,
        "gpu_query_exit_code": gpu.returncode,
        "gpu_snapshot": gpu.stdout, "gpu_query_error": gpu.stderr,
        "process_command": subprocess.check_output(
            ["ps", "-p", str(os.getpid()), "-o", "args="], text=True).strip(),
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/environment.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
