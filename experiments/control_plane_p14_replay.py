"""Independent model-free replay of the first P1.4 semantic-development receipts."""
import argparse
import hashlib
import json
from pathlib import Path

from neumann1.control_plane_p14 import _routing_from_proposal, parse_proposal, run_mixed_and_execute
from experiments.control_plane_p14_dev import _executor, _hidden_verifier, evaluate
from experiments.control_plane_p14_registration import registration


class RecordedFallback:
    def __init__(self, receipt):
        self.receipt = receipt

    def score(self, view, remaining_ms):
        return self.receipt


def replay(directory):
    directory = Path(directory)
    terminal = json.loads((directory / "terminal.json").read_bytes())
    names = {p.name for p in directory.glob("*.json") if p.name != "terminal.json"}
    if names != set(terminal["files"]):
        raise ValueError("P1.4 terminal receipt coverage drift")
    for name, expected in terminal["files"].items():
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != expected:
            raise ValueError("P1.4 receipt byte drift: " + name)

    report = json.loads((directory / "report.json").read_bytes())
    reg, rows, refs = registration()
    complete = report["status"] == "COMPLETE"
    records = []
    for i, (row, ref) in enumerate(zip(rows, refs)):
        path = directory / ("task_%02d.json" % i)
        if not path.exists():
            if complete:
                raise ValueError("complete P1.4 result missing task receipt")
            continue
        record = json.loads(path.read_bytes())
        if record.get("task_id") != row["task_id"] or record.get("kind") != ref["kind"]:
            raise ValueError("P1.4 task identity drift")

        if ref["kind"] == "RAW_SEMANTIC":
            if record.get("model_calls") != 1:
                raise ValueError("raw semantic item must charge exactly one model call")
            proposal = record.get("proposal")
            if proposal is None:
                receipt = record.get("semantic_receipt")
                if record.get("status") != "FAILED" or not record.get("error"):
                    raise ValueError("missing proposal requires retained semantic failure")
                if type(receipt) is dict and type(receipt.get("raw")) is str:
                    try:
                        parse_proposal(receipt["raw"])
                    except Exception:
                        pass
                    else:
                        # A syntactically valid raw proposal can still fail a
                        # post-generation identity/deadline/VRAM gate.
                        if not any(x in record["error"] for x in (
                            "deadline", "VRAM", "identity", "receipt", "budget"
                        )):
                            raise ValueError("unexplained semantic failure with valid proposal")
                if record.get("accepted") is not False or record.get("executed") is not False:
                    raise ValueError("failed semantic compilation cannot execute")
            elif proposal.get("route") == "ABSTAIN":
                if record.get("status") != "ABSTAINED" or record.get("accepted") is not False or record.get("executed") is not False:
                    raise ValueError("semantic abstention replay drift")
            else:
                typed, routed = _routing_from_proposal(row["view"], proposal)
                answer = _executor(routed["selected_route"], routed["project"])
                accepted = _hidden_verifier(ref)(row["view"], answer)
                expected_status = "ACCEPTED" if accepted else "REJECTED_BY_ORIGINAL_VERIFIER"
                if record.get("selected_route") != routed["selected_route"]:
                    raise ValueError("raw semantic selected-route drift")
                if record.get("status") != expected_status or record.get("accepted") is not accepted or record.get("executed") is not True:
                    raise ValueError("raw semantic execution/verifier replay drift")
        else:
            routing = record.get("routing")
            receipt = routing.get("fallback_receipt") if type(routing) is dict else None
            if type(receipt) is dict:
                expected = run_mixed_and_execute(
                    row["view"],
                    lambda receipt=receipt: RecordedFallback(receipt),
                    _executor,
                    _hidden_verifier(ref),
                )
                for key in ("status", "accepted", "executed", "selected_route"):
                    if record.get(key) != expected.get(key):
                        raise ValueError("mixed fallback replay drift: " + key)
            else:
                if record.get("status") != "FAILED" or not record.get("error"):
                    raise ValueError("missing mixed fallback receipt requires retained failure")
                if record.get("accepted") is not False:
                    raise ValueError("failed mixed fallback cannot be accepted")
        records.append(record)

    decision = evaluate(records, refs if complete else [], report["core_audit"].get("unchanged"), complete, report["whole_study_ms"])
    if decision != report["decision"] or terminal["decision"] != decision["verdict"] or terminal["complete"] != complete:
        raise ValueError("P1.4 decision/terminal drift")
    if terminal.get("no_replacement") is not True or terminal.get("development_only") is not True:
        raise ValueError("P1.4 first-only boundary drift")
    if report.get("frontier_calls") != 0 or report.get("new_training") is not False or report.get("sealed_data_opened") is not False:
        raise ValueError("P1.4 forbidden-study drift")
    if report.get("development_only") is not True:
        raise ValueError("P1.4 opened-development boundary drift")
    if decision.get("p2_registration_admitted") is not False or decision.get("p2_admitted") is not False or decision.get("decision3_admitted") is not False:
        raise ValueError("P1.4 admission boundary drift")
    if complete:
        manifest = json.loads((directory / "manifest.json").read_bytes())
        if manifest["registration"] != reg or manifest["public_rows"] != rows or manifest["frozen_head"] != report["source_head"]:
            raise ValueError("P1.4 frozen manifest drift")
    return {
        "integrity_valid": True,
        "complete": complete,
        "decision": decision,
        "model_inference": False,
        "p2_registration_admitted": False,
        "decision3_admitted": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    args = parser.parse_args()
    print(json.dumps(replay(args.directory), sort_keys=True))
