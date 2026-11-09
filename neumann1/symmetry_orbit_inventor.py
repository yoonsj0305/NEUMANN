"""Q3/Q6: invent a variable-size structural representation from learned terms.

The source learned polynomial contains raw interaction-mask features. This
inventor finds complete symmetry ORBITS of those terms, reconstructs the
minimal structural motif, and compiles that motif to different input widths.

Schema provides only raw input coordinate topology (graph edge endpoints or
symbolic position order). It NEVER names triangle, 4-cycle or any string
rule. This is conditional symmetry-equivariant abstraction, not arbitrary
unknown ontology invention; source-completeness and transfer must be checked.
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations,permutations
from .causal_representation_inventor import (
    InventedRepresentation,_validate_point,_encode)


@dataclass(frozen=True)
class GraphSchema:
    vertices:int

    @property
    def width(self):
        return self.vertices*(self.vertices-1)//2

    def edges(self):
        return tuple(combinations(range(self.vertices),2))


@dataclass(frozen=True)
class SequenceSchema:
    positions:int

    @property
    def width(self):
        return self.positions


def _graph_template(mask,shape):
    included=tuple(e for i,e in enumerate(shape.edges())
                   if mask&(1<<i))
    vertices=tuple(sorted({v for edge in included for v in edge}))
    if not vertices:return ()
    local_index={v:i for i,v in enumerate(vertices)}
    local=tuple((local_index[a],local_index[b]) for a,b in included)
    return min(tuple(sorted(tuple(sorted((perm[a],perm[b])))
                            for a,b in local))
               for perm in permutations(range(len(vertices))))


def _sequence_template(mask,shape):
    positions=[i for i in range(shape.positions) if mask&(1<<i)]
    return tuple(i-positions[0] for i in positions) if positions else ()


@lru_cache(maxsize=256)
def graph_orbit(pattern,vertices):
    edges=tuple(combinations(range(vertices),2))
    index={e:i for i,e in enumerate(edges)}
    k=1+max(max(edge) for edge in pattern)
    masks=set()
    for selected in combinations(range(vertices),k):
        for perm in permutations(selected):
            mask=0
            for a,b in pattern:
                u,v=sorted((perm[a],perm[b]))
                mask|=1<<index[u,v]
            masks.add(mask)
    return frozenset(masks)


@lru_cache(maxsize=256)
def sequence_orbit(offsets,positions):
    if not offsets:return frozenset()
    return frozenset(
        sum(1<<(j+start) for j in offsets)
        for start in range(positions-max(offsets)))


@dataclass(frozen=True)
class InventedOrbitRepresentation:
    kind:str
    source_width:int
    templates:tuple
    constant_bit:int
    verified_source_orbit_terms:int

    @property
    def ast(self):
        return ("invented_structural_orbit_representation",self.kind,
                tuple(("learned_orbit_motif",motif)
                      for motif in self.templates),
                ("orbit_closure","all_injective_embeddings"
                 if self.kind=="graph" else "all_valid_translations"),
                ("reduce","xor"))

    def masks(self,shape):
        if self.kind=="graph" and not isinstance(shape,GraphSchema):
            raise ValueError("typed graph schema required")
        if self.kind=="sequence" and not isinstance(shape,SequenceSchema):
            raise ValueError("typed symbolic-position schema required")
        if self.kind=="graph":
            if shape.vertices<1 or shape.vertices>16:
                raise ValueError("bounded graph input required")
            return frozenset().union(
                *(graph_orbit(t,shape.vertices) for t in self.templates))
        if shape.positions<1 or shape.positions>1024:
            raise ValueError("bounded symbolic input required")
        return frozenset().union(
            *(sequence_orbit(t,shape.positions) for t in self.templates))

    def apply(self,raw,shape):
        packed=_encode(_validate_point(raw,shape.width))
        return self.constant_bit ^ (
            sum(packed&m==m for m in self.masks(shape))&1)


class SymmetryOrbitInventor:
    """Learn a NEW structural feature grammar, never examine target gold."""

    def invent(self,learned,source_schema):
        if not isinstance(learned,InventedRepresentation):
            raise TypeError("source-certified polynomial representation required")
        if not isinstance(source_schema,(GraphSchema,SequenceSchema)):
            raise TypeError("explicit source-coordinate symmetry contract")
        if learned.input_width!=source_schema.width:
            raise ValueError("source/schema coordinate mismatch")
        kind=("graph" if isinstance(source_schema,GraphSchema)
              else "sequence")
        latent=tuple(learned.latent_features)
        constant_bit=int(0 in latent)
        active={m for m in latent if m}
        extractor=(_graph_template if kind=="graph"
                   else _sequence_template)
        inferred={extractor(m,source_schema) for m in active}
        if not inferred or () in inferred:
            raise ValueError("no source-supported structural motif")
        program=InventedOrbitRepresentation(
            kind,learned.input_width,tuple(sorted(inferred)),
            constant_bit,len(active))
        if program.masks(source_schema)!=active:
            raise ValueError(
                "learned features are not COMPLETE symmetry orbits; "
                "out-of-domain extrapolation is unsupported")
        return program
