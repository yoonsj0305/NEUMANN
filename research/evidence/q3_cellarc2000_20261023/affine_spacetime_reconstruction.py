"""Infer sparse affine CA dynamics entirely from original source demonstrations.

Source generator family is NOT given. Enumerate small support affine maps
F(x)=b+sum(a_j*x_j) mod k for radius <=3 with <=3 active coefficients,
consistent with every observed demonstration INTERIOR. Reconstruct canonical
full space-time diagram and verify every source demonstration before query.
This is a human-authored *family* with task-local automatic coefficients,
not neural invention or full CA class completeness.
"""
import itertools,time
from debruijn_structural_model import debruijn
from latent_spacetime_reconstruction import combined,roll,phase_candidates,span

MAX_SOURCE_FIT_AFFINE_RULES=32

def affine_source_models(pairs,k,r):
    width=2*r+1
    samples=[]
    for pair in pairs:
        x,y=pair["input"],pair["output"]
        if len(x)!=len(y) or len(x)<width:return []
        samples.extend((tuple(x[i-r:i+r+1]),y[i]) for i in range(r,len(x)-r))
    if not samples:return []
    positions=range(width)
    all_models=[]
    # Original published sparse affine family has one to three nonzero
    # positions, and an optional intercept. Constant case included as control.
    for nterms in range(0,4):
        for support in itertools.combinations(positions,nterms):
            for coeff in itertools.product(range(1,k),repeat=nterms):
                contributions=[sum(a*row[j] for j,a in zip(support,coeff))%k for row,_ in samples[:3]]
                for bias in range(k):
                    if any((x+bias)%k!=y for x,(_,y) in zip(contributions,samples[:3])):continue
                    if all((bias+sum(a*row[j] for j,a in zip(support,coeff)))%k==y for row,y in samples):
                        all_models.append((support,coeff,bias))
                        if len(all_models)>MAX_SOURCE_FIT_AFFINE_RULES:
                            return None  # Fail-closed incomplete enumeration.
    return all_models

def recover_affine(task):
    begin=time.process_time()
    pairs=task["train"];q=task["query"]
    if len(pairs)!=5 or not q:
        return {"status":"ABSTAIN_UNSUPPORTED","prediction":None}
    observed=q+list(v for e in pairs for a in ("input","output") for v in e[a])
    if any(not isinstance(v,int) or v<0 or v>5 for v in observed):
        return {"status":"ABSTAIN_SYMBOL_DOMAIN","prediction":None}
    min_k=max(2,max(observed)+1)
    candidates=0;source_fitted=0;accepted=0;possible=set();overflow=0
    for k in range(min_k,7):
        for r in (1,2,3):
            W=2*r+1
            if k**W>512:continue
            assignments=affine_source_models(pairs,k,r)
            if assignments is None:
                overflow+=1;continue
            source_fitted+=len(assignments)
            cycle=debruijn(k,W)
            all_windows=tuple(itertools.product(range(k),repeat=W))
            for support,coeff,bias in assignments:
                candidates+=1
                table={x:(bias+sum(a*x[j] for j,a in zip(support,coeff)))%k for x in all_windows}
                history=roll(cycle,table,r,steps=25)
                consistent=True
                for ex in pairs:
                    x=ex["input"];y=tuple(ex["output"]);found=False
                    for t in range(25):
                        for phase in phase_candidates(x,history[t]):
                            if span(history[t+1],phase,len(y))==y:
                                found=True;break
                        if found:break
                    if not found:
                        consistent=False;break
                if not consistent:continue
                accepted+=1;found_predictions=set()
                for t in range(25):
                    for phase in phase_candidates(q,history[t]):
                        found_predictions.add(span(history[t+1],phase,len(q)))
                if len(found_predictions)>1:
                    return {"status":"ABSTAIN_TIME_OR_PHASE_AMBIGUITY","prediction":None,
                            "admitted_models":accepted,"candidate_predictions":len(found_predictions),
                            "cpu_s":time.process_time()-begin}
                if found_predictions:possible.update(found_predictions)
    if overflow:
        return {"status":"ABSTAIN_TOO_MANY_SOURCE_AFFINE_MODELS","prediction":None,
                "source_models_truncated_groups":overflow,"cpu_s":time.process_time()-begin}
    if len(possible)!=1:
        return {"status":"ABSTAIN_NO_UNIQUE_AFFINE_TRAJECTORY","prediction":None,
                "possible_outputs":len(possible),"source_fit_models":source_fitted,
                "trajectory_admitted_models":accepted,"cpu_s":time.process_time()-begin}
    return {"status":"SOURCE_FITTED_SPARSE_AFFINE_TIME_RECONSTRUCTED",
            "prediction":list(next(iter(possible))),"source_fit_models":source_fitted,
            "trajectory_admitted_models":accepted,
            "cpu_s":time.process_time()-begin}

def combined_with_affine(task):
    begin=time.process_time()
    first=combined(task)
    if first["combined_prediction"] is not None:
        return {"prior":first,"affine":{"status":"SKIP_ALREADY_PREDICTED","prediction":None},
                "prediction":first["combined_prediction"],"route":"PRIOR",
                "cpu_s":time.process_time()-begin}
    new=recover_affine(task)
    return {"prior":first,"affine":new,"prediction":new.get("prediction"),
            "route":"AFFINE" if new.get("prediction") is not None else "UNKNOWN",
            "cpu_s":time.process_time()-begin}
