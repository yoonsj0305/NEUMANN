"""Bounded v0.0.82 integration smoke. No admission or timing claim."""
import json

from neumann1.lp_basis_headroom_v082 import (
    DIRECT_METHODS,
    direct_once,
    generate_case,
    oracle_basis_once,
    specifications,
)


def main():
    spec = next(
        s for s in specifications()
        if s["rows"] == 32
        and s["condition_number"] == 1
        and s["width_factor"] == 16
        and s["replicate"] == 0
    )
    case = generate_case(spec)
    direct = {method: direct_once(case, method) for method in DIRECT_METHODS}
    oracle = oracle_basis_once(case, case["oracle_basis"])
    if not oracle["accepted"]:
        raise SystemExit(f"oracle certificate failed: {oracle}")
    if not any(result["accepted"] for result in direct.values()):
        raise SystemExit(f"no Direct method reached verified capability: {direct}")
    print(json.dumps({
        "experiment": "v0.0.82 integration smoke",
        "case_id": spec["id"],
        "verified_direct_methods": [
            method for method, result in direct.items() if result["accepted"]
        ],
        "oracle_verified": oracle["accepted"],
        "decision": "SMOKE_ONLY_NO_HEADROOM_CLAIM",
        "q3": "OPEN",
        "q4": "OPEN",
    }, indent=2))


if __name__ == "__main__":
    main()
