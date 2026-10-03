"""Run this repository-pinned script once in a Kaggle GPU notebook cell.

Set NEUMANN_P1_FROZEN_HEAD to the published tested/merged commit, then run.
No provider credentials, paid compute, answers, tools or sealed data are used.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

frozen_head = os.environ.get("NEUMANN_P1_FROZEN_HEAD", "")
if len(frozen_head) != 40 or any(c not in "0123456789abcdef" for c in frozen_head):
    raise ValueError("published frozen 40-character commit required")
working = Path("/kaggle/working")
if not working.is_dir():
    raise RuntimeError("registered Kaggle notebook required")
setup = working / "neumann_p1_first_setup.json"
output = working / "neumann_p1_first"
archive = working / "NEUMANN_P1_FIRST_EVIDENCE.zip"
if setup.exists() or output.exists() or archive.exists():
    raise RuntimeError("first attempt already started; preserve existing evidence, do not rerun")
started = time.perf_counter()
setup_data = {"schema": "neumann.control-plane-p1-setup.v1", "frozen_head": frozen_head,
              "status": "STARTED", "favorable_rerun": False}
setup.write_text(json.dumps(setup_data, sort_keys=True, indent=2) + "\n")
repository = working / "NEUMANN_P1_FROZEN"
try:
    import torch
    if torch.__version__ != "2.11.0+cu128":
        raise RuntimeError("registered torch-2.11.0+cu128 required; no automatic torch replacement")
    if not torch.cuda.is_available() or torch.cuda.get_device_name(0) != "Tesla T4":
        raise RuntimeError("select Kaggle Tesla T4 GPU before running")
    if repository.exists():
        raise RuntimeError("fresh pinned checkout path required")
    subprocess.run(["git", "clone", "--no-checkout", "https://github.com/yoonsj0305/NEUMANN.git", str(repository)], check=True, timeout=180)
    subprocess.run(["git", "checkout", "--detach", frozen_head], cwd=repository, check=True, timeout=60)
    # Preserve the known CUDA torch/torchvision runtime; install no alternative model.
    subprocess.run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
                    "transformers==5.16.1", "huggingface_hub", "pillow", "numpy>=1.26", "scipy>=1.11", "scikit-learn>=1.4"],
                   check=True, timeout=600)
    subprocess.run([sys.executable, "-m", "experiments.control_plane_p1_first", "--check-registration"],
                   cwd=repository, check=True, timeout=60)
    command = [sys.executable, "-m", "experiments.control_plane_p1_first", "--directory", str(output), "--frozen-head", frozen_head]
    outcome = subprocess.run(command, cwd=repository, timeout=2700, check=False)
    setup_data["runner_exit_code"] = outcome.returncode
    if (output / "terminal.json").is_file():
        replay = subprocess.run([sys.executable, "-m", "experiments.control_plane_p1_replay", "--directory", str(output)],
                                cwd=repository, capture_output=True, text=True, timeout=60)
        (working / "neumann_p1_replay_stdout.txt").write_text(replay.stdout + replay.stderr)
        setup_data["replay_exit_code"] = replay.returncode
    setup_data["status"] = "FINISHED"
except Exception as exc:
    setup_data.update(status="FAILED_OR_INTERRUPTED", error=type(exc).__name__ + ": " + str(exc))
    print(setup_data["error"], flush=True)
finally:
    setup_data["setup_and_runner_wall_ms"] = (time.perf_counter() - started) * 1000
    setup.write_text(json.dumps(setup_data, sort_keys=True, indent=2) + "\n")
    packaging_started = time.perf_counter()
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(setup, setup.name)
        if output.is_dir():
            for path in sorted(output.glob("*.json")):
                z.write(path, "p1/" + path.name)
        replay_path = working / "neumann_p1_replay_stdout.txt"
        if replay_path.is_file():
            z.write(replay_path, replay_path.name)
    packaging = {"archive": archive.name, "packaging_ms": (time.perf_counter()-packaging_started)*1000,
                 "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                 "no_replacement": True}
    (working / "NEUMANN_P1_FIRST_EVIDENCE.sha256.json").write_text(json.dumps(packaging,sort_keys=True,indent=2)+"\n")
    print("Preserve and download:", archive, flush=True)
    print(json.dumps(packaging, sort_keys=True), flush=True)
    try:
        from IPython.display import display, FileLink
        display(FileLink(str(archive)))
    except ImportError:
        pass
