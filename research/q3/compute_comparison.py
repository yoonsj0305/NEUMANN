"""Same 125 TARGET list functions: NEUMANN invention-core arms vs published BIG-bench LMs.

Read-only post-hoc report (not a pre-registered test). Inputs:
  * docs/experiments/results/invention_first_result.json   (NEUMANN, frozen FIRST run)
  * docs/experiments/results/invention_core_frozen.json     (SOURCE investment)
  * BIG-bench pinned commit: list_functions/results/scores_*.json (blob SHA-1 checked)
    and the TARGET task.json files (blob SHA-1 checked; only character counts are used,
    no task content is written anywhere).

python research/q3/compute_comparison.py <bigbench_clone> <dir_with_scores_json>

Compute units (stated, not hidden):
  * LM inference  >= 2 * N_params * T_prompt FLOPs per query (dense forward pass lower bound;
    T_prompt estimated as characters / 4 of the k demonstrations + query, which UNDER-counts
    digit-list tokens, i.e. favours the LMs).
  * LM training   = 6 * N * D with D = published training tokens (PaLM 780e9, GPT-3 300e9);
    BIG-G tokens not used (not stated in the score files) -> reported as None.
  * NEUMANN       = measured CPU seconds of the pure-Python search, converted with an
    UPPER bound of 1e10 primitive machine operations per CPU second (a 3-4 GHz core
    retires < 1e10 instructions/s), i.e. favours the LMs again.
Protocol differences (disclosed): LMs saw <= 5 (PaLM) / <= 3 (GPT-3, BIG-G) demonstrations,
NEUMANN saw 8; an LM is scored per query, NEUMANN per task (single program must reproduce
ALL hidden examples). "LM perfect" = exact_str_match 1.0 on every scored query of the task.
"""
from __future__ import annotations
import hashlib, json, pathlib, sys
sys.path.insert(0, ".")

PIN = "092b196c1f8f14a54bbc62f24759d43bde46dd3b"
RESULT = "docs/experiments/results/invention_first_result.json"
FROZEN = "docs/experiments/results/invention_core_frozen.json"
REGISTRY = "docs/experiments/invention_first_registry.json"
OUT = "docs/experiments/results/compute_comparison_list_functions.json"
OPS_PER_CPU_S = 1e10
SCORE_BLOBS = {  # git blob SHA-1 at PIN, bigbench/benchmark_tasks/list_functions/results/
    "scores_PaLM_535b.json": "06ca9f4b131370bd825444a5eb97f8c5b3afb20d",
    "scores_PaLM_64b.json": "7b035b07a4e671cacbb8279f1cb9900e164ca6ed",
    "scores_PaLM_8b.json": "e2ccda1216f7511705d9ec6e11b703d97464e0b4",
    "scores_GPT_GPT-3-200B.json": "2e107772157a18be9bc280e932b3e3f0c8bb0399",
    "scores_GPT_GPT-3-13B.json": "19caf31ffc5973f4d3441267289bb2a6a0cb2f0b",
    "scores_BIG-G_128b_T=0.json": "bc7c6e6e8fd179e478fab4abbf0d2bcce623e2ac",
    "scores_BIG-G_8b_T=0.json": "0544d485470905d919025f864d401970027e018d",
    "scores_BIG-G_1b_T=0.json": "fbe81127302dde3cc76f3a0d03e81a1a49f22c47",
}
TRAIN_TOKENS = {"PaLM": 780e9, "GPT": 300e9}


def blob_sha(b):
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def main(bigbench, scores_dir):
    reg = json.loads(pathlib.Path(REGISTRY).read_text())
    res = json.loads(pathlib.Path(RESULT).read_text())
    frozen = json.loads(pathlib.Path(FROZEN).read_text())
    target = reg["splits"]["rule_target"]
    ids = [p.split("/")[-2] for p in target]
    # prompt size per task from the real examples (characters only)
    chars = {}
    for p in target:
        raw = (pathlib.Path(bigbench) / p).read_bytes()
        if blob_sha(raw) != reg["rule_blobs"][p]:
            raise SystemExit("TASK_BLOB_MISMATCH " + p)
        ex = json.loads(raw)["examples"]
        chars[p.split("/")[-2]] = [len("Input: %s\nOutput: %s\n" % (e["input"], e["target"]))
                                   for e in ex]
    rows = res["families"]["rule"]["rows"]
    out = {"schema": "neumann.compute-comparison.list-functions.v1", "pin": PIN,
           "target_tasks": len(ids), "neumann": {}, "lms": {},
           "assumptions": {"ops_per_cpu_second_upper_bound": OPS_PER_CPU_S,
                           "lm_tokens_per_char": 0.25, "train_tokens": TRAIN_TOKENS}}
    src_cpu = frozen["train_wall_s"] * 4
    for arm in ("A", "A4", "B", "C"):
        rs = [rows["rule/" + i][arm] for i in ids if arm in rows["rule/" + i]]
        cpu = sum(r["seconds"] for r in rs)
        out["neumann"][arm] = {
            "solved_tasks": sum(r["solved"] for r in rs),
            "candidates": sum(r["candidates"] for r in rs),
            "cpu_seconds": round(cpu, 1),
            "ops_upper_bound_total": cpu * OPS_PER_CPU_S,
            "ops_upper_bound_per_task": cpu * OPS_PER_CPU_S / len(ids)}
    out["neumann"]["C"]["source_investment_cpu_seconds_upper"] = round(src_cpu, 1)
    out["neumann"]["C"]["source_investment_ops_upper"] = src_cpu * OPS_PER_CPU_S
    c_solved = {i for i in ids if rows["rule/" + i].get("C", {}).get("solved")}
    for fname, want in SCORE_BLOBS.items():
        local = pathlib.Path(scores_dir) / fname.replace("scores_", "")
        raw = local.read_bytes()
        if blob_sha(raw) != want:
            raise SystemExit("SCORE_BLOB_MISMATCH " + fname)
        d = json.loads(raw)
        n = d["model"]["total_params"]
        fam = d["model"]["model_family"].split()[0]
        best = {}
        for s in d["scores"]:
            sd = s["subtask_description"]
            if ":" not in sd:
                continue
            tid = sd.split(":")[1]
            if tid in ids and "exact_str_match" in s["score_dict"]:
                k = s["number_of_shots"]
                if tid not in best or k > best[tid][0]:
                    best[tid] = (k, s["score_dict"]["exact_str_match"])
        shots = max(k for k, _ in best.values())
        acc = [best[i][1] for i in ids if i in best]
        perfect = {i for i in ids if i in best and best[i][1] >= 1 - 1e-9}
        tokens = [sum(chars[i][:best[i][0] + 1]) / 4 for i in ids if i in best]
        flops_q = [2 * n * t for t in tokens]
        train = 6 * n * TRAIN_TOKENS[fam] if fam in TRAIN_TOKENS else None
        out["lms"][fname[7:-5]] = {
            "params": n, "shots": shots, "tasks_scored": len(acc),
            "mean_exact_str_match": round(sum(acc) / len(acc), 4),
            "tasks_perfect": len(perfect),
            "perfect_and_C_solved": len(perfect & c_solved),
            "perfect_not_C": len(perfect - c_solved),
            "C_not_perfect": len(c_solved - perfect),
            "inference_flops_per_query_lower_bound_mean": sum(flops_q) / len(flops_q),
            "training_flops_6ND": train}
    c = out["neumann"]["C"]
    for m, v in out["lms"].items():
        v["inference_per_query_over_C_per_task"] = (
            v["inference_flops_per_query_lower_bound_mean"] / c["ops_upper_bound_per_task"])
        if v["training_flops_6ND"]:
            v["training_over_C_source"] = v["training_flops_6ND"] / c["source_investment_ops_upper"]
    pathlib.Path(OUT).write_text(json.dumps(out, indent=1, sort_keys=True))
    print("NEUMANN:", json.dumps(out["neumann"], indent=1))
    print("| model | params | shots | mean exact | perfect tasks | inf FLOPs/query (lb) | x C ops/task (ub) | train FLOPs | x C SOURCE |")
    for m, v in sorted(out["lms"].items(), key=lambda kv: -kv[1]["params"]):
        print("| %s | %.3g | %d | %.3f | %d | %.2g | %.2g | %s | %s |" % (
            m, v["params"], v["shots"], v["mean_exact_str_match"], v["tasks_perfect"],
            v["inference_flops_per_query_lower_bound_mean"], v["inference_per_query_over_C_per_task"],
            "%.2g" % v["training_flops_6ND"] if v["training_flops_6ND"] else "-",
            "%.2g" % v["training_over_C_source"] if v.get("training_over_C_source") else "-"))


if __name__ == "__main__":
    main(*sys.argv[1:3])
