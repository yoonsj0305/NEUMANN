"""Q3: reconstruct an UNDECLARED graph ontology from learned interactions.

No edge list or vertex IDs are provided. From source-learned cubic interaction
masks, find the co-occurrence graph of raw coordinates. If they are edges of
a complete graph K_n, n>=5, its (n-1)-cliques are vertex stars. Every raw
coordinate belongs to exactly two stars; recover endpoints and a NEW type.

The final executable motif is inferred from recovered edge interactions,
NOT supplied as a named 'triangle' solver. An exhaustive source orbit
certificate is required. Arbitrary hidden ontology recovery remains OPEN.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations,permutations
from math import isqrt
from .causal_representation_inventor import (
    InventedRepresentation,_validate_point,_encode)
from .symmetry_orbit_inventor import (
    graph_orbit,InventedOrbitRepresentation)


@dataclass(frozen=True)
class InferredGraphOntology:
    vertices:int
    raw_coordinates_to_latent_edges:tuple[tuple[int,int],...]
    recovered_vertex_stars:tuple[frozenset[int],...]
    source_interaction_monomials:int
    learned_motifs:tuple

    @property
    def ast(self):
        return ("source_invented_graph_ontology",
                ("inferred_vertices",self.vertices),
                ("inferred_edge_incidence",
                 self.raw_coordinates_to_latent_edges),
                ("inferred_unlabeled_motifs",self.learned_motifs),
                ("reduce","xor"))

    def apply(self,raw):
        width=len(self.raw_coordinates_to_latent_edges)
        encoded=_encode(_validate_point(raw,width))
        lookup={edge:i for i,edge in
                enumerate(self.raw_coordinates_to_latent_edges)}
        masks=set()
        for motif in self.learned_motifs:
            k=1+max(max(e) for e in motif)
            for selected in combinations(range(self.vertices),k):
                for permutation in permutations(selected):
                    mask=0
                    for a,b in motif:
                        u,v=sorted((permutation[a],permutation[b]))
                        mask|=1<<lookup[u,v]
                    masks.add(mask)
        return sum(encoded&m==m for m in masks)&1

    def export_variable_width_program(self):
        """Apply discovered motif to a new graph with declared raw schema."""
        return InventedOrbitRepresentation(
            "graph",len(self.raw_coordinates_to_latent_edges),
            self.learned_motifs,0,self.source_interaction_monomials)


class LatentGraphOntologyInventor:
    """Propose graph type only if source interaction signatures prove it."""

    def invent(self,source):
        if not isinstance(source,InventedRepresentation):
            raise TypeError("independent-source-verified representation needed")
        width=source.input_width
        n=(1+isqrt(1+8*width))//2
        if n<5 or n>7 or n*(n-1)//2!=width:
            raise ValueError("unsupported or unidentifiable graph input width")
        terms=tuple(source.latent_features)
        if 0 in terms or len(terms)!=n*(n-1)*(n-2)//6:
            raise ValueError("source support not a complete cubic relation")
        if any(m.bit_count()!=3 for m in terms):
            raise ValueError("must first discover source triadic interactions")
        support={tuple(i for i in range(width) if mask&(1<<i))
                 for mask in terms}
        if len(support)!=len(terms):
            raise ValueError("duplicate latent interaction features")
        cooccur=set()
        for triad in support:
            for i,j in combinations(triad,2):
                cooccur.add((min(i,j),max(i,j)))
        # Discover the vertex stars (large maximal coordinate cliques).
        stars=[]
        for subset in combinations(range(width),n-1):
            if all((min(i,j),max(i,j)) in cooccur
                   for i,j in combinations(subset,2)):
                stars.append(frozenset(subset))
        if len(stars)!=n:
            raise ValueError("unidentifiable source vertex stars")
        if any(sum(i in star for star in stars)!=2 for i in range(width)):
            raise ValueError("source coordinate not incident to exactly 2 vertices")
        edges=[]
        for coordinate in range(width):
            ends=tuple(i for i,star in enumerate(stars)
                       if coordinate in star)
            if len(ends)!=2:
                raise ValueError("ill-formed learned edge endpoints")
            edges.append(ends)
        if len(set(edges))!=width:
            raise ValueError("nonunique inferred raw-to-edge map")
        # Generate new motif AST directly from actual observed raw triads.
        def canonical(term):
            raw_edges=tuple(edges[i] for i in term)
            vertices=tuple(sorted({v for e in raw_edges for v in e}))
            remap={v:i for i,v in enumerate(vertices)}
            local=tuple((remap[a],remap[b]) for a,b in raw_edges)
            return min(tuple(sorted(tuple(sorted((p[a],p[b])))
                                    for a,b in local))
                       for p in permutations(range(len(vertices))))
        motifs=tuple(sorted({canonical(term) for term in support}))
        # Reencode original raw interactions with a newly inferred canonical
        # vertex ordering and verify full closure under all automorphisms.
        canonical_index={edge:i for i,edge in
                         enumerate(combinations(range(n),2))}
        observed_masks={
            sum(1<<canonical_index[tuple(sorted(edges[i]))]
                for i in term) for term in support}
        generated=set().union(*(graph_orbit(motif,n)
                                for motif in motifs))
        if observed_masks!=generated:
            raise ValueError("inferred coordinate ontology fails orbit certificate")
        return InferredGraphOntology(
            n,tuple(edges),tuple(stars),len(terms),motifs)
