"""Q3 FIRST: heterogeneous types on unbounded-vs-finite state tasks.

Target formula generators here are hidden from source inventor module.
Train: only whole input/output sequences. Source knows no family labels.
Results report every wrong or abstained target; no code tuned by TEST gold.
"""
from __future__ import annotations
import argparse
import json
import random
import time
from pathlib import Path

from research.q3.heterogeneous_representation_invention import (
    invent_representation,HeterogeneousLanguage,
)
from research.q3.auto_state_type_first import (
    named_machine,samples_whole_word,output_of,
)


def arithmetic_train(fn,initial,seed,n=80,alphabet=2):
    rng=random.Random(seed)
    examples=[]
    for j in range(n):
        word=[rng.randrange(alphabet)
              for _ in range(rng.randrange(1,11))]
        state=initial;out=[]
        for symbol in word:
            state=fn(state,symbol)
            out.append(state)
        examples.append((word,out))
    return examples


def arithmetic_heldout(fn,initial,seed,alphabet=2,n=24):
    rng=random.Random(seed)
    examples=[]
    for j in range(n):
        word=[rng.randrange(alphabet)
              for _ in range(rng.randrange(11,23))]
        state=initial;out=[]
        for symbol in word:
            state=fn(state,symbol)
            out.append(state)
        examples.append((word,out))
    return examples


def study_arithmetic(name,fn,initial,seed):
    train=arithmetic_train(fn,initial,seed)
    chosen,trace=invent_representation(train)
    held=arithmetic_heldout(fn,initial,seed+100007)
    if chosen is None:
        return {"name":name,"status":"ABSTAIN","total":len(held),
                "exact":0,"candidate_trace":trace}
    kind,program,cost=chosen
    passes=sum(program.apply(x)==y for x,y in held)
    training_values={v for x,y in train for v in y}
    new_value_success=sum(
        program.apply(x)==y and bool(set(y)-training_values)
        for x,y in held)
    return {"name":name,"status":"COMPILED",
            "chosen_new_representation":kind,
            "generated_operator_AST":program.ast()
              if kind=="SymbolicIntegerState" else program.to_ast(),
            "chosen_description_cost":cost,
            "candidate_trace":trace,
            "exact":passes,"total":len(held),
            "heldout_correct_with_new_unseen_output_symbols":new_value_success,
            "finite_state_model_cannot_emit_new_unseen_symbols":True
              if new_value_success>0 else False}


def study_finite(name,alphabet,seed):
    machine=named_machine(name)
    train=samples_whole_word(machine,seed,alphabet)
    chosen,trace=invent_representation(train)
    rng=random.Random(seed+100007)
    tests=[]
    for _ in range(24):
        word=[rng.randrange(alphabet) for i in range(rng.randrange(11,23))]
        tests.append((word,output_of(machine,word)))
    if chosen is None:
        return {"name":name,"status":"ABSTAIN","exact":0,
                "total":24,"candidate_trace":trace}
    kind,program,cost=chosen
    return {"name":name,"status":"COMPILED","total":24,
            "exact":sum(program.apply(x)==y for x,y in tests),
            "chosen_new_representation":kind,
            "generated_operator_AST":program.ast()
                 if kind=="SymbolicIntegerState" else program.to_ast(),
            "chosen_description_cost":cost,"candidate_trace":trace}


def persisted_language_test():
    language=HeterogeneousLanguage()
    steps=[]
    fn=lambda p,x:p+x
    tasks=[
      ("sum",arithmetic_train(fn,0,70551)),
      ("sum",arithmetic_train(fn,0,70552)),
      ("mod3",samples_whole_word(named_machine("running_mod3"),7131,2)),
      ("mod3",samples_whole_word(named_machine("running_mod3"),7132,2)),
      ("balance",arithmetic_train(lambda p,x:p+2*x-1,0,73551)),
      ("balance",arithmetic_train(lambda p,x:p+2*x-1,0,73552)),
    ]
    for label,example in tasks:
        name,op,mode,kind=language.solve(example)
        steps.append({"family":label,"mode":mode,"kind":kind,"symbol":name,
                      "original_train_exact":op is not None and
                        all(op.apply(x)==y for x,y in example)})
    saved=language.dump()
    if HeterogeneousLanguage.load(saved).dump()!=saved:
        raise RuntimeError("generated heterogeneous language lost semantics")
    return saved,steps


def run(out:Path,extra_unknown=32):
    if out.exists():raise ValueError("NO_OVERWRITE_HETEROGENEOUS_FIRST")
    out.mkdir(parents=True)
    t0=time.perf_counter()
    named=[
      ("running_count",lambda p,x:p+x,0),
      ("running_product",lambda p,x:p*x,1),
      ("signed_balance",lambda p,x:p+2*x-1,0),
      ("double_accumulator",lambda p,x:2*p+x,0),
      ("running_decrement",lambda p,x:p-x,0),
      ("weighted_sum",lambda p,x:p+2*x,0)
    ]
    results=[]
    for i,(label,fn,initial) in enumerate(named):
        results.append(study_arithmetic(label,fn,initial,100+i*17))
    generator=random.Random(98232)
    for i in range(24+extra_unknown):
        a=generator.choice((-1,0,1,2))
        b=generator.choice((0,1,2))
        c=generator.choice((-1,0,1))
        initial=generator.choice((0,1))
        fn=lambda p,x,a=a,b=b,c=c:a*p+b*x+c
        seed=3000+i*37 if i<24 else 200000+(i-24)*131
        results.append(study_arithmetic(
            "unseen_affine_law_"+str(i),fn,initial,seed))
    for j,(name,alphabet) in enumerate((
        ("running_parity",2),("running_mod3",2),("resetting_parity",3))):
        results.append(study_finite(name,alphabet,5500+j*19))
    saved,events=persisted_language_test()
    (out/"GROWN_HETEROGENEOUS_LANGUAGE.json").write_text(
        json.dumps(saved,indent=2,sort_keys=True)+"\n")
    total=sum(x["total"] for x in results)
    exact=sum(x["exact"] for x in results)
    stats={
       "problems":len(results),
       "problems_all_heldout_exact":sum(
           x["exact"]==x["total"] for x in results),
       "heldout_total":total,"heldout_exact":exact,
       "invented_integer_state_programs":sum(
           x.get("chosen_new_representation")=="SymbolicIntegerState"
           for x in results),
       "invented_finite_variant_programs":sum(
           x.get("chosen_new_representation")=="FiniteVariantState"
           for x in results),
       "correct_new_out_of_training_value_tests":sum(
           x.get("heldout_correct_with_new_unseen_output_symbols",0)
           for x in results),
       "failed_or_partially_wrong":sum(
           x["exact"]!=x["total"] for x in results),
       "registry_generated_type_definitions":len(saved["definitions"]),
       "registry_invention_events":sum(e["mode"]=="invent" for e in events),
       "registry_reuse_events":sum(e["mode"]=="reuse" for e in events),
    }
    report={
       "schema":"neumann.q3.heterogeneous-type-first.v1",
       "human_bootstrap_two_representation_constructor_families":True,
       "no_task_specific_operator_was_passed_to_inventor":True,
       "generator_targets_only_in_evaluator_not_solver":True,
       "same_frozen_model_selection_policy_across_finite_and_integer":True,
       "source_and_test_input_seeds_disjoint":True,
       "Q3_GLOBAL":"OPEN","Q4":"OPEN","Q6":"OPEN",
       "elapsed_s":round(time.perf_counter()-t0,5),
       "summary":stats,"registry":events,"rows":results}
    (out/"FIRST.json").write_text(
        json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("Q3_HETEROGENEOUS_FIRST_SUMMARY",json.dumps(stats,sort_keys=True),flush=True)
    for rec in results:
        if rec["exact"]!=rec["total"]:
            print("INCOMPLETE_NEW_REPRESENTATION",rec["name"],
                  rec["exact"],"/",rec["total"],
                  rec.get("chosen_new_representation"),flush=True)
    print("REGISTRY",json.dumps(events,sort_keys=True),flush=True)
    print("GLOBAL_Q3_OPEN__NOT_UNRESTRICTED_CREATION",flush=True)
    return report


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--extra-unknown",type=int,default=32)
    a=ap.parse_args()
    run(a.out,a.extra_unknown)
