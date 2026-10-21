"""Real source AST structural canonicalizer, alpha-renaming and arity robust.

Eight ORIGINAL authenticated SyGuS programs, dynamic 2/3/4/5 typed Int
state counts, 3 synthetic alpha renamings each, full exact source Pre Trans
Post preserved. Independently require original-vs-renamed source same-logic
XOR UNSAT in both native Z3 and cvc5 before crediting any canonical
identity. Original code written and admitted POSTHOC after 7 new source
bodies were opened by preceding PR378 Q6 experiment.

This does NOT discover any invariant or create an ML model! It is a
verifier-backed structural representation primitive, accessible to strong
classical Direct equally. Q3/Q6 unique/generalisation remain OPEN.
"""
from __future__ import annotations
import argparse,hashlib,itertools,json,random,time
from pathlib import Path
import z3
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import (
    prepare,dual,DUAL_S
)
UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
CONTRACT_COMMIT="f535c21787201c18e13d911f6208717d3e91ce48"
OLD_FIB32="lib/Inv_Track/from_2018/fib_32.sl"
ORIGINAL_FIB32_GIT="4fb129488bee3e1e0cdae899b318d6503ae23c12"

def digest(s):
    return hashlib.sha256(s.encode()).hexdigest()

def canonical_pre_trans_post(formulas,now,nextvars):
    if len(now)!=len(nextvars) or len(now)<2 or len(now)>6:
        raise ValueError("TRUE_SOURCE_STATE_VARIABLE_COUNT_OUT_OF_BOUNDED_DYNAMIC_ARITY")
    if any(v.sort().kind()!=z3.Z3_INT_SORT for v in list(now)+list(nextvars)):
        raise ValueError("ALPHA_NORMALIZER_SOURCE_NONINTEGER_BOUNDED_SORT")
    if len({str(v) for v in list(now)+list(nextvars)})!=2*len(now):
        raise ValueError("ORIGINAL_TWIN_STATE_NAMESPACE_NOT_DISJOINT")
    n=len(now)
    canon=[z3.Int("__neumann_role_slot_"+str(i)) for i in range(n)]
    canon_next=[z3.Int("__neumann_role_slot_next_"+str(i)) for i in range(n)]
    minimized=None;winning_permutation=None
    for pi in itertools.permutations(range(n)):
        replace=[(now[i],canon[pi[i]]) for i in range(n)]+[
                 (nextvars[i],canon_next[pi[i]]) for i in range(n)]
        # Each original native formula copied WHOLE, no dropping any source
        # conjunctions, original source variable inter-roles preserved.
        items=[z3.substitute(formulas[k],*replace).sexpr()
               for k in ("pre","trans","post")]
        rendered="DYNAMIC_INT_STATE_ARITY="+str(n)+"\n"+"\n==SEPARATE_ORIGINAL_FORMULA==\n".join(items)
        if minimized is None or rendered<minimized:
            minimized=rendered;winning_permutation=pi
    return {"dynamic_source_integer_state_arity":n,
            "alpha_variable_name_and_order_invariant_sha256":digest(minimized),
            "source_arithmetic_formula_no_human_role_names":True,
            "enumerated_all_state_permutations":True,
            "source_full_formula_key_contains_pre_trans_post":True,
            "lexicographic_minimum_signature_bytes":len(minimized.encode()),
            "minimizing_original_state_assignment":list(winning_permutation)}

def synthetically_alpha_rename_all_source_states(formulas,now,nxt,seed):
    n=len(now)
    rng=random.Random(20261021+seed)
    shuffle=list(range(n))
    rng.shuffle(shuffle)
    renamed_now=[z3.Int(f"pseudonym_r{seed}_variable_{i*11+13}") for i in range(n)]
    renamed_next=[z3.Int(f"pseudonym_r{seed}_NEXT_{i*17+19}") for i in range(n)]
    replacements=[(now[i],renamed_now[i]) for i in range(n)]+[
                  (nxt[i],renamed_next[i]) for i in range(n)]
    changed={k:z3.substitute(formulas[k],*replacements) for k in ("pre","trans","post")}
    # The source program's declaration-order is ALSO permuted. No names
    # from the original author survive in canonical representation.
    return changed,[renamed_now[i] for i in shuffle],[renamed_next[i] for i in shuffle],(
        [(renamed_now[i],now[i]) for i in range(n)]+
        [(renamed_next[i],nxt[i]) for i in range(n)]
    )

def original_3x_source_independent_math_equivalence(before,after,undo):
    receipts={}
    for key in ("pre","trans","post"):
        reversed_ast=z3.substitute(after[key],*undo)
        actual=dual(z3.Xor(before[key],reversed_ast),"unsat",DUAL_S)
        receipts[key]={"original_vs_alpha_native_XOR_dual_proved_UNSAT":bool(actual["dual_pass"]),
                       "independent_z3_cvc5_original_source_receipt":actual}
    return receipts

def one_true_original(root,item):
    t=time.perf_counter_ns()
    r={"source":item["path"],"true_source_git_blob":item["git_blob"],
       "actual_original_SHA_authenticated":False,
       "dynamic_arity_original_canonical_success":False,
       "three_synthetic_alpha_semantic_equivalence_test_count":0,
       "original_source_and_renamed_3x_full_dual_equivalence_tests_passed":0,
       "status":"ABSTAIN"}
    try:
        raw,src,native,proof_id=prepare(root,item)
        r["actual_original_SHA_authenticated"]=True
        r["prior_verified_true_original_native_Pre_Trans_Post_parity"]=proof_id
        now=src["now"];nxt=src["next"]
        original=canonical_pre_trans_post(native,now,nxt)
        r["original_source_full_semantic_skeleton"]=original
        r["original_source_dynamic_arity"]=len(now)
        experiments=[]
        for seed in (1,2,3):
            altered,renamed_now,renamed_next,undo=synthetically_alpha_rename_all_source_states(
                native,now,nxt,seed)
            signature=canonical_pre_trans_post(altered,renamed_now,renamed_next)
            checked=original_3x_source_independent_math_equivalence(native,altered,undo)
            pass_count=sum(q["original_vs_alpha_native_XOR_dual_proved_UNSAT"] for q in checked.values())
            hash_equal=(signature["alpha_variable_name_and_order_invariant_sha256"]==
                        original["alpha_variable_name_and_order_invariant_sha256"])
            experiments.append({"renaming_seed":seed,
                "all_native_source_integer_roles_preserved_and_signature_order_permuted":True,
                "source_canonical_alpha_name_order_sha_equal":hash_equal,
                "independent_source_3_math_grammars_semantics_dual_equivalence":checked,
                "independent_dual_original_Pre_Trans_Post_pass_count":pass_count,
                "renamed_typed_arity":signature["dynamic_source_integer_state_arity"]})
        r["three_synthetic_renamed_semantic_source_test_cases"]=experiments
        r["three_synthetic_alpha_semantic_equivalence_test_count"]=len(experiments)
        r["original_source_and_renamed_3x_full_dual_equivalence_tests_passed"]=sum(
            row["independent_dual_original_Pre_Trans_Post_pass_count"] for row in experiments)
        r["all_three_alpha_signature_digests_identical_to_original"]=all(
            row["source_canonical_alpha_name_order_sha_equal"] for row in experiments)
        # Deliberate single-source SEMANTIC mutation is never an alpha
        # renaming. Native original post NOT(original post) is inequivalent.
        mutated=dict(native)
        mutated["post"]=z3.Not(native["post"])
        changed=canonical_pre_trans_post(mutated,now,nxt)
        negative=dual(z3.Xor(native["post"],mutated["post"]),"sat",DUAL_S)
        r["negative_post_mutation_real_semantics_dual_SAT"]=bool(negative["dual_pass"])
        r["negative_post_mutation_canonical_sha_differs"] = (
            changed["alpha_variable_name_and_order_invariant_sha256"] !=
            original["alpha_variable_name_and_order_invariant_sha256"])
        r["negative_original_source_dual_check_receipt"]=negative
        r["dynamic_arity_original_canonical_success"]=(
            r["all_three_alpha_signature_digests_identical_to_original"] and
            r["original_source_and_renamed_3x_full_dual_equivalence_tests_passed"]==9 and
            r["negative_post_mutation_real_semantics_dual_SAT"] and
            r["negative_post_mutation_canonical_sha_differs"])
        r["status"]="ACTUAL_SOURCE_POSTHOC_ALPHA_CANONICAL_AND_DUAL_SEMANTIC_PASS" if r[
           "dynamic_arity_original_canonical_success"] else "FAIL_INDEPENDENT_ORIGINAL_SOURCE_ALPHA_PROOF"
    except Exception as e:
        r["status"]="ABSTAIN_ORIGINAL_SOURCE_OR_CANONICALIZER_ERROR"
        r["error"]=type(e).__name__+":"+str(e)[:310]
    r["all_original_source_parse_permutations_dual_receipts_wall_ms"]=(time.perf_counter_ns()-t)/1e6
    print("Q6_DYNAMIC_ALPHA_TYPED_NATIVE_ORIGINAL",item["path"].split("/")[-1],
          "ARITY",r.get("original_source_dynamic_arity"),
          "PASS",r["dynamic_arity_original_canonical_success"],
          "DUAL",r["original_source_and_renamed_3x_full_dual_equivalence_tests_passed"],
          "STATUS",r["status"],"ERROR",r.get("error"),flush=True)
    return r

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--source24",type=Path,required=True)
    p.add_argument("--seven",type=Path,required=True)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    c=json.loads(args.contract.read_text())
    m=json.loads(args.source24.read_text())
    new=json.loads(args.seven.read_text())
    if c["schema"]!="neumann.q6.posthoc_alpha_invariant_dynamic_original_program_semantic_skeleton_eight.v1":
        raise RuntimeError("PRESOURCE_REGISTERED_SEMANTIC_CANONICAL_V1_CHANGED")
    fib=next(x for x in m["cases"] if x["path"]==OLD_FIB32)
    if fib["git_blob"]!=ORIGINAL_FIB32_GIT:raise RuntimeError("HISTORIC_SOURCE_FIB32_GIT_CHANGED")
    original_cases=[fib]+new["test_case_git_blobs"]
    assert len(original_cases)==8 and len(set(x["git_blob"] for x in original_cases))==8
    originals=[one_true_original(args.root,x) for x in original_cases]
    passed=sum(x["dynamic_arity_original_canonical_success"] for x in originals)
    dual=sum(x["original_source_and_renamed_3x_full_dual_equivalence_tests_passed"] for x in originals)
    report={"schema":"neumann.q6.real_eight_original_dynamic_alpha_semantic_skeleton_independently_proved.v1",
            "preregistered_posthoc_original_source_structure_commit":CONTRACT_COMMIT,
            "all_original_source_bodies_previously_opened_by_PR376_and_PR378":True,
            "same_8_original_git_source_files_retained":len(originals)==8,
            "true_original_sha_identity_authenticated":sum(x["actual_original_SHA_authenticated"] for x in originals),
            "dynamic_state_arity_independent_source_normalizer_pass":passed,
            "true_native_3xdifferent_names_per_original_semantics_dual_pass":dual,
            "synthetic_alpha_source_test_count":sum(x["three_synthetic_alpha_semantic_equivalence_test_count"] for x in originals),
            "all_actual_source_negative_post_mutations_detected":sum(
                x.get("negative_post_mutation_real_semantics_dual_SAT",False) and
                x.get("negative_post_mutation_canonical_sha_differs",False) for x in originals),
            "no_new_source_original_SAFE_UNSAFE_claim":True,
            "not_a_learned_role_mapping_model_yet":True,
            "equal_rights_classical_direct_can_compute_same_AST_canonicalization":True,
            "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN","global_Q6":"OPEN",
            "real_originals":originals}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("Q6_POSTHOC_EIGHT_REAL_ORIGINAL_SHA_AUTHENTIC",report["true_original_sha_identity_authenticated"])
    print("Q6_DYNAMIC_SOURCE_ARITY_CANONICAL_NAME_ORDER_INDEPENDENT",passed,"/8")
    print("Q6_TRUE_SOURCE_ALPHA_24_MUTATIONS_INDEPENDENT_72_ORIGINAL_SEMANTICS",dual,"/72")
    print("Q6_TRUE_SOURCE_NEGATIVE_SEMANTIC_MUTATION_GUARDS",report["all_actual_source_negative_post_mutations_detected"],"/8")
    print("Q6_DYNAMIC_SOURCE_CANONICAL_GLOBAL_Q6_OPEN",report["global_Q6"])
if __name__=="__main__":
    main()
