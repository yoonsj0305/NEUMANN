"""NEUMANN 1 P1.7: small operator-view contrastive pilot, frozen first-run only.

This is *NOT* JEPA, PRH-theorem replication, or NEUMANN autonomous operator
invention. Both encoders share architecture, initialization and optimization.
The only intervention is whether positives depict separate operator executions
or two corruptions of a single execution. Original query labels withheld until
scoring. Do not change seeds/thresholds after this run.
"""
from __future__ import annotations
import json
import os
import platform
import resource
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

CONTRACT = {
    "schema": "neumann.q3.operator-good-views.p17.v1",
    "global_q1_q7": "OPEN",
    "program_semantics": "eight human-defined grid transforms; six in training",
    "shape": [12, 12],
    "foreground_probability": 0.18,
    "train_seed": 20261117,
    "support_seed": 20261118,
    "query_seed": 20261119,
    "weights_seed": 20261120,
    "torch_batch_seed": 20261121,
    "training_operators": ["up", "down", "left", "right", "flip_h", "flip_v"],
    "unseen_operators": ["rot90", "rot270"],
    "minibatches": 400,
    "training_pair_size": 6,
    "support_per_operator": 24,
    "query_per_operator": 48,
    "embedding_dim": 48,
    "lr": 0.002,
    "temperature": 0.12,
    "bad_view_flip_probability": 0.025,
    "local_gate": {"good_top1_min": 0.80, "good_minus_bad_min": 0.15, "unseen_top1_min": 0.50},
    "full_cost_gate": "NOT_RUN",
    "JEPA": "NOT_RUN",
}
ALL_OPS = CONTRACT["training_operators"] + CONTRACT["unseen_operators"]
H = W = 12


def execute(x: np.ndarray, op: str) -> np.ndarray:
    y = np.zeros_like(x)
    if op == "up": y[:-1, :] = x[1:, :]
    elif op == "down": y[1:, :] = x[:-1, :]
    elif op == "left": y[:, :-1] = x[:, 1:]
    elif op == "right": y[:, 1:] = x[:, :-1]
    elif op == "flip_h": y = x[:, ::-1].copy()
    elif op == "flip_v": y = x[::-1, :].copy()
    elif op == "rot90": y = np.rot90(x, 1).copy()
    elif op == "rot270": y = np.rot90(x, 3).copy()
    else: raise ValueError("unknown operator")
    return y


def scene(rng: np.random.Generator) -> np.ndarray:
    return (rng.random((H, W)) < CONTRACT["foreground_probability"]).astype(np.float32)


def one_view(rng: np.random.Generator, op: str) -> np.ndarray:
    x = scene(rng)
    return np.stack((x, execute(x, op)), axis=0)


def pair_batch(rng: np.random.Generator, mode: str):
    a = np.zeros((6, 2, H, W), dtype=np.float32)
    b = np.zeros_like(a)
    for i, op in enumerate(CONTRACT["training_operators"]):
        sample = one_view(rng, op)
        if mode == "good":
            a[i] = sample
            b[i] = one_view(rng, op)
        else:
            # Deliberately weak correlated positive: one observed execution
            # corrupted twice, rather than independent executions.
            flip_a = rng.random(sample.shape) < CONTRACT["bad_view_flip_probability"]
            flip_b = rng.random(sample.shape) < CONTRACT["bad_view_flip_probability"]
            a[i] = np.where(flip_a, 1.0 - sample, sample)
            b[i] = np.where(flip_b, 1.0 - sample, sample)
    return torch.from_numpy(a), torch.from_numpy(b)


class Encoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(2, 24, 3, padding=1), nn.GELU(),
            nn.Conv2d(24, 32, 3, padding=1), nn.GELU(),
            nn.MaxPool2d(2), nn.Flatten(),
            nn.Linear(32 * 6 * 6, 96), nn.GELU(),
            nn.Linear(96, CONTRACT["embedding_dim"]),
        )

    def forward(self, x):
        return F.normalize(self.net(x), dim=-1)


def train_arm(mode: str, initial: dict, fixed_batches: list):
    model = Encoder()
    model.load_state_dict(initial)
    opt = torch.optim.AdamW(model.parameters(), lr=CONTRACT["lr"])
    start = time.perf_counter_ns()
    final_loss = None
    model.train()
    for a, b in fixed_batches:
        # Batches frozen before either model is fitted.
        aa, bb = a[mode], b[mode]
        embeddings_a, embeddings_b = model(aa), model(bb)
        sim = embeddings_a @ embeddings_b.T / CONTRACT["temperature"]
        labels = torch.arange(len(embeddings_a))
        loss = 0.5 * (F.cross_entropy(sim, labels) + F.cross_entropy(sim.T, labels))
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        final_loss = float(loss.detach())
    train_ns = time.perf_counter_ns() - start
    model.eval()
    return model, {"training_ns": train_ns, "final_loss": final_loss,
                   "parameter_count": sum(p.numel() for p in model.parameters())}


def make_split(seed: int, n: int):
    rng = np.random.default_rng(seed)
    examples, labels = [], []
    for i, op in enumerate(ALL_OPS):
        for _ in range(n):
            examples.append(one_view(rng, op))
            labels.append(i)
    return torch.from_numpy(np.stack(examples)), np.asarray(labels, dtype=np.int64)


def evaluate(model: Encoder, support, query, support_labels, query_labels):
    started = time.perf_counter_ns()
    with torch.no_grad():
        support_emb = model(support)
        query_emb = model(query)
        prototypes = F.normalize(torch.stack([support_emb[support_labels == i].mean(axis=0)
                                              for i in range(len(ALL_OPS))]), dim=1)
        logits = query_emb @ prototypes.T
        predicted = logits.argmax(axis=1).cpu().numpy()
    inference_ns = time.perf_counter_ns() - started
    confusion = np.zeros((len(ALL_OPS), len(ALL_OPS)), dtype=np.int64)
    for gold, pred in zip(query_labels, predicted): confusion[gold, pred] += 1
    ok = predicted == query_labels
    return {
        "top1": float(ok.mean()),
        "seen_top1": float(ok[query_labels < 6].mean()),
        "unseen_top1": float(ok[query_labels >= 6].mean()),
        "query_count": len(query_labels),
        "correct": int(ok.sum()),
        "confusion": confusion.tolist(),
        "prototype_inference_ns": inference_ns,
        "query_amortized_ns_per_item": inference_ns / len(query_labels),
    }


def symbolic_exact(query, labels):
    matches, correct, rejected = 0, 0, 0
    started = time.perf_counter_ns()
    for sample, gold in zip(query, labels):
        x = sample[0].numpy()
        y = sample[1].numpy()
        matching = [i for i, op in enumerate(ALL_OPS) if np.array_equal(execute(x, op), y)]
        matches += len(ALL_OPS)
        if len(matching) != 1:
            rejected += 1
        elif matching[0] == gold:
            correct += 1
    elapsed = time.perf_counter_ns() - started
    return {"correct": correct, "abstain": rejected, "queries": len(labels),
            "program_executions": matches, "time_ns": elapsed,
            "exact_task_accuracy": correct / len(labels)}


def run():
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(CONTRACT["weights_seed"])
    initial = Encoder().state_dict()
    # Both arms receive equal number of training batches with the same frozen
    # sequence of operator labels. The intervention is positive pair formation.
    rng_good = np.random.default_rng(CONTRACT["train_seed"])
    rng_bad = np.random.default_rng(CONTRACT["train_seed"])
    batches = []
    for _ in range(CONTRACT["minibatches"]):
        g1, g2 = pair_batch(rng_good, "good")
        b1, b2 = pair_batch(rng_bad, "bad")
        batches.append(({"good": g1, "bad": b1}, {"good": g2, "bad": b2}))
    support, s_labels = make_split(CONTRACT["support_seed"], CONTRACT["support_per_operator"])
    query, q_labels = make_split(CONTRACT["query_seed"], CONTRACT["query_per_operator"])
    good_net, good_train = train_arm("good", initial, batches)
    bad_net, bad_train = train_arm("bad", initial, batches)
    untrained = Encoder(); untrained.load_state_dict(initial); untrained.eval()
    results = {
        "contract": CONTRACT,
        "synthetic_only": True,
        "public_arc_original_task_score": "NOT_RUN",
        "good_train": good_train,
        "bad_train": bad_train,
        "good": evaluate(good_net, support, query, s_labels, q_labels),
        "bad": evaluate(bad_net, support, query, s_labels, q_labels),
        "untrained": evaluate(untrained, support, query, s_labels, q_labels),
        "strong_symbolic_direct": symbolic_exact(query, q_labels),
        "environment": {"python": platform.python_version(), "torch": torch.__version__,
                        "numpy": np.__version__, "cpu_threads": torch.get_num_threads(),
                        "peak_rss_kib_process": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
        "complete_system_cost": {"energy_joule": None, "flops": None,
                                 "monetary_usd": None, "teacher_cost": None},
        "global_q1_q7": "OPEN",
    }
    g, b, gate = results["good"], results["bad"], CONTRACT["local_gate"]
    results["local_view_gate"] = ("PASS_OPERATOR_VIEW_ABLATION" if
                                  g["top1"] >= gate["good_top1_min"] and
                                  g["top1"] - b["top1"] >= gate["good_minus_bad_min"] and
                                  g["unseen_top1"] >= gate["unseen_top1_min"]
                                  else "FAIL_OPERATOR_VIEW_ABLATION")
    return results


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    result = run()
    with args.out.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    for arm in ("good", "bad", "untrained", "strong_symbolic_direct"):
        print(arm, {k: v for k, v in result[arm].items() if k not in ("confusion",)})
    print("local gate:", result["local_view_gate"])

if __name__ == "__main__":
    main()
