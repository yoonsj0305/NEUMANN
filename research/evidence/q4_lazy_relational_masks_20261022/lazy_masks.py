#!/usr/bin/env python3
"""Lazy compiled execution of actual NEUMANN relational edit rules.

Computes only AST-referenced predicates; exact same result as eager 65-ish-mask
materialization. This does NOT accelerate source search or improve Q3 accuracy.
"""
import collections,functools,numpy as np
from scipy.ndimage import binary_fill_holes,label
from infer_edit_rule import brect,border,geometries,apply

def count_fg(a):
    a=np.asarray(a)
    nonzero=a[a!=0]
    if not len(nonzero):return {}
    vals,counts=np.unique(nonzero,return_counts=True)
    return {int(v):int(n) for v,n in zip(vals,counts)}

def spans(mask,axis):
    mask=np.asarray(mask,bool)
    if axis=='h':
        count=mask.sum(axis=1);active=count>1
        first=mask.argmax(axis=1)
        last=mask.shape[1]-1-mask[:,::-1].argmax(axis=1)
        loc=np.arange(mask.shape[1])[None,:]
        return active[:,None]&(loc>=first[:,None])&(loc<=last[:,None])
    count=mask.sum(axis=0);active=count>1
    first=mask.argmax(axis=0)
    last=mask.shape[0]-1-mask[::-1,:].argmax(axis=0)
    loc=np.arange(mask.shape[0])[:,None]
    return active[None,:]&(loc>=first[None,:])&(loc<=last[None,:])

def paint(a,rule):
    mode,c=rule
    if mode=='fixed_output_color':return int(c)
    q=count_fg(a)
    if not q:return None
    ranks=sorted(q.items(),key=lambda e:(-e[1],e[0]))
    return int({'input_most':ranks[0][0],'input_least':ranks[-1][0],
         'input_smallest_id':min(q),'input_largest_id':max(q)}[mode])


def lazy_predicate(a,key,cache):
    if key in cache:return cache[key]
    h,w=a.shape
    def fetch(k):return lazy_predicate(a,k,cache)
    fg=fetch('foreground') if key!='foreground' else a!=0
    if key=='all':out=np.ones(a.shape,bool)
    elif key=='foreground':out=fg
    elif key=='background':out=~fg
    elif key=='bbox':out=brect(fg)
    elif key=='bbox_border':out=border(fg)
    elif key=='bbox_holes':out=fetch('bbox') & ~fg
    elif key=='enclosed_holes':out=binary_fill_holes(fg)&~fg
    elif key=='rowspan':out=spans(fg,'h')
    elif key=='colspan':out=spans(fg,'v')
    elif key=='rowcol_union':out=fetch('rowspan')|fetch('colspan')
    elif key=='rowcol_intersection':out=fetch('rowspan')&fetch('colspan')
    elif key=='fg_flipped_lr':out=np.fliplr(fg)
    elif key=='fg_flipped_ud':out=np.flipud(fg)
    elif key=='fg_rot180':out=np.rot90(fg,2)
    elif key=='fg_sym_lr_missing':out=fetch('fg_flipped_lr')&~fg
    elif key=='fg_sym_ud_missing':out=fetch('fg_flipped_ud')&~fg
    elif key=='fg_sym_180_missing':out=fetch('fg_rot180')&~fg
    elif key=='left_edge':out=np.broadcast_to(np.arange(w)==0,(h,w))
    elif key=='right_edge':out=np.broadcast_to(np.arange(w)==w-1,(h,w))
    elif key=='top_edge':out=np.broadcast_to(np.arange(h)[:,None]==0,(h,w))
    elif key=='bottom_edge':out=np.broadcast_to(np.arange(h)[:,None]==h-1,(h,w))
    elif key=='row_even':out=np.broadcast_to(np.arange(h)[:,None]%2==0,(h,w))
    elif key=='col_even':out=np.broadcast_to(np.arange(w)%2==0,(h,w))
    elif key=='center_row':out=np.broadcast_to(np.arange(h)[:,None]==h//2,(h,w))
    elif key=='center_col':out=np.broadcast_to(np.arange(w)==w//2,(h,w))
    elif key.startswith('color_'):
        rest=key[len('color_'):]
        rank=next((r for r in ('smallest_id','largest_id','most','least') if rest==r or rest.startswith(r+'_')),None)
        if rank is None:raise KeyError(key)
        part=rest[len(rank):].lstrip('_')
        counts=count_fg(a)
        ranks=sorted(counts.items(),key=lambda e:(-e[1],e[0]))
        selection={'most':ranks[0][0] if ranks else None,
                   'least':ranks[-1][0] if ranks else None,
                   'smallest_id':min(counts) if counts else None,
                   'largest_id':max(counts) if counts else None}
        selected=selection[rank]
        mask=a==selected if selected is not None else np.zeros(a.shape,bool)
        if not part:out=mask
        elif part=='bbox':out=brect(mask)
        elif part=='border':out=border(mask)
        elif part=='boxholes':out=brect(mask)&~mask
        elif part=='enclosedholes':out=binary_fill_holes(mask)&~mask
        elif part=='rowspan':out=spans(mask,'h')
        elif part=='colspan':out=spans(mask,'v')
        elif part=='sym_lr_missing':out=np.fliplr(mask)&~mask
        elif part=='sym_ud_missing':out=np.flipud(mask)&~mask
        elif part=='sym_180_missing':out=np.rot90(mask,2)&~mask
        elif part=='rowcol_intersection':out=np.broadcast_to(mask.any(1)[:,None],a.shape)&np.broadcast_to(mask.any(0),a.shape)
        elif part in ('component_boxes','component_holes'):
            marks,n=label(mask,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
            boxes=np.zeros(a.shape,bool)
            for i in range(1,n+1):boxes|=brect(marks==i)
            out=boxes if part=='component_boxes' else boxes&~mask
        else:raise KeyError(key)
    else:raise KeyError(key)
    cache[key]=np.asarray(out,bool)
    return cache[key]

def run_lazy(input_grid,ast):
    a=np.asarray(input_grid,np.int16)
    kind,k1,k2=ast['mask_expression']
    memo={}
    m=lazy_predicate(a,k1,memo)
    if kind!='one':
        n=lazy_predicate(a,k2,memo)
        if kind=='and':m=m&n
        elif kind=='or':m=m|n
        elif kind=='xor':m=m^n
        elif kind=='and-not':m=m&~n
        else:raise KeyError(kind)
    color=paint(a,ast['paint_rule'])
    if color is None:return None
    return np.where(m,color,a).astype(np.int16)

def audit_semantics(seed=182,random_grids=180):
    rng=np.random.default_rng(seed)
    checks=0;keys=None
    for trial in range(random_grids):
        h=int(rng.integers(2,18));w=int(rng.integers(2,18))
        a=rng.choice([0,0,0,0,1,2,3,4,5,6,7,8,9],size=(h,w)).astype(np.int16)
        all_masks=geometries(a);keys=set(all_masks) if keys is None else keys
        assert set(all_masks)==keys
        cache={}
        for k,expect in all_masks.items():
            got=lazy_predicate(a,k,cache)
            assert np.array_equal(got,expect),(trial,k)
            checks+=1
    return {'seed':seed,'random_original_grammar_grids':random_grids,
            'typed_mask_keys':len(keys),'exact_boolean_predicate_checks':checks}
