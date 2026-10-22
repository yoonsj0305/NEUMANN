#!/usr/bin/env python3
"""Composition of two zero-learning source-only engines; no gold or manual invariant.

This tool selects only ASTs that already passed exact original Z3 3VC in
separately executed frozen search engines. An INDEPENDENT Z3+cvc5 checker
is still required to admit a final source proof.
"""
import argparse,hashlib,json,pathlib

def main():
 p=argparse.ArgumentParser();p.add_argument('--affine',type=pathlib.Path,required=True);p.add_argument('--houdini',type=pathlib.Path,required=True);p.add_argument('--registry',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
 m=json.loads(a.registry.read_text());A=json.loads(a.affine.read_text());B=json.loads(a.houdini.read_text());
 assert len(m['cases'])==len(A['cases'])==len(B['cases'])==12
 ma={x['file']:x for x in A['cases']};mb={x['file']:x for x in B['cases']};rows=[]
 for obj in m['cases']:
  file=obj['name'];av=ma[file];bv=mb[file]
  if av.get('safe') and av.get('original_3vc')==['unsat']*3:
   arm='EXACT_SOURCE_AFFINE_GUARDED';selected=av['invariant']
  elif bv.get('safe_certified') and bv.get('whole_source_original_3vc')==['unsat']*3:
   arm='EXACT_SOURCE_FINITE_HOUDINI';selected=bv['invariant']
  else:arm='NO_AUTOMATIC_CERTIFICATE';selected=None
  rows.append({'file':file,'safe_certified':selected is not None,'invariant':selected,'source_algorithm':arm,'advanced_z3_3vc':av.get('original_3vc'),'classic_z3_3vc':bv.get('whole_source_original_3vc')})
 o={'schema':'neumann.q3.source_truth_automated_classical_union.v1','autonomous_no_manual_invariant_inputs':True,'firstblind':False,'new_neural_structure_invention':False,'cases':rows,'source_registry_sha256':hashlib.sha256(a.registry.read_bytes()).hexdigest(),'affine_receipt_sha256':hashlib.sha256(a.affine.read_bytes()).hexdigest(),'baseline_receipt_sha256':hashlib.sha256(a.houdini.read_bytes()).hexdigest(),'union_success':sum(x['safe_certified'] for x in rows),'source_denominator':len(rows),'unsafe_requires_separate_original_sat':True}
 a.out.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print('AUTONOMOUS_UNION',o['union_success'],'/',len(rows),'methods',{z:sum(c['source_algorithm']==z for c in rows) for z in ('EXACT_SOURCE_AFFINE_GUARDED','EXACT_SOURCE_FINITE_HOUDINI','NO_AUTOMATIC_CERTIFICATE')},flush=True)
if __name__=='__main__':main()
