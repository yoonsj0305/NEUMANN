"""Single source-opened continuation of first bounded relational Houdini.

Same original 48 clauses, exactly same previously frozen 1105 candidate-language
definitions; no additions, no invented templates and no neural calls. The prior
8-round broad scan was stopped before fixpoint, so switch to work-efficient
immediate counterexample elimination (same fixed-point semantics).

Scientific success only when all 48 original clauses are independently
validated after convergence. A fixed-point cut-off is NOT scientific PASS.
"""
import hashlib,json,os,time,urllib.request
from pathlib import Path
from relational_houdini_single_gate import (
    source_assertions,candidate_program,query,SHA,REV,PATH
)
from collections import Counter

MAX_SMT_CHECKS=1500
WALL_CAP_SECONDS=235
OUT=Path(os.getenv("FGSR_RESULT","relational_continuation_receipt.json"))

def main():
    start=time.perf_counter_ns()
    receipt={
        "experiment":"FGSR original 48 Horn efficient fixed-point follow-up to 8-round INCOMPLETE",
        "status":"NOT_RUN","source_sha256":SHA,"source_opened":True,
        "no_template_changes_after_first_run":True,"neural_calls":0,"global_Q1_Q7":"OPEN",
        "max_smt_checks":MAX_SMT_CHECKS,"wall_cap_s":WALL_CAP_SECONDS,
        "replays_first_frozen_candidate_language":True,
        "attempts":0,"counterexample_refinements":0,"worklist_passes":0,
        "removed_by_original_rule":{}
    }
    try:
        url=f"https://raw.githubusercontent.com/chc-comp/chc-comp26-benchmarks/{REV}/{PATH}"
        with urllib.request.urlopen(url,timeout=30) as f:data=f.read()
        if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError("SOURCE_HASH_MISMATCH")
        rules=source_assertions(data.decode())
        templates=candidate_program()
        active=set(range(len(templates)))
        if len(rules)!=48 or len(templates)!=1105:
            raise ValueError("CHANGED_ORIGINAL_OR_CANDIDATE_LANGUAGE")
        receipt["z3_version"]=__import__("z3").get_version_string()
        receipt["frozen_candidate_count"]=len(templates)
        removal_log=Counter()
        while True:
            if (time.perf_counter_ns()-start)/1e9>WALL_CAP_SECONDS:
                raise TimeoutError("TOTAL_RESEARCH_WALL_CAP")
            receipt["worklist_passes"]+=1
            changed=False
            for rule in rules:
                if rule["kind"]!="relation":continue
                while True:
                    if receipt["attempts"]>=MAX_SMT_CHECKS:
                        raise TimeoutError("SMT_CHECK_CAP")
                    if (time.perf_counter_ns()-start)/1e9>WALL_CAP_SECONDS:
                        raise TimeoutError("TOTAL_RESEARCH_WALL_CAP")
                    ans,invalid,wall=query(rule,templates,active)
                    receipt["attempts"]+=1
                    if ans=="unsat":break
                    if ans!="sat":raise ValueError("SOLVER_INCOMPLETE_"+str(rule["index"]))
                    bad=set(invalid)&active
                    if not bad:raise RuntimeError("SPURIOUS_COUNTEREXAMPLE_"+str(rule["index"]))
                    active-=bad
                    removal_log[rule["index"]]+=len(bad)
                    receipt["counterexample_refinements"]+=1
                    changed=True
                # Every clause proved inductive relative to current active set,
                # but previously checked clauses must be revisited after weakening.
            if not changed:break
        receipt["inductive_fixed_point"]=True
        receipt["remaining_candidates"]=len(active)
        receipt["accepted_predicate_names"]=[templates[i]["name"] for i in sorted(active)]
        receipt["removed_by_original_rule"]=dict(sorted(removal_log.items()))
        checked=[]
        for rule in rules:
            if receipt["attempts"]>=MAX_SMT_CHECKS:raise TimeoutError("FINAL_PROOF_SMT_CAP")
            if (time.perf_counter_ns()-start)/1e9>WALL_CAP_SECONDS:
                raise TimeoutError("FINAL_PROOF_WALL_CAP")
            ans,bad,wall=query(rule,templates,active)
            receipt["attempts"]+=1
            checked.append({"rule":rule["index"],"result":ans,"wall_ms":wall})
        receipt["original_clause_results"]=checked
        receipt["verified_original_unsat"]=sum(x["result"]=="unsat" for x in checked)
        receipt["first_original_nonunsat"]=next((x for x in checked if x["result"]!="unsat"),None)
        receipt["status"]=(
           "ALL_48_ORIGINAL_CERTIFIED_CLASSICAL_RELATIONAL_HOUDINI"
           if len(checked)==48 and receipt["verified_original_unsat"]==48
           else "INDUCTIVE_RELATION_INSUFFICIENT_ORIGINAL_GOAL"
        )
    except TimeoutError as exc:
        receipt["status"]="INCOMPLETE_BUDGET_EXCEEDED"
        receipt["error"]=str(exc)
        receipt["remaining_candidates_unverified"]=len(active) if 'active' in locals() else None
        receipt["removed_by_original_rule"]=dict(sorted(removal_log.items())) if 'removal_log' in locals() else {}
    except Exception as exc:
        receipt["status"]="BLOCKED_OR_ERROR"
        receipt["error"]=type(exc).__name__+": "+str(exc)[:800]
    receipt["total_wall_ms"]=round((time.perf_counter_ns()-start)/1e6,3)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    print("NEUMANN_FGSR_RESULT",receipt["status"])
    print("FIXPOINT",receipt.get("inductive_fixed_point"))
    print("VERIFIED_ORIGINAL",receipt.get("verified_original_unsat"),"of 48")
    print("RETAINED",receipt.get("remaining_candidates",receipt.get("remaining_candidates_unverified")))
    print("SMT_CHECKS",receipt["attempts"],"COUNTEREXAMPLES",receipt["counterexample_refinements"])
    print("GLOBAL_Q",receipt["global_Q1_Q7"])

if __name__=="__main__":main()
