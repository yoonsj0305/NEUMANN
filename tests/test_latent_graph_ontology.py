"""Q3: raw coordinate topology is NOT provided to the ontology inventor.

Independent random permutations of 10 coordinates conceal all named edges.
Source interaction features must recover the vertex/edge incidence structure
and motif AST. Fixed-size exhaustive check on 1,024 raw bit inputs for each
permutation; 6-vertex transfer is separately tested.
"""
from dataclasses import replace
from itertools import combinations
from random import Random
import pytest
from neumann1.causal_representation_inventor import (
    CausalRepresentationInventor)
from neumann1.latent_graph_ontology import LatentGraphOntologyInventor
from neumann1.symmetry_orbit_inventor import GraphSchema


def raw_bits(n,width):return tuple((n>>i)&1 for i in range(width))


def oracle5(raw,permutation):
    # A separate scoring oracle knows the original bit-to-edge mapping.
    # Neither the polynomial nor ontology inventor receives this mapping.
    x=tuple(raw[permutation.index(i)] for i in range(10))
    e={pair:i for i,pair in enumerate(combinations(range(5),2))}
    return sum(x[e[a,b]]&x[e[a,c]]&x[e[b,c]]
               for a,b,c in combinations(range(5),3))&1


def source_design(oracle):
    basis=[tuple(int(i in selected) for i in range(10))
           for k in range(4)
           for selected in combinations(range(10),k)]
    observed=set(basis)
    remaining=[raw_bits(i,10) for i in range(1024)
               if raw_bits(i,10) not in observed]
    Random(9017).shuffle(remaining)
    return ([(x,oracle(x)) for x in basis],
            [(x,oracle(x)) for x in remaining[:50]])


def test_discovers_full_graph_ontology_without_known_edge_schema():
    for seed in (51,73,903,1117,2209):
        permutation=list(range(10))
        Random(seed).shuffle(permutation)
        oracle=lambda raw:oracle5(raw,permutation)
        source,verifier=source_design(oracle)
        discovered=CausalRepresentationInventor(max_degree=3).invent(
            source,independent_source_checks=verifier)
        assert discovered.status=="SOURCE_VERIFIED_NEW_REPRESENTATION"
        ontology=LatentGraphOntologyInventor().invent(discovered.program)
        assert ontology.vertices==5
        assert ontology.source_interaction_monomials==10
        assert len(ontology.recovered_vertex_stars)==5
        assert len(set(ontology.raw_coordinates_to_latent_edges))==10
        assert len(ontology.learned_motifs)==1
        assert len(ontology.learned_motifs[0])==3
        for k in range(1024):
            x=raw_bits(k,10)
            assert ontology.apply(x)==oracle(x)
        variable=ontology.export_variable_width_program()
        # A NEW input dimension is structurally expressible with no model
        # fitting or graph motif named in the inventor.
        for k in range(64):
            raw=raw_bits(k,15)
            edges={p:i for i,p in enumerate(combinations(range(6),2))}
            gold=sum(raw[edges[a,b]]&raw[edges[a,c]]&raw[edges[b,c]]
                     for a,b,c in combinations(range(6),3))&1
            assert variable.apply(raw,GraphSchema(6))==gold


def test_unstructured_interaction_program_does_not_fake_hidden_ontology():
    permutation=list(range(10))
    Random(903).shuffle(permutation)
    oracle=lambda raw:oracle5(raw,permutation)
    source,verify=source_design(oracle)
    learned=CausalRepresentationInventor(max_degree=3).invent(
        source,independent_source_checks=verify).program
    with pytest.raises(ValueError):
        LatentGraphOntologyInventor().invent(
            replace(learned,latent_features=learned.latent_features[:9]))
    with pytest.raises(ValueError):
        LatentGraphOntologyInventor().invent(
            replace(learned,latent_features=tuple(1<<i for i in range(10))))


def test_both_production_engines_reconstruct_ontology_without_schema():
    from neumann1 import NeumannEngine,RegistryEngine
    perm=list(range(10))
    Random(19).shuffle(perm)
    source,checks=source_design(lambda x:oracle5(x,perm))
    for engine in (NeumannEngine(None,[],None),
                   RegistryEngine(None,None)):
        found,ontology=engine.invent_hidden_graph_ontology(
            source,checks,max_degree=3)
        assert found.status=="SOURCE_VERIFIED_NEW_REPRESENTATION"
        assert ontology is not None
        assert ontology.vertices==5
        assert all(ontology.apply(raw_bits(i,10))==oracle5(raw_bits(i,10),perm)
                   for i in range(1024))
