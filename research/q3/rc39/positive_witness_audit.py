"""RC39 post-FIRST audit: positive witness acquisition cost and a minimax bound.

This script NEVER reruns / changes the FIRST RC39 programs or their original
independent grades. The original winner was GIVEN a satisfying witness.
We now evaluate the counterfactual price of acquiring it with the SAME
point-membership oracle. Exact assumption: unknown k distinct offsets, each
independent required ABC symbol, uniform random secrets and queries.

FORMAL OBSERVATION: A single point-membership query is positive for exactly
3^-k of secret assignments (also when active locations are uniformly unknown).
Until the first positive, EVERY answer is the identical 'no'. For any
deterministic adaptive strategy its entire all-negative path is a fixed
sequence of q candidates. The chance of a positive in <=q probes is bounded
by the union bound q/3^k. Randomized policies average the same bound.
Therefore >=50% chance requires q >= (3^k)/2. This is conditional on
ONE-BIT-at-one-center oracle access; whole-string outputs violate the model.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
from itertools import combinations,product
from time import process_time_ns
from statistics import mean,median
import json,random,sys

FIRST_SHA256="8be501ee87f432ffdededb093421095ea8438befc8cafe497a08aa502648cab3"
K=(0,1,2,3,4,4,2,1,3,4,0,3)
ALPHABET="ABC"
RADIUS=512

def hidden_cases():
    """Independent pure author-target reconstruction; no learner import."""
    for index,k in enumerate(K):
        rr=random.Random(0x39c700+index*17971)
        original="".join(rr.choice(ALPHABET) for _ in range(1025))
        original=original[:512]+"B"+original[513:]
        offsets=sorted(rr.sample([x for x in range(-512,513) if x!=0],k))
        yield index,tuple((d,original[512+d]) for d in offsets)
def oracle(reads,word):
    return word[512]=="B" and all(word[512+d]==c for d,c in reads)
def random_positive_acquisition(reads,rng,cap=10000):
    # No satisfying witness is passed. A negative response gives only 1 bit.
    for n in range(1,cap+1):
        w="".join(rng.choice(ALPHABET) for _ in range(1025))
        w=w[:512]+"B"+w[513:]
        if oracle(reads,w):return n
    return None
def exact_small_prior_union_bound():
    # All 4-position / 2-hidden-read hypotheses equiprobable.
    m,k=4,2
    hypotheses=[dict(zip(pos,chars)) for pos in combinations(range(m),k)
                for chars in product(ALPHABET,repeat=k)]
    assert len(hypotheses)==54
    plan=[tuple(x) for x in product(ALPHABET,repeat=m)]
    assert len(plan)==81
    cases=[]
    for q in [1,2,3,4,5,8]:
        candidates=plan[:q]
        covered=sum(any(all(word[j]==c for j,c in hidden.items()) for word in candidates)
                    for hidden in hypotheses)
        upper=min(1,q/(3**k))
        probability=covered/len(hypotheses)
        assert probability<=upper+1e-12,(q,probability,upper)
        cases.append({"point_membership_questions":q,
          "exact_hypothesis_success_probability":probability,
          "union_bound":upper})
    return cases
def quantile(values,p):
    sorted_values=sorted(values)
    i=(len(sorted_values)-1)*p
    a=int(i);b=min(a+1,len(sorted_values)-1)
    return sorted_values[a]+(sorted_values[b]-sorted_values[a])*(i-a)
def study(first_path):
    bytes_=Path(first_path).read_bytes()
    assert sha256(bytes_).hexdigest()==FIRST_SHA256
    first=json.loads(bytes_)
    assert first['summary']['candidate_source_queries']==644
    assert first['summary']['classical_single_site_queries']==12300
    assert first['summary']['classical_strong_adaptive_queries']==644
    start=process_time_ns()
    repetitions=32
    cohorts=[]
    table=[]
    for repeat in range(repetitions):
        per=[]
        for i,reads in hidden_cases():
            seed=int(FIRST_SHA256[:12],16)+101*i+99991*repeat
            q=random_positive_acquisition(reads,random.Random(seed))
            if q is None:raise RuntimeError("POSITIVE_SOURCE_ACQUISITION_BUDGET_EXHAUSTED")
            per.append(q)
            if repeat==0:
                table.append({"task":f"AUTHOR_NEW_{i:02d}","k":len(reads),
                  "min_queries_for_half_chance_information_bound":(3**len(reads))/2,
                  "random_acquisition_first_trial_questions":q})
        acquired=sum(per)
        groups=644+acquired
        singles=12300+acquired
        cohorts.append({"replicate":repeat,"paid_positive_acquisition_queries":acquired,
          "candidate_all_oracle_calls":groups,"single_site_all_oracle_calls":singles,
          "strong_adaptive_all_oracle_calls":groups,
          "ratio_vs_single_site":singles/groups})
    baseline=12300/644
    ratios=[x['ratio_vs_single_site'] for x in cohorts]
    return {"schema":"neumann.q3.rc39.after-first-positive-witness-acquisition-audit.v1",
      "first_original_sha256":FIRST_SHA256,
      "scoring":"POSTGRADE_COST_ABLATION_ONLY; never changes first source program or first heldout scores",
      "oracle_access":"one-bit point membership at center; no reference code or satisfying assignment; alphabet ABC",
      "hypothesis_distribution":"uniform k distinct relative offsets; independent uniform ABC required symbols; inherited frozen author prior",
      "task_count":12,"cohort_repetitions":repetitions,"discovered_prog_original_query_count":644,
      "single_site_original_query_count":12300,
      "strong_classical_adaptive_original_query_count":644,
      "unpriced_satisfying_witness_ratio":baseline,
      "paid_witness_ratio_median":median(ratios),
      "paid_witness_ratio_p05":quantile(ratios,.05),
      "paid_witness_ratio_p95":quantile(ratios,.95),
      "paid_acquisition_query_total_median":median(x["paid_positive_acquisition_queries"] for x in cohorts),
      "paid_acquisition_query_total_p95":quantile([x["paid_positive_acquisition_queries"] for x in cohorts],.95),
      "simulations_exceed_tenfold_ratio":sum(r>=10 for r in ratios),
      "total_simulations":repetitions,
      "minimax_half_success_queries_by_k":{str(k):(3**k)/2 for k in range(9)},
      "theorem":"for random hidden k-sparse exact-symbol conjunctions, Pr(at_least_one_positive_with_q_point_oracle_queries)<=min(1,q/3^k), including adaptive algorithms before first positive",
      "small_exact_unconditional_hypothesis_census":exact_small_prior_union_bound(),
      "postgrade_cpu_ms":(process_time_ns()-start)/1e6,
      "source_regret_vs_equal_rights_adaptive":"NO_ADVANTAGE",
      "all_in_oracle_plus_program_cost_10x":"NOT_PROVEN",
      "q3_global":"OPEN","q6_external_semantic_family":"OPEN",
      "first_trial_table":table,"all_cohort_replicates":cohorts}
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("python -m research.q3.rc39.positive_witness_audit ORIGINAL_FIRST.json")
    result=study(sys.argv[1])
    print(json.dumps(result,sort_keys=True,indent=2))
