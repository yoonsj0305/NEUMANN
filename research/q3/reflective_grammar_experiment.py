"""Q3 source-language freeze then new-family invention on synthetic development tasks.

All task-generator formulas reside ONLY in this evaluation script, not the
generically trained inventor. This is a deliberately SMALL development gate,
NOT independent evidence of universal inventive intelligence.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import random
import time

from research.q3.reflective_grammar_inventor import MetaLanguage,exec_safe,ident


def quad(xs,c):return [x*x+c for x in xs]
def divisible(xs,d):return [x for x in xs if x%d==0]
def scalar_data(fn,inputs):return [(x,fn(x)) for x in inputs]
def list_data(fn,inputs):return [(x,fn(x)) for x in inputs]


def freeze_source(out):
    learning=MetaLanguage.empty()
    original=[]
    originals={}
    def learn(label,inputs,fun,budget=2):
        examples=scalar_data(fun,inputs)
        result=learning.solve(examples,budget=budget)
        if result is None:raise AssertionError('SOURCE_NOT_LEARNED:'+label)
        original.append({'label':label,**result})
        originals[label]=result['symbol']
        return result
    for c in (1,2):
        learn('quadratic_'+str(c),list(range(0,7)),lambda x,c=c:x*x+c)
    for d in (2,3):
        learn('predicate_'+str(d),list(range(0,21)),lambda x,d=d:x%d==0)
    for a,b in (('quadratic_1','quadratic_2'),('predicate_2','predicate_3')):
        if learning.invent_production(originals[a],originals[b]) is None:
            raise AssertionError('SOURCE_GRAMMAR_DISCOVERY_FAILED')

    values=[[0,1,2,3,4],[5,6,7,8],[1,3,5,7,9],[2,6,8,12]]
    source_map=[];source_filter=[]
    for c in (1,2):
        r=learning.solve(list_data(lambda z,c=c:quad(z,c),values),budget=1)
        if r is None:raise AssertionError('SOURCE_LIST_MAPPING_FAILED')
        source_map.append(r['symbol'])
        original.append({'label':'map_quadratic_'+str(c),**r})
    for d in (2,3):
        r=learning.solve(list_data(lambda z,d=d:divisible(z,d),values),budget=1)
        if r is None:raise AssertionError('SOURCE_LIST_FILTER_FAILED')
        source_filter.append(r['symbol'])
        original.append({'label':'filter_mod_'+str(d),**r})
    if learning.invent_production(*source_map) is None:
        raise AssertionError('SOURCE_MAP_PRODUCTION_FAILED')
    if learning.invent_production(*source_filter) is None:
        raise AssertionError('SOURCE_FILTER_PRODUCTION_FAILED')

    nested=[[[0,1],[2,3,4]],[[5,6,7],[8,9]],[[4,8,12],[1,3,5]]]
    nmap=[];nfilter=[]
    for c in (1,2):
        r=learning.solve(list_data(lambda z,c=c:[quad(row,c) for row in z],nested))
        if r is None:raise AssertionError('SOURCE_NESTED_MAP_FAILED')
        nmap.append(r['symbol'])
        original.append({'label':'nested_map_quad_'+str(c),**r})
    for d in (2,3):
        r=learning.solve(list_data(lambda z,d=d:[divisible(row,d) for row in z],nested))
        if r is None:raise AssertionError('SOURCE_NESTED_FILTER_FAILED')
        nfilter.append(r['symbol'])
        original.append({'label':'nested_filter_mod_'+str(d),**r})
    if learning.invent_production(*nmap) is None:
        raise AssertionError('SOURCE_NESTED_MAP_PRODUCTION_FAILED')
    # These transformations infer the SAME nested map generator, and should
    # count as only one production rather than two discoveries.
    learning.invent_production(*nfilter)
    frozen=learning.source_only_json()
    (out/'FROZEN_SOURCE_LANGUAGE.json').write_text(
        json.dumps(frozen,indent=2,sort_keys=True)+'\n')
    return frozen,original


def random_arrays(seed,n,length_min=1,length_max=12,high=90):
    r=random.Random(seed)
    return [[r.randrange(-10,high) for _ in range(
        r.randint(length_min,length_max))] for _ in range(n)]


def learn_target_set(frozen):
    learner=MetaLanguage.load(frozen)
    ablated=MetaLanguage.load(frozen)
    ablated.productions.clear()
    records=[]
    xtrain=list(range(0,20))
    scalar_targets=[
        ('new_quadratic_offset',
         scalar_data(lambda x:x*x+5,xtrain),
         scalar_data(lambda x:x*x+5,range(25,61)),1),
        ('new_modular_predicate',
         scalar_data(lambda x:x%4==0,xtrain),
         scalar_data(lambda x:x%4==0,range(25,75)),1),
    ]
    arrays=random_arrays(44,6,2,10,18)
    arrays_test=random_arrays(5555,32,1,10,65)
    list_targets=[
        ('new_list_mapping',list_data(lambda v:quad(v,5),arrays),
         list_data(lambda v:quad(v,5),arrays_test),1),
        ('new_list_filter',list_data(lambda v:divisible(v,4),arrays),
         list_data(lambda v:divisible(v,4),arrays_test),1),
    ]
    rng=random.Random(55)
    nested=[random_arrays(rng.randint(1,100000),rng.randint(1,4),1,8,19)
            for _ in range(6)]
    nested_test=[random_arrays(rng.randint(1,100000),rng.randint(1,5),1,8,75)
                 for _ in range(32)]
    nested_targets=[
        ('new_nested_mapping',
         list_data(lambda v:[quad(row,5) for row in v],nested),
         list_data(lambda v:[quad(row,5) for row in v],nested_test),1),
        ('new_nested_filter',
         list_data(lambda v:[divisible(row,4) for row in v],nested),
         list_data(lambda v:[divisible(row,4) for row in v],nested_test),1),
    ]
    for label,train,test,budget in scalar_targets+list_targets+nested_targets:
        # The target formulas exist only in this evaluator. The inventor sees
        # (input, output) examples and a FROZEN source-discovered language.
        ablated.defs=dict(learner.defs)
        ablation=ablated.solve(train,budget=budget,allow_core_lifting=False)
        got=learner.solve(train,budget=budget,allow_core_lifting=False)
        if got is None:
            records.append({'label':label,'result':'NOT_SOLVED',
                            'source_grammar_ablation_solved':ablation is not None})
            continue
        ast=learner.defs[got['symbol']]['body']
        heldout=[]
        for x,y in test:
            ok,pred=exec_safe(['call',got['symbol'],['arg']],x,learner.defs)
            heldout.append(ok and type(pred)==type(y) and pred==y)
        records.append({
            'label':label,'result':'EXACT' if all(heldout) else 'FAILED',
            'new_symbol':got['symbol'],'mechanism':got['mechanism'],
            'generated_program_ast':ast,
            'invented_source_production':got.get('production'),
            'source_grammar_ablation_solved':ablation is not None,
            'heldout_count':len(test),'heldout_exact':sum(heldout),
            'input_type':learner.defs[got['symbol']]['input'],
            'output_type':learner.defs[got['symbol']]['output'],
        })
    return learner,records


def run(out:Path):
    if out.exists():raise ValueError('NO_OVERWRITE_FIRST')
    out.mkdir(parents=True)
    t0=time.perf_counter()
    frozen,sources=freeze_source(out)
    first_sha=ident(frozen)
    learner,rows=learn_target_set(frozen)
    (out/'GROWN_LANGUAGE.json').write_text(
        json.dumps(learner.source_only_json(),indent=2,sort_keys=True)+'\n')
    report={
        'schema':'neumann.q3.reflective-metagrammar-autoinvention-first.v1',
        'frozen_source_language_sha256_short':first_sha,
        'baseline_universal_core':'Int+list combinators, type-inferred; no ARC-specific expressions',
        'human_authored_seed_runtime':True,
        'human_authored_synthetic_target_families':True,
        'trained_neural_policy':False,
        'source_programs_learned':len(sources),
        'source_generated_grammar_productions':len(frozen['productions']),
        'target_new_function_definitions':sum(x['result']=='EXACT' for x in rows),
        'target_distinct_type_signatures':sorted({(x['input_type'],x['output_type'])
            for x in rows if x['result']=='EXACT'}),
        'heldout_total':sum(x.get('heldout_count',0) for x in rows),
        'heldout_exact':sum(x.get('heldout_exact',0) for x in rows),
        'target_tasks_invented_grammar_necessary':sum(
            x.get('source_grammar_ablation_solved') is False and
            x['result']=='EXACT' for x in rows),
        'source_programs':sources,'target_tasks':rows,
        'elapsed_s':round(time.perf_counter()-t0,5),
        'Q3_GLOBAL':'OPEN','Q4_GLOBAL':'OPEN','Q6_GLOBAL':'OPEN',
    }
    (out/'FIRST.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('Q3_REFLECTIVE_RESULT',json.dumps({
        k:v for k,v in report.items() if k not in ('target_tasks','source_programs')
    },sort_keys=True))
    for rec in rows:
        print('Q3_SELF_INVENTED',rec['label'],rec['result'],
              rec.get('mechanism'),
              str(rec.get('heldout_exact','?'))+'/'+str(rec.get('heldout_count','?')),
              'no_grammar_solved=',rec.get('source_grammar_ablation_solved'))
    return report


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    run(a.out)
