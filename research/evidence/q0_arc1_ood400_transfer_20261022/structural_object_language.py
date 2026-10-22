#!/usr/bin/env python3
"""NEUMANN Q0: source-demo-only relational object DSL for ARC-AGI-2.

Development on SHA-frozen ARC-2 TRAIN split; no evaluation outputs or holdout answers
enter selection. No claim that finite language is neural operator invention.
"""
import argparse, collections, hashlib, json, pathlib, time, sys
import numpy as np
from arc_minimal_controller import arr, do_transform, key
from arc_compositional_grammar import candidates_from_grammar,run_raw,apply_mapping,fit_mapping,program_complexity

DIHEDRAL=('identity','flip_lr','flip_ud','rot90','rot180','rot270','transpose','anti_transpose')

def bboxmask(x,m):
    pts=np.argwhere(m)
    if not len(pts):return None
    l=pts.min(axis=0);h=pts.max(axis=0)
    return x[l[0]:h[0]+1,l[1]:h[1]+1].copy()

def ccs_color(x, include_diagonal=False):
    h,w=x.shape;seen=np.zeros((h,w),bool);res=[]
    for i in range(h):
      for j in range(w):
        if x[i,j]==0 or seen[i,j]:continue
        color=int(x[i,j]);stack=[(i,j)];seen[i,j]=True;pts=[]
        while stack:
          a,b=stack.pop();pts.append((a,b))
          nb=[(a+1,b),(a-1,b),(a,b+1),(a,b-1)]
          if include_diagonal: nb +=[(a+1,b+1),(a+1,b-1),(a-1,b+1),(a-1,b-1)]
          for c,d in nb:
            if 0<=c<h and 0<=d<w and not seen[c,d] and x[c,d]==color:seen[c,d]=True;stack.append((c,d))
        res.append((color,pts))
    return res

def selected_color(x,kind):
    v,n=np.unique(x,return_counts=True);pairs=[(int(a),int(b)) for a,b in zip(v,n) if a!=0]
    if not pairs:return None
    if kind.startswith('fixed:'):
      c=int(kind.split(':')[1]);return c if c in v else None
    if kind=='max':return sorted(pairs,key=lambda p:(-p[1],p[0]))[0][0]
    if kind=='min':return sorted(pairs,key=lambda p:(p[1],p[0]))[0][0]
    if kind=='low':return min(a for a,b in pairs)
    if kind=='high':return max(a for a,b in pairs)
    if kind=='unique':return pairs[0][0] if len(pairs)==1 else None
    return None

def run_op(x,op):
    typ=op[0]
    if typ=='cc':
      # monochrome component selected by area/position, then crop to its own bbox
      chosen=ccs_color(x,include_diagonal=(op[2]=='eight'))
      if not chosen:return None
      if op[1]=='largest':chosen.sort(key=lambda c:(-len(c[1]),min(c[1])))
      elif op[1]=='smallest':chosen.sort(key=lambda c:(len(c[1]),min(c[1])))
      elif op[1]=='top':chosen.sort(key=lambda c:min(c[1]))
      elif op[1]=='bottom':chosen.sort(key=lambda c:min(c[1]),reverse=True)
      elif op[1]=='left':chosen.sort(key=lambda c:(min(p[1] for p in c[1]),min(p[0] for p in c[1])))
      elif op[1]=='right':chosen.sort(key=lambda c:(max(p[1] for p in c[1]),-min(p[0] for p in c[1])),reverse=True)
      color,pts=chosen[0]
      ys=[p[0] for p in pts];xs=[p[1] for p in pts];r0=min(ys);c0=min(xs)
      q=np.zeros((max(ys)-r0+1,max(xs)-c0+1),np.int8)
      for i,j in pts:q[i-r0,j-c0]=color
      if op[3]=='global':return x[r0:max(ys)+1,c0:max(xs)+1].copy()
      return q
    if typ=='color':
      sel=selected_color(x,op[1]);
      if sel is None:return None
      mask=x==sel
      if op[2]=='crop_global':return bboxmask(x,mask)
      if op[2]=='crop_mask':return bboxmask(np.where(mask,x,0).astype(np.int8),mask)
      if op[2]=='mask_same':return np.where(mask,x,0).astype(np.int8)
      if op[2]=='remove':return np.where(mask,0,x).astype(np.int8)
      if op[2]=='crop_other':return bboxmask(x,x!=sel)
      return None
    if typ=='compress':
      color=op[1];axis=op[2]
      if color=='bg':
        v,n=np.unique(x,return_counts=True);color=int(v[np.argmax(n)])
      if axis=='rows':return x[np.any(x!=color,axis=1),:].copy() if np.any(x!=color) else None
      if axis=='cols':return x[:,np.any(x!=color,axis=0)].copy() if np.any(x!=color) else None
      r=np.any(x!=color,axis=1);c=np.any(x!=color,axis=0)
      return x[np.ix_(r,c)].copy() if np.any(r) and np.any(c) else None
    if typ=='canvas':
      op_=op[1]; color=op[2]
      m=x!=0;
      if not np.any(m):return None
      q=np.zeros_like(x)
      if color=='major':
        v,n=np.unique(x[m],return_counts=True);col=int(v[np.argmax(n)])
      else:col=selected_color(x,color)
      if col is None:return None
      if op_=='fill_all':q[m]=col
      elif op_=='bbox':
        pts=np.argwhere(m);l=pts.min(0);h=pts.max(0);q[l[0]:h[0]+1,l[1]:h[1]+1]=col
      elif op_=='outline':
        pts=np.argwhere(m);l=pts.min(0);h=pts.max(0);q[l[0],l[1]:h[1]+1]=col;q[h[0],l[1]:h[1]+1]=col;q[l[0]:h[0]+1,l[1]]=col;q[l[0]:h[0]+1,h[1]]=col
      return q
    if typ=='concat':
      how=op[1];y=do_transform(x,op[2])
      if how=='horizontal':z=np.concatenate((x,y),axis=1)
      elif how=='vertical':z=np.concatenate((x,y),axis=0)
      elif how=='h3':z=np.concatenate((x,y,x),axis=1)
      elif how=='v3':z=np.concatenate((x,y,x),axis=0)
      else:return None
      return z if max(z.shape)<=30 else None
    if typ=='geometry':
      y=do_transform(x,op[1]);post=op[2]
      if post=='remove_bg':return bboxmask(y,y!=0)
      if post=='compress':
        r=np.any(y!=0,axis=1);c=np.any(y!=0,axis=0)
        return y[np.ix_(r,c)].copy() if np.any(r) and np.any(c) else None
      return None
    return None

def structural_ops(task):
    colors=set()
    for q in task['train']:
      colors.update(np.unique(arr(q['input'])).tolist())
    csel=['max','min','low','high','unique']+['fixed:'+str(c) for c in sorted(colors) if c!=0]
    yield from (('cc',v,conn,shape) for v in ('largest','smallest','top','bottom','left','right') for conn in ('four','eight') for shape in ('mask','global'))
    yield from (('color',v,op) for v in csel for op in ('crop_global','crop_mask','mask_same','remove','crop_other'))
    yield from (('compress',v,op) for v in ('bg',0) for op in ('rows','cols','both'))
    yield from (('canvas',v,c) for v in ('fill_all','bbox','outline') for c in ('major','max','min'))
    yield from (('concat',v,t) for v in ('horizontal','vertical','h3','v3') for t in DIHEDRAL)
    yield from (('geometry',t,op) for t in DIHEDRAL for op in ('remove_bg','compress'))

def eval_op(grid,p):
    try:
      x=arr(grid)
      z=run_op(x,p)
      return z if z is not None and z.ndim==2 and min(z.shape)>0 and max(z.shape)<=30 else None
    except (ValueError,TypeError,IndexError,AssertionError):return None

def try_candidate(task,p):
    demos=task['train'];observations=[]
    for q in demos:
      inp=eval_op(q['input'],p)
      if inp is None:return None
      target=arr(q['output'])
      if inp.shape!=target.shape:return None
      observations.append((inp,target))
    if all(key(i)==key(o) for i,o in observations):return {}
    mapped={}
    for inp,out in observations:
      for col in np.unique(inp):
        vals=np.unique(out[inp==col]);
        if len(vals)!=1:return None
        old=int(col);new=int(vals[0]);
        if old in mapped and mapped[old]!=new:return None
        mapped[old]=new
    if all(np.array_equal(apply_mapping(i,mapped),o) for i,o in observations):return mapped
    return None

def all_candidates(task,stop_if_proven=False):
    # Fixed order: old 96 and 64 object operations, then new source-derived object/color/shape transforms
    prior=[]
    for p in candidates_from_grammar():
      mapping=fit_mapping(task['train'],p)
      if mapping is None:continue
      for q in task['train']:
        x=run_raw(q['input'],p)
        if not np.array_equal(apply_mapping(x,mapping),arr(q['output'])):break
      else:prior.append((('old',p),mapping))
    new=[]
    for op in structural_ops(task):
      m=try_candidate(task,op)
      if m is not None:new.append((('new',op),m))
    return prior,new

def predict_with(t,c):
    typ,p=c[0];m=c[1]
    out=[]
    for pair in t['test']:
      z=run_raw(pair['input'],p) if typ=='old' else eval_op(pair['input'],p)
      if z is None:return None
      z=apply_mapping(z,m) if m else z
      out.append(z.tolist())
    return out

def choice_key(c):
    typ,p=c[0];m=c[1];n=sum(k!=v for k,v in m.items())
    # Less brittle: exact transform/no recolor then color maps and geometric ops
    if typ=='old':complexity=1+(2 if p[0]=='object' else 0)+n+int(bool(m))
    else:
      if p[0]=='color':complexity=4+n+int(p[1].startswith('fixed:'))
      elif p[0]=='cc':complexity=5+n
      elif p[0]=='geometry':complexity=3+n
      elif p[0]=='compress':complexity=3+n
      elif p[0]=='canvas':complexity=4+n
      else:complexity=4+n
    return (complexity, repr(c[0]))

def run_task(t):
    task={'train':t['train'],'test':[{'input':q['input']} for q in t['test']]}
    a,b=all_candidates(task);original=min(a,key=choice_key) if a else None
    full=min(a+b,key=choice_key) if a+b else None
    return {'old_coverage':len(a),'new_coverage':len(b),'chosen':repr(full) if full else None,
            'selected_family':full[0][0] if full else None,
            'old_guess':predict_with(task,original) if original else None,
            'new_guess':predict_with(task,full) if full else None,
            'new_families':sorted(set(x[0][1][0] for x in b)),
            'count_all_candidates':len(a+b)}

def main():
 p=argparse.ArgumentParser();p.add_argument('--training-dir',required=True);p.add_argument('--freeze',required=True);p.add_argument('--subset',choices=('dev','holdout'),required=True);p.add_argument('--limit',type=int,default=0);p.add_argument('--out',required=True); a=p.parse_args()
 folder=pathlib.Path(a.training_dir);files=sorted(folder.glob('*.json'),key=lambda f:hashlib.sha256(f.stem.encode()).hexdigest())
 assert len(files)==1000
 reg=json.load(open(a.freeze));dev=files[:800];valid=files[800:]
 hashids=lambda ls:hashlib.sha256(('\n'.join(x.stem for x in ls)+'\n').encode()).hexdigest()
 assert hashids(dev)==reg['dev_id_sha256'] and hashids(valid)==reg['val_id_sha256']
 selected=dev if a.subset=='dev' else valid
 if a.limit:selected=selected[:a.limit]
 t0=time.perf_counter();results=[]
 for i,f in enumerate(selected):
    task=json.load(open(f)); result=run_task(task);result['id']=f.stem
    results.append(result)
    if (i+1)%25==0:print('RUNNING',a.subset,i+1,'COVERAGE',sum(x['new_coverage']+x['old_coverage']>0 for x in results),flush=True)
 raw={'source_split':a.subset,'firstblind':False,'n':len(results),'train_id_hash':reg['dev_id_sha256'],
      'validation_id_hash':reg['val_id_sha256'],'outputs_provided_to_solver':0,'wall_s':time.perf_counter()-t0,
      'baseline_demo_fit':sum(x['old_coverage']>0 for x in results),
      'structural_demo_fit':sum(x['new_coverage']>0 for x in results),'union_demo_fit':sum(x['new_coverage']+x['old_coverage']>0 for x in results),
      'rows':results}
 out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);b=json.dumps(raw,sort_keys=True,separators=(',',':')).encode();out.write_bytes(b)
 print('PREGRADE_SHA256',hashlib.sha256(b).hexdigest(),'WALL',raw['wall_s'],'COVER',raw['baseline_demo_fit'],raw['union_demo_fit'])

if __name__=='__main__':main()
