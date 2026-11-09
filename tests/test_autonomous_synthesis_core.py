"""NEUMANN live auto-synthesis: exercise normal production engine interfaces.

The original-verified classical solver is FIRST by default, never a hidden
reference oracle. Invented methods are considered on actual classical gaps or
measured positive source-only utility.
Every result must pass the caller's original obligation before promotion.
These checks distinguish behavior from benchmarking/general-intelligence claims.
"""
from itertools import product
from neumann1 import NeumannEngine, RegistryEngine, StructuralMetaInventor


def a(i):
    return ("arg",i)


def run(t,values):
    kind=t[0]
    if kind=="arg":return values[t[1]]
    if kind=="lit":return t[1]
    xs=[run(x,values) for x in t[1:]]
    if kind=="lt":return xs[0]<xs[1]
    if kind=="gt":return xs[0]>xs[1]
    if kind=="add":return xs[0]+xs[1]
    if kind=="ite":return xs[1] if xs[0] else xs[2]
    raise ValueError("unexpected operation")


def max_program(n):
    result=a(0)
    for i in range(1,n):
        new=a(i)
        result=("ite",("lt",result,new),new,result)
    return result


def min_program(n):
    result=a(0)
    for i in range(1,n):
        new=a(i)
        result=("ite",("lt",result,new),result,new)
    return result


def scan_program(n,k):
    result=("lit",0)
    for i in reversed(range(n-1)):
        pair=("add",a(i),a(i+1))
        result=("ite",("gt",pair,("lit",k)),pair,result)
    return result


def proves(expr,n,kind,k=None):
    if kind=="scan":
        alphabet=(-1,0,2,9,18)
    else:
        alphabet=(-3,0,2,7)
    for row in product(alphabet,repeat=n):
        if kind=="max":expected=max(row)
        elif kind=="min":expected=min(row)
        else:
            expected=next((row[i]+row[i+1] for i in range(n-1)
                           if row[i]+row[i+1]>k),0)
        if run(expr,row)!=expected:return False
    return True


def test_engine_automatically_bootstraps_two_sources_and_invents_next_method():
    eng=NeumannEngine(None,[],None)
    classical_calls=[]
    def cold(n,params):
        classical_calls.append(n)
        return max_program(n) if n <= 3 else None
    first=eng.synthesize_program("general.maximum",2,
        verify=lambda tree:proves(tree,2,"max"),classical=cold)
    second=eng.synthesize_program("general.maximum",3,
        verify=lambda tree:proves(tree,3,"max"),classical=cold)
    assert first["origin"]=="classical_verified_then_learned"
    assert second["origin"]=="classical_verified_then_learned"
    assert second["new_method_ids"]  # Source 2 and 3 induced a new program generator.
    assert classical_calls==[2,3]

    # Classical is tried FIRST; its explicit gap enables a new method.
    learned=eng.synthesize_program("general.maximum",4,
        verify=lambda tree:proves(tree,4,"max"),classical=cold)
    assert learned and learned["origin"]=="self_invented_method"
    assert learned["classical_invocations"]==1
    assert learned["method_queries"]>=1
    assert classical_calls==[2,3,4]
    assert learned["new_method_ids"]  # Self-generated solution learns new method.

    # Checkpoint the entire LEARNED METHOD LANGUAGE, then continue learning
    # through the other production engine.
    snap=eng.meta_inventor.checkpoint()
    restored=StructuralMetaInventor.from_checkpoint(snap)
    reg=RegistryEngine(None,None,meta_inventor=restored)
    result=reg.synthesize_program("general.maximum",5,
        verify=lambda tree:proves(tree,5,"max"),classical=cold)
    assert result and result["origin"]=="self_invented_method"
    assert classical_calls==[2,3,4,5]


def test_autonomous_new_family_first_hit_and_changed_threshold():
    engine=RegistryEngine(None,None)
    called=[]
    def cold(n,params):
        called.append((n,params))
        return scan_program(n,params[0]) if n <= 3 else None
    engine.synthesize_program("automatic.first_hit",2,params=(5,),
        verify=lambda t:proves(t,2,"scan",5),classical=cold)
    source=engine.synthesize_program("automatic.first_hit",3,params=(5,),
        verify=lambda t:proves(t,3,"scan",5),classical=cold)
    assert source["new_method_ids"]
    fresh=engine.synthesize_program("automatic.first_hit",4,params=(15,),
        verify=lambda t:proves(t,4,"scan",15),classical=cold)
    assert fresh and fresh["origin"]=="self_invented_method"
    assert fresh["classical_invocations"]==1
    assert fresh["method_queries"]>=1
    assert called==[(2,(5,)),(3,(5,)),(4,(15,))]


def test_failure_triggers_safe_degraded_classical_and_method_relearning():
    engine=NeumannEngine(None,[],None)
    for n in (2,3):
        r=engine.synthesize_program("changing.domain",n,
            verify=lambda t,n=n:proves(t,n,"max"),
            classical=lambda n,params:max_program(n))
        assert r and r["verified"]
    assert engine.meta_inventor.methods
    # The old max method is WRONG for the changed original MIN obligation.
    calls=[]
    def cold_min(n,params):
        calls.append(n)
        return min_program(n)
    repair=engine.synthesize_program("changing.domain",4,
        verify=lambda t:proves(t,4,"min"),classical=cold_min)
    assert repair and repair["origin"]=="classical_verified_then_learned"
    assert calls==[4]
    # Classical-first avoids wasting a candidate on an already solved task.
    assert all(m.failures==0 for m in engine.meta_inventor.methods.values())
    # In a genuine classical gap, the old MAX method is checked, rejected,
    # and cannot pollute the method memory for the changed MIN semantics.
    gap=engine.synthesize_program("changing.domain",5,
        verify=lambda t:proves(t,5,"min"),classical=lambda n,p:None)
    assert gap is None
    assert any(m.failures>=1 for m in engine.meta_inventor.methods.values())
    before=len(engine.meta_inventor.methods)
    repair2=engine.synthesize_program("changing.domain",5,
        verify=lambda t:proves(t,5,"min"),classical=cold_min)
    assert repair2 and repair2["verified"]
    assert len(engine.meta_inventor.methods)>=before
    # No source/target verifier -> no bogus success or hidden fallback call.
    assert engine.synthesize_program("changing.domain",6,
        classical=cold_min) is None
    assert calls==[4,5]


def test_invalid_classic_program_never_enters_method_memory():
    engine=NeumannEngine(None,[],None)
    wrong=engine.synthesize_program("invalid",2,
        verify=lambda t:proves(t,2,"max"),
        classical=lambda n,p:("lit",123))
    assert wrong is None
    assert not engine.meta_inventor.methods
    assert not engine.meta_inventor.observations
    # Unsupported index rejected before original verifier executes.
    wrong2=engine.synthesize_program("invalid",2,
        verify=lambda t:True,
        classical=lambda n,p:("arg",3))
    assert wrong2 is None
    assert not engine.meta_inventor.observations
