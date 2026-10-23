"""Blind source-learned CA rule identification vs three strong classical gates.

Stage infer never reads any original rule, reference answer or metadata.
Stage grade separately sees identical SHA-pinned original author cases and
uses ORIGINAL official verifier. Source demo pairs constitute *additional*
calibration information deliberately produced from original rule, so do not
present result as raw published hidden-rule test or novel neural invention.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,pathlib,time
from hidden_rule_inference import discover,source_pair_mapping,candidate_rules
from source_then_official_grade import official_verifier

POLICIES=("lookup","one_missing","joint")
PIN="7d86373fdb63fe1bd3592ddf71d923ceebc5acd9"

def infer(file):
    rows={};counts=collections.Counter();costs=collections.defaultdict(float)
    for i,line in enumerate(pathlib.Path(file).read_text().splitlines()):
        record=json.loads(line)
        assert "permutation" not in record["task"]["rule"] and "answer" not in record
        assert record["id"] not in rows
        pol={}
        for name in POLICIES:
            r=discover(record,policy=name)
            pol[name]=r
            costs[name]+=r["cpu_s"]
            counts[f"{record['budget']}:{name}:{r['status']}"]+=1
        # Progressive source information should never change an already
        # mathematically proven answer (all policies cover same consistent rules).
        preds=[tuple(r["prediction"]) for r in pol.values() if r.get("prediction")]
        assert len(set(preds))<=1,(record["id"],"conflicting proof predictions")
        rows[record["id"]]={"original_id":record["original_id"],
            "budget":record["budget"],"policy":pol}
        counts["total"]+=1
        if (i+1)%150==0:
            print("BLIND_UNKNOWN_RULE_PROGRESS",i+1,dict(counts),flush=True)
    assert len(rows)==900
    result={"schema":"NEUMANN_HIDDEN_2D_RULE_CALIBRATION_900_SOURCE_ONLY.v1",
        "n_original_tasks":300,"n_episodes":900,
        "source_hidden_true_rule_absent":True,"query_answer_never_seen":True,
        "neural_model_trained":False,"requires_task_supplied_rule_family":True,
        "source_demos_are_new_supervised_transition_observations":True,
        "policies":POLICIES,"status_counts":dict(counts),
        "source_cpu_by_policy_s":dict(costs),"rows":rows}
    print("BLIND_HIDDEN_RULE_TOTAL_SOURCE_COUNTS",json.dumps(dict(counts),sort_keys=True),flush=True)
    print("BLIND_HIDDEN_RULE_TOTAL_CPU",json.dumps(dict(costs),sort_keys=True),flush=True)
    return result

def grade(sealed,original_file,expected_sha,masked_file):
    prefile=pathlib.Path(sealed);d=json.loads(prefile.read_text())
    assert d["n_episodes"]==900 and d["query_answer_never_seen"]
    original_raw=pathlib.Path(original_file).read_bytes()
    assert hashlib.sha256(original_raw).hexdigest()==expected_sha
    full={r["id"]:r for r in [json.loads(x) for x in original_raw.splitlines()]}
    assert len(full)==300
    masked=[json.loads(x) for x in pathlib.Path(masked_file).read_text().splitlines()]
    assert len(masked)==900
    source={x["id"]:x for x in masked};assert len(source)==900
    verify,official_sha=official_verifier(PIN)
    counts=collections.Counter();cells=collections.Counter();failure_ids=[]
    for uid,receipt in d["rows"].items():
        original=full[receipt["original_id"]];record=source[uid]
        assert record["original_id"]==receipt["original_id"]
        assert "permutation" not in record["task"]["rule"]
        assert verify(original,original["answer"])
        known,error=source_pair_mapping(record["demos"])
        assert error is None
        true_rule=original["rule"]["permutation"]
        assert all(true_rule[a]==b for a,b in known.items())
        budget=record["budget"]
        missing=16-len(known)
        counts[f"{budget}:n"]+=1
        counts[f"{budget}:fully_known_rule"]+=int(missing==0)
        counts[f"{budget}:at_most_one_missing"]+=int(missing<=1)
        counts[f"{budget}:at_most_five_missing"]+=int(missing<=5)
        cells[f"{budget}:sum_missing_rule_entries"]+=missing
        for policy in POLICIES:
            out=receipt["policy"][policy]
            prediction=out.get("prediction")
            assert out.get("observed_map_size",len(known))==len(known)
            if prediction is None:continue
            # Rule remains absent during source inference; independent official
            # author verification only now uses true test rule to evaluate.
            correct=(prediction==original["answer"]["initial_state"] and
                     bool(verify(original,prediction)))
            counts[f"{budget}:{policy}:attempted"]+=1
            counts[f"{budget}:{policy}:correct"]+=int(correct)
            counts[f"{budget}:{policy}:wrong"]+=int(not correct)
            if not correct:failure_ids.append(uid+":"+policy)
    assert sum(counts[f"{b}:n"] for b in (3,6,12))==900
    result={"schema":"NEUMANN_HIDDEN_2D_CA_RULE_COMPLETION_ORIGINAL_GRADE.v1",
        "original_author_exact_raw_sha256":hashlib.sha256(original_raw).hexdigest(),
        "source_prediction_sha256":hashlib.sha256(prefile.read_bytes()).hexdigest(),
        "author_official_verifier_sha256":official_sha,
        "n_original_distinct":300,"n_source_episodes":900,
        "counts":dict(counts),"rule_entry_evidence":dict(cells),
        "failed_submitted_policy_ids":failure_ids,
        "supervised_new_calibration_is_not_part_of_raw_original_benchmark":True,
        "generic_task_rule_family_supplied_not_discovered":True,
        "neural_exclusive_new_primitive_not_proved":True,
        "global_q3_neural_only":"OPEN",
        "global_q4_end_to_end_10x":"OPEN"}
    print("INDEPENDENT_AUTHOR_HIDDEN_RULE_CALIBRATION_ACTUAL_SCORE",
          json.dumps(result["counts"],sort_keys=True),flush=True)
    print("INDEPENDENT_AUTHOR_HIDDEN_RULE_SUBMISSION_FAILURES",
          json.dumps(failure_ids[:10]),flush=True)
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=("infer","grade"),required=True)
    p.add_argument("--source");p.add_argument("--sealed");p.add_argument("--original")
    p.add_argument("--expected-original-sha");p.add_argument("--out",required=True)
    a=p.parse_args()
    result=infer(a.source) if a.mode=="infer" else grade(a.sealed,a.original,a.expected_original_sha,a.source)
    path=pathlib.Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,separators=(",",":"),sort_keys=True)+"\n")
    print("HIDDEN_CA_RULE_EVIDENCE_SHA256",hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
