"""Q3 original SyGuS anfp recovery: source-only relational counterexample pruning.

Frozen Issue #277 before this implementation's FIRST source proof result.
Uses already-opened 2017 official originals previously BOTH ABSTAIN in
first official source campaign; NOT independent families nor a neural model.
All original 3VCs are native Z3 AND separately cvc5-checked.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import time
from pathlib import Path

import z3

from experiments.q3_source_prove import (
    sexprs, extract_mixed_original, native_original_relations,
    check_parity, check_formula, source_proof,
)
from experiments.am2_sygus_native_three_vc_checker import check_original_candidate

UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
FILES=(
 "comp/2017/Inv_Track/anfp.sl",
 "comp/2017/Inv_Track/anfp-new.sl",
)
PREDECLARED_SOURCE_SHA={
 "anfp.sl":"1caa46662e6093fa0d95f48349558abda0ffa2974bc23db025b78d3d5a1a63cb",
 "anfp-new.sl":"97d4acb56916aca25cc4136cee9da4760baa3b15eb9a2e2feff1bca62da86769",
}
OFFSETS=(-1,0,1)
MAX_ATOMS=128
MAX_ITERATIONS=128

def sha(data):
    return hashlib.sha256(data).hexdigest()

def check(formula,limit=2500):
    solver=z3.Solver()
    solver.set(timeout=limit)
    solver.add(formula)
    return solver.check()

def _safe_int_model_values(formula,variables):
    solver=z3.Solver()
    solver.set(timeout=2500)
    solver.add(formula)
    if solver.check()!=z3.sat:
        raise RuntimeError("NO_PUBLIC_INITIAL_SOURCE_WITNESS")
    model=solver.model()
    return [model.eval(v,model_completion=True).as_long() for v in variables]

def original_source_atom_grammar(src,native):
    """Finite sparse octagons derived from source state names + public Pre.

    Uniform grammar, no filename case-switching, golden invariant or Post.
    Positive/negative singleton and variable-pair signed combinations.
    Allowed cutpoints -1,0,1 + Pre witness linear-form values.
    """
    now=src["now"]
    if not 1<=len(now)<=5 or src["num_bool"]:
        raise RuntimeError("UNSUPPORTED_INTEGER_STATE_DIMENSION")
    first=_safe_int_model_values(native["pre"],now)
    atom_info=[]
    all_coeffs=[]
    for tuple_ in itertools.product((-1,0,1),repeat=len(now)):
        if 0<sum(c!=0 for c in tuple_)<=2:
            all_coeffs.append(tuple_)
    for coeffs in all_coeffs:
        expression=z3.Sum(*[z3.IntVal(int(c))*v
                      for c,v in zip(coeffs,now) if c])
        witness_value=sum(c*v for c,v in zip(coeffs,first))
        cuts=sorted(set(OFFSETS+(witness_value,)))
        for threshold in cuts:
            atom=(expression>=threshold)
            # Only PUBLIC Pre may certify whether a candidate is a possible
            # invariant. Original Post and solver answer never enter grammar.
            if check(z3.And(native["pre"],z3.Not(atom)))==z3.unsat:
                atom_info.append({
                    "coefficients":tuple(int(x) for x in coeffs),
                    "threshold":int(threshold),
                    "assertion":atom,
                    "primed":z3.substitute(atom,*list(
                        zip(now,src["next"]))),
                })
    if len(atom_info)>MAX_ATOMS:
        raise RuntimeError("FROZEN_ATOM_POOL_SIZE_EXCEEDED")
    if not atom_info:
        raise RuntimeError("NO_SOURCE_CONSISTENT_ATOMS")
    return atom_info

def original_houdini(src,native):
    atoms=original_source_atom_grammar(src,native)
    kept=list(range(len(atoms)))
    removals=[]
    t=time.perf_counter_ns()
    for iteration in range(MAX_ITERATIONS):
        actual=z3.And(*(atoms[j]["assertion"] for j in kept))
        primed=z3.And(*(atoms[j]["primed"] for j in kept))
        bad=z3.Solver()
        bad.set(timeout=3500)
        bad.add(actual,native["trans"],z3.Not(primed))
        status=bad.check()
        if status==z3.unsat:
            break
        if status!=z3.sat:
            raise RuntimeError("HOUDINI_ORIGINAL_STEP_UNKNOWN_OR_TIMEOUT")
        m=bad.model()
        violated=[
            j for j in kept
            if not z3.is_true(m.eval(atoms[j]["primed"],model_completion=True))
        ]
        if not violated:
            raise RuntimeError("SAT_COUNTEREXAMPLE_WITHOUT_REMOVABLE_ATOM")
        kept=[j for j in kept if j not in set(violated)]
        removals.append({
            "step":iteration,
            "removed_count":len(violated),
            "removed_coefficients_and_cutpoints":[
                 [list(atoms[j]["coefficients"]),atoms[j]["threshold"]]
                 for j in violated],
        })
    else:
        raise RuntimeError("FROZEN_HOUDINI_ITERATION_CAP")
    invariant=z3.And(*(atoms[j]["assertion"] for j in kept))
    proof=source_proof(invariant,native)
    return {"invariant":invariant,
        "candidate_count":len(atoms),"surviving_atoms":len(kept),
        "source_atom_pool_sha256":sha(json.dumps(
             [[list(a["coefficients"]),a["threshold"]] for a in atoms],
             sort_keys=True).encode()),
        "surviving_source_atoms":[
            {"coefficients":list(atoms[j]["coefficients"]),
             "threshold":atoms[j]["threshold"]}
            for j in kept],
        "removed_counterexample_iterations":len(removals),
        "actual_removed_atom_count":sum(x["removed_count"] for x in removals),
        "first_counterexample_trace":removals,
        "relation_atom_survived":any(sum(c!=0 for c in
             atoms[j]["coefficients"])==2 for j in kept),
        "candidate_inductiveness_original_3vc":proof["vcs"],
        "native_original_three_vc_proved":proof["accepted"],
        "houdini_wall_ms":round((time.perf_counter_ns()-t)/1e6,3),
    }

def one_file(source):
    start=time.perf_counter_ns()
    raw=source.read_bytes()
    digest=sha(raw)
    if digest!=PREDECLARED_SOURCE_SHA.get(source.name):
        raise RuntimeError("PREDECLARED_EXTERNAL_SOURCE_SHA_MISMATCH")
    forms=sexprs(raw)
    src=extract_mixed_original(forms)
    native=native_original_relations(forms,src)
    native.update({"now":src["now"],"next":src["next"]})
    parity=check_parity(src,native)
    if len(parity)!=3 or any(x!="unsat" for x in parity.values()):
        raise RuntimeError("ORIGINAL_PRE_TRANS_POST_NATIVE_PARITY_MISMATCH")
    if check_formula(native["pre"])!="sat" or check_formula(
        z3.Not(native["post"]))!="sat":
        raise RuntimeError("ORIGINAL_SOURCE_VACUOUS")
    post_only=source_proof(native["post"],native)
    learnt=original_houdini(src,native)
    # INFRA-ONLY cross-SMT-LIB serialization repair after FIRST run FAIL.
    # Z3 lets z3.Sum(singleton) print a one-argument SMT-LIB (+ ...), while
    # strict cvc5 rejects it before any proof. Do NOT change the discovered
    # invariant's semantics or grammar. Canonicalize and PROVE equivalence
    # against the first native-source invariant BEFORE external rechecking.
    first_native_invariant=learnt["invariant"]
    canonical_invariant=z3.simplify(first_native_invariant)
    equivalence=z3.Solver()
    equivalence.set(timeout=2500)
    equivalence.add(z3.Xor(first_native_invariant,canonical_invariant))
    if equivalence.check()!=z3.unsat:
        raise RuntimeError("CANONICAL_SMT_INVARIANT_NOT_PROVABLY_EQUIVALENT")
    full_formula=canonical_invariant.sexpr()
    # External adapter re-parses original SyGuS and candidate, runs native Z3
    # 3VC and then separate strict cvc5 on the full original bad conditions.
    verified=check_original_candidate(source,full_formula,
          expected_source_sha256=digest)
    wrong={}
    for variant,input_str,expected_sha in (
        ("TRUE","true",digest),
        ("FALSE","false",digest),
        ("COMMAND_INJECTION","(assert false)",digest),
        ("WRONG_ORIGINAL_SOURCE_SHA",full_formula,"0"*64),
    ):
        status=check_original_candidate(source,input_str,
            expected_source_sha256=expected_sha)
        wrong[variant]={
            "status":status["status"],
            "accepted":status["status"]=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5",
        }
    return {
        "original_source_path":str(source.relative_to(source.parents[3])),
        "original_source_sha256":digest,
        "original_source_parser_parity":parity,
        "native_original_pre_and_notpost_nonvacuous":True,
        "historical_first_official_source_status":"ABSTAIN",
        "original_post_alone_inductive":bool(post_only["accepted"]),
        "original_post_only_vcs":post_only["vcs"],
        "source_only_relational_houdini":{
            k:v for k,v in learnt.items() if k!="invariant"},
        "native_first_discovered_invariant_sexpr":first_native_invariant.sexpr(),
        "semantic_preserving_smt_canonicalization":"Z3_SIMPLIFY_WITH_EXACT_XOR_UNSAT",
        "native_vs_cross_backend_candidate_xor":"unsat",
        "first_original_cross_backend_failure_preserved":True,
        "discovered_source_only_invariant_sexpr":full_formula,
        "discovered_source_only_invariant_sha256":sha(full_formula.encode()),
        "external_original_checker_result":verified,
        "native_plus_cvc5_original_3vc_certified":
           verified["status"]=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5",
        "negative_original_checks":wrong,
        "total_original_wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
    }

def run(root):
    rows=[]
    for rel in FILES:
        p=root/rel
        row=one_file(p)
        rows.append(row)
        print("ANFP_FROZEN_ORIGINAL_3VC",p.name,
              row["native_plus_cvc5_original_3vc_certified"],
              "surviving",row["source_only_relational_houdini"]["surviving_atoms"],
              "removed",row["source_only_relational_houdini"][
                 "actual_removed_atom_count"])
    conditions={
        "exact_two_predeclared_old_abstain_origins":len(rows)==2
           and len({x["original_source_sha256"] for x in rows})==2,
        "both_native_custom_source_semantics_parity":all(
           all(v=="unsat" for v in row["original_source_parser_parity"].values())
           for row in rows),
        "both_source_derived_invariants_original_3vc_and_cvc5":all(
            row["native_plus_cvc5_original_3vc_certified"] and
            row["source_only_relational_houdini"][
               "native_original_three_vc_proved"] for row in rows),
        "both_original_post_alone_noninductive":all(
           not row["original_post_alone_inductive"] for row in rows),
        "both_survive_nontrivial_two_variable_relational_atom":all(
           row["source_only_relational_houdini"][
               "relation_atom_survived"] for row in rows),
        "real_counterexample_guided_pruning_occurred":any(
           row["source_only_relational_houdini"][
              "actual_removed_atom_count"]>0 for row in rows),
        "all_true_false_original_checker_negative_controls_rejected":all(
           not row["negative_original_checks"][a]["accepted"]
           for row in rows for a in ("TRUE","FALSE")),
        "all_tampered_source_or_command_injection_negative_controls_rejected":all(
           not row["negative_original_checks"][a]["accepted"]
           for row in rows for a in ("COMMAND_INJECTION","WRONG_ORIGINAL_SOURCE_SHA")),
    }
    return {
        "schema":"neumann.q3.public-anfp-relational-houdini-original.v1",
        "preregistered_issue":277,
        "upstream_repo":"SyGuS-Org/benchmarks","upstream_commit":UPSTREAM,
        "scientific_scope":"DEVELOPMENT_ONLY_TWO_NEAR_DUPLICATE_PREVIOUSLY_OPENED_ORIGINALS",
        "original_source_family_count_verified":1,
        "original_source_prior_statuses_unchanged":"TWO_ABSTAIN",
        "first_frozen_recovery_scoped_pass":all(conditions.values()),
        "predeclared_conditions":conditions,
        "cases":rows,
        "learned_neural_structure_contribution":False,
        "source_conditional_classical_structure_discovery":True,
        "strong_full_classical_novelty_or_gain":False,
        "complete_cost_energy_economics":"NOT_EVALUATED",
        "actual_models_called":0,"gpu_calls":0,"paid_api_calls":0,
        "sealed_D3":"BLOCKED","historical_AM1":"FAIL_UNCHANGED",
        "global_Q1_Q7":"OPEN",
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--official-root",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    result=run(args.official_root)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("FIRST_Q3_ANFP_RECOVERY_GATE",result["first_frozen_recovery_scoped_pass"])
    print("FIRST_Q3_ANFP_CONDITIONS",json.dumps(result["predeclared_conditions"],sort_keys=True))
    print("GLOBAL_Q1_Q7",result["global_Q1_Q7"])

if __name__=="__main__":
    main()
