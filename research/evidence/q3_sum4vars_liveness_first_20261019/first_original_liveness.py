"""First POSTHOC Q3 development: goal-safe dead-state elimination before Pre-tight invariant search.

Preregistered Issue #285 AFTER FIRST blind Issue #283 FAIL. This source was
already inspected, so this cannot count as unseen Q6 or blind Q3 generality.
Objective: mathematically safe dropping of entirely UNUSED state coordinates,
then unchanged source-Pre-tight sparse Houdini, then strengthen with original
Post only AFTER source-only relational structure has been fixed.
Final source ORIGINAL remains unprojected; independent Z3+cvc5 checks real 3VC.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
import z3
from z3.z3util import get_vars

from experiments.q3_source_prove import (
    sexprs, extract_mixed_original, native_original_relations,
    check_parity, check_formula, source_proof, prove_source,
)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate
from research.evidence.q3_cegar_pre_tight_facets_20261019.first_original_tight_facet import (
    pre_tight_source_atoms,exact_counterexample_pruning,
)

SCHEMA="neumann.q3.sum4vars.deadstate-source-tight.post-strengthen.dev.v1"
OFFICIAL="comp/2017/Inv_Track/sum4_vars.sl"
GIT_COMMIT="13c8deb68a873635879c9a69bc78caebd340f646"
EXPECTED_GIT_BLOB="ba2a948d21a8b64a6ede2a441448118736792172"

def sha(b):
    return hashlib.sha256(b).hexdigest()

def blob(b):
    return hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()

def safe_used_states(original,native):
    """Drop only coordinates absent in ALL original actual public source relations.

    This is exact syntactic dead-state elimination, no quantifier
    elimination, no Post-based solution choice or raw symbolic substitution.
    Both original Pre/Trans/Post stay UNCHANGED in original proof.
    """
    used_symbols=set()
    for predicate in (native["pre"],native["trans"],native["post"]):
        used_symbols.update(v.decl().name() for v in get_vars(predicate))
    zipped=list(zip(original["now"],original["next"]))
    keep=[]
    drop=[]
    for now,next_ in zipped:
        if now.decl().name() in used_symbols or next_.decl().name() in used_symbols:
            keep.append((now,next_))
        else:
            drop.append((now,next_))
    if not keep:raise RuntimeError("NO_ACTIVE_SYMBOLIC_STATE")
    # Original propositions must contain NO dropped symbols or the
    # reduction would change the transition relation/goals.
    for now,nxt in drop:
        if now.decl().name() in used_symbols or nxt.decl().name() in used_symbols:
            raise RuntimeError("PROJECTION_DROPS_USED_PUBLIC_SOURCE_SYMBOL")
    reduced=dict(original)
    reduced["now"]=[now for now,_ in keep]
    reduced["next"]=[nxt for _,nxt in keep]
    details={
       "original_state_coordinates":len(zipped),
       "projected_live_coordinates":len(keep),
       "provably_unused_dead_coordinates":len(drop),
       "retained_public_source_state_names":[x.decl().name() for x,_ in keep],
       "dropped_public_source_state_names":[x.decl().name() for x,_ in drop],
       "all_syntactic_public_pre_trans_post_symbols":sorted(used_symbols),
       "all_dropped_symbols_absent_from_original_three_public_relations":True,
       "the_original_Pre_Trans_Post_formula_objects_remain_unchanged":True,
    }
    return reduced,details

def certify(path,source_sha,inv):
    canonical=z3.simplify(inv)
    s=z3.Solver()
    s.set(timeout=3000)
    s.add(z3.Xor(inv,canonical))
    if s.check()!=z3.unsat:
        raise RuntimeError("CANONICAL_ORIGINAL_INVARIANT_XOR_NOT_UNSAT")
    direct=check_original_candidate(path,canonical.sexpr(),
       expected_source_sha256=source_sha)
    return {
       "status":direct.get("status"),
       "original_source_sha256":source_sha,
       "original_three_vc_native":direct.get("native_original_three_vc"),
       "independent_cvc5_three_vc":direct.get("cvc5_original_three_vc"),
       "source_bound_original":direct.get("original_source_bound",False),
       "accepted":direct.get("status")=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5",
       "exact_submitted_invariant_smt2":canonical.sexpr(),
       "raw_and_canonical_semantically_equivalent_xor_unsat":True,
    }

def original_study(source):
    wall=time.perf_counter_ns()
    raw=source.read_bytes()
    if blob(raw)!=EXPECTED_GIT_BLOB:
        raise RuntimeError("REGISTERED_OFFICIAL_ORIGINAL_GIT_BLOB_MISMATCH")
    digest=sha(raw)
    original=extract_mixed_original(sexprs(raw))
    native=native_original_relations(sexprs(raw),original)
    native.update({"now":original["now"],"next":original["next"]})
    parity=check_parity(original,native)
    if len(parity)!=3 or any(x!="unsat" for x in parity.values()):
        raise RuntimeError("ORIGINAL_SOURCE_NATIVE_CUSTOM_PARSER_DISAGREEMENT")
    if check_formula(native["pre"])!="sat" or check_formula(
       z3.Not(native["post"]))!="sat":
        raise RuntimeError("ORIGINAL_PRE_OR_POST_VACUOUS")
    historical=prove_source(source)
    postonly=source_proof(native["post"],native)
    old_cap_status="NOT_RUN"
    try:
        pre_tight_source_atoms(original,native)
        old_cap_status="UNEXPECTEDLY_SUPPORTED_ALL_STATES"
    except Exception as e:
        old_cap_status=type(e).__name__+":"+str(e)[:120]
    reduced,projection=safe_used_states(original,native)
    t0=time.perf_counter_ns()
    atoms,opt_proofs,extras=pre_tight_source_atoms(reduced,native)
    discovered=exact_counterexample_pruning(atoms,native)
    R=discovered.pop("invariant")
    search_ms=(time.perf_counter_ns()-t0)/1e6
    raw_proof=source_proof(R,native)
    # The original published Post is appended ONLY AFTER R is frozen.
    # NEVER strengthen with arbitrary learned gold answer or solve names.
    full_candidate=z3.And(R,native["post"])
    full_native=source_proof(full_candidate,native)
    verified=certify(source,digest,full_candidate)
    negatives={}
    for name,term,source_identity in (
        ("TRUE","true",digest),
        ("FALSE","false",digest),
        ("FORGED_ORIGINAL_SHA",verified["exact_submitted_invariant_smt2"],"0"*64),
        ("SMT_COMMAND_INJECTION","(assert false)",digest),
    ):
        neg=check_original_candidate(source,term,
                  expected_source_sha256=source_identity)
        negatives[name]={
            "source_bound_original_status":neg["status"],
            "correctly_rejected":neg["status"]!="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5",
        }
    live_relational=[a for a in discovered["kept"]
                    if sum(c!=0 for c in a["coefficients"])==2]
    result={
       "original_git_blob_sha1":EXPECTED_GIT_BLOB,
       "actual_original_sha256":digest,
       "original_source":OFFICIAL,
       "official_git_commit":GIT_COMMIT,
       "native_custom_pre_trans_post_semantics_xor":parity,
       "old_frozen_full_portfolio_status":historical.get("status"),
       "old_frozen_full_portfolio_route":historical.get("selected_route"),
       "post_only_original_inductive":postonly["accepted"],
       "post_only_original_three_vc":postonly["vcs"],
       "unreduced_6dim_pre_tight_old_cap_status":old_cap_status,
       "exact_original_syntactic_liveness_projection":projection,
       "source_pre_optimize_bounded_facets_generated":len(opt_proofs),
       "source_pre_entailed_candidate_atoms":len(atoms),
       "actual_source_trans_counterexample_steps":discovered["iterations"],
       "actual_source_trans_counterexample_trace":discovered["removed"],
       "source_only_surviving_atoms":discovered["kept"],
       "nontrivial_surviving_two_variable_source_relations":live_relational,
       "source_only_invariant_sexpr":R.sexpr(),
       "source_only_invariant_native_original_three_vc":raw_proof["vcs"],
       "source_only_invariant_native_original_three_vc_accepted":raw_proof["accepted"],
       "full_original_post_strengthening_done_after_source_structure_freeze":True,
       "strengthened_native_actual_original_three_vc":full_native["vcs"],
       "strengthened_native_actual_original_three_vc_accepted":full_native["accepted"],
       "full_exact_sha_bound_original_3vc_cvc5":verified,
       "independent_cvc5_three_original_negative_obligations_accepted":verified["accepted"],
       "negative_original_verifier_controls":negatives,
       "source_only_state_search_wall_ms":round(search_ms,3),
       "whole_study_python_wall_ms":round((time.perf_counter_ns()-wall)/1e6,3),
       "model_calls":0,"accelerator_calls":0,"paid_api_calls":0,
    }
    return result

def run(root):
    v=original_study(root/OFFICIAL)
    cvc5=v["full_exact_sha_bound_original_3vc_cvc5"]["independent_cvc5_three_vc"]
    sourceproof=v["source_only_invariant_native_original_three_vc"]
    projection=v["exact_original_syntactic_liveness_projection"]
    gates={
       "fixed_known_official_original_sha_and_native_parity":len(v[
           "native_custom_pre_trans_post_semantics_xor"])==3 and all(
           x=="unsat" for x in v["native_custom_pre_trans_post_semantics_xor"].values()),
       "original_unreduced_first_grammar_cap_block_reproduced":
           "UNSUPPORTED_ORIGINAL_STATE_DIMENSION" in v[
              "unreduced_6dim_pre_tight_old_cap_status"],
       "generic_exact_dead_state_liveness_reduces_six_states_to_three":
           projection["original_state_coordinates"]==6
           and projection["projected_live_coordinates"]==3
           and projection["provably_unused_dead_coordinates"]==3
           and projection["all_dropped_symbols_absent_from_original_three_public_relations"],
       "old_full_portfolio_had_spacer_safety_but_no_explicit_original_3vc":
           v["old_frozen_full_portfolio_status"]=="ORIGINAL_SOURCE_ONLY_SPACER_UNSAT",
       "published_original_post_alone_not_inductive":not v["post_only_original_inductive"],
       "genuine_source_only_relational_atom_survives":len(v[
           "nontrivial_surviving_two_variable_source_relations"])>=1,
       "real_trans_cegis_deletes_at_least_one_source_candidate":
           v["actual_source_trans_counterexample_steps"]>=1,
       "source_only_relation_inductive_but_cannot_alone_imply_original_post":
           sourceproof["initial"]=="unsat" and sourceproof["consecution"]=="unsat"
           and sourceproof["post"]=="sat",
       "adding_published_post_after_source_learning_is_fully_original_inductive":
           v["strengthened_native_actual_original_three_vc_accepted"]
           and v["full_original_post_strengthening_done_after_source_structure_freeze"],
       "full_unprojected_sygus_original_three_vc_independent_cvc5_x3_unsat":
           v["independent_cvc5_three_original_negative_obligations_accepted"]
           and len(cvc5)==3
           and all(q["status"]=="unsat" and q["returncode"]==0 for q in cvc5.values()),
       "all_adversarial_wrong_or_spoofed_original_candidates_rejected":
           len(v["negative_original_verifier_controls"])==4
           and all(x["correctly_rejected"] for x in
             v["negative_original_verifier_controls"].values()),
    }
    return {
       "schema":SCHEMA,"preregistered_issue":285,
       "prior_original_first_prospective_issue283_verdict":"FAIL_IMMUTABLE",
       "first_dev_scoped_pass":all(gates.values()),
       "first_dev_gate_conditions":gates,
       "one_already_opened_official_original_case":v,
       "allowed_claim":"POSTHOC_ONE_SOURCE_CLASSICAL_DEAD_STATE_PROJECTION_PLUS_POST_STRENGTHENING",
       "new_independent_original_families_proven":0,
       "learned_unique_neural_operator_proven":False,
       "full_energy_monetary_economics":"NOT_EVALUATED",
       "global_Q1_Q7":"OPEN","sealed_D3":"BLOCKED",
       "historic_AM1_first":"FAIL_UNCHANGED",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--official-root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    report=run(args.official_root)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("Q3_SUM4_VARS_POSTHOC_SOURCE_LIVENESS_FIRST",report["first_dev_scoped_pass"])
    print("Q3_SUM4_VARS_FIRST_GATES",json.dumps(report["first_dev_gate_conditions"],sort_keys=True))
    print("GLOBAL_Q1_Q7",report["global_Q1_Q7"])
if __name__=="__main__":
    main()
