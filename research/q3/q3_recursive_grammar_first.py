"""Q3 learned recursive grammar: source-only induction + matched execution costs.

Reference BFS is an independently implemented classical comparator.
Performance claims are for this exact local CPU/Python benchmark only.
"""
from __future__ import annotations
from collections import defaultdict,deque
from statistics import median
from time import perf_counter_ns
import json

from neumann1.induced_fixpoint_grammar import RecursiveGrammarInventor


def independent_bfs(task):
    adjacency=defaultdict(list)
    for a,b in task["edges"]:
        adjacency[a].append(b)
    visited=set(task["seeds"])
    pending=deque(task["seeds"])
    while pending:
        for node in adjacency[pending.popleft()]:
            if node not in visited:
                visited.add(node)
                pending.append(node)
    return frozenset(visited)


def example(nodes,edges,seeds):
    task={"nodes":tuple(nodes),"edges":tuple(edges),"seeds":tuple(seeds)}
    task["answer"]=tuple(independent_bfs(task))
    return task


def source_learning():
    a=example("ABCDEFG",[(a,b) for a,b in zip("ABCDE","BCDEF")],("A",))
    b=example("abcdefghij",[
        ("a","b"),("b","c"),("c","d"),("d","e"),
        ("b","f"),("f","g")],("a",))
    verifier=example(range(12),[(i,i+1) for i in range(7)]+[(10,11)],(0,10))
    inventor=RecursiveGrammarInventor()
    proposed=inventor.invent([a,b],verification_tasks=[verifier])
    assert proposed.verified_for_all_finite_graphs
    return proposed


def timed(fn,task,n=21):
    outputs=[]
    elapsed=[]
    fn(task)
    for i in range(n):
        start=perf_counter_ns()
        out=fn(task)
        elapsed.append((perf_counter_ns()-start)/1e6)
        outputs.append(out)
    assert all(x==outputs[0] for x in outputs)
    return round(median(elapsed),5), outputs[0]


def main():
    compiled=source_learning()
    result=[]
    for size in (100,250,500,1000):
        target={"nodes":tuple(range(size)),
                "edges":tuple((i,i+1) for i in range(size-1)),
                "seeds":(0,)}
        naive,naive_out=timed(compiled.apply,target)
        delta,delta_out=timed(compiled.apply_delta,target)
        bfs,bfs_out=timed(independent_bfs,target)
        assert naive_out==delta_out==bfs_out==frozenset(range(size))
        result.append({
            "nodes":size,
            "naive_generated_ast_median_ms":naive,
            "delta_generated_ast_median_ms":delta,
            "strong_classical_bfs_median_ms":bfs,
            "delta_vs_naive_speedup":round(naive/delta,2),
            "delta_vs_bfs_slowdown":round(delta/bfs,2),
        })
    report={
        "schema":"neumann.q3.recursive-controlled-source-invention.conditional-FIRST.v1",
        "learned_ast":repr(compiled.ast),"source_tasks":compiled.source_count,
        "source_candidate_checks":compiled.checked,
        "source_discovery_ms":round(compiled.discovery_ns/1e6,5),
        "measurements":result,
        "scope":"All finite directed relations when task semantics truly equal reachability.",
        "caveats":[
            "This is newly synthesized AST and new primitive within hand-designed set/loop metalanguage.",
            "BFS is an equally expressive strong classical comparator and is faster in the local measurements.",
            "The very large speedup is delta vs a naive generated program, not vs BFS or frontier AI.",
            "Training and test task structures are author-generated, not external independent-author originals.",
            "Wall measurements depend on host CPU and the distribution; full Q4 total cost is not proven.",
        ]
    }
    print(json.dumps(report,indent=2))
    return report


if __name__=="__main__":
    main()
