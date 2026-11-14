"""Rebuild the final frozen generator in a NEW directory; no benchmark input.

OPENBLAS_NUM_THREADS=1 python research/q3/semantic_generator_train.py --out /tmp/new-replay
This reproduces model/corpus content, not historical CPU telemetry or gzip timestamps.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from neumann1 import semantic_program_generator as gen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit("refuse to overwrite frozen training or experiment evidence")
    out.mkdir(parents=True, exist_ok=True)
    start = time.process_time()
    tasks, receipt = gen.selfplay(n=3500, seed=917, max_tries=150000,
                                  log=lambda r: print(json.dumps(r), flush=True))
    raw = json.dumps(tasks, separators=(",", ":")).encode()
    with (out / "selfplay.json.gz").open("wb") as f:
        with gzip.GzipFile(fileobj=f, mode="wb", mtime=0) as z:
            z.write(raw)
    model = gen.SemanticProgramGenerator(hidden=128, seed=9127)
    receipt["training"] = model.fit(tasks[:-64], epochs=64, batch=512, seed=31)
    model.save(out / "model.npz")
    receipt.update({"train_tasks": len(tasks) - 64, "heldout_tasks": 64,
                    "decoded_corpus_sha256": hashlib.sha256(raw).hexdigest(),
                    "model_sha256": hashlib.sha256((out / "model.npz").read_bytes()).hexdigest(),
                    "total_cpu_seconds": time.process_time() - start})
    (out / "training.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
