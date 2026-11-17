"""Development data only: the SOURCE splits of the FIRST registry (rule_source, oeis_source).

No TARGET path and no reserve path can be reached through this module.
"""
from __future__ import annotations
import pathlib, sys
sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
import invention_first as first


def load(bigbench, oeis):
    reg, _ = first.load_registry()
    out = {}
    for fam, clone, key, blobs, loader in (("rule", bigbench, "rule_source", "rule_blobs", first.load_rule),
                                           ("oeis", oeis, "oeis_source", "oeis_blobs", first.load_oeis)):
        tasks = []
        for p in reg["splits"][key]:
            raw = (pathlib.Path(clone) / p).read_bytes()
            if first.blob_sha(raw) != reg[blobs][p]:
                raise SystemExit("SOURCE_BLOB_MISMATCH " + p)
            t = loader(p, raw)
            if "unsupported" not in t:
                tasks.append(t)
        out[fam] = tasks
    return out
