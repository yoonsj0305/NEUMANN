"""Bounded v0.0.81 integration smoke.  This is not a timing audit."""
import json

from neumann1.lp_certificate_v081 import (
    contract_fixture,
    highs_candidate,
    verify_standard_form_certificate,
)


def main():
    case = contract_fixture(seed=8101, rows=8, cols=64)
    known = verify_standard_form_certificate(
        case["A"], case["b"], case["c"], case["known_x"], case["known_y"]
    )
    candidate = highs_candidate(case["A"], case["b"], case["c"])
    if not known["accepted"] or not candidate["solver_success"]:
        raise SystemExit("certificate integration failed")
    if not candidate["certificate"]["accepted"]:
        raise SystemExit("HiGHS candidate failed original-certificate verification")
    print(json.dumps({
        "experiment": "v0.0.81 LP certificate interface smoke",
        "decision": "INTERFACE_READY_PERFORMANCE_UNTESTED",
        "known_certificate_accepted": known["accepted"],
        "highs_certificate_accepted": candidate["certificate"]["accepted"],
        "rows": known["rows"],
        "cols": known["cols"],
        "nnz": known["nnz"],
        "q3": "OPEN",
        "q4": "OPEN",
    }, indent=2))


if __name__ == "__main__":
    main()
