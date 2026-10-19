"""Q3 post-first-FAIL development: SOURCE-Pre-tight symbolic facets.

Issue #281 registered AFTER original one-shot #279 FAIL on independent
metadata-frozen cegar/const/fib sources. Do NOT rewrite first FAIL as pass.
This narrowed cegar1 case has been inspected; its development outcome is NOT
an independent prospective new-family Q3 result.

Changes only source-derived integer cutpoints: old Pre witness and -1,0,1
PLUS exact finite minima of each signed <=2-var octagon under PUBLIC Pre.
A Z3 Optimize finite lower bound is NEVER accepted without a separate
Pre=>linear-cutpoint Z3 proof. Same counterexample-guided Houdini filter,
same native original 3VC and separate cvc5 original source verifier.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, time
from pathlib import Path
import z3

from experiments.q3_source_prove import (
    sexprs,extract_mixed_original,native_original_relations,check_parity,
    check_formula,source_proof,
)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate
from research.evidence.q3_anfp_relational_source_houdini_20261019.first_anfp_source_original import (
    original_houdini,original_source_atom_grammar,MAX_ATOMS,MAX_ITERATIONS,
    OFFSETS,
)

GIT_COMMIT="13c8deb68a873635879c9a69bc78caebd340f646"
ORIGINAL="comp/2017/Inv_Track/cegar1.sl"
ORIGINAL_GIT_BLOB="5265f78e457228bfb7eef931aca690ee40f53a31"

def sha(x:bytes):
    return hashlib.sha256(x).hexdigest()

def blob(x:bytes):
    return hashlib.sha1(("blob "+str(len(x))+"\0").encode()+x).hexdigest()

def chk(x,timeout=2500):
    s=z3.Solver();s.set(timeout=timeout);s.add(x);return s.check()

def source_pre_tight_bound(pre, linear):
    """Return integer tight L when min(Pre,linear) exists and is exact."""
    opt=z3.Optimize()
    opt.set(timeout=2500)
    opt.add(pre)
    handle=opt.minimize(linear)
    status=opt.check()
    if status!=z3.sat:
        return None,{"status":str(status)}
    lower=opt.lower(handle)
    if not z3.is_int_value(lower):
        return None,{"status":"NONFINITE_OR_NONINTEGER_OPTIMUM",
                     "reported_minimum":str(lower)[:120]}
    v=lower.as_long()
    # Z3 optimize is NOT independently trusted as source proof evidence.
    # Prove original Pre=>sparse linear>=v by separate ordinary exact SMT.
    if chk(z3.And(pre,linear<v))!=z3.unsat:
        return None,{"status":"MINIMUM_NOT_ORIGINAL_PRE_ENTAILED"}
    if chk(z3.And(pre,linear==v))!=z3.sat:
        return None,{"status":"OPTIMUM_NOT_ATTAINABLE"}
    return v,{"status":"EXACT_FINITE_MINIMUM_SOURCE_PROVEN",
              "minimum":v}

def pre_tight_source_atoms(src,native):
    now=src["now"]
    if src["num_bool"] or not 1<=len(now)<=5:
        raise RuntimeError("UNSUPPORTED_ORIGINAL_STATE_DIMENSION")
    pre=native["pre"]
    witness=z3.Solver();witness.set(timeout=2500);witness.add(pre)
    if witness.check()!=z3.sat:
        raise RuntimeError("NO_REAL_PUBLIC_SOURCE_PRE_SAT")
    m=witness.model()
    init=[m.eval(v,model_completion=True).as_long() for v in now]
    atoms=[]
    all_cutproofs=[]
    extra=[]
    for coeff in itertools.product((-1,0,1),repeat=len(now)):
        if not 1<=sum(c!=0 for c in coeff)<=2:
            continue
        lin=z3.Sum(*[z3.IntVal(int(c))*v for c,v in zip(coeff,now) if c])
        witness_cut=int(sum(a*b for a,b in zip(coeff,init)))
        minimum,proof=source_pre_tight_bound(pre,lin)
        if minimum is not None:
            all_cutproofs.append({"coefficients":list(coeff),
                                 "source_tight_cutpoint":minimum,
                                 "source_minimum_proof":proof["status"]})
        candidates=sorted(set([*OFFSETS,witness_cut]+
                  ([minimum] if minimum is not None else [])))
        for cut in candidates:
            term=lin>=cut
            if chk(z3.And(pre,z3.Not(term)))!=z3.unsat:continue
            atoms.append({"coefficients":list(coeff),
                          "threshold":int(cut),
                          "source_tight":minimum is not None and cut==minimum,
                          "assertion":term,
                          "primed":z3.substitute(term,*list(zip(now,src["next"])))})
            if minimum is not None and cut==minimum and cut not in set([*OFFSETS,witness_cut]):
                extra.append({"coefficients":list(coeff),"threshold":int(cut)})
    if not 1<=len(atoms)<=MAX_ATOMS:
        raise RuntimeError("PROSPECTIVELY_FROZEN_ATOM_CAP_EXCEEDED")
    return atoms,all_cutproofs,extra

def exact_counterexample_pruning(atoms,native):
    kept=list(range(len(atoms)))
    evidence=[]
    began=time.perf_counter_ns()
    for step in range(MAX_ITERATIONS):
        cur=z3.And(*(atoms[j]["assertion"] for j in kept))
        nxt=z3.And(*(atoms[j]["primed"] for j in kept))
        solver=z3.Solver();solver.set(timeout=3500)
        solver.add(cur,native["trans"],z3.Not(nxt))
        st=solver.check()
        if st==z3.unsat:break
        if st!=z3.sat:raise RuntimeError("ORIGINAL_TRANS_CEGIS_UNKNOWN_OR_TIMEOUT")
        model=solver.model()
        removed=[j for j in kept if not z3.is_true(
            model.eval(atoms[j]["primed"],model_completion=True))]
        if not removed:raise RuntimeError("INDUCTIVE_COUNTEREXAMPLE_NO_REMOVABLE_ATOM")
        remove=set(removed)
        kept=[j for j in kept if j not in remove]
        evidence.append({"iteration":step,"removed_count":len(remove),
                         "witness_removed_coeff_cut":[
                          [atoms[j]["coefficients"],atoms[j]["threshold"]]
                           for j in removed]})
    else:raise RuntimeError("FROZEN_CEGIS_ITERATION_CAP")
    invariant=z3.And(*(atoms[j]["assertion"] for j in kept))
    return {"invariant":invariant,
       "kept":[{k:a[k] for k in ("coefficients","threshold","source_tight")}
               for j in kept for a in (atoms[j],)],
       "removed":evidence,"iterations":len(evidence),
       "wall_ms":round((time.perf_counter_ns()-began)/1e6,3)}

def do_one(source):
    raw=source.read_bytes()
    if blob(raw)!=ORIGINAL_GIT_BLOB:raise RuntimeError("UPSTREAM_FILE_BLOB_NOT_PREDECLARED")
    dig=sha(raw)
    forms=sexprs(raw)
    src=extract_mixed_original(forms)
    native=native_original_relations(forms,src)
    native.update({"now":src["now"],"next":src["next"]})
    parity=check_parity(src,native)
    if len(parity)!=3 or any(s!="unsat" for s in parity.values()):
        raise RuntimeError("ORIGINAL_NATIVE_SYGUS_PARSER_DISAGREE")
    if check_formula(native["pre"])!="sat" or check_formula(z3.Not(native["post"]))!="sat":
        raise RuntimeError("VACUOUS_ORIGINAL_SOURCE")
    old=original_houdini(src,native)
    old_prob=old.pop("invariant")
    old_vcs=source_proof(old_prob,native)
    atoms,minimum_evidence,extra=pre_tight_source_atoms(src,native)
    derived=exact_counterexample_pruning(atoms,native)
    proposal=derived.pop("invariant")
    native_candidate=source_proof(proposal,native)
    canonical=z3.simplify(proposal)
    assert chk(z3.Xor(proposal,canonical))==z3.unsat
    accepted=check_original_candidate(source,canonical.sexpr(),
                    expected_source_sha256=dig)
    status=accepted["status"]=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5"
    negatives={}
    for name,candidate,identity in (
        ("TRUE","true",dig),("FALSE","false",dig),
        ("SHA_TAMPERED",canonical.sexpr(),"0"*64),
        ("SMT_COMMAND_INJECTED","(assert false)",dig)):
        v=check_original_candidate(source,candidate,expected_source_sha256=identity)
        negatives[name]=v["status"]!="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5"
    tight_survivors=[r for r in derived["kept"] if r["source_tight"] and
            r["threshold"] not in set(OFFSETS)]
    return {
        "source_relative":ORIGINAL,
        "upstream_git_sha":GIT_COMMIT,
        "source_sha256":dig,
        "source_git_blob_sha1":ORIGINAL_GIT_BLOB,
        "native_original_pre_trans_post_parity":parity,
        "post_only_inductive":source_proof(native["post"],native)["accepted"],
        "old_original_houdini_no_tight_cutpoints":{
            "original_3vc":old_vcs["vcs"],"accepted":old_vcs["accepted"],
            "candidate_count":old["candidate_count"],
            "surviving_atoms":old["surviving_atoms"]},
        "new_public_Pre_tight_inequality_candidates":len(atoms),
        "new_pre_optimize_source_proven_bounds":minimum_evidence,
        "new_tight_integer_facets_not_in_previous_grammar":extra,
        "new_inductive_relational_atoms":derived["kept"],
        "new_source_pre_tight_surviving_facets":tight_survivors,
        "counterexample_pruning_trace":derived["removed"],
        "counterexample_steps":derived["iterations"],
        "new_original_native_three_vc":native_candidate["vcs"],
        "new_original_native_three_vc_accepted":native_candidate["accepted"],
        "new_canonical_invariant_smt2":canonical.sexpr(),
        "new_independent_real_original_verifier":accepted,
        "new_z3_cvc5_3vc_accepted":status,
        "four_negative_controls":negatives,
        "post_used_only_by_final_original_verifier":True,
        "learned_neural_weights_used":False,
        "source_name_solution_lookup":False,
    }

def run(root):
    case=do_one(root/ORIGINAL)
    exact_facet=any(
        x["coefficients"]==[-1,1] and x["threshold"]==-2 for x in
        case["new_source_pre_tight_surviving_facets"])
    conditions={
       "source_identity_exact_2017_cegar1_blob":case["source_git_blob_sha1"]==ORIGINAL_GIT_BLOB,
       "native_custom_original_syguS_semantics_match":all(
          v=="unsat" for v in case["native_original_pre_trans_post_parity"].values()),
       "old_frozen_cutpoint_grammar_did_not_prove_original":not case[
           "old_original_houdini_no_tight_cutpoints"]["accepted"],
       "actual_source_optimize_derives_non_guessed_facet_y_minus_x_ge_minus2":exact_facet,
       "real_counterexample_pruning_records":case["counterexample_steps"]>=1,
       "post_only_original_is_not_inductive":not case["post_only_inductive"],
       "same_original_new_smt_candidate_inductively_proved_and_cvc5_crosschecked":
          case["new_original_native_three_vc_accepted"] and case[
            "new_z3_cvc5_3vc_accepted"],
       "adversarial_original_inputs_four_of_four_rejected":len(
           case["four_negative_controls"])==4 and all(
           case["four_negative_controls"].values()),
    }
    return {
      "schema":"neumann.q3.cegar-after-first-failure-pre-tight-facet.dev.v1",
      "preregistered_issue":281,
      "is_posthoc_development_after_issue279_first_failure":True,
      "prior_issue279_first_verdict_preserved":"FAIL",
      "scientific_scope":"ONE_PREVIOUSLY_OPENED_OFFICIAL_SOURCE_DEV_ONLY",
      "original":case,
      "fixed_first_development_checks":conditions,
      "scoped_development_pass":all(conditions.values()),
      "new_unseen_external_originals":0,
      "genuine_independent_author_families_proven":False,
      "novel_neural_learned_semantic_operator":False,
      "global_Q1_Q7":"OPEN",
      "paid_api_calls":0,"gpu_calls":0,"model_calls":0,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--original-root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    result=run(args.original_root)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("CEGAR_POSTHOC_DEVELOPMENT_PRE_TIGHT_GATE",result["scoped_development_pass"])
    print("CEGAR_ORIGINAL_INDEPENDENT_3VC",result["original"]["new_z3_cvc5_3vc_accepted"])
    print("ISSUE281_FIXED_CHECKS",json.dumps(result["fixed_first_development_checks"],sort_keys=True))
    print("GLOBAL_Q1_Q7",result["global_Q1_Q7"])
if __name__=="__main__":main()
