"""Self-generated SOURCE probes between frozen, source-consistent hypotheses.

No task-specific answer generator: both outputs come from already discovered
programs. A disagreement is NOT an oracle saying which program is correct.
"""
from __future__ import annotations
import json
import pathlib
import random
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/q6"))
from source_study import OUT
from neumann1.q6.contracts import digest
from neumann1.q6.transport import tup
from reference import execute, parse_program


def main():
    path = OUT / "self_probe_disagreements.json"
    if path.exists():
        raise SystemExit("preserve first self-probe diagnostic")
    first = json.loads((OUT / "result.json").read_text())
    old = json.loads((ROOT / "docs/experiments/results/spec_core_dev_source.json").read_text())["rule"]["S_rows"]
    rng = random.Random(745)
    inputs = [((tuple(rng.randint(0, 9) for _ in range(n))),) for n in (0, 1, 2, 4, 8, 16, 24, 32, 40) for _ in range(4)]
    records, c0 = [], time.process_time()
    for r in first["grades"]:
        if r["arm"] != "C" or r.get("via") != "compound_transport":
            continue
        prior = old[r["id"]]
        if not prior["solved"] or not prior.get("program"):
            records.append({"receiver": r["id"], "status": "NO_ALTERNATIVE_Q3_HYPOTHESIS",
                            "scope": "no equivalence/correctness conclusion"})
            continue
        alternative = parse_program(prior["program"])
        candidate = tup(r["sol"])
        disagreements, undefined = [], 0
        for i in inputs:
            a, b = execute(candidate, i), execute(alternative, i)
            if a is None or b is None:
                undefined += 1
                continue
            if a != b:
                disagreements.append({"input_digest": digest(i), "input_length": len(i[0]),
                                      "transported_output_digest": digest(a), "alternative_output_digest": digest(b)})
        records.append({"receiver": r["id"], "transported_program": r["program"],
                        "alternative_q3_program": prior["program"], "generic_probes": len(inputs),
                        "disagreements": disagreements, "undefined_probes": undefined,
                        "status": "HYPOTHESES_NOT_EQUIVALENT" if disagreements else "NO_DISAGREEMENT_ON_FINITE_PROBES",
                        "scope": "neither program is a gold oracle; this disproves equivalence, not original-task correctness; no policy update or score change"})
    result = {"scope": "SOURCE-only post-primary diagnostic", "records": records,
              "receiver_TEST_read": False, "new_target_answer_generator": False,
              "cpu_seconds": time.process_time() - c0}
    path.write_text(json.dumps(result, indent=2) + "\n")
    print({"records": [(r["receiver"], r["status"], len(r.get("disagreements", []))) for r in records]})


if __name__ == "__main__":
    main()
