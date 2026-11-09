"""Q3 source-induced TOPOLOGICAL-region operator on independent ARC grids.

Previous NEUMANN programs operate on filled components, point attributes and
single/bulk edits. This discovers an executable *dual representation*:
the CONNECTED EMPTY FACES separated by foreground boundaries, with each face
indexed by its relational order among the other faces.

Source I/O, not task ID or test answers, determines the interpretation of
background, the connectivity, and the table assigning effects to discovered
faces. All inverse-witness checks are on SOURCE observations. No official
target output is accepted, queried, or recoverable through this interface.

This is a new bounded object-representation interpreter, not unrestricted
meta-language creation: graph connectivity and ordinal coordinates are human
provided classical primitives. Independent original target success is needed.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from time import perf_counter_ns
from .relational_grid_inventor import grid


@dataclass(frozen=True)
class Face:
    cells: tuple[tuple[int, int], ...]
    bounds: tuple[int, int, int, int]
    rank: tuple[int, int]


def _faces(g, bg, diagonal, max_faces=120):
    h,w=len(g),len(g[0])
    seen=set()
    offsets=((-1,0),(1,0),(0,-1),(0,1))
    if diagonal:offsets+=((-1,-1),(-1,1),(1,-1),(1,1))
    blobs=[]
    for row in range(h):
        for col in range(w):
            if g[row][col]!=bg or (row,col) in seen:continue
            seen.add((row,col))
            pending=[(row,col)]
            cells=[]
            while pending:
                r,c=pending.pop()
                cells.append((r,c))
                for dr,dc in offsets:
                    y,x=r+dr,c+dc
                    if (0<=y<h and 0<=x<w and
                            (y,x) not in seen and g[y][x]==bg):
                        seen.add((y,x))
                        pending.append((y,x))
            ys=[x[0] for x in cells]
            xs=[x[1] for x in cells]
            blobs.append((tuple(sorted(cells)),
                          (min(ys),max(ys),min(xs),max(xs))))
            if len(blobs)>max_faces:return ()
    if len(blobs)<4:return ()
    rows={v:i for i,v in enumerate(sorted({b[0] for _,b in blobs}))}
    cols={v:i for i,v in enumerate(sorted({b[2] for _,b in blobs}))}
    # This is deliberately an inferred *face lattice* from actual observed
    # empty regions, not a hard-coded 3x3 or a task ID template.
    if len(rows)<2 or len(cols)<2:return ()
    faces=tuple(Face(cells,bounds,(rows[bounds[0]],cols[bounds[2]]))
                for cells,bounds in blobs)
    if len({f.rank for f in faces}) !=len(faces):return ()
    return faces


def _background(g, mode, color):
    if mode=="constant":return color
    if mode=="modal":
        hist=Counter(v for row in g for v in row)
        return min(hist,key=lambda v:(-hist[v],v))
    if mode=="corner":return g[0][0]
    raise ValueError("unknown inferred background semantics")


@dataclass(frozen=True)
class InventedFaceOperator:
    background_mode: str
    background_color: int
    diagonal: bool
    learned_effects: tuple[tuple[tuple[int,int],int], ...]
    source_examples: int
    independent_source_checks: int
    discovery_ms: float

    @property
    def ast(self):
        return (
            "source_invented_face_graph_operator",
            ("discover_connected_empty_regions",self.background_mode,
             self.background_color,self.diagonal),
            ("infer_relational_row_col_coordinates",),
            ("learned_face_effects",self.learned_effects),
            ("render_preserving_foreground",)
        )

    def apply(self, raw):
        g=grid(raw)
        bg=_background(g,self.background_mode,self.background_color)
        faces=_faces(g,bg,self.diagonal)
        if not faces:return None
        effects=dict(self.learned_effects)
        if any(face.rank not in effects for face in faces):
            # Unknown topological role must not silently receive a guessed
            # effect from an unvalidated lookup table.
            return None
        out=[list(row) for row in g]
        for face in faces:
            color=effects[face.rank]
            for r,c in face.cells:out[r][c]=color
        return tuple(tuple(row) for row in out)


@dataclass(frozen=True)
class FaceInvention:
    status: str
    operator: InventedFaceOperator | None
    candidates_examined: int
    elapsed_ms: float
    reason: str

    def apply(self, raw):
        return self.operator.apply(raw) if self.operator else None


class TopologicalRegionInventor:
    def __init__(self,*,max_source_ms=1500,max_face_count=120):
        if not 1<=max_source_ms<=120000 or not 4<=max_face_count<=500:
            raise ValueError("finite topology-program budgets required")
        self.max_source_ms=max_source_ms
        self.max_face_count=max_face_count

    def invent(self, source_pairs,*,independent_source_checks,
               known_classical=()):
        started=perf_counter_ns()
        train=tuple((grid(a),grid(b)) for a,b in source_pairs)
        check=tuple((grid(a),grid(b)) for a,b in independent_source_checks)
        if not train or not check:
            raise ValueError("independent SOURCE I/O required; no target gold")
        for a,b in train+check:
            if (len(a),len(a[0]))!=(len(b),len(b[0])):
                return FaceInvention("ABSTAIN_SHAPE",None,0,0,
                                     "face paint preserves source dimensions")
        for classical in known_classical:
            if all(classical(a)==b for a,b in train+check):
                return FaceInvention(
                    "CLASSICAL_FIRST",None,0,(perf_counter_ns()-started)/1e6,
                    "verified existing solver preempts invention")
        n=0
        # Candidate topology and background interpretation are selected from
        # SOURCE data. Never specialize the algorithm using task IDs/colors.
        modes=[("modal",0),("corner",0)]
        common=set(v for a,b in train for row in a for v in row)
        for v in sorted(common):modes.append(("constant",v))
        for mode,color in modes:
            for diagonal in (False,True):
                n+=1
                if (perf_counter_ns()-started)/1e6>self.max_source_ms:
                    return FaceInvention("ABSTAIN_BUDGET",None,n,
                                         (perf_counter_ns()-started)/1e6,
                                         "bounded inverse operator synthesis")
                labels={}
                changed=0
                valid=True
                for a,b in train:
                    bg=_background(a,mode,color)
                    faces=_faces(a,bg,diagonal,self.max_face_count)
                    if not faces:valid=False;break
                    for r in range(len(a)):
                        for c in range(len(a[0])):
                            if a[r][c]!=bg and a[r][c]!=b[r][c]:
                                valid=False;break
                        if not valid:break
                    if not valid:break
                    for face in faces:
                        outcomes={b[r][c] for r,c in face.cells}
                        if len(outcomes)!=1:valid=False;break
                        label=next(iter(outcomes))
                        prior=labels.setdefault(face.rank,label)
                        if prior!=label:valid=False;break
                        changed+=sum(a[r][c]!=label for r,c in face.cells)
                    if not valid:break
                if not valid or changed==0:continue
                program=InventedFaceOperator(
                    mode,color,diagonal,tuple(sorted(labels.items())),
                    len(train),len(check),(perf_counter_ns()-started)/1e6)
                if all(program.apply(a)==b for a,b in check):
                    return FaceInvention(
                        "SOURCE_VERIFIED_NEW_FACE_OPERATOR",program,n,
                        (perf_counter_ns()-started)/1e6,
                        "SOURCE-induced dual empty-face topology, not preset task")
        return FaceInvention(
            "ABSTAIN_NO_SOURCE_VERIFIED_TOPOLOGY",None,n,
            (perf_counter_ns()-started)/1e6,
            "no missing-region operator supported by SOURCE evidence")
