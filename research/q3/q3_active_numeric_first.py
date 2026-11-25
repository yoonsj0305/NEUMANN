"""Numeric symbolic construction: FIRST synthetic heldout; not external tasks."""
from __future__ import annotations
import json
from pathlib import Path
from random import Random
from fractions import Fraction
from neumann1.active_numeric_inventor import invent_numeric_function


def main():
    tasks=[
        ('cubic_1d',1,3,lambda x:7*x**3-2*x**2+5*x-11),
        ('quadratic_2d',2,2,lambda x,y:2*x*x+3*x*y-7*y*y+4*x-13),
        ('cubic_2d',2,3,lambda x,y:4*x**3-3*x*x*y+8*x*y*y-2*y**3+11),
        ('cubic_3d',3,3,lambda x,y,z:3*x*y*z+5*x*x-2*y*z+4*z-17),
        ('affine_4d',4,1,lambda a,b,c,d:9*a-11*b+3*c+2*d+17),
        ('quartic_3d',3,4,lambda x,y,z:2*x**4+3*y**3*z-4*x*x*y*y+7*z*z-11),
    ]
    results=[]
    for name,arity,degree,f in tasks:
        success=0;heldout=0;correct=0;source=0;nonzero=[]
        for seed in range(30):
            m=invent_numeric_function(f,arity=arity,max_degree=degree+1,
                                      budget=180,validation=8,seed=seed)
            if m.degree!=degree:
                raise AssertionError((name,seed,'wrong degree',m.degree,degree))
            observed={p for p,y in m.source_facts}
            rng=Random(19793+seed)
            samples=[]
            while len(samples)<200:
                point=tuple(Fraction(rng.choice([-1,1])*rng.randint(31,100))
                            for _ in range(arity))
                if point not in observed:samples.append(point)
            good=sum(m.apply(*p)==f(*p) for p in samples)
            success+=1;heldout+=len(samples);correct+=good
            source+=len(observed);nonzero.append(len(m.nonzero_terms))
        results.append(dict(name=name,variables=arity,degree=degree,
                            constructed=success,source_queries=source,
                            heldout=heldout,correct=correct,
                            min_nonzero_terms=min(nonzero),max_nonzero_terms=max(nonzero)))
    assert all(x['constructed']==30 and x['heldout']==x['correct'] for x in results)
    report={'schema':'NEUMANN.Q3.active-numeric-synthesis.synthetic-FIRST.v1',
            'date':'2026-11-08','suites':results,
            'totals':{'constructed':sum(x['constructed'] for x in results),
                      'source_queries':sum(x['source_queries'] for x in results),
                      'heldout':sum(x['heldout'] for x in results),
                      'correct':sum(x['correct'] for x in results)},
            'caveat':'Synthetic exact polynomials; prior polynomial grammar and bounded degree human-provided. Same-author oracles; not autonomous global axioms or independent-author proofs.'}
    path=Path(__file__).with_name('q3_active_numeric_first_result.json')
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return report

if __name__=='__main__':main()
