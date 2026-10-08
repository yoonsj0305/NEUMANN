"""Independent DAG interpretation and SymPy induction audit of engineering data."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.representation_headroom import digest, package_identity, save
from neumann1.representation_program import validate


def symbolic(program):
    import sympy as sp
    validate(program)
    values = []
    for node in program["nodes"]:
        if node[0] == "input":
            value = sp.Symbol(node[1])
        elif node[0] == "const":
            value = sp.Integer(node[1])
        elif node[0] == "add":
            value = values[node[1]] + values[node[2]]
        else:
            value = values[node[1]] * values[node[2]]
        values.append(value)
    return [values[i] for i in program["outputs"]]


def interpret(program, row):
    mapping, values = dict(zip(program["inputs"], row)), []
    for node in program["nodes"]:
        if node[0] == "input":
            value = mapping[node[1]]
        elif node[0] == "const":
            value = node[1]
        elif node[0] == "add":
            value = values[node[1]] + values[node[2]]
        else:
            value = values[node[1]] * values[node[2]]
        values.append(value)
    return [values[i] for i in program["outputs"]]


def independently_check(problem, proposal):
    import sympy as sp
    parameters, state = problem["parameters"], problem["state"]
    phi = symbolic(proposal["encoding"])
    initial, transition, goal = [symbolic(problem[k]) for k in ["initial", "transition", "goal"]]
    latent = [sp.Symbol(f"__z{i}") for i in range(len(phi))]
    n = sp.Symbol("__steps")
    latent_initial, latent_transition, closed, decode = [symbolic(proposal[k]) for k in ["initial", "transition", "closed_form", "decode"]]
    state_symbols = [sp.Symbol(s) for s in state]
    identities = [("ENCODE_INITIAL", [e.subs(dict(zip(state_symbols, initial)), simultaneous=True) for e in phi], latent_initial),
                  ("TRANSITION_COMMUTES", [e.subs(dict(zip(state_symbols, transition)), simultaneous=True) for e in phi],
                   [e.subs(dict(zip(latent, phi)), simultaneous=True) for e in latent_transition]),
                  ("ORIGINAL_GOAL_SUFFICIENT", goal, [e.subs(dict(zip(latent, phi)), simultaneous=True) for e in decode]),
                  ("CLOSED_BASE", [e.subs(n, 0) for e in closed], latent_initial),
                  ("CLOSED_STEP", [e.subs(n, n+1) for e in closed], [e.subs(dict(zip(latent, closed)), simultaneous=True) for e in latent_transition])]
    return {name: len(left) == len(right) and all(sp.expand(a-b) == 0 for a, b in zip(left, right)) for name, left, right in identities}


def main(preparation, first, output):
    reg = json.loads((preparation / "registration.json").read_text(encoding="utf-8"))
    receipt = json.loads((preparation / "first-result-receipt.json").read_text(encoding="utf-8"))
    assert digest(first / "report.json") == receipt["report_sha256"] and digest(first / "manifest.json") == receipt["manifest_sha256"]
    assert digest(preparation / "registration.json") == json.loads((preparation / "freeze-receipt.json").read_text())["registration_sha256"]
    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert all(digest(first / path) == pin for path, pin in manifest.items())
    assert all(digest(ROOT / path) == pin and digest(preparation / "source" / path) == pin for path, pin in reg["sources"].items())
    assert all(package_identity(p) == pin for p, pin in reg["packages"].items())
    report = json.loads((first / "report.json").read_text(encoding="utf-8"))
    proofs, comparisons, large, original = 0, 0, 0, 0
    for summary in report["cases"]:
        problem = json.loads((first / "problems" / (summary["id"] + ".json")).read_text(encoding="utf-8"))
        offline = json.loads((first / "offline" / (summary["id"] + ".json")).read_text(encoding="utf-8"))
        routes = {"MANUAL_OFFLINE_REFERENCE": offline["manual_reference"], "PUBLIC_SYMBOLIC_GENERATED": offline["native"]["proposal"]}
        for proposal in routes.values():
            independent = independently_check(problem, proposal)
            assert len(independent) == 5 and all(independent.values())
            proofs += 5
        for invariant in offline["invariants"]["invariants"]:
            import sympy as sp
            p = symbolic(invariant["program"])[0]
            after = p.subs(dict(zip([sp.Symbol(s) for s in problem["state"]], symbolic(problem["transition"]))), simultaneous=True)
            assert sp.expand(p-after) == 0
        for witness in offline["witnesses"]:
            proposal, params, steps = routes[witness["route"]], witness["parameters"], witness["steps"]
            z = interpret(proposal["closed_form"], params + [steps])
            actual = interpret(proposal["decode"], params + z)
            assert actual == witness["actual"]
            if "original" in witness:
                current = interpret(problem["initial"], params)
                for _ in range(steps):
                    current = interpret(problem["transition"], params + current)
                assert interpret(problem["goal"], params + current) == witness["original"] == actual
                comparisons += 1
                original += witness["route"] == "MANUAL_OFFLINE_REFERENCE"
            else:
                power, goal = int(summary["id"][5]), summary["id"].split("_", 1)[1]
                a, b, c, k = params
                formula = [(a+k*steps)**power + b-a**power if goal == "position" else b-a**power]
                assert actual == witness["independent_fixture_formula"] == formula
                large += 1
    controls = json.loads((first / "controls.json").read_text(encoding="utf-8"))
    for control in controls:
        assert not all(independently_check(control["problem"], control["proposal"]).values())
    outside = json.loads((first / "outside_grammar.json").read_text(encoding="utf-8"))
    assert outside["result"]["status"].startswith("ABSTAINED")
    assert proofs == report["universal_identity_obligations"] == 40 and comparisons == report["paired_numeric_comparisons"] == 96
    assert large == report["large_horizon_formula_checks"] == 24 and original == report["original_loops_replayed"] == 48
    assert not report["headroom_measured"] and not report["G1_admitted"]
    output.mkdir(parents=True, exist_ok=False)
    save(output / "replay.json", {"status": "PASS_ENGINEERING_AUDIT", "manifest_files_checked": len(manifest),
                                 "independent_sympy_identity_checks": proofs, "independent_DAG_numeric_comparisons": comparisons,
                                 "large_horizon_formula_checks": large, "wrong_proposals_independently_rejected": len(controls),
                                 "original_report_sha256": digest(first / "report.json"), "original_manifest_sha256": digest(first / "manifest.json"),
                                 "engineering_only_not_headroom": True, "G1_admitted": False})
    print((output / "replay.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main(*(Path(p) for p in sys.argv[1:]))
