#!/usr/bin/env python3
"""Uniform original-Pre/Trans/Post BMC(0,1) source-grounded UNSAFE discovery.

Not a complete safety solver. SAT produces a real original reachable trace;
UNSAT or UNKNOWN is NEVER called SAFE. Independently recheck EVERY found
concrete witness with Z3 and (when requested) cvc5 against the exact original.
No target labels, fixed program names, or given winning traces in this code.
"""
import argparse,ctypes,hashlib,importlib.util,json,pathlib,re,subprocess,time

def import_engine(path):
 spec=importlib.util.spec_from_file_location('classic_source_parser',path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def import_ast_parser(path):
 spec=importlib.util.spec_from_file_location('generic_ast_reader',path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def num(node):
 if isinstance(node,str) and node.lstrip('-').isdigit():return int(node)
 if isinstance(node,list) and len(node)==2 and node[0]=='-':return -num(node[1])
 if isinstance(node,list) and len(node)==3 and node[0]=='+':return num(node[1])+num(node[2])
 raise ValueError('NONINTEGER_SMT_MODEL_VALUE_'+str(node))

def int_smt(a):return str(a) if a>=0 else '(- '+str(-a)+')'

def smt_original(raw,engine):
 names,forms,fns=engine.parse(raw)
 header='(set-logic LIA)\n'+'\n'.join('(declare-const '+v+' Int)\n(declare-const '+v+'! Int)' for v in names)+'\n'+'\n'.join(forms)+'\n'
 pre='('+fns[0]+' '+' '.join(names)+')'
 trans='('+fns[1]+' '+' '.join(names+[v+'!' for v in names])+')'
 post='('+fns[2]+' '+' '.join(names)+')'
 postp='('+fns[2]+' '+' '.join([v+'!' for v in names])+')'
 return names,header,pre,trans,post,postp

def z3_run(script,engine):
 lines=engine.z.run(script)
 statuses=[line.strip() for line in lines if line.strip() in ('sat','unsat','unknown')]
 if len(statuses)!=1:raise RuntimeError('Z3_INVALID_REPLY_'+str(lines[:10]))
 return statuses[0]

def cvc5_run(script):
 p=subprocess.run(['cvc5','--lang','smt2','--tlimit=10000'],input=script,text=True,capture_output=True,timeout=15)
 lines=[k.strip() for k in p.stdout.splitlines() if k.strip() in ('sat','unsat','unknown')]
 return lines[-1] if lines else 'ERROR_CVC5_'+p.stderr[-200:]

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-dir',type=pathlib.Path,required=True);p.add_argument('--registry',type=pathlib.Path,required=True);p.add_argument('--engine',type=pathlib.Path,required=True);p.add_argument('--ast-parser',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--cvc5',action='store_true');args=p.parse_args()
 eng=import_engine(args.engine);parser=import_ast_parser(args.ast_parser)
 reg=json.loads(args.registry.read_text());assert len(reg['cases'])==12
 start=time.monotonic();cases=[];total={'bmc_z3':0,'concrete_z3':0,'bmc_cvc5':0,'concrete_cvc5':0,'genuine_unsafes':0,'no_short_witness':0,'abstain':0}
 for case in reg['cases']:
  name=case['name'];row={'file':name,'schema':'source-only bounded original Pre/Trans/Post, never infer SAFE from depth limit','registered_sha':case['sha']}
  try:
   raw=(args.source_dir/name).read_bytes();git=hashlib.sha1(('blob '+str(len(raw))+'\0').encode()+raw).hexdigest()
   if git!=case['sha'] or len(raw)!=case['size']:raise ValueError('SOURCE_IDENTITY_MISMATCH')
   state,head,pre,tr,post,postp=smt_original(raw.decode(),eng)
   vars0=state;vars1=[v+'!' for v in state]
   attempts=[('depth0','(and '+pre+' (not '+post+'))',vars0),('depth1','(and '+pre+' '+tr+' (not '+postp+'))',vars0+vars1)]
   found=False;errors=[]
   for key,goal,vars_ in attempts:
    q=head+'\n(assert '+goal+')\n(check-sat)\n'
    zs=z3_run(q,eng);total['bmc_z3']+=1
    res={'z3':zs,'original_query_sha256':hashlib.sha256(q.encode()).hexdigest()}
    if args.cvc5:
     cv=cvc5_run(q);total['bmc_cvc5']+=1;res['cvc5']=cv
     if cv!=zs:raise RuntimeError('DUAL_BACKEND_BMC_DISAGREEMENT_'+str((zs,cv)))
    row[key]=res
    if zs=='sat':
     # A SAT answer alone is not enough for ground truth. Obtain every variable value.
     script=q+'(get-value ('+' '.join(vars_)+'))\n'
     lines=eng.z.run(script)
     pos=next((i for i,v in enumerate(lines) if v.strip()=='sat'),None)
     if pos is None:raise RuntimeError('Z3_SAT_MODEL_UNAVAILABLE')
     values='\n'.join(lines[pos+1:]).strip()
     a=parser.parse_sexpr(values)
     if not isinstance(a,list):raise RuntimeError('BAD_MODEL_PAIR_LIST')
     val={k:num(v) for k,v in a if isinstance(k,str)}
     if set(val)!=set(vars_):raise RuntimeError('MISSING_VARIABLE_IN_MODEL_'+str((set(val),set(vars_))))
     assignment=' '.join('(= '+v+' '+int_smt(val[v])+')' for v in vars_)
     grounded=head+'\n(assert (and '+goal+' '+assignment+'))\n(check-sat)\n'
     zz=z3_run(grounded,eng);total['concrete_z3']+=1
     cv='NOT_RUN'
     if args.cvc5:cv=cvc5_run(grounded);total['concrete_cvc5']+=1
     if zz!='sat' or (args.cvc5 and cv!='sat'):raise RuntimeError('UNVERIFIED_CONCRETE_TRACE')
     res['ground_original_sha256']=hashlib.sha256(grounded.encode()).hexdigest()
     res['grounded_z3']=zz;res['grounded_cvc5']=cv;res['values']=val
     found=True;row['status']='ORIGINAL_CONCRETE_UNSAFE_DUAL_SAT' if args.cvc5 else 'ORIGINAL_CONCRETE_UNSAFE_Z3_SAT';row['witness_depth']=0 if key=='depth0' else 1
     total['genuine_unsafes']+=1
     break
    if zs=='unknown':errors.append('UNKNOWN_'+key)
   if not found:
    row['status']='ABSTAIN_INCONCLUSIVE_BMC' if errors else 'NO_WITNESS_UP_TO_DEPTH1'
    total['abstain']+=bool(errors);total['no_short_witness']+=not bool(errors)
  except Exception as e:row.update(status='ABSTAIN_OR_ERROR',error=type(e).__name__+': '+str(e)[:200]);total['abstain']+=1
  cases.append(row);print('SOURCE_BMC',name,row['status'],flush=True)
 o={'schema':'neumann.q3.source_original_bmc_depth0_1.v1','firstblind':False,'only_real_original':True,'never_assume_safe_from_bmc_unknown':True,'cases':cases,'totals':total,'source_registry_sha256':hashlib.sha256(args.registry.read_bytes()).hexdigest(),'total_wall_s':round(time.monotonic()-start,5)}
 args.out.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print('SOURCE_BMC_SUMMARY',total,'wall',o['total_wall_s'],flush=True)
if __name__=='__main__':main()