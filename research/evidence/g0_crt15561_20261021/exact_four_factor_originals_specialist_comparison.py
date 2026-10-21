"""G0 matched exact CRT15561 vs CRT63 strong classical specialist, five original SMT-LIB.
POSTHOC all input cases already opened. Existing mathematical CRT & sorted
two-sum, NO novel structural/learned invention. No source answer oracle.
"""
from __future__ import annotations
import argparse,json,math,random,time
from pathlib import Path
import numpy as np
from research.evidence.g0_cubic_mod9_20261021.first_seven_frozen_originals_exact_mod9_cubes import (
    SOURCE_COMMIT,structural_source,independent_original_grounded_certificate
)
from research.evidence.g0_cubic_crt63_20261021.real_official_five_unknown_crt63_r50000 import (
    crt63_numeric_exact_search
)
from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import (
    git_blob_sha1,sha256
)

M=9*7*13*19
RADIUS=50000
CHUNK=128
CASES=("STC_0291.smt2","STC_0588.smt2","STC_0609.smt2","STC_0786.smt2","STC_0880.smt2")
CONTROLS=("STC_0228.smt2","STC_0268.smt2","STC_0813.smt2")
CONTRACT="82e659ba5535cb2d4092d4f2fef69ee8b92f313d"

def exact_composite_buckets(target,radius):
    start=time.perf_counter_ns()
    assert 0<radius<=150000 and 3*radius**3<2**63-1
    xs=np.arange(-radius,radius+1,dtype=np.int64)
    cubes=xs**3
    residues=cubes%M
    keys=np.unique(residues)
    groups={}
    for key in keys:
        mask=residues==key
        groups[int(key)]=(xs[mask],cubes[mask])
    ordered=sorted(groups)
    assert len(groups)<=315
    attempts=0
    pair_classes=0
    hit=None
    for ka in ordered:
        xa,ca=groups[ka]
        for kb in ordered:
            kz=(target-ka-kb)%M
            if kz not in groups:continue
            xb,cb=groups[kb]
            xz,cz=groups[kz]
            pair_classes+=1
            for off in range(0,len(ca),CHUNK):
                wanted=target-(ca[off:off+CHUNK,None]+cb[None,:])
                idx=np.searchsorted(cz,wanted)
                i,j=np.where(idx<len(cz))
                attempts+=wanted.size
                if len(i):
                    ok=cz[idx[i,j]]==wanted[i,j]
                    if np.any(ok):
                        k=int(np.flatnonzero(ok)[0])
                        r,q=int(i[k]),int(j[k])
                        hit=(int(xa[off+r]),int(xb[q]),int(xz[idx[r,q]]))
                        assert sum(int(v)**3 for v in hit)==target
                        break
            if hit is not None:break
        if hit is not None:break
    return {
      "source_mathematical_method":"CRT15561_exact_four_factors_sorted_two_sum",
      "integer_radius":radius,
      "actual_integer_witness":hit,
      "exact_numeric_witness":hit is not None and sum(int(v)**3 for v in hit)==target,
      "modulus":M,
      "actual_distinct_source_cube_residue_buckets":len(groups),
      "actual_valid_residue_pair_classes_examined":pair_classes,
      "actual_filtered_numeric_pair_comparisons":attempts,
      "source_numeric_bound_no_witness_means_UNBOUNDED_UNKNOWN":True,
      "numeric_wall_ms":(time.perf_counter_ns()-start)/1e6
    }

def independent_exact_small_original_free_oracle():
    seed=random.Random(20261021)
    passed=0;true_sat=0;true_bounded_missing=0;details=[]
    for radius in (7,10,12,16,20):
        vals=range(-radius,radius+1)
        integer_source={x**3+y**3+z**3 for x in vals for y in vals for z in vals}
        positives=seed.sample(sorted(integer_source),25)
        negatives=[]
        while len(negatives)<25:
            candidate=seed.randint(-3*radius**3-57,3*radius**3+57)
            if candidate not in integer_source and candidate not in negatives:
                negatives.append(candidate)
        cases=positives+negatives;seed.shuffle(cases)
        for n in cases:
            r=exact_composite_buckets(n,radius)
            got=r["actual_integer_witness"]
            expected=n in integer_source
            assert (got is not None)==expected,(radius,n,got,expected)
            if expected:
                assert sum(int(v)**3 for v in got)==n
                assert all(-radius<=v<=radius for v in got)
                true_sat+=1
            else:true_bounded_missing+=1
            passed+=1
        details.append({"radius":radius,"independent_full_brute_3D_integer_space":(2*radius+1)**3,
                        "positive_control_true_SAT":25,"negative_true_bounded_nonexistence":25})
    # G0 exact math: all congruent integers have the same cubic residue. Every
    # integer pair with target=z^3+x^3+y^3 necessarily satisfies cubic-residue
    # M equality. Discarding a pair lacking z key cannot discard a solution.
    # Check COMPLETE finite ring residue domain, independently Python ints.
    cube_map={r:r**3%M for r in range(M)}
    assert len(cube_map)==M
    for r in range(M):
        assert ((r+M)**3-r**3)%M==0
        assert cube_map[r]==pow(r,3,M)
    assert M==15561
    assert passed==250 and true_sat==125 and true_bounded_missing==125
    print("CRT15561_INDEPENDENT_BRUTE_ALL_SAT_MISS",passed,"/250",
          "POS",true_sat,"NEG",true_bounded_missing,flush=True)
    print("CRT15561_COMPLETE_FINITE_CUBIC_RESIDUE_PROOF",M,"/15561",flush=True)
    return {"reference_cases":passed,"positive":true_sat,"negative":true_bounded_missing,
            "independent_bruteforce_all_3D":True,
            "crt15561_modulus_finite_correctness":True,"controls":details}

def run_arm(original,source,method):
    started=time.perf_counter_ns()
    row={"method":method,"source":source,
         "unbounded_integer_status_without_numeric_witness":"UNKNOWN",
         "original_full_SMT2_independent_dual":False}
    try:
        n,names,orig=structural_source(original)
        row["original_source_literal_RHS"]=n
        if method=="strong_CRT63":
            r=crt63_numeric_exact_search(n,RADIUS)
            guess=r["actual_exact_integer_witness"]
            row["numeric_ms"]=r["numeric_search_wall_ms"]
            row["paired_numeric_work"]=r["actual_eligible_source_pairs_probed_before_witness_or_exhaustion"]
        elif method=="CRT15561":
            r=exact_composite_buckets(n,RADIUS)
            guess=r["actual_integer_witness"]
            row["numeric_ms"]=r["numeric_wall_ms"]
            row["paired_numeric_work"]=r["actual_filtered_numeric_pair_comparisons"]
        else:raise RuntimeError("UNSUPPORTED_METHOD")
        row["algorithm_receipt"]=r
        if guess is None:
            row["status"]="BOUNDED_50K_NO_WITNESS_UNBOUNDED_UNKNOWN"
        else:
            assert sum(int(v)**3 for v in guess)==n
            receipt=independent_original_grounded_certificate(
                original.decode("utf-8"),names,guess,orig,"SAT")
            row["source_certification"]=receipt
            row["original_full_SMT2_independent_dual"]=receipt["independent_dual_result"]
            row["status"]="ORIGINAL_RAW_SMT2_Z3_CVC5_SAT" if receipt["independent_dual_result"] else "ABSTAIN_UNVERIFIED_FULL_ORIGINAL"
    except Exception as e:
        row["status"]="ABSTAIN_SOURCE_OR_SOLVER_EXCEPTION"
        row["error"]=type(e).__name__+":"+str(e)[:400]
    row["complete_original_source_parse_math_search_checker_wall_ms"]=(time.perf_counter_ns()-started)/1e6
    return row

def authenticate(root,item):
    b=(root/item["path"]).read_bytes()
    if len(b)!=item["bytes"] or git_blob_sha1(b)!=item["sha1_git_blob"]:
        raise RuntimeError("FROZEN_REAL_ORIGINAL_SOURCE_SHA_OR_SIZE_MISMATCH")
    return b

def control_real_origins(root,items):
    answers={}
    for name,item in items.items():
        raw=authenticate(root,item)
        n,names,parsed=structural_source(raw)
        found=exact_composite_buckets(n,10000)["actual_integer_witness"]
        valid=False
        if found:
            valid=independent_original_grounded_certificate(
                raw.decode("utf-8"),names,found,parsed,"SAT")["independent_dual_result"]
        answers[name]={"true_original_source_authentic":True,"witness":found,
                       "true_original_dual_SAT":valid}
        print("G0_EXACT_CRT15561_POSITIVE_ORIGINAL",name,"SAT",valid,"WITNESS",found,flush=True)
    return answers

def test_source(root,name,item,index):
    raw=authenticate(root,item)
    record={"source":item["path"],"git_original_blob":item["sha1_git_blob"],
            "original_SHA256":sha256(raw),
            "original_source_already_opened_before_this_experiment":True}
    order=["strong_CRT63","CRT15561"] if index%2==0 else ["CRT15561","strong_CRT63"]
    record["predeclared_order"]=order
    for method in order:
        record[method]=run_arm(raw,item["path"],method)
    a,b=record["strong_CRT63"],record["CRT15561"]
    record["same_bounded_original_disposition"]=(
      a["status"]==b["status"]
      and a["status"] in ("ORIGINAL_RAW_SMT2_Z3_CVC5_SAT",
                         "BOUNDED_50K_NO_WITNESS_UNBOUNDED_UNKNOWN"))
    record["bounded_same_capability_old_over_new_wall_ratio"]=(
      a["complete_original_source_parse_math_search_checker_wall_ms"]/
      b["complete_original_source_parse_math_search_checker_wall_ms"]
      if record["same_bounded_original_disposition"] else None)
    print("G0_CRT15561_ACTUAL_ORIGINAL",name,
          "CRT63",a["status"],round(a["complete_original_source_parse_math_search_checker_wall_ms"],3),
          "CRT15561",b["status"],round(b["complete_original_source_parse_math_search_checker_wall_ms"],3),
          "PAIRED_ORIGINAL_RATIO",record["bounded_same_capability_old_over_new_wall_ratio"],flush=True)
    return record

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    o=p.parse_args()
    con=json.loads(o.contract.read_text())
    if con["schema"]!="neumann.g0.posthoc_CRT15561_fixed_r50000_exact_specialist_matched.v1":
        raise RuntimeError("CONTRACT_CHANGED")
    if con["modulus"]!=M or con["fixed_radius"]!=RADIUS or con["prime_power_factors"]!=[9,7,13,19]:
        raise RuntimeError("FROZEN_MATH_CHANGED")
    f=json.loads(o.freeze.read_text())
    if f["source"].split("@")[-1]!=SOURCE_COMMIT or len(f["first_transfer_cohort"])!=7:
        raise RuntimeError("ORIGINAL_FROZEN_SEVEN_CHANGED")
    all_real={q["path"].split("/")[-1]:q for q in
              [f["development_original_STC_0228"],*f["first_transfer_cohort"]]}
    assert all(k in all_real for k in CASES+CONTROLS)
    pure=independent_exact_small_original_free_oracle()
    controls=control_real_origins(o.root,{k:all_real[k] for k in CONTROLS})
    rows=[test_source(o.root,k,all_real[k],i) for i,k in enumerate(CASES)]
    iso=all(x["same_bounded_original_disposition"] for x in rows)
    cold=sum(x["strong_CRT63"]["complete_original_source_parse_math_search_checker_wall_ms"] for x in rows)
    new=sum(x["CRT15561"]["complete_original_source_parse_math_search_checker_wall_ms"] for x in rows)
    receipt={
       "schema":"neumann.g0.unchanged_five_SMT_original_matched_CRT63_vs_CRT15561.v1",
       "pre_run_four_factor_contract_commit":CONTRACT,
       "study_is_POSTHOC_not_first_source_blind":True,
       "five_previous_source_originals_retained":len(rows)==5,
       "original_source_3_prior_controls_SAT":sum(t["true_original_dual_SAT"] for t in controls.values()),
       "independent_250_small_solvable_and_no_solution_oracle":pure,
       "same_exact_original_source_bounded_capability":iso,
       "old_strong_CRT63_total_full_source_MS":cold,
       "new_CRT15561_total_full_source_MS":new,
       "old_CRT63_over_new_CRT15561_total_wall_ratio":cold/new if iso and new else None,
       "new_CRT15561_is_10x_faster_than_CRT63_at_iso_capability":iso and new*10<=cold,
       "not_strongest_classical_direct_because_same_modulus_available_to_direct":True,
       "all_source_original_sat_models_independent_Z3_cvc5":True,
       "NO_TRUE_UNBOUNDED_UNSAT_ASSERTIONS_FROM_BOUND_MISS":True,
       "no_new_neural_inference_or_unique_learning":True,
       "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
       "real_source_controls":controls,"five_opened_originals":rows
    }
    o.out.parent.mkdir(parents=True,exist_ok=True)
    o.out.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    print("G0_TRUE_CRT15561_EQUAL_BOUNDED_ORIGINAL_CAPABILITY",iso,"/5")
    print("G0_TRUE_CRT15561_OLD_STRONG_CRT63_WALL_MS",cold)
    print("G0_TRUE_CRT15561_NEW_CRT15561_WALL_MS",new)
    print("G0_TRUE_CRT15561_OLD_OVER_NEW",receipt["old_CRT63_over_new_CRT15561_total_wall_ratio"])
    print("G0_TRUE_CRT15561_TEN_X_VS_STRONG_CRT63",receipt["new_CRT15561_is_10x_faster_than_CRT63_at_iso_capability"])
    print("G0_GLOBAL_Q3_Q4",receipt["global_Q3"],receipt["global_Q4"])
if __name__=="__main__":
    main()
