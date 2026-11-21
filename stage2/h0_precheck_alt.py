"""H-0 record only (not a pipeline change, not used for any decision): the pre-check ratio with the all-"stay" reference
shifted onto the first operand token.

With BOS, the all-"stay" table's heads sit on BOS (position 0); BOS is the only symbol of its token kind, so its
content-substitution dependency is 0 by definition (stage1/c3_compile.extract_substitution), score(all stay) = 0 and
the unchanged gate score(correct) >= 2 x score(all stay) always passes (ratio recorded as null).  Without BOS (G-0,
G-0') the all-"stay" heads sat on the first prompt token, which is position 1 with BOS.  This script recomputes, from
each H-0 compile's local dependency_rows.pt and with stage1/c3_compile.dense / table_score, the score of heads that
stay on position 1, and the ratio score(correct) / that score -- the G-0 reading of the pre-check on the same rows.

  python stage2/h0_precheck_alt.py        # writes stage2/results/h0/precheck_alt.json
"""
from __future__ import annotations
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import h_adapter as A          # noqa: E402


def main():
    A.install()
    import numpy as np
    import torch
    import c3_compile as CC
    res = {}
    for d in sorted((HERE / "results" / "h0").glob("*_compile_s*")):
        cr_p, rows_p = d / "compile_result.json", d / "dependency_rows.pt"
        if not (cr_p.exists() and rows_p.exists()):
            continue
        cr = json.loads(cr_p.read_text())
        rows = torch.load(rows_p, weights_only=False)["rows"]
        S = CC.dense(rows, 2)
        ar = np.arange(S.shape[0])
        pos1 = np.ones(S.shape[0], dtype=int)
        s1 = CC.table_score(S, [pos1])[0]
        c = cr["precheck"]["dependency"]["correct"]
        res[d.name] = {"correct": c, "all_stay_on_bos": cr["precheck"]["dependency"]["all_stay"],
                       "stay_on_position_1": s1, "ratio_vs_position_1": c / s1 if s1 > 0 else None,
                       "would_pass_g0_reading": c >= 2 * s1, "output_steps": int(len(ar))}
    p = HERE / "results" / "h0" / "precheck_alt.json"
    p.write_text(json.dumps(res, indent=1))
    for k, v in res.items():
        print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items()})


if __name__ == "__main__":
    main()
