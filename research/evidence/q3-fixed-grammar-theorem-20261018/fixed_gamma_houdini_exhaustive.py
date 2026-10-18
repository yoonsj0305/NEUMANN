"""Q3 fixed-candidate-grammar neural-vs-classical representational ceiling.
Preregistered #234. This does NOT prove neural learning worthless/slow/never novel.
THEOREM (complete Houdini): for a fixed finite set Gamma of predicates, any
inductive source-safety proof whose invariant is conjunction S subset Gamma
implies a source-safety proof from complete classical Houdini initialized
with all Gamma. The neural selection can be cheaper, not more expressive.

Machine model exact finite universe set semantics; exhaust over all 2-state
Pre, Trans, Post, ALL Gamma subsets of all four 2-state predicates,
and ALL S subsets Gamma. No task learned labels or ML library.
"""
import hashlib,json,itertools,random,time
from pathlib import Path

OUT=Path("/tmp/q3_fixed_grammar_dominance_first_receipt.json")

def allowed(predicates,universe):
    mask=(1<<universe)-1
    for p in predicates:mask &= p
    return mask

def inductive(candidate_mask,pre_mask,transition_mask,n):
    if pre_mask & ~candidate_mask:return False
    for a in range(n):
        if not (candidate_mask>>a)&1:continue
        for b in range(n):
            if ((transition_mask>>(a*n+b))&1) and not ((candidate_mask>>b)&1):
                return False
    return True

def houdini(gamma,pre,transition,n):
    current=set(gamma)
    rounds=0
    while True:
        rounds+=1
        cur_allowed=allowed(current,n)
        remove=set()
        for p in current:
            if pre & ~p:remove.add(p);continue
            for a in range(n):
                if ((cur_allowed>>a)&1)==0:continue
                if any((transition>>(a*n+b))&1 and ((p>>b)&1)==0 for b in range(n)):
                    remove.add(p);break
        if not remove:return sorted(current),rounds
        current.difference_update(remove)
        if rounds>len(gamma)+1:raise RuntimeError("HOUDINI_FIXPOINT_DOES_NOT_TERMINATE")

def subsets_of(seq):
    for selector in range(1<<len(seq)):
        yield [seq[i] for i in range(len(seq)) if selector>>i&1]

def check(n,pre,trans,post,gamma):
    kept,rounds=houdini(gamma,pre,trans,n)
    hmask=allowed(kept,n)
    if not inductive(hmask,pre,trans,n):
        raise AssertionError("HOUDINI_FINAL_STATE_NOT_INDUCTIVE")
    count=0;winning=0;distinct=0
    for sub in subsets_of(gamma):
        count+=1
        smask=allowed(sub,n)
        if not inductive(smask,pre,trans,n) or smask & ~post:continue
        winning+=1
        if not set(sub).issubset(kept):
            raise AssertionError("COUNTEREXAMPLE_HOUDINI_REMOVED_A_VALID_SUBSET_MEMBER")
        if hmask & ~post:
            raise AssertionError("COUNTEREXAMPLE_SUBSET_PROVES_BUT_HOUDINI_CANNOT")
        if set(sub)!=set(kept):distinct+=1
    return count,winning,distinct,rounds

def main():
    start=time.perf_counter()
    overview={"status":"Q3_FIXED_GRAMMAR_FIRST_PROOF_INCOMPLETE",
        "preregistration":"https://github.com/yoonsj0305/NEUMANN/issues/234",
        "theorem":"Any inductive conjunction of S subset Gamma proving Post is also covered by complete precise full-Gamma Houdini",
        "completeness_conditions":["same original exact Pre/Trans/Post",
            "neural output only conjunction from fixed finite Gamma",
            "classical checks complete and exact (no resource error, same grammar)",
            "classical Houdini run to fixed point"],
        "neural_training_in_this_experiment":False,
        "Q3_GLOBAL":"OPEN","GLOBAL_Q1_Q7":"OPEN"}
    OUT.write_text(json.dumps(overview,indent=2)+"\n")
    try:
        n=2
        all_predicates=list(range(1<<n))
        tests=0;valid_s=0;different_subsets=0;rounds_max=0
        by_grammar={}
        # Each semantic source is enumerated completely: 4 Pre, 16 Trans, 4 Post.
        # Grammar may be ANY subset of ALL four predicates over the two states.
        for gam in subsets_of(all_predicates):
            local=0
            for pre in range(1<<n):
                for trans in range(1<<(n*n)):
                    for post in range(1<<n):
                        c,w,d,r=check(n,pre,trans,post,gam)
                        tests+=c;valid_s+=w;different_subsets+=d
                        rounds_max=max(rounds_max,r);local+=c
            by_grammar[str(len(gam))]=by_grammar.get(str(len(gam)),0)+local
        # Additional deterministic samples of 3 or 4 state universes to
        # detect encoding mistakes outside the fully enumerated 2-state case.
        rng=random.Random(20261018)
        random_tests=0;random_winners=0
        for n in (3,4):
            for _ in range(4096):
                pre=rng.randrange(1<<n)
                trans=rng.randrange(1<<(n*n))
                post=rng.randrange(1<<n)
                gam=sorted(rng.sample(list(range(1<<n)),
                    rng.randrange(0,min(7,1<<n)+1)))
                c,w,d,r=check(n,pre,trans,post,gam)
                random_tests+=c;random_winners+=w
                rounds_max=max(rounds_max,r)
        # Negative control: if we used an illegally incomplete classical
        # selection (empty grammar), S from a larger grammar CAN beat it.
        # Shows conclusion actually DEPENDS on equal candidate grammar.
        n=2
        pre=1 # only state 0 initialized
        trans=1 # only 0->0 step
        post=1 # only state 0 safe
        good=[1]
        assert check(n,pre,trans,post,good)[1]>=1
        empty_kept,_=houdini([],pre,trans,n)
        assert allowed(empty_kept,n)&~post
        overview.update({
            "status":"Q3_FIXED_GRAMMAR_COMPLETE_HOUDINI_COVERAGE_THEOREM_AUDIT_PASS",
            "complete_universe_states":2,
            "complete_semantic_source_models":(1<<2)*(1<<4)*(1<<2),
            "all_possible_original_gamma_sets":1<<(1<<2),
            "exhaustive_full_grammar_and_subset_semantic_comparisons":tests,
            "winning_neural_subset_conjunctions_verified":valid_s,
            "winning_subsets_not_identical_to_classical_final_retained_predicates":different_subsets,
            "hardened_extra_universe_3_or_4_state_random_subset_comparisons":random_tests,
            "hardened_random_winning_subsets":random_winners,
            "maximum_classical_fixpoint_rounds":rounds_max,
            "per_grammar_size_subset_tests":by_grammar,
            "illegally_weak_classical_grammar_negative_control_detected":True,
            "counterexample_with_equal_grammar":False,
            "conclusion":"CURRENT_FIXED_GAMMA_NEURAL_OPERATOR_NOVELTY_IMPOSSIBLE_BY_CONSTRUCTION",
            "classical_source_derived_structures_other_than_fixed_gamma":"NOT_DISPROVEN",
            "learned_novel_operator_generation_outside_gamma":"NOT_TESTED",
            "time_s":round(time.perf_counter()-start,6)})
        OUT.write_text(json.dumps(overview,indent=2,sort_keys=True)+"\n")
        print("Q3_FIXED_GRAMMAR_THEOREM_FIRST",json.dumps(overview,sort_keys=True))
    except Exception as exc:
        overview.update({"status":"Q3_THEOREM_TEST_FAILED","error_type":type(exc).__name__,
                         "error":str(exc),"time_s":round(time.perf_counter()-start,6)})
        OUT.write_text(json.dumps(overview,indent=2,sort_keys=True)+"\n")
        raise

if __name__=="__main__":main()
