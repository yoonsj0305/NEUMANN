"""Q3 meta invention: generate new source-certified method constructors.

The source grammar supplies NAND and a one-bit fold schema, but neither a
specific Boolean base operator nor one of the 16 possible extension laws.
"""
from itertools import product
import pytest
from neumann1 import NeumannEngine, RegistryEngine
from neumann1.boolean_meta_inventor import invent_boolean_fold, InsufficientEvidence


def table_eval(table,a,b):
    return table[2*a+b]


def make_program(base, step):
    def oracle(bits):
        value=table_eval(base,*bits[:2])
        for bit in bits[2:]:
            value=table_eval(step,value,bit)
        return value
    return oracle


def only_nand_and_arg(expr):
    if expr[0]=="arg":
        assert expr[1] in (0,1)
        return
    assert expr[0]=="nand"
    only_nand_and_arg(expr[1])
    only_nand_and_arg(expr[2])


def test_all_224_discovered_methods_extrapolate_to_new_arities():
    solved=source=unseen=0
    for base_mask in range(16):
        base=tuple((base_mask>>i)&1 for i in range(4))
        if len(set(base))<2:
            continue
        for step_mask in range(16):
            step=tuple((step_mask>>i)&1 for i in range(4))
            oracle=make_program(base,step)
            method=invent_boolean_fold(oracle)
            assert method.base_table==base
            assert method.extension_table==step
            only_nand_and_arg(method.base_circuit)
            only_nand_and_arg(method.extension_circuit)
            assert method.source_observations==28
            for n in (5,6,7):
                for bits in product((0,1),repeat=n):
                    assert method.apply(bits)==oracle(bits)
                    unseen+=1
            source+=method.source_observations
            solved+=1
    assert solved==224 and source==6272 and unseen==50176


def test_runtime_invents_new_method_once_and_reuses_without_oracle():
    base=(0,1,1,0);step=(0,1,1,0)
    oracle=make_program(base,step)
    for engine in (NeumannEngine(None,[],None),RegistryEngine(None,None)):
        calls=[]
        def source(bits):
            calls.append(bits)
            assert len(bits)<=4
            return oracle(bits)
        learned=engine.learn_boolean_constructor(source)
        assert learned["new_constructor"]
        assert learned["source_query_count"]==28
        assert len(calls)==28
        before=len(calls)
        for n in (8,9):
            bits=(1,0,1,1,0,1,0,1,0)[:n]
            assert engine.execute_boolean_constructor(
                learned["method_id"],bits)==oracle(bits)
        assert len(calls)==before
        assert not engine.learn_boolean_constructor(source)["new_constructor"]


def test_falsify_nonfold_at_arity_3():
    base=(0,1,1,0)
    def nonfold(bits):
        if len(bits)==2:return table_eval(base,*bits)
        return bits[0]
    with pytest.raises(InsufficientEvidence,match="contradicted"):
        invent_boolean_fold(nonfold)


def test_falsify_arity_4_counterexample():
    original=make_program((0,1,1,0),(0,1,1,0))
    def altered(bits):
        return original(bits) ^ int(len(bits)==4 and bits==(1,1,1,1))
    with pytest.raises(InsufficientEvidence,match="falsified"):
        invent_boolean_fold(altered)


def test_budget_and_constant_base_fail_closed():
    original=make_program((0,1,1,0),(0,1,1,0))
    with pytest.raises(InsufficientEvidence,match="budget"):
        invent_boolean_fold(original,max_source_queries=27)
    with pytest.raises(InsufficientEvidence,match="both"):
        invent_boolean_fold(lambda bits:0)


def test_adversarial_target_exception_is_not_proven_away():
    oracle=make_program((0,1,1,0),(0,1,1,0))
    def altered(bits):
        return oracle(bits) ^ int(len(bits)==5 and bits==(1,1,1,1,1))
    method=invent_boolean_fold(altered)
    assert not method.unconditional_for_arbitrary_functions
    assert method.apply((1,1,1,1,1))!=altered((1,1,1,1,1))


def test_bad_type_and_missing_method_refused():
    with pytest.raises(InsufficientEvidence,match="Boolean"):
        invent_boolean_fold(lambda bits:0.1)
    with pytest.raises(InsufficientEvidence):
        invent_boolean_fold(lambda bits:False)
    engine=NeumannEngine(None,[],None)
    with pytest.raises(InsufficientEvidence,match="inventory"):
        engine.execute_boolean_constructor(((0,1,1,0),(0,1,1,0)),(1,0,1))
