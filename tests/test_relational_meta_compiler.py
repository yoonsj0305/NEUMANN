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
