"""Native procedure reuse across changed connectivity, with public cost guards.

An operand-join program can remain mathematically valid when its index network
changes. Same-arity prior paths must get this chance in the strong comparator.
This is known procedure reuse, not learned/new representation discovery.
"""
import json
from time import perf_counter
from neumann1.contraction_structure import certify_path, validate_public


class PreparedPublicPriors:
    """Pay historical sorting/certification once as engine investment."""
    def __init__(self, records):
        self.by_arity = {}
        for record in records:
            if record.get("oracle_used") is not False or record.get("learned") is not False:
                raise ValueError("Native public priors only")
            check = certify_path(record["public"], record["path"])
            owned = json.loads(json.dumps(record))
            self.by_arity.setdefault(len(record["public"]["shapes"]), []).append((check["dense_arithmetic_work_model"], owned))
        self.by_arity = {n: tuple(row[1] for row in sorted(rows, key=lambda row: row[0])) for n, rows in self.by_arity.items()}


def propose(public, records, strategy, *, max_work, max_elements):
    validate_public(public)
    if strategy not in {"FIRST", "BEST_MODEL"}:
        raise ValueError("Explicit prior selection strategy required")
    begin = perf_counter()
    prepared = records if isinstance(records, PreparedPublicPriors) else PreparedPublicPriors(records)
    prior = prepared.by_arity.get(len(public["shapes"]), ())
    if strategy == "FIRST":
        prior = prior[:1]
    choices = []
    for r in prior:
        check = certify_path(public, r["path"])
        if check["dense_arithmetic_work_model"] <= max_work and check["largest_intermediate_elements"] <= max_elements:
            choices.append((check["dense_arithmetic_work_model"], check["largest_intermediate_elements"], r, check))
    if not choices:
        return {"status": "NO_ELIGIBLE_PUBLIC_PRIOR", "examined": len(prior),
                "lookup_certificate_seconds": perf_counter() - begin}
    _, _, selected, check = min(choices, key=lambda row: row[:2])
    return {"status": "CERTIFIED_PUBLIC_PRIOR", "path": json.loads(json.dumps(selected["path"])),
            "certificate": check, "examined": len(prior), "oracle_used": False, "learned": False,
            "global_optimum_proven": False, "lookup_certificate_seconds": perf_counter() - begin}
