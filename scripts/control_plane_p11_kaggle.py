"""Frozen first P1.1 development bootstrap; importing this file does no work.

The bootstrap is published separately from the unchanged PR134 runtime commit.
No model, revision, codes, thresholds or study directories are configurable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import zipfile

RUNTIME_HEAD = "4e6db9926a27c94f63c8d539d0c6e57c34b49336"
REPOSITORY_URL = "https://github.com/yoonsj0305/NEUMANN.git"
SETUP = "neumann_p11_first_setup.json"
OUTPUT = "neumann_p11_first"
CHECKOUT = "NEUMANN_P11_FROZEN"
ARCHIVE = "NEUMANN_P11_FIRST_EVIDENCE.zip"
HASH_RECEIPT = "NEUMANN_P11_FIRST_EVIDENCE.sha256.json"
LOG = "neumann_p11_bootstrap.log"
REPLAY = "neumann_p11_replay_stdout.txt"
CONSTRAINTS = "neumann_p11_runtime_constraints.txt"

# Run in child interpreters: pip changes cannot leave stale imported modules in
# a notebook kernel. Never replace the registered CUDA Torch/vision packages.
PREFLIGHT = '''import json
from importlib.metadata import version
import torch
assert version("torch") == "2.11.0+cu128", "registered CUDA Torch required"
assert version("torchvision") == "0.26.0+cu128", "registered CUDA vision required"
assert torch.cuda.is_available(), "select Tesla T4 before the first attempt"
assert torch.cuda.get_device_name(0) == "Tesla T4", "registered Tesla T4 required"
print(json.dumps({"torch":version("torch"),"torchvision":version("torchvision"),
                 "device":torch.cuda.get_device_name(0)},sort_keys=True))
'''


def write_json(path, value, exclusive=False):
    with Path(path).open("x" if exclusive else "w", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


def digest_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def command(args, *, cwd, log, timeout, on_started):
    """Keep subprocess output on disk; stop the whole owned group on timeout."""
    with log.open("ab") as stream:
        process = subprocess.Popen(args, cwd=cwd, stdout=stream,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            on_started(process.pid)
            return process.wait(timeout=timeout)
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            raise


def package(working):
    """Exclusive evidence-only packaging. Never starts or repairs inference."""
    working = Path(working)
    archive = working / ARCHIVE
    receipt = working / HASH_RECEIPT
    if archive.exists() or receipt.exists():
        raise RuntimeError("original archive/receipt exists; preserve it, never replace")
    started = time.perf_counter()
    paths = [working / name for name in (SETUP, LOG, REPLAY, CONSTRAINTS)]
    output = working / OUTPUT
    if output.is_dir():
        paths.extend(sorted(output.rglob("*")))
    members = {}
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for path in paths:
            if path.is_symlink():
                raise ValueError("symlink evidence forbidden")
            if not path.is_file():
                continue
            name = path.relative_to(working).as_posix()
            raw = path.read_bytes()
            z.writestr(name, raw)
            members[name] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        raw = Path(__file__).read_bytes()
        name = "bootstrap/control_plane_p11_kaggle.py"
        z.writestr(name, raw)
        members[name] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        z.writestr("archive_manifest.json", json.dumps({
            "schema": "neumann.control-plane-p11-archive.v1", "members": members,
            "runtime_head": RUNTIME_HEAD, "development_only": True,
            "p2_admitted": False, "decision3_admitted": False,
            "no_replacement": True}, sort_keys=True, indent=2) + "\n")
    result = {"archive": ARCHIVE, "archive_sha256": digest_file(archive),
              "archive_bytes": archive.stat().st_size,
              "packaging_ms": (time.perf_counter() - started) * 1000,
              "no_replacement": True, "development_only": True}
    write_json(receipt, result, exclusive=True)
    print(json.dumps(result, sort_keys=True), flush=True)
    return result


def package_existing(working):
    """After a hard kernel stop only; a live child blocks recovery."""
    working = Path(working)
    data = json.loads((working / SETUP).read_bytes())
    if data.get("runtime_head") != RUNTIME_HEAD or data.get("development_only") is not True:
        raise ValueError("original P1.1 setup identity required")
    if data.get("bootstrap_sha256") != digest_file(__file__):
        raise ValueError("recovery requires the exact original bootstrap bytes")
    pid = data.get("active_child_pid")
    if pid is not None:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pass
        else:
            raise RuntimeError("child still exists; do not package changing evidence")
    return package(working)


def run(working=Path("/kaggle/working"), execute=command, *, launcher_wall_ms=None):
    working = Path(working)
    if not working.is_dir():
        raise RuntimeError("registered Kaggle working directory required")
    names = (SETUP, OUTPUT, CHECKOUT, ARCHIVE, HASH_RECEIPT, LOG, REPLAY, CONSTRAINTS)
    if any((working / name).exists() for name in names):
        raise RuntimeError("first attempt already started; retain evidence, do not rerun")
    if launcher_wall_ms is not None and (not math.isfinite(launcher_wall_ms) or launcher_wall_ms < 0):
        raise ValueError("finite nonnegative launcher timing required")
    started = time.perf_counter()
    data = {"schema": "neumann.control-plane-p11-setup.v1", "runtime_head": RUNTIME_HEAD,
            "bootstrap_sha256": digest_file(__file__), "status": "STARTED", "stages": [],
            "launcher_wall_ms": launcher_wall_ms,
            "development_only": True, "favorable_rerun": False,
            "p2_admitted": False, "decision3_admitted": False, "active_child_pid": None}
    # Atomic reservation precedes any dependency change, download or model load.
    write_json(working / SETUP, data, exclusive=True)
    checkout = working / CHECKOUT

    def stage(name, args, timeout, cwd=working, required=True, log=None):
        record = {"name": name, "status": "STARTED"}
        data["stages"].append(record)
        write_json(working / SETUP, data)
        print("P1.1:", name, flush=True)
        began = time.perf_counter()
        def on_started(pid):
            data["active_child_pid"] = pid
            write_json(working / SETUP, data)
        try:
            code = execute(args, cwd=cwd, log=log or working / LOG,
                           timeout=timeout, on_started=on_started)
            record.update(exit_code=code, status="COMPLETE" if code == 0 else "NONZERO")
            if required and code != 0:
                raise RuntimeError(name + " failed; see retained bootstrap log")
            return code
        except BaseException as exc:
            record.update(status="FAILED_OR_INTERRUPTED", error=type(exc).__name__)
            raise
        finally:
            data["active_child_pid"] = None
            record["wall_ms"] = (time.perf_counter() - began) * 1000
            write_json(working / SETUP, data)

    try:
        stage("CUDA runtime preflight", [sys.executable, "-c", PREFLIGHT], 60)
        stage("clone", ["git", "clone", "--no-checkout", REPOSITORY_URL, str(checkout)], 180)
        stage("frozen checkout", ["git", "checkout", "--detach", RUNTIME_HEAD], 60, checkout)
        (working / CONSTRAINTS).write_text(
            "torch==2.11.0+cu128\ntorchvision==0.26.0+cu128\ntransformers==5.16.1\n", encoding="utf-8")
        stage("dependencies", [sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
              "-c", str(working / CONSTRAINTS), "transformers==5.16.1", "huggingface_hub", "pillow",
              "numpy>=1.26", "scipy>=1.11", "scikit-learn>=1.4"], 600)
        stage("post-install CUDA preflight", [sys.executable, "-c", PREFLIGHT], 60)
        stage("package inventory", [sys.executable, "-m", "pip", "list", "--format=json"], 60)
        stage("frozen registration", [sys.executable, "-m", "experiments.control_plane_p11_dev",
              "--check-registration"], 60, checkout)
        runner_code = stage("first development run", [sys.executable, "-u", "-m",
              "experiments.control_plane_p11_dev", "--directory", str(working / OUTPUT),
              "--frozen-head", RUNTIME_HEAD], 2700, checkout, required=False)
        data["runner_exit_code"] = runner_code
        if not (working / OUTPUT / "terminal.json").is_file():
            raise RuntimeError("runner has no terminal receipt; preserve partial attempt")
        # Replay does no model loading. Output is a separate retained member.
        replay_log = working / REPLAY
        replay_code = stage("model-free receipt replay", [sys.executable, "-m",
                            "experiments.control_plane_p11_replay", "--directory", str(working / OUTPUT)],
                            60, checkout, required=False, log=replay_log)
        data["replay_exit_code"] = replay_code
        if replay_code != 0:
            raise RuntimeError("receipt replay failed; no admission")
        report = json.loads((working / OUTPUT / "report.json").read_bytes())
        decision = report["decision"]
        if (report.get("development_only") is not True or decision.get("p2_admitted") is not False
                or decision.get("decision3_admitted") is not False
                or (runner_code == 0) != (decision["verdict"] == "PASS")
                or runner_code not in (0, 2)):
            raise ValueError("development-only exit/decision boundary drift")
        data["development_verdict"] = decision["verdict"]
        data["status"] = "FINISHED" if runner_code == 0 else "FINISHED_NONPASS"
    except BaseException as exc:
        data.update(status="FAILED_OR_INTERRUPTED", error=type(exc).__name__ + ": " + str(exc))
        print(data["error"], flush=True)
    finally:
        data["setup_and_runner_wall_ms"] = (time.perf_counter() - started) * 1000
        data["launcher_setup_and_runner_wall_ms"] = (
            None if launcher_wall_ms is None else launcher_wall_ms + data["setup_and_runner_wall_ms"])
        write_json(working / SETUP, data)
        result = package(working)
        print("Download from the Kaggle Output panel:", ARCHIVE, flush=True)
    return data, result


def display_archive(working):
    # Relative URL avoids the broken absolute /kaggle/working hyperlink.
    try:
        from IPython.display import HTML, display
        if (Path(working) / ARCHIVE).is_file():
            display(HTML('<a href="/files/' + ARCHIVE + '" download>' + ARCHIVE + '</a>'))
    except ImportError:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-existing", action="store_true")
    args = parser.parse_args()
    if args.package_existing:
        package_existing(Path("/kaggle/working"))
    else:
        data, _ = run()
        display_archive(Path("/kaggle/working"))
        raise SystemExit(0 if data["status"] == "FINISHED" else 2)
