"""Q3/Q6: source-induced executable Boolean/affine relational programs.

One unchanged metaprogram builds predicates and output expressions by looking
at typed observed entity attributes. It has NO domain-name router. Strong
classical source-verified solvers run FIRST and bypass all invention.

Bounded human-designed relational metalanguage: this is not arbitrary
Turing-complete grammar invention or frontier Q3/Q6 generalization. Source
fitting is conditional on representability and independent source checks.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Callable
from itertools import combinations
from time import perf_counter_ns


@dataclass(frozen=True)
class Entity:
    key: object
    attributes: tuple[tuple[str,int],...]
    value: int

    @classmethod
    def from_attrs(cls,key,attributes,value):
        if (type(value) is not int or
                any(type(v) is not int for v in attributes.values())):
            raise ValueError("integer typed entity features required")
        return cls(key,tuple(sorted(attributes.items())),value)

    def attr(self,name):
        if isinstance(name,tuple):
            op,a,b=name
            x,y=self.attr(a),self.attr(b)
            if op=="sub":return x-y
            if op=="add":return x+y
            if op=="abs_sub":return abs(x-y)
            if op=="mul":return x*y
            raise ValueError("unsupported generated feature constructor")
        return dict(self.attributes)[name]


@dataclass(frozen=True)
class Scene:
    entities: tuple[Entity,...]

    def __post_init__(self):
        if (not self.entities or len(self.entities)>120 or
                len(set(e.key for e in self.entities))!=len(self.entities)):
            raise ValueError("bounded uniquely keyed entity set required")

    def features(self):
        return set.intersection(*(set(dict(e.attributes))
                                  for e in self.entities))


def _predicate(atom,entity,scene):
    kind,name,value=atom
    n=entity.attr(name)
    if kind=="eq":return n==value
    if kind=="le":return n<=value
    if kind=="ge":return n>=value
    values=[e.attr(name) for e in scene.entities]
    if kind=="min":return n==min(values)
    if kind=="max":return n==max(values)
    if kind=="ltmax":return n<max(values)
    if kind=="gtmin":return n>min(values)
    raise ValueError("unrecognized learned predicate")


def _rhs(expr,entity,scene):
    kind=expr[0]
    if kind=="literal":return expr[1]
    if kind=="affine":return expr[1]*entity.value+expr[2]
    if kind=="affine_feature":
        return expr[2]*entity.attr(expr[1])+expr[3]
    if kind=="scene_min":
        return min(e.attr(expr[1]) for e in scene.entities)
    if kind=="scene_max":
        return max(e.attr(expr[1]) for e in scene.entities)
    if kind=="role":
        feature,rank=expr[1],expr[2]
        ordered=sorted(scene.entities,
                       key=lambda e:(e.attr(feature),repr(e.key)))
        return ordered[0].value if rank=="min" else ordered[-1].value
    raise ValueError("unrecognized learned output expression")


@dataclass(frozen=True)
class InventedRelationalProgram:
    clauses: tuple[tuple[tuple,...],...]
    result: tuple

    @property
    def ast(self):
        return ("parallel_relational_edit",
                ("induced_predicate",self.clauses),
                ("induced_output_expression",self.result))

    def apply(self,scene):
        out={}
        for e in scene.entities:
            selected=any(all(_predicate(a,e,scene) for a in clause)
                         for clause in self.clauses)
            out[e.key]=_rhs(self.result,e,scene) if selected else e.value
        return out


@dataclass(frozen=True)
class Discovery:
    program: InventedRelationalProgram|None
    source_checked: int
    clauses_tested: int
    source_ms: float
    status: str="ABSTAIN_UNSUPPORTED"
    classical: Callable|None=None

    def apply(self,scene):
        if self.status=="CLASSICAL_VERIFIED" and self.classical is not None:
            return self.classical(scene)
        if self.status not in ("SOURCE_VERIFIED_INVENTION",
                               "SOURCE_VERIFIED_REUSED_PROGRAM") or self.program is None:
            raise ValueError("abstain without source verification")
        return self.program.apply(scene)


class DomainIndependentRuleInventor:
    """Learn typed operations without task names, then fail closed on checks."""

    def __init__(self,*,max_ms=750,max_atoms=500,max_pairs=80000,
                 feature_depth=1):
        if not (1<=max_ms<=120000 and 1<=max_atoms<=10000 and
                1<=max_pairs<=1000000 and feature_depth in (0,1)):
            raise ValueError("finite search budget required")
        self.max_ms=max_ms
        self.max_atoms=max_atoms
        self.max_pairs=max_pairs
        self.feature_depth=feature_depth

    def invent(self,train,*,verification,classical_solvers=(),
               known_programs=()):
        start=perf_counter_ns()
        if len(train)<2 or not verification:
            raise ValueError("2 source pairs and independent checks required")
        pairs=tuple(train)+tuple(verification)
        if len({repr(x) for x,y in pairs})!=len(pairs):
            raise ValueError("source verifier must not repeat training input")
        for scene,target in pairs:
            if (not isinstance(scene,Scene) or
                    set(target)!=set(e.key for e in scene.entities) or
                    any(type(v) is not int for v in target.values())):
                raise ValueError("typed target must align with source entities")
        # Preserve the user contract: already classically solved = no invention.
        for known in classical_solvers:
            if all(known(scene)==target for scene,target in pairs):
                return Discovery(None,len(pairs),0,
                                 (perf_counter_ns()-start)/1e6,
                                 "CLASSICAL_VERIFIED",known)
        # Prior inventions are real executable syntax, not an answer cache.
        # Every remembered program must pass THIS new task's source examples
        # and independent verifier before it can run on a target input.
        for program in known_programs:
            if not isinstance(program,InventedRelationalProgram):
                raise TypeError("only typed executable laws can be remembered")
            try:
                if all(program.apply(scene)==target for scene,target in pairs):
                    return Discovery(program,len(pairs),0,
                                     (perf_counter_ns()-start)/1e6,
                                     "SOURCE_VERIFIED_REUSED_PROGRAM")
            except (ValueError,KeyError,TypeError):
                continue
        rows=[]
        features=None
        for scene,target in train:
            features=(scene.features() if features is None
                      else features & scene.features())
            for e in scene.entities:
                rows.append((scene,e,target[e.key],target[e.key]!=e.value))
        mask=sum(1<<i for i,row in enumerate(rows) if row[3])
        negative=((1<<len(rows))-1)^mask
        if not mask or not negative or not features:
            return Discovery(None,len(pairs),0,(perf_counter_ns()-start)/1e6)
        deadline=start+int(self.max_ms*1e6)
        if self.feature_depth:
            base=sorted(features)
            for a in base:
                for b in base:
                    if a==b:continue
                    for op in ("sub","add","abs_sub","mul"):
                        features.add((op,a,b))
        atoms=[]
        for name in sorted(features,key=repr):
            vals=sorted({e.attr(name) for scene,e,_,flag in rows})
            atoms.extend((kind,name,None)
                         for kind in ("min","max","ltmax","gtmin"))
            for v in vals:
                atoms.extend((kind,name,v) for kind in ("eq","le","ge"))
        atoms=atoms[:self.max_atoms]
        cover=[]
        for atom in atoms:
            positive=unwanted=0
            for i,(scene,e,y,changed) in enumerate(rows):
                if _predicate(atom,e,scene):
                    if changed:positive|=1<<i
                    else:unwanted|=1<<i
            if positive:cover.append((atom,positive,unwanted))

        # The FIRST changed source row uniquely fixes every possible
        # affine offset. Do not enumerate redundant constant hypotheses
        # from every later source observation.
        seed_scene,seed_entity,seed_target,_=next(
            row for row in rows if row[3])
        expressions=[("literal",seed_target)]
        for a in (-3,-2,-1,0,1,2,3):
            b=seed_target-a*seed_entity.value
            if abs(b)<=32:expressions.append(("affine",a,b))
            for name in features:
                b=seed_target-a*seed_entity.attr(name)
                if abs(b)<=32:
                    expressions.append(("affine_feature",name,a,b))
        for name in sorted(features,key=repr):
            expressions.extend((("scene_min",name),("scene_max",name),
                                ("role",name,"min"),("role",name,"max")))
        expressions=sorted(set(expressions),key=lambda x:(
            x[0]!="role",x[0]!="affine",len(x),repr(x)))
        candidates=[expr for expr in expressions if all(
            _rhs(expr,e,scene)==target
            for scene,e,target,changed in rows if changed)]
        if not candidates:
            return Discovery(None,len(pairs),0,(perf_counter_ns()-start)/1e6)

        safe=[];checked=0
        for atom,positive,unwanted in cover:
            checked+=1
            if unwanted==0:
                safe.append(((atom,),positive))
                # Complete one-clause witnesses must precede pair search.
                if positive==mask:
                    for expression in candidates:
                        program=InventedRelationalProgram(((atom,),),
                                                          expression)
                        if all(program.apply(scene)==target
                               for scene,target in verification):
                            return Discovery(program,len(pairs),checked,
                                (perf_counter_ns()-start)/1e6,
                                "SOURCE_VERIFIED_INVENTION")
        for (a,ay,an),(b,by,bn) in combinations(cover,2):
            if perf_counter_ns()>deadline or checked>=self.max_pairs:
                break
            checked+=1
            if ay&by and not(an&bn):
                safe.append(((a,b),ay&by))
        dnfs=[(clause,) for clause,covered in safe if covered==mask]
        if not dnfs:
            for i,(clause,m) in enumerate(safe):
                if perf_counter_ns()>deadline:break
                for other,n in safe[i+1:]:
                    if m|n==mask:
                        dnfs.append((clause,other))
                        if len(dnfs)>=100:break
                if len(dnfs)>=100:break
        for dnf in dnfs:
            if perf_counter_ns()>deadline:break
            for expression in candidates:
                program=InventedRelationalProgram(tuple(dnf),expression)
                if all(program.apply(scene)==target for scene,target in verification):
                    return Discovery(program,len(pairs),checked,
                                     (perf_counter_ns()-start)/1e6,
                                     "SOURCE_VERIFIED_INVENTION")
        return Discovery(None,len(pairs),checked,
                         (perf_counter_ns()-start)/1e6)
