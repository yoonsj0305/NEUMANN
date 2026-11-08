"""Q3/Q6: learned features become newly invented variable-size abstractions.

Graph source is 5 vertices; target has 6/7/8. Symbolic source has
12 positions; target has 13/20/37/64. No target gold enters either learner.
Different graph motifs (triangle AND 4-cycle) are discovered from raw
source I/O, not hardcoded into the representation learner.

These tasks are researcher-generated mathematical laws, not frontier
independent-author ARC-AGI-2 originals.
"""
from itertools import combinations,permutations
from random import Random
from dataclasses import replace
import pytest
from neumann1.causal_representation_inventor import (
    CausalRepresentationInventor)
from neumann1.symmetry_orbit_inventor import (
    SymmetryOrbitInventor,GraphSchema,SequenceSchema)


def bits(n,width):return tuple((n>>i)&1 for i in range(width))


def source_cases(n,degree,oracle,checks=50):
    basis=[tuple(int(i in inds) for i in range(n))
           for k in range(degree+1) for inds in combinations(range(n),k)]
    domain=[bits(i,n) for i in range(1<<n)]
    rest=[x for x in domain if x not in set(basis)]
    Random(n*191+degree).shuffle(rest)
    return ([(x,oracle(x)) for x in basis],
            [(x,oracle(x)) for x in rest[:checks]])


def graph_motif_oracle(x,n,cycle_edges):
    idx={e:i for i,e in enumerate(combinations(range(n),2))}
    masks=set()
    for nodes in combinations(range(n),len(cycle_edges)):
        for p in permutations(nodes):
            edges=tuple(tuple(sorted((p[a],p[b])))
                        for a,b in cycle_edges)
            masks.add(sum(1<<idx[e] for e in edges))
    packed=sum(value<<i for i,value in enumerate(x))
    return sum(packed&m==m for m in masks)&1


TRIANGLE=((0,1),(1,2),(0,2))
CYCLE4=((0,1),(1,2),(2,3),(3,0))


def seq_oracle(x):
    return sum(x[i]&(1^x[i+1])&x[i+2]
               for i in range(len(x)-2))&1


def learn_graph(pattern,degree):
    source,checks=source_cases(
        10,degree,lambda x:graph_motif_oracle(x,5,pattern))
    learned=CausalRepresentationInventor(max_degree=degree).invent(
        source,independent_source_checks=checks)
    assert learned.status=="SOURCE_VERIFIED_NEW_REPRESENTATION"
    return learned.program


def learn_seq():
    source,checks=source_cases(12,3,seq_oracle,90)
    learned=CausalRepresentationInventor(max_degree=3).invent(
        source,independent_source_checks=checks)
    assert learned.status=="SOURCE_VERIFIED_NEW_REPRESENTATION"
    return learned.program


def test_source_discovers_unknown_triangle_then_exhaustively_solves_k6_graphs():
    original=learn_graph(TRIANGLE,3)
    inferred=SymmetryOrbitInventor().invent(original,GraphSchema(5))
    assert inferred.kind=="graph"
    assert len(inferred.templates)==1
    assert len(inferred.templates[0])==3
    assert len(inferred.masks(GraphSchema(5)))==10
    for vertices,samples in ((6,32768),(7,1000),(8,400)):
        rng=Random(vertices*100)
        width=vertices*(vertices-1)//2
        for i in range(samples):
            raw=bits(i if vertices==6 else rng.getrandbits(width),width)
            assert inferred.apply(raw,GraphSchema(vertices))==(
                graph_motif_oracle(raw,vertices,TRIANGLE))
    with pytest.raises(ValueError):
        original.apply(bits(3,15))


def test_source_discovers_distinct_cycle4_not_hardcoded_triangular_rule():
    original=learn_graph(CYCLE4,4)
    inferred=SymmetryOrbitInventor().invent(original,GraphSchema(5))
    assert inferred.kind=="graph"
    assert len(inferred.templates)==1
    assert len(inferred.templates[0])==4
    assert len(inferred.masks(GraphSchema(5)))==15
    assert inferred.templates[0] != (
        SymmetryOrbitInventor().invent(
            learn_graph(TRIANGLE,3),GraphSchema(5)).templates[0])
    for vertices,samples in ((6,32768),(7,600)):
        rng=Random(vertices*811)
        width=vertices*(vertices-1)//2
        for i in range(samples):
            raw=bits(i if vertices==6 else rng.getrandbits(width),width)
            assert inferred.apply(raw,GraphSchema(vertices))==(
                graph_motif_oracle(raw,vertices,CYCLE4))


def test_source_discovers_local_sequence_motifs_and_extends_to_length64():
    original=learn_seq()
    inferred=SymmetryOrbitInventor().invent(original,SequenceSchema(12))
    assert set(inferred.templates)=={(0,2),(0,1,2)}
    for n in (13,20,37,64):
        rng=Random(n*701)
        for i in range(400):
            raw=bits(rng.getrandbits(n),n)
            assert inferred.apply(raw,SequenceSchema(n))==seq_oracle(raw)
    with pytest.raises(ValueError):
        original.apply(bits(3,20))


def test_partial_orbit_and_position_specific_rule_are_rejected():
    p=learn_graph(TRIANGLE,3)
    with pytest.raises(ValueError):
        SymmetryOrbitInventor().invent(
            replace(p,latent_features=p.latent_features[:2]),
            GraphSchema(5))
    with pytest.raises(ValueError):
        SymmetryOrbitInventor().invent(p,GraphSchema(6))
    with pytest.raises(ValueError):
        SymmetryOrbitInventor().invent(p,SequenceSchema(10))
    oracle=lambda x:x[0]&x[1]&x[2]
    source,checks=source_cases(12,3,oracle,30)
    learned=CausalRepresentationInventor(max_degree=3).invent(
        source,independent_source_checks=checks)
    assert learned.status=="SOURCE_VERIFIED_NEW_REPRESENTATION"
    with pytest.raises(ValueError):
        SymmetryOrbitInventor().invent(
            learned.program,SequenceSchema(12))
