"""Screen resource budgets before fitting or GPU runs; never certify capability.

All costs in one envelope use the same additive resource unit and workload.
Floors are assumptions for a specified implementation, not universal bounds.
Unknown costs block screening. A positive budget only warrants measurement.
"""
from __future__ import annotations

import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


COMPONENTS = ("parse", "reduce", "execute", "reconstruct", "verify", "transport")


def number(value, name: str, *, positive: bool = False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{name}: expected a finite nonnegative cost")
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError(f"{name}: invalid number") from error
    if not result.is_finite() or result < 0 or (positive and result == 0):
        raise ValueError(f"{name}: invalid range")
    return result


def screen(envelope: dict) -> dict:
    """Charge both sides' investments and candidate failed-path/fallback work.

    Baseline qualification is an externally verified claim, not established
    here. Each baseline must have a receipt and meet the SAME capability floor.
    Choose its cheapest complete cost at each PREDECLARED reuse count.
    discovery_budget = baseline/S - investment/N - fixed - failed - fallback.
    """
    axis = envelope["resource_axis"]
    if not isinstance(axis, str) or not axis.strip():
        raise ValueError("resource_axis must name one additive measured unit")
    target = number(envelope["target_multiplier"], "target", positive=True)
    if target <= 1:
        raise ValueError("target must exceed one")
    counts = envelope["reuse_counts"]
    if not counts or any(type(n) is not int or n < 1 for n in counts):
        raise ValueError("reuse_counts must contain positive integers")
    baselines = []
    for baseline in envelope["baselines"]:
        if baseline.get("qualified") is not True:
            continue
        if not baseline.get("receipt"):
            raise ValueError("qualified baseline requires a capability/cost receipt")
        baselines.append((baseline["id"],
                          number(baseline["investment"], "baseline investment"),
                          number(baseline["per_item"], "baseline per_item", positive=True)))
    rows = []
    for candidate in envelope["candidates"]:
        for count in counts:
            row = {"candidate": candidate["id"], "reuse_count": count}
            if not baselines:
                rows.append({**row, "status": "NEEDS_QUALIFIED_BASELINE"})
                continue
            fixed = candidate.get("fixed_floor", {})
            required = [candidate.get("investment"), candidate.get("failed_path_floor"),
                        candidate.get("fallback_rate"), candidate.get("fallback_cost"),
                        *[fixed.get(component) for component in COMPONENTS]]
            if any(value is None for value in required) or not candidate.get("floor_receipt"):
                rows.append({**row, "status": "NEEDS_COST_FLOORS"})
                continue
            rate = number(candidate["fallback_rate"], "fallback_rate")
            if rate > 1:
                raise ValueError("fallback_rate must be <= 1")
            fixed_cost = sum((number(fixed[key], key) for key in COMPONENTS), Decimal(0))
            investment = number(candidate["investment"], "candidate investment")
            failed = number(candidate["failed_path_floor"], "failed_path_floor")
            fallback = rate * number(candidate["fallback_cost"], "fallback_cost")
            baseline_id, baseline_cost = min(
                ((name, upfront / count + hot) for name, upfront, hot in baselines),
                key=lambda pair: pair[1])
            floor = investment / count + fixed_cost + failed + fallback
            budget = baseline_cost / target - floor
            # Equality leaves no room for discovery: measure it instead of rejecting.
            status = ("BUDGET_INFEASIBLE_UNDER_DECLARED_FLOORS" if budget < 0
                      else "HEADROOM_ONLY_REQUIRES_CAPABILITY_AND_DISCOVERY_TEST")
            discovery = candidate.get("discovery_cost")
            measured_exceeds = (None if discovery is None else
                                number(discovery, "discovery_cost") > budget)
            rows.append({**row, "status": status, "baseline": baseline_id,
                         "baseline_complete_per_item": str(baseline_cost),
                         "candidate_floor_per_item": str(floor),
                         "discovery_budget_per_item": str(budget),
                         "measured_discovery_exceeds_budget": measured_exceeds})
    return {"resource_axis": axis, "target_multiplier": str(target),
            "scope": "declared cost envelope only; no optimality or capability verdict",
            "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("envelope", type=Path)
    args = parser.parse_args()
    print(json.dumps(screen(json.loads(args.envelope.read_text(encoding="utf-8"))),
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
