"""Q3 cycle-break admission gate: no more fixed-H revisions as learned novelty.

This is an EXECUTABLE PRE-EXPERIMENT stop rule, NOT a proof of scientific Q3.
It validates byte-locked inputs, independent source-family rights, the
generator/classical comparator match and full cost meters BEFORE any original
held-out scoring. The underlying domain tasks and model weights are NEVER
loaded or evaluated here. Only stdlib needed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CLOSED_MECHANISM_CLASSES = {
    "FIXED_DSL_RANKER": "P1.5 U=E 1/32; more same-H rankers cannot repair H_D empty",
    "FIXED_DSL_DEEPER_SEARCH": "P2.5 0/32, P2.6 31/31 out-of-language",
    "TEACHER_PROGRAM_CACHE": "P1.4 0/24; P43 only 1/400 unchanged programs",
    "ONE_SEED_SYMMETRY_ORBIT": "P44 180 variants, +0 beyond previous 55",
    "ONE_SEED_MASK_MERGE": "P45 1800 variants; independently complete 720000 checks, 399/400 H_D empty",
    "BOUNDED_MEALY_CLASSICAL_REUSE": "RC39-RC42 is classical under supplied Mealy semantics and state bound",
    "HAND_EXPANDED_FINITE_GRAMMAR": "P2.5/P2.6 and P44/P45: manual H growth is not learned Q3",
    "EASY_CLASSICAL_ROUTE_ONLY": "AM3 12/12 already solved by classical, no learned-only headroom",
    "KNOWN_VERYMAX_OR_SPLIT": "G0 original source UNKNOWN in both branches, subsequent posthoc tuning barred",
}

HEX="0123456789abcdef"
COST_FIELDS=(
    "data_preparation","model_training","inference","candidate_search",
    "source_queries","independent_verification","failed_attempts",
    "fallback_and_operations",
)


def is_hash(x: Any) -> bool:
    return isinstance(x,str) and len(x)==64 and all(c in HEX for c in x)


def valid_original_sha(path: Any, digest: Any, repo: Path) -> bool:
    """Local checkpoint and frozen source identities, refuse path escapes."""
    if not isinstance(path,str) or not path or not is_hash(digest):
        return False
    rel=Path(path)
    if rel.is_absolute() or ".." in rel.parts:
        return False
    try:
        resolved=(repo/rel).resolve(strict=True)
        resolved.relative_to(repo.resolve())
        if not resolved.is_file():
            return False
        return hashlib.sha256(resolved.read_bytes()).hexdigest()==digest
    except (ValueError,OSError):
        return False


def analyze(spec: dict[str,Any],repo: Path) -> dict[str,Any]:
    """The only affirmative outcome is READY_TO_ATTEMPT, never Q3 PASS."""
    errors=[]
    if spec.get("schema")!="neumann.q3.unseen-semantic-proposer-admission.v1":
        errors.append("INVALID_CORE_CONTRACT_SCHEMA")
    strategy=spec.get("strategy")
    if strategy in CLOSED_MECHANISM_CLASSES:
        return {
            "schema":"neumann.q3.cycle-break-verdict.v1",
            "decision":"HARD_STOP_REPEAT_CLASS",
            "strategy":strategy,
            "reason":CLOSED_MECHANISM_CLASSES[strategy],
            "Q3_learned_discovery":"NOT_PROVEN",
            "can_consume_untouched_arc_eval":False,
            "spend_authorized":False
        }
    if strategy!="OWN_WEIGHT_GENERATIVE_EXECUTABLE_AST":
        errors.append("NO_GENUINELY_LEARNED_PROGRAM_GENERATOR")
    generator=spec.get("generator",{})
    if not isinstance(generator,dict):
        generator={}
    for key in ("own_weights_trained","candidate_can_escape_frozen_H",
                "not_only_ranking_or_retrieval","typed_executable_AST",
                "frozen_before_original_test"):
        if generator.get(key) is not True:
            errors.append("GENERATOR_REQUIRED_"+key.upper())
    for role in ("learned_checkpoint","learned_training_code",
                 "strong_classical_solver","independent_original_verifier"):
        info=spec.get("artifacts",{}).get(role,{}) if isinstance(spec.get("artifacts"),dict) else {}
        if not valid_original_sha(info.get("file"),info.get("sha256"),repo):
            errors.append("MISSING_OR_UNVERIFIED_FROZEN_ARTIFACT_"+role.upper())
    evaluation=spec.get("evaluation",{})
    if not isinstance(evaluation,dict):
        evaluation={}
    if evaluation.get("source_author") in (None,"","neumann_project","experiment_designer"):
        errors.append("NO_INDEPENDENT_EXTERNAL_TASK_AUTHOR")
    if evaluation.get("task_status")!="NEVER_OPENED_BY_PROJECT":
        errors.append("NOT_PROJECT_UNSEEN")
    if evaluation.get("original_scope")!="DIFFERENT_SEMANTIC_FAMILY":
        errors.append("NOT_CROSS_FORMALISM")
    if evaluation.get("gold_hidden_until_source_freeze") is not True:
        errors.append("TEST_GOLD_LEAK_RISK")
    if evaluation.get("training_and_test_task_ids_disjoint") is not True:
        errors.append("TRAIN_TEST_IDS_NOT_DISJOINT")
    if not valid_original_sha(evaluation.get("source_manifest_file"),
                              evaluation.get("source_manifest_sha256"),repo):
        errors.append("SOURCE_MANIFEST_UNPINNED_OR_UNVERIFIED")
    if evaluation.get("from_arc_agi_1_evaluation") is True:
        # Globally only 11/400 remain untouched; no new source evaluation
        # without the separate PR #650 ledger + novel semantic proposal.
        errors.append("ARC_EVAL_RESERVED_GLOBAL_389_USED_11_LEFT")
    compare=spec.get("comparison",{})
    if not isinstance(compare,dict):
        compare={}
    for key in ("same_program_language_and_primitives",
                "same_input_and_tool_rights","same_total_runtime_budget",
                "strong_GP_CEGIS_and_domain_specialist",
                "untrained_generator_ablation",
                "independent_original_witness_checker"):
        if compare.get(key) is not True:
            errors.append("MISSING_EQUAL_RIGHTS_CONTROL_"+key.upper())
    cost=spec.get("cost_contract",{})
    if not isinstance(cost,dict) or any(
        not isinstance(cost.get(k),dict) or
        cost[k].get("unit") not in ("ns","ms","s","J","MiB","USD","calls","tokens") or
        cost[k].get("meter") in (None,"","UNKNOWN") for k in COST_FIELDS
    ):
        errors.append("INCOMPLETE_ALL_IN_RESOURCE_ACCOUNTING")
    first=spec.get("first_run",{})
    if not isinstance(first,dict):
        first={}
    if type(first.get("original_denominator")) is not int or first["original_denominator"]<1:
        errors.append("NO_FROZEN_ORIGINAL_DENOMINATOR")
    if first.get("one_original_FIRST_only") is not True:
        errors.append("FAVORABLE_RERUN_RISK")
    if first.get("negative_mutations_preregistered") is not True:
        errors.append("NO_INDEPENDENT_NEGATIVE_CONTROLS")
    if first.get("no_success_from_unknown") is not True:
        errors.append("UNSAFE_UNKNOWN_PROMOTION")
    if first.get("complete_cost_and_new_witness_required") is not True:
        errors.append("PROOF_OR_COST_CANNOT_BE_SKIPPED")
    return {
        "schema":"neumann.q3.cycle-break-verdict.v1",
        "decision":("READY_FOR_ONE_FIRST_ATTEMPT_NOT_A_PROOF" if not errors
                    else "HOLD_NO_NEW_EXPENSIVE_ORIGINAL_EVALUATION"),
        "strategy":strategy,
        "errors":errors,
        "experiment_ready":not errors,
        "Q3_learned_discovery":"NOT_PROVEN",
        "can_consume_untouched_arc_eval":False,
        "spend_authorized":not errors,
        "warning":"A READY preflight is never a scientific PASS. External task authorship, exact original proof and matched capability + complete cost must be independently audited after the one FIRST run."
    }


def main() -> int:
    parser=argparse.ArgumentParser(description="Preflight reject duplicate fixed-H Q3 research. Does not score originals.")
    parser.add_argument("contract",type=Path)
    parser.add_argument("--repo",type=Path,default=Path("."))
    args=parser.parse_args()
    try:
        spec=json.loads(args.contract.read_text())
        if not isinstance(spec,dict):
            raise ValueError("contract must be a JSON object")
        verdict=analyze(spec,args.repo)
    except (OSError,ValueError,json.JSONDecodeError) as exc:
        verdict={"schema":"neumann.q3.cycle-break-verdict.v1",
                 "decision":"HOLD_UNREADABLE_CONTRACT",
                 "error":str(exc)[:180],"spend_authorized":False}
    print(json.dumps(verdict,sort_keys=True,indent=2))
    return 0 if verdict.get("experiment_ready") else 2


if __name__=="__main__":
    raise SystemExit(main())
