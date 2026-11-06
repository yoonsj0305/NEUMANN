"""RC40 independent, READ-ONLY audit of exact FIRST artifact. No re-learning.

This auditor uses an alternate raw-state-table product checker; it never calls
the active learner, W-method, or their interpreter. A pre-pinned SHA256 binds the
FIRST receipt, preventing favorable replay/score replacement.
"""
import hashlib
import json
import sys
from collections import deque
from pathlib import Path

from research.q3.rc39.independent_first_grader import hidden_family

FIRST_SHA256 = "9174cbaf28715a36bae57731b0295e39c8a0b5c63e4436541692a1f09fc446e2"
FAMILIES = ("prefix_parity", "prefix_mod3", "presence",
            "random_3state", "random_4state", "random_5state")
EXPECTED = {(f, seed) for f in FAMILIES for seed in (39,40,41,42)}


def alternate_product_proof(reference, raw):
    """Own transition and output access without MealyProgram or original grader."""
    if not isinstance(raw, dict) or raw.get("schema") != "neumann.rc39.mealy-ast.v1":
        return False
    alphabet = raw.get("alphabet")
    moves = raw.get("transitions")
    outputs = raw.get("emissions")
    count = raw.get("states")
    initial = raw.get("initial")
    if alphabet != list(reference.alphabet) or type(count) is not int or count < 1:
        return False
    if not isinstance(moves,list) or not isinstance(outputs,list) or len(moves)!=count or len(outputs)!=count:
        return False
    if type(initial) is not int or not 0 <= initial < count:
        return False
    queue = deque([(reference.initial, initial)])
    seen = set(queue)
    while queue:
        source_state, candidate_state = queue.popleft()
        for index, letter in enumerate(alphabet):
            if (len(moves[candidate_state])!=len(alphabet)
                    or len(outputs[candidate_state])!=len(alphabet)):
                return False
            target_next, target_output = reference.table[source_state,letter]
            candidate_output = outputs[candidate_state][index]
            candidate_next = moves[candidate_state][index]
            if type(candidate_next) is not int or not 0 <= candidate_next < count:
                return False
            if candidate_output != target_output:
                return False
            pair = (target_next, candidate_next)
            if pair not in seen:
                seen.add(pair)
                queue.append(pair)
    return True


def audit(path):
    data = Path(path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    errors = []
    if digest != FIRST_SHA256:
        errors.append("ORIGINAL_FIRST_RECEIPT_SHA_DRIFT")
    try:
        raw = json.loads(data)
    except Exception as exc:
        return {"audit_pass":False,"errors":errors+[str(exc)],"sha256":digest}
    rows = raw.get("rows",[])
    if len(rows)!=24 or {(r["family"],r["seed"]) for r in rows}!=EXPECTED:
        errors.append("ORIGINAL_TASK_SET_CHANGED")
    totals = {k:0 for k in (
        "w_unique_source_queries","baseline_unique_source_queries",
        "w_unique_source_symbols","baseline_unique_source_symbols",
        "w_conformance_words_checked","baseline_conformance_words_checked")}
    verified=0
    mutated_rejected=0
    for row in rows:
        reference=hidden_family(row["family"],row["seed"])
        original=row["w_ast"]
        correct=alternate_product_proof(reference,original)
        verified+=int(correct)
        if not correct or not row["w_certificate"] or not row["w_independent_exact"]:
            errors.append("UNSOUND_W_STATE_PROGRAM")
        if row["w_false_certificate"]:
            errors.append("REPORTED_FALSE_CERTIFICATE")
        if original:
            changed=json.loads(json.dumps(original))
            state=changed["initial"]
            a=changed["emissions"][state][0]
            changed["emissions"][state][0]="1" if a=="0" else "0"
            rejected=not alternate_product_proof(reference,changed)
            mutated_rejected+=int(rejected)
            if not rejected:
                errors.append("MUTATION_FALSE_ACCEPT")
        for k in totals:
            totals[k]+=row[k]
    aggregate=raw.get("metrics",{})
    for k,expected in totals.items():
        if aggregate.get(k)!=expected:
            errors.append("REPORTED_METRIC_DRIFT_"+k)
    if verified!=24 or mutated_rejected!=24:
        errors.append("NOT_ALL_24_PROVED_AND_MUTANTS_REJECTED")
    if totals["baseline_unique_source_queries"]!=172051:
        errors.append("BASELINE_COST_CHANGED")
    if totals["w_unique_source_queries"]!=6117:
        errors.append("W_FIRST_COST_CHANGED")
    if not 172051/totals["w_unique_source_queries"] > 28:
        errors.append("QUERY_REDUCTION_NOT_OVER_28")
    if raw.get("science_status")!="SCOPED_W_QUERY_10X_PASS":
        errors.append("ORIGINAL_SCIENCE_STATUS_CHANGED")
    if raw.get("scientific_limits",{}).get("Q6_external_semantic_family_transfer")!="OPEN":
        errors.append("GLOBAL_GENERALIZATION_OVERCLAIM")
    return {
        "schema":"neumann.q3.rc40.independent-readonly-original-audit.v1",
        "audit_pass":not errors,"errors":errors,
        "first_sha256":digest,
        "independent_all_length_programs":verified,
        "altered_programs_rejected":mutated_rejected,
        "source_queries_original_total":totals["baseline_unique_source_queries"],
        "source_queries_w_total":totals["w_unique_source_queries"],
        "query_reduction_factor":172051/6117,
        "model_or_w_method_reexecuted":False,
        "new_semantic_family_tested":False,
        "global_Q3_Q4_Q6_Q7":"OPEN"
    }


if __name__ == "__main__":
    result=audit(sys.argv[1])
    print(json.dumps(result,indent=2))
    if not result["audit_pass"]:
        raise SystemExit(1)
