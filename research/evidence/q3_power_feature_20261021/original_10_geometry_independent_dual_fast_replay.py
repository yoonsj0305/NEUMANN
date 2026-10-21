"""Fast independent source-native replay when matched original nonlinear Direct
uses excessive CI wall. Does NOT replace original FIRST attempt and does
NOT infer a raw Direct speed/gap. All ten source Git identities remain frozen
before their first original bodies were opened at 941ec4d1.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import z3
from research.evidence.q3_power_feature_20261021.first_ten_unchanged_power_magic_original_unbounded_unsat import (
  original_exact_geometry,independent_necessary_linear_certificate,
  theorem_positive_injectivity_controls,IDENTITY_FREEZE,UPSTREAM
)
from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import git_blob_sha1,sha256

def one(root,item,split):
    started=time.perf_counter_ns()
    out={"source":item["path"],"group":split,"genuine_original_authenticated":False,
         "source_injective_UNSAT_dual_pass":False,"status":"UNKNOWN"}
    try:
        raw=(root/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or git_blob_sha1(raw)!=item["sha1_git_blob"]:
            raise RuntimeError("TRUE_ORIGINAL_SOURCE_GIT_SHA_MISMATCH")
        out["genuine_original_authenticated"]=True
        out["original_sha256"]=sha256(raw)
        s=z3.Solver();s.from_string(raw.decode("utf-8"))
        out["raw_original_full_assertions"]=len(s.assertions())
        geom=original_exact_geometry(list(s.assertions()))
        out["source_geometry"]=geom
        if geom:
            q=independent_necessary_linear_certificate(geom)
            out["independent_dual_original_necessary_QFLIA"]=q
            out["source_injective_UNSAT_dual_pass"]=q["both_independent_unbounded_necessary_condition_UNSAT"]
            out["status"]="TRUE_ORIGINAL_UNBOUNDED_UNSAT_SOUND_SOURCE_GEOMETRY" if out["source_injective_UNSAT_dual_pass"] else "ABSTAIN_FAILED_INDEPENDENT_LINEAR_CERT"
        else:
            out["status"]="UNKNOWN_NO_VALID_ORIGINAL_SOURCE_GEOMETRIC_CERTIFICATE"
    except Exception as e:
        out["status"]="ABSTAIN_ERROR"
        out["error"]=type(e).__name__+":"+str(e)[:300]
    out["authentic_source_parse_and_independent_proof_ms"]=(time.perf_counter_ns()-started)/1e6
    print("Q3_TRUE_POWER_MAGIC_FAST_ORIGINAL",out["source"].split("/")[-1],
          "GROUP",split,"CERT",out["source_injective_UNSAT_dual_pass"],
          "STATUS",out["status"],"ERROR",out.get("error"),flush=True)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--freeze",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    x=ap.parse_args()
    f=json.loads(x.freeze.read_text())
    if f["schema"]!="neumann.q3.first_original_10_power_features_magic_semimagic_geometric_injective.v1" or f["source"].split("@")[-1]!=UPSTREAM:
        raise RuntimeError("SOURCE_PRE_FROZEN_CONTRACT_CHANGED")
    assert [len(f[z]) for z in ("five_original_2x2_targets","five_original_3x3_controls","two_previously_opened_development_controls")]==[5,5,2]
    controls=theorem_positive_injectivity_controls()
    rows=[]
    for source,split in (("five_original_2x2_targets","FIRST_SOURCE_2X2"),
                         ("five_original_3x3_controls","FIRST_SOURCE_3X3"),
                         ("two_previously_opened_development_controls","OPENED_DEV")):
        rows.extend(one(x.root,t,split) for t in f[source])
    result={
      "schema":"neumann.q3.original10_power_geometry_independent_fast_replay.v1",
      "original_git_sha_source_locked_prior_first_content":IDENTITY_FREEZE,
      "this_run_is_after_original_first_source_look_not_first_trial":True,
      "historical_first_full_original_direct_CI_is_independent_and_untouched":True,
      "original_source_authenticated_count":sum(r["genuine_original_authenticated"] for r in rows[:10]),
      "five_true_original_power2x2_unbounded_unsat":sum(r["source_injective_UNSAT_dual_pass"] for r in rows[:5]),
      "five_source3x3_proved_unsat":sum(r["source_injective_UNSAT_dual_pass"] for r in rows[5:10]),
      "previous_two_opened_positive_controls":sum(r["source_injective_UNSAT_dual_pass"] for r in rows[10:]),
      "no_original_raw_direct_claim_or_measured_speed_ratio":True,
      "finite_8_powers_exact_factorization_guards":controls,
      "same_algorithm_permission_strong_classical_Direct":True,
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
      "cases":rows,
    }
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("Q3_FAST_TEN_TRUE_ORIGINAL_AUTHENTIC",result["original_source_authenticated_count"],"/10")
    print("Q3_FAST_NEW_FIVE_2X2_UNBOUNDED_UNSAT",result["five_true_original_power2x2_unbounded_unsat"],"/5")
    print("Q3_FAST_NEW_FIVE_3X3_UNBOUNDED_UNSAT",result["five_source3x3_proved_unsat"],"/5")
    print("Q3_FAST_PREVIOUS_2X2_DEV_POSITIVES",result["previous_two_opened_positive_controls"],"/2")
if __name__=="__main__":
    main()
