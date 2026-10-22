"""Source-only latent spacetime search: full deterministic 1-step CA trajectories.

NO original test outputs, hidden rule metadata, or source construction labels.
Use public benchmark generator class as a prior, not neural primitive discovery.
Fail-closed on missing rule values or any conflicting trajectories.
"""
import collections,itertools,time
from debruijn_structural_model import debruijn
from debruijn_index_full_key_early import infer_fast

KINDS=("full","sum","center_outer","center_hist")
def feature(w,kind):
    if kind=="full":return w
    if kind=="sum":return (sum(w),)
    middle=len(w)//2
    if kind=="center_outer":return (w[middle],sum(w)-w[middle])
    if kind=="center_hist":
        return (w[middle],tuple(sorted(collections.Counter(w[:middle]+w[middle+1:]).items())))
    raise ValueError(kind)

def obtain_rules(pairs,k,r):
    n=2*r+1;full_windows=itertools.product(range(k),repeat=n)
    all_windows=tuple(full_windows)
    models=[]
    for kind in KINDS:
        table={};valid=True;seen=0
        for pair in pairs:
            x=pair["input"];y=pair["output"]
            if len(x)!=len(y) or len(x)<n:
                valid=False;break
            for i in range(r,len(x)-r):
                window=tuple(x[i-r:i+r+1])
                key=feature(window,kind);target=y[i]
                if key in table and table[key]!=target:
                    valid=False;break
                table[key]=target;seen+=1
            if not valid:break
        if not valid or not seen:continue
        if any(feature(w,kind) not in table for w in all_windows):continue
        full={w:table[feature(w,kind)] for w in all_windows}
        models.append((kind,full))
    return models

def roll(start,rule,r,steps=26):
    cur=tuple(start);n=len(cur)
    all_states=[cur]
    for _ in range(steps):
        cur=tuple(rule[tuple(cur[(i+j)%n] for j in range(-r,r+1))] for i in range(n))
        all_states.append(cur)
    return all_states

def phase_candidates(fragment,state):
    n=len(state);L=len(fragment)
    # Source slices may exceed the full base ring length and wrap repeatedly.
    prefix=fragment[:min(L,n)]
    candidates=[i for i in range(n) if all(state[(i+j)%n]==v for j,v in enumerate(prefix))]
    if L>n:
        candidates=[i for i in candidates if all(state[(i+j)%n]==v for j,v in enumerate(fragment))]
    return candidates

def span(state,pos,size):
    n=len(state)
    return tuple(state[(pos+j)%n] for j in range(size))

def recover(task):
    begin=time.process_time()
    pairs=task["train"];query=task["query"]
    if not query or len(pairs)!=5:
        return {"status":"ABSTAIN_UNSUPPORTED_INPUT","prediction":None}
    all_symbols=list(query)
    for pair in pairs:all_symbols.extend(pair["input"]);all_symbols.extend(pair["output"])
    if not all_symbols or any(not isinstance(v,int) or v<0 or v>5 for v in all_symbols):
        return {"status":"ABSTAIN_SYMBOLS","prediction":None}
    k_min=max(2,max(all_symbols)+1)
    possibilities=set();records=[];attempted_programs=0;complete_tables=0
    for k in range(k_min,7):
        for r in (1,2,3):
            W=2*r+1
            if k**W>512:continue
            for kind,rule in obtain_rules(pairs,k,r):
                complete_tables+=1
                history=roll(debruijn(k,W),rule,r)
                # Every demonstrated source pair must be represented on ONE global
                # cyclic space-time diagram, though each source may have its own time.
                supports=True
                for pair in pairs:
                    x=pair["input"];y=pair["output"];exists=False
                    for t in range(25):
                        for phase in phase_candidates(x,history[t]):
                            if span(history[t+1],phase,len(y))==tuple(y):
                                exists=True;break
                        if exists:break
                    if not exists:
                        supports=False;break
                if not supports:continue
                attempted_programs+=1
                answers=set()
                for t in range(25):
                    for phase in phase_candidates(query,history[t]):
                        answers.add(span(history[t+1],phase,len(query)))
                if not answers:continue
                if len(answers)>1:
                    return {"status":"ABSTAIN_AMBIGUOUS_SPACETIME","prediction":None,
                            "viable_models":attempted_programs,"candidate_outputs":len(answers),
                            "cpu_s":time.process_time()-begin}
                solution=next(iter(answers))
                possibilities.add(solution)
                records.append({"k":k,"radius":r,"rule_family":kind})
    if not possibilities:
        return {"status":"ABSTAIN_NO_GLOBAL_RECONSTRUCTION","prediction":None,
                "full_rule_candidates":complete_tables,"viable_global_models":attempted_programs,
                "cpu_s":time.process_time()-begin}
    if len(possibilities)>1:
        return {"status":"ABSTAIN_GENERATOR_DISAGREEMENT","prediction":None,
                "viable_models":attempted_programs,"possible_outputs":len(possibilities),
                "cpu_s":time.process_time()-begin}
    return {"status":"GLOBAL_SPACETIME_RECONSTRUCTED","prediction":list(next(iter(possibilities))),
            "viable_global_models":attempted_programs,"source_rules":records,
            "full_rule_candidates":complete_tables,"cpu_s":time.process_time()-begin}

def combined(task):
    start=time.process_time()
    baseline=infer_fast(task)
    if baseline.get("prediction") is not None:
        return {"base":baseline,"reconstructed":{"status":"SKIP_BASE_ALREADY_PREDICTED","prediction":None},
                "combined_prediction":baseline["prediction"],"route":"BASE",
                "cpu_s":time.process_time()-start}
    new=recover(task)
    return {"base":baseline,"reconstructed":new,
            "combined_prediction":new.get("prediction"),
            "route":"SPACETIME" if new.get("prediction") is not None else "UNKNOWN",
            "cpu_s":time.process_time()-start}
