"""Real Q3 production CEGIS: generated SOURCE probes can rewrite a process AST.

Researcher-authored falsification example, not independent-author frontier proof.
No target terminal outputs or hidden state successors are supplied to invent().
"""
from neumann1 import NeumannEngine, RegistryEngine
from neumann1.active_terminal_process_inventor import (
    ActiveTerminalProcessInventor, _source_probe_pool)
from research.q3.q3_higher_order_method_blind import training


def _control(engine):
    a,b,c=training()
    engine.meta_learn_higher_order_method(a)
    engine.meta_revise_higher_order_method(b)
    method=engine.meta_revise_higher_order_method(c).program
    assert method.ast[0]=="while"
    assert "length" not in repr(method.ast)
    return method


SOURCE=tuple((x,0) for x in (0,1,2,3,5,8,13,17))
CHECKS=tuple((x,0) for x in (4,7,11,19))


def test_generic_experiment_compiler_finds_counterfactual_signed_inputs():
    probes, programs=_source_probe_pool(
        "int",tuple(x for x,_ in SOURCE),
        {x for x,_ in SOURCE+CHECKS},frozenset(),
        max_programs=512,max_probes=512)
    assert programs>10
    assert any(x<0 for x in probes)
    assert all(x not in {v for v,_ in SOURCE+CHECKS} for x in probes)


def test_active_source_falsification_rewrites_latent_process_ast():
    engine=NeumannEngine(None,[],None)
    _control(engine)
    old=engine.meta_invent_terminal_only_process(
        SOURCE,CHECKS,max_nodes=8,max_expressions=150000,
        max_source_ms=25000)
    assert old is not None
    assert old.compile().run(-7).value!= -7

    # Hidden SOURCE endpoint behavior keeps negative states fixed and
    # decreases positive states to zero.  Never provides state successors.
    oracle=lambda x:min(0,x)
    result=engine.meta_invent_active_terminal_process(
        SOURCE,CHECKS,oracle,max_nodes=8,max_expressions=150000,
        max_source_ms=25000,max_rounds=5,max_oracle_queries=160)
    assert result.status=="SOURCE_PROBE_CONSISTENT"
    assert result.program is not None
    assert len(result.revisions)>=1
    assert result.program.transition_ast!=old.transition_ast
    assert result.source_oracle_queries<=160
    for x in tuple(range(-24,0))+tuple(range(0,100)):
        execution=result.program.compile().run(x)
        assert execution.status=="HALT_CERTIFIED_FIXED_POINT"
        assert execution.value==oracle(x)


def test_classical_first_has_zero_new_oracle_queries():
    engine=RegistryEngine(None,None)
    _control(engine)
    result=engine.meta_invent_active_terminal_process(
        SOURCE,CHECKS,lambda x:0,known_classical=lambda x:0)
    assert result.status=="CLASSICAL_FIRST"
    assert result.program is None
    assert result.source_oracle_queries==0


def test_unexpressible_source_counterexample_abstains_instead_of_guessing():
    engine=RegistryEngine(None,None)
    control=_control(engine)
    result=ActiveTerminalProcessInventor(
        max_nodes=6,max_source_ms=6000,max_rounds=2,
        max_oracle_queries=32).discover(
            SOURCE,independent_terminal_checks=CHECKS,
            source_terminal_oracle=lambda x:99 if x<0 else 0,
            control=control)
    assert result.status in (
        "ABSTAIN_GRAMMAR_GAP","ABSTAIN_ORACLE_BUDGET",
        "ABSTAIN_REPAIR_BUDGET")
    assert result.program is None


def test_forbidden_target_input_is_never_probed():
    engine=NeumannEngine(None,[],None)
    control=_control(engine)
    forbidden=-17
    asked=[]
    def oracle(x):
        assert x!=forbidden
        asked.append(x)
        return min(x,0)
    result=ActiveTerminalProcessInventor(
        max_nodes=6,max_source_ms=6000,
        max_oracle_queries=24).discover(
            SOURCE,independent_terminal_checks=CHECKS,
            source_terminal_oracle=oracle,control=control,
            forbidden_target_inputs=(forbidden,))
    assert forbidden not in asked
    assert result.source_oracle_queries==len(asked)
