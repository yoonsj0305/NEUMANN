"""External published Darmon-Merel result as explicit theorem premise.

NO new model innovation: for THREE previously opened original full 3x3 magic
n-th power (n=3,4,5) SMT-LIB source problems, independently prove source
linear sum constraints entail non-trivial 3-term power arithmetic progression,
and verify native source strict positivity and all three pairwise distinct.
Known deep theorem then excludes the original full integer solutions.

The Z3 and cvc5 certificates ONLY verify the original source -> arithmetic
progression implication, NOT the external deep number-theoretic theorem.
Never call this a self-contained formal SMT proof or new math result.
Original semimagic source controls must safely ABSTAIN from theorem.
"""
from __future__ import annotations
import argparse,json,subprocess,time
from pathlib import Path
import z3
from research.evidence.q3_original_3x3_rank_20261021.exact_true_original_magic_power_rowspace_dual import (
    parse_true_source_linear_skeleton,row_qflia
)
from research.evidence.q3_power_feature_20261021.first_ten_unchanged_power_magic_original_unbounded_unsat import (
    original_positive,original_distinct
)
from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import git_blob_sha1,sha256

UPSTREAM="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"
EXTERNAL_LEMMA="Darmon-Merel 1997, n>=3 no three distinct positive nth powers in arithmetic progression; cited by Hajdu 2004, Acta Arithmetica 113.4 p343"
EXTERNAL_CITATION="https://www.impan.pl/shop/en/publication/transaction/download/product/83315"
PRE_RUN="7526ef89241594793eefe36c6337bc073ed53463"

def independent_entailment(source_rows,columns,power):
    names=[f"formal_{i}" for i in range(len(columns))]
    top=f"x_0_1^{power}";middle=f"x_1_1^{power}";bottom=f"x_2_1^{power}"
    if any(k not in columns for k in (top,middle,bottom)):
        raise ValueError("ACTUAL_ORIGINAL_SOURCE_LACKS_THREE_CENTER_POWER_FEATURES")
    a,b,c=[columns.index(k) for k in (top,middle,bottom)]
    x=[z3.Int(t) for t in names]
    s=z3.Solver();s.set(timeout=4000)
    for row in source_rows:
        s.add(z3.Sum(*[int(q)*v for q,v in zip(row,x)])==0)
    s.add(x[a]+x[c]!=2*x[b])
    status=str(s.check()).upper()
    lines=["(set-logic QF_LIA)"]
    lines.extend(f"(declare-fun {v} () Int)" for v in names)
    lines.extend("(assert "+row_qflia(row,names)+")" for row in source_rows)
    lines.append(f"(assert (not (= (+ {names[a]} {names[c]}) (* 2 {names[b]}))))")
    lines+=["(check-sat)","(exit)"]
    payload="\n".join(lines)+"\n"
    try:
        p=subprocess.run(["cvc5","--lang=smt2","--tlimit-per=4000","-"],
                         input=payload,text=True,capture_output=True,timeout=6)
        output=[q.strip().upper() for q in p.stdout.splitlines() if q.strip().lower() in ("sat","unsat","unknown")]
        cvc=output[0] if p.returncode==0 and output else "UNKNOWN"
        code=p.returncode
        error=p.stderr[:150]
    except Exception as e:
        cvc="UNKNOWN_EXCEPTION";code=None;error=type(e).__name__
    return {
      "exact_source_three_center_original_variable_names":[top,middle,bottom],
      "actual_original_source_linear_sum_to_AP_Z3":status,
      "actual_original_source_linear_sum_to_AP_cvc5":cvc,
      "two_independent_provers_agree":status==cvc and status in ("SAT","UNSAT"),
      "full_original_sums_entail_three_power_AP_DUAL":status==cvc=="UNSAT",
      "full_original_sums_DO_NOT_entail_AP_DUAL":status==cvc=="SAT",
      "proof_QF_LIA_sha256":sha256(payload.encode()),
      "checker_cvc5_exit":code,"checker_stderr_excerpt":error,
      "this_only_proves_original_source_TO_AP_not_the_external_deep_theorem":True
    }

def one(root,item):
    start=time.perf_counter_ns()
    row={"path":item["path"],"true_original_source_sha_authenticated":False,
         "status":"ABSTAIN","original_unbounded_UNSAT_conditional_on_EXTERNAL_PUBLISHED_theorem":False,
         "external_number_theory_not_formally_proved_in_this_repository":True}
    try:
        raw=(root/item["path"]).read_bytes()
        if len(raw)!=item["bytes"] or git_blob_sha1(raw)!=item["sha1_git_blob"]:
            raise RuntimeError("EXACT_TRUE_ORIGINAL_SOURCE_SHA_OR_BYTES_CHANGED")
        row["true_original_source_sha_authenticated"]=True
        row["original_source_sha256"]=sha256(raw)
        src=z3.Solver();src.from_string(raw.decode("utf-8"))
        assertions=list(src.assertions())
        spec,lines=parse_true_source_linear_skeleton(src)
        kvalues=spec["native_power_exponents"]
        if len(kvalues)!=1:raise RuntimeError("MIXED_ORIGINAL_POWER_DEGREES")
        k=int(kvalues[0]);row["true_original_source_power_k"]=k
        bridge=independent_entailment(lines,spec["columns"],k)
        row["source_3x3_actual_original_to_three_term_AP_dual"]=bridge
        symbols=["x_0_1","x_1_1","x_2_1"]
        positivity=[original_positive(assertions,n) for n in symbols]
        distinct=[original_distinct(assertions,a,b) for a,b in (
            ("x_0_1","x_1_1"),("x_0_1","x_2_1"),("x_1_1","x_2_1"))]
        row["original_three_variables_all_strictly_positive_NATIVE"]=all(v is not None for v in positivity)
        row["original_three_variables_pairwise_distinct_NATIVE"]=all(v is not None for v in distinct)
        row["original_native_positivity_source_AST_SHA"]=[None if v is None else v["true_original_positive_ast_sha256"] for v in positivity]
        row["original_native_distinctness_source_AST_SHA"]=[None if v is None else v["true_original_distinct_ast_sha256"] for v in distinct]
        row["source_necessary_original_sum_row_SHA"]=[s["source_ast_sha256"] for s in spec["source_rows"]]
        row["source_has_8_full_3x3_magic_sum_constraints"]=spec["matched_source_sum_ast_count"]==8
        all_ok=(k>=3 and row["original_three_variables_all_strictly_positive_NATIVE"]
                and row["original_three_variables_pairwise_distinct_NATIVE"]
                and row["source_has_8_full_3x3_magic_sum_constraints"]
                and bridge["full_original_sums_entail_three_power_AP_DUAL"])
        row["original_unbounded_UNSAT_conditional_on_EXTERNAL_PUBLISHED_theorem"]=bool(all_ok)
        if all_ok:
            row["status"]="SOURCE_ORIGINAL_UNBOUNDED_UNSAT_ASSUMING_PUBLISHED_DARMON_MEREL_THEOREM"
            row["external_theorem_number_theory"]=EXTERNAL_LEMMA
            row["external_theorem_link"]=EXTERNAL_CITATION
            row["full_source_machine_certification_only_COVERS_source_to_theorem_PREMISES"]=True
        else:
            row["status"]="UNKNOWN_EXTERNAL_THEOREM_PRECONDITIONS_NOT_ALL_PROVED"
    except Exception as e:
        row["status"]="ABSTAIN_REAL_SOURCE_AST_OR_THEOREM_ERROR"
        row["error"]=type(e).__name__+":"+str(e)[:360]
    row["actual_original_source_parse_and_mathematical_bridge_cost_ms"]=(time.perf_counter_ns()-start)/1e6
    print("Q3_PUBLISHED_EXTERNAL_THEOREM_REAL_ORIGINAL",item["path"].split("/")[-1],
          "K",row.get("true_original_source_power_k"),
          "AP",row.get("source_3x3_actual_original_to_three_term_AP_dual",{}).get("full_original_sums_entail_three_power_AP_DUAL"),
          "LITERATURE_CONDITIONAL_UNSAT",row["original_unbounded_UNSAT_conditional_on_EXTERNAL_PUBLISHED_theorem"],
          "STATUS",row["status"],"ERR",row.get("error"),flush=True)
    return row

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--freeze",type=Path,required=True)
    ap.add_argument("--contract",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    c=json.loads(a.contract.read_text());f=json.loads(a.freeze.read_text())
    if c["schema"]!="neumann.q3.source_original_power_magic_external_deep_number_theory_v1":
        raise RuntimeError("PUBLISHED_THEOREM_PROTOCOL_CHANGED")
    if f["source"].split("@")[-1]!=UPSTREAM or len(f["five_original_3x3_controls"])!=5:
        raise RuntimeError("AUTHENTIC_ORIGINAL_SHA_COHORT_CHANGED")
    out=[one(a.root,p) for p in f["five_original_3x3_controls"]]
    admitted=sum(q["original_unbounded_UNSAT_conditional_on_EXTERNAL_PUBLISHED_theorem"] for q in out)
    report={
      "schema":"neumann.q3.posthoc_five_originals_literature_derivation_darmon_merel_v1",
      "pre_run_external_theorem_and_all_case_frozen_commit":PRE_RUN,
      "all_previously_opened_five_originals_retained":len(out)==5,
      "original_SHA_authenticated_count":sum(q["true_original_source_sha_authenticated"] for q in out),
      "source_3x3_full_magic_external_theorem_conditions_verified_and_CLASSICAL_UNSAT_count":admitted,
      "this_is_NOT_a_self_contained_formal_proof_of_number_theory":True,
      "external_known_theorem_provided_as_separate_trusted_literature_premise":True,
      "external_peer_reviewed_reference":EXTERNAL_CITATION,
      "do_not_count_these_as_Neumann_unique_or_neural_structure_discovery":True,
      "independent_Z3_cvc5_certification_SCOPE":"ONLY the necessary source full magic sums -> nontrivial 3-term arithmetic progression, plus original positivity/distinct AST checks",
      "full_original_direct_3sec_generic_old_result":"0/5 previously passed PR358, no fresh raw comparison claimed here",
      "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
      "five_originals":out}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("Q3_LITERATURE_DERIVED_SOURCE_TRUE_CONDITIONAL_UNSAT",admitted,"/5")
    print("Q3_ORIGINAL_SOURCE_PUBLISHED_EXTERNAL_THEOREM_SCOPE_NOT_SELF_CONTAINED_FORMAL",True)
    print("Q3_GLOBAL_Q3_Q4",report["global_Q3"],report["global_Q4"])
if __name__=="__main__":
    main()
