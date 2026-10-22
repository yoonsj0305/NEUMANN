"""Source-only phase/output consistency and stochastic-query guard for published
CellARC generator. No test solution, hidden class, true radius, or metadata read.
The query guard is explicitly HEURISTIC, not a correctness certificate.
"""
from debruijn_structural_model import debruijn,infer,occurs_on_cycle

def phase_consistency(task,info):
    k,W=int(info["k"]),int(info["W"])
    cycle=debruijn(k,W)
    L=len(cycle)
    lookup={tuple(cycle[(p+j)%L] for j in range(W)):p for p in range(L)}
    same_y={}
    source_overlap=0
    phases=[]
    for demo in task["train"]:
        x,y=demo["input"],demo["output"]
        if len(x)<W or len(x)!=len(y):
            return {"valid":False,"reason":"SHORT_OR_BAD_SEGMENT","source_overlap":source_overlap}
        p=lookup.get(tuple(x[:W]))
        if p is None or any(x[i]!=cycle[(p+i)%L] for i in range(len(x))):
            return {"valid":False,"reason":"NON_CANONICAL_INPUT","source_overlap":source_overlap}
        phases.append(p)
        for i,val in enumerate(y):
            global_cell=(p+i)%L
            if global_cell in same_y:
                source_overlap+=1
                if same_y[global_cell]!=val:
                    return {"valid":False,"reason":"PHASE_ALIGNED_OUTPUT_CONTRADICTION",
                            "source_overlap":source_overlap}
            else:
                same_y[global_cell]=val
    return {"valid":True,"reason":"PHASE_OUTPUT_COHERENT",
            "source_overlap":source_overlap,"known_absolute_cells":len(same_y),
            "phases":phases}

def source_only_policy_comparison(task):
    original=infer(task)
    variants={"baseline":original}
    info=original.get("structural_model")
    train_values=[v for d in task["train"] for v in d["output"]]
    alphabet_pass=(not info) or (train_values and max(train_values)<int(info["k"]))
    structural_pass=True
    reason="NOT_UNIQUE_STRUCTURE"
    qmatch=False
    phase_data=None
    if info:
        phase_data=phase_consistency(task,info)
        structural_pass=phase_data["valid"]
        reason=phase_data["reason"]
        qmatch=occurs_on_cycle(task["query"],debruijn(int(info["k"]),int(info["W"])))
    allowed={
        "source_alphabet":bool(alphabet_pass),
        "source_alphabet_plus_phase":bool(alphabet_pass and structural_pass),
        "source_alphabet_plus_query":bool(alphabet_pass and not qmatch),
        "source_all_three":bool(alphabet_pass and structural_pass and not qmatch)
    }
    for label,admit in allowed.items():
        variants[label]=original if admit else {
            "status":"ABSTAIN_SOURCE_STRUCTURE_CONTRADICTION",
            "reason":("SOURCE_ALPHABET" if not alphabet_pass else
                      "PHASE_OUTPUT_CONTRADICTION" if not structural_pass else
                      "RANDOM_QUERY_MATCHES_CANONICAL"),
            "prediction":None}
    return {"variants":variants,
            "source_phase_audit":phase_data,
            "query_canonical_subword":qmatch,
            "source_alphabet_pass":alphabet_pass}
