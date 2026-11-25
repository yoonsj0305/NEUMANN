"""Reproducible synthetic FIRST: active law proposals and source-query budgets.

The source oracle is accessible to the synthesizer only during discovery;
after freeze, the benchmark evaluator scores pairs that were NEVER queried.
The same author wrote both synthesis benchmark and test oracles. Therefore
this is NOT independent-author or frontier benchmark evidence.
"""
from __future__ import annotations
import itertools
import json
from random import Random
from pathlib import Path
from neumann1.active_law_inventor import invent_with_oracle, EvidenceInsufficient


def cycle(n=31):
    xs=list(range(n)); Random(887).shuffle(xs)
    ix={v:i for i,v in enumerate(xs)}
    return xs, lambda a,b:xs[(ix[a]+ix[b])%n]


def s3z(n=5):
    ps=list(itertools.permutations(range(3)))
    xs=[(p,i) for p in ps for i in range(n)]
    Random(456).shuffle(xs)
    return xs,lambda a,b:(tuple(a[0][b[0][i]] for i in range(3)),(a[1]+b[1])%n)


def noninvertible(n=7):
    e=(0,1,2); g1=(1,2,0); g2=(0,0,0)
    compose=lambda a,b:tuple(a[b[i]] for i in range(3))
    seen={e};pending=[e]
    while pending:
        x=pending.pop()
        for gen in (g1,g2):
            y=compose(gen,x)
            if y not in seen:
                seen.add(y);pending.append(y)
    xs=[(a,i) for a in seen for i in range(n)]
    Random(444).shuffle(xs)
    return xs,lambda a,b:(compose(a[0],b[0]),(a[1]+b[1])%n)


def join():
    xs=list(range(32));Random(77).shuffle(xs)
    return xs,lambda a,b:a|b


def strings():
    xs=['']
    for length in range(4):
        xs.extend([x+c for x in (s for s in xs if len(s)==length) for c in 'ab'])
    Random(88).shuffle(xs)
    return xs,lambda a,b:(a+b)[:4]


def main():
    suites=[('cyclic_group',cycle,450),('noncommutative_group',s3z,700),
            ('noninvertible_monoid',noninvertible,1000),
            ('union_semilattice',join,800),('bounded_string_concat',strings,850)]
    results=[]
    for name,maker,budget in suites:
        xs,op=maker();size=len(xs)
        correct=queried=withheld=success=abstain=0
        for seed in range(30):
            try:
                model=invent_with_oracle(xs,op,budget=budget,seed=seed,
                                         law_assignments=5,validation=12)
            except EvidenceInsufficient:
                abstain+=1
                continue
            observed={(a,b) for a,b,_ in model.source_facts}
            heldout=[(a,b) for a in xs for b in xs if (a,b) not in observed]
            correct+=sum(model.apply(a,b)==op(a,b) for a,b in heldout)
            withheld+=len(heldout)
            queried+=len(observed)
            success+=1
        results.append({'family':name,'domain_size':size,'runs':30,
                        'source_query_budget_per_run':budget,'accepted':success,
                        'abstained':abstain,'source_queries':queried,
                        'original_unqueried_pairs':withheld,
                        'exact_unqueried_pairs':correct,
                        'full_table_source_queries_for_30_runs':30*size*size})
    xs,op=cycle();clean=invent_with_oracle(xs,op,budget=450,seed=0,
                                             validation=12)
    seen={(a,b) for a,b,_ in clean.source_facts}
    pair=next((a,b) for a,b in itertools.product(xs,repeat=2)
              if (a,b) not in seen)
    order={x:i for i,x in enumerate(xs)}
    adversarial_answer=xs[(order[op(*pair)]+1)%len(xs)]
    imposter=lambda a,b:adversarial_answer if (a,b)==pair else op(a,b)
    false_friend=invent_with_oracle(xs,imposter,budget=450,seed=0,validation=12)
    bad_cell_unseen=pair not in {(a,b) for a,b,_ in false_friend.source_facts}
    wrong=bad_cell_unseen and false_friend.apply(*pair)!=imposter(*pair)
    assert all(x['exact_unqueried_pairs']==x['original_unqueried_pairs']
               for x in results)
    assert all(x['accepted']==30 and x['abstained']==0 for x in results)
    assert wrong, 'counterexample must remain detectable in independent audit'
    totals={'accepted':sum(x['accepted'] for x in results),
            'source_queries':sum(x['source_queries'] for x in results),
            'unqueried':sum(x['original_unqueried_pairs'] for x in results),
            'correct':sum(x['exact_unqueried_pairs'] for x in results),
            'full_table_source_queries':sum(x['full_table_source_queries_for_30_runs']
                                            for x in results)}
    report={'schema':'NEUMANN.Q3.active-law-source-query-FIRST.v1',
            'date':'2026-11-08','results':results,'totals':totals,
            'counterexample':{'one_cell_nonassociative_false_friend_accepted':True,
                              'wrong_unqueried_prediction':wrong},
            'limitations':['synthetic author-programmed oracles',
                           'all five families share associativity + identity',
                           'discovered laws empirical, not independently proved',
                           'relabeling seeds are not independent math domains',
                           'query savings not CPU or frontier efficiency',
                           'cannot claim global Q3, Q4 or Q6']}
    output=Path(__file__).with_name('q3_active_law_first_result.json')
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    main()
