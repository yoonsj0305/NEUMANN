#!/usr/bin/env python3
"""Automatic source-derived upper certificate support filter; no manual invariants."""
import pathlib,json,re,argparse

def atoms(expr):
 txt=expr.strip()
 if not txt.startswith('(and '):return [txt]
 body=txt[5:-1].strip();found=[];j=0
 while j<len(body):
  if body[j].isspace():j+=1;continue
  if body[j]!='(':raise ValueError('not parenthesized')
  start=j;depth=0
  while j<len(body):
   depth+=(body[j]=='(')-(body[j]==')');j+=1
   if depth==0:break
  found.append(body[start:j])
 return found

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--proposals',required=True);ap.add_argument('--lower-bounds',required=True);ap.add_argument('--out',required=True)
 a=ap.parse_args();r=json.load(open(a.proposals));q=json.load(open(a.lower_bounds));out=[]
 for c in r['cases']:
  v=q['certified'][c['file']]
  names=v['variables'];k=v['necessary_support_at_least']
  cand=atoms(c['invariant'])
  keep=[];removed=[]
  for term in cand:
   toks=set(re.findall(r'[a-zA-Z_!][a-zA-Z_0-9!]*',term))
   sv=[name for name in names if name in toks]
   if len(sv)<=k:keep.append(term)
   else:removed.append({'term':term,'arity':len(sv)})
  inv='(and '+' '.join(keep)+')'
  out.append({'file':c['file'],'safe_certified':bool(c['safe']),'invariant':inv,'source_algorithm':'UNTRAINED_SOURCE_ONLY_SUPPORT_FILTER','count_total':len(cand),'count_kept':len(keep),'count_removed':len(removed),'removed':removed,'max_k':k})
  print(c['file'],'k=',k,'keep',len(keep),'remove',len(removed),flush=True)
 pathlib.Path(a.out).write_text(json.dumps({'cases':out,'status':'NO_GOLD_AUTOMATIC_MINIMAL_SUPPORT_FILTER'},indent=2)+'\n')
if __name__=='__main__':main()
