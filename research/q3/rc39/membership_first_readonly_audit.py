"""Read-only audit of RC39 24 reopened source-membership-only FIRST receipt.

Uses earlier separate-language-of-implementation (different source and
independent AST interpreter), not the learning code or the conformance code.
No learning, no source queries or hidden EQ oracle during this audit.
"""
from __future__ import annotations
from hashlib import sha1,sha256
from pathlib import Path
import json,sys
from research.q3.rc39.independent_readonly_audit import external_reference,prove_independent

ROOT=Path(__file__).resolve().parents[3]
FIRST="f89b488bee9dfe3f04ec2ac0566bab265385b08d32611ea637c4fa299e3d1f1f"
def blob(path:Path):
    x=path.read_bytes()
    return sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()

def audit(first_path):
    b=Path(first_path).read_bytes()
    first=json.loads(b)
    lock=json.loads((ROOT/"docs/experiments/q3_RC39_MEMBERSHIP_ONLY_SOURCE_LOCK.json").read_text())
    pre=json.loads((ROOT/"docs/experiments/q3_RC39_MEMBERSHIP_ONLY_REOPENED24_PREREG.json").read_text())
    errors=[]
    def check(ok,description):
        if not ok:errors.append(description)
    check(sha256(b).hexdigest()==FIRST,"ORIGINAL_FIRST_RECEIPT_SHA_DRIFT")
    for path,sha in lock["source_blobs"].items():
        check(blob(ROOT/path)==sha,"ORIGINAL_SOURCE_CHANGED:"+path)
    check(first["scope"]=="REUSED_OPENED_24_SAME_HIDDEN_STATE_FAMILY_NOT_NEW_HELDOUT","SCIENTIFIC_SCOPE_DRIFT")
    check(first["upper_bound_on_reference_states"]==5,"ASSUMED_STATE_BOUND_CHANGED")
    check(not first["uses_hidden_reference_graph_during_learning"] and
          not first["uses_true_equivalence_counterexamples_during_learning"],"EXTRA_SOURCE_RIGHTS_CLAIM_CHANGED")
    pairs=[(f,s) for f in pre["source_rights"] and
           ["prefix_parity","prefix_mod3","presence","random_3state","random_4state","random_5state"]
           for s in (39,40,41,42)]
    check(len(first["rows"])==24,"FIRST_TASK_COUNT_CHANGED")
    proven=0;rejected=0;total_nodes=0
    for i,((family,seed),row) in enumerate(zip(pairs,first["rows"])):
        check(row["family"]==family and row["seed"]==seed,"FIRST_TASK_ORDER:"+str(i))
        ref=external_reference(family,seed)
        check(ref[0]<=5,"REFERENCE_OUTSIDE_AUTHORIZED_STATE_BOUND:"+str(i))
        source=row["model_generated"]
        check(source is not None,"MISSING_ORIGINAL_EXECUTABLE_PROGRAM:"+str(i))
        if source is None:continue
        try:
            is_equal,ce,nodes=prove_independent(ref,source)
            proven+=int(is_equal)
            total_nodes+=nodes
            check(is_equal and ce is None,"FAILED_INDEPENDENT_ALL_LENGTH_PROOF:"+str(i))
            check(row["independent_product_exact"]==is_equal,"FIRST_ORIGINAL_CERT_DRIFT:"+str(i))
            check(row["source_only_claim_status"]=="SCOPED_ALL_LENGTHS_PROVED","FALSE_ORIGINAL_SOURCE_CERT:"+str(i))
            check(row["completed_completeness_cutoff"]==5+source["states"]-1,
                  "SHORT_FINITE_CONFORMANCE_SCOPE:"+str(i))
            mutant=json.loads(json.dumps(source))
            q=mutant["initial"]
            mutant["emissions"][q][0]="1" if mutant["emissions"][q][0]=="0" else "0"
            should_fail,found,_=prove_independent(ref,mutant)
            rejected+=int(not should_fail and found is not None)
        except Exception as e:errors.append("REPLAY_MALFORMED:"+str(i)+":"+str(e))
    check(proven==first["independently_all_length_proven"],"ORIGINAL_TOTAL_CORRECTNESS_CHANGED")
    check(proven==24 and rejected==24,"ORIGINAL_NEGATIVE_CONTROLS_FAILURE")
    expected={
      "source_distinct_membership_calls":"total_unique_source_membership_calls",
      "source_distinct_membership_symbols":"total_unique_source_symbols",
      "all_source_membership_requests_including_cache":"all_source_query_requests_including_cached",
      "conformance_words_checked":"conformance_full_word_checks",
      "conformance_callbacks":"conformance_callbacks"}
    for outer,inner in expected.items():
        check(sum(x[inner] for x in first["rows"])==first["metrics"][outer],"ORIGINAL_COST_METER_DRIFT:"+outer)
    check(first["science_status"]=="SCOPED_MEMBERSHIP_ONLY_FIRST_24_PASS","FALSE_FIRST_SCIENCE_PROMOTION")
    return {
      "schema":"neumann.q3.rc39.membership-only-first-independent-readonly.v1",
      "first_receipt_sha256":sha256(b).hexdigest(),
      "auditor_pass":not errors,"errors":errors,
      "original_24_mealy_all_length_certificates_replayed":proven,
      "independent_mutated_programs_rejected":rejected,
      "independent_product_states_visited":total_nodes,
      "original_distinct_membership_query_cost":first["metrics"]["source_distinct_membership_calls"],
      "original_total_membership_symbols":first["metrics"]["source_distinct_membership_symbols"],
      "original_word_conformance_checks":first["metrics"]["conformance_words_checked"],
      "exact_assumption":"reference is a deterministic complete Mealy machine with max 5 states",
      "true_equivalence_oracle_used_during_training":False,
      "referenced_task_cohort":"previously opened 24 RC39 examples, not unseen tasks",
      "baseline":"the algorithm itself is classical; no independent model-vs-TOOL advantage",
      "q3":"OPEN","q6":"OPEN","q7":"OPEN"
    }
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: python -m research.q3.rc39.membership_first_readonly_audit FIRST.json")
    r=audit(sys.argv[1])
    print(json.dumps(r,sort_keys=True,indent=2))
    if not r["auditor_pass"]:raise SystemExit(1)
