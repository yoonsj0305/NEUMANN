#!/usr/bin/env python3
"""Task-conditioned relational edit-mask program synthesis from real demonstrations.

First run previous exact typed/2-stage solver unchanged. On abstain, infer a
BOOLEAN relation on original input coordinates that identifies only necessary
changes; learn repaint color from source demos. Predicates are explicit and
source-independent. Neither neural invention nor global Q3 is implied.
"""
import argparse,collections,hashlib,json,pathlib,sys,time
import numpy as np
from scipy.ndimage import binary_fill_holes,label
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'q3_adaptive_representation_20261022'))
from auto_typed_composer import synthesize
MAX_PIXELS=3500

def count_fg(a):
    q=collections.Counter(int(v) for v in a.flat if v!=0)
    return q

def brect(mask):
    pos=np.argwhere(mask)
    out=np.zeros(mask.shape,bool)
    if len(pos):
        lo=pos.min(0);hi=pos.max(0)
        out[lo[0]:hi[0]+1,lo[1]:hi[1]+1]=True
    return out

def border(mask):
    q=brect(mask)
    if not q.any():return q
    a=np.zeros(q.shape,bool)
    pos=np.argwhere(q);lo=pos.min(0);hi=pos.max(0)
    a[lo[0],lo[1]:hi[1]+1]=True;a[hi[0],lo[1]:hi[1]+1]=True
    a[lo[0]:hi[0]+1,lo[1]]=True;a[lo[0]:hi[0]+1,hi[1]]=True
    return a

def spans(mask,axis):
    out=np.zeros(mask.shape,bool)
    if axis=='h':
        for i in range(mask.shape[0]):
            j=np.flatnonzero(mask[i])
            if len(j)>1:out[i,j[0]:j[-1]+1]=True
    else:
        for j in range(mask.shape[1]):
            i=np.flatnonzero(mask[:,j])
            if len(i)>1:out[i[0]:i[-1]+1,j]=True
    return out

def geometries(a):
    a=np.asarray(a,np.int16);h,w=a.shape
    foreground=a!=0
    z=np.zeros((h,w),bool)
    result={'all':np.ones((h,w),bool),'foreground':foreground,'background':~foreground,
      'bbox':brect(foreground),'bbox_border':border(foreground),
      'bbox_holes':brect(foreground)&~foreground,
      'enclosed_holes':binary_fill_holes(foreground)&~foreground,
      'rowspan':spans(foreground,'h'),'colspan':spans(foreground,'v'),
      'rowcol_union':spans(foreground,'h')|spans(foreground,'v'),
      'rowcol_intersection':spans(foreground,'h')&spans(foreground,'v'),
      'fg_flipped_lr':np.fliplr(foreground),'fg_flipped_ud':np.flipud(foreground),
      'fg_rot180':np.rot90(foreground,2),
      'left_edge':np.broadcast_to(np.arange(w)==0,(h,w)),
      'right_edge':np.broadcast_to(np.arange(w)==w-1,(h,w)),
      'top_edge':np.broadcast_to(np.arange(h)[:,None]==0,(h,w)),
      'bottom_edge':np.broadcast_to(np.arange(h)[:,None]==h-1,(h,w)),
      'row_even':np.broadcast_to(np.arange(h)[:,None]%2==0,(h,w)),
      'col_even':np.broadcast_to(np.arange(w)%2==0,(h,w)),
      'center_row':np.broadcast_to(np.arange(h)[:,None]==h//2,(h,w)),
      'center_col':np.broadcast_to(np.arange(w)==w//2,(h,w))}
    result['fg_sym_lr_missing']=result['fg_flipped_lr']&~foreground
    result['fg_sym_ud_missing']=result['fg_flipped_ud']&~foreground
    result['fg_sym_180_missing']=result['fg_rot180']&~foreground
    q=count_fg(a)
    ranked=[int(v) for v,_ in sorted(q.items(),key=lambda e:(-e[1],e[0]))]
    selections={'most':ranked[0] if ranked else None,'least':ranked[-1] if ranked else None,
                'smallest_id':min(q) if q else None,'largest_id':max(q) if q else None}
    for rank,c in selections.items():
        m=(a==c) if c is not None else z
        result['color_'+rank]=m
        result['color_'+rank+'_bbox']=brect(m)
        result['color_'+rank+'_border']=border(m)
        result['color_'+rank+'_boxholes']=brect(m)&~m
        result['color_'+rank+'_enclosedholes']=binary_fill_holes(m)&~m
        result['color_'+rank+'_rowspan']=spans(m,'h')
        result['color_'+rank+'_colspan']=spans(m,'v')
        result['color_'+rank+'_sym_lr_missing']=np.fliplr(m)&~m
        result['color_'+rank+'_sym_ud_missing']=np.flipud(m)&~m
        result['color_'+rank+'_sym_180_missing']=np.rot90(m,2)&~m
        result['color_'+rank+'_rowcol_intersection']=np.broadcast_to(m.any(1)[:,None],a.shape)&np.broadcast_to(m.any(0),a.shape)
    # Each object box is formed from the input graph, not test labels.
    for rank in ('most','least'):
        c=selections[rank]
        m=a==c if c is not None else z
        marks,n=label(m,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
        obj=np.zeros(a.shape,bool)
        for i in range(1,n+1):
            comp=marks==i
            obj|=brect(comp)
        result['color_'+rank+'_component_boxes']=obj
        result['color_'+rank+'_component_holes']=obj&~m
    return {k:np.asarray(v,dtype=bool) for k,v in result.items()}

def repaints(demos):
    diffs=[]
    for ex in demos:
        inp=np.asarray(ex['input']);out=np.asarray(ex['output'])
        if inp.shape!=out.shape:return []
        changed=out[inp!=out]
        diffs.append(changed)
    if not any(len(z) for z in diffs):return []
    flattened=[int(x) for z in diffs for x in z.tolist()]
    colors=[]
    if len(set(flattened))==1:colors.append(('fixed_output_color',flattened[0]))
    for typ in ('most','least','smallest_id','largest_id'):
        good=True
        for ex,z in zip(demos,diffs):
            q=count_fg(np.asarray(ex['input']))
            if not q or len(z)==0:continue
            ranks=sorted(q.items(),key=lambda e:(-e[1],e[0]))
            c={'most':ranks[0][0],'least':ranks[-1][0],'smallest_id':min(q),'largest_id':max(q)}[typ]
            if any(int(x)!=int(c) for x in z):good=False;break
        if good:colors.append(('input_'+typ,None))
    return colors

def paint(a,formula):
    mode,c=formula
    if mode=='fixed_output_color':return int(c)
    q=count_fg(a)
    if not q:return None
    ranks=sorted(q.items(),key=lambda e:(-e[1],e[0]))
    return int({'input_most':ranks[0][0],'input_least':ranks[-1][0],
         'input_smallest_id':min(q),'input_largest_id':max(q)}[mode])

def boolean_expr(masks,recipe):
    kind,u,v=recipe
    a=masks[u]
    if kind=='one':return a
    b=masks[v]
    if kind=='and':return a&b
    if kind=='or':return a|b
    if kind=='xor':return a^b
    if kind=='and-not':return a&~b
    raise ValueError(kind)

def apply(grid,ast):
    a=np.asarray(grid,np.int16);masks=geometries(a)
    m=boolean_expr(masks,ast['mask_expression'])
    p=paint(a,ast['paint_rule'])
    if p is None:return None
    return np.where(m,p,a).astype(np.int16)

def discover(demos,max_mask_pairs=11000):
    t=time.perf_counter()
    if len(demos)<2:return None,{'reason':'INSUFFICIENT_DEMOS'}
    xs=[np.asarray(ex['input'],np.int16) for ex in demos]
    ys=[np.asarray(ex['output'],np.int16) for ex in demos]
    if any(x.shape!=y.shape for x,y in zip(xs,ys)):return None,{'reason':'SHAPE_CHANGE_NOT_SUPPORTED'}
    if sum(x.size for x in xs)>MAX_PIXELS:return None,{'reason':'PIXEL_LIMIT'}
    candidates=repaints(demos)
    if not candidates:return None,{'reason':'NO_LEARNABLE_REPAINT'}
    targs=np.concatenate([(x!=y).ravel() for x,y in zip(xs,ys)])
    mats=[geometries(x) for x in xs]
    assert all(set(m)==set(mats[0]) for m in mats)
    seen={}
    for key in sorted(mats[0]):
        vector=np.concatenate([m[key].ravel() for m in mats])
        if vector.tobytes() not in seen:seen[vector.tobytes()]=(key,vector)
    unique=list(seen.values())
    target=targs.tobytes();checked=0
    def admit(formula):
        for rule in candidates:
            ast={'mask_expression':list(formula),'paint_rule':list(rule)}
            if all(np.array_equal(apply(ex['input'],ast),np.asarray(ex['output'])) for ex in demos):
                return ast
        return None
    for key,vec in unique:
        checked+=1
        if vec.tobytes()==target:
            ast=admit(('one',key,None))
            if ast:return ast,{'reason':'SINGLE_SOURCE_PREDICATE','predicate_count':len(unique),'checked':checked,'wall_s':time.perf_counter()-t}
    for i,(name,a) in enumerate(unique):
        for j,(other,b) in enumerate(unique):
            if checked>=max_mask_pairs:break
            for op,truth in (('and',a&b),('or',a|b),('xor',a^b),('and-not',a&~b)):
                checked+=1
                if truth.tobytes()!=target:continue
                ast=admit((op,name,other))
                if ast:return ast,{'reason':'COMPOSED_SOURCE_PREDICATE','predicate_count':len(unique),'checked':checked,'wall_s':time.perf_counter()-t}
            if checked>=max_mask_pairs:break
        if checked>=max_mask_pairs:break
    return None,{'reason':'NO_EXACT_RELATIONAL_PREDICATE','predicate_count':len(unique),'checked':checked,'wall_s':time.perf_counter()-t}

def infer(task):
    existing=synthesize(task)
    if existing.get('prediction') is not None:
        existing['mask_search_status']='SKIPPED_STRONG_PREVIOUS_PROPOSAL'
        return existing
    demos=task['train']
    ast,details=discover(demos)
    if ast is None:return {'status':'ABSTAIN_NO_RELATIONAL_EDIT_RULE','prediction':None,'search':details}
    pred=[]
    for t in task['test']:
        z=apply(t['input'],ast)
        if z is None:return {'status':'ABSTAIN_EDIT_TEST_INAPPLICABLE','prediction':None,'ast':ast,'search':details}
        pred.append(z.tolist())
    return {'status':'INFERRED_RELATIONAL_EDIT_RULE','prediction':pred,'ast':ast,'search':details,
            'prior_status':existing['status']}

def main():
    p=argparse.ArgumentParser();p.add_argument('--masked-dir',required=True)
    p.add_argument('--out',required=True);p.add_argument('--n',type=int,required=True)
    a=p.parse_args();files=sorted(pathlib.Path(a.masked_dir).glob('*.json'));assert len(files)==a.n
    start=time.perf_counter();rows={}
    for f in files:
        task=json.loads(f.read_text());assert all('output' not in x for x in task['test'])
        tm=time.perf_counter()
        try:res=infer(task)
        except Exception as exc:res={'status':'ERROR','prediction':None,'error':type(exc).__name__+': '+str(exc)[:200]}
        res['task_wall_s']=time.perf_counter()-tm
        rows[f.stem]=res
        if len(rows)%20==0:print('EDIT_LEARN_SOURCE_PROGRESS',len(rows),dict(collections.Counter(r['status'] for r in rows.values())),flush=True)
    result={'schema':'NEUMANN_RELATIONAL_EDIT_PROGRAM_LEARNER.v1','n':a.n,'test_labels_seen':False,
            'base_program_synthesizer':'frozen PR480 two-stage first',
            'counts':dict(collections.Counter(r['status'] for r in rows.values())),
            'total_wall_s':time.perf_counter()-start,'rows':rows}
    out=pathlib.Path(a.out);out.parent.mkdir(exist_ok=True,parents=True);out.write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n')
    print('SEALED_RELATIONAL_EDIT_PREDICTIONS',json.dumps(result['counts'],sort_keys=True),
          'wall_s',result['total_wall_s'],'sha256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
