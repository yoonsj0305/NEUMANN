#!/usr/bin/env python3
"""Original-source SMT-guided conjunct removal, NO manual invariant or benchmark basename branch.
Keep a candidate only if FULL original pre/step/post 3VC are UNSAT. This is a
certificate compaction operation, not source-only invariant synthesis.
Upstream generator and its total cost are NOT free.
"""
import argparse,hashlib,json,pathlib,re,sys,time,statistics
from select_verified_upper_k import Z3,atoms,balanced,original_vc

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-dir',type=pathlib.Path,required=True);p.add_argument('--manifest',type=pathlib.Path,required=True)
 p.add_argument('--proposals',type=pathlib.Path,required=True);p.add_argument('--upper',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--order',choices=['as_given','reverse'],default='as_given')
 a=p.parse_args();start=time.perf_counter();z=Z3();d=json.load(open(a.proposals));m=json.load(open(a.manifest));K=json.load(open(a.upper))['proven_upper_k'];out=[];total_calls=0
 for meta,c in zip(m['cases'],d['cases']):
  assert meta['name']==c['file']
  raw=(a.source_dir/meta['name']).read_bytes();assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==meta['sha']
  src=raw.decode();mm=re.search(r'\(synth-inv\s+[^\s()]+\s+',src);ns=re.findall(r'\(\s*([^\s()]+)\s+Int\s*\)',balanced(src,mm.end()))
  current=[atom for atom in atoms(c['invariant']) if sum(n in set(re.findall(r'[A-Za-z_!][A-Za-z_0-9!]*',atom)) for n in ns)<=K[meta['name']]]
  initial=list(current);checked=0;rejections=[]
  def check(seq):
   nonlocal checked,total_calls
   q=original_vc(src,seq,ns)
   statuses={}
   for key,script in q.items():
    r=z.check(script);checked+=1;total_calls+=1;statuses[key]=r
    if r!='unsat':break
   return len(statuses)==3 and all(x=='unsat' for x in statuses.values()),statuses
  valid,_=check(current);assert valid,(meta['name'],'invalid starting candidate')
  candidates=list(reversed(initial)) if a.order=='reverse' else initial[:]
  for term in candidates:
   if term not in current:continue
   trial=current.copy();trial.remove(term)
   valid,statuses=check(trial)
   if valid:current=trial
   else:rejections.append({'atom':term,'stage':next((k for k,v in statuses.items() if v!='unsat'),'UNKNOWN')})
  valid,_=check(current);assert valid
  old_chars=len('(and '+' '.join(initial)+')');new_chars=len('(and '+' '.join(current)+')')
  out.append({'file':meta['name'],'source_algorithm':'EXACT_FULL_ORIGINAL_3VC_GREEDY_ATOM_DELETION',
    'safe_certified':True,'invariant':'(and '+' '.join(current)+')' if current else 'true',
    'original_atoms':len(initial),'pruned_atoms':len(current),'original_chars':old_chars,'pruned_chars':new_chars,
    'deleted_atoms':len(initial)-len(current),'original_source_sha':meta['sha'],
    'checks_from_source_pre_trans_post':checked,'retained_atoms':current,'blocked_deletions':rejections})
  print('ORIGINAL_PROOF_ATOM_PRUNING',meta['name'],'atoms',len(initial),'->',len(current),'chars',old_chars,'->',new_chars,'Z3-VC-calls',checked,flush=True)
 r={'schema':'NEUMANN.Q4.source_exact_reusable_proof_compaction.v1','cases':out,'order':a.order,'total_original_z3_vc_calls':total_calls,
 'total_old_atoms':sum(x['original_atoms'] for x in out),'total_compacted_atoms':sum(x['pruned_atoms'] for x in out),
 'total_old_characters':sum(x['original_chars'] for x in out),'total_compacted_characters':sum(x['pruned_chars'] for x in out),
 'wall_s':round(time.perf_counter()-start,6),'scope':'Four already-opened SyGuS programs, human-free but exact classical no neural method. Greedy certificate subset minimality not mathematically global minimal clause count.'}
 a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
 print('PROOF_CERTIFICATE_COMPACTION_SUMMARY',json.dumps({k:r[k] for k in ['total_original_z3_vc_calls','total_old_atoms','total_compacted_atoms','total_old_characters','total_compacted_characters','wall_s']}),flush=True)
if __name__=='__main__':main()
