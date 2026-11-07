"""Q3 scientific boundary: induction of NEW algebraic types on unfamiliar I/O.

Synthetic evaluator deliberately separate from the generic type inventor:
the learner never reads family implementations, state count, transitions, or
random generator parameters. No ARC task IDs are opened by this experiment.

Families A: prefix-observed, variable-length emitted output, 42 tasks.
Families B: only whole-word I/O, equal-length output, 40 tasks.
Families C: fresh independently seeded whole-word random machines.
No claim of arbitrary new primitive invention; finite-state hypothesis
class and safe interpreter were HUMAN implemented.
"""
from __future__ import annotations
import argparse
import json
import random
import time
from pathlib import Path
from research.q3.autonomous_state_type_invention import (
    SelfExtendingLanguage,learn_new_type,learn_from_complete_io,
    elementwise_impossibility_witness,fingerprint,
)


def random_machine(seed,states,alphabet,variable_output):
    r=random.Random(seed)
    machine={}
    for q in range(states):
        for a in range(alphabet):
            if variable_output:
                chunk=tuple(r.randrange(3) for _ in range(r.randrange(3)))
            else:
                chunk=(r.randrange(3),)
            machine[q,a]=(chunk,r.randrange(states))
    return machine


def named_machine(name):
    if name=="running_parity":
        return {(q,a):((q^a,),q^a)
                for q in range(2) for a in range(2)}
    if name=="running_mod3":
        return {(q,a):(((q+a)%3,),((q+a)%3))
                for q in range(3) for a in range(2)}
    if name=="delete_consecutive_duplicates":
        return {(q,a):((a,) if q!=a+1 else (),a+1)
                for q in range(3) for a in range(2)}
    if name=="duplicate_ones":
        return {(0,a):((a,)*(1+a),0) for a in range(2)}
    if name=="last_symbol_delayed":
        return {(q,a):((0 if q==2 else q,),a)
                for q in range(3) for a in range(2)}
    if name=="resetting_parity":
        return {(q,a):(((0 if a==2 else q^a),),
                       (0 if a==2 else q^a))
                for q in range(2) for a in range(3)}
    raise ValueError("unknown heldout family")


def output_of(machine,word):
    state=0;outputs=[]
    for symbol in word:
        chunk,state=machine[state,symbol]
        outputs.extend(chunk)
    return outputs


def samples_prefix_observed(machine,seed,alphabet):
    random_gen=random.Random(seed)
    words={()}
    for _ in range(18):
        length=random_gen.randrange(7,11)
        word=tuple(random_gen.randrange(alphabet)
                   for i in range(length))
        for j in range(1,length+1):words.add(word[:j])
    return [(list(w),output_of(machine,w))
            for w in sorted(words,key=lambda w:(len(w),w))]


def samples_whole_word(machine,seed,alphabet):
    rng=random.Random(seed)
    words=[]
    for _ in range(80):
        n=rng.randrange(1,13)
        word=[rng.randrange(alphabet) for _ in range(n)]
        words.append((word,output_of(machine,word)))
    return words


def heldout(machine,seed,alphabet,known,number=24):
    generator=random.Random(seed)
    previous={tuple(word) for word,out in known}
    cases=[]
    for _ in range(number):
        for attempts in range(20):
            size=generator.randrange(16,41)
            word=[generator.randrange(alphabet)
                  for i in range(size)]
            if tuple(word) not in previous:break
        cases.append((word,output_of(machine,word)))
    return cases


def evaluate_one(label,machine,alphabet,seed,mode):
    train=(samples_prefix_observed(machine,seed,alphabet)
           if mode=="prefix_observed"
           else samples_whole_word(machine,seed,alphabet))
    first=time.perf_counter()
    op,merges=(learn_new_type(train) if mode=="prefix_observed"
               else learn_from_complete_io(train))
    seconds=round(time.perf_counter()-first,6)
    tests=heldout(machine,seed+400007,alphabet,train)
    hits=sum(op.apply(x)==y for x,y in tests)
    internal=op if mode=="prefix_observed" else op.internal
    return {
        "label":label,"source_mode":mode,
        "original_training_pairs":len(train),
        "inferred_state_count":internal.num_states,
        "inferred_transition_count":len(internal.transitions),
        "learned_language_AST":op.to_ast(),
        "new_type_name":op.to_ast()[1],
        "model_code_compiled":True,
        "source_state_type_or_rules_provided_to_learner":False,
        "heldout_count":len(tests),"heldout_exact":hits,
        "all_heldout_exact":hits==len(tests),
        "prior_elementwise_language_witness":
            elementwise_impossibility_witness(train),
        "synthesis_merge_attempts":merges,
        "source_induction_wall_s":seconds,
    }


def study_registry():
    """One mutable language; 3 inventions then 3 true reuse events."""
    grammar=SelfExtendingLanguage()
    events=[]
    for i,(label,alphabet) in enumerate((
        ("running_parity",2),("running_parity",2),
        ("running_mod3",2),("running_mod3",2),
        ("resetting_parity",3),("resetting_parity",3)
    )):
        machine=named_machine(label)
        train=samples_whole_word(machine,1200+i*11,alphabet)
        sym,compiled,kind=grammar.solve(train)
        test=heldout(machine,47000+i*23,alphabet,train)
        exact=sum(compiled.apply(x)==y for x,y in test)
        events.append({"problem":label,"mode":kind,
                       "symbol":sym,
                       "state_count":compiled.internal.num_states,
                       "heldout_exact":exact,"heldout_total":len(test)})
    record=grammar.dump()
    restored=SelfExtendingLanguage.load(record)
    if restored.dump()!=record:
        raise RuntimeError("type registry failed durable round trip")
    if sum(e["mode"]=="invent" for e in events)!=3 or \
       sum(e["mode"]=="reuse" for e in events)!=3:
        raise RuntimeError("no repeated autonomous invention and reuse")
    if any(e["heldout_exact"]!=e["heldout_total"] for e in events):
        raise RuntimeError("invent/reuse did not generalize")
    return record,events


def run(out:Path,random_extra=48):
    if out.exists():raise ValueError("NO_OVERWRITE_ORIGINAL_FIRST")
    out.mkdir(parents=True)
    t0=time.perf_counter()
    data=[]
    variable_names=(
        "running_parity","running_mod3",
        "delete_consecutive_duplicates","duplicate_ones",
        "last_symbol_delayed","resetting_parity")
    for idx,name in enumerate(variable_names):
        alphabet=3 if name=="resetting_parity" else 2
        data.append(evaluate_one(
            name,named_machine(name),alphabet,13+idx*7,
            "prefix_observed"))
    for idx in range(36):
        states=2+(idx%3);alphabet=2+(idx%2)
        machine=random_machine(100000+idx*97,states,alphabet,True)
        data.append(evaluate_one(
            "unknown_variable_rule_"+str(idx),machine,alphabet,
            20000+idx*41,"prefix_observed"))
    # Whole-sequence I/O ONLY: no intermediate supervision.
    whole_names=(
        "running_parity","running_mod3",
        "last_symbol_delayed","resetting_parity")
    for idx,name in enumerate(whole_names):
        alphabet=3 if name=="resetting_parity" else 2
        data.append(evaluate_one(
            name,named_machine(name),alphabet,800+idx*17,
            "whole_input_output"))
    for idx in range(36+random_extra):
        states=2+(idx%3);alphabet=2+(idx%2)
        # Independent external-seed bucket not visible to generator.
        seed=(700000+idx*67 if idx<36
              else 910003+(idx-36)*101)
        training_seed=(30000+idx*43 if idx<36
                       else 90500+(idx-36)*113)
        machine=random_machine(seed,states,alphabet,False)
        data.append(evaluate_one(
            "unknown_full_io_rule_"+str(idx),machine,alphabet,
            training_seed,"whole_input_output"))
    registry,events=study_registry()
    (out/"GROWN_ALGEBRAIC_LANGUAGE.json").write_text(
        json.dumps(registry,sort_keys=True,indent=2)+"\n")
    bymode={}
    for mode in ("prefix_observed","whole_input_output"):
        rows=[row for row in data if row["source_mode"]==mode]
        bymode[mode]={
            "tasks":len(rows),
            "exact_tasks":sum(r["all_heldout_exact"] for r in rows),
            "heldout_total":sum(r["heldout_count"] for r in rows),
            "heldout_exact":sum(r["heldout_exact"] for r in rows),
            "outside_old_elementwise_map_witnesses":sum(
                r["prior_elementwise_language_witness"]
                 ["old_elementwise_map_impossible"] for r in rows),
            "learned_operator_definitions":len({
                fingerprint(r["learned_language_AST"]) for r in rows}),
            "inferred_state_counts":sorted({
                r["inferred_state_count"] for r in rows})
        }
    report={
        "schema":"neumann.q3.self-extending-new-algebraic-types-original-first.v1",
        "human_supplied_generic_finite_state_model_class":True,
        "human_supplied_experiment_generators":True,
        "no_per_family_code_in_type_inventor":True,
        "output_only_after_full_word_training_supported":True,
        "new_type_defined_by_quotient_of_observational_prefix_graph":True,
        "actual_executable_transition_rules_learned":True,
        "model_state_cardinality_not_provided_to_learner":True,
        "cross_task_language_history":events,
        "persistent_generated_language_schema":registry["schema"],
        "source_state_type_or_rules_never_given_to_inventor":True,
        "summary":bymode,
        "machine_time_s":round(time.perf_counter()-t0,5),
        "Q3_GLOBAL":"OPEN","Q4":"OPEN","Q6":"OPEN",
        "rows":data
    }
    (out/"FIRST.json").write_text(
        json.dumps(report,sort_keys=True,indent=2)+"\n")
    for mode in bymode:
        print("ACTUAL_Q3_NEW_TYPE",mode,json.dumps(bymode[mode],sort_keys=True),
              flush=True)
    print("REGISTRY_EVENTS",json.dumps(events,sort_keys=True),flush=True)
    print("GLOBAL_Q3_OPEN_TRUE_AUTONOMOUS_GENERIC_CREATIVITY_NOT_PROVEN",
          flush=True)
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--extra-unknown",default=48,type=int)
    a=p.parse_args()
    run(a.out,a.extra_unknown)
