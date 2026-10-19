"""ONE post-FIRST-failure classical PolyRank source-invariant grammar enlargement.

Issue #289 froze this EXACT 5-var signed coefficient grammar before its
first actual proof run. Existing prospective FIRST #287 remains FAIL.
No filenames/target invariant in candidate search; ALL signed vectors [-1,0,1]^d
are considered, up to 242 at d=5. Only public Pre and Trans build and prove
each atom; published Post is used solely for final checker/strengthening.
Original Z3 3VC + independent cvc5 full original source SHA authority.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,time
from pathlib import Path
import z3

from experiments.q3_source_prove import (
  sexprs,extract_mixed_original,native_original_relations,check_parity,
  check_formula,source_proof,prove_source,
)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate
from research.evidence.q3_cegar_pre_tight_facets_20261019.first_original_tight_facet import source_pre_tight_bound

SOURCE="benchmarks/LIA/2005.ICALP_PolyRank/poly2.sl"
GIT_COMMIT="6ac90265b11431c9477dfbd33e3e3380234c0499"
GIT_BLOB="17448225fffad0cef48634b9d68f4f9193d616d8"
ISSUE=289
SCHEMA="neumann.q3.posthoc-polyrank-full-signed-linear-potentials-first.v1"

def sha(b):
    return hashlib.sha256(b).hexdigest()
def blob(b):
    return hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()

def check_exact(predicate):
    sol=z3.Solver()
    sol.set(timeout=2500)
    sol.add(predicate)
    return str(sol.check())

def all_full_signed_source_pre_potentials(src,native):
    if src["num_bool"] or not 1<=len(src["now"])<=5:
        raise RuntimeError("FROZEN_FULL_LINEAR_ORIGINAL_INT_DIMENSION_CAP")
    now,nxt=src["now"],src["next"]
    examined=0
    finite=[]
    individually_inductive=[]
    incomplete_unknown=0
    source_only_start=time.perf_counter_ns()
    for coeffs in itertools.product((-1,0,1),repeat=len(now)):
        if not any(coeffs):continue
        examined+=1
        linear=z3.Sum(*[z3.IntVal(c)*v for c,v in zip(coeffs,now) if c])
        minimum,trust=source_pre_tight_bound(native["pre"],linear)
        if minimum is None:
            if trust["status"]=="unknown":
                incomplete_unknown+=1
            continue
        atom=linear>=minimum
        primed=z3.substitute(atom,*list(zip(now,nxt)))
        cur=check_exact(z3.And(native["pre"],z3.Not(atom)))
        reached=check_exact(z3.And(native["pre"],linear==minimum))
        if cur!="unsat" or reached!="sat":
            raise RuntimeError("FULL_FACET_SOURCE_PRE_EVIDENCE_CHANGED")
        finite.append([list(coeffs),minimum])
        step=check_exact(z3.And(atom,native["trans"],z3.Not(primed)))
        if step=="unknown":
            incomplete_unknown+=1
            # Unsupported native proof means no invented certificate, skip.
            continue
        if step=="unsat":
            individually_inductive.append({
               "coefficients":list(coeffs),
               "support_variables":sum(c!=0 for c in coeffs),
               "source_pre_exact_integer_minimum":minimum,
               "source_pre_entailment":"unsat",
               "source_pre_bound_attained":"sat",
               "individual_original_trans_induction":"unsat",
               "formula":atom,
            })
    if examined != (3**len(now)-1):
        raise RuntimeError("DID_NOT_ENUMERATE_EXACT_COMPLETE_FROZEN_COEFFICIENT_GRID")
    if incomplete_unknown:
        raise RuntimeError("INCOMPLETE_SOURCE_OPTIMIZE_OR_INDUCTION_UNKNOWN")
    if not individually_inductive:
        raise RuntimeError("NO_SOURCE_PROVEN_INDIVIDUAL_MULTI_LINEAR_POTENTIAL")
    R=z3.And(*(a["formula"] for a in individually_inductive))
    return R,{
       "full_integer_coeff_grid_directions_checked":examined,
       "public_source_pre_finite_exact_minima_count":len(finite),
       "public_source_pre_finite_minima":[
           {"coefficients":c,"minimum":m} for c,m in finite],
       "all_individually_inductive_source_linear_potentials":[
           {k:v for k,v in a.items() if k!="formula"}
           for a in individually_inductive],
       "source_individual_potentials_count":len(individually_inductive),
       "source_inductive_5_nonzero_coefficient_potentials":[
           {k:v for k,v in a.items() if k!="formula"}
           for a in individually_inductive if a["support_variables"]==5],
       "fully_enumerated_without_source_gold":True,
       "source_only_proposer_solver_wall_ms":round(
             (time.perf_counter_ns()-source_only_start)/1e6,3),
    }

def strict_source_bound_certificate(path,original_sha,formula):
    simple=z3.simplify(formula)
    equivalence=check_exact(z3.Xor(formula,simple))
    if equivalence!="unsat":
        raise RuntimeError("ORIGINAL_INVARIANT_CANONICAL_XOR_NOT_UNSAT")
    checked=check_original_candidate(path,simple.sexpr(),
             expected_source_sha256=original_sha)
    return {
       "status":checked.get("status"),
       "source_bound_native_original_three_vc":checked.get("native_original_three_vc"),
       "source_bound_independent_cvc5_three_vc":checked.get("cvc5_original_three_vc"),
       "accepted":checked.get("status")=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5",
       "submitted_original_invariant_sexpr":simple.sexpr(),
       "source_original_sexpr_sha256":sha(simple.sexpr().encode()),
       "XOR_equivalence_to_raw_source_R":"unsat",
    }

def original_study(path):
    started=time.perf_counter_ns()
    raw=path.read_bytes()
    if blob(raw)!=GIT_BLOB:
        raise RuntimeError("ORIGINAL_GIT_BLOB_SHA_PIN_MISMATCH")
    original_digest=sha(raw)
    sexp=sexprs(raw)
    src=extract_mixed_original(sexp)
    native=native_original_relations(sexp,src)
    native.update({"now":src["now"],"next":src["next"]})
    parity=check_parity(src,native)
    if len(parity)!=3 or any(v!="unsat" for v in parity.values()):
        raise RuntimeError("ORIGINAL_SYGUS_NATIVE_AND_CUSTOM_SEMANTICS_DISAGREE")
    if check_formula(native["pre"])!="sat" or check_formula(z3.Not(native["post"]))!="sat":
        raise RuntimeError("ORIGINAL_VACUITY")
    old=prove_source(path)
    post_alone=source_proof(native["post"],native)
    full_R,structure=all_full_signed_source_pre_potentials(src,native)
    raw_native=source_proof(full_R,native)
    # Fixed source-only invariant R produced without any Post.
    # Source Post read only now, to form an optional goal strengthening.
    strengthened=z3.And(full_R,native["post"])
    goal_native=source_proof(strengthened,native)
    cert_raw=strict_source_bound_certificate(path,original_digest,full_R) if raw_native["accepted"] else None
    cert_goal=strict_source_bound_certificate(path,original_digest,strengthened) if goal_native["accepted"] else None
    approved=cert_raw if cert_raw and cert_raw["accepted"] else cert_goal
    invalid_checks={}
    if approved is not None and approved["accepted"]:
        for key,text,expected in (
          ("TRUE","true",original_digest),
          ("FALSE","false",original_digest),
          ("INJECTED_SMT_COMMAND","(assert false)",original_digest),
          ("TAMPERED_SHA",approved["submitted_original_invariant_sexpr"],"0"*64),
        ):
            r=check_original_candidate(path,text,expected_source_sha256=expected)
            invalid_checks[key]=r.get("status")!="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5"
    return {
      "original_path":SOURCE,
      "origin_git_commit":GIT_COMMIT,
      "original_git_blob_sha1":GIT_BLOB,
      "actual_original_source_sha256":original_digest,
      "original_state_variables":len(src["now"]),
      "original_native_custom_semantic_parity":parity,
      "old_strongest_frozen_source_portfolio_status":old.get("status"),
      "old_strongest_frozen_source_portfolio_route":old.get("selected_route"),
      "old_source_portfolio_wall_ms":old.get("total_wall_ms"),
      "original_post_alone_vcs":post_alone["vcs"],
      "exact_new_full_signed_source_only_structure":structure,
      "source_only_R_original_three_vc":raw_native["vcs"],
      "source_only_R_proved":raw_native["accepted"],
      "public_Post_added_after_all_frozen_R_candidates":True,
      "source_R_AND_Post_original_three_vc":goal_native["vcs"],
      "source_R_AND_Post_proved":goal_native["accepted"],
      "R_only_original_cvc5":cert_raw,
      "R_and_Post_original_cvc5":cert_goal,
      "accepted_original_certificate":approved,
      "actual_full_original_Z3_and_external_cvc5_proven":bool(approved and approved["accepted"]),
      "four_adversarial_original_checker_controls":invalid_checks,
      "total_python_original_study_wall_ms":round((time.perf_counter_ns()-started)/1e6,3),
    }

def run(root):
    data=original_study(root/SOURCE)
    vars=data["exact_new_full_signed_source_only_structure"]
    proof=data["accepted_original_certificate"]
    cvc5=proof["source_bound_independent_cvc5_three_vc"] if proof else None
    conditions={
      "one_exact_upstream_git_blob_pinned_and_native_parity":len(data[
        "original_native_custom_semantic_parity"])==3 and all(
          v=="unsat" for v in data["original_native_custom_semantic_parity"].values()),
      "old_full_classical_portfolio_spacer_no_inductive_original_certificate":
          data["old_strongest_frozen_source_portfolio_status"]=="ORIGINAL_SOURCE_ONLY_SPACER_UNSAT",
      "post_original_alone_is_non_inductive":
          data["original_post_alone_vcs"]["consecution"]=="sat",
      "all_5var_signed_grid_directions_enumerated":
          data["original_state_variables"]==5 and vars[
              "full_integer_coeff_grid_directions_checked"]==242,
      "genuinely_5variable_tight_source_pre_proven_inductive_potential":
          len(vars["source_inductive_5_nonzero_coefficient_potentials"])>=1,
      "source_only_proposer_freezes_before_post_goal_join":
          data["public_Post_added_after_all_frozen_R_candidates"],
      "new_complete_original_inductive_and_external_cvc5_3vc":
          data["actual_full_original_Z3_and_external_cvc5_proven"] and
          cvc5 is not None and len(cvc5)==3 and
          all(v["status"]=="unsat" and v["returncode"]==0 for v in cvc5.values()),
      "all_four_strict_source_bound_negative_controls_refused":
          len(data["four_adversarial_original_checker_controls"])==4 and
          all(data["four_adversarial_original_checker_controls"].values()),
    }
    return {
       "schema":SCHEMA,"preregistered_issue":ISSUE,
       "historical_first_issue287_three_origin_first":"FAIL_IMMUTABLE",
       "one_already_opened_original_posthoc_only":True,
       "fixed_first_development_gate":conditions,
       "first_scoped_dev_pass":all(conditions.values()),
       "authentic_original_source_case":data,
       "unique_neural_learned_operator":False,
       "unseen_external_original_author_or_family_generalization":False,
       "cold_complete_cost_and_energy":"NOT_EVALUATED",
       "historical_first_AM1":"FAIL_UNCHANGED",
       "global_Q1_Q7":"OPEN",
       "gpu_calls":0,"model_calls":0,"paid_api_calls":0,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    report=run(args.source_root)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("Q3_POLYRANK_POSTHOC_FULL_SIGNED_FIRST_GATE",report["first_scoped_dev_pass"])
    print("Q3_POLYRANK_FULL_LINEAR_GATES",json.dumps(report["fixed_first_development_gate"],sort_keys=True))
    print("Q3_POLYRANK_ORIGINAL_PROOF",report["authentic_original_source_case"]["actual_full_original_Z3_and_external_cvc5_proven"])
    print("GLOBAL_Q1_Q7",report["global_Q1_Q7"])
if __name__=="__main__":main()
