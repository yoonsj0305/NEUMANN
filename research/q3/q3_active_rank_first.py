"""Transparent same-author synthetic rank-representation experiment.

Original oracle outputs are used only by a bounded source-time interface.
Every nonqueried original pair is checked by an independent evaluation pass.
Twenty exploration seeds per one of six author-defined relation families do
NOT imply 120 independently authored problem algorithms.
"""
from __future__ import annotations
import json
from fractions import Fraction
from random import Random
from time import perf_counter_ns
from pathlib import Path
from neumann1.active_rank_inventor import invent_rank_operator


def make_case(name,seed):
    n,m,r=(60,65,2) if name in ('nonsquare2','bipartite_graph') else (
        45,54,{'random3':3,'random5':5,'hidden_rank':2,'rational3':3}[name])
    rows=list(range(n));cols=list(range(m))
    rng=Random(seed)
    left=[[rng.randint(-8,8) for _ in range(r)] for i in rows]
    right=[[rng.randint(-8,8) for j in cols] for k in range(r)]
    def base(i,j):
        return sum(left[i][k]*right[k][j] for k in range(r))
    if name=='bipartite_graph':
        a=[(i+seed)%2 for i in rows];b=[(j+seed+1)%2 for j in cols]
        op=lambda i,j:int(a[i]!=b[j])
    elif name=='hidden_rank':
        special=set(Random(seed).sample(rows,7))
        op=lambda i,j:(2+i%5 if j%3==0 else int(i in special)*(1+j%7))
    elif name=='rational3':
        op=lambda i,j:Fraction(base(i,j),19)
    else:
        op=base
    return rows,cols,op,r


def main():
    suites=[]
    totals={'cases':0,'passed':0,'source_queries':0,'full_table_queries':0,
            'heldout':0,'heldout_correct':0,'representation_repairs':0,
            'build_wall_ms':0.0,'heldout_execution_wall_ms':0.0}
    for family in ('random3','random5','nonsquare2','bipartite_graph',
                   'hidden_rank','rational3'):
        summary={'family':family,'cases':0,'passed':0,'source_queries':0,
                 'full_table_queries':0,'heldout':0,'heldout_correct':0,
                 'representation_repairs':0,'build_wall_ms':0.0,
                 'heldout_execution_wall_ms':0.0}
        for seed in range(20):
            rows,cols,op,expected_rank=make_case(family,seed)
            t=perf_counter_ns()
            model=invent_rank_operator(rows,cols,op,query_budget=len(rows)*len(cols),
                                       seed=seed,patience=6,validation=32,max_rank=12)
            build_ms=(perf_counter_ns()-t)/1e6
            source={(a,b) for a,b,_ in model.source_facts}
            heldout=[(i,j) for i in rows for j in cols if (i,j) not in source]
            t=perf_counter_ns()
            correct=sum(model.apply(i,j)==op(i,j) for i,j in heldout)
            execute_ms=(perf_counter_ns()-t)/1e6
            assert correct==len(heldout) and model.rank==expected_rank,(
                family,seed,correct,len(heldout),model.rank)
            summary['cases']+=1;summary['passed']+=1
            summary['source_queries']+=len(source)
            summary['full_table_queries']+=len(rows)*len(cols)
            summary['heldout']+=len(heldout);summary['heldout_correct']+=correct
            summary['representation_repairs']+=model.repairs
            summary['build_wall_ms']+=build_ms
            summary['heldout_execution_wall_ms']+=execute_ms
        summary['build_wall_ms']=round(summary['build_wall_ms'],3)
        summary['heldout_execution_wall_ms']=round(
            summary['heldout_execution_wall_ms'],3)
        suites.append(summary)
        for key in totals: totals[key]+=summary[key]
    totals['build_wall_ms']=round(totals['build_wall_ms'],3)
    totals['heldout_execution_wall_ms']=round(
        totals['heldout_execution_wall_ms'],3)
    report={'schema':'NEUMANN.Q3.active-rank-repair.first-local.v1',
            'kind':'same-author synthetic repair, no independent holdout',
            'families':suites,'totals':totals,
            'first_diagnostic':(
              'Prior random validation missed hidden_rank seed=1: 119/120 passes'),
            'after_fix':(
              'Stratify source probes across novel rows and rebuild IR on counterexample'),
            'limitations':['same-author synthetic exact low-rank relations',
             'finite source cannot rule out adversarial one-cell exceptions',
             'CPU/runtime not proven better than classical exact rank completion',
             'query savings versus full table is not global Q4',
             'seeds are not independent mathematical tasks']}
    path=Path(__file__).with_name('q3_active_rank_first_results.json')
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    main()
