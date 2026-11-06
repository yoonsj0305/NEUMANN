"""One-shot external-author original CHC classical baseline, not Q3 learner.

Eldarica 2.2, publicly released 2025 solver. ORIGINALS have already
been opened in PR #672/#674. Never rescore these as unopened Q3 tests.
This reports raw native status only, NOT independent model certification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path
from urllib.request import Request, urlopen

UPSTREAM = "chc-comp/chc-comp25-benchmarks"
UPSTREAM_COMMIT = "ddd279cab0717db6effe69baad451a8eb04ffd86"
ORIGINALS = (
    ("COPY2", "quic3/data/standard_copy2_true-unreach-call_ground_000.smt2",
     6318, "30b3bab8834aa6f834cf493539180e6b92caf16f"),
    ("COPY3", "quic3/data/standard_copy3_true-unreach-call_ground_000.smt2",
     8201, "f8fd0b73c3aa45ee5f49426416a378bcfc462605"),
)
TIME_CAP_SECONDS = 60


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def classify(stdout: str, timed_out: bool, returncode: int | None) -> str:
    if timed_out:
        return "TIMEOUT_CENSORED"
    verdicts = [s.strip() for s in stdout.splitlines()
                if s.strip() in ("sat", "unsat", "unknown")]
    if returncode != 0 or len(verdicts) != 1:
        return "CHECKER_ERROR_OR_UNPARSABLE"
    return verdicts[0]


def run_one(eld: Path, label: str, relative: str, nbytes: int,
            expected_blob: str, out: Path) -> dict:
    url = ("https://raw.githubusercontent.com/" + UPSTREAM + "/"
           + UPSTREAM_COMMIT + "/" + relative)
    req = Request(url, headers={"User-Agent": "NEUMANN-classical-native-first"})
    with urlopen(req, timeout=30) as handle:
        source = handle.read(nbytes + 1)
    if len(source) != nbytes or git_blob(source) != expected_blob:
        raise ValueError("ORIGINAL_BLOB_INTEGRITY_FAIL_" + label)
    path = out / (label + ".original.smt2")
    path.write_bytes(source)

    cmd = [str(eld.resolve()), "-ssol", str(path.resolve())]
    started = time.perf_counter_ns()
    timed_out = False
    returncode = None
    stdout = ""
    stderr = ""
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True,
                                   errors="replace", timeout=TIME_CAP_SECONDS,
                                   check=False)
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as e:
        timed_out = True
        stdout = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = (e.stderr or b"").decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
    elapsed = (time.perf_counter_ns() - started) / 1e9

    (out / (label + ".native.stdout")).write_text(stdout, encoding="utf-8")
    (out / (label + ".native.stderr")).write_text(stderr, encoding="utf-8")
    verdict = classify(stdout, timed_out, returncode)
    return {
        "label": label, "original": relative, "original_bytes": nbytes,
        "original_git_blob": expected_blob, "original_sha256": sha256(source),
        "solver": "Eldarica 2.2 native 2025 release",
        "solver_command": ["eld", "-ssol", "<pinned-original-file>"],
        "time_cap_seconds": TIME_CAP_SECONDS, "native_wall_seconds": round(elapsed, 4),
        "exit_code": returncode, "timed_out": timed_out,
        "native_status": verdict,
        "native_sat_claim": verdict == "sat",
        "independent_original_model_proof": "NOT_RUN",
        "native_stdout_sha256": sha256(stdout.encode()),
        "native_stderr_sha256": sha256(stderr.encode()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eld", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--release-archive", type=Path, required=True)
    args = parser.parse_args()
    if not args.eld.is_file() or not args.release_archive.is_file():
        raise ValueError("SOLVER_OR_ARCHIVE_MISSING")
    if args.out.exists():
        raise ValueError("FIRST_OUTPUT_OVERWRITE_FORBIDDEN")
    args.out.mkdir(parents=True)
    report = {
        "schema": "neumann.q3.strong-classical-native-copy-opened-development-first.v1",
        "cohort": "ALREADY_OPENED_EXTERNAL_ORIGINALS_NOT_HELDOUT",
        "upstream": UPSTREAM, "upstream_commit": UPSTREAM_COMMIT,
        "archive_source": "https://github.com/uuverifiers/eldarica/releases/download/v2.2/eldarica-bin-2.2.zip",
        "archive_sha256_observed": sha256(args.release_archive.read_bytes()),
        "human_H1_not_retrained": True, "student_not_retrained": True,
        "same_tool_competition_benchmark_no_new_originals": True,
        "Q3": "OPEN", "Q4": "OPEN", "Q6": "OPEN",
        "results": [],
    }
    try:
        for item in ORIGINALS:
            outcome = run_one(args.eld, *item, args.out)
            report["results"].append(outcome)
            print(json.dumps({k: outcome[k] for k in
                              ("label", "native_status", "native_wall_seconds",
                               "time_cap_seconds")}, sort_keys=True))
    finally:
        (args.out / "FIRST_NATIVE_STATUS.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("NATIVE_ONLY_NO_INDEPENDENT_MODEL_PROOF")


if __name__ == "__main__":
    main()
