"""Independent exhaustive integer reference for CRT mod63 actual program.

Reference uses triple nested Python loops and exact arbitrary-precision cube
sums, not numpy sorted buckets / searchsorted, and checks both discovered SAT
and bounded NO-WITNESS results on 5 radii and 250 deterministic cases.
Small brute reference is scope-limited; it is not a source SAT/UNSAT proof for
unbounded original integers. No oracle labels pass into tested solver.
"""
from __future__ import annotations
import random
from research.evidence.g0_cubic_crt63_20261021.real_official_five_unknown_crt63_r50000 import (
    crt63_numeric_exact_search,finite_exact_residue_proof
)

def source_free_reference(radius):
    domain=range(-radius,radius+1)
    sums={x**3+y**3+z**3
          for x in domain for y in domain for z in domain}
    return sums

def test():
    randomgen=random.Random(20261021)
    cases=0
    truths=0
    misses=0
    all_cases=[]
    for radius in (7,10,12,16,20):
        universe=source_free_reference(radius)
        positives=sorted(universe)
        upper=3*radius**3+57
        # NEGATIVE target values verified absent from exact all-domain reference.
        negatives=[]
        while len(negatives)<25:
            v=randomgen.randint(-upper,upper)
            if v not in universe and v not in negatives:
                negatives.append(v)
        targets=randomgen.sample(positives,25)+negatives
        randomgen.shuffle(targets)
        assert len(targets)==50
        for n in targets:
            result=crt63_numeric_exact_search(n,radius)
            witness=result["actual_exact_integer_witness"]
            expected=n in universe
            observed=witness is not None
            if expected!=observed:
                raise AssertionError(f"CRT63_INDEPENDENT_3D_ORACLE_MISMATCH:R{radius}:N{n}")
            if observed:
                assert all(abs(int(v))<=radius for v in witness)
                assert sum(int(v)**3 for v in witness)==n
                truths+=1
            else:
                misses+=1
            cases+=1
        all_cases.append({"integer_radius":radius,"cases":len(targets),
                          "independently_python_brute_all_xyz_count":(2*radius+1)**3,
                          "tested_exact_positive":25,
                          "tested_exact_negative":25,
                          "algorithm_agreed_with_exhaustive_oracle":True})
    # Distinct independent finite modular mathematical theorem controls.
    mod_math={n:finite_exact_residue_proof(n) for n in (0,1,7,9,228,268,291,880)}
    assert all(r["pruning_exact_no_integer_solution_lost"] for r in mod_math.values())
    assert cases==250 and truths==125 and misses==125
    print("INDEPENDENT_TRIPLE_BRUTE_ORACLE_EXACT_CRT63_PASS",cases,"/250",
          "SAT",truths,"BOUNDED_NO_WITNESS",misses)
    print("FINITE_CRT63_MODULAR_INTEGER_PROOF",len(mod_math),"/8")
    print("EXACT_SMALL_DOMAIN_POSITIVE_NEGATIVE_CONTROLS",all_cases)
    return {"independent_source_free_reference_cases":cases,
            "positive":truths,"negative":misses,"all_proven":True,
            "radii":[7,10,12,16,20]}

if __name__=="__main__":
    test()
