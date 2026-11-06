"""Post-FIRST independent read-only audit of archived student CHC certificates.

Does NOT import original student proposer, original source parser,
human G3 generator or first evaluator. Independently:
- read frozen original FIRST artifact + trained weights; prove weights explain
  first output four-token ASTs with an independently written float scorer;
- re-fetch exact original Git blobs and reconstruct every source assertion;
- independently substitute recorded four-token AST predicate interpretations;
- prove UNSAT of negated EVERY unchanged original Horn clause with real Z3;
- require a genuine SAT counterexample on one deliberately wrong template.
NO fitting, NO new source-unseen evaluation, NO original verdict promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.request import Request,urlopen

FIRST_TASKS = (
 ("standard_init2_true-unreach-call_ground_000.smt2",
  "cba84803dc722ac8e556daf196578793f4400947",4798),
 ("standard_init3_true-unreach-call_ground_000.smt2",
  "1a2f2c157fa25e6dd89850c8bf4239d052143207",6100)
)
UPSTREAM="https://raw.githubusercontent.com/chc-comp/chc-comp25-benchmarks/ddd279cab0717db6effe69baad451a8eb04ffd86/quic3/data/"
FROZEN_WEIGHT_SHA="982ef08b88758537dfe56f3ad8451de26fbd438df295802c491c25d231de9bdc"


def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def blob(raw:bytes)->str:return hashlib.sha1(
 b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()


def forms(source:str)->list[str]:
    result=[];depth=0;start=-1;comment=False;quoted=False
    for i,c in enumerate(source):
        if comment:
            if c in "\r\n":comment=False
            continue
        if c==";" and not quoted:
            comment=True;continue
        if c=="|":
            quoted=not quoted;continue
        if quoted:continue
        if c=="(":
            if depth==0:start=i
            depth+=1
        elif c==")":
            depth-=1
            if depth<0:raise ValueError("SOURCE_NEGATIVE_PARENTHESIS_DEPTH")
            if depth==0:
                result.append(source[start:i+1]);start=-1
    if depth!=0 or quoted:raise ValueError("SOURCE_UNBALANCED")
    return result


def score(weights,stage:int,nstages:int)->list[int]:
    x=(1.0,float(stage==0),float(0<stage<nstages),float(stage==nstages),
       stage/nstages,nstages/12.0)
    ans=[]
    if len(weights)!=4:raise ValueError("INVALID_WEIGHT_HEADS")
    for head in weights:
        if len(head)!=6 or any(len(v)!=4 for v in head):
            raise ValueError("INVALID_WEIGHT_SHAPE")
        logits=[sum(x[f]*head[f][k] for f in range(6)) for k in range(4)]
        ans.append(max(range(4),key=lambda k:logits[k]))
    return ans


def predicate(name:str,stage:int,values:list[int],array_idx:int,token:list[int])->str:
    if type(token) is not list or len(token)!=4 or any(type(t) is not int or t<0 or t>3 for t in token):
        raise ValueError("INVALID_FROZEN_AST_TOKENS")
    params=[("n","Int"),("i","Int"),("arr","(Array Int Int)"),("limit","Int")]
    if array_idx==1:params=[params[0],params[2],params[1],params[3]]
    elif array_idx!=2:raise ValueError("INVALID_ARRAY_ARGUMENT_SLOT")
    clauses=["(> n 0)","(> limit 0)","(<= 0 i)","(<= i limit)"]
    for s in (0,2):
        rng,val=token[s:s+2]
        if rng==0 and val==0:continue
        if rng==0 or val==0:raise ValueError("INCOMPLETE_QUANTIFIER")
        lo,hi={1:("0","i"),2:("i","limit"),3:("0","limit")}[rng]
        if val==1:
            if stage>=len(values):raise ValueError("OUT_OF_RANGE_NEW_VALUE")
            expected=values[stage]
        elif val==2:
            if stage==0:raise ValueError("NO_PREVIOUS_VALUE_AT_FIRST")
            expected=values[stage-1]
        else:expected=-987654321
        clauses.append("(forall ((j Int)) (=> (and (<= "+lo+" j) (< j "+hi+
            ")) (= (select arr (+ n j)) "+str(expected)+")))")
    if len(clauses)==4:raise ValueError("TRIVIAL_ALWAYS_TRUE_PREDICATE")
    return "(define-fun |"+name+"| ("+" ".join(
        "("+p+" "+sort+")" for p,sort in params)+") Bool (and "+" ".join(clauses)+"))"


def reconstruct(original:str,decisions:list[dict])->tuple[str,list[str]]:
    source_forms=forms(original)
    stage_info=[]
    for form in source_forms:
        m=re.fullmatch(r"\(\s*declare-fun\s+\|main@bb(\d+)\.i\|\s+\(\s*(.*?)\s*\)\s+Bool\s*\)",form,re.S)
        if not m:continue
        sorts=re.findall(r"\(Array\s+Int\s+Int\)|Int|Bool",m[2])
        if len(sorts)!=4 or sorts.count("(Array Int Int)")!=1 or sorts.count("Int")!=3:
            raise ValueError("UNSUPPORTED_ORIGINAL_TYPED_LOOP")
        stage_info.append((int(m[1]),form,sorts))
    stage_info.sort()
    values=[int(v) for v in re.findall(
        r"\(\s*store\s+[A-Za-z0-9_!]+\s+[A-Za-z0-9_!]+\s+(\d+)\s*\)",original)]
    if not values or len(values)+1!=len(stage_info):
        raise ValueError("SOURCE_STAGE_COUNT_MISMATCH")
    if values!=list(range(values[0],values[0]+len(values))):
        raise ValueError("UNSUPPORTED_ORIGINAL_WRITE_VALUES")
    if len(decisions)!=len(stage_info):
        raise ValueError("FIRST_MODEL_AST_ROLE_COUNT_CHANGED")
    defs={}
    for idx,(number,decl,sorts) in enumerate(stage_info):
        decision=decisions[idx]
        if decision.get("stage")!=idx:raise ValueError("FIRST_STAGE_ORDER_DRIFT")
        defs[decl]=predicate("main@bb"+str(number)+".i",idx,values,sorts.index("(Array Int Int)"),decision["four_token_AST"])
    for form in source_forms:
        if re.fullmatch(r"\(\s*declare-fun\s+\|main@entry\|\s+\(\s*Int\s*\)\s+Bool\s*\)",form):
            defs[form]="(define-fun |main@entry| ((n Int)) Bool true)"
        elif re.fullmatch(r"\(\s*declare-fun\s+\|main@entry\|\s+\(\s*\)\s+Bool\s*\)",form):
            defs[form]="(define-fun |main@entry| () Bool true)"
        elif re.fullmatch(r"\(\s*declare-fun\s+\|main@verifier\.error\.split\|\s+\(\s*\)\s+Bool\s*\)",form):
            defs[form]="(define-fun |main@verifier.error.split| () Bool false)"
    if len(defs)!=len(stage_info)+2:
        raise ValueError("UNEXPECTED_ADDITIONAL_RELATIONS")
    for form in source_forms:
        if re.match(r"^\(\s*declare-fun",form) and form not in defs:
            raise ValueError("UNKNOWN_SOURCE_RELATION_NOT_SILENTLY_IGNORED")
    assertions=[f for f in source_forms if re.match(r"^\(\s*assert\s+",f)]
    if len(assertions)!=2*len(values)+5:
        # This is an explicit expected family check, not proof shortcut.
        raise ValueError("ORIGINAL_CLAUSE_DENOMINATOR_UNEXPECTED")
    prefix="(set-logic ALL)\n"+"\n".join(defs[f] for f in source_forms if f in defs)+"\n"
    return prefix,assertions


def refute(script:str,timeout_s:int=7)->dict:
    started=time.perf_counter_ns()
    with tempfile.NamedTemporaryFile("w",suffix=".smt2",encoding="utf8") as f:
        f.write(script);f.flush()
        try:
            p=subprocess.run(["z3","-smt2","-T:"+str(timeout_s),f.name],
                capture_output=True,text=True,timeout=timeout_s+2,check=False)
            words=[x.strip() for x in p.stdout.splitlines() if x.strip()]
            result=words[0] if p.returncode==0 and len(words)==1 and words[0] in ("sat","unsat","unknown") else "CHECKER_FAILURE"
        except subprocess.TimeoutExpired:
            result="TIMEOUT"
    return {"verdict":result,"obligation_sha256":sha(script.encode()),
            "wall_ms":round((time.perf_counter_ns()-started)/1e6,3)}


def independent_audit(first_file:Path,checkpoint:Path)->dict:
    first_raw=first_file.read_bytes()
    first=json.loads(first_raw)
    raw=checkpoint.read_bytes()
    if sha(raw)!=FROZEN_WEIGHT_SHA or first["checkpoint_SHA256"]!=FROZEN_WEIGHT_SHA:
        raise ValueError("ORIGINAL_FROZEN_WEIGHT_OR_FIRST_MISMATCH")
    w=json.loads(raw)
    if w.get("original_external_test_sources_opened")!=0:
        raise ValueError("TARGET_DATA_LEAK_IN_STUDENT_TRAIN")
    weights=w["student_weight"]
    if len(first["rows"])!=2 or first["train_source_only_actual_run"]!=42198111692:
        raise ValueError("ORIGINAL_FIRST_DENOMINATOR_OR_TRAIN_RUN_DRIFT")
    results=[]
    mutant_seen=False
    for index,(name,expected_blob,source_bytes) in enumerate(FIRST_TASKS):
        item=first["rows"][index]
        if item.get("name")!=name or item.get("original_git_blob")!=expected_blob:
            raise ValueError("ORIGINAL_FIRST_TASK_ORDER_CHANGED")
        with urlopen(Request(UPSTREAM+name,headers={"User-Agent":"NEUMANN-independent-first-audit"}),timeout=40) as f:
            data=f.read(18000)
        if blob(data)!=expected_blob or len(data)!=source_bytes or sha(data)!=item["source_sha256"]:
            raise ValueError("ACTUAL_ORIGINAL_SOURCE_FILE_CHANGED")
        text=data.decode("utf8")
        tokens=item["student_ast_tokens"]
        nstages=len(tokens)-1
        for k,decision in enumerate(tokens):
            if decision["four_token_AST"]!=score(weights,k,nstages):
                raise ValueError("ARCHIVED_PROPOSAL_NOT_PREDICTED_BY_ACTUAL_TRAINED_WEIGHTS")
        prefix,orig_assertions=reconstruct(text,tokens)
        if sha(prefix.encode())!=item["student_interpretation_sha256"]:
            raise ValueError("INDEPENDENT_RECONSTRUCTED_PROPOSAL_SOURCE_SHA_MISMATCH")
        obligations=[]
        for i,original_assertion in enumerate(orig_assertions):
            phi=original_assertion[len("(assert"):-1].strip()
            job=prefix+"(assert (not "+phi+"))\n(check-sat)\n"
            result=refute(job)
            obligations.append(result)
            if result["verdict"]!="unsat":
                raise ValueError("INDEPENDENT_ORIGINAL_CLAUSE_NOT_PROVEN_"+name+"_"+str(i))
        if len(obligations)!=item["student_original_total_clauses"]:
            raise ValueError("FIRST_VERIFIER_ORIGINAL_CLAUSE_COUNT_CHANGED")
        # A deliberate false new-value claim should make at least one of the
        # actual original unchanged clauses satisfiable (counterexample).
        corrupted=json.loads(json.dumps(tokens))
        corrupted[0]["four_token_AST"][1]=3
        bad_prefix,_=reconstruct(text,corrupted)
        if not mutant_seen:
            verdicts=[]
            for original_assertion in orig_assertions:
                phi=original_assertion[len("(assert"):-1].strip()
                verdicts.append(refute(bad_prefix+"(assert (not "+phi+"))\n(check-sat)\n"))
                if verdicts[-1]["verdict"]=="sat":break
            mutant_seen=any(x["verdict"]=="sat" for x in verdicts)
        results.append({"original_file":name,"git_blob":expected_blob,
          "student_rule_reconstructed_sha256":sha(prefix.encode()),
          "all_original_horn_clauses_independently_proved":True,
          "number_original_clauses":len(orig_assertions),
          "all_archived_token_proposals_generated_by_actual_frozen_weights":True,
          "independent_obligation_hashes":[x["obligation_sha256"] for x in obligations]})
    return {
      "schema":"neumann.g3.ownweight-first-postfirst-third-party-independent-certificate.v1",
      "first_run":42198669136,"first_result_sha256":sha(first_raw),
      "frozen_student_training_run":42198111692,
      "frozen_actual_weights_SHA256":sha(raw),
      "first_originals_verified":len(results),
      "all_original_clauses_verified":sum(x["number_original_clauses"] for x in results),
      "wrong_quantified_value_mutation_rejected_by_actual_SAT_counterexample":mutant_seen,
      "first_result_json_unchanged":True,
      "student_retraining_runs":0,"original_first_reruns":0,
      "human_taught_quantifier_grammar_not_autonomous_invention":True,
      "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN",
      "rows":results
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--first",type=Path,required=True)
    p.add_argument("--checkpoint",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    result=independent_audit(a.first,a.checkpoint)
    a.report.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},indent=2,sort_keys=True))
    if result["first_originals_verified"]!=2 or result["all_original_clauses_verified"]!=20 or not result["wrong_quantified_value_mutation_rejected_by_actual_SAT_counterexample"]:
        raise SystemExit(1)


if __name__=="__main__":
    main()
