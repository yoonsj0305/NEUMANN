#!/usr/bin/env python3
"""NEUMANN L0 external evidence: actual fitted per-program small decision tree of local rules.
Read ONLY ARC task demonstrations and TEST INPUT. Do not access target labels.
No claim of unique novel operator or frontier parity.
"""
import numpy as np
from sklearn.tree import DecisionTreeClassifier
import hashlib,json,argparse,zipfile,collections,time

OFFSETS=((0,0),(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1))

def features(g):
 g=np.asarray(g,dtype=np.int32); h,w=g.shape
 mode=collections.Counter(g.flatten().tolist()).most_common(1)[0][0]
 colorcounts=collections.Counter(g.flatten().tolist())
 low=min(colorcounts,key=lambda c:(colorcounts[c],c))
 X=[]
 for i in range(h):
  for j in range(w):
   center=int(g[i,j]); valid=[]; vals=[]
   for di,dj in OFFSETS[1:]:
    y,x=i+di,j+dj
    valid.append(0<=y<h and 0<=x<w)
    vals.append(int(g[y,x]) if valid[-1] else -1)
   hist=collections.Counter(v for v in vals if v>=0)
   same=sum(v==center for v in vals)
   nz=sum(v!=0 and v!=-1 for v in vals)
   f=[center, int(center==0), int(center==mode),int(center==low),i==0,j==0,i==h-1,j==w-1,
      int(i==h//2),int(j==w//2),i%2,j%2,h%2,w%2,
      min(i,h-1-i),min(j,w-1-j),same,nz, sum(v==mode for v in vals), sum(v==low for v in vals),
      colorcounts[center],colorcounts[center]//max(1,h*w//10),len(colorcounts), h,w]
   f+=valid
   f += [v==center for v in vals]
   f += [v==0 for v in vals]
   f += [v==mode for v in vals]
   f += [v==low for v in vals]
   f += [v if v>=0 else 10 for v in vals]
   f += [max(hist,key=lambda x:(hist[x],-x)) if hist else 0]
   X.append(f)
 return np.asarray(X,dtype=np.float32)

def attempt(task, max_depths=(1,2,3,4,5,6), budget_s=1.0):
 starts=time.perf_counter(); demos=task['train']
 if not demos or any(np.shape(d['input'])!=np.shape(d['output']) for d in demos):return {'status':'shape_mismatch'}
 # avoid pathological overtraining; typical ARC 30x30
 total_pixels=sum(len(d['input'])*len(d['input'][0]) for d in demos)
 if total_pixels>3500:return {'status':'data_cap'}
 X=np.concatenate([features(d['input']) for d in demos],axis=0)
 Y=np.concatenate([np.asarray(d['output'],dtype=np.int32).ravel() for d in demos])
 # Count a no-training direct center->output lookup: strong source-specific classical control.
 idx=0;lookup={};conflicting=False
 for d in demos:
  inp=np.asarray(d['input']);out=np.asarray(d['output'])
  for v,y in zip(inp.ravel().tolist(),out.ravel().tolist()):
   if v in lookup and lookup[v]!=y:conflicting=True
   lookup[v]=y
 mappingfit=not conflicting
 # Mathematical impossibility gate: any deterministic f(X) must map equal vectors to equal outputs.
 # If two original demonstration positions have identical ALL frozen model features
 # but different target values, no possible decision tree on this vocabulary can fit.
 feature_labels={}
 for feature_vec,target in zip(X,Y):
  key=feature_vec.tobytes(); label=int(target)
  if key in feature_labels and feature_labels[key]!=label:
   return {'status':'feature_collision','trained':False,'proof':'identical complete feature vectors imply incompatible labels','pixel_samples':len(Y),'mapping_fit':mappingfit}
  feature_labels[key]=label
 family=[]; fit_method=None
 for depth in max_depths:
  if time.perf_counter()-starts>budget_s:break
  model=DecisionTreeClassifier(max_depth=depth,random_state=182,min_samples_leaf=2,criterion='entropy')
  model.fit(X,Y)
  pred=model.predict(X)
  if np.array_equal(pred,Y):
   # exclude simple training-memorization by requiring >=2 demos and all demos exact; explicit early stop
   fit_method=(depth,int(model.tree_.node_count),model);break
 if fit_method is None:return {'status':'no_exact_fit','mapping_fit':mappingfit,'trained':True,'pixel_samples':len(Y)}
 depth,nodes,model=fit_method
 # Cross-demonstration gate: relearn the same transparent decision tree after
 # removing one full original example, predict that held-out example exactly.
 cv=[]
 for j,dj in enumerate(demos):
  others=demos[:j]+demos[j+1:]
  if not others:cv.append(False);continue
  Xcv=np.concatenate([features(t['input']) for t in others],axis=0)
  Ycv=np.concatenate([np.asarray(t['output'],dtype=np.int32).ravel() for t in others])
  mcv=DecisionTreeClassifier(max_depth=depth,random_state=182,min_samples_leaf=2,criterion='entropy')
  mcv.fit(Xcv,Ycv)
  predicted=mcv.predict(features(dj['input'])).reshape(np.asarray(dj['input']).shape)
  cv.append(np.array_equal(predicted,np.asarray(dj['output'])))
 outs=[];mappingouts=[]
 for test in task['test']:
  g=np.asarray(test['input']);o=model.predict(features(g)).reshape(g.shape).astype(int).tolist();outs.append(o)
  mappingouts.append([[lookup.get(int(z),int(z)) for z in row] for row in test['input']] if mappingfit else None)
 return {'status':'fit','depth':depth,'nodes':nodes,'prediction':outs,'baseline_color_lookup':mappingouts,'mapping_fit':mappingfit,'cv_all':all(cv),'cv_fraction':sum(cv)/len(cv),'model_cost_s':time.perf_counter()-starts,'pixel_samples':len(Y),'trained':True}

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--zip',required=True);ap.add_argument('--subset',choices=['dev','valid'],required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 with zipfile.ZipFile(a.zip) as z:
  ids=[n.split('/')[-1][:-5] for n in z.namelist() if n.startswith('training/') and n.endswith('.json')]
  ids.sort(key=lambda v:hashlib.sha256(v.encode()).hexdigest());ids=ids[:800] if a.subset=='dev' else ids[800:]
  rows={};t=time.perf_counter()
  for n,id in enumerate(ids):
   d=json.loads(z.read('training/'+id+'.json'))
   # SAT/GATE no use test outputs, removed even when present in file
   masked={'train':d['train'],'test':[{'input':q['input']} for q in d['test']]}
   rows[id]=attempt(masked)
  result={'schema':'NEUMANN_REAL_TASK_LOCAL_LEARNED_RULE.v1','subset':a.subset,'count':len(ids),'source':'ARC2 published TRAIN only','test_label_access':False,'id_sha256':hashlib.sha256(('\n'.join(ids)+'\n').encode()).hexdigest(),'wall_s':time.perf_counter()-t,'rows':rows}
  open(a.out,'w').write(json.dumps(result,sort_keys=True)+'\n')
  print('COUNTS',collections.Counter(x['status'] for x in rows.values()),'FITS',[(n,x['depth']) for n,x in rows.items() if x['status']=='fit'][:30],'TOTAL_WALL',result['wall_s'],flush=True)
