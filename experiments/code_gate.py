"""One-shot public capability baseline + post-discovery cost diagnostics.

References are private evaluation authority only, never generation context.
This does not reopen Decision3, reproduce the full benchmark, or prove Q1-Q7.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

from neumann1.code_contract import admit, messages


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def references(tasks, output):
    from evalplus.gen.util import trusted_exec
    outputs = {}
    started = time.perf_counter()
    for task in tasks:
        code = task["prompt"] + task["canonical_solution"]
        outputs[task["task_id"]] = {}
        for group in ("base", "plus"):
            expected, elapsed = trusted_exec(code, task[group + "_input"], task["entry_point"], record_time=True)
            outputs[task["task_id"]][group] = {"expected": expected, "reference_times": elapsed}
    # Use pickle for reference outputs whose exact tuple/set types matter.
    import pickle
    (output / "reference.private.pkl").write_bytes(pickle.dumps(outputs))
    return outputs, time.perf_counter() - started


def run(root):
    import multiprocessing
    # Fresh CPU checker processes avoid inheriting CUDA context/model VM.
    multiprocessing.set_start_method("spawn", force=True)
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from evalplus.sanitize import sanitize
    from evalplus.eval import untrusted_check
    reg = json.loads((root / "registration.json").read_text())
    repo = Path(__file__).resolve().parents[1]
    for rel, expected in reg["source_sha256"].items():
        if sha(repo / rel) != expected:
            raise ValueError(f"registered source mismatch: {rel}")
    for filename, expected in reg["data_sha256"].items():
        if sha(root / filename) != expected:
            raise ValueError("registered data mismatch")
    if (root / "records.jsonl").exists():
        raise ValueError("first evidence already exists; rerun forbidden")
    public = json.loads((root / "public.json").read_text())
    tasks = json.loads((root / "references.private.json").read_text())
    if [item["task_id"] for item in public] != [item["task_id"] for item in tasks]:
        raise ValueError("public/reference alignment mismatch")
    if not torch.cuda.is_available():
        raise ValueError("CUDA required; no CPU model fallback")
    torch.manual_seed(reg["seed"])
    torch.set_num_threads(1)
    study_started = time.perf_counter()
    ref_outputs, reference_preparation_seconds = references(tasks, root)
    load_started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(root / "model", local_files_only=True)
    for task in public:
        encoded = tokenizer.apply_chat_template(messages(task), tokenize=True, add_generation_prompt=True)
        if len(encoded) > reg["max_input_tokens"]:
            raise ValueError("pre-inference prompt admission exceeded")
    model = AutoModelForCausalLM.from_pretrained(root / "model", local_files_only=True,
             dtype=torch.float16, attn_implementation="sdpa").to("cuda:0").eval()
    torch.cuda.synchronize()
    model_setup_seconds = time.perf_counter() - load_started
    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    rows = []
    with (root / "records.jsonl").open("x", encoding="utf-8") as receipt:
        for visible, private in zip(public, tasks):
            started = time.perf_counter()
            torch.cuda.reset_peak_memory_stats()
            inputs = tokenizer.apply_chat_template(messages(visible), tokenize=True,
                        add_generation_prompt=True, return_tensors="pt", return_dict=True).to("cuda:0")
            if inputs["input_ids"].shape[1] > reg["max_input_tokens"]:
                raise ValueError("registered prompt admission exceeded")
            generation_started = time.perf_counter()
            with torch.inference_mode():
                generated = model.generate(**inputs, do_sample=False,
                    max_new_tokens=reg["max_new_tokens"], max_time=reg["max_generation_seconds"],
                    pad_token_id=tokenizer.eos_token_id)
            torch.cuda.synchronize()
            generation_seconds = time.perf_counter() - generation_started
            tokens = generated[0, inputs["input_ids"].shape[1]:]
            completion = tokenizer.decode(tokens, skip_special_tokens=True)
            checks = {}
            sanitize_started = time.perf_counter()
            source = sanitize(completion, private["entry_point"])
            try:
                admit(source, private["entry_point"])
                error = None
            except (ValueError, SyntaxError) as exception:
                error = str(exception)
            parse_seconds = time.perf_counter() - sanitize_started
            verification_started = time.perf_counter()
            for group in ("base", "plus"):
                if error:
                    checks[group] = {"status": "ADMISSION_FAIL", "passed_cases": 0,
                                     "total_cases": len(private[group + "_input"])}
                else:
                    gold = ref_outputs[visible["task_id"]][group]
                    status, details = untrusted_check("humaneval", source, private[group + "_input"],
                        private["entry_point"], expected=gold["expected"], atol=private["atol"],
                        ref_time=gold["reference_times"], fast_check=False)
                    checks[group] = {"status": status, "passed_cases": int(sum(details)),
                                     "total_cases": len(private[group + "_input"])}
            verification_seconds = time.perf_counter() - verification_started
            row = {"task_id": visible["task_id"], "raw_completion": completion, "source": source,
                   "input_tokens": inputs["input_ids"].shape[1], "output_tokens": len(tokens),
                   "ended_at_eos": int(tokens[-1]) == tokenizer.eos_token_id if len(tokens) else False,
                   "generation_seconds": generation_seconds, "parse_seconds": parse_seconds,
                   "verification_seconds": verification_seconds,
                   "complete_seconds": time.perf_counter() - started,
                   "gpu_peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                   "gpu_peak_reserved_bytes": torch.cuda.max_memory_reserved(),
                   "admission_error": error, "checks": checks,
                   "joint_correct": all(check["status"] == "pass" for check in checks.values())}
            rows.append(row)
            receipt.write(json.dumps(row, ensure_ascii=False) + "\n")
            receipt.flush()
            print(f"{len(rows)}/{len(public)} {row['task_id']} base={checks['base']['status']} plus={checks['plus']['status']}", flush=True)
    passed = sum(row["joint_correct"] for row in rows)
    # A FREE already-correct program gives only post-discovery verifier costs.
    # It is not a deployable NEUMANN candidate or complete cost lower bound.
    diagnostics = {"generation_seconds": sum(row["generation_seconds"] for row in rows),
                   "verification_seconds_all_attempts": sum(row["verification_seconds"] for row in rows),
                   "meaning": "cost attribution, not oracle-free discovery or 10x gain"}
    report = {"status": "COMPLETE", "study": reg["study"], "passed": passed, "total": len(rows),
              "capability_floor": reg["capability_floor"], "baseline_admitted": passed >= reg["capability_floor"],
              "model": reg["model"], "parameter_count": parameter_count,
              "model_setup_seconds": model_setup_seconds,
              "reference_preparation_seconds": reference_preparation_seconds,
              "study_seconds": time.perf_counter() - study_started,
              "complete_items_seconds": sum(row["complete_seconds"] for row in rows),
              "cost_attribution": diagnostics, "model_calls": len(rows),
              "input_tokens": sum(row["input_tokens"] for row in rows),
              "output_tokens": sum(row["output_tokens"] for row in rows),
              "gpu_peak_allocated_bytes": max(row["gpu_peak_allocated_bytes"] for row in rows),
              "limitations": reg["limitations"],
              "cost_unknown": ["original model training", "energy", "FLOPs", "money", "GPU idle/allocation overhead"],
              "receipts_sha256": sha(root / "records.jsonl"),
              "registration_sha256": sha(root / "registration.json")}
    save(root / "report.json", report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    run(args.root)
