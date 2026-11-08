"""Q3 learned grammar must be generated from source I/O and reused across types."""
from __future__ import annotations
from neumann1 import NeumannEngine, RegistryEngine
from neumann1.induced_grammar import GrammarInventor, eval_ast, antiunify, freeze
from research.q3.q3_induced_grammar_development import source, target, main


def trained():
    g=GrammarInventor(max_cost=4)
    for name,examples,f in source:
        r=g.invent_from_source(name,[(x,f(x)) for x in examples])
        assert r.solved
    return g


def test_induce_not_hardcode_three_new_executable_grammar_rules():
    g=trained()
    assert len(g.productions)==3
    assert ('call','sum',('map',('fn_hole','MAP'),('hole','ARG'))) in [
        p.template for p in g.productions]
    p=next(p for p in g.productions if p.template==
           ('call','sum',('map',('fn_hole','MAP'),('hole','ARG'))))
    generated=tuple(p.instantiate(('call','flatten',('input',))))
    assert ('call','sum',('map','inc',('call','flatten',('input',)))) in generated


def test_no_family_routing_and_genuine_type_crossing():
    g=trained()
    for i,(name,gen,f) in enumerate(target):
        train=gen(600+i*29,7)
        result=g.solve([(x,f(x)) for x in train])
        assert result.solved,name
        assert all(eval_ast(result.expression,x)==freeze(f(x))
                   for x in gen(700+i*29,30)),name


def test_new_grammar_improves_search_checks_with_equal_expressivity():
    g=trained()
    name,gen,f=target[0]
    examples=[(x,f(x)) for x in gen(600,7)]
    a=g.solve(examples,learned=True)
    b=g.solve(examples,learned=False)
    assert a.solved and b.solved and a.checked<b.checked
    assert a.used_invented_production


def test_metagrammar_abstains_if_source_solutions_structurally_unrelated():
    assert antiunify(('call','length',('hole','ARG')),
                     ('map','square',('hole','ARG'))) is None


def test_no_false_global_guarantee_from_finite_examples():
    g=GrammarInventor(max_cost=2)
    f=lambda x:x.lower() if x!='never_seen!' else 'unpredictable'
    r=g.solve([(x,f(x)) for x in [' Ab ', ' xY ', ' Hi ', 'A  ']])
    assert r.solved
    assert eval_ast(r.expression,'never_seen!')!=f('never_seen!')


def test_unsupported_graph_connectivity_fails_closed():
    g=GrammarInventor(max_cost=4)
    examples=[(((0,1,0),(1,0,0),(0,0,0)),2),
              (((0,1,1),(1,0,0),(1,0,0)),1),
              (((0,0,0),(0,0,0),(0,0,0)),3),
              (((0,1,0),(1,0,1),(0,1,0)),1)]
    assert not g.solve(examples).solved


def test_live_engines_keep_their_own_learned_grammar():
    for engine in (NeumannEngine(None,[],None),RegistryEngine(None,None)):
        for name,examples,f in source:
            assert engine.learn_invention_grammar(
                name,[(x,f(x)) for x in examples]).solved
        assert len(engine.invention_grammar_rules())==3
        name,gen,f=target[0]
        assert engine.synthesize_with_invented_grammar([
            (x,f(x)) for x in gen(600,7)]).solved


def test_replay_both_classical_and_invented_grammars():
    r=main()
    s=r['summary']
    assert s['source_candidate_checks']==251
    assert s['target_candidate_checks_invented'] == 596
    assert s['target_candidate_checks_cold'] == 1108
    assert s['correct_invented']==s['correct_cold']==1080
