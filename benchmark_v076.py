"""Frozen post-head parity audit. Not a trained-model or timing benchmark."""

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from neumann1.paired_linear_dataset import make_near_negative, sequence_challenger_final_examples
from neumann1.program_parity_v076 import direct_tool_program_route, structural_route


def run():
    digest = hashlib.sha256()
    rows = []
    positive_verified = negative_rejected = 0
    mismatches = 0
    for index, example in enumerate(sequence_challenger_final_examples()):
        for negative in (False, True):
            text = make_near_negative(example, index) if negative else example.text
            local_mismatches = 0
            for head in range(82):
                structural = structural_route(text, head)
                program = direct_tool_program_route(text, head)
                local_mismatches += structural != program
                record = {"index": index, "negative": negative, "head": head,
                          "structural": asdict(structural), "program": asdict(program)}
                digest.update((json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode())
                if head == 0:
                    if negative:
                        negative_rejected += program.status == "COMPILER_REJECT"
                    else:
                        answer = dict(program.answer)
                        known_match = all(abs(answer.get(v, float("inf")) - value) < 1e-7
                                          for v, value in zip(example.variables, example.solution))
                        positive_verified += program.status == "VERIFIED" and known_match
            mismatches += local_mismatches
            rows.append({"index": index, "negative": negative,
                         "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                         "heads_checked": 82, "mismatches": local_mismatches})
    okay = mismatches == 0 and positive_verified == 243 and negative_rejected == 243
    return {"experiment": "v0.0.76 direct atomic-program post-head parity",
            "decision": "POST_HEAD_EQUIVALENCE_ONLY_NOT_Q4_PASS" if okay else "PARITY_CONTRACT_FAILED",
            "texts": len(rows), "paired_post_head_checks": sum(r["heads_checked"] for r in rows),
            "mismatches": mismatches, "positive_head0_verified_known_matches": positive_verified,
            "negative_head0_compiler_rejections": negative_rejected,
            "stream_sha256": digest.hexdigest(), "model_inferences": 0,
            "new_training_runs": 0, "timing_measurements": 0, "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))
