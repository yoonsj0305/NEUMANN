#!/usr/bin/env python3
"""Bounded adaptive representation discovery from demonstration input-output pairs.

Original labels are inaccessible: accepts ONLY demonstration outputs and test inputs.
Discovers a two-stage *typed composition*, not a new primitive and not a neural claim.
Pure sequence dedup avoids paying twice for identical intermediate representations.
Strong historical source-exact baseline is always prioritized.
"""
import argparse,collections,hashlib,json,pathlib,sys,time
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'q3_object_synthesis_transfer_20261022'))
from frozen_original_typed_selector_v2 import select,asarr,mapped,uniform_color_map,d4
from object_relational_proposer import solve,operation

SELECTORS=(
 ('whole',),('crop_fg',),('strip','rows'),('strip','cols'),
 ('component','largest',4,'mask'),('component','largest',8,'mask'),
 ('component','smallest',4,'mask'),('component','smallest',8,'mask'),
 ('component','top',4,'global'),('component','bottom',4,'global'),
 ('component','left',4,'global'),('component','right',4,'global'),
 ('crop_color','most'),('crop_color','least'),
 ('crop_mask_color','most'),('crop_mask_color','least'),
 ('isolate_color','most'),('drop_color','most'))
OPS=('id','lr','ud','r90','r180','r270','tr','anti',
     'connect:row','connect:col','connect:both',
     'foreground:box','foreground:outline',
     'rect:fill:4','rect:fill:8','rect:outline:4',
     'sym-lr:complete','sym-ud:complete','sym-both:complete',
     'sym-lr:intersect','sym-ud:intersect',
     'rowcol:intersection','rowcol:cross',
     'reduce:rows','reduce:cols','reduce:both',
     'pack:h:large:0','pack:v:large:0')
MAX_STATE=900

def step(x,op):
    if op in ('id','lr','ud','r90','r180','r270','tr','anti'):r=d4(x,op)
    else:r=operation(x,op)
    if r is None:return None
    r=asarr(r)
    if r.ndim!=2 or r.size==0 or r.size>MAX_STATE or max(r.shape)>30:return None
    return r

def signature(arrs):
    h=hashlib.sha256()
    for a in arrs:
        h.update(str(a.shape).encode());h.update(a.tobytes())
    return h.hexdigest()

def source_candidate(task, max_states=1800):
    examples=task['train']
    if not examples:return None,{'reason':'NO_DEMONSTRATIONS','states':0}
    xs=[asarr(ex['input']) for ex in examples]
    ys=[asarr(ex['output']) for ex in examples]
    if any(x.ndim!=2 or y.ndim!=2 or not x.size or not y.size for x,y in zip(xs,ys)):
        return None,{'reason':'INVALID_GRID','states':0}
    # No uniform recoloring over a k-color representation can yield >k output colors.
    # First & second operators here never create novel colors, so this is a proven necessary bound.
    if any(len(np.unique(y))>len(np.unique(x)) for x,y in zip(xs,ys)):
        return None,{'reason':'PALETTE_INFORMATION_IMPOSSIBLE','states':0}
    start=time.perf_counter();checks=0;unique_select={};states=0;dedup_stage1=set()
    for sel in SELECTORS:
        try: src=[select(x,sel) for x in xs]
        except (ValueError,TypeError,IndexError):continue
        if any(a is None or not np.asarray(a).size for a in src):continue
        src=[asarr(a) for a in src]
        if any(a.size>MAX_STATE for a in src):continue
        sig=signature(src)
        if sig in unique_select:continue
        unique_select[sig]=sel
        for op1 in OPS:
            try:middle=[step(x,op1) for x in src]
            except (ValueError,TypeError,IndexError):continue
            if any(a is None for a in middle):continue
            pair_sig=signature(middle)
            if pair_sig in dedup_stage1:continue
            dedup_stage1.add(pair_sig);states+=1
            if states>max_states:
                return None,{'reason':'STATE_CAP','states':states,'shape_checks':checks,
                             'wall_s':time.perf_counter()-start}
            for op2 in OPS:
                checks+=1
                try:out0=step(middle[0],op2)
                except (ValueError,TypeError,IndexError):continue
                if out0 is None or out0.shape!=ys[0].shape:continue
                lookup={}
                if not uniform_color_map(out0,ys[0],lookup):continue
                remaining=[];valid=True
                for m,y in zip(middle[1:],ys[1:]):
                    try:o=step(m,op2)
                    except (ValueError,TypeError,IndexError):valid=False;break
                    if o is None or o.shape!=y.shape or not uniform_color_map(o,y,lookup):
                        valid=False;break
                    remaining.append(o)
                if not valid:continue
                # Recheck every demo after mapping is inferred across ALL examples.
                outs=[out0]+remaining
                if not all(np.array_equal(mapped(o,lookup),y) for o,y in zip(outs,ys)):continue
                # Exactly source-derived two-step AST; zero reference-test interaction.
                ast={'selector':list(sel),'first':op1,'second':op2,
                     'uniform_color_mapping':lookup}
                return ast,{'reason':'EXACT_SOURCE_DERIVED_PROGRAM','states':states,
                            'shape_checks':checks,'wall_s':time.perf_counter()-start}
    return None,{'reason':'NO_EXACT_TWO_STAGE_PROGRAM','states':states,
                 'shape_checks':checks,'wall_s':time.perf_counter()-start}

def replay_grid(g,ast):
    source=select(asarr(g),tuple(ast['selector']))
    if source is None:return None
    one=step(asarr(source),ast['first'])
    if one is None:return None
    two=step(one,ast['second'])
    if two is None:return None
    # JSON mapping keys are text after receipt load. Make both integer and string accepted.
    lookup={int(k):int(v) for k,v in ast['uniform_color_mapping'].items()}
    return mapped(two,lookup)

def synthesize(task):
    base=solve(task)
    if base.get('prediction') is not None:
        base['adaptive_status']='SKIPPED_ALREADY_EXACT_DEMO_PROGRAM'
        return base
    ast,metadata=source_candidate(task)
    if ast is None:
        return {'status':'ABSTAIN_NO_ADAPTIVE_AST','prediction':None,
                'adaptive_search':metadata,'prior_status':base['status']}
    # Independently replay all source demos using learned AST
    for ex in task['train']:
        z=replay_grid(ex['input'],ast)
        if z is None or not np.array_equal(z,asarr(ex['output'])):
            return {'status':'ERROR_SOURCE_REPLAY','prediction':None,'ast':ast,
                    'adaptive_search':metadata}
    outs=[]
    for ex in task['test']:
        z=replay_grid(ex['input'],ast)
        if z is None:return {'status':'ABSTAIN_TEST_INAPPLICABLE','prediction':None,
                              'ast':ast,'adaptive_search':metadata}
        outs.append(z.tolist())
    return {'status':'ADAPTIVE_TWO_STEP_AST','prediction':outs,'ast':ast,
            'adaptive_search':metadata,'prior_status':base['status']}

def main():
    p=argparse.ArgumentParser();p.add_argument('--masked-dir',required=True)
    p.add_argument('--out',required=True);p.add_argument('--n',type=int,required=True)
    args=p.parse_args();files=sorted(pathlib.Path(args.masked_dir).glob('*.json'))
    assert len(files)==args.n;start=time.perf_counter()
    rows={}
    for f in files:
        d=json.loads(f.read_text())
        assert all('output' not in t for t in d['test'])
        t=time.perf_counter()
        try:r=synthesize(d)
        except Exception as e:r={'status':'ERROR','prediction':None,
                                 'error':type(e).__name__+': '+str(e)[:200]}
        r['task_wall_s']=time.perf_counter()-t
        rows[f.stem]=r
        if len(rows)%20==0:
            print('ADAPTIVE_SOURCE_PROGRESS',len(rows),
                  dict(collections.Counter(v['status'] for v in rows.values())),flush=True)
    out={'schema':'NEUMANN_ADAPTIVE_REPRESENTATION_TWO_STEP.v1','n':len(files),
         'test_labels_seen':False,'solver_baseline':'unchanged prior #478 object DSL first',
         'adaptive_condition':'ONLY IF PRIOR HAS NO SOURCE_FITTED_PROGRAM',
         'counts':dict(collections.Counter(z['status'] for z in rows.values())),
         'complete_wall_s':time.perf_counter()-start,'rows':rows}
    dest=pathlib.Path(args.out);dest.parent.mkdir(exist_ok=True,parents=True)
    dest.write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n')
    print('FROZEN_ADAPTIVE_SOURCE',json.dumps(out['counts'],sort_keys=True),
          'full_wall_s',out['complete_wall_s'],
          'sha256',hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
