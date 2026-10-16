"""FGSR one-attempt neural structural proposal on an OPENED authentic source.

Diagnostic of pretrained language semantics, not NEUMANN Q3/Q7 proof.
No gold auxiliary theorem or coefficient is provided in the prompt.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import time
import urllib.request

SOURCE_COMMIT = "e5a86a1ad252fe1df75e06814769ec1d14540032"
SOURCE = "trees-2-inc-all-safe.smt2"
SOURCE_SHA = "713e61bb9abe535491e93a36581d1d16f2ba617e454366a1b589d692b0453456"
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
SEED = 20261016
MAX_NEW_TOKENS = 640
REQUIRED = {"%inc", "%inc.0", "%main", "%main.5", "%size", "%size.0", "%sum", "%sum.0"}
PROMPT = """You are given the complete source code of a constrained Horn clause verification problem. Your task is to propose an entirely new, fully typed mathematical interpretation of every declared Bool relation that satisfies ALL original assertions, including the final safety condition. You may introduce new mathematical auxiliary functions as needed; invent their signatures and full recursive definitions yourself.
Output ONLY valid SMT-LIB2 (define-fun ...) or (define-fun-rec ...) definitions, no narrative, no assertions, no snippets of Python. Every declared Bool relation needs a complete interpretation with the exact original name, type and arity. All original source Horn clauses will be checked independently, unchanged. Do not assume an existing helper theorem is given.

Original exact SMT-LIB2 problem:
"""

def top_level(text):
    depth = 0
    start = None
    comment = False
    string = False
    escape = False
    result = []
    for i, char in enumerate(text):
        if char == "\n" and not string:
            comment = False
        if comment:
            continue
        if char == ";" and not string:
            comment = True
            continue
        if char == '"' and not escape:
            string = not string
        if string:
            escape = char == "\\" and not escape
            continue
        if char == "(":
            if depth == 0:
                start = i
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise ValueError("unbalanced source")
            if depth == 0:
                result.append(text[start:i + 1])
    if depth:
        raise ValueError("unbalanced ending")
    return result

def extract_definitions(output):
    defs = [expr for expr in top_level(output) if re.match(r"^\(define-fun(?:-rec)?\s+", expr)]
    names = []
    for expr in defs:
        match = re.match(r"^\(define-fun(?:-rec)?\s+([^\s()]+)", expr)
        if match:
            names.append(match.group(1))
    return defs, names

def proof_scripts(source, witness):
    elements = top_level(source)
    data = [expr for expr in elements if expr.startswith("(declare-datatypes")]
    rules = [expr for expr in elements if expr.startswith("(assert ")]
    if len(data) != 3 or len(rules) != 13:
        raise ValueError("original Horn source is not expected pinned grammar")
    prefix = "(set-logic ALL)\n" + "\n".join(data) + "\n" + witness + "\n"
    for rule in rules:
        yield prefix + "(assert (not " + rule[len("(assert "):-1] + ")\n"

def certify(source, witness):
    import z3
    verdicts, costs = [], []
    for script in proof_scripts(source, witness):
        start = time.perf_counter_ns()
        try:
            solver = z3.Solver()
            solver.set(timeout=4000)
            solver.from_string(script)
            value = str(solver.check())
            verdict = value if value in ("sat", "unsat", "unknown") else "ERROR"
        except (z3.Z3Exception, RuntimeError, ValueError):
            verdict = "ERROR"
        verdicts.append(verdict)
        costs.append(round((time.perf_counter_ns() - start) / 1e6, 3))
        if verdict != "unsat":
            break
    return verdicts, costs

def main():
    start = time.perf_counter_ns()
    result = {
        "experiment": "FGSR_Q3_PRETRAINED_SOURCE_GOAL_ONE_SHOT_OPENED_DEV",
        "status": "NOT_EVALUATED",
        "global_q1_q7": "OPEN",
        "candidate_type": "full_new_typed_helper_and_original_relation_interpretations",
        "neumann_model": False,
        "open_dev_not_blind": True,
        "pretraining_contamination_unknown": True,
        "one_frozen_attempt": True,
        "seed": SEED,
        "model": MODEL_ID,
        "model_revision": None,
        "source_commit": SOURCE_COMMIT,
        "source_sha256": SOURCE_SHA,
        "max_new_tokens": MAX_NEW_TOKENS,
        "resources": {
            "wall_ms": None,
            "money_usd": None,
            "energy_j": None,
            "training_amortization": "UNKNOWN"
        }
    }
    try:
        from huggingface_hub import model_info
        model_rev = model_info(MODEL_ID).sha
        result["model_revision"] = model_rev  # pinned before original text is fetched
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        torch.set_num_threads(2)
        torch.manual_seed(SEED)
        url = f"https://raw.githubusercontent.com/chc-comp/rust-horn/{SOURCE_COMMIT}/{SOURCE}"
        with urllib.request.urlopen(url, timeout=30) as response:
            raw = response.read()
        if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
            raise ValueError("SOURCE_HASH_MISMATCH")
        original = raw.decode("utf-8")
        tok = AutoTokenizer.from_pretrained(MODEL_ID, revision=model_rev)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, revision=model_rev, torch_dtype=torch.float32
        )
        model.eval()
        messages = [{"role": "user", "content": PROMPT + original}]
        chat = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        batch = tok([chat], return_tensors="pt")
        in_tokens = int(batch["input_ids"].shape[-1])
        generation_start = time.perf_counter_ns()
        with torch.inference_mode():
            outputs = model.generate(
                **batch, do_sample=False, max_new_tokens=MAX_NEW_TOKENS,
                pad_token_id=tok.eos_token_id
            )
        out_tokens = int(outputs.shape[-1]) - in_tokens
        model_response = tok.decode(outputs[0, in_tokens:], skip_special_tokens=True)
        result["model_response"] = model_response
        result["measured_inference"] = {
            "prompt_tokens": in_tokens,
            "output_tokens": out_tokens,
            "generate_wall_ms": round((time.perf_counter_ns() - generation_start) / 1e6, 3),
            "cpu_threads": torch.get_num_threads()
        }
        defs, names = extract_definitions(model_response)
        found = set(names)
        result["candidate_structure"] = {
            "defined_original_relations": sorted(found & REQUIRED),
            "missing_relations": sorted(REQUIRED - found),
            "new_helper_names": sorted(found - REQUIRED),
            "total_definitions": len(defs)
        }
        if REQUIRED.issubset(found) and found - REQUIRED and len(names) == len(set(names)):
            verdicts, costs = certify(original, "\n".join(defs))
            result["independent_original_proof"] = verdicts
            result["per_clause_wall_ms"] = costs
            result["status"] = (
                "ORIGINAL_13_OF_13_CERTIFIED_OPENED_PRETRAINED_ONLY"
                if len(verdicts) == 13 and all(x == "unsat" for x in verdicts)
                else "REJECTED_INDEPENDENT_PROOF"
            )
        else:
            result["status"] = "REJECTED_INCOMPLETE_TYPED_DEFINITIONS"
    except Exception as exc:
        result["status"] = "BLOCKED_ENVIRONMENT_OR_MODEL"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)[:900]
    finally:
        result["resources"]["wall_ms"] = round((time.perf_counter_ns() - start) / 1e6, 3)
        out = Path(os.environ.get("FGSR_RESULT", "receipt.json"))
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print("FGSR", result["status"], str(out))

if __name__ == "__main__":
    main()
