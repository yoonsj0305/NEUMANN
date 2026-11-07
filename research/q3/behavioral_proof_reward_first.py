"""Q3 strict learner-vs-GP admission experiment, with all-domain Z3 verification.

The actor receives only 32 black-box I/O observations, NEVER the hidden
reference executable term. The reference is present only inside the external
checker and strong same-language GP control. Neural actor is a genuine
own-weight autoregressive typed expression AST generator, trained by
counterexample-derived finite observational reward; a candidate is marked
PROVED only after an independent Z3 all-integer/all-array UNSAT proof.

This source-free DEVELOPMENT class is intentionally not a global Q3 pass. A
strong GP baseline has identical primitive/AST rights, input examples and
proof oracle, and may saturate it. Abort if saturated; do not inflate counts.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import subprocess
import time
from pathlib import Path
from dataclasses import dataclass
from research.q3.generative_typed_operator_policy import AST, PRODUCTIONS, Generator, check_ast
from research.q3.task_conditional_operator_generator import (
    BehavioralProblem, TaskConditionalGenerator
)

TRAIN_INPUTS=tuple(range(-16,16))
# Hidden mathematical reference program; only the verifier reads this.
# The learned actor receives BehavioralProblem(examples), never these terms.
PRIVATE_DEV_REFERENCE={
    "source_plus_one": "(+ (select src j) 1)",
    "one_minus_source": "(- 1 (select src j))",
}
REFERENCE_SHA={k:hashlib.sha256(v.encode()).hexdigest()
               for k,v in PRIVATE_DEV_REFERENCE.items()}


def numerical_program(op:str,x:int)->int:
    # Observations are generated from actual executable programs. No AST
    # target, human predicate label, or symbolic RHS is sent to the learner.
    if op=="source_plus_one":return x+1
    if op=="one_minus_source":return 1-x
    raise ValueError("UNKNOWN_DEVELOPMENT_REFERENCE")


def observe(op:str)->BehavioralProblem:
    return BehavioralProblem(tuple((x,numerical_program(op,x))
                                   for x in TRAIN_INPUTS),True,0)


def evaluate_ast(node:AST,*,x:int,j:int,depth=0)->int:
    if depth>30:
        raise ValueError("TREE_TOO_DEEP")
    name=node.name
    if name=="zero":return 0
    if name=="one":return 1
    if name=="j":return j
    if name=="cursor":return j+7
    if name=="bound":return j+9
    if name=="base_src":return j+11
    if name=="base_dst":return j+13
    if name in ("add","sub"):
        a=evaluate_ast(node.children[0],x=x,j=j,depth=depth+1)
        b=evaluate_ast(node.children[1],x=x,j=j,depth=depth+1)
        return a+b if name=="add" else a-b
    if name in ("read_src","read_dst"):
        index=evaluate_ast(node.children[0],x=x,j=j,depth=depth+1)
        # Non-target addresses give distinct deterministic non-constant data.
        if name=="read_src":
            return x if index==j else 31+((3*index+j+x)%17)
        return -42+((7*index+2*j-x)%23)
    raise ValueError("NOT_AN_INT_EXECUTABLE_EXPRESSION")


class IndependentChecker:
    """The ONLY object that sees the reference program's source term."""
    def __init__(self,op:str,observations:BehavioralProblem):
        if op not in PRIVATE_DEV_REFERENCE:
            raise ValueError("UNAUTHORIZED_REFERENCE")
        self.op=op
        self.observations=observations
        self.solver_calls=0
        self.proof_ms=0.
        self.cache={}

    def __call__(self,candidate:AST):
        check_ast(candidate,bound_j=True,ceiling=80)
        expr=candidate.to_smt()
        if expr in self.cache:
            return self.cache[expr]
        successes=0
        for row_no,(src_value,reference_output) in enumerate(self.observations.observations):
            try:
                result=evaluate_ast(candidate,x=src_value,j=row_no)
            except (ValueError,OverflowError):
                result=None
            successes+=int(result==reference_output)
        fraction=successes/len(self.observations.observations)
        if fraction<1.0:
            result={"verdict":"CEX","validated_fraction":fraction,
                    "proof_verdict":"NOT_RUN","source_free_finite_examples":True}
            self.cache[expr]=result
            return result
        script="""(set-logic ALL)
(declare-const src (Array Int Int))
(declare-const dst (Array Int Int))
(declare-const j Int)
(declare-const cursor Int)
(declare-const bound Int)
(declare-const base_src Int)
(declare-const base_dst Int)
(assert (not (= """+expr+" "+PRIVATE_DEV_REFERENCE[self.op]+""")))
(check-sat)
"""
        start=time.perf_counter_ns()
        try:
            process=subprocess.run(["z3","-smt2","-in"],input=script,
                       capture_output=True,text=True,timeout=7,check=False)
            outputs=[s.strip() for s in process.stdout.splitlines() if s.strip()]
            verdict=outputs[0] if process.returncode==0 and outputs in (["unsat"],["sat"]) else "UNKNOWN"
        except subprocess.TimeoutExpired:
            verdict="UNKNOWN"
        self.proof_ms+=(time.perf_counter_ns()-start)/1e6
        self.solver_calls+=1
        if verdict=="unsat":
            result={"verdict":"PROVED","validated_fraction":1.,
                    "proof_verdict":"unsat","source_free_finite_examples":True,
                    "proved_AST_smt":expr,"original_reference_sha256":REFERENCE_SHA[self.op]}
        elif verdict=="sat":
            result={"verdict":"CEX","validated_fraction":fraction,
                    "proof_verdict":"sat","source_free_finite_examples":True}
        else:
            result={"verdict":"UNKNOWN","validated_fraction":0.,
                    "proof_verdict":"UNKNOWN","source_free_finite_examples":True}
        self.cache[expr]=result
        return result


def gp_candidates(max_size=4):
    """Same primitive AST language, typed bottom-up enumerator, no target hints."""
    terms={}
    leaves=[AST("Int",name) for name,children in PRODUCTIONS["Int"] if not children]
    terms[1]=leaves
    for k in range(2,max_size+1):
        new_nodes=[]
        for name,children in PRODUCTIONS["Int"]:
            if len(children)==1:
                for x in terms.get(k-1,[]):
                    new_nodes.append(AST("Int",name,(x,)))
            elif len(children)==2:
                for left_size in range(1,k-1):
                    right_size=k-1-left_size
                    for a in terms.get(left_size,[]):
                        for b in terms.get(right_size,[]):
                            new_nodes.append(AST("Int",name,(a,b)))
        terms[k]=new_nodes
    for k in sorted(terms):
        yield from terms[k]


def neural_attempt(op:str,episodes:int,seed:int,train:bool):
    observation=observe(op)
    model=TaskConditionalGenerator(seed=seed)
    model.set_observation(observation)
    checker=IndependentChecker(op,observation)
    first_hash=model.parameters_hash()
    started=time.perf_counter()
    found=None
    nvalid=0
    nwrong=0
    for episode in range(episodes):
        try:
            ast,history=model.sample(collision=True,failed_proofs=0,root_kind="Int",
                   bound_index=True,max_depth=4,max_nodes=80)
        except ValueError:
            nwrong+=1
            continue
        result=checker(ast)
        nvalid+=1
        if result["verdict"]=="PROVED":
            found={"episode":episode,"ast":ast.to_data(),"smt":ast.to_smt(),
                   "certificate":result}
            break
        if train:
            # Train only from *measured* examples and verifier outcomes.
            # The reference DSL program is not supplied to the actor.
            reward=(0.8*result["validated_fraction"]-0.3
                     if result["verdict"]=="CEX" else -0.15)
            model.apply_feedback(history,reward)
    return {
        "mode":"LEARNED_REINFORCE" if train else "UNTRAINED_ABLATION",
        "checked":nvalid,"invalid":nwrong,"budget":episodes,
        "proof_solver_calls":checker.solver_calls,
        "proof_z3_wall_ms":round(checker.proof_ms,3),
        "wall_seconds":round(time.perf_counter()-started,4),
        "starting_checkpoint_sha256":first_hash,
        "final_checkpoint_sha256":model.parameters_hash(),
        "actual_weight_updates":model.gradient_steps,
        "found":found
    }


def gp_attempt(op:str,limit:int):
    checker=IndependentChecker(op,observe(op))
    started=time.perf_counter()
    checked=0;found=None
    for candidate in gp_candidates(4):
        if checked>=limit:break
        checked+=1
        try:
            out=checker(candidate)
        except ValueError:
            continue
        if out["verdict"]=="PROVED":
            found={"candidate_number":checked,"smt":candidate.to_smt(),
                   "certificate":out}
            break
    return {
        "mode":"SAME_LANGUAGE_GP_ENUMERATION","checked":checked,
        "budget":limit,"proof_solver_calls":checker.solver_calls,
        "proof_z3_wall_ms":round(checker.proof_ms,3),
        "wall_seconds":round(time.perf_counter()-started,4),
        "found":found
    }


def run(out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_ORIGINAL_Q3_LEARNER_FIRST")
    out.mkdir(parents=True)
    experiments=[]
    for op in PRIVATE_DEV_REFERENCE:
        # GP gets the identical primitive grammar, 32 examples and oracle.
        classical=gp_attempt(op,limit=1000)
        # Deliberately avoid cost explosion: 1000 attempted samples per
        # arm. If GP saturates, never claim learner-exclusive Q3.
        trained=neural_attempt(op,episodes=1000,seed=83,train=True)
        ablation=neural_attempt(op,episodes=1000,seed=83,train=False)
        experiments.append({
           "source_free_dev_task":op,
           "observations_sha256":observe(op).sha(),
           "reference_program_sha256_for_verifier_only":REFERENCE_SHA[op],
           "same_language_GP":classical,
           "trained_own_weights":trained,
           "untrained_ablation":ablation,
           "learned_exclusive_proof":
               bool(trained["found"] and not classical["found"] and not ablation["found"])
        })
    report={
      "schema":"neumann.q3.observation-only-sourcefree-proof-learn-v1",
      "scientific_scope":"SOURCE_FREE_DEVELOPMENT_NOT_EXTERNAL_UNSEEN_ORIGINAL",
      "test_tasks":len(experiments),
      "classical_proven":sum(bool(e["same_language_GP"]["found"]) for e in experiments),
      "learned_proven":sum(bool(e["trained_own_weights"]["found"]) for e in experiments),
      "untrained_proven":sum(bool(e["untrained_ablation"]["found"]) for e in experiments),
      "learned_exclusive":sum(e["learned_exclusive_proof"] for e in experiments),
      "human_macro_answer_list_supplied_to_actor":False,
      "hidden_reference_AST_supplied_to_actor":False,
      "independent_all_domain_z3_required_for_proof":True,
      "source_free_development_only":True,
      "new_independent_external_originals":0,
      "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN",
      "experiments":experiments
    }
    (out/"FIRST_REPORT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="experiments"},indent=2,sort_keys=True))
    for row in experiments:
        print(row["source_free_dev_task"],
              "GP",row["same_language_GP"]["checked"],bool(row["same_language_GP"]["found"]),
              "NEURAL",row["trained_own_weights"]["checked"],bool(row["trained_own_weights"]["found"]),
              "UNTRAINED",row["untrained_ablation"]["checked"],bool(row["untrained_ablation"]["found"]))
    # This run is *evidence collection*. No synthetic result can pass Q3.
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    run(args.out)
