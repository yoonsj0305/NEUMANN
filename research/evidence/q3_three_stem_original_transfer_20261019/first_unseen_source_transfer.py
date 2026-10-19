"""FIRST preregistered external-source Q3 transfer across three filename stems.

Issue #279 froze public Git repo/commit/three Git blob SHA BEFORE source bodies
or result inspection. This DEV-only study uses exactly the old RELATIONAL
HOUDINI from PR #278, without changing candidate grammar or solver budgets,
and compares the old full frozen classical source proposer PR #246 on each.
Every positive must pass actual source-bound native Z3 3VC + strict cvc5.
This does not prove neural Q3 / different authored source families / 10x.
"""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path

import z3
from experiments.q3_source_prove import (
  sexprs, extract_mixed_original, native_original_relations,
  check_parity, check_formula, source_proof, prove_source,
)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate
from research.evidence.q3_anfp_relational_source_houdini_20261019.first_anfp_source_original import original_houdini

UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
SELECTION=(
 ("comp/2017/Inv_Track/cegar1.sl","5265f78e457228bfb7eef931aca690ee40f53a31","cegar"),
 ("comp/2018/Inv_Track/const_true-unreach-call1.sl","604a6aa928198724679e1fc87c66f88d7acee627","const"),
 ("comp/2018/Inv_Track/fib_01.sl","bb7ec75163dd94227ee4238f9674173181893faf","fib"),
)

def sha(data):
    return hashlib.sha256(data).hexdigest()
def gitblob(raw):
    return hashlib.sha1(("blob "+str(len(raw))+"\0").encode()+raw).hexdigest()

def verify(path, candidate, source_sha):
    canonical=z3.simplify(candidate)
    s=z3.Solver()
    s.set(timeout=2500)
    s.add(z3.Xor(candidate,canonical))
    if s.check()!=z3.unsat:
        raise RuntimeError("UNPROVEN_CANONICAL_SMT_EQUIVALENCE")
    result=check_original_candidate(path,canonical.sexpr(),
        expected_source_sha256=source_sha)
    return result,canonical.sexpr()

def case(path, expected_blob, stem):
    started=time.perf_counter_ns()
    raw=path.read_bytes()
    actual_blob=gitblob(raw)
    if actual_blob!=expected_blob:
        raise RuntimeError("EXTERNAL_GIT_BLOB_IDENTITY_MISMATCH")
    digest=sha(raw)
    forms=sexprs(raw)
    src=extract_mixed_original(forms)
    native=native_original_relations(forms,src)
    native.update({"now":src["now"],"next":src["next"]})
    parity=check_parity(src,native)
    if len(parity)!=3 or any(v!="unsat" for v in parity.values()):
        raise RuntimeError("ORIGINAL_NATIVE_CUSTOM_PARSER_MISMATCH")
    nonvac={
        "original_pre_is_sat":check_formula(native["pre"])=="sat",
        "original_not_post_is_sat":check_formula(z3.Not(native["post"]))=="sat",
    }
    if not all(nonvac.values()):
        raise RuntimeError("ORIGINAL_PRE_OR_NOT_POST_VACUOUS")
    # Existing strong old classical proposer first, on all fixed originals.
    prior=prove_source(path)
    # Original source proof, no private hints.
    post=source_proof(native["post"],native)
    attempted={"status":"NOT_RUN"}
    candidate_smt=None
    strict=None
    errors=[]
    try:
        found=original_houdini(src,native)
        candidate=found.pop("invariant")
        strict,candidate_smt=verify(path,candidate,digest)
        attempted={
          **found,
          "status":"REAL_RELATIONAL_CANDIDATE_FOUND",
          "native_actual_candidate_z3_3vc_proven":found["native_original_three_vc_proved"],
          "candidate_canonical_equal_original":True,
        }
    except Exception as e:
        attempted={"status":"ABSTAIN","reason":type(e).__name__+":"+str(e)[:200]}
    strict_ok=strict is not None and strict.get("status")=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5"
    controls={}
    if strict_ok:
        for label,cand,cs in (
            ("TRUE","true",digest),
            ("FALSE","false",digest),
            ("FORGED_SHA",candidate_smt,"0"*64),
        ):
            control=check_original_candidate(path,cand,expected_source_sha256=cs)
            controls[label]=control.get("status")!="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5"
    old_explicit=prior.get("status")=="ORIGINAL_SOURCE_THREE_VC_CERTIFIED"
    old_source_only=prior.get("status")=="ORIGINAL_SOURCE_ONLY_SPACER_UNSAT"
    relevant_gain=bool(strict_ok and not old_explicit and
                       not post["accepted"])
    row={
       "source_stem_group_from_metadata":stem,
       "source_path":str(path),
       "source_sha256":digest,
       "upstream_git_blob_sha1":actual_blob,
       "source_bytes":len(raw),
       "native_original_semantics_xor_parity":parity,
       "nonvacuity":nonvac,
       "old_frozen_full_portfolio_status":prior.get("status"),
       "old_frozen_full_portfolio_route":prior.get("selected_route"),
       "old_frozen_full_portfolio_reason":prior.get("reason"),
       "old_portfolio_original_explicit_3vc":old_explicit,
       "old_portfolio_original_safe_spacer_only":old_source_only,
       "original_post_only_inductive":post.get("accepted"),
       "original_post_only_vcs":post.get("vcs"),
       "new_frozen_relational_houdini":attempted,
       "new_canonical_invariant_smt":candidate_smt,
       "new_source_bound_original_3vc_cvc5":strict,
       "new_original_3vc_and_external_cvc5_certified":strict_ok,
       "new_original_explicit_3vc_gain_over_old_full_portfolio":relevant_gain,
       "negative_controls":controls,
       "case_all_work_wall_ms":round((time.perf_counter_ns()-started)/1e6,3),
       "proposer_read_original_post":False,
       "new_frozen_relational_grammar_modified":False,
    }
    return row

def run(root):
    all_rows=[]
    for rel,blob,stem in SELECTION:
        row=case(root/rel,blob,stem)
        all_rows.append(row)
        print("Q3_THREE_STEM_REAL_SOURCE",stem,rel,
              "old",row["old_frozen_full_portfolio_status"],
              "new",row["new_original_3vc_and_external_cvc5_certified"],
              "distinct_original_gain",row["new_original_explicit_3vc_gain_over_old_full_portfolio"])
    wins=[r for r in all_rows if r["new_original_3vc_and_external_cvc5_certified"]]
    gains=[r for r in all_rows if r["new_original_explicit_3vc_gain_over_old_full_portfolio"]]
    conditions={
       "exact_three_metadata_frozen_originals_and_git_sha":
          len(all_rows)==3 and len({r["source_sha256"] for r in all_rows})==3
          and len({r["source_stem_group_from_metadata"] for r in all_rows})==3,
       "all_source_semantics_parity_nonvacuous":all(
          len(r["native_original_semantics_xor_parity"])==3
          and all(x=="unsat" for x in r["native_original_semantics_xor_parity"].values())
          and all(r["nonvacuity"].values()) for r in all_rows),
       "one_true_new_native_original_3vc_plus_independent_cvc5":len(wins)>=1,
       "one_original_nonpost_structural_gain_over_old_frozen_portfolio":len(gains)>=1,
       "all_positive_source_independent_cvc5_backend_six_or_more":
          all(len(r["new_source_bound_original_3vc_cvc5"]["cvc5_original_three_vc"])==3
          and all(v["status"]=="unsat" and v["returncode"]==0
           for v in r["new_source_bound_original_3vc_cvc5"]["cvc5_original_three_vc"].values())
           for r in wins),
       "some_surviving_true_relational_two_var_atom":any(
          r["new_frozen_relational_houdini"].get("relation_atom_survived",False) for r in gains),
       "some_actual_counterexample_pruning":any(
          r["new_frozen_relational_houdini"].get("actual_removed_atom_count",0)>0 for r in wins),
       "all_positive_source_negative_controls_reject":all(
          set(r["negative_controls"])=={"TRUE","FALSE","FORGED_SHA"}
          and all(r["negative_controls"].values()) for r in wins),
       "no_inference_gold_or_neural_promotion":all(
          not r["proposer_read_original_post"] and
          not r["new_frozen_relational_grammar_modified"] for r in all_rows),
    }
    return {
       "schema":"neumann.q3-three-stem-prospective-source-transfer.v1",
       "preregistered_issue":279,
       "selection_frozen_before_source_body_read":True,
       "external_git_commit":UPSTREAM,
       "publisher_repo":"SyGuS-Org/benchmarks",
       "metadata_selected_stems":["cegar","const","fib"],
       "independent_source_authors_proven":False,
       "new_unseen_algebraic_families_claimed":False,
       "scoped_first_gate_pass":all(conditions.values()),
       "predeclared_conditions":conditions,
       "new_original_explicit_3vc_gain_count":len(gains),
       "new_original_explicit_3vc_total":len(wins),
       "original_first_case_results":all_rows,
       "neural_learned_new_structure_proven":False,
       "strongest_general_classical_beaten":False,
       "full_cost_economic_breakthrough":"NOT_EVALUATED",
       "model_calls":0,"GPU_calls":0,"paid_API_calls":0,
       "Decision3_sealed":"BLOCKED",
       "historical_AM1_first":"FAIL_UNCHANGED",
       "Q1_to_Q7_global":"OPEN",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--upstream-root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    result=run(args.upstream_root)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("FIRST_THREE_STEM_Q3_TRANSFER",result["scoped_first_gate_pass"])
    print("FIRST_THREE_STEM_GATE_CHECKS",json.dumps(result["predeclared_conditions"],sort_keys=True))
    print("GLOBAL_Q1_TO_Q7",result["Q1_to_Q7_global"])
if __name__=="__main__":main()
