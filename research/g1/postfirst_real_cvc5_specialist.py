"""G1 post-first REAL SyGuS specialist baseline: cvc5, original grammar, withheld final constraint.

This is an externally published original benchmark after an already negative
NEUMANN FIRST and an independently audited source-metadata correction.
No original FIRST is rewritten. Does not import the neural model or original
restricted-225-program first scorer. Stronger specialist gets the *published*
SyGuS grammar and the same original TRAIN constraints, never withheld final
original constraint. Evaluates only genuine independently checked solutions.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
PRE = ROOT / "docs/experiments/G1_OWNWEIGHT_STRING_AST_EXTERNAL_FIRST_PREREG_2026_11_06.json"
ERRATUM = ROOT / "docs/experiments/G1_EXTERNAL_SYGUS_FIRST_METADATA_SHA_ERRATUM_2026_11_06.json"
CONTRACT = ROOT / "docs/experiments/G1_POSTFIRST_REAL_CVC5_SPECIALIST_AUDIT_PREREG_2026_11_06.json"
FROZEN_FIRST_SHA = "6d9940cefc43d9b8ccb93b375bcaf4ba02690481ca432637e54de28a09bfe8cc"
Q = r'"(?:[^"]|"")*"'
FORM = re.compile(r"^\s*\(constraint\s+\(=\s+\(f\s*((?:" + Q + r"\s*)+)\)\s*(" + Q + r")\s*\)\s*\)\s*$", re.S)
STRINGS = re.compile(Q)
FUNCTION = re.compile(r"\(\s*define-fun\s+f\b")


def gitblob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def top_forms(source: str) -> list[tuple[int, int, str]]:
    """S-expression boundaries, skipping string-literal and comment parentheses."""
    output = []
    depth = 0
    string = False
    comment = False
    start = -1
    j = 0
    while j < len(source):
        c = source[j]
        if comment:
            if c in "\r\n":
                comment = False
            j += 1
            continue
        if string:
            if c == '"':
                if j + 1 < len(source) and source[j + 1] == '"':
                    j += 2
                    continue
                string = False
            j += 1
            continue
        if c == ";":
            comment = True
            j += 1
            continue
        if c == '"':
            string = True
            j += 1
            continue
        if c == "(":
            if depth == 0:
                start = j
            depth += 1
        elif c == ")":
            depth -= 1
            if depth < 0:
                raise ValueError("SOURCE_UNBALANCED_CLOSE")
            if depth == 0 and start >= 0:
                output.append((start, j + 1, source[start:j+1]))
                start = -1
        j += 1
    if depth != 0 or string:
        raise ValueError("SOURCE_UNBALANCED_OR_UNTERMINATED_STRING")
    return output


def parse_constraint(form: str) -> tuple[list[str], str] | None:
    match = FORM.fullmatch(form.strip())
    if not match:
        return None
    lhs = STRINGS.findall(match.group(1))
    rhs = match.group(2)
    if not lhs or not rhs:
        return None
    return lhs, rhs


def prepare_original(raw: bytes) -> dict:
    text = raw.decode("utf8")
    forms = top_forms(text)
    constraints = [(s, e, f) for s, e, f in forms if re.match(r"^\(\s*constraint\b", f)]
    if len(constraints) < 2 or "(check-synth)" not in text:
        raise ValueError("NOT_ORIGINAL_SYGUS_WITH_MULTIPLE_CONSTRAINTS")
    s, e, heldout = constraints[-1]
    parsed = parse_constraint(heldout)
    if parsed is None:
        raise ValueError("UNSUPPORTED_HELDOUT_ORIGINAL_CONSTRAINT_FORMAT")
    # Keep the full *original grammar*, everything except exactly the LAST
    # original constraint as the SyGuS source for the specialist.
    train_source = text[:s] + text[e:]
    if heldout in train_source and train_source.count(heldout) > 0:
        # Duplicates in the training set may be legitimate; the original
        # withheld constraint remains logically known. Refuse as holdout.
        raise ValueError("HELDOUT_ORIGINAL_DUPLICATE_IN_TRAIN")
    train_forms = top_forms(train_source)
    ntrain = sum(bool(re.match(r"^\(\s*constraint\b", f)) for _,_,f in train_forms)
    if ntrain != len(constraints) - 1:
        raise ValueError("HOLDOUT_REMOVAL_CHANGED_OTHER_ORIGINAL_CONSTRAINTS")
    return {
        "train_source": train_source,
        "train_source_sha256": sha(train_source.encode()),
        "heldout_form": heldout,
        "heldout_form_sha256": sha(heldout.encode()),
        "heldout_args": parsed[0],
        "heldout_gold": parsed[1],
        "train_constraints": [f for _,_,f in train_forms if re.match(r"^\(\s*constraint\b",f)],
        "original_constraint_count":len(constraints),
    }


def extract_define(stdout: str) -> str | None:
    """Extract just the frozen candidate define-fun, never regenerate it."""
    for match in FUNCTION.finditer(stdout):
        fragment = stdout[match.start():]
        try:
            forms = top_forms(fragment)
        except ValueError:
            # A later form might follow; scan with an explicit depth parser.
            forms = []
        if forms and re.match(r"^\(\s*define-fun\s+f\b", forms[0][2]):
            return forms[0][2]
        # cvc5 typically prints ( (define-fun ... ) ). Strip one outer
        # wrapper only; do not accept multiple conflicting candidate funcs.
        depth = 0
        string = False
        j = match.start()
        while j < len(stdout):
            c=stdout[j]
            if c == '"' and (j+1 >= len(stdout) or stdout[j+1]!='"'):
                string = not string
            if not string:
                if c == "(":depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        candidate = stdout[match.start():j+1]
                        if re.match(r"^\(\s*define-fun\s+f\b",candidate):
                            return candidate
            j+=1
    return None


def professional_solver(train_source: str, timeout_s: float) -> dict:
    if shutil.which("cvc5") is None:
        return {"status":"CVC5_CLI_NOT_INSTALLED"}
    # The historic source uses the pre-2019 SyGuS dialect. These switches
    # are ONLY dialect parsers, not alternative grammars or policies.
    attempts = [
       ("sygus1", ["cvc5","--lang=sygus1","--sygus","--tlimit-per=12000"]),
       ("sygus2", ["cvc5","--lang=sygus2","--sygus","--tlimit-per=12000"]),
    ]
    records=[]
    with tempfile.TemporaryDirectory(prefix="g1_specialist_") as temp:
        p=Path(temp)/"original_train_only.sl"
        p.write_text(train_source,encoding="utf8")
        for dialect,command in attempts:
            begin=time.perf_counter_ns()
            try:
                done=subprocess.run(command+[str(p)],stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE, text=True, timeout=timeout_s,
                   check=False)
                wall_ms=(time.perf_counter_ns()-begin)/1e6
                rec={"dialect":dialect,"exit":done.returncode,"wall_ms":round(wall_ms,3),
                    "stdout_sha256":sha(done.stdout.encode()),
                    "stderr_tail":done.stderr[-650:],
                    "stdout_excerpt":done.stdout[:900]}
                candidate=extract_define(done.stdout)
                records.append(rec)
                if done.returncode==0 and candidate is not None:
                    return {"status":"CANDIDATE_UNVERIFIED","candidate":candidate,
                        "candidate_sha256":sha(candidate.encode()),
                        "dialect":dialect,"attempts":records}
            except subprocess.TimeoutExpired:
                records.append({"dialect":dialect,"status":"TIMEOUT",
                                "wall_ms":round((time.perf_counter_ns()-begin)/1e6,3)})
        return {"status":"NO_SYNTHESIS_CANDIDATE","attempts":records}


def ground_verify(candidate:str, train:list[str], heldout:str, seconds:float=12.) -> dict:
    """Verify TRAIN first; heldout gold *only* after candidate was frozen."""
    if not re.match(r"^\(\s*define-fun\s+f\b",candidate):
        return {"status":"INVALID_SOLUTION_SYNTAX"}
    reports=[]
    for label, formulas in [("train",train), ("heldout",[heldout])]:
        ground=candidate+"\n"+'\n'.join(
           f"(assert {x[len('(constraint '):-1]})" for x in formulas)+"\n(check-sat)\n"
        with tempfile.NamedTemporaryFile(mode="w",encoding="utf8",
              suffix=".smt2",delete=True) as source:
            source.write("(set-logic ALL)\n"+ground)
            source.flush()
            try:
                r=subprocess.run(["cvc5","--lang=smt2",source.name],
                   stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                   timeout=seconds,check=False)
                answer=r.stdout.strip().splitlines()
                good=(r.returncode==0 and answer and answer[-1].strip()=="sat")
                reports.append({"label":label,"verified":good,
                   "solver_answer":answer[-1][:180] if answer else None,
                   "solver_exit":r.returncode,"solver_stderr_tail":r.stderr[-450:]})
            except subprocess.TimeoutExpired:
                reports.append({"label":label,"verified":False,"solver_answer":"TIMEOUT"})
            if not reports[-1]["verified"]:
                break
    return {"status":"CANDIDATE_TRAIN_AND_HELDOUT_VERIFIED" if len(reports)==2
          and all(x["verified"] for x in reports) else "CANDIDATE_NOT_INDEPENDENTLY_VERIFIED",
          "checks":reports}


def main() -> int:
    pre=json.loads(PRE.read_text())
    err=json.loads(ERRATUM.read_text())["actual_source_error"]
    contract=json.loads(CONTRACT.read_text())
    if len(pre["external_original"]["tasks"])!=8 or contract["original_task_denominator"]!=8:
        raise ValueError("DENOMINATOR_CHANGED")
    corrected=err["correct_original_github_blob_40_hex"]
    rows=[]
    cmd_version=subprocess.run(["cvc5","--version"],capture_output=True,text=True,timeout=8)
    begin=time.perf_counter_ns()
    for target in pre["external_original"]["tasks"]:
        url=("https://raw.githubusercontent.com/"+pre["external_original"]["repo"]+"/"+
             pre["external_original"]["commit"]+"/"+pre["external_original"]["subdir"]+
             "/"+target["name"])
        with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G1-real-specialist"}),timeout=40) as r:
            raw=r.read(50000)
        observed=gitblob(raw)
        expected=(corrected if target["name"]==err["file"] else target["git_blob"])
        if observed!=expected or len(observed)!=40:
            raise ValueError("OFFICIAL_ORIGINAL_GIT_BLOB_DRIFT_"+target["name"])
        row={"name":target["name"],"original_source_blob":observed,
             "source_bytes":len(raw)}
        try:
            p=prepare_original(raw)
        except (ValueError,UnicodeDecodeError) as e:
            row.update({"status":"UNSUPPORTED_ORIGINAL_WITHHELD_FORMAT",
                        "reason":str(e),"specialist":None})
            rows.append(row)
            continue
        row.update({"original_constraint_count":p["original_constraint_count"],
           "train_only_sha256":p["train_source_sha256"],
           "heldout_sha256":p["heldout_form_sha256"],
           "original_heldout_gold_never_in_synthesis":True})
        slv=professional_solver(p["train_source"],12.)
        if slv["status"]=="CANDIDATE_UNVERIFIED":
            candidate=slv.pop("candidate")
            slv["ground_original_verification"]=ground_verify(candidate,
                         p["train_constraints"],p["heldout_form"])
            slv["verified_exact"]=(slv["ground_original_verification"]["status"]==
                                "CANDIDATE_TRAIN_AND_HELDOUT_VERIFIED")
        else:
            slv["verified_exact"]=False
        row.update({"status":"SPECIALIST_RUN",
                   "specialist":slv})
        rows.append(row)
    scored=[r for r in rows if r["status"]=="SPECIALIST_RUN"]
    stats={
        "external_source_denominator":len(rows),
        "source_parsed":len(scored),
        "unsupported_counted":len(rows)-len(scored),
        "cvc5_proposed":sum(r["specialist"]["status"]=="CANDIDATE_UNVERIFIED" for r in scored),
        "independent_original_heldout_verified":sum(r["specialist"]["verified_exact"] for r in scored),
        "real_specialist_version":cmd_version.stdout.strip() or cmd_version.stderr.strip(),
        "source_only_training_not_repeated":True,
        "original_model_v2_checkpoint_sha256":"ae5e291d525098b05ade6eaaf5be76c5fc432fb20a39306be8b782377e4c1641",
        "original_ARC_evaluation_IDs_consumed":0,
        "total_external_source_fetch_and_solve_wall_ms":(time.perf_counter_ns()-begin)/1e6
    }
    out={
      "schema":"neumann.g1.cvc5-real-specialist-post-first-audit.v1",
      "scientific_status":"SPECIALIST_POST_FIRST_RESULT_RECORDED_NOT_Q3",
      "equal_rights_note":"Real specialist uses strictly broader ORIGINAL source grammar, not matched model AST, favorable-to-classical strong reference",
      "source_first_not_rerun":True,
      "globally_learned_new_semantics":"OPEN",
      "global_Q4":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
      "stats":stats,"rows":rows
    }
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(json.dumps({"scientific_status":"INFRASTRUCTURE_FAIL_CLOSED",
          "exception":type(e).__name__,"message":str(e)[:400]},indent=2))
        raise SystemExit(2)
