"""G1 independent ORIGINAL first cvc5 eight-source read-only proof audit.

No import from the original specialist, first evaluator, official format
conversion, original proposer or student. All eight cvc5 candidates are
reconstructed byte-exactly from pinned FIRST stdout excerpts, with SHA256
proof, then verified by a strictly stronger negative ground-equality
UNSAT test against independently re-downloaded original TRAIN and held-out
PBE constraints. The cvc5 synthesizer is NOT rerun, model NOT retrained.
Original test already opened; does NOT establish blind generalization.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[2]
PINNED_FIRST_SHA256="0650d9c9d75f8f25311ee5b522ac6aed8ca9c6b1941a283e013cd6cb5019835f"
ORIGINAL_CONTRACT=ROOT/"docs/experiments/G1_OWNWEIGHT_STRING_AST_EXTERNAL_FIRST_PREREG_2026_11_06.json"
ORIGINAL_ERRATUM=ROOT/"docs/experiments/G1_EXTERNAL_SYGUS_FIRST_METADATA_SHA_ERRATUM_2026_11_06.json"
WEIGHTS_SHA256="ae5e291d525098b05ade6eaaf5be76c5fc432fb20a39306be8b782377e4c1641"

def digest(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def gitblob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def forms(source:str)->list[tuple[int,int,str]]:
    """Alternate single-pass grounded S-expression parser, no dependency on first."""
    result=[]
    depth=0
    start=None
    literal=False
    comment=False
    j=0
    while j<len(source):
        c=source[j]
        if comment:
            if c=="\n": comment=False
            j+=1
            continue
        if literal:
            if c=='"':
                if j+1<len(source) and source[j+1]=='"':
                    j+=2
                    continue
                literal=False
            j+=1
            continue
        if c==';':
            comment=True
        elif c=='"':
            literal=True
        elif c=='(':
            if depth==0:start=j
            depth+=1
        elif c==')':
            depth-=1
            if depth<0:raise ValueError("UNBALANCED_ORIGINAL_CLOSING_PAREN")
            if depth==0:
                result.append((start,j+1,source[start:j+1]))
                start=None
        j+=1
    if depth or literal:raise ValueError("UNBALANCED_ORIGINAL_OR_UNTERMINATED_STRING")
    return result

def full_source_candidate(excerpt:str)->str|None:
    m=re.search(r"\(\s*define-fun\s+f\b",excerpt)
    if not m:return None
    fragment=excerpt[m.start():]
    # cvc5 wraps solutions in an outer S-expression. The excerpt still
    # contains the OUTER closing paren after this define-fun, so do not
    # parse the entire suffix as if it were one balanced document.
    depth=0
    in_string=False
    i=0
    while i<len(fragment):
        ch=fragment[i]
        if in_string:
            if ch=='"':
                if i+1<len(fragment) and fragment[i+1]=='"':
                    i+=2
                    continue
                in_string=False
        elif ch=='"':
            in_string=True
        elif ch=='(':
            depth+=1
        elif ch==')':
            depth-=1
            if depth==0:
                candidate=fragment[:i+1]
                return candidate if re.match(r"^\(\s*define-fun\s+f\b",candidate) else None
            if depth<0:
                return None
        i+=1
    return None

def original_split(raw:bytes):
    text=raw.decode("utf-8")
    src_forms=forms(text)
    cs=[(a,b,f) for a,b,f in src_forms if re.match(r"^\(\s*constraint\b",f)]
    if len(cs)<2:
        raise ValueError("NOT_ORIGINAL_MULTICONSTRAINT")
    s,e,last=cs[-1]
    train=text[:s]+text[e:]
    fs=forms(train)
    train_cs=[f for _,_,f in fs if re.match(r"^\(\s*constraint\b",f)]
    if len(train_cs)!=len(cs)-1:
        raise ValueError("REMOVED_MORE_THAN_HELDOUT")
    if last in train:
        raise ValueError("HELDOUT_DUPLICATED_IN_TRAIN")
    return train,train_cs,last,len(cs)

def query_false_equality(candidate:str,original_constraints:list[str]):
    if not original_constraints:return ("","NO_EXAMPLES")
    negated=[]
    for original in original_constraints:
        if not original.startswith("(constraint ") or not original.endswith(")"):
            return ("","NOT_CANONICAL_ORIGINAL_CONSTRAINT")
        expression=original[len("(constraint "):-1]
        negated.append("(not "+expression+")")
    claim=negated[0] if len(negated)==1 else "(or "+" ".join(negated)+")"
    return "(set-logic ALL)\n"+candidate+"\n(assert "+claim+")\n(check-sat)\n",None

def prove_by_unsat(candidate:str,examples:list[str],seconds:float=7):
    script,error=query_false_equality(candidate,examples)
    if error:
        return {"proof":"FAIL_CLOSED","reason":error}
    with tempfile.NamedTemporaryFile("w",suffix=".smt2",encoding="utf-8") as p:
        p.write(script)
        p.flush()
        try:
            completed=subprocess.run(["cvc5","--lang=smt2",p.name],
                capture_output=True,text=True,timeout=seconds,check=False)
        except subprocess.TimeoutExpired:
            return {"proof":"UNKNOWN","reason":"CVC5_SMT_GROUND_TIMEOUT"}
    outs=[l.strip() for l in completed.stdout.splitlines() if l.strip()]
    exact=(completed.returncode==0 and outs==["unsat"])
    return {
        "proof":"ALL_ORIGINAL_GROUND_EQUALITIES_PROVEN" if exact else "NOT_PROVEN",
        "solver_output":outs[:4],
        "solver_exit":completed.returncode,
        "stderr":completed.stderr[-180:]
    }

def audit(receipt_file:Path)->dict:
    data=receipt_file.read_bytes()
    receipt=json.loads(data)
    errors=[]
    if digest(data)!=PINNED_FIRST_SHA256:
        errors.append("IMMUTABLE_EIGHT_ORIGINAL_FIRST_SHA256_DRIFT")
    if receipt.get("scientific_status")!="POST_FIRST_STRONG_SPECIALIST_RESULTS_RECORDED":
        errors.append("SCOPED_FIRST_STATUS_DRIFT")
    if receipt.get("stats",{}).get("independently_original_heldout_verified")!=8:
        errors.append("FIRST_AGGREGATE_CORRUPTED")
    if receipt.get("student_unchanged_checkpoint_sha256")!=WEIGHTS_SHA256:
        errors.append("STUDENT_CHECKPOINT_DRIFT")
    contract=json.loads(ORIGINAL_CONTRACT.read_text())
    erratum=json.loads(ORIGINAL_ERRATUM.read_text())["actual_source_error"]
    originals=contract["external_original"]["tasks"]
    if len(originals)!=8 or len(receipt.get("rows",[]))!=8:
        errors.append("CHANGED_EXTERNAL_ORIGINAL_DENOMINATOR")
        return {"audit_pass":False,"errors":errors}
    res=[]
    valid=0
    for i,original in enumerate(originals):
        first=receipt["rows"][i]
        expected=(erratum["correct_original_github_blob_40_hex"]
           if original["name"]==erratum["file"] else original["git_blob"])
        if first["name"]!=original["name"]:
            errors.append("ORIGINAL_SOURCE_ORDER_DRIFT_"+original["name"])
            continue
        url=("https://raw.githubusercontent.com/"+contract["external_original"]["repo"]+
            "/"+contract["external_original"]["commit"]+"/"+contract["external_original"]["subdir"]+
            "/"+original["name"])
        with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G1-independent-SMT-audit"}),timeout=40) as r:
            raw=r.read(50000)
        observed=gitblob(raw)
        if observed!=expected or first["original_git_blob"]!=observed:
            errors.append("ORIGINAL_PUBLISHER_SOURCE_SHA_CHANGED_"+original["name"])
            continue
        train_source,train,last,n=original_split(raw)
        if digest(train_source.encode())!=first["original_source_train_sha256"]:
            errors.append("TRAIN_WITHHELD_SOURCE_HASH_DRIFT_"+original["name"])
        if digest(last.encode())!=first["withheld_last_constraint_sha256"]:
            errors.append("ORIGINAL_WITHHELD_GOLD_HASH_DRIFT_"+original["name"])
        if first["original_constraints"]!=n:
            errors.append("ORIGINAL_CONSTRAINT_COUNT_DRIFT_"+original["name"])
        specialist=first["specialist"]
        att=next((a for a in specialist["attempts"] if
                  a.get("dialect")==specialist.get("dialect")),None)
        candidate=full_source_candidate(att["stdout_excerpt"]) if att else None
        if not candidate or digest(candidate.encode())!=specialist["candidate_sha256"]:
            errors.append("PINNED_CVC5_ORIGINAL_PROGRAM_MISSING_OR_ALTERED_"+original["name"])
            continue
        # This is NOT the original verifier. It asks cvc5 to prove there
        # exists NO input/output constraint violation, not to SAT-test
        # positive equalities as in the FIRST verifier.
        train_proof=prove_by_unsat(candidate,train,7)
        withheld_proof=prove_by_unsat(candidate,[last],7)
        good=(train_proof["proof"]=="ALL_ORIGINAL_GROUND_EQUALITIES_PROVEN" and
              withheld_proof["proof"]=="ALL_ORIGINAL_GROUND_EQUALITIES_PROVEN")
        valid+=int(good)
        if not good or not first["verified_heldout"]:
            errors.append("GOLD_ORIGINAL_NOT_INDEPENDENTLY_PROVEN_"+original["name"])
        res.append({
          "original_file":original["name"],
          "exact_original_git_blob":observed,
          "original_train_constraints":n-1,
          "candidate_SHA256_from_original_FIRST":digest(candidate.encode()),
          "train_unsat_of_counterexample":train_proof,
          "original_heldout_unsat_of_counterexample":withheld_proof,
          "independent_original_verified":good,
          "candidate_reexecuted_for_synthesis":False
        })
    if valid!=8:errors.append("EIGHT_ORIGINAL_COMPLETE_PROOF_NOT_ESTABLISHED")
    return {
      "schema":"neumann.g1.eight-original-cvc5-expert-independent-negative-SMT-proof.v1",
      "audit_pass":not errors,
      "errors":errors[:25],
      "first_source_receipt_SHA256":digest(data),
      "independent_full_first_candidate_sha_verified":len(res),
      "original_independently_proven_count":valid,
      "original_external_denominator":8,
      "originals":res,
      "NN_retrained":False,
      "original_specialist_synthesis_rerun":False,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
      "scope":"PBE exact all original finite TRAIN and withheld last equalities, not universal string-equivalence or matched-language 10x"
    }

if __name__=="__main__":
    try:
        o=audit(Path(sys.argv[1]))
        print(json.dumps(o,indent=2,sort_keys=True))
        if not o["audit_pass"]:raise SystemExit(1)
    except Exception as ex:
        print("READONLY_EXPERT_AUDIT_FAIL_CLOSED",type(ex).__name__,str(ex),file=sys.stderr)
        raise SystemExit(2)
