"""Post-primary generation replay, with TRAIN only and no new score claim."""
from __future__ import annotations
import json
import multiprocessing as mp
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/q6"))
from source_study import OUT, worker
from neumann1.q6.transport import tup


def main():
    path = OUT / "witness_generation_replay.json"
    if path.exists():
        raise SystemExit("preserve first generation replay")
    primary = json.loads((OUT / "result.json").read_text())
    cases = {t["id"]: t for t in json.loads((ROOT.parent / "q6_source_v1_train_cache.json").read_text())}
    records = []
    ctx = mp.get_context("spawn")
    for tid in primary["compound_attributed_exclusive"]:
        task = cases[tid]
        task["train"] = [(tup(i), tup(o)) for i, o in task["train"]]
        task["test"] = ()
        original = next(r for r in primary["grades"] if r["id"] == tid and r["arm"] == "C")
        for arm in ("C", "C-no-map"):
            q = ctx.Queue()
            p = ctx.Process(target=worker, args=((task, arm), q))
            p.start()
            try:
                r = q.get(timeout=30)
            finally:
                p.join(timeout=2)
                if p.is_alive():
                    p.terminate()
                    p.join()
            records.append({"id": tid, "arm": arm, "via": r.get("via"), "program": r.get("program"),
                            "generation_reproduced_exact_AST": tup(r.get("sol")) == tup(original.get("sol")) if arm == "C" else None,
                            "no_map_still_UNKNOWN": r.get("sol") is None if arm == "C-no-map" else None,
                            "worker_total_cpu_seconds": r.get("worker_total_cpu_seconds"),
                            "receiver_TEST_read": False})
            q.close()
    path.write_text(json.dumps({"scope": "post-primary TRAIN-only generation replay; original outcomes unchanged", "records": records}, indent=2) + "\n")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
