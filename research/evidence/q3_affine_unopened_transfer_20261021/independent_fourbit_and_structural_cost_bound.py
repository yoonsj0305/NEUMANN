"""Q3/Q4 scope: independently exhaustive four-bit affine finite-state oracle
and exact real source elimination of exponential candidate ENUMERATION.

This is NOT an empirical speedup vs an optimized classical solver.
This is NOT a learned-invention or global Q4 10x pass.
All four frozen real cases must be reread verbatim from immutable CI receipt.
"""
import argparse, hashlib, itertools, json, random
from pathlib import Path
import z3
from research.evidence.q3_exact_GF2_all_arity_20261021.dragon2_exact_affine_inductive_fixpoint import converge

HISTORICAL_SHA="74ea53adf4db64e5adb97f6421ea05b1ddf2473b5b8cab55abc1790a575f524c"

def affine_spaces(n=4):
    choices=[]
    for mask in range(1,1<<(1<<n)):
        s={x for x in range(1<<n) if (mask>>x)&1}
        origin=min(s)
        offsets={x^origin for x in s}
        if all((a^b) in offsets for a in offsets for b in offsets):
            choices.append(frozenset(s))
    return choices

def cube(vars,number):
    return z3.And(*(v if (number>>i)&1 else z3.Not(v)
                    for i,v in enumerate(vars)))

def exact_oracle(pre,edges,affine):
    covers=[x for x in affine if pre.issubset(x) and
            all(b in x for a,b in edges if a in x)]
    if not covers:
        raise RuntimeError("NO_VALID_AFFINE_SUPERSET")
    return frozenset(set.intersection(*(set(a) for a in covers)))

def check_fourbit_oracle():
    n=4
    affine=affine_spaces(n)
    if len(affine)!=307:
        raise RuntimeError("FULL_FOURBIT_AFFINE_SET_COUNT_NOT_307")
    rng=random.Random(20261021)
    allstates=list(range(1<<n))
    tests=[
      ({0},set()),
      (set(allstates),set()),
      ({0},{(i,j) for i in allstates for j in allstates}),
      ({0},{(i,j) for i in allstates for j in allstates if i.bit_count()%2==j.bit_count()%2}),
      ({0},{(i,j) for i in allstates for j in allstates if (i^j) in (0,1)}),
    ]
    for _ in range(35):
        first=set(rng.sample(allstates,rng.randint(1,8)))
        edges={(i,j) for i in allstates for j in allstates
               if rng.randrange(7)==0}
        tests.append((first,edges))
    a=z3.Bools("a0 a1 a2 a3")
    b=z3.Bools("b0 b1 b2 b3")
    receipts=[]
    for i,(initial,edge) in enumerate(tests):
        pre=z3.Or(*[cube(a,x) for x in initial])
        trans=z3.Or(*[z3.And(cube(a,x),cube(b,y)) for x,y in edge])
        actual=converge(pre,trans,a,b,list(range(n)),30000)
        if actual["status"]!="Z3_EXACT_LEAST_AFFINE_FIXEDPOINT_OBTAINED":
            raise RuntimeError(f"FOURBIT_CASE_{i}_FIXPOINT_ABSTAIN")
        basis=actual["complete_affine_GF2_kernel_vectors"]
        found=frozenset(x for x in allstates
                    if all((v&((1<<n)-1)&x).bit_count()%2==(v>>n)&1 for v in basis))
        wanted=exact_oracle(initial,edge,affine)
        if found!=wanted:raise RuntimeError(f"FOURBIT_CASE_{i}_MISMATCH")
        receipts.append({"case":i,"chosen_affine_size":len(found),
                          "GF2_nullity":len(basis),"source_rank":actual["GF2_augmented_row_rank"]})
    return {"independent_full_set_4bit_affine_spaces":len(affine),
            "independent_source_transition_oracle_count":len(tests),
            "pass_count":len(receipts),
            "cases":receipts}

def audit_four_originals(first):
    data=Path(first).read_bytes()
    if hashlib.sha256(data).hexdigest()!=HISTORICAL_SHA:
        raise RuntimeError("HISTORICAL_FROZEN_FOUR_ORIGINAL_RESULTS_SHA_CHANGED")
    f=json.loads(data)
    if f["num_exact_full_affine_original_dual_pass"]!=4 or f["num_full_affine_lowarity_complete_original_dual_pass"]!=4:
        raise RuntimeError("FIRST_FOUR_SOURCE_SCOPED_RESULTS_NOT_4_OF_4")
    rows=[]
    for r in f["source_results"]:
        assert r["status"]=="PASS_FULL_ORIGINAL_AFFINE_AND_LOWARITY_GENERATION"
        n=len(r["eligible_bool_original_state_indices"])
        g=r["least_affine_inductive_hull"]
        rank=g["GF2_augmented_row_rank"]
        nullity=g["GF2_complete_inductive_affine_kernel_nullity"]
        bound=n+1
        assert rank+nullity==bound
        assert g["number_of_independent_source_model_witnesses"]==rank<=bound
        assert g["witness_rank_strict_increments"]
        assert r["source_proven_lowarity_rank"]==nullity
        assert all(v["dual_pass"] for v in r["final_original_conjunction_independent_dual_Z3_cvc5"].values())
        for p in r["proved_independent_lowarity_certificates"]:
            assert p["independently_source_inductive"]
            assert all(a["dual_pass"] for a in p["original_dual_2VC"].values())
        count=(1 << (n+1))-2 # all nonempty LHS parity masks and both Boolean offsets.
        rows.append({
            "source":r["source"],"eligible_Bool_n":n,
            "possible_nontrivial_affine_equations_full_universe":count,
            "observed_true_independent_affine_basis_dimension":nullity,
            "true_nonempty_source_affine_equation_span_size":(1<<nullity)-1,
            "minimum_affine_hull_source_witness_count":rank,
            "max_witness_rank_increases_after_initial":n,
            "raw_first_actual_witness_rank_increases":rank-1,
            "proven_lowarity_generating_rank":r["source_proven_lowarity_rank"],
            "candidate_expression_count_per_rank_witness":count//rank,
            "source_specific_actual_wall_ms":r["wall_ms"],
        })
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--first",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    arg=ap.parse_args()
    experiments=check_fourbit_oracle()
    sources=audit_four_originals(arg.first)
    proof={
      "schema":"neumann.q34.all_affine_candidates_exact_finite_dimension_structural_bound.v1",
      "historical_first_four_original_json_sha256":HISTORICAL_SHA,
      "independent_4bit_true_oracle":experiments,
      "actual_four_frozen_originals":sources,
      "mathematical_theorem":"For n Boolean coordinates every affine equation is one of 2^(n+1)-2 nonempty-mask affine equations; the exact least inductive affine hull is determined by at most n+1 independent augmented GF2 original-model rows, since each new violated hull adds rank exactly one. At convergence native source Pre and Trans are universally UNSAT outside that hull. Witness bound is not a comparison with advanced classical solvers.",
      "structural_enumeration_avoidance_proved":all(x["possible_nontrivial_affine_equations_full_universe"]>10*x["minimum_affine_hull_source_witness_count"] for x in sources),
      "NOT_runtime_10x":True,
      "NOT_state_of_the_art_classical_10x":True,
      "global_Q4":"OPEN","global_Q3":"OPEN","new_neural_train":0,
    }
    arg.out.parent.mkdir(parents=True,exist_ok=True)
    arg.out.write_text(json.dumps(proof,indent=2,sort_keys=True)+"\n")
    print("INDEPENDENT_4BIT_AFFINE_ORACLE_PASS",experiments["pass_count"],"/40")
    for x in sources:
        print("EXACT_STRUCTURAL_SEARCH_SPACE",x["source"],
              "EQUATION_UNIVERSE",x["possible_nontrivial_affine_equations_full_universe"],
              "ACTUAL_WITNESS_RANK",x["minimum_affine_hull_source_witness_count"],
              "LOWARITY_RANK",x["proven_lowarity_generating_rank"])
    print("PROVED_ABOVE_10X_ENUMERATION_AVOIDANCE",proof["structural_enumeration_avoidance_proved"])
    print("ACTUAL_RUNTIME_10X","NOT_PROVEN")
    print("GLOBAL_Q4",proof["global_Q4"])
if __name__=="__main__":
    main()
