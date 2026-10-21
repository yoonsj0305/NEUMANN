"""Posthoc exact CRT 63 arithmetic search for five genuine hard QF_NIA originals.

Original 7-case results were already opened under PR #344. This is **NOT**
new first-blind external transfer; source bytes are frozen, numeric radius
increased only after historical first outcome UNKNOWN. True original source
model validity requires full Z3+cvc5 SAT independent check. Mathematical
finite proof shows mod 63 filter is complete inside bounded domain, and a
bounded miss never certifies unbounded original UNSAT.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import numpy as np

from research.evidence.g0_cubic_mod9_20261021.first_seven_frozen_originals_exact_mod9_cubes import (
  SOURCE_COMMIT,structural_source,independent_original_grounded_certificate
)
from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import (
  git_blob_sha1,sha256
)

NEW_RADIUS=50000
POS_RADIUS=10000
CHUNK=128
CUBE_RESIDUES_9=(0,1,8)
CUBE_RESIDUES_7=(0,1,6)
CRITICAL_FIVE=("STC_0291.smt2","STC_0588.smt2","STC_0609.smt2","STC_0786.smt2","STC_0880.smt2")
CTRL_THREE=("STC_0228.smt2","STC_0268.smt2","STC_0813.smt2")
CONTRACT_COMMIT="bfb94b7733fb1ee4b9166d1db04ac975f9e42979"

def finite_exact_residue_proof(target):
    r7={x**3 % 7 for x in range(7)}
    r9={x**3 % 9 for x in range(9)}
    assert r7==set(CUBE_RESIDUES_7)
    assert r9==set(CUBE_RESIDUES_9)
    classes={}
    for r in range(63):
        key=(r**3 % 9,r**3 % 7)
        classes.setdefault(key,[]).append(r)
    assert len(classes)==9
    for x in range(63):
        for y in range(63):
            zset=[z for z in range(63)
                  if (x**3 +y**3 +z**3 -target)%63==0]
            expected={z for z in range(63)
                      if ((target-x**3-y**3)%9,(target-x**3-y**3)%7)==
                      ((z**3)%9,(z**3)%7)}
            assert set(zset)==expected
    return {"CRT9x7_verified_exhaustive_integer_residue_states":63,
            "all_63x63_pairs_zclass_exhaustively_checked":3969,
            "all_63_residue_values_exhaustively_covered":True,
            "allowed_cubic_signatures_9":sorted(r9),
            "allowed_cubic_signatures_7":sorted(r7),
            "pruning_exact_no_integer_solution_lost":True,
            "target_mod9":target%9,"target_mod7":target%7}

def exact_bounded_universe(target,values,cubes):
    n=len(values)
    map9={c:int(np.count_nonzero(cubes%9==c)) for c in CUBE_RESIDUES_9}
    map63={(a,b):int(np.count_nonzero((cubes%9==a)&(cubes%7==b)))
          for a in CUBE_RESIDUES_9 for b in CUBE_RESIDUES_7}
    rawpairs=n*n
    mod9=sum(mx*my for a,mx in map9.items() for b,my in map9.items()
             if ((target-a-b)%9) in map9)
    mod63=sum(mx*my for (a,u),mx in map63.items()
              for (b,v),my in map63.items()
              if ((target-a-b)%9,(target-u-v)%7) in map63)
    # The exact small-domain reference legitimately contains target values
    # for which NO x,y pair can lead to any cube-residue z signature.
    # A zero eligible-pair universe is a bounded NO-WITNESS certificate,
    # not an internal assertion failure. First 50k source originals were
    # unaffected because their eligible-pair universes were all positive.
    assert 0<=mod63<=mod9<=rawpairs
    return {"original_full_bounded_x_y_pair_universe":rawpairs,
            "mod9_admissible_x_y_pair_universe":mod9,
            "CRT63_admissible_x_y_pair_universe":mod63,
            "full_x_y_pair_universe_over_CRT63":rawpairs/mod63 if mod63 else None,
            "mod9_pair_universe_over_CRT63":mod9/mod63 if mod63 else None,
            "candidate_pair_count_compression_not_wall_speed":True}

def crt63_numeric_exact_search(target,radius):
    ts=time.perf_counter_ns()
    assert 0<radius<=150000
    assert 3*radius**3 < (2**63)-1
    values=np.arange(-radius,radius+1,dtype=np.int64)
    cubes=values**3
    universe=exact_bounded_universe(target,values,cubes)
    buckets={}
    for m9 in CUBE_RESIDUES_9:
        for m7 in CUBE_RESIDUES_7:
            mask=(cubes%9==m9)&(cubes%7==m7)
            buckets[(m9,m7)]=(values[mask],cubes[mask])
    assert len(buckets)==9 and all(len(x)>0 for x,_ in buckets.values())
    combos=0
    comparisons=0
    solution=None
    for (x9,x7),(xs,xc) in buckets.items():
        for (y9,y7),(ys,yc) in buckets.items():
            zkey=((target-x9-y9)%9,(target-x7-y7)%7)
            if zkey not in buckets:continue
            zs,zc=buckets[zkey]
            combos+=1
            for i in range(0,len(xs),CHUNK):
                wanted=target-(xc[i:i+CHUNK,None]+yc[None,:])
                indices=np.searchsorted(zc,wanted)
                xidx,yidx=np.where(indices<len(zc))
                comparisons+=wanted.size
                if len(xidx):
                    truth=zc[indices[xidx,yidx]]==wanted[xidx,yidx]
                    if truth.any():
                        hit=int(np.flatnonzero(truth)[0])
                        a,b=int(xidx[hit]),int(yidx[hit])
                        z=int(zs[indices[a,b]])
                        candidate=(int(xs[i+a]),int(ys[b]),z)
                        assert sum(int(n)**3 for n in candidate)==target
                        assert all(-radius<=n<=radius for n in candidate)
                        solution=candidate
                        break
            if solution is not None:break
        if solution is not None:break
    return {
        "method":"exact_source_rhs_CRT_mod9_mod7_signature_buckets_sorted_two_sum",
        "integer_search_radius":radius,
        "actual_exact_integer_witness":solution,
        "exact_witness_arithmetic_confirmed":None if solution is None else sum(int(n)**3 for n in solution)==target,
        "numeric_search_wall_ms":(time.perf_counter_ns()-ts)/1e6,
        "actual_eligible_source_pairs_probed_before_witness_or_exhaustion":comparisons,
        "complete_eligible_bounded_combinations_if_no_early_witness":universe["CRT63_admissible_x_y_pair_universe"],
        "source_has_no_full_integer_UNSAT_from_bounded_miss":True,
        "no_neural_forward_no_oracle_label":True,
        "analytic_exact_bounded_search_space_count":universe,
    }

def original_case(root,item,radius,category):
    begin=time.perf_counter_ns()
    record={
        "source":item["path"],"expected_original_git_blob":item["sha1_git_blob"],
        "research_split":category,
        "status":"UNKNOWN",
        "original_source_sat_verified_Z3_cvc5":False,
        "unbounded_original_sat_if_numeric_miss":"UNKNOWN"
    }
    try:
        raw=(root/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or git_blob_sha1(raw)!=item["sha1_git_blob"]:
            raise RuntimeError("TRUE_ORIGINAL_SOURCE_SHA_OR_BYTES_CHANGED")
        record["original_authentic_source_sha256"]=sha256(raw)
        target,variables,parsed_original=structural_source(raw)
        record["actual_original_target"]=target
        record["all_source_original_variables"]=variables
        proof=finite_exact_residue_proof(target)
        record["finite_CRT63_mathematical_completeness_certificate"]=proof
        found=crt63_numeric_exact_search(target,radius)
        record["CRT63_bounded_numeric_search"]=found
        guess=found["actual_exact_integer_witness"]
        if guess is not None:
            cert=independent_original_grounded_certificate(
                raw.decode("utf-8"),variables,guess,parsed_original,"SAT")
            record["genuine_original_smt2_Z3_cvc5_independent_SAT"]=cert
            record["original_source_sat_verified_Z3_cvc5"]=cert["independent_dual_result"]
            record["status"]="TRUE_ORIGINAL_SAT_DUAL_CERTIFIED" if cert["independent_dual_result"] else "ABSTAIN_EXACT_NUMERIC_BUT_ORIGINAL_SMT2_NOT_DUAL"
        else:
            record["status"]="UNKNOWN_AFTER_EXACT_BOUNDED_CRT63_RADIUS_50000"
    except Exception as e:
        record["status"]="ABSTAIN_SOURCE_SEMANTIC_OR_SEARCH_ERROR"
        record["error"]=type(e).__name__+":"+str(e)[:380]
    record["full_source_wall_ms"]=(time.perf_counter_ns()-begin)/1e6
    print("G0_CRT63_REAL_ORIGINAL",item["path"],category,
          "TARGET",record.get("actual_original_target"),
          "FOUND",record.get("CRT63_bounded_numeric_search",{}).get("actual_exact_integer_witness"),
          "STATUS",record["status"],
          "NUMERIC_WALL",record.get("CRT63_bounded_numeric_search",{}).get("numeric_search_wall_ms"),
          "ERROR",record.get("error"),flush=True)
    return record

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    c=json.loads(a.contract.read_text())
    m=json.loads(a.freeze.read_text())
    if c["schema"]!="neumann.g0.cubic_posthoc_CRT63_vs_mod9_frozen_expand_to50k.v1" or c["preregistered_new_radius"]!=NEW_RADIUS:
        raise RuntimeError("POSTHOC_PRECOMMITTED_CRT63_PROTOCOL_CHANGED")
    if m["source"].split("@")[-1]!=SOURCE_COMMIT or len(m["first_transfer_cohort"])!=7:
        raise RuntimeError("ORIGINAL_PRIOR_SEVEN_SOURCE_COHORT_CHANGED")
    sources={i["path"].split("/")[-1]:i for i in [m["development_original_STC_0228"],*m["first_transfer_cohort"]]}
    if set(CRITICAL_FIVE+CTRL_THREE)!=set(sources):raise RuntimeError("TARGET_RESELECTED_OR_MISSING")
    controls=[original_case(a.root,sources[name],POS_RADIUS,"PRIOR_SAT_POSITIVE_CONTROL_NOT_NEW")
              for name in CTRL_THREE]
    new=[original_case(a.root,sources[name],NEW_RADIUS,"POSTHOC_EXTENDED_RADIUS_PRIOR_UNKNOWN") for name in CRITICAL_FIVE]
    good_controls=sum(x["original_source_sat_verified_Z3_cvc5"] for x in controls)
    newly=sum(x["original_source_sat_verified_Z3_cvc5"] for x in new)
    report={
      "schema":"neumann.g0.qfnia_posthoc_CRT63_r50000_original_seven_v1",
      "source_original_source_revision":SOURCE_COMMIT,
      "pre_run_protocol_git_commit":CONTRACT_COMMIT,
      "this_is_not_a_sealed_or_first_blind_transfer":True,
      "five_previous_unknown_rows_retained":len(new)==5,
      "three_source_SAT_positive_controls_dual":good_controls,
      "newly_source_SAT_proven_previous_unknown":newly,
      "five_bounded_radius_50000_unknown_or_unverified":5-newly,
      "full_original_integer_UNSAT_from_numeric_miss_never_claimed":True,
      "mod63_filter_lossless_over_all_integer_residue_classes":all(
          x.get("finite_CRT63_mathematical_completeness_certificate",{}).get("pruning_exact_no_integer_solution_lost",False)
          for x in [*controls,*new]),
      "candidate_search_pair_counts_not_runtime_speed_ratios":True,
      "strongest_classical_specialist_can_use_same_filter":True,
      "no_new_neural_or_learned_structure":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
      "previous_true_SAT_positive_controls":controls,
      "previously_unknown_five_originals":new,
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("G0_EXACT_CRT63_THREE_PRIOR_SAT_DUAL",good_controls,"/3")
    print("G0_EXACT_CRT63_FIVE_FORMER_UNKNOWN_NOW_SAT",newly,"/5")
    print("G0_EXACT_CRT63_CANDIDATE_PAIR_REDUCTION_VS_MOD9",{
      x["source"].split("/")[-1]:round(x["CRT63_bounded_numeric_search"]["analytic_exact_bounded_search_space_count"]["mod9_pair_universe_over_CRT63"],3)
      for x in new if "CRT63_bounded_numeric_search" in x})
    print("G0_Q3_Q4_GLOBAL_OPEN",report["global_Q3"],report["global_Q4"])
if __name__=="__main__":
    main()
