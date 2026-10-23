"""Hidden 2x2 reversible local rule from FULL source demonstration grid pairs.

In the genuine benchmark, test task rule is given. Our controlled NEW condition
redacts it. A separate data-prep process creates demonstration (state_t,
state_{t+1}) pairs by replaying the true rule; no rule permutations, true answer
or metadata appear in the solver's source JSON. The chosen 2x2 block model class
is provided and is NOT autonomously discovered.

For any source calibration, direct 2x2 training pairs identify a partial
16-element permutation. Bijectivity makes the remaining target values a
permutation of unused symbols, enumerated COMPLETELY if <= max_unknown.
For each consistent rule, exactly enumerate 2^16 initial candidate states and
check every source test observation. Admit a test prediction only if ALL rule
completions that fit calibration also agree on the same single initial state.
If a completion allows multiple states or no bounded exhaustive rule enumeration
is possible, abstain. Never use the hidden benchmark reference rule at infer time.
"""
from __future__ import annotations
import itertools,time
from exact_16bit_filter import exhaustive_4x4
from reversible_ca_solver import blocks,valid_task,native_verify

RULE_SIZE=16

def source_pair_mapping(demos):
    rule={}
    reverse={}
    for d in demos:
        before=d["before"];after=d["after"]
        h=len(before);w=len(before[0])
        assert h==w==4 and len(after)==4 and len(after[0])==4
        assert all(len(row)==4 and set(row)<=set("01") for row in before+after)
        for block in blocks(4,4,0):
            old=sum((int(before[y][x])<<j) for j,(y,x) in enumerate(block))
            new=sum((int(after[y][x])<<j) for j,(y,x) in enumerate(block))
            if old in rule and rule[old]!=new:
                return None,"OBSERVATIONS_CONTRADICT_DETERMINISM"
            if new in reverse and reverse[new]!=old:
                return None,"OBSERVATIONS_CONTRADICT_BIJECTIVITY"
            rule[old]=new
            reverse[new]=old
    return rule,None

def candidate_rules(mapping,max_unknown):
    missing=[x for x in range(16) if x not in mapping]
    outputs=[x for x in range(16) if x not in set(mapping.values())]
    assert len(missing)==len(outputs)
    if len(missing)>max_unknown:return None,len(missing)
    candidates=[]
    for assignment in itertools.permutations(outputs):
        rule=dict(mapping)
        rule.update(zip(missing,assignment))
        complete=tuple(rule[i] for i in range(16))
        assert sorted(complete)==list(range(16))
        candidates.append(complete)
    return candidates,len(missing)

def reconstruct_with_rule(original_task,rule):
    task={**original_task,"rule":{"type":"margolus_block_ca","permutation":list(rule)}}
    h,w,T,p=valid_task(task)
    assert (h,w)==(4,4)
    result=exhaustive_4x4(task)
    return result,task

def discover(record,max_unknown=5,policy="joint"):
    started=time.process_time()
    assert policy in ("lookup","one_missing","joint")
    assert "answer" not in record and "metadata" not in record
    assert "permutation" not in record["task"]["rule"]
    mapping,error=source_pair_mapping(record["demos"])
    if error:
        return {"status":error,"prediction":None,"cpu_s":time.process_time()-started}
    permitted=0 if policy=="lookup" else (1 if policy=="one_missing" else max_unknown)
    candidates,missing=candidate_rules(mapping,permitted)
    if candidates is None:
        return {"status":"ABSTAIN_UNIDENTIFIED_RULE","prediction":None,
                "observed_map_size":len(mapping),"remaining_rule_entries":missing,
                "cpu_s":time.process_time()-started}
    possible=set()
    rules_compatible=0
    for rule in candidates:
        result,task=reconstruct_with_rule(record["task"],rule)
        n=result.get("candidate_count",None)
        guess=result.get("prediction")
        # A complete candidate rule admitting >=2 initial states invalidates
        # *unique* initial reconstruction. The exact enumeration is decisive.
        if n is not None and n>1:
            return {"status":"ABSTAIN_AMBIGUOUS_ORIGINAL_INITIAL_STATE",
                    "prediction":None,"observed_map_size":len(mapping),
                    "remaining_rule_entries":missing,"rule_candidates":len(candidates),
                    "cpu_s":time.process_time()-started}
        if n==0:
            continue
        if guess is None:
            # The full-state solver's UNKNOWN with >1 handled above.
            return {"status":"ABSTAIN_INCOMPLETE_RULE_VALIDATION","prediction":None,
                    "cpu_s":time.process_time()-started}
        assert native_verify(task,guess)
        rules_compatible+=1
        possible.add(tuple(guess))
        if len(possible)>1:
            return {"status":"ABSTAIN_DIFFERENT_INITIAL_STATES",
                    "prediction":None,"observed_map_size":len(mapping),
                    "remaining_rule_entries":missing,"rule_candidates":len(candidates),
                    "rules_compatible":rules_compatible,
                    "cpu_s":time.process_time()-started}
    if len(possible)!=1:
        return {"status":"ABSTAIN_NO_INITIAL_STATE","prediction":None,
                "observed_map_size":len(mapping),
                "remaining_rule_entries":missing,"rule_candidates":len(candidates),
                "cpu_s":time.process_time()-started}
    prediction=list(next(iter(possible)))
    # The source answer is invariant across ALL calibration-compatible rules
    # but this need NOT uniquely identify the rule itself.
    return {"status":"PROVEN_INVARIANT_INITIAL_ACROSS_ALL_RULES",
            "prediction":prediction,"observed_map_size":len(mapping),
            "remaining_rule_entries":missing,"rule_candidates":len(candidates),
            "rules_compatible":rules_compatible,
            "rule_identifiable":missing<=1,
            "cpu_s":time.process_time()-started}
