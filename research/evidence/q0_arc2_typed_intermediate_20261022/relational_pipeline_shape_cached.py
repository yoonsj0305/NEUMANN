#!/usr/bin/env python3
"""Task-local intermediate-object program synthesis. Input demonstrations only for generation and ranking.
Typed AST: SelectRegion -> D4 -> Scale -> Tile -> fitted uniform output color map.
No eval/test truth access by proposer, no artificial success claim. Fail closed on unknown.
"""
import argparse,hashlib,json,time,pathlib,collections,sys
import numpy as np
from scipy.ndimage import label

def asarr(x):return np.asarray(x,dtype=np.int16)
def key(x):return (x.shape,x.tobytes())
def box(a,mask):
    pos=np.argwhere(mask)
    if not len(pos):return None
    low=pos.min(axis=0);hi=pos.max(axis=0)
    return a[low[0]:hi[0]+1,low[1]:hi[1]+1].copy()
def colors(a):
    v,n=np.unique(a,return_counts=True);d=[(int(x),int(y)) for x,y in zip(v,n) if int(x)!=0]
    return d

def color_select(a,kind):
    q=colors(a)
    if not q:return None
    if kind=='most':return sorted(q,key=lambda z:(-z[1],z[0]))[0][0]
    if kind=='least':return sorted(q,key=lambda z:(z[1],z[0]))[0][0]
    if kind=='lowest':return min(z[0] for z in q)
    if kind=='highest':return max(z[0] for z in q)
    if kind=='only':return q[0][0] if len(q)==1 else None
    if kind=='second_most':return sorted(q,key=lambda z:(-z[1],z[0]))[1][0] if len(q)>=2 else None
    if kind=='second_least':return sorted(q,key=lambda z:(z[1],z[0]))[1][0] if len(q)>=2 else None
    if kind.startswith('c'):return int(kind[1:]) if any(z[0]==int(kind[1:]) for z in q) else None
    return None

def regions(x,conn):
    st=np.ones((3,3),int) if conn==8 else np.array([[0,1,0],[1,1,1],[0,1,0]])
    objs=[]
    for color,_ in colors(x):
        labels,count=label(x==color,structure=st)
        for i in range(1,count+1):
            m=labels==i;pos=np.argwhere(m)
            if not len(pos):continue
            low=pos.min(0);hi=pos.max(0)
            objs.append(dict(color=color,mask=m,area=len(pos),top=int(low[0]),left=int(low[1]),bottom=int(hi[0]),right=int(hi[1]),h=int(hi[0]-low[0]+1),w=int(hi[1]-low[1]+1)))
    return objs

def select(x,sel,cache=None):
    typ=sel[0]
    if typ=='whole':return x
    if typ=='crop_fg':return box(x,x!=0)
    if typ in ('crop_color','crop_mask_color','drop_color','isolate_color'):
        color=color_select(x,sel[1])
        if color is None:return None
        mask=x==color
        if typ=='crop_color':return box(x,mask)
        if typ=='crop_mask_color':return box(np.where(mask,x,0),mask)
        if typ=='drop_color':return np.where(mask,0,x)
        return np.where(mask,x,0)
    if typ=='component':
        conn=sel[2];which=sel[1];style=sel[3]
        if cache is not None:
            if conn not in cache:cache[conn]=regions(x,conn)
            objects=cache[conn]
        else:objects=regions(x,conn)
        if not objects:return None
        keys={'largest':lambda o:(-o['area'],o['top'],o['left']),
              'smallest':lambda o:(o['area'],o['top'],o['left']),
              'top':lambda o:(o['top'],o['left']),'left':lambda o:(o['left'],o['top']),
              'bottom':lambda o:(-o['bottom'],o['left']),'right':lambda o:(-o['right'],o['top']),
              'tallest':lambda o:(-o['h'],o['left']),'widest':lambda o:(-o['w'],o['top'])}
        if which not in keys:return None
        o=min(objects,key=keys[which]);
        if style=='global':return box(x,o['mask'])
        if style=='mask':return box(np.where(o['mask'],x,0),o['mask'])
    if typ=='strip':
        axis=sel[1];
        if axis=='both':return box(x,x!=0)
        if axis=='rows':return x[np.any(x!=0,axis=1),:]
        if axis=='cols':return x[:,np.any(x!=0,axis=0)]
    return None

def d4(x,t):
    if t=='id':return x
    if t=='lr':return np.fliplr(x)
    if t=='ud':return np.flipud(x)
    if t=='r90':return np.rot90(x,1)
    if t=='r180':return np.rot90(x,2)
    if t=='r270':return np.rot90(x,3)
    if t=='tr':return x.T
    if t=='anti':return np.rot90(x,2).T
    raise ValueError(t)

def geom(x,t,k,rep):
    q=d4(x,t)
    if k!=1:q=np.repeat(np.repeat(q,k,axis=0),k,axis=1)
    if rep=='h2':q=np.tile(q,(1,2))
    if rep=='v2':q=np.tile(q,(2,1))
    if rep=='hv2':q=np.tile(q,(2,2))
    if rep=='h3':q=np.tile(q,(1,3))
    if rep=='v3':q=np.tile(q,(3,1))
    if q.size==0 or max(q.shape)>30:return None
    return q

def uniform_color_map(a,b,lookup):
    if a.shape!=b.shape:return False
    for col in np.unique(a):
        targets=np.unique(b[a==col])
        if len(targets)!=1:return False
        col=int(col);tar=int(targets[0]);old=lookup.get(col)
        if old is not None and old!=tar:return False
        lookup[col]=tar
    return True

def mapped(a,m):
    if a is None:return None
    return np.array([m.get(int(z),int(z)) for z in a.ravel()],dtype=np.int16).reshape(a.shape)

def task_rules(task,limit=0):
    pairs=task['train'];first=asarr(pairs[0]['input']);first_target=asarr(pairs[0]['output']);
    col_kinds=('most','least','lowest','highest','only','second_most','second_least')+tuple('c'+str(x) for x,_ in colors(first))
    selectors=[('whole',),('crop_fg',),('strip','rows'),('strip','cols')]
    for color in col_kinds:
        for kind in ('crop_color','crop_mask_color','drop_color','isolate_color'):selectors.append((kind,color))
    for conn in (4,8):
        for which in ('largest','smallest','top','left','bottom','right','tallest','widest'):
            for style in ('global','mask'):selectors.append(('component',which,conn,style))
    trans=('id','lr','ud','r90','r180','r270','tr','anti')
    out=[];count=0;region_cache={}
    for sel in selectors:
        try:y0=select(first,sel,region_cache)
        except (ValueError,IndexError):continue
        if y0 is None or not y0.size:continue
        for k in (1,2,3):
            for rep in ('none','h2','v2','hv2','h3','v3'):
                for t in trans:
                    # Syntactic shape/type admission: if the output size cannot match,
                    # skip ALL intermediate ndarray allocation and all pixel operations.
                    h0,w0=y0.shape
                    if t in ('r90','r270','tr','anti'):h0,w0=w0,h0
                    h0*=k;w0*=k
                    if rep=='h2':w0*=2
                    elif rep=='v2':h0*=2
                    elif rep=='hv2':h0*=2;w0*=2
                    elif rep=='h3':w0*=3
                    elif rep=='v3':h0*=3
                    if (h0,w0)!=first_target.shape:continue
                    z0=geom(y0,t,k,rep)
                    if z0 is None or z0.shape!=first_target.shape:continue
                    lookup={}
                    if not uniform_color_map(z0,first_target,lookup):continue
                    success=True
                    for pair in pairs[1:]:
                        u=select(asarr(pair['input']),sel)
                        if u is None:success=False;break
                        u=geom(u,t,k,rep)
                        if u is None or not uniform_color_map(u,asarr(pair['output']),lookup):success=False;break
                    if not success:continue
                    # Replay all pairs to ensure later mapping didn't silently invalidate prior observations
                    for pair in pairs:
                        u=select(asarr(pair['input']),sel)
                        if u is None:success=False;break
                        u=geom(u,t,k,rep)
                        if u is None or not np.array_equal(mapped(u,lookup),asarr(pair['output'])):success=False;break
                    if not success:continue
                    rule={'select':sel,'transform':t,'scale':k,'tile':rep,'mapping':lookup}
                    out.append(rule);count+=1
                    if limit and count>=limit:return out
    return out

def complexity(p):
    s=p['select'];typ=s[0]
    return (1+(0 if typ=='whole' else 2)+(0 if p['transform']=='id' else 1)+(0 if p['scale']==1 else 2)+(0 if p['tile']=='none' else 2)+len([1 for a,b in p['mapping'].items() if a!=b]),str(s),p['transform'],p['scale'],p['tile'])

def predict(task,rule):
    out=[]
    for ex in task['test']:
        x=select(asarr(ex['input']),tuple(rule['select']))
        if x is None:return None
        x=geom(x,rule['transform'],rule['scale'],rule['tile'])
        if x is None:return None
        out.append(mapped(x,rule['mapping']).tolist())
    return out

def main():
    par=argparse.ArgumentParser();par.add_argument('--data',required=True);par.add_argument('--freeze',required=True);par.add_argument('--subset',choices=['dev','holdout'],default='dev');par.add_argument('--limit',type=int,default=0);par.add_argument('--offset',type=int,default=0);par.add_argument('--out',required=True);a=par.parse_args()
    files=list(pathlib.Path(a.data).glob('*.json'));assert len(files)==1000
    files.sort(key=lambda x:hashlib.sha256(x.stem.encode()).hexdigest())
    reg=json.load(open(a.freeze));df=files[:800];hf=files[800:]
    digest=lambda f:hashlib.sha256(('\n'.join(x.stem for x in f)+'\n').encode()).hexdigest()
    assert digest(df)==reg['dev_id_sha256'] and digest(hf)==reg['val_id_sha256']
    selected=df if a.subset=='dev' else hf
    selected=selected[a.offset:]
    if a.limit:selected=selected[:a.limit]
    start=time.perf_counter();records=[]
    for idx,f in enumerate(selected):
        task=json.loads(f.read_text());masked={'train':task['train'],'test':[{'input':q['input']} for q in task['test']]};
        rules=task_rules(masked)
        best=min(rules,key=complexity) if rules else None
        result=predict(masked,best) if best else None
        records.append({'id':f.stem,'num_candidates':len(rules),'candidate':best,'pred':result,'rule_types':list(sorted({r['select'][0] for r in rules}))})
        if (idx+1)%40==0:print('PROGRESS',idx+1,'coverage',sum(r['num_candidates']>0 for r in records),'wall',time.perf_counter()-start,flush=True)
    p=pathlib.Path(a.out);p.parent.mkdir(exist_ok=True,parents=True)
    payload={'schema':'NEUMANN_OBJECT_RELATIONAL_TYPED_COMPOSITION_V0','status':'DEVELOPMENT_UNLESS_FROZEN','subset':a.subset,'num':len(selected),'wall_s':time.perf_counter()-start,'coverage':sum(r['num_candidates']>0 for r in records),'records':records};p.write_text(json.dumps(payload,sort_keys=True))
    print('DONE',len(selected),'coverage',payload['coverage'],'wall',payload['wall_s'],flush=True)
if __name__=='__main__':main()
