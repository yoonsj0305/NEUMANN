"""Q3 source-frozen, multi-type grammar-induction vs equal-primitive cold synthesis.

Author-programmed tasks, not independent benchmark authors. The user-visible
metric is semantic candidate checks and source+target cost, NOT 10x compute.
"""
from __future__ import annotations
import json
from random import Random
from pathlib import Path
from neumann1.induced_grammar import GrammarInventor, eval_ast, freeze


def text(seed,size=7):
    r=Random(seed)
    return [''.join(r.choice('aBCxyYqz  ') for _ in range(r.randint(5,18)))
            for _ in range(size)]


def integer_list(seed,size=7):
    r=Random(seed)
    return [tuple(r.randint(-9,9) for _ in range(r.randint(5,12))) for _ in range(size)]


def edge_matrix(seed,size=7):
    r=Random(seed)
    return [tuple(tuple(r.randint(-5,5) for _ in range(4)) for _ in range(4))
            for _ in range(size)]


def positive_number(seed,size=7):
    r=Random(seed)
    return [r.randint(100000,999999) for _ in range(size)]


def uniq(x):
    return tuple(dict.fromkeys(x)) if isinstance(x,tuple) else ''.join(dict.fromkeys(x))


def sort(x):
    return tuple(sorted(x)) if isinstance(x,tuple) else ''.join(sorted(x))


def flatten(x):
    return tuple(y for row in x for y in row)


source=[
    ('strings_sorted_distinct',text(1),lambda x:sort(uniq(x))),
    ('integer_series_sorted_distinct',integer_list(3),lambda x:sort(uniq(x))),
    ('strings_distinct_count',text(6),lambda x:len(uniq(x))),
    ('sensor_series_distinct_count',integer_list(9),lambda x:len(uniq(x))),
    ('sensor_absolute_aggregate',integer_list(12,9),lambda x:sum(abs(v) for v in x)),
    ('signed_series_square_energy',integer_list(13,9),lambda x:sum(v*v for v in x)),
]

target=[
    ('graph_weight_absolute_sum',edge_matrix,lambda x:sum(abs(v) for v in flatten(x))),
    ('graph_incremented_edge_aggregate',edge_matrix,lambda x:sum(v+1 for v in flatten(x))),
    ('graph_distinct_weight_count',edge_matrix,lambda x:len(uniq(flatten(x)))),
    ('graph_sorted_distinct_weights',edge_matrix,lambda x:sort(uniq(flatten(x)))),
    ('numeric_digit_distinct_count',positive_number,lambda x:len(uniq(tuple(int(c) for c in str(x))))),
    ('text_sorted_unique_lowercase',text,lambda x:sort(uniq(x.lower()))),
    ('text_reverse_sorted_unique_lower',text,lambda x:sort(uniq(x.lower()))[::-1]),
    ('text_distinct_count_after_lower',text,lambda x:len(uniq(x.lower()))),
    ('sensor_unique_square_sum',integer_list,lambda x:sum(v*v for v in uniq(x))),
]


def main():
    inventor=GrammarInventor(max_cost=4,max_candidates=100000)
    sources=[]
    for i,(name,examples,f) in enumerate(source):
        # Fresh source-only oracle checks are disjoint from task training I/O
        generator=text if isinstance(examples[0],str) else integer_list
        source_validation=[(x,f(x)) for x in generator(1000+i,30)]
        r=inventor.invent_from_source(name,[(x,f(x)) for x in examples],
                                     verification_pairs=source_validation)
        sources.append({'name':name,'solved':r.solved,'checked':r.checked,
                        'expression':repr(r.expression)})
    productions=[{'template':repr(x.template),'support':x.source_tasks}
                 for x in inventor.productions]
    results=[]
    for i,(name,gen,reference) in enumerate(target):
        train=gen(600+i*29,7)
        seen={freeze(x) for x in train}
        held=[x for x in gen(700+i*29,120) if freeze(x) not in seen]
        examples=[(x,reference(x)) for x in train]
        learned=inventor.solve(examples,learned=True)
        cold=inventor.solve(examples,learned=False)
        results.append({
            'name':name,'train':len(train),'heldout':len(held),
            'with_grammar':{'solved':learned.solved,'checked':learned.checked,
                            'elapsed_ms':round(learned.elapsed_ms,4),
                            'used_new_rule':learned.used_invented_production,
                            'correct':sum(eval_ast(learned.expression,x)==freeze(reference(x))
                                          for x in held) if learned.solved else 0,
                            'program':repr(learned.expression)},
            'cold':{'solved':cold.solved,'checked':cold.checked,
                    'elapsed_ms':round(cold.elapsed_ms,4),
                    'correct':sum(eval_ast(cold.expression,x)==freeze(reference(x))
                                  for x in held) if cold.solved else 0,
                    'program':repr(cold.expression)},
        })
    summary={'source_verification_examples':180,'source_tasks':len(sources),'source_candidate_checks':sum(x['checked'] for x in sources),
             'induced_rules':len(productions),'target_tasks':len(results),
             'target_solved_invented':sum(x['with_grammar']['solved'] for x in results),
             'target_solved_cold':sum(x['cold']['solved'] for x in results),
             'target_using_new_rules':sum(x['with_grammar']['used_new_rule'] for x in results),
             'unseen_test_cases':sum(x['heldout'] for x in results),
             'correct_invented':sum(x['with_grammar']['correct'] for x in results),
             'correct_cold':sum(x['cold']['correct'] for x in results),
             'target_candidate_checks_invented':sum(x['with_grammar']['checked'] for x in results),
             'target_candidate_checks_cold':sum(x['cold']['checked'] for x in results)}
    assert summary['induced_rules']==3
    assert summary['target_solved_invented']==summary['target_solved_cold']==9
    assert summary['correct_invented']==summary['correct_cold']==summary['unseen_test_cases']==1080
    assert summary['target_candidate_checks_invented']==596
    assert summary['target_candidate_checks_cold']==1108
    report={'schema':'NEUMANN.Q3.induced-grammar.cross-type-development.v1',
            'source':sources,'productions':productions,'target':results,'summary':summary,
            'limits':['same-author constructed tasks and oracle functions',
                      'finite human-coded atomic and map DSL, not arbitrary invention language',
                      'semantic candidate count is not wall-clock/FLOP savings',
                      'uncertified extrapolation may overfit; nonexpressible graph algorithms abstain']}
    Path('research/q3/q3_induced_grammar_development_results.json').write_text(
        json.dumps(report,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    return report


if __name__=='__main__':main()
