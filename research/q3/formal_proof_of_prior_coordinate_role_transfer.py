"""Independent post-FIRST theorem for the ACTUAL machine-generated GP-Suite AST.

Do not introduce a hand-authored palindrome or mirror-image answer program.
Load the unchanged earlier first-generated AST from the #718 immutable
post-FIRST artifact. Normalize the previous discovered coordinate expression
by structural recursion and ask an external Z3 process whether any
(n,i) violates the affine identity or valid index bounds.

Then check that the discovered input-role binding + quantifier AST is
definitionally identical to equality with the reverse of the other vector
for *ALL* finite sequences. Finite exhaustive enumerations provide an
independent fault-finding control, not the basis of the symbolic theorem.

Original GPCS domain was inspected in #718 before this audit, so this is a
POSTFIRST formal proof, not a new hidden independent benchmark.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import itertools
import json
from pathlib import Path
import random
import shutil
import subprocess
import time

from research.q3.discover_index_relation_constructor import coeffs
from research.q3.learn_argument_roles_for_prior_relation import run_role_program
from research.q3.connected_constructor_router import program_id

SCHEMA="neumann.q3.original-learned-crossargument-relation-formal-proof.v1"
PREVIOUS_POSTFIRST=42365959895
PREVIOUS_ORIGINAL_FIRST=42365072610


def to_smt(ast):
    """Encode actual generated expression recursively; no fixed formula."""
    tag=ast[0]
    if tag in ("i","n"):return tag
    if tag=="c":
        v=ast[1]
        if type(v) is not int:raise ValueError("NONINTEGER_COORDINATE")
        return str(v) if v>=0 else f"(- {-v})"
    if tag in ("add","sub"):
        operator="+" if tag=="add" else "-"
        return f"({operator} {to_smt(ast[1])} {to_smt(ast[2])})"
    raise ValueError("UNCERTIFIED_OPERATION_IN_SOURCE_AST")


def prove_z3(assertion,expected):
    if not shutil.which("z3"):raise RuntimeError("INDEPENDENT_Z3_REQUIRED")
    script=("(set-logic QF_LIA)\n"
            "(declare-const n Int)\n"
            "(declare-const i Int)\n"
            "(assert (>= n 1))\n"
            "(assert (>= i 0))\n"
            "(assert (< i n))\n"
            f"(assert {assertion})\n(check-sat)\n")
    result=subprocess.run(
        ["z3","-in"],input=script,text=True,capture_output=True,
        timeout=20,check=False)
    got=result.stdout.strip().splitlines()
    verdict=got[0] if got else ""
    return {"expected":expected,"observed":verdict,
            "pass":verdict==expected,
            "script":script,"stderr":result.stderr[:300]}


def evaluate(first_path:Path,out:Path):
    if out.exists():raise ValueError("IMMUTABLE_POSTFIRST_FORMAL_PROOF")
    out.mkdir(parents=True)
    first=json.loads(first_path.read_text())
    if first.get("schema")!=\
       "neumann.q3.prior-affine-relation-auto-role-transfer-gpcs-postfirst.v1":
        raise ValueError("SOURCE_ORIGINAL_RESULT_NOT_VALID")
    if first["original_29_first_run"]!=PREVIOUS_ORIGINAL_FIRST:
        raise ValueError("HISTORIC_FIRST_PROVENANCE_CHANGED")
    mirror=next((r for r in first["rows"]
                 if r.get("source_family")=="mirror-image"),None)
    if not mirror or not mirror["warm_original_score"]["exact"]:
        raise ValueError("SOURCE_ORIGINAL_ROLE_PROGRAM_NOT_VERIFIED")
    warm=mirror["warm_with_source_memory"]
    if warm["status"]!="TRANSFERRED_NEW_INPUT_ROLE_BINDING":
        raise ValueError("OPERATOR_DID_NOT_ACTUALLY_REUSE_SOURCE_MEMORY")
    actual=warm["program"]
    old=mirror["cold_same_64_program_budget"]
    new=mirror["cold_larger_1200_program_budget"]
    if old["program"] is not None and mirror["cold_64_original_score"]["exact"]:
        raise ValueError("NO_CAUSAL_BUDGET_ADVANTAGE")
    if not mirror["cold_1200_original_score"]["exact"]:
        raise ValueError("COLD_EXPRESSIVITY_HAS_NOT_BEEN_CHECKED")

    ast=actual["learned_coordinate_expression"]
    formula=to_smt(ast)
    j=actual["learned_coordinate_expression"]
    provenance_hash=first["source_memory_ast_sha256"]

    if (actual["left_argument_role"],actual["right_argument_role"]) not in (
        (0,1),(1,0)):
        raise ValueError("NOT_A_CROSS_ARGUMENT_INVENTION")
    if actual["value_relation"]!="eq" or actual["quantifier"]!="all" or \
       actual["length_guard"]!="equal":
        raise ValueError("NOT_EVERY_ELEMENT_CROSSARGUMENT_EQ")
    # Z3 first proves exact index relation on ALL positive integer lengths,
    # then proves the selected index never goes out of bounds.
    theorem={
      "learned_affine_reflection_identity":
         prove_z3(f"(not (= {formula} (- (- n 1) i)))","unsat"),
      "valid_index_lower_bound":
         prove_z3(f"(< {formula} 0)","unsat"),
      "valid_index_upper_bound":
         prove_z3(f"(>= {formula} n)","unsat"),
      "independent_negative_wrong_coordinate":
         prove_z3("(not (= i (- (- n 1) i)))","sat"),
    }
    # Independent exhaustive consistency with specification across all
    # two-symbol length-matched pairs n in 0..7; not a substitute for Z3.
    count=0;wrong=0
    for n in range(8):
        strings=["".join(v) for v in itertools.product("ab",repeat=n)]
        for a in strings:
            for b in strings:
                predicted=run_role_program(actual,[a,b])
                expected=(a==b[::-1])
                count+=1
                if predicted is not expected:wrong+=1
    # Heterogeneous length cases and random wider lists (original VM
    # bound is 1024; expression is polymorphic).
    rng=random.Random(31811)
    for n in (0,1,2,3,4,5,8,16,32,64,127,256,512):
        for _ in range(20):
            a=[rng.randrange(5) for _ in range(n)]
            b=[rng.randrange(5) for _ in range(n)]
            for left,right in ((a,b),(a,b[::-1]),(b,a)):
                expected=(left==right[::-1])
                if run_role_program(actual,[left,right]) is not expected:
                    wrong+=1
                count+=1
            if n:
                if run_role_program(actual,[a,b[:-1]]) is not False:
                    wrong+=1
                count+=1
    proven=all(v["pass"] for v in theorem.values())
    assert count>=20000 and wrong==0 and proven
    report={
        "schema":SCHEMA,
        "genuine_original_prior_coordinates_from_HumanEval_48":True,
        "prior_generated_coordinate_source_sha256":provenance_hash,
        "target_role_BINDER_generated_in_GP_postfirst_not_handcoded_correct_answer":True,
        "generated_program_sha256":program_id(actual),
        "generated_program_AST":actual,
        "original_GP_source_family":"mirror-image",
        "prior_original_FIRST":PREVIOUS_ORIGINAL_FIRST,
        "actual_GP_postfirst_role_learner_run":PREVIOUS_POSTFIRST,
        "source_exposed_before_formal_theorem":True,
        "warm_original_32_of_32_exact":True,
        "cold_same_candidate_budget_original_exact":False,
        "cold_larger_candidate_budget_original_exact":True,
        "warm_source_candidate_checks":warm["attempts"],
        "cold64_source_candidate_checks":old["attempts"],
        "cold1200_source_candidate_checks":new["attempts"],
        "learned_coordinate_ast_coefficients":coeffs(ast),
        "theorem":theorem,
        "independent_exhaustive_and_random_tests":count,
        "exhaustive_runtime_semantic_disagreements":wrong,
        "proved_all_length_crossargument_reverse_equivalence":proven,
        "this_is_old_external_corpus_POSTFIRST":True,
        "human_defined_two_argument_generic_expression_VM":True,
        "Q3_GLOBAL":"OPEN","Q4_GLOBAL":"OPEN","Q6_GLOBAL":"OPEN",
    }
    (out/"POSTFIRST_FORMAL_THEOREM.json").write_text(
        json.dumps(report,sort_keys=True,indent=2)+"\n")
    for name,check in theorem.items():
        (out/(name+".smt2")).write_text(check["script"])
    print("Q3_SOURCE_MEMORY_ROLE_TRANSFER_INDEPENDENT_FORMAL_PROOF",json.dumps({
        "program_sha256":report["generated_program_sha256"],
        "affine_coefficients":report["learned_coordinate_ast_coefficients"],
        "proven_Z3_obligations":{k:v["pass"] for k,v in theorem.items()},
        "independent_tests":count,
        "disagreements":wrong,
        "warm_attempts":warm["attempts"],
        "cold64_attempts":old["attempts"],
        "cold1200_attempts":new["attempts"],
        "Q3_GLOBAL":"OPEN",
    },sort_keys=True),flush=True)
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    evaluate(a.source,a.out)
