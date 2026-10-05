"""P1.11.1 identity-repair first-evaluable Kaggle bootstrap."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import signal
import subprocess
import sys
import time
import zipfile
from pathlib import Path

RUNTIME_HEAD = os.environ.get("NEUMANN_P1111_FROZEN_HEAD", "")
REPOSITORY_URL = "https://github.com/yoonsj0305/NEUMANN.git"

SETUP = "neumann_p1111_first_setup.json"
OUTPUT = "neumann_p1111_first"
CHECKOUT = "NEUMANN_P1111_FROZEN"
MODEL_DIR = "NEUMANN_P1111_MINILM_FROZEN"
MODEL_ARTIFACTS = "neumann_p1111_model_artifacts.json"
ARCHIVE = "NEUMANN_P1111_FIRST_EVIDENCE.zip"
HASH_RECEIPT = "NEUMANN_P1111_FIRST_EVIDENCE.sha256.json"
LOG = "neumann_p1111_bootstrap.log"
REPLAY = "neumann_p1111_replay_stdout.txt"
CONSTRAINTS = "neumann_p1111_runtime_constraints.txt"

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
REQUIRED_MODEL_FILES = (
    "config.json",
    "model.safetensors",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.txt",
)

PREFLIGHT = '''import json
from importlib.metadata import version
import torch
assert version("torch") == "2.11.0+cu128", "registered CUDA Torch required"
assert version("torchvision") == "0.26.0+cu128", "registered CUDA torchvision required"
assert torch.cuda.is_available(), "select Tesla T4 before the first attempt"
assert torch.cuda.get_device_name(0) == "Tesla T4", "registered Tesla T4 required"
print(json.dumps({"torch":version("torch"),"torchvision":version("torchvision"),
                  "device":torch.cuda.get_device_name(0)},sort_keys=True))
'''

FETCH_MODEL = r'''import sys
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="sentence-transformers/all-MiniLM-L6-v2",
    revision="1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
    local_dir=sys.argv[1],
    allow_patterns=[
        "config.json",
        "model.safetensors",
        "special_tokens_map.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.txt",
    ],
)
print("P1.11 model artifact acquisition complete")
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


def build_artifact_manifest(model_dir):
    model_dir = Path(model_dir)
    files = {}
    for name in REQUIRED_MODEL_FILES:
        path = model_dir / name
        if not path.is_file() or path.is_symlink():
            raise ValueError("missing or unsafe P1.11 model artifact: " + name)
        files[name] = {
            "bytes": path.stat().st_size,
            "sha256": digest_file(path),
        }
    return {
        "schema": "neumann.control-plane-p111-model-artifacts.v1",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "files": files,
    }


def command(args, *, cwd, log, timeout, on_started):
    with log.open("ab") as stream:
        process = subprocess.Popen(
            args,
            cwd=cwd,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
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
    working = Path(working)
    archive = working / ARCHIVE
    receipt = working / HASH_RECEIPT
    if archive.exists() or receipt.exists():
        raise RuntimeError("original P1.11 archive exists; preserve it")

    started = time.perf_counter()
    paths = [
        working / name
        for name in (SETUP, LOG, REPLAY, CONSTRAINTS, MODEL_ARTIFACTS)
    ]
    output = working / OUTPUT
    if output.is_dir():
        paths.extend(sorted(output.rglob("*")))

    members = {}
    with zipfile.ZipFile(
        archive, "x", compression=zipfile.ZIP_DEFLATED
    ) as zipped:
        for path in paths:
            if path.is_symlink():
                raise ValueError("symlink evidence forbidden")
            if not path.is_file():
                continue
            name = path.relative_to(working).as_posix()
            raw = path.read_bytes()
            zipped.writestr(name, raw)
            members[name] = {
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
            }

        raw = Path(__file__).read_bytes()
        name = "bootstrap/control_plane_p1111_kaggle.py"
        zipped.writestr(name, raw)
        members[name] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
        zipped.writestr(
            "archive_manifest.json",
            json.dumps({
                "schema": "neumann.control-plane-p1111-archive.v1",
                "identity_repair_revision": "P1.11.1",
                "historical_first_archive_sha256": "d75aeeccbd54e5c96041a41f4c40c1df17a5504d44c026336c53fab2b247e5e0",
                "historical_observations": 0,
                "historical_model_calls": 0,
                "historical_neural_forward_calls": 0,
                "task_scores_seen_before_repair": False,
                "members": members,
                "runtime_head": RUNTIME_HEAD,
                "development_only": True,
                "p110_task_score_reuse": False,
                "p2_registration_admitted": False,
                "p2_admitted": False,
                "decision3_admitted": False,
                "no_replacement": True,
            }, sort_keys=True, indent=2) + "\n",
        )

    result = {
        "archive": ARCHIVE,
        "archive_sha256": digest_file(archive),
        "archive_bytes": archive.stat().st_size,
        "packaging_ms": (time.perf_counter() - started) * 1000,
        "no_replacement": True,
        "development_only": True,
    }
    write_json(receipt, result, exclusive=True)
    print(json.dumps(result, sort_keys=True), flush=True)
    return result


def package_existing(working):
    working = Path(working)
    data = json.loads((working / SETUP).read_bytes())
    if (
        data.get("runtime_head") != RUNTIME_HEAD
        or data.get("development_only") is not True
    ):
        raise ValueError("P1.11.1 repair setup identity required")
    if data.get("bootstrap_sha256") != digest_file(__file__):
        raise ValueError("recovery requires exact P1.11.1 bootstrap")
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
    if (
        len(RUNTIME_HEAD) != 40
        or any(char not in "0123456789abcdef" for char in RUNTIME_HEAD)
    ):
        raise ValueError("published exact 40-character P1.11.1 source head required")

    working = Path(working)
    if not working.is_dir():
        raise RuntimeError("registered Kaggle working directory required")
    names = (
        SETUP, OUTPUT, CHECKOUT, MODEL_DIR, MODEL_ARTIFACTS,
        ARCHIVE, HASH_RECEIPT, LOG, REPLAY, CONSTRAINTS,
    )
    if any((working / name).exists() for name in names):
        raise RuntimeError("P1.11.1 repair attempt already started; preserve evidence")
    if (
        launcher_wall_ms is not None
        and (not math.isfinite(launcher_wall_ms) or launcher_wall_ms < 0)
    ):
        raise ValueError("finite nonnegative launcher timing required")

    started = time.perf_counter()
    data = {
        "schema": "neumann.control-plane-p1111-setup.v1",
        "identity_repair_revision": "P1.11.1",
        "historical_first_archive_sha256": "d75aeeccbd54e5c96041a41f4c40c1df17a5504d44c026336c53fab2b247e5e0",
        "historical_first_verdict": "NOT_EVALUATED",
        "historical_first_observations": 0,
        "historical_first_model_calls": 0,
        "historical_first_neural_forward_calls": 0,
        "task_scores_seen_before_repair": False,
        "repair_scope": "MODEL_PARAMETER_IDENTITY_ONLY",
        "runtime_head": RUNTIME_HEAD,
        "bootstrap_sha256": digest_file(__file__),
        "status": "STARTED",
        "stages": [],
        "launcher_wall_ms": launcher_wall_ms,
        "development_only": True,
        "favorable_rerun": False,
        "replacement_of_historical_first": False,
        "p110_task_score_reuse": False,
        "p2_registration_admitted": False,
        "p2_admitted": False,
        "decision3_admitted": False,
        "active_child_pid": None,
    }
    write_json(working / SETUP, data, exclusive=True)
    checkout = working / CHECKOUT
    model_dir = working / MODEL_DIR

    def stage(name, args, timeout, cwd=working, required=True, log=None):
        record = {"name": name, "status": "STARTED"}
        data["stages"].append(record)
        write_json(working / SETUP, data)
        print("P1.11.1:", name, flush=True)
        began = time.perf_counter()

        def on_started(pid):
            data["active_child_pid"] = pid
            write_json(working / SETUP, data)

        try:
            code = execute(
                args,
                cwd=cwd,
                log=log or working / LOG,
                timeout=timeout,
                on_started=on_started,
            )
            record.update(
                exit_code=code,
                status="COMPLETE" if code == 0 else "NONZERO",
            )
            if required and code != 0:
                raise RuntimeError(name + " failed; see retained P1.11 bootstrap log")
            return code
        except BaseException as exc:
            record.update(
                status="FAILED_OR_INTERRUPTED",
                error=type(exc).__name__,
            )
            raise
        finally:
            data["active_child_pid"] = None
            record["wall_ms"] = (time.perf_counter() - began) * 1000
            write_json(working / SETUP, data)

    try:
        stage("CUDA runtime preflight", [sys.executable, "-c", PREFLIGHT], 60)
        stage(
            "clone",
            ["git", "clone", "--no-checkout", REPOSITORY_URL, str(checkout)],
            180,
        )
        stage(
            "frozen checkout",
            ["git", "checkout", "--detach", RUNTIME_HEAD],
            60,
            checkout,
        )

        (working / CONSTRAINTS).write_text(
            "torch==2.11.0+cu128\n"
            "torchvision==0.26.0+cu128\n"
            "transformers==5.16.1\n",
            encoding="utf-8",
        )
        stage(
            "dependencies",
            [
                sys.executable, "-m", "pip", "install",
                "--disable-pip-version-check",
                "-c", str(working / CONSTRAINTS),
                "transformers==5.16.1",
                "huggingface_hub",
                "pillow",
                "numpy>=1.26",
                "scipy>=1.11",
                "scikit-learn>=1.4",
            ],
            600,
        )
        stage("post-install CUDA preflight", [sys.executable, "-c", PREFLIGHT], 60)
        stage(
            "frozen model artifact acquisition",
            [sys.executable, "-c", FETCH_MODEL, str(model_dir)],
            600,
        )

        artifact_manifest = build_artifact_manifest(model_dir)
        write_json(
            working / MODEL_ARTIFACTS,
            artifact_manifest,
            exclusive=True,
        )
        data["model_artifact_manifest_sha256"] = digest_file(
            working / MODEL_ARTIFACTS
        )
        write_json(working / SETUP, data)

        stage(
            "package inventory",
            [sys.executable, "-m", "pip", "list", "--format=json"],
            60,
        )
        stage(
            "frozen registration",
            [sys.executable, "-m", "experiments.control_plane_p111_registration"],
            60,
            checkout,
        )

        runner = stage(
            "first evaluable semantic-microexecutor run after identity repair",
            [
                sys.executable, "-u", "-m", "experiments.control_plane_p111_dev",
                "--directory", str(working / OUTPUT),
                "--frozen-head", RUNTIME_HEAD,
                "--model-dir", str(model_dir),
                "--artifact-manifest", str(working / MODEL_ARTIFACTS),
            ],
            600,
            checkout,
            required=False,
        )
        data["runner_exit_code"] = runner
        if not (working / OUTPUT / "terminal.json").is_file():
            raise RuntimeError(
                "P1.11 runner has no terminal receipt; preserve partial attempt"
            )

        replay_code = stage(
            "model-free receipt replay",
            [
                sys.executable, "-m", "experiments.control_plane_p111_replay",
                "--directory", str(working / OUTPUT),
            ],
            120,
            checkout,
            required=False,
            log=working / REPLAY,
        )
        data["replay_exit_code"] = replay_code
        if replay_code != 0:
            raise RuntimeError("P1.11 receipt replay failed; no admission")

        report = json.loads((working / OUTPUT / "report.json").read_bytes())
        decision = report["decision"]
        if (
            report.get("development_only") is not True
            or report.get("p110_task_score_reuse") is not False
            or decision.get("p2_registration_admitted") is not False
            or decision.get("p2_admitted") is not False
            or decision.get("decision3_admitted") is not False
            or runner not in (0, 2)
            or (runner == 0) != (decision["verdict"] == "PASS")
        ):
            raise ValueError("P1.11 development exit/decision boundary drift")

        data["development_verdict"] = decision["verdict"]
        data["status"] = "FINISHED" if runner == 0 else "FINISHED_NONPASS"
    except BaseException as exc:
        data.update(
            status="FAILED_OR_INTERRUPTED",
            error=type(exc).__name__ + ": " + str(exc),
        )
        print(data["error"], flush=True)
    finally:
        data["setup_and_runner_wall_ms"] = (
            time.perf_counter() - started
        ) * 1000
        data["launcher_setup_and_runner_wall_ms"] = (
            None if launcher_wall_ms is None
            else launcher_wall_ms + data["setup_and_runner_wall_ms"]
        )
        write_json(working / SETUP, data)
        result = package(working)
        print("Download from the Kaggle Output panel:", ARCHIVE, flush=True)

    return data, result


def display_archive(working):
    try:
        from IPython.display import HTML, display
        if (Path(working) / ARCHIVE).is_file():
            display(HTML(
                '<a href="/files/' + ARCHIVE + '" download>' + ARCHIVE + "</a>"
            ))
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
