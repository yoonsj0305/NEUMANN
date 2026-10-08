"""Small preregistered engineering cost probe, not a third G0 or learning study.

All three routes receive the same resident compiler, polynomial goal composition,
Horner/CSE specialization and reuse. Native discovery is a strong existing method.
Complete operational wall time is distinct from UNKNOWN total research investment.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
from time import perf_counter

from neumann1.guarded_perspective import bind_guarded_witness, compile_guarded_acceleration, digest, snapshot
from neumann1.inductive_perspective import HORIZON, constants, projections, split, substitute, compile_acceleration
from neumann1.inductive_symbolic_baseline import from_expressions, propose_polynomial_acceleration
from neumann1.guarded_symbolic_baseline import propose_guarded_acceleration, compile_discovered_guarded
from neumann1.representation_program import compile_program, sympy_transform
from experiments.inductive_fixture_cases import coordinate_fixture

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ["neumann1/representation_program.py", "neumann1/inductive_perspective.py",
    "neumann1/inductive_symbolic_baseline.py", "neumann1/guarded_perspective.py",
    "neumann1/guarded_symbolic_baseline.py", "experiments/inductive_fixture_cases.py",
    "experiments/guarded_fixture_probe.py"]
ROUTES = ["STRONG_NATIVE_SYMBOLIC", "GUARDED_SYMBOLIC", "FREE_VALID_GUARDED"]


def supplied_fixture():
    import sympy as sp
    problem, _ = coordinate_fixture()
    a,b,k,x,y,z = sp.symbols("a b k x y __z0")
    n = sp.Symbol(HORIZON)
    params, space = problem["parameters"], problem["parameters"]+problem["state"]
    proposal = {"encoding": projections(space,["x"]), "initial": projections(params,["a"]),
        "transition": from_expressions(params+["__z0"],[z+k]),
        "closed_form": from_expressions(params+[HORIZON],[a+k*n]),
        "decode": from_expressions(params+["__z0"],[z*z+b-a*a])}
    witness = bind_guarded_witness(problem,proposal,from_expressions(space,[y-x*x-b+a*a]),
        preservation=constants(space,[1]),transition=constants(space,[0]),goal=constants(space,[1]))
    return problem, proposal, witness


def requests():
    horizons = [0,1,31,10**6,10**30,10**100,7,101]
    return [([i-32,3*i+7,-i,i%7-3],horizons[i%8]) for i in range(64)]


def expected(row):
    a,b,c,k,n = row
    return ((a+k*n)**2+b-a*a,)


def fuse_goal(problem, proposal):
    params = problem["parameters"]
    space = params+[HORIZON]
    variables = dict(zip(space,split(projections(space,space))))
    latents = [f"__z{i}" for i in range(len(proposal["encoding"]["outputs"]))]
    composed = substitute(proposal["decode"], {**{p:variables[p] for p in params},
        **dict(zip(latents,split(proposal["closed_form"])))}, space)
    return compile_program(sympy_transform(composed,"HORNER_CSE"))


def freeze(path):
    problem, proposal, witness = supplied_fixture()
    contract = {"name":"GUARDED_ENGINEERING_COST_PROBE_V1", "kind":"FIXTURE_ENGINEERING_NOT_G0",
        "routes":ROUTES,"original_problem_sha256":digest(problem),
        "supplied_proposal":proposal,"supplied_witness":witness,"requests":requests(),
        "source_sha256":{p:sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES},
        "cold_repeats":3,"warm_repeats":7,"warm_batch_copies":64,"cold_counts":[1,64],
        "worker_timeout_seconds":30,"headroom_screen":10,
        "rule":"no 10x operational headroom if native/free paired geometric mean <10 in both cold scopes and resident warm scope; all outputs must verify; any missing worker INCOMPLETE",
        "rights":"same process residency, compiler, goal fusion, Horner/CSE, certificate reuse; no answer cache",
        "independence":"one already opened coordinate_fixture(power=2); F engineering only, not fresh generalization",
        "ordering":"round-robin routes rotated per repeat; no selective re-runs",
        "cost_scope":"cold process + imports + reads + discovery/checks + final certification/compilation/specialization + new requests + write/exit + parent validation",
        "unknown":["prior R&D/environment investment","energy","FLOPs","peak memory","money"],
        "gates":{"G0":"NOT_DECIDED_BY_THIS_FIXTURE","G1":False,"G2":False,"learning":False,"sealed_access":False}}
    with Path(path).open("x",encoding="utf-8") as stream:
        stream.write(snapshot(contract)+"\n")
    return contract


def check_sources(contract):
    for path, pinned in contract["source_sha256"].items():
        if sha256((ROOT/path).read_bytes()).hexdigest() != pinned:
            raise ValueError("Frozen source mismatch: "+path)


def worker(contract, route, count):
    check_sources(contract)
    begin = perf_counter()
    problem,_ = coordinate_fixture()
    structure = perf_counter()-begin
    discovery_begin = perf_counter()
    if route == "STRONG_NATIVE_SYMBOLIC":
        result = propose_polynomial_acceleration(problem)
        proposal = result["proposal"]
    elif route == "GUARDED_SYMBOLIC":
        result = propose_guarded_acceleration(problem)
        proposal = result["proposal"]
    else:
        result = {"proposal":contract["supplied_proposal"],"witness":contract["supplied_witness"]}
        proposal = result["proposal"]
    discovery = perf_counter()-discovery_begin
    certify_begin = perf_counter()
    if route == "STRONG_NATIVE_SYMBOLIC":
        engine = compile_acceleration(problem,proposal)
    else:
        engine = compile_discovered_guarded(problem,result)
    compiled = fuse_goal(problem,proposal)
    certify_compile = perf_counter()-certify_begin
    rows = [tuple(p)+(n,) for p,n in contract["requests"][:count]]
    start = perf_counter()
    outputs = compiled.run(rows)
    execution = perf_counter()-start
    assert outputs == [expected(row) for row in rows]
    assert outputs == [engine.run(row[:-1],row[-1]) for row in rows]
    warm = []
    warm_rows = []
    if count == 0:  # separate workers; warm timing work never enters cold service cost
        warm_rows = [tuple(p)+(n,) for p,n in contract["requests"]]*contract["warm_batch_copies"]
        compiled.run(warm_rows)
        for _ in range(contract["warm_repeats"]):
            start = perf_counter()
            values = compiled.run(warm_rows)
            elapsed = perf_counter()-start
            assert values == [expected(row) for row in warm_rows]
            warm.append(elapsed/len(warm_rows))
    return {"status":"VERIFIED","route":route,"count":count,"outputs":outputs,
        "structure_seconds":structure,"discovery_including_candidate_checks_seconds":discovery,
        "final_certify_compile_specialize_seconds":certify_compile,"execute_seconds":execution,
        "warm_seconds_per_request":warm,"warm_rows_per_round":len(warm_rows),
        "certificate":engine.certificate,"fused_goal_sha256":sha256(compiled.source.encode()).hexdigest(),
        "fused_add_calls":compiled.add_calls,"fused_mul_calls":compiled.mul_calls,
        "original_state_count":len(problem["state"]),"latent_state_count":len(proposal["encoding"]["outputs"]),
        "original_unfolded_transitions_removed":"n for every closed-form route, including native",
        "total_investment_cost":None,"learned":False}


def run(contract_path, output_path):
    contract_path = Path(contract_path).resolve()
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    check_sources(contract)
    # Reserve first evidence path before execution; never overwrite an earlier run.
    output_path = Path(output_path)
    with output_path.open("x",encoding="utf-8") as evidence:
        observations = []
        for count in contract["cold_counts"]+[0]:
            for repeat in range(contract["cold_repeats"]):
                routes = ROUTES[repeat%3:]+ROUTES[:repeat%3]
                for route in routes:
                    begin = perf_counter()
                    command = [sys.executable,"-X","utf8","-m","experiments.guarded_fixture_probe","worker",
                        "--contract",str(contract_path),"--route",route,"--count",str(count)]
                    try:
                        process = subprocess.run(command,cwd=ROOT,text=True,encoding="utf-8",capture_output=True,
                            timeout=contract["worker_timeout_seconds"])
                        if process.returncode:
                            raise ValueError(process.stderr or process.stdout)
                        row = json.loads(process.stdout)
                        assert row["outputs"] == [list(expected(tuple(p)+(n,))) for p,n in contract["requests"][:count]]
                        row.update({"repeat":repeat,"operational_parent_wall_seconds":perf_counter()-begin})
                    except (subprocess.TimeoutExpired,ValueError,AssertionError) as exc:
                        row = {"route":route,"count":count,"repeat":repeat,"status":"INCOMPLETE",
                            "error":str(exc),"operational_parent_wall_seconds":perf_counter()-begin}
                    observations.append(row)
                    print(route,count,repeat,row["status"],round(row["operational_parent_wall_seconds"],4),flush=True)
        complete = all(row["status"] == "VERIFIED" for row in observations)
        ratios = {}
        if complete:
            for count in contract["cold_counts"]:
                indexed = {(row["route"],row["repeat"]):row["operational_parent_wall_seconds"] for row in observations if row["count"]==count}
                ratios[f"cold{count}_native_over_free"] = statistics.geometric_mean(indexed[(ROUTES[0],i)]/indexed[(ROUTES[2],i)] for i in range(contract["cold_repeats"]))
                ratios[f"cold{count}_guarded_over_native"] = statistics.geometric_mean(indexed[(ROUTES[1],i)]/indexed[(ROUTES[0],i)] for i in range(contract["cold_repeats"]))
            warm = {(row["route"],row["repeat"]):statistics.median(row["warm_seconds_per_request"]) for row in observations if row["count"]==0}
            ratios["warm_native_over_free"] = statistics.geometric_mean(warm[(ROUTES[0],i)]/warm[(ROUTES[2],i)] for i in range(contract["cold_repeats"]))
            ratios["warm_guarded_over_native"] = statistics.geometric_mean(warm[(ROUTES[1],i)]/warm[(ROUTES[0],i)] for i in range(contract["cold_repeats"]))
        no_headroom = complete and all(ratios[k]<contract["headroom_screen"] for k in
            ["cold1_native_over_free","cold64_native_over_free","warm_native_over_free"])
        report = {"contract_sha256":sha256(contract_path.read_bytes()).hexdigest(),"contract":contract,
            "platform":platform.platform(),"python":sys.version,"observations":observations,"ratios":ratios,
            "engineering_cost_conclusion":"NO_MEANINGFUL_HEADROOM" if no_headroom else "INCOMPLETE",
            "scope":"opened engineering fixture operational measurements only; not G0/G1/G2 or learned NEUMANN",
            "complete_total_including_investment":None,"unmeasured":contract["unknown"]}
        evidence.write(snapshot(report)+"\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode",choices=["freeze","run","worker"])
    parser.add_argument("--contract",required=True)
    parser.add_argument("--output")
    parser.add_argument("--route",choices=ROUTES)
    parser.add_argument("--count",type=int)
    args = parser.parse_args()
    if args.mode == "freeze":
        print(digest(freeze(args.contract)))
    elif args.mode == "worker":
        print(snapshot(worker(json.loads(Path(args.contract).read_text(encoding="utf-8")),args.route,args.count)))
    else:
        print(snapshot({k:v for k,v in run(args.contract,args.output).items() if k not in {"observations","contract"}}))
