"""Q3 after-first *causal* repair: local subtree credit + bidirectional residual.

Failures preserved:
- #42325390566: old semantic actor 0/2, same-language GP 2/2.
- #42326733253: after 86-feature gradient bug repaired, still 0/2.

New test: a learned candidate subtree with output signature s is useful even when
s != target; an invertible binary operation can complete it with residual t-s.
Instead of whole-program exact-match reward, use per-subtree MAE and only
reinforce actions that built that subtree. The completion library is all
typed primitive leaves, never an answer-macro or hidden reference.

Critical: a strong classical competitor gets the exact SAME completion
operator, terminal library, observations and independent Z3 verifier. Thus
synthesis with local repair is NOT "learned-only" if classical succeeds.
The two old source-free tasks are regression cases, NOT new Q3 heldout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path

from research.q3.generative_typed_operator_policy import AST,PRODUCTIONS,check_ast
from research.q3.behavioral_proof_reward_first import (
    PRIVATE_DEV_REFERENCE, IndependentChecker, evaluate_ast,
    gp_candidates, gp_attempt, observe,
)
from research.q3.task_conditional_operator_generator import TaskConditionalGenerator


def walk_subtrees(root:AST):
    """Yield preorder intervals; model.sample's score-event order is preorder."""
    def inner(node,start):
        size=check_ast(node,bound_j=True,ceiling=80)
        yield node,start,start+size
        cursor=start+1
        for child in node.children:
            yield from inner(child,cursor)
            cursor+=check_ast(child,bound_j=True,ceiling=80)
    yield from inner(root,0)


def signature(node:AST,observations):
    result=[]
    for j,(x,y) in enumerate(observations):
        try:
            v=evaluate_ast(node,x=x,j=j)
            if type(v) is not int or abs(v)>1e8:
                return None
            result.append(v)
        except (ValueError,OverflowError,RecursionError):
            return None
    return tuple(result)


def mean_absolute_distance(sig,goal):
    if sig is None:
        return math.inf
    return sum(abs(a-b) for a,b in zip(sig,goal))/len(goal)


FILLERS=tuple(AST("Int",name) for name,childs in PRODUCTIONS["Int"]
              if not childs and name!="j")+(AST("Int","j"),)


def residual_repair(probe:AST, observations, checker:IndependentChecker,
                    metrics:dict):
    """Find one-level closure by the PUBLIC primitive inverse operations.

    This is not hard-coded x+1 or 1-x. Targets used here are only observations,
    and no Z3 checker sees a proposed proof until 32/32 examples agree.
    """
    goal=tuple(y for x,y in observations)
    probesig=signature(probe,observations)
    metrics["observed_candidate_signatures"]+=1
    if probesig is None:
        return None
    if probesig==goal:
        metrics["full_Z3_candidates"]+=1
        checked=checker(probe)
        if checked["verdict"]=="PROVED":
            return {"ast":probe.to_data(),"smt":probe.to_smt(),
                    "checker":checked,"via":"DIRECT_SUBTREE"}
    for fill in FILLERS:
        fill_sig=signature(fill,observations)
        metrics["observed_candidate_signatures"]+=1
        if fill_sig is None:
            continue
        # Algebraically valid inverses for binary + and -, same grammar as GP.
        for op,left,right,outputs in (
            ("add",probe,fill,tuple(a+b for a,b in zip(probesig,fill_sig))),
            ("sub",probe,fill,tuple(a-b for a,b in zip(probesig,fill_sig))),
            ("sub",fill,probe,tuple(b-a for a,b in zip(probesig,fill_sig))),
        ):
            metrics["observed_candidate_signatures"]+=1
            if outputs!=goal:
                continue
            candidate=AST("Int",op,(left,right))
            try:
                check_ast(candidate,bound_j=True,ceiling=80)
            except ValueError:
                continue
            metrics["full_Z3_candidates"]+=1
            checked=checker(candidate)
            if checked["verdict"]=="PROVED":
                return {"ast":candidate.to_data(),"smt":candidate.to_smt(),
                        "checker":checked,"via":"ONE_INVERSE_COMPLETION"}
    return None


def trainable_local_credit(op:str, *, seed=83,episodes=256,learn=True):
    p=observe(op)
    m=TaskConditionalGenerator(seed=seed)
    m.set_observation(p)
    initial=m.parameters_hash()
    ck=IndependentChecker(op,p)
    metrics={"observed_candidate_signatures":0,"full_Z3_candidates":0,
             "invalid_sampling":0,"distinct_sampled_roots":0,
             "subtree_credit_updates":0}
    goal=tuple(y for x,y in p.observations)
    roots=set()
    witness=None
    t0=time.perf_counter()
    for attempt in range(episodes):
        try:
            root,events=m.sample(collision=True,failed_proofs=0,
                       root_kind="Int",bound_index=True,max_depth=4,
                       max_nodes=80)
        except ValueError:
            metrics["invalid_sampling"]+=1
            continue
        roots.add(root.to_smt())
        nodes=list(walk_subtrees(root))
        best=None
        # Choose the subtree having the most residual predictive information.
        # Unlike exact-match count, x is strictly better than zero for x+1.
        for sub,start,end in nodes:
            sig=signature(sub,p.observations)
            metrics["observed_candidate_signatures"]+=1
            mae=mean_absolute_distance(sig,goal)
            if not math.isfinite(mae):
                continue
            entry=(mae,end-start,start,end,sub)
            if best is None or entry[:3]<best[:3]:
                best=entry
            result=residual_repair(sub,p.observations,ck,metrics)
            if result is not None:
                witness={"attempt":attempt,"probe":sub.to_smt(),
                    "candidate":result,"model_weight_updates_before_proof":m.gradient_steps}
                if learn:
                    m.apply_feedback(events[start:end],reward=1.0)
                    metrics["subtree_credit_updates"]+=1
                break
        if witness is not None:
            break
        if best is not None and learn:
            mae,sz,start,end,sub=best
            reward=max(-1.,min(1.,2./(1.+mae)-0.2))
            m.apply_feedback(events[start:end],reward=reward)
            metrics["subtree_credit_updates"]+=1
    metrics["distinct_sampled_roots"]=len(roots)
    return {
      "mode":"LEARNED_SUBTREE_CREDIT" if learn else "SAME_REPAIR_UNTRAINED",
      "observed_sha256":p.sha(),
      "initial_weights_sha256":initial,
      "final_weights_sha256":m.parameters_hash(),
      "gradient_steps":m.gradient_steps,
      "episodes_budget":episodes,
      "observed_wall_ms":round(1000*(time.perf_counter()-t0),3),
      "Z3_subprocess_calls":ck.solver_calls,
      "Z3_subprocess_ms":round(ck.proof_ms,3),
      "metrics":metrics,"proof_witness":witness
    }


def strong_classical_inverse(op:str, *, max_candidates=256):
    p=observe(op)
    ck=IndependentChecker(op,p)
    metrics={"observed_candidate_signatures":0,"full_Z3_candidates":0}
    t0=time.perf_counter()
    found=None;count=0
    # Same primitive grammar, exact examples, inverse completion and verifier.
    for probe in gp_candidates(max_size=2):
        count+=1
        if count>max_candidates:break
        found=residual_repair(probe,p.observations,ck,metrics)
        if found:
            break
    return {"mode":"CLASSICAL_INVERSE_GP_STRONGER_BASELINE",
            "probes_considered":count,"observed_wall_ms":round(1000*(time.perf_counter()-t0),3),
            "Z3_subprocess_calls":ck.solver_calls,
            "Z3_subprocess_ms":round(ck.proof_ms,3),
            "metrics":metrics,"proof_witness":found}


def run(out:Path):
    if out.exists():
        raise ValueError("NO_OVERWRITE_AFTERFIRST_CAUSAL_REGRESSION")
    out.mkdir(parents=True)
    tasks=[]
    for op in PRIVATE_DEV_REFERENCE:
        # All source-free reopened; neither is an independent external
        # original; the strong classical arm has SAME residual repair rights.
        direct=gp_attempt(op,limit=1000)
        strong=strong_classical_inverse(op)
        trained=trainable_local_credit(op,learn=True)
        ablated=trainable_local_credit(op,learn=False)
        tasks.append({"task":op,
           "full_GP_classical":direct,
           "strong_same_repair_classical":strong,
           "learned_local_credit":trained,"untrained_same_repair":ablated,
           "learned_exclusive":bool(trained["proof_witness"]
               and not strong["proof_witness"] and not ablated["proof_witness"])})
    report={
       "schema":"neumann.q3.local-credit-inverse-repair-afterfirst.v1",
       "scope":"CAUSAL_REGRESSION_PREVIOUSLY_OPENED_SOURCE_FREE_TASKS",
       "frozen_orig_FIRST_run":42325390566,
       "frozen_86_grad_fix_run":42326733253,
       "result_tasks":len(tasks),
       "learned_proofs":sum(bool(t["learned_local_credit"]["proof_witness"]) for t in tasks),
       "strong_classical_proofs":sum(bool(t["strong_same_repair_classical"]["proof_witness"]) for t in tasks),
       "untrained_proofs":sum(bool(t["untrained_same_repair"]["proof_witness"]) for t in tasks),
       "learned_exclusive":sum(t["learned_exclusive"] for t in tasks),
       "external_original_tasks":0,
       "target_program_macro_supplied_to_actor":False,
       "same_inverse_operator_rights_for_strong_classical":True,
       "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN",
       "tasks":tasks
    }
    (out/"POSTFIRST_REPORT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="tasks"},sort_keys=True,indent=2))
    for t in tasks:
        print(t["task"],"GP",bool(t["full_GP_classical"]["found"]),
          "CLASSICAL_INVERSE",bool(t["strong_same_repair_classical"]["proof_witness"]),
          "LEARNED",bool(t["learned_local_credit"]["proof_witness"]),
          "ABLATION",bool(t["untrained_same_repair"]["proof_witness"]),
          "learned_episodes",t["learned_local_credit"]["proof_witness"]["attempt"]
                if t["learned_local_credit"]["proof_witness"] else None)
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    run(p.parse_args().out)
