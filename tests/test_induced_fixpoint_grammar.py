"""Q3: learn control syntax, create a new primitive and transfer, with proofs.

All held-out results use an independent queue/BFS implementation. No target
oracle is passed into RecursiveGrammarInventor. Synthetic authored domains:
the shared structural principle is *finite relational reachability*.
"""
from collections import defaultdict, deque
from itertools import product
from random import Random

import pytest

from neumann1 import NeumannEngine, RegistryEngine
from neumann1.induced_grammar import GrammarInventor, eval_ast
from neumann1.induced_fixpoint_grammar import (
    CompiledRule, InsufficientEvidence, RecursiveGrammarInventor,
)


def independent_reference(nodes, edges, seeds):
    adjacency = defaultdict(list)
    for a,b in edges:
        adjacency[a].append(b)
    seen = set(seeds)
    pending = deque(seeds)
    while pending:
        for nxt in adjacency[pending.popleft()]:
            if nxt not in seen:
                seen.add(nxt)
                pending.append(nxt)
    return frozenset(seen)


def source_task(nodes, edges, seeds):
    return {"nodes": tuple(nodes), "edges": tuple(edges), "seeds": tuple(seeds),
            "answer": tuple(independent_reference(nodes,edges,seeds))}


def training():
    a = source_task("ABCDEFG",[(a,b) for a,b in zip("ABCDE","BCDEF")],("A",))
    b = source_task("abcdefghij",[
        ("a","b"),("b","c"),("c","d"),("d","e"),("b","f"),("f","g")],("a",))
    c = source_task(range(12),[(i,i+1) for i in range(7)]+[(10,11)],(0,10))
    d = source_task(range(8),[(i,i+1) for i in range(1,7)],(1,))
    return [a,b],[c,d]


def trained():
    source,source_verify = training()
    inventor = RecursiveGrammarInventor()
    rule = inventor.invent(source,verification_tasks=source_verify)
    return inventor,rule


def test_invents_unseen_recursive_control_ast():
    engine,rule = trained()
    assert rule.ast == ("iterate","seeds","rel_image","forward","union","stable")
    assert rule.checked > 1
    assert rule.verified_for_all_finite_graphs
    assert rule.proof is not None
    assert rule.compile_delta()[0] == "delta_while_nonempty"


def test_complete_n3_graph_model_check_4096_cases():
    inventor,rule = trained()
    nodes = (0,1,2)
    possible = tuple(product(nodes,repeat=2))
    checks = 0
    for edge_mask in range(1<<len(possible)):
        edges = tuple(e for i,e in enumerate(possible) if (edge_mask>>i)&1)
        for seed_mask in range(1<<len(nodes)):
            seeds = tuple(i for i in nodes if (seed_mask>>i)&1)
            inp = {"nodes":nodes,"edges":edges,"seeds":seeds}
            result = independent_reference(nodes,edges,seeds)
            assert rule.apply(inp) == result
            assert rule.apply_delta(inp) == result
            checks += 1
    assert checks == 4096


def test_unmodified_operator_transfers_to_grid_flood_regions():
    _,rule = trained()
    rng = Random(41)
    for seed in range(100):
        width,height = 4+seed%6,4+(seed//6)%6
        nodes = tuple(product(range(height),range(width)))
        open_cells = {cell for cell in nodes if rng.random()<0.7}
        edges = []
        for i,j in open_cells:
            for k in ((i+1,j),(i-1,j),(i,j+1),(i,j-1)):
                if k in open_cells:
                    edges.append(((i,j),k))
        starts = tuple(rng.sample(tuple(sorted(open_cells)),
                                  min(len(open_cells),1+seed%3))) if open_cells else ()
        task = {"nodes":nodes,"edges":edges,"seeds":starts}
        assert rule.apply_delta(task)==independent_reference(nodes,edges,starts)


def test_unmodified_operator_transfers_to_dfa_states_and_dependencies():
    _,rule = trained()
    rng = Random(9143)
    for seed in range(100):
        nodes = tuple("state_"+str(i*173+seed) for i in range(4,16))
        edges = tuple((a,b) for a in nodes for b in nodes if rng.random()<.09)
        starts = tuple(rng.sample(nodes,rng.randrange(1,4)))
        task = {"nodes":nodes,"edges":edges,"seeds":starts}
        assert rule.apply_delta(task)==independent_reference(nodes,edges,starts)
        dep_nodes=tuple("component_"+str(k) for k in range(12+seed%13))
        dep_edges=tuple((dep_nodes[i],dep_nodes[j]) for i in range(len(dep_nodes))
                        for j in range(i+1,len(dep_nodes)) if rng.random()<.19)
        dep_starts=(dep_nodes[0],dep_nodes[2])
        dep_task={"nodes":dep_nodes,"edges":dep_edges,"seeds":dep_starts}
        assert rule.apply_delta(dep_task)==independent_reference(
            dep_nodes,dep_edges,dep_starts)


def test_source_counterexample_reinvents_control_not_parameters():
    a=source_task(range(5),[(0,1),(1,2)],(0,))
    b=source_task("abcde",[("a","b"),("b","c")],("a",))
    c=source_task(range(6),[(0,1),(1,2)],(0,))
    engine=RecursiveGrammarInventor()
    before=engine.invent([a,b],verification_tasks=[c])
    assert before.ast[-1]=="two"
    long=source_task(range(9),[(i,i+1) for i in range(6)],(0,))
    assert engine.revise_with_source_counterexample(long)
    assert engine.learned[0].ast[-1]=="stable"
    assert engine.solve(long)==frozenset(long["answer"])
    assert engine.repairs==1
    assert not engine.revise_with_source_counterexample(long)


def test_new_executable_primitive_added_to_previous_unary_grammar():
    _,rule=trained()
    input_task={"nodes":(0,1,2,3,4),
                "edges":((0,1),(1,2),(2,3)),"seeds":(0,)}
    result=independent_reference(
        input_task["nodes"],input_task["edges"],input_task["seeds"])
    cold=GrammarInventor(max_cost=2).solve([(input_task,result)])
    assert not cold.solved
    grammar=GrammarInventor(max_cost=2)
    grammar.register_generated_primitive("invented:testclosure",rule)
    solved=grammar.solve([(input_task,result)])
    assert solved.solved
    assert solved.expression==("call","invented:testclosure",("input",))
    fresh={"nodes":("s","t","u","v"),"edges":(("s","t"),("t","u")),"seeds":("s",)}
    assert eval_ast(solved.expression,fresh,
                    dynamic_primitives=grammar.dynamic_primitives)==frozenset(
                        ("s","t","u"))


def test_both_production_engines_promote_generated_primitive():
    training_tasks, source_checks=training()
    for engine in (NeumannEngine(None,[],None),RegistryEngine(None,None)):
        rule=engine.learn_recursive_control(
            training_tasks,independent_source_checks=source_checks)
        assert rule.verified_for_all_finite_graphs
        assert len(engine._invented_grammar.dynamic_primitives)==1
        task={"nodes":tuple(range(8)),
              "edges":tuple((i,i+1) for i in range(7)),"seeds":(0,)}
        truth=frozenset(range(8))
        assert engine.execute_recursive_control(task)==truth
        result=engine.synthesize_with_invented_grammar([(task,truth)])
        assert result.solved
        assert result.expression[0:2][0]=="call"


def test_refuses_unverified_primitive_unknown_source_and_budget():
    source,source_checks=training()
    bad=CompiledRule(
        ("iterate","seeds","rel_image","backward","union","stable"),0,(),0,0)
    with pytest.raises(ValueError):
        GrammarInventor().register_generated_primitive("invented:wrong",bad)
    with pytest.raises(InsufficientEvidence):
        RecursiveGrammarInventor(max_candidates=2).invent(
            source,verification_tasks=source_checks)
    with pytest.raises(InsufficientEvidence):
        RecursiveGrammarInventor().invent(source,verification_tasks=())
    with pytest.raises(InsufficientEvidence):
        RecursiveGrammarInventor().solve(source[0])
    with pytest.raises(InsufficientEvidence):
        bad.compile_delta()


def test_strict_nonmonotone_policy_refused():
    candidate=CompiledRule(
        ("iterate","seeds","rel_image","forward","replace","stable"),0,(),0,0)
    with pytest.raises(InsufficientEvidence):
        candidate.apply({"nodes":(0,1,2),"edges":((0,1),),"seeds":(0,)})


def test_external_exception_not_identifiable_from_finite_source():
    engine,_=trained()
    target={"nodes":("x","y","z","w","q"),
            "edges":(("x","y"),("y","z"),("z","w")),"seeds":("x",)}
    prediction=engine.solve(target)
    # An arbitrary task-output oracle might agree with all source data
    # yet omit 'w' on this new target. Our conditional theorem relies
    # on the output actually meaning relational reachability.
    assert prediction!=frozenset(("x","y","z"))
