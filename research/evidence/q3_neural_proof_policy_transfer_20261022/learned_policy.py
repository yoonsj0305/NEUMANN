#!/usr/bin/env python3
"""NEUMANN experimental cross-source learned proof search policy.

TRAIN exclusively from eight already opened sources' original checked MINIMIZED
invariants. Target only original bytes + full original SMT goal, not answer files.
A supervised *search policy*, NOT new AST primitives, invariant discovery ability,
or exclusive advantage over strong complete finite-class exact Houdini.
"""
import argparse, collections, hashlib, importlib.util, json, pathlib, random, re, sys, time, zipfile
import numpy as np
import torch

PARSER=None

def load_engine(path):
 global PARSER
 spec=importlib.util.spec_from_file_location('neumann_frozen_source',path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);PARSER=mod

def separate_and(expr):
 text=expr.strip()
 if not text.startswith('(and '):return [text]
 inner=text[5:-1].strip(); out=[];k=0
 while k<len(inner):
  if inner[k].isspace():k+=1;continue
  if inner[k]=='(':
   atom=PARSER.balanced(inner,k);out.append(atom);k+=len(atom)
  else:
   q=inner.find(' ',k);q=q if q!=-1 else len(inner);out.append(inner[k:q]);k=q
 return out

def sources_for(raw):
 names,fs,fns=PARSER.parse(raw)
 decl='\n'.join(f'(declare-const {v} Int)\n(declare-const {v}! Int)' for v in names)
 head='(set-logic LIA)\n'+decl+'\n'+'\n'.join(fs)+'\n'
 pre='('+fns[0]+' '+' '.join(names)+')'
 trans='('+fns[1]+' '+' '.join(names+[v+'!' for v in names])+')'
 post='('+fns[2]+' '+' '.join(names)+')'
 return names,fs,head,pre,trans,post

def features(atom,names,fs):
 # Source-only predicate AST's structure, language-agnostic by variable index.
 # Does not encode source filename, per-benchmark labels or correctness.
 non_post=not atom.startswith('(post-f ') and '(post-f ' not in atom
 variables=[v for v in names if re.search(r'(?<![\w!])'+re.escape(v)+r'(?![\w!])',atom)]
 n=len(names);support=len(variables)
 eq=int(atom.startswith('(= '));le=int(atom.startswith('(<= '));ge=int(atom.startswith('(>= '));guard=int(atom.startswith('(=> '))
 bound_match=re.search(r'\s(\(-\s*\d+\)|-?\d+)\)$',atom)
 bound=0
 if bound_match:
  s=bound_match.group(1);bound=-int(re.findall(r'\d+',s)[0]) if s.startswith('(-') else int(s)
 init=fs[0];trans=fs[1];post=fs[2]
 pre_occ=sum(len(re.findall(r'(?<![\w!])'+re.escape(v)+r'(?![\w!])',init)) for v in variables)
 trans_occ=sum(len(re.findall(r'(?<![\w!])'+re.escape(v)+r'(?![\w!])',trans)) for v in variables)
 post_occ=sum(len(re.findall(r'(?<![\w!])'+re.escape(v)+r'(?![\w!])',post)) for v in variables)
 neg=atom.count('(- ');times=atom.count('(* ')
 return [min(n,5)/5, support/5, eq,le,ge,guard,min(abs(bound),5)/5,int(bound>0),int(bound<0),min(neg,5)/5,min(pre_occ,15)/15,min(trans_occ,30)/30,min(post_occ,15)/15,min(len(atom),90)/90,times/5,int(non_post)]

def candidate_pool(names,fs,max_support=4):
 pool=list(PARSER.pred_pool(names,fs[0]+fs[1],max_support=max_support))
 return pool

def train(dev_dir, min_archive, manifest, seed=19):
 torch.set_num_threads(1);torch.manual_seed(seed); random.seed(seed);np.random.seed(seed)
 dataset=[];details=[]
 with zipfile.ZipFile(min_archive) as z: mins=json.loads(z.read('dev8_minimized.json'))
 min_by={r['original_name']:r for r in mins['cases']}
 entries=json.loads(manifest.read_text())['cases']
 for e in entries:
  raw=(dev_dir/e['name']).read_bytes();g=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
  assert g==e['sha'],(e['name'],g,e['sha'])
  names,fs,*_=sources_for(raw.decode());pool=candidate_pool(names,fs)
  positives=set(separate_and(min_by[e['name']]['minimized_invariant']))
  # Include only source-operator predicates, exclude original Post and grammar-missing.
  eligible=[a for a in pool if a!='true']; tp=[a for a in eligible if a in positives]
  details.append(dict(case=e['name'],pool=len(pool),minimized=len(positives),matched=len(tp),missing=sorted(positives-set(pool))[:2]))
  for a in eligible:dataset.append((features(a,names,fs),int(a in positives),e['name']))
 X=np.asarray([r[0] for r in dataset],dtype=np.float32)
 y=np.asarray([r[1] for r in dataset],dtype=np.float32)
 mean=X.mean(axis=0);sd=np.maximum(X.std(axis=0),0.05)
 tx=torch.from_numpy((X-mean)/sd);ty=torch.from_numpy(y)
 network=torch.nn.Sequential(torch.nn.Linear(X.shape[1],24),torch.nn.Tanh(),torch.nn.Linear(24,8),torch.nn.Tanh(),torch.nn.Linear(8,1))
 loss_fn=torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor(max(1.0,len(y)/max(1,sum(y))/2),dtype=torch.float32))
 optimizer=torch.optim.Adam(network.parameters(),lr=0.012,weight_decay=0.004)
 tic=time.monotonic()
 for step in range(500):
  optimizer.zero_grad();v=network(tx).flatten();loss=loss_fn(v,ty);loss.backward();optimizer.step()
 train_seconds=time.monotonic()-tic
 with torch.no_grad():score=torch.sigmoid(network(tx)).flatten().numpy()
 return network,mean,sd,dict(samples=len(y),positive=int(y.sum()),train_s=round(train_seconds,5),final_loss=round(float(loss),6),source_details=details,training_origins=[e['name'] for e in entries],training_sha256=hashlib.sha256(min_archive.read_bytes()+manifest.read_bytes()).hexdigest())

def scored(pool,names,fs,net,mean,sd,mode,seed=19):
 if mode=='learned':
  X=np.asarray([features(x,names,fs) for x in pool],dtype=np.float32)
  with torch.no_grad():v=net(torch.from_numpy((X-mean)/sd)).flatten().numpy().tolist()
 elif mode=='no_training':
  torch.manual_seed(seed+3);untrained=torch.nn.Sequential(torch.nn.Linear(16,24),torch.nn.Tanh(),torch.nn.Linear(24,8),torch.nn.Tanh(),torch.nn.Linear(8,1))
  X=np.asarray([features(x,names,fs) for x in pool],dtype=np.float32)
  with torch.no_grad():v=untrained(torch.from_numpy((X-mean)/sd)).flatten().numpy().tolist()
 elif mode=='static':
  # Source-independent simple admissible ordering, favors lower-degree simpler terms.
  v=[-(len([x for x in names if re.search(r'(?<![\w!])'+re.escape(x)+r'(?![\w!])',a)])*2.0) + (2 if a.startswith('(= ') else 0) -0.0001*len(a) for a in pool]
 elif mode=='random':
  r=random.Random(seed);v=[r.random() for _ in pool]
 else:raise ValueError(mode)
 return [pool[i] for i in sorted(range(len(pool)),key=lambda k:(-v[k],k))]

def run_houdini(head,pre,trans,post,names,atoms):
 # Only certify against original complete unreduced source. A failed attempt is
 # not admissible as success; UNKNOWN removes candidates and cannot grant SAFE.
 tic=time.monotonic();q=0
 pool=list(dict.fromkeys(list(atoms)+[post]));start_n=len(pool)
 init=PARSER.check_batch(head,[f'(and {pre} (not {a}))' for a in pool]);q+=len(pool)
 keep=[a for a,b in zip(pool,init) if b=='unsat'];rounds=0
 for i in range(8):
  rounds+=1;premise=PARSER.conj(keep)
  vc=PARSER.check_batch(head,[f'(and {premise} {trans} (not {PARSER.ren(a,names)}))' for a in keep]);q+=len(keep)
  new=[a for a,b in zip(keep,vc) if b=='unsat']
  if len(new)==len(keep):keep=new;break
  keep=new
 inv=PARSER.conj(keep)
 vc=PARSER.check_batch(head,[f'(and {pre} (not {inv}))',f'(and {inv} {trans} (not {PARSER.ren(inv,names)}))',f'(and {inv} (not {post}))']);q+=3
 return dict(original_3vc=vc,safe_certified=vc==['unsat']*3,invariant=inv if vc==['unsat']*3 else None,retained=len(keep),initial=start_n,rounds=rounds,queries=q,wall_s=round(time.monotonic()-tic,5))

def git_sha(raw):return hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()

def main():
 pa=argparse.ArgumentParser();pa.add_argument('--engine',type=pathlib.Path,required=True);pa.add_argument('--dev-dir',type=pathlib.Path,required=True);pa.add_argument('--dev-manifest',type=pathlib.Path,required=True);pa.add_argument('--min-archive',type=pathlib.Path,required=True);pa.add_argument('--target-dir',type=pathlib.Path,required=True);pa.add_argument('--target-manifest',type=pathlib.Path,required=True);pa.add_argument('--out',type=pathlib.Path,required=True);a=pa.parse_args()
 load_engine(a.engine);alltime=time.monotonic()
 net,mean,sd,train_record=train(a.dev_dir,a.min_archive,a.dev_manifest)
 manifest=json.loads(a.target_manifest.read_text());cases=[]
 # A fixed identical small source-grammar budget, no per-target changes.
 budgets=[24,48,96]
 for m in manifest['cases']:
  row=dict(file=m['name'],expected_sha=m['sha'],routes={});tic=time.monotonic()
  try:
   raw=(a.target_dir/m['name']).read_bytes();assert len(raw)==m['size'] and git_sha(raw)==m['sha'],'TARGET_SOURCE_MISMATCH'
   names,fs,head,pre,trans,post=sources_for(raw.decode());pool=candidate_pool(names,fs,4)
   postonly=PARSER.check_batch(head,[f'(and {pre} (not {post}))',f'(and {post} {trans} (not {PARSER.ren(post,names)}))'])
   row['post_only']=postonly;row['candidate_pool']=len(pool)
   if postonly==['unsat','unsat']:
    for mode in ['learned','no_training','static','random','full']:
     row['routes'][mode]=dict(safe_certified=True,invariant=PARSER.conj([post]),original_3vc=['unsat']*3,queries=2,wall_s=0,budget=0)
   else:
    for mode in ['learned','no_training','static','random','full']:
     try:
      order=scored(pool,names,fs,net,mean,sd,mode) if mode!='full' else pool
      variants=[]
      for n in ([len(pool)] if mode=='full' else budgets):
       x=run_houdini(head,pre,trans,post,names,order[:n]);x['budget']=n;variants.append(x)
       if x['safe_certified']:break
      first=next((x for x in variants if x['safe_certified']),variants[-1]);first=dict(first)
      first['total_queries_including_failed']=sum(x['queries'] for x in variants)
      first['total_wall_s_including_failed']=round(sum(x['wall_s'] for x in variants),5)
      first['retries']=len(variants)
      row['routes'][mode]=first
     except Exception as ex:
      row['routes'][mode]=dict(safe_certified=False,invariant=None,status='ABSTAIN',reason=type(ex).__name__+': '+str(ex)[:140],retries=0)

   row['status']='COMPLETE'
  except Exception as exc:row['status']='ABSTAIN';row['reason']=type(exc).__name__+': '+str(exc)[:180]
  row['wall_s']=round(time.monotonic()-tic,5);cases.append(row)
  print('CROSS_SOURCE',row['file'],row['status'],{k:(v['safe_certified'],v.get('budget'),v.get('total_queries_including_failed')) for k,v in row['routes'].items()},flush=True)
 scores={x:sum(c['routes'].get(x,{}).get('safe_certified',False) for c in cases) for x in ['learned','no_training','static','random','full']}
 rec=dict(schema='neumann.q3.weight_transfer_proof_policy.v1',trained_on='dev8 previously opened original minimizer certificates ONLY',target_status='posthoc previously opened original source bodies, model not source-trained',candidate_grammar='existing frozen affine and guards, NO new operator invention',training=train_record,source_manifest_sha256=hashlib.sha256(a.target_manifest.read_bytes()).hexdigest(),cases=cases,matched_scores=scores,wall_s=round(time.monotonic()-alltime,5),global_Q3='OPEN')
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(rec,ensure_ascii=False,indent=2)+'\n');print('FINAL',scores,'SHA256',hashlib.sha256(a.out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()