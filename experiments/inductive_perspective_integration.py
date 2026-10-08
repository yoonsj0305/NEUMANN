"""Opened engineering integration, NOT a G0/G1 capability or speed benchmark."""
import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.representation_headroom import digest, package_identity, save
from experiments.inductive_fixture_cases import coordinate_fixture, exponential_goal_fixture
from neumann1.inductive_perspective import (HORIZON, check_perspective, compile_acceleration,
    original_execution, projections)
from neumann1.inductive_symbolic_baseline import (discover_polynomial_invariants, from_expressions,
    propose_polynomial_acceleration)

SOURCES = ["neumann1/inductive_perspective.py", "neumann1/inductive_symbolic_baseline.py",
           "experiments/inductive_fixture_cases.py", "neumann1/representation_program.py",
           "experiments/inductive_perspective_integration.py", "experiments/representation_headroom.py"]


def freeze(preparation):
    preparation.mkdir(parents=True, exist_ok=False)
    reg = {"identity": "INDUCTIVE_PERSPECTIVE_ENGINEERING_V1", "kind": "OPENED_ENGINEERING_NOT_G0_G1",
           "fixture_powers": [2, 3], "fixture_goals": ["position", "invariant"],
           "parameter_rows": [[2, 7, 3, 1], [-4, 11, -2, -3], [10**40, -10**60, 9, 0]],
           "original_horizons": [0, 1, 7, 31], "proof_only_large_horizon": 10**30,
           "native_degree": 3, "source_role": "F", "manual_proposal_role": "O",
           "performance_gate": None, "timings_scope": "diagnostic verification/discovery calls only, not complete comparative cost",
           "sources": {p: digest(ROOT / p) for p in SOURCES}, "packages": {p: package_identity(p) for p in ["sympy", "mpmath"]},
           "fresh_eligible": 0, "learned_model": False, "G1_admitted": False}
    save(preparation / "registration.json", reg)
    for p in SOURCES:
        target = preparation / "source" / p
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / p).read_bytes())
    save(preparation / "freeze-receipt.json", {"registration_sha256": digest(preparation / "registration.json")})


def run(preparation, output):
    import sympy as sp
    reg = json.loads((preparation / "registration.json").read_text(encoding="utf-8"))
    assert digest(preparation / "registration.json") == json.loads((preparation / "freeze-receipt.json").read_text())["registration_sha256"]
    assert all(digest(ROOT / p) == pin for p, pin in reg["sources"].items())
    assert all(package_identity(p) == pin for p, pin in reg["packages"].items())
    output.mkdir(parents=True, exist_ok=False)
    (output / "problems").mkdir()
    (output / "offline").mkdir()
    rows, numerical, original_count, large = [], 0, 0, 0
    for power in reg["fixture_powers"]:
        for goal in reg["fixture_goals"]:
            identifier = f"power{power}_{goal}"
            problem, manual = coordinate_fixture(power, goal=goal)
            save(output / "problems" / (identifier + ".json"), problem)
            native = propose_polynomial_acceleration(problem, degree=reg["native_degree"])
            invariants = discover_polynomial_invariants(problem, degree=power)
            assert native["status"] == "CERTIFIED_NATIVE_PROPOSAL"
            # Manual proposals are explicitly offline engineering references.
            routes = {"MANUAL_OFFLINE_REFERENCE": manual, "PUBLIC_SYMBOLIC_GENERATED": native["proposal"]}
            witnesses, proofs = [], {}
            engines = {}
            for route, proposal in routes.items():
                proofs[route] = check_perspective(problem, proposal)
                assert proofs[route]["accepted"]
                engines[route] = compile_acceleration(problem, proposal)
            for params in reg["parameter_rows"]:
                for steps in reg["original_horizons"]:
                    original = original_execution(problem, params, steps)
                    original_count += 1
                    for route, engine in engines.items():
                        actual = engine.run(params, steps)
                        assert actual == original
                        numerical += 1
                        witnesses.append({"route": route, "parameters": params, "steps": steps, "original": list(original), "actual": list(actual)})
                steps = reg["proof_only_large_horizon"]
                a, b, c, k = params
                expected = ((a+k*steps)**power + b-a**power if goal == "position" else b-a**power,)
                for route, engine in engines.items():
                    actual = engine.run(params, steps)
                    assert actual == expected
                    large += 1
                    witnesses.append({"route": route, "parameters": params, "steps": steps, "independent_fixture_formula": list(expected), "actual": list(actual),
                                      "original_loop_replayed": False, "authority": "universal proof plus independent fixture formula"})
            offline = {"manual_reference": manual, "native": native, "invariants": invariants, "proofs": proofs, "witnesses": witnesses}
            save(output / "offline" / (identifier + ".json"), offline)
            rows.append({"id": identifier, "original_state": 3, "manual_latent": len(manual["encoding"]["outputs"]),
                         "native_latent": len(native["proposal"]["encoding"]["outputs"]), "verified_invariant_count": len(invariants["invariants"]),
                         "both_routes_certified": True, "manual_is_learned": False, "native_is_learned": False})
    problem, proposal = coordinate_fixture()
    changed_goal = copy.deepcopy(problem)
    changed_goal["goal"] = projections(problem["parameters"] + problem["state"], ["t"])
    changed_step = copy.deepcopy(problem)
    x, y, t, k, a, b = sp.symbols("x y t k a b")
    changed_step["transition"] = from_expressions(problem["parameters"] + problem["state"], [x+k, y+2*k*x+k*k+1, 3*t+1])
    wrong_closed = copy.deepcopy(proposal)
    n = sp.Symbol(HORIZON)
    wrong_closed["closed_form"] = from_expressions(problem["parameters"] + [HORIZON], [a+k*n+sp.expand(n*(n-1)*(n-2)*(n-3)), b-a*a])
    controls = [{"id": "relevant_goal_changed", "problem": changed_goal, "proposal": proposal, "check": check_perspective(changed_goal, proposal)},
                {"id": "transition_constraint_changed", "problem": changed_step, "proposal": proposal, "check": check_perspective(changed_step, proposal)},
                {"id": "four_unrolled_points_are_not_a_proof", "problem": problem, "proposal": wrong_closed, "check": check_perspective(problem, wrong_closed)}]
    assert all(c["check"]["status"] == "REJECTED" for c in controls)
    exponential = exponential_goal_fixture()
    exponential_result = propose_polynomial_acceleration(exponential)
    assert exponential_result["status"].startswith("ABSTAINED")
    save(output / "controls.json", controls)
    save(output / "outside_grammar.json", {"problem": exponential, "result": exponential_result})
    report = {"identity": reg["identity"], "status": "PASS_ENGINEERING_ONLY", "cases": rows,
              "certified_proposals": 8, "universal_identity_obligations": 40, "original_loops_replayed": original_count,
              "paired_numeric_comparisons": numerical, "large_horizon_formula_checks": large, "false_proposals_rejected": 3,
              "outside_grammar_abstentions": 1, "learned_perspective_policy": False, "headroom_measured": False,
              "G0_passed": False, "G1_admitted": False, "fresh_eligible": 0, "registration_sha256": digest(preparation / "registration.json")}
    save(output / "report.json", report)
    save(output / "manifest.json", {str(p.relative_to(output)): digest(p) for p in output.rglob("*") if p.is_file() and p.name != "manifest.json"})
    save(preparation / "first-result-receipt.json", {"report_sha256": digest(output / "report.json"), "manifest_sha256": digest(output / "manifest.json")})
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["freeze", "run"])
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    freeze(args.preparation) if args.mode == "freeze" else run(args.preparation, args.output)
