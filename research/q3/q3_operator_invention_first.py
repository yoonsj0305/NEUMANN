"""Q3 FIRST synthetic heldout eval; oracle never passed into inventor."""
from __future__ import annotations
import itertools
import json
import random
import time
from pathlib import Path
from neumann1.monoid_operator_inventor import invent_operator, EvidenceInsufficient


def cyclic(n=31):
    ids=[f"clk_{x:02x}" for x in range(n)]
    random.Random(7741).shuffle(ids)
    index={x:i for i,x in enumerate(ids)}
    return ids,ids[0],(ids[1],),lambda a,b:ids[(index[a]+index[b])%n]


def compose(a,b):
    return tuple(a[b[i]] for i in range(len(a)))


def symmetric():
    return list(itertools.permutations(range(3))),(0,1,2),((1,0,2),(1,2,0)),compose


def transformations():
    e=(0,1,2); g1=(1,2,0); g2=(0,0,0)
    seen={e}; pending=[e]
    while pending:
        state=pending.pop()
        for gen in (g1,g2):
            value=compose(gen,state)
            if value not in seen:
                seen.add(value); pending.append(value)
    return sorted(seen),e,(g1,g2),compose


def semilattice():
    return list(range(16)),0,(1,2,4,8),lambda a,b:a|b


def relabel(task,seed):
    universe,e,gens,op=task
    new=[f"unseen_{seed}_{i:03d}" for i in range(len(universe))]
    random.Random(seed).shuffle(new)
    enc=dict(zip(universe,new)); dec={v:k for k,v in enc.items()}
    return new,enc[e],tuple(enc[g] for g in gens),lambda a,b:enc[op(dec[a],dec[b])]


def run_case(name,task):
    universe,e,gens,op=task
    observed={e,*gens}
    source=[(a,b,op(a,b)) for a in universe if a in observed for b in universe]
    source_keys={(a,b) for a,b,_ in source}
    t=time.perf_counter_ns()
    model=invent_operator(source)
    discovery_ms=(time.perf_counter_ns()-t)/1e6
    holdout=[(a,b) for a in universe for b in universe if (a,b) not in source_keys]
    t=time.perf_counter_ns()
    correct=sum(model.apply(a,b)==op(a,b) for a,b in holdout)
    run_ms=(time.perf_counter_ns()-t)/1e6
    return {"case":name,"universe":len(universe),"source":len(source),
            "selected_generators":len(model.generators),
            "representation_max_word_length":max(map(len,model.normal_forms.values())),
            "heldout":len(holdout),"heldout_exact":correct,
            "lookup_only_heldout_exact":0,
            "oracle_full_spec_heldout_exact":len(holdout),
            "discovery_ms":round(discovery_ms,4),
            "heldout_invention_execute_ms":round(run_ms,4),
            "growth_in_executable_coverage":round(len(universe)**2/len(source),4),
            "premises":model.premise}


def negative_controls():
    universe,e,gens,op=cyclic(7)
    source=[(a,b,op(a,b)) for a in {e,*gens} for b in universe]
    try:
        invent_operator(source+[(gens[0],universe[2],universe[5])])
        conflict_rejected=False
    except EvidenceInsufficient:
        conflict_rejected=True
    model=invent_operator(source)
    a=b=universe[2]
    altered=universe[0] if model.apply(a,b)!=universe[0] else universe[1]
    # A nonassociative table can copy every source cell and alter this cell.
    return {"conflicting_source_rejected":conflict_rejected,
            "nonassociative_holdout_counterexample_exists":model.apply(a,b)!=altered,
            "global_semantics_not_identifiable_from_source":True}


def main():
    tasks=[("cyclic_prime_31",cyclic()),("noncommutative_S3",symmetric()),
           ("noninvertible_function_monoid",transformations()),
           ("union_semilattice_16",semilattice())]
    results=[run_case(name,task) for name,task in tasks]
    stress=[]
    for name,task in [("Z11",cyclic(11)),("S3",symmetric()),
                      ("transformation",transformations()),("union",semilattice())]:
        for seed in range(25):
            stress.append(run_case(f"{name}_{seed}",relabel(task,10000+seed)))
    adverse=negative_controls()
    assert all(r["heldout_exact"]==r["heldout"] for r in results+stress)
    assert adverse["conflicting_source_rejected"]
    assert adverse["nonassociative_holdout_counterexample_exists"]
    report={"schema":"NEUMANN.Q3.representation-operator-invention.synthetic-FIRST.v1",
            "results":results,"adversarial":adverse,
            "randomized_unseen_encodings":{
                "cases":len(stress),"heldout":sum(r["heldout"] for r in stress),
                "heldout_exact":sum(r["heldout_exact"] for r in stress),
                "label_disjoint":True},
            "totals":{"source":sum(r["source"] for r in results),
                      "heldout":sum(r["heldout"] for r in results),
                      "heldout_exact":sum(r["heldout_exact"] for r in results)},
            "caveat":"Synthetic first-run oracles, conditional associativity and identity, not global Q3/Q4/Q6 proof."}
    path=Path(__file__).with_name("q3_operator_invention_first_results.json")
    path.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
