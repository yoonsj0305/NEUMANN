"""Q3/Q6: one unchanged source-only meta-compiler across three semantic types.

SELF-AUTHORED typed benchmark cases. Pass does NOT establish frontier level,
unrestricted new grammar or genuine independent-author mathematical transfer.
"""
from random import Random
import pytest
from neumann1.relational_meta_compiler import Entity,Scene,DomainIndependentRuleInventor


def numeric(seed):
    rng=Random(seed)
    values=[-1,-2,-3,rng.randint(-8,-4),rng.randint(1,7),rng.randint(2,9)]
    rng.shuffle(values)
    x=Scene(tuple(Entity.from_attrs(i,{"reading":v,"slot":i},v)
                  for i,v in enumerate(values)))
    return x,{i:abs(v) for i,v in enumerate(values)}


def graph(seed):
    rng=Random(seed)
    pivot=rng.choice((0,1,2))
    degree={pivot:4,(pivot+1)%4:2,(pivot+2)%4:1,(pivot+3)%4:1}
    entities=[];answer={}
    for src in range(4):
        for dst in range(degree[src]):
            v=rng.randint(-8,8)
            key=(src,dst)
            entities.append(Entity.from_attrs(
                key,{"outdegree":degree[src],"destination":dst},v))
            answer[key]=v+3 if degree[src]==4 else v
    return Scene(tuple(entities)),answer


def spatial(seed):
    rng=Random(seed)
    colors=rng.sample(range(1,10),4)
    areas=(1,1,2,4)
    entities=[Entity.from_attrs(i,{"area":area,"x":i+seed%3},c)
              for i,(c,area) in enumerate(zip(colors,areas))]
    answer={i:colors[3] if area==1 else c
            for i,(c,area) in enumerate(zip(colors,areas))}
    return Scene(tuple(entities)),answer


@pytest.mark.parametrize("generator,semantic_atom",[
    (numeric,("le","reading",-1)),
    (graph,("max","outdegree",None)),
    (spatial,("min","area",None)),
])
def test_source_generated_rules_on_three_distinct_record_semantics(
        generator,semantic_atom):
    train=[generator(s) for s in (1,11,23,31,37)]
    source_verifier=[generator(s) for s in (41,47,53,59)]
    solver=DomainIndependentRuleInventor()
    method=solver.invent(train,verification=source_verifier)
    assert method.status=="SOURCE_VERIFIED_INVENTION"
    assert method.program.ast[0]=="parallel_relational_edit"
    assert any(semantic_atom==atom
               for clause in method.program.clauses for atom in clause)
    assert method.source_checked==9
    assert sum(method.apply(generator(s)[0])==generator(s)[1]
               for s in range(100,200))==100


@pytest.mark.parametrize("generator",(numeric,graph,spatial))
def test_strong_classical_solution_preempts_entire_invention_search(generator):
    train=[generator(s) for s in (1,11,23,31,37)]
    checks=[generator(s) for s in (41,47,53,59)]
    def specialist(scene):
        if generator is numeric:
            return {e.key:abs(e.value) for e in scene.entities}
        if generator is graph:
            return {e.key:e.value+(3 if e.attr("outdegree")==4 else 0)
                    for e in scene.entities}
        max_area=max(scene.entities,key=lambda e:e.attr("area"))
        return {e.key:max_area.value if e.attr("area")==1 else e.value
                for e in scene.entities}
    r=DomainIndependentRuleInventor().invent(
        train,verification=checks,classical_solvers=(specialist,))
    assert r.status=="CLASSICAL_VERIFIED"
    assert r.clauses_tested==0
    assert r.program is None
    assert r.apply(generator(333)[0])==generator(333)[1]


def test_source_counterexample_must_abstain():
    train=[numeric(i) for i in (1,11,23)]
    scene,target=numeric(41)
    false=dict(target);false[0]+=999
    out=DomainIndependentRuleInventor().invent(
        train,verification=[(scene,false)])
    assert out.status=="ABSTAIN_UNSUPPORTED"
    with pytest.raises(ValueError):
        out.apply(scene)


def test_topology_changing_outputs_are_not_falsely_claimed():
    scene,target=graph(1)
    wrong=dict(target);wrong["added_node"]=4
    with pytest.raises(ValueError):
        DomainIndependentRuleInventor().invent(
            [graph(1),graph(2)],verification=[(scene,wrong)])


def test_source_verifier_must_not_repeat_train():
    train=[graph(1),graph(2)]
    with pytest.raises(ValueError):
        DomainIndependentRuleInventor().invent(
            train,verification=train[:1])


def test_unseen_one_point_exception_blocks_unrestricted_proof():
    train=[numeric(i) for i in (1,11,23)]
    verification=[numeric(i) for i in (41,47)]
    r=DomainIndependentRuleInventor().invent(train,verification=verification)
    assert r.status=="SOURCE_VERIFIED_INVENTION"
    scene,original=numeric(500)
    exceptional=dict(original);exceptional[0]+=1
    assert r.apply(scene)!=exceptional
    assert all(r.apply(x)==y for x,y in train+verification)



@pytest.mark.parametrize("engine_factory",[
    lambda: __import__("neumann1",fromlist=["NeumannEngine"]).NeumannEngine(None,[],None),
    lambda: __import__("neumann1",fromlist=["RegistryEngine"]).RegistryEngine(None,None),
])
def test_live_engine_invents_and_reuses_generalized_program_syntax(engine_factory):
    engine=engine_factory()
    first=engine.invent_typed_relational_method(
        [numeric(i) for i in (1,11,23,31,37)],
        [numeric(i) for i in (41,47,53,59)])
    assert first.status=="SOURCE_VERIFIED_INVENTION"
    assert len(engine._q3_typed_methods)==1

    # New source history but the same learned program. No answer cache.
    reused=engine.invent_typed_relational_method(
        [numeric(i) for i in (201,211,223)],
        [numeric(i) for i in (241,247)])
    assert reused.status=="SOURCE_VERIFIED_REUSED_PROGRAM"
    assert reused.clauses_tested==0
    assert all(reused.apply(numeric(s)[0])==numeric(s)[1]
               for s in range(301,341))

    # Different attribute names and underlying relational semantics.
    # Old numeric method is invalid, so the same controller must discover
    # an entirely new graph law instead of silently transplanting it.
    different=engine.invent_typed_relational_method(
        [graph(i) for i in (1,11,23,31,37)],
        [graph(i) for i in (41,47,53,59)])
    assert different.status=="SOURCE_VERIFIED_INVENTION"
    assert len(engine._q3_typed_methods)==2
    spatial_result=engine.invent_typed_relational_method(
        [spatial(i) for i in (1,11,23,31,37)],
        [spatial(i) for i in (41,47,53,59)])
    assert spatial_result.status=="SOURCE_VERIFIED_INVENTION"
    assert len(engine._q3_typed_methods)==3
    assert spatial_result.apply(spatial(99)[0])==spatial(99)[1]



def derived_feature_source(seed,keys=("reading","reference")):
    """A two-feature inequality whose boundary cannot be expressed by
    the old <=2-clause axis-aligned predicate language on the entire source.
    The *new* feature grammar invents an AST for feature_a-feature_b.
    """
    rng=Random(seed)
    coordinates=[(a,b) for a in range(1,10) for b in range(1,10)]
    rng.shuffle(coordinates)
    field_a,field_b=keys
    entities=[]
    target={}
    for i,(a,b) in enumerate(coordinates):
        current=rng.randint(-6,8)
        entities.append(Entity.from_attrs(
            i,{field_a:a,field_b:b},current))
        target[i]=current+2 if a>b else current
    return Scene(tuple(entities)),target


@pytest.mark.parametrize("attributes",(
    ("reading","reference"),
    ("outdegree_src","outdegree_dst"),
    ("width","height"),
))
def test_new_feature_grammar_closes_an_original_relational_capability_gap(attributes):
    train=[derived_feature_source(i,attributes)
           for i in (1,11,23,31,37)]
    checks=[derived_feature_source(i,attributes)
            for i in (41,47,53)]
    # The previous grammar can use existing features only.
    original=DomainIndependentRuleInventor(
        max_ms=1000,max_atoms=1000,
        feature_depth=0).invent(train,verification=checks)
    assert original.status=="ABSTAIN_UNSUPPORTED"
    # A single unchanged construction rule creates an executable
    # feature difference, rank predicate and output algebra in ALL
    # three source schemas without domain labels.
    invented=DomainIndependentRuleInventor(
        max_ms=10000,max_atoms=1600,
        feature_depth=1).invent(train,verification=checks)
    assert invented.status=="SOURCE_VERIFIED_INVENTION"
    assert invented.program is not None
    assert any(isinstance(atom[1],tuple)
               for clause in invented.program.clauses for atom in clause)
    assert invented.clauses_tested<600
    assert all(invented.apply(derived_feature_source(i,attributes)[0])==
               derived_feature_source(i,attributes)[1]
               for i in range(100,200))


def test_derived_feature_classical_specialist_still_blocks_reinvention():
    source=[derived_feature_source(i) for i in (1,11,23,31,37)]
    check=[derived_feature_source(i) for i in (41,47,53)]
    def classical(scene):
        return {e.key:e.value+2 if
                e.attr("reading")>e.attr("reference") else e.value
                for e in scene.entities}
    r=DomainIndependentRuleInventor(
        feature_depth=1).invent(
        source,verification=check,classical_solvers=(classical,))
    assert r.status=="CLASSICAL_VERIFIED"
    assert r.clauses_tested==0
    assert r.apply(derived_feature_source(900)[0])==derived_feature_source(900)[1]
