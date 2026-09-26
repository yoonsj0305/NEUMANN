from __future__ import annotations
import json
from neumann1 import Problem, NeumannEngine, BipartiteMatchingSolver, DeterministicVerifier, CostLedger, IRKind
from neumann1.matching_ir import ControlledMatchingStructureFormer, MatchingSemanticVerifier


FIXTURES = [
    (
        "satellite",
        "S1 can use A or C; S2 can use B or C; S3 can use A or D; S4 can use D or E; S5 can use C or F; S6 can use E or F",
        {"S1":["A","C"],"S2":["B","C"],"S3":["A","D"],"S4":["D","E"],"S5":["C","F"],"S6":["E","F"]},
    ),
    (
        "employees",
        "P1 may be assigned to J1, J3; P2 may be assigned to J2 or J3; P3 may be assigned to J1 or J4; P4 may be assigned to J4, J5",
        {"P1":["J1","J3"],"P2":["J2","J3"],"P3":["J1","J4"],"P4":["J4","J5"]},
    ),
    (
        "allowed_for",
        "Allowed for R1: X, Z; Allowed for R2: Y and Z; Allowed for R3: X, W",
        {"R1":["X","Z"],"R2":["Y","Z"],"R3":["X","W"]},
    ),
]


def run():
    former = ControlledMatchingStructureFormer()
    semantic = MatchingSemanticVerifier()
    engine = NeumannEngine(former, [BipartiteMatchingSolver()], DeterministicVerifier())
    rows=[]
    for name,text,edges in FIXTURES:
        p=Problem(text, {"matching_semantic_contract":{"expected_edges":edges}})
        ledger=CostLedger()
        rep=former.form(p, ledger)
        sem=semantic.verify_representation(p, rep, ledger)
        result=engine.solve(p)
        rows.append({
            "name":name,
            "kind":rep.kind.value,
            "semantic_fidelity":sem.ok,
            "solver_verified":result.verified,
            "perfect":bool(result.answer and result.answer.get("perfect")),
            "left_count":len(rep.payload.get("left",[])),
            "edge_count":sum(len(v) for v in rep.payload.get("edges",{}).values()),
        })

    unknown = Problem("Compute a minimum spanning tree of the weighted graph.")
    unknown_rep = former.form(unknown, CostLedger())
    return {
        "rows":rows,
        "all_semantically_faithful":all(r["semantic_fidelity"] for r in rows),
        "all_solver_verified":all(r["solver_verified"] for r in rows),
        "unknown_fail_closed":unknown_rep.kind == IRKind.UNKNOWN,
        "boundary":"Controlled grammar only; not general natural-language understanding.",
    }


if __name__ == "__main__":
    result=run()
    print(json.dumps(result, indent=2))
    with open("benchmark_v007_results.json","w",encoding="utf-8") as f:
        json.dump(result,f,indent=2)