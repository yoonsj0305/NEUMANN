"""One preregistered independent-family ORIGINAL CHC solver portfolio.

Do not edit, normalize, split or add assertions to original source.
No generative model calls. CPU runner contains no target-aware lemma language.
"""
import hashlib
import json
import os
import platform
from pathlib import Path
import re
import shutil
import subprocess
import time
import urllib.request

OWNER_REPO = "chc-comp/chc-comp26-benchmarks"
SOURCE_REV = "b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"
SOURCE_PATH = "ultimate/LIA-NonLin/33_double_lock_p1_vs_simplified_000.smt2"
SOURCE_BLOB = "9c6f22f32de6c32dce69394e38c7a1cf2368e65c"
CAP_SECONDS = 10
OUT = Path(os.environ.get("FGSR_RESULT", "receipt.json"))

def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def summary(source):
    return {
        "declared_relations": re.findall(r"\(declare-fun\s+([^\s()]+)", source),
        "assert_count": len(re.findall(r"\(assert\s", source)),
        "multi_inv_rule_count": sum(
            f.count("(Inv ") >= 2
            for f in source.split("(assert")[1:]
        ),
        "contains_original_check_sat": "(check-sat)" in source,
        "logic": re.findall(r"\(set-logic\s+([^\s()]+)", source),
        "source_bytes": len(source.encode()),
    }

def measure_solver(name, command, source_path):
    executable = shutil.which(command[0])
    if executable is None:
        return {"solver": name, "status": "MISSING", "wall_ms": None, "cmd": command[:1]}
    try:
        ver = subprocess.run([executable, "--version" if name == "cvc5" else "-version"],
                             capture_output=True, text=True, timeout=4)
        version = (ver.stdout + ver.stderr)[:300].strip()
    except Exception as exc:
        version = type(exc).__name__
    start = time.perf_counter_ns()
    try:
        process = subprocess.run([executable, *command[1:], str(source_path)],
                                 stdin=subprocess.DEVNULL, capture_output=True,
                                 text=True, timeout=CAP_SECONDS, check=False)
        stdout = process.stdout.strip()
        stderr = process.stderr.strip()
        lines = stdout.splitlines()
        sat_lines = [line.strip() for line in lines if line.strip() in ("sat", "unsat", "unknown")]
        status = ("DECIDED_" + sat_lines[-1].upper()) if len(sat_lines) == 1 and process.returncode == 0 else (
            "UNKNOWN" if sat_lines == ["unknown"] and process.returncode == 0 else "ERROR"
        )
        output = {
            "status": status, "returncode": process.returncode,
            "stdout_prefix": stdout[:1000], "stderr_prefix": stderr[:1500]
        }
    except subprocess.TimeoutExpired as exc:
        output = {"status": "TIMEOUT", "stdout_prefix": str(exc.stdout)[:300],
                  "stderr_prefix": str(exc.stderr)[:300]}
    except OSError as exc:
        output = {"status": "ERROR", "error": repr(exc)}
    return {
        "solver": name, "version": version, "command": command,
        "cap_s": CAP_SECONDS,
        "wall_ms": round((time.perf_counter_ns() - start) / 1e6, 3),
        **output
    }

def run():
    t0 = time.perf_counter_ns()
    result = {
        "research": "FGSR-Q3 independent-family preregistered classical gap screen",
        "registration": "research/evidence/fgsr-q3-single-independent-family/PREREG_BEFORE_SOURCE_20261016.md",
        "source_repo": OWNER_REPO, "source_revision": SOURCE_REV, "source_path": SOURCE_PATH,
        "expected_git_blob": SOURCE_BLOB,
        "global_questions": "Q1-Q7 OPEN",
        "model_calls": 0,
        "model_training": False,
        "source_modified_for_solver": False,
        "outcome": "NOT_RUN",
        "machine": {"os":platform.platform(), "arch":platform.machine(), "processor":platform.processor()}
    }
    try:
        url=f"https://raw.githubusercontent.com/{OWNER_REPO}/{SOURCE_REV}/{SOURCE_PATH}"
        with urllib.request.urlopen(url, timeout=25) as response:
            data = response.read()
        if git_blob(data) != SOURCE_BLOB:
            raise ValueError("ORIGINAL_GIT_BLOB_HASH_MISMATCH")
        original = data.decode("utf-8")
        result["git_blob_verified"] = True
        result["source_sha256"] = hashlib.sha256(data).hexdigest()
        result["source_structure"] = summary(original)
        # Save original external bytes transiently on CI runner only; never upload.
        temp=Path("/tmp/fgsr_original_external.smt2")
        temp.write_bytes(data)
        commands=[("z3", ["z3", "-smt2"]), ("cvc5",["cvc5","--lang","smt2"])]
        result["solvers"]=[measure_solver(name,cmd,temp) for name,cmd in commands]
        decisions=[x for x in result["solvers"] if x["status"] in ("DECIDED_SAT","DECIDED_UNSAT")]
        result["outcome"]="BASELINE_SOLVED" if decisions else (
            "HEADROOM_CANDIDATE_ONLY" if any(x["status"] in ("TIMEOUT","UNKNOWN") for x in result["solvers"]) else
            "BASELINE_RUNTIME_UNSUPPORTED"
        )
        result["scientific_admission"] = "NO_NEURAL_ADMISSION" # no equally-informed specialist headroom proof
        result["cost_caveats"]="At most two fresh cold one-shot solvers; no broad expert CHC-portfolio exhaustiveness, no match vs learned output; no frontier evidence."
    except Exception as exc:
        result["outcome"]="SOURCE_OR_RUNTIME_BLOCKED"
        result["error_type"]=type(exc).__name__
        result["error"]=str(exc)[:650]
    result["total_wall_ms"]=round((time.perf_counter_ns()-t0)/1e6,3)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("FGSR_VERDICT", result["outcome"])
    for solver in result.get("solvers",[]):
        print("SOLVER",solver["solver"],solver["status"],solver["wall_ms"])
    print("NO_NEURAL_Q_PROMOTION",result["global_questions"])

if __name__=="__main__":
    run()
