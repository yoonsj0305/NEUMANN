"""PRE-SOURCE-FROZEN first real cross-source model transfer gate.

Two fixed external CHC-COMP original target files selected before reading.
Uses the existing original five-relation Houdini candidate-language operators
and frozen 15 trained linear weights unchanged, with ONLY generic source
quantifier parsing and result-count proof handling. Unsupported => ABSTAIN.

No manual source-specific source repair; no trained operator invention claim.
"""
import ctypes as C
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import urllib.request

REV="b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"
BASE="https://raw.githubusercontent.com/chc-comp/chc-comp26-benchmarks/"
TARGETS=[
    ("HOPV_MOCHI_SUM","hopv/lia/mochi/sum_000.smt2"),
    ("ELDARICA_LLREVE_FIB","eldarica-misc/LIA/llreve/fib_safe.c-1_000.smt2")
]
ORIGINAL_CLASSICAL_LIMIT=8
PER_SOURCE_WALL_LIMIT=115
MAX_SOURCE_CLAUSES=40
MAX_RELATIONS=10
MAX_RELATION_ARITY=6
OUT=Path(os.environ.get("FGSR_RESULT","transfer_first_receipt.json"))
CORE=Path(__file__).parent.parent/"fgsr-q3-automatic-scaffold-20261017"/"autonomous_scaffold_once.py"

spec=importlib.util.spec_from_file_location("frozen_previous_head",CORE)
core=importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

def unsupported(reason):
    raise ValueError("ABSTAIN_UNSUPPORTED_SOURCE:"+reason)

def inspect_original(txt):
    import z3
    try:forms=z3.parse_smt2_string(txt)
    except Exception as exc:unsupported("Z3_SMT2_PARSE_"+type(exc).__name__)
    if not (1 <= len(forms) <= MAX_SOURCE_CLAUSES):
        unsupported("CLAUSE_COUNT_"+str(len(forms)))
    rules=[];relations={}
    for idx,q in enumerate(forms,1):
        if not z3.is_quantifier(q) or not q.is_forall():
            unsupported("NOT_FORALL_RULE_"+str(idx))
        vars_=[z3.Const(f"heldout_{idx}_var{j}",q.var_sort(j))
               for j in range(q.num_vars())]
        if any(v.sort()!=z3.IntSort() for v in vars_):
            unsupported("NON_INT_SOURCE_QUANTIFIER_"+str(idx))
        implied=z3.substitute_vars(q.body(),*vars_)
        if not z3.is_implies(implied):
            unsupported("NON_HORN_BODY_"+str(idx))
        prem,head=implied.children()
        terms=list(core.atoms(prem))
        relations_in=[
            a for a in terms if z3.is_app(a)
            and a.decl().kind()==z3.Z3_OP_UNINTERPRETED
            and a.sort()==z3.BoolSort()]
        guards=[a for a in terms if a not in relations_in]
        if z3.is_false(head):kind="false"
        elif (z3.is_app(head) and head.decl().kind()==z3.Z3_OP_UNINTERPRETED
               and head.sort()==z3.BoolSort()):kind="relation"
        else:unsupported("UNSUPPORTED_HEAD_"+str(idx))
        for a in ([head] if kind=="relation" else [])+relations_in:
            signature=a.decl()
            if any(signature.domain(i)!=z3.IntSort()
                   for i in range(signature.arity())):
                unsupported("NON_INT_RELATION_SORT")
            name=signature.name()
            if name in relations and relations[name]!=a.num_args():
                unsupported("RELATION_ARITY_CONFLICT")
            relations[name]=a.num_args()
        rules.append(dict(index=idx,calls=relations_in,guards=guards,head=head))
    if not (1<=len(relations)<=MAX_RELATIONS):
        unsupported("RELATION_COUNT_"+str(len(relations)))
    if max(relations.values())>MAX_RELATION_ARITY:
        unsupported("RELATION_ARITY_GT_"+str(MAX_RELATION_ARITY))
    if not any(z3.is_false(x["head"]) for x in rules):
        unsupported("NO_EXPLICIT_FALSE_GOAL")
    if any(not name.startswith("inv_") for name in relations):
        unsupported("RELATION_NAMES_NOT_IN_FROZEN_INV_STAR_GRAMMAR")
    return rules,relations

def original_native(path):
    import z3
    lib=C.CDLL(str(Path(z3.__file__).parent/"lib/libz3.so"))
    lib.Z3_mk_config.restype=C.c_void_p
    lib.Z3_mk_context.argtypes=[C.c_void_p];lib.Z3_mk_context.restype=C.c_void_p
    lib.Z3_del_config.argtypes=[C.c_void_p];lib.Z3_del_context.argtypes=[C.c_void_p]
    lib.Z3_eval_smtlib2_string.argtypes=[C.c_void_p,C.c_char_p]
    lib.Z3_eval_smtlib2_string.restype=C.c_char_p
    cfg=lib.Z3_mk_config();ctx=lib.Z3_mk_context(cfg);lib.Z3_del_config(cfg)
    try:
        ans=lib.Z3_eval_smtlib2_string(ctx,path.read_bytes())
        print((ans or b"").decode(errors="replace").strip())
    finally:lib.Z3_del_context(ctx)

def original_baseline(path):
    start=time.perf_counter_ns()
    try:
        p=subprocess.run([sys.executable,__file__,"--native",str(path)],
                         capture_output=True,text=True,check=False,timeout=ORIGINAL_CLASSICAL_LIMIT)
        stdout=p.stdout.strip()
        result=("SOLVED_"+stdout.upper() if p.returncode==0 and stdout in ("sat","unsat")
                else "UNKNOWN" if p.returncode==0 and stdout=="unknown" else "RUNTIME_OR_PARSE_ERROR")
        return {"status":result,"stdout":stdout[:500],
                "wall_ms":round((time.perf_counter_ns()-start)/1e6,3)}
    except subprocess.TimeoutExpired:
        return {"status":"TIMEOUT","wall_ms":round((time.perf_counter_ns()-start)/1e6,3)}

def independent_original_replay(text,definitions,n):
    # Same generic second-verifier architecture as frozen original research gate.
    import z3
    originals=z3.parse_smt2_string(text)
    if len(originals)!=n:raise ValueError("REPLAY_SOURCE_CLAUSE_COUNT_CHANGED")
    entries=[]
    for index,quant in enumerate(originals,1):
        variables=[z3.Const(f"transferred_goal_{index}_{j}",quant.var_sort(j))
                   for j in range(quant.num_vars())]
        # Compile emitted definitions + the original universal clause together:
        # fresh variable interpretation avoids quantified solver incompleteness.
        scripts=z3.parse_smt2_string("(set-logic ALL)\n"+definitions+
                    "\n(assert "+quant.sexpr()+")")
        if len(scripts)!=1 or not z3.is_quantifier(scripts[0]):
            raise ValueError("REPLAY_QUANTIFIER_UNSUPPORTED")
        q=scripts[0]
        fresh=[z3.Const(f"independent_{index}_{j}",q.var_sort(j))
               for j in range(q.num_vars())]
        body=z3.substitute_vars(q.body(),*fresh)
        solver=z3.Solver();solver.set(timeout=4000);solver.add(z3.Not(body))
        t=time.perf_counter_ns()
        result=str(solver.check())
        entries.append({"original":index,"result":result,
             "ms":round((time.perf_counter_ns()-t)/1e6,3)})
    return {"all_original_certified":len(entries)==n and
            all(x["result"]=="unsat" for x in entries),
            "original_rule_results":entries}

class AbortOverBudget(Exception):pass
def alarm_handler(signum,frame):raise AbortOverBudget("PER_SOURCE_115S_WALL_CAP")

def do_one(name,path,workdir):
    start=time.monotonic()
    result={"target_id":name,"source_path":path,"source_rev":REV,
            "status":"UNSTARTED","source_was_new_before_prereg":True,
            "source_modified":False,"model_revision":"FROZEN_15_WEIGHT_NO_RETRAIN",
            "no_human_patched_relations":True,"all_global_questions":"OPEN"}
    try:
        with urllib.request.urlopen(BASE+REV+"/"+path,timeout=30) as f:blob=f.read()
        original=blob.decode()
        result.update({"source_sha256":hashlib.sha256(blob).hexdigest(),
                       "source_bytes":len(blob),
                       "source_git_content_not_redistributed":True})
        import z3
        rules,relations=inspect_original(original)
        result["original_clause_count"]=len(rules)
        result["source_relation_signatures"]=relations
        # DOMAIN SUPPORT gate before any neural matrix multiplication or expensive source solver.
        prior_signal=signal.signal(signal.SIGALRM,alarm_handler)
        signal.alarm(PER_SOURCE_WALL_LIMIT)
        try:
            loops=core.infer_loop_candidates(rules)
            if not loops:
                unsupported("NO_FROZEN_DECREMENT_ACCUMULATOR_LOOP")
            if len(loops)>5:unsupported("TOO_MANY_SOURCE_RECURSIONS")
            result["domain_supported"]=True
            result["discovered_recursions"]={
                k:{"source_rule":v["original_rule"],
                   "features":list(v["source_features"])}
                for k,v in loops.items()}
            p=workdir/("original_"+name+".smt2")
            p.write_bytes(blob)
            result["cold_original_z3"]=original_baseline(p)
            partial=core.solve_source(rules,relations,loops,"LEARNED",time.monotonic())
            result["learner_scaffold"]={
                k:v for k,v in partial.items() if k!="explicit_original_relation_definitions_smt2"}
            result["proof_rule_count"]=len(partial["original_verdicts"])
            result["full_generated_smt_relation_definitions"]=partial["explicit_original_relation_definitions_smt2"]
            result["replay"]=independent_original_replay(
                original,partial["explicit_original_relation_definitions_smt2"],len(rules))
            result["status"]=(
                "REAL_TRANSFER_FULL_ORIGINAL_CERTIFIED"
                if result["replay"]["all_original_certified"]
                else "REAL_TRANSFER_ATTEMPT_ORIGINAL_NOT_CERTIFIED")
            result["same_information_exact_classical_coefficients"]={
                k:loops[k]["learned"]==loops[k]["classical"] for k in loops}
            if any(not v for v in result["same_information_exact_classical_coefficients"].values()):
                exact=core.solve_source(rules,relations,loops,"CLASSICAL",time.monotonic())
                result["strong_exact_classical_original_count"]=exact["original_unsat_count"]
            else:result["strong_exact_classical_is_identical"] = True
        finally:
            signal.alarm(0);signal.signal(signal.SIGALRM,prior_signal)
    except ValueError as exc:
        reason=str(exc)
        if reason.startswith("ABSTAIN_UNSUPPORTED_SOURCE:"):
            result["status"]="ABSTAIN_UNSUPPORTED_SOURCE"
            result["abstain_reason"]=reason.split(":",1)[1]
        else:
            result["status"]="BLOCKED_OR_ERROR";result["error"]=type(exc).__name__+":"+str(exc)[:650]
    except (AbortOverBudget,TimeoutError) as exc:
        result["status"]="INCOMPLETE_BUDGET";result["error"]=str(exc)[:500]
    except Exception as exc:
        result["status"]="BLOCKED_OR_ERROR";result["error"]=type(exc).__name__+":"+str(exc)[:650]
    result["elapsed_wall_ms"]=round((time.monotonic()-start)*1000,3)
    return result

def main():
    import z3
    output={"study":"NEUMANN Q3 first source-family transfer heldout",
            "targets_precommitted_count":2,
            "prereg_git_commit":"bdf8b4704ea3b3394c3148cf9e84fab139f1bf3e",
            "head_training_changed":False,"operator_grammar_changed_after_sources":False,
            "scientific_status":"PENDING","global_q1_q7":"OPEN",
            "z3_version":z3.get_version_string(),"targets":[]}
    workdir=Path("/tmp/neumann_q3_first_external_transfer")
    workdir.mkdir(parents=True,exist_ok=True)
    for name,path in TARGETS:
        entry=do_one(name,path,workdir)
        output["targets"].append(entry)
        print("TRANSFER_CASE",name,entry["status"],entry.get("abstain_reason",entry.get("error","")),flush=True)
    output["full_source_certificates"]=sum(
        x["status"]=="REAL_TRANSFER_FULL_ORIGINAL_CERTIFIED" for x in output["targets"])
    output["source_coverage_denominator"]=len(TARGETS)
    output["scientific_status"]=(
       "TWO_SOURCE_RESTRICTED_OPERATOR_TRANSFER_ONLY"
       if output["full_source_certificates"]==2
       else "CROSS_SOURCE_TRANSFER_NOT_ESTABLISHED")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n")
    print("TRANSFER_ACTUAL",output["full_source_certificates"],"/",len(TARGETS))
    print("Q1_TO_Q7",output["global_q1_q7"])

if __name__=="__main__":
    if len(sys.argv)==3 and sys.argv[1]=="--native":original_native(Path(sys.argv[2]))
    else:main()
