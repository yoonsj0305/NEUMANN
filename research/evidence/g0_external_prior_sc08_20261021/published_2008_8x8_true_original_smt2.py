"""PUBLIC PRIOR ART example, NEVER counted as NEUMANN Q3 invented solution.

Walter Trump's published 8x8 magic square of distinct positive cube bases
(2008), as transcribed in Plus Magazine, https://plus.maths.org/comment/8496
This official source STC contest instance SC_08 was already opened.
The external 64-number witness is **supplied from literature**, not created
by any Neumann model/algorithm. It is a sound source-original positive
oracle-reference control only. External prior art must never be presented as
first unseen source autonomous success.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import z3
from research.evidence.g0_cubic_mod9_20261021.first_seven_frozen_originals_exact_mod9_cubes import (
    independent_original_grounded_certificate
)
from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import (
    git_blob_sha1,sha256
)

SOURCE="non-incremental/QF_NIA/20220315-MathProblems/SC_08.smt2"
SOURCE_COMMIT="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"
SOURCE_GIT_BLOB="2641f701a4d085737d12c7924a7511c9e25a381a"
SOURCE_BYTES=71254
PRIOR_ART="https://plus.maths.org/comment/8496"
PUBLIC_TRUMP_2008_BASES=[
 [11,9,15,61,18,40,27,68],
 [21,34,64,57,32,24,45,14],
 [38,3,58,8,66,2,46,10],
 [63,31,41,30,13,42,39,50],
 [37,51,12,6,54,65,23,19],
 [47,36,43,33,29,59,52,4],
 [55,53,20,49,25,16,5,56],
 [1,62,26,35,48,7,60,22]
]

def certificate(root):
    start=time.perf_counter_ns()
    rec={"authentic_original_source":SOURCE,"source_git_blob":SOURCE_GIT_BLOB,
         "witness_origin":"EXTERNAL_PRIOR_ART_RETRIEVED_2008_WALTER_TRUMP",
         "witness_reference_url":PRIOR_ART,
         "not_original_discovery":True,
         "not_prospective_first_blind_source":True,
         "not_neural_generated":True,"not_new_algorithm":True,
         "original_SMT2_SAT_independent_dual":False,"status":"ABSTAIN"}
    try:
        raw=(root/SOURCE).read_bytes()
        if len(raw)!=SOURCE_BYTES or git_blob_sha1(raw)!=SOURCE_GIT_BLOB:
            raise RuntimeError("AUTHENTIC_SMT2_SOURCE_HASH_OR_LENGTH_CHANGED")
        rec["authentic_original_source_sha256"]=sha256(raw)
        m=PUBLIC_TRUMP_2008_BASES
        vals=[int(v) for row in m for v in row]
        assert len(vals)==64 and min(vals)>0 and len(set(vals))==64
        row_sums=[sum(v**3 for v in row) for row in m]
        col_sums=[sum(m[i][j]**3 for i in range(8)) for j in range(8)]
        diagonals=[sum(m[i][i]**3 for i in range(8)),
                   sum(m[i][7-i]**3 for i in range(8))]
        assert len(set(row_sums+col_sums+diagonals))==1
        t=row_sums[0]
        assert t==636363
        rec["external_prior_math_check"]={
            "all_64_base_numbers_positive_distinct":True,
            "all_8_row_exact_cube_sums":row_sums,
            "all_8_column_exact_cube_sums":col_sums,
            "both_diagonal_exact_cube_sums":diagonals,
            "original_common_cube_sum_t":t
        }
        original=z3.Solver()
        original.from_string(raw.decode("utf-8"))
        rec["original_SMT2_statement_count"]=len(original.assertions())
        names=[f"x_{i}_{j}" for i in range(8) for j in range(8)]+["t"]
        grounds=vals+[t]
        cert=independent_original_grounded_certificate(raw.decode("utf-8"),names,
                    grounds,original,"SAT")
        rec["true_original_entire_SMT2_source_dual_Z3_and_cvc5"]=cert
        rec["original_SMT2_SAT_independent_dual"]=cert["independent_dual_result"]
        rec["status"]="PUBLIC_REFERENCE_INDEPENDENT_ORIGINAL_QFNIA_SAT_PROVED" if cert["independent_dual_result"] else "ABSTAIN_UNVERIFIED_PUBLIC_REFERENCE"
        bad=[list(row) for row in m];bad[0][0]+=1
        negrow=sum(v**3 for v in bad[0])
        rec["external_math_negative_control_modified_one_entry"]={
            "mutation":"CHANGE_PUBLIC_REFERENCE_FIRST_BASE_BY_PLUS_ONE",
            "negative_row_cube_sum":negrow,
            "unchanged_other_row_cube_sum":t,
            "source_row_constraint_false":negrow!=t,
            "source_distinct_constraint_also_false":bad[0][0] in {
                bad[i][j] for i in range(8) for j in range(8)
                if (i,j)!=(0,0)
            },
            "no_claim_of_second_solver_UNSAT_without_actual_check":True
        }
    except Exception as e:
        rec["status"]="ABSTAIN_EXCEPTION"
        rec["error"]=type(e).__name__+":"+str(e)[:380]
    rec["whole_true_source_verification_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    print("G0_EXTERNAL_PRIOR_ART_SC08_SOURCE",rec["status"],
          "DUAL",rec["original_SMT2_SAT_independent_dual"],
          "TIME",round(rec["whole_true_source_verification_wall_ms"],2),
          "ERROR",rec.get("error"),flush=True)
    return rec

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    x=ap.parse_args()
    rec=certificate(x.root)
    output={
        "schema":"neumann.G0.SC08_original_external_prior_art_positive_control.v1",
        "official_original_source_revision":SOURCE_COMMIT,
        "source_and_reference_opened_before_experiment":True,
        "external_web_literature_is_an_oracle_not_NEUMANN_research_answer":True,
        "do_not_count_this_as_genuine_unknown_first_2026_G0_solution":True,
        "source_reproduced_from_2008_external_math":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q7":"OPEN",
        "original_prior_art_example":rec
    }
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(output,sort_keys=True,indent=2)+"\n")
    print("G0_PUBLIC_REFERENCE_SC08_ORIGINAL_SMT2_DUAL",rec["original_SMT2_SAT_independent_dual"])
    print("NOT_NEUMANN_ORIGINAL_DISCOVERY",output["external_web_literature_is_an_oracle_not_NEUMANN_research_answer"])
if __name__=="__main__":
    main()
