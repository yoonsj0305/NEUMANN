"""Q3: learn, revise, then freeze a DISCOVERY METHOD on unrelated backends."""
from itertools import combinations
from random import Random
import pytest
from neumann1.recursive_method_discovery import (
    MetaCase,ObservedOracle,RecursiveMethodInventor,execute,
    RecursiveMethod,InsufficientEvidence)
from research.q3.meta_domain_adapters import (
    BooleanPolynomialBackend,PeriodicProcessBackend)


def poly_oracle(seed,degree=3,width=10):
    rng=Random(seed)
    terms=set()
    while len(terms)<5:
        terms.add(tuple(sorted(rng.sample(range(width),degree))))
    def f(x):
        return sum(all(x[j] for j in term) for term in terms)&1
    return f


def period_oracle(seed,period):
    rng=Random(seed)
    while True:
        pattern=tuple(rng.getrandbits(1) for _ in range(period))
        if all(any(pattern[i]!=pattern[i%k] for i in range(period))
               for k in range(1,period)):
            return lambda t,p=pattern:p[t%len(p)]


def case(family,seed,complexity,*,width=10):
    if family=="boolean":
        oracle=poly_oracle(seed,complexity,width)
        pool=[j for j in range(1<<width) if j.bit_count()>5]
        heldout=tuple(tuple((i>>j)&1 for j in range(width))
                      for i in Random(seed+12345).sample(pool,80))
        def factory(ledger):
            return BooleanPolynomialBackend(width,ledger,seed+900)
    else:
        oracle=period_oracle(seed,complexity)
        heldout=tuple(range(300,400))
        def factory(ledger):
            return PeriodicProcessBackend(ledger,seed+900)
    return MetaCase(family,factory,oracle,heldout)


def run(policy,cases):
    result=[]
    for c in cases:
        src=ObservedOracle(c.oracle,c.heldout)
        solved=execute(policy,c.backend_factory(src))
        right=(solved.model is not None and
               all(solved.apply(x)==c.oracle(x) for x in c.heldout))
        result.append((bool(right),solved.source_queries,solved.trace))
    return result


def studies():
    train=tuple(case("boolean",i+3000,3)
                for i in range(12))+tuple(
          case("period",i+700,3) for i in range(12))
    feedback=tuple(case("boolean",i+80000,4+i%2)
                   for i in range(15))
    inventor=RecursiveMethodInventor(
        max_complexity=9,challenges=(4,8,16,32,64,96))
    return train,feedback,inventor


def test_meta_policy_is_rewritten_by_real_source_counterexamples():
    train,feedback,inventor=studies()
    first=inventor.learn(train)
    assert first.correct_on_meta_training==24
    assert first.incorrect_on_meta_training==0
    assert first.method.ast[0]=="repeat"
    assert first.method.challenges==16
    assert first.method.transition==("increment",2)
    failure=run(first.method,feedback)
    assert sum(r[0] for r in failure)<15
    revised=inventor.learn(train+feedback)
    assert revised.correct_on_meta_training==39
    assert revised.incorrect_on_meta_training==0
    assert revised.method.ast!=first.method.ast
    assert revised.method.challenges==64
    assert revised.method.transition==("increment",1)
    assert revised.training_work_units>0
    assert revised.method.transition==("increment",1)
    assert revised.training_cost_queries>0
    assert revised.grade_label_cost==3360


def test_same_frozen_meta_ast_solves_new_polynomials_and_periodic_sequences():
    train,feedback,inventor=studies()
    revised=inventor.learn(train+feedback)
    unseen=tuple(case("boolean",i+60000,4+i%2)
                 for i in range(40))+tuple(
        case("period",i+70000,7+2*(i%2))
        for i in range(40))
    outcomes=run(revised.method,unseen)
    assert sum(r[0] for r in outcomes[:40])==40
    assert sum(r[0] for r in outcomes[40:])==40


def test_new_recursion_extends_to_unseen_input_widths_without_refitting():
    train,feedback,inventor=studies()
    revised=inventor.learn(train+feedback)
    wider=tuple(case("boolean",i+90000,4+i%2,width=11+i%2)
                for i in range(20))
    results=run(revised.method,wider)
    assert sum(r[0] for r in results)==20,results


def test_strong_classical_bypass_skips_all_invented_method_stages():
    f=lambda x:x[0]^x[1]
    model=RecursiveMethod(("increment",1),64,9)
    ledger=ObservedOracle(f)
    backend=BooleanPolynomialBackend(10,ledger,72)
    probes=[tuple((i>>j)&1 for j in range(10))
            for i in range(24)]
    result=execute(model,backend,known_classical=(f,),
                   classical_probe_inputs=probes)
    assert result.status=="CLASSICAL_SOURCE_VERIFIED"
    assert result.trace==(("CLASSICAL","SOURCE_VERIFIED"),)
    assert result.source_queries==24


def test_forbidden_target_source_queries_abstain_and_no_false_success():
    f=poly_oracle(89,2)
    forbidden=(tuple(0 for _ in range(10)),)
    ledger=ObservedOracle(f,forbidden)
    backend=BooleanPolynomialBackend(10,ledger,2)
    outcome=execute(RecursiveMethod(("increment",1),8,9),backend)
    assert outcome.status=="ABSTAIN_SOURCE_LIMIT"
    assert outcome.model is None
    with pytest.raises(InsufficientEvidence):
        outcome.apply(tuple(0 for _ in range(10)))


def test_invalid_discovery_method_guard_rejects_infinite_or_nonprogressing_loop():
    f=period_oracle(7,3)
    for method in (
        RecursiveMethod(("increment",0),8,9),
        RecursiveMethod(("multiply",1),8,9),
    ):
        backend=PeriodicProcessBackend(ObservedOracle(f),91)
        # These contracts are required to fail if the first stage refutes.
        with pytest.raises(InsufficientEvidence):
            execute(method,backend)


@pytest.mark.parametrize("engine_type",["NeumannEngine","RegistryEngine"])
def test_live_engines_self_rewrite_method_then_transfer_without_new_solvers(
        engine_type):
    from neumann1 import NeumannEngine,RegistryEngine
    engine=(NeumannEngine(None,[],None) if engine_type=="NeumannEngine"
            else RegistryEngine(None,None))
    train,feedback,_=studies()
    first=engine.meta_learn_recursive_discovery_method(train)
    assert first.method.challenges==16
    assert first.method.transition==("increment",2)
    revision=engine.meta_revise_recursive_discovery_method(feedback)
    assert revision.method.challenges==64
    assert revision.method.ast!=first.method.ast
    unseen=case("period",700009,9)
    run=engine.meta_execute_recursive_discovery_method(
        unseen.backend_factory(
            ObservedOracle(unseen.oracle,unseen.heldout)))
    assert run.status=="SOURCE_VERIFIED"
    assert all(run.apply(t)==unseen.oracle(t)
               for t in unseen.heldout)
    # Already verified classical algorithms bypass both source-invented
    # feature generation and the learned conditional meta search.
    classical=case("boolean",201,2)
    backend=classical.backend_factory(
        ObservedOracle(classical.oracle,classical.heldout))
    probes=[tuple((i>>j)&1 for j in range(10)) for i in range(24)]
    bypass=engine.meta_execute_recursive_discovery_method(
        backend,known_classical=(classical.oracle,),
        classical_probe_inputs=probes)
    assert bypass.status=="CLASSICAL_SOURCE_VERIFIED"
    with pytest.raises(ValueError):
        engine.meta_revise_recursive_discovery_method(
            tuple(case("boolean",i+400,1) for i in range(2)))
