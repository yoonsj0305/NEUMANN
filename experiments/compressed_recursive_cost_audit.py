"""Independent proofs and receipt replay; never changes the first cost run."""
from collections import Counter
from pathlib import Path
import hashlib, itertools, json, math, random, statistics, sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.recursive_summary_replay import independent_obligations, eval_program


def read(path): return json.loads(path.read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def ident(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
def save(path, value):
    path.write_text(json.dumps(value, indent=2)+"\n", encoding="utf-8")


def dag_replay(proposal, dag):
    """Separate schema/length/goal traversal, without the production executor."""
    assert set(dag) == {"semantics", "nodes", "roots"}
    assert dag["semantics"] == "ordered_integer_list_dag"
    states, lengths = [], []
    for index, node in enumerate(dag["nodes"]):
        if node == ["nil"]:
            state, length = list(proposal["empty"]), 0
        elif node[0] == "single":
            assert len(node) == 2 and type(node[1]) is int
            state = eval_program(proposal["step"], [node[1]]+proposal["empty"])
            length = 1
        else:
            assert len(node) == 3 and node[0] == "concat"
            left, right = node[1:]
            assert all(type(i) is int and 0 <= i < index for i in [left, right])
            state = eval_program(proposal["merge"], states[left]+states[right])
            length = lengths[left]+lengths[right]
        states.append(state); lengths.append(length)
    assert 1 <= len(dag["roots"]) <= 8
    assert all(type(i) is int and 0 <= i < len(states) for i in dag["roots"])
    return [eval_program(proposal["decode"], states[i]) for i in dag["roots"]], [lengths[i] for i in dag["roots"]]


def small_control(proposal, public, seed):
    rng = random.Random(seed)
    nodes, lists = [["nil"]], [[]]
    for i in range(4):
        h = rng.randint(-17, 17); nodes.append(["single", h]); lists.append([h])
    for i in range(12):
        eligible = [j for j, values in enumerate(lists) if len(values) <= 16]
        a, b = rng.choice(eligible), rng.choice(eligible)
        nodes.append(["concat", a, b]); lists.append(lists[a]+lists[b])
    roots = [len(nodes)-1, len(nodes)-2, 0]
    outputs, lengths = dag_replay(proposal, {"semantics":"ordered_integer_list_dag", "nodes":nodes, "roots":roots})
    expected = []
    for index in roots:
        z = list(public["empty"])
        for h in reversed(lists[index]): z = eval_program(public["step"], [h]+z)
        expected.append(z)
    assert outputs == expected and lengths == [len(lists[r]) for r in roots]
    return len(roots)


def audit(preparation, first, output):
    import z3
    contract, report = read(preparation/"preregister.json"), read(first/"report.json")
    assert sha(preparation/"preregister.json") == "b19e8576bb7ca3e2c8b9e325c2e18c06aa5e3a913a52f6f982ff1d9447296a72"
    assert (first/"preregister.json").read_bytes() == (preparation/"preregister.json").read_bytes()
    assert sha(preparation/"preregister.json") == read(preparation/"freeze.json")["registration_sha256"]
    for path, pin in contract["sources"].items():
        assert sha(ROOT/path) == sha(preparation/"source"/path) == pin
    for path, pin in contract["prepared_assets"].items(): assert sha(preparation/path) == pin
    manifest = read(first/"manifest.json")
    assert all(sha(first/path) == pin for path, pin in manifest.items())
    rows, assets, expected = read(first/"observations.json"), read(preparation/"assets.json"), read(preparation/"expected.json")
    required = set(itertools.product(contract["cases"], contract["routes"], contract["reuse_counts"], range(3)))
    actual = {(r["case"], r["route"], r["count"], r["repeat"]) for r in rows}
    assert len(rows) == len(actual) == 240 and actual == required
    proposals, smt_seen, components = {}, {}, []
    proofs = serialized = comparisons = certified_workers = small = 0
    for row in rows:
        assert math.isfinite(row["complete_operational_seconds"]) and row["complete_operational_seconds"] > 0
        destination = first/row["worker"]
        if not row["accepted"]:
            assert row["all_goal_outputs_checked"] == 0
            continue
        assert not row["timeout"] and row["exit_code"] == 0
        assert row["all_goal_outputs_checked"] == row["count"]
        result, proposal, cert = (read(destination/n) for n in ["result.json", "proposal.json", "certificate.json"])
        key, route, count = row["case"], row["route"], row["count"]
        public = read(preparation/assets[key]["public"]["path"])
        assert ident(public) == key == cert["problem_sha256"]
        proposal_id = ident(proposal)
        assert proposal_id == cert["proposal_sha256"] and cert["accepted"] and len(cert["obligations"]) == 9
        assert result["case"] == key and result["route"] == route and result["count"] == count
        assert result["oracle_used"] == (route == "FREE_VALID_REFERENCE")
        assert not result["learning_performed"] and result["neural_forward_calls"] == 0
        unique = (key, proposal_id)
        smt = [(r["obligation"], r["smt2"]) for r in cert["obligations"]]
        assert all(r["status"] == "unsat" for r in cert["obligations"])
        if unique not in proposals:
            proposals[unique] = proposal; smt_seen[unique] = smt
            for name, theorem in independent_obligations(public, proposal).items():
                solver = z3.Solver(); solver.set(timeout=2000); solver.add(z3.Not(theorem))
                assert solver.check() == z3.unsat, (key, proposal_id, name)
                proofs += 1
            for name, statement in smt:
                solver = z3.Solver(); solver.set(timeout=2000); solver.from_string(statement)
                assert solver.check() == z3.unsat, (key, proposal_id, name)
                serialized += 1
            for seed in range(10): small += small_control(proposal, public, seed)
        else: assert smt_seen[unique] == smt
        queries = read(preparation/"queries"/key/(str(count)+".json"))
        assert len(queries) == len(result["queries"]) == count
        for i, (query, saved) in enumerate(zip(queries, result["queries"])):
            answer, lengths = dag_replay(proposal, query)
            result_dag = saved["result"]
            assert saved["index"] == i and ident(query) == saved["query_sha256"] == result_dag["dag_sha256"]
            assert answer == result_dag["outputs"] == expected[key][i]
            assert lengths == result_dag["expanded_root_lengths"]
            assert result_dag["problem_sha256"] == key and result_dag["proposal_sha256"] == proposal_id
            assert result_dag["input_nodes"] == len(query["nodes"])
            assert 1 <= result_dag["evaluated_nodes"] <= len(query["nodes"])
            assert not result_dag["expanded_length_is_speedup_claim"]
            comparisons += 1
        certified_workers += 1
        generation, proof, execution = result["generation_seconds"], result["certificate_and_engine_seconds"], sum(q["seconds"] for q in result["queries"])
        assert min(generation, proof, execution) >= 0
        components.append({"case":key,"route":route,"count":count,"repeat":row["repeat"],
                           "complete_seconds":row["complete_operational_seconds"],"generation_seconds":generation,
                           "certificate_and_engine_seconds":proof,"execution_seconds":execution,
                           "unattributed_seconds":row["complete_operational_seconds"]-generation-proof-execution,
                           "scope":"observed component diagnostic; not warm-service measurement or total research cost"})
    regimes = {}
    for count in contract["reuse_counts"]:
        cases = []
        for key in contract["cases"]:
            medians = {}
            for route in contract["routes"]:
                selected = [r for r in rows if r["case"] == key and r["count"] == count and r["route"] == route]
                if all(r["accepted"] for r in selected): medians[route] = statistics.median(r["complete_operational_seconds"] for r in selected)
            qualified = len(medians) == len(contract["routes"])
            ratio = medians["PUBLIC_GENERATIVE_NATIVE"]/medians["FREE_VALID_REFERENCE"] if qualified else None
            cases.append({"case":key,"qualified":qualified,"ratio":ratio})
        complete = all(c["qualified"] for c in cases)
        mean = math.exp(statistics.mean(math.log(c["ratio"]) for c in cases)) if complete else None
        wins = sum(c["ratio"] >= 10 for c in cases if c["qualified"])
        original = report["analysis"]["regimes"][str(count)]
        assert complete == original["all_evaluable"] and wins == original["10x_wins"]
        assert mean == original["geometric_mean_native_over_free"]
        regimes[str(count)] = {"all_evaluable":complete,"geometric_mean":mean,"10x_wins":wins,"passed":complete and mean >= 10 and wins >= 16}
    complete = all(r["all_evaluable"] for r in regimes.values())
    decision = contract["incomplete"] if not complete else contract["positive"] if all(r["passed"] for r in regimes.values()) else contract["negative"]
    assert decision == report["analysis"]["decision"]
    assert certified_workers == report["accepted_workers"] and comparisons == report["actual_queries_checked"]
    for key in contract["cases"]:
        all_queries = read(preparation/"queries"/key/"16.json")
        assert len({ident(q) for q in all_queries}) == 16
        assert read(preparation/"queries"/key/"1.json") == all_queries[:1]
    assert not output.exists(); output.mkdir(parents=True)
    save(output/"components.json", components)
    save(output/"audit.json", {"status":"PASS_INDEPENDENT_COMPRESSED_COST_AUDIT","first_report_sha256":sha(first/"report.json"),
         "first_manifest_sha256":sha(first/"manifest.json"),"manifest_files_checked":len(manifest),"workers_checked":len(rows),
         "certified_workers":certified_workers,"distinct_certified_programs":len(proposals),"independent_Z3_conditions":proofs,
         "serialized_CVC5_conditions_in_Z3":serialized,"independent_large_DAG_output_comparisons":comparisons,
         "small_unrolled_original_fold_controls":small,"regimes":regimes,"decision":decision,
         "full_original_OCaml_protocol":False,"performance_observations_replaced":False,"G1_admitted":False,"fresh_eligible":0})
    save(output/"manifest.json", {str(p.relative_to(output)):sha(p) for p in output.rglob("*") if p.is_file()})
    print((output/"audit.json").read_text(encoding="utf-8"))


if __name__ == "__main__": audit(*(Path(p) for p in sys.argv[1:]))
