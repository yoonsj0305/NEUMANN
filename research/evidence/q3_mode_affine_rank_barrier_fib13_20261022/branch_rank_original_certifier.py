#!/usr/bin/env python3
"""Source-native rational rank certificate for unconditional vs guarded affine conservation.

Scope of impossibility: constant-coefficient equalities w*x=k that hold on the
ENTIRE original initial-state set and are preserved by EVERY original mode.
Only claims a barrier for that fixed representation family, not arbitrary
linear inequalities, nonlinear/logical formulas, or neural discovery.

No target invariant is supplied. Conditional equalities are generated from the
original source Pre/Trans. Verify their conjunction against the full original
initialization, induction and safety formulas in *two independent SMT solvers*.
"""
import argparse,hashlib,importlib.util,json,pathlib,subprocess,time
import sympy as S

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,str(path))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',type=pathlib.Path,required=True)
    ap.add_argument('--expected-gitblob',required=True)
    ap.add_argument('--affine-engine',type=pathlib.Path,required=True)
    ap.add_argument('--classical-engine',type=pathlib.Path,required=True)
    ap.add_argument('--out',type=pathlib.Path,required=True)
    ap.add_argument('--smt-out',type=pathlib.Path,required=True)
    ap.add_argument('--cvc5',action='store_true')
    args=ap.parse_args()
    start=time.monotonic()
    raw=args.source.read_bytes()
    blob=hashlib.sha1(('blob '+str(len(raw))+'\0').encode()+raw).hexdigest()
    if blob!=args.expected_gitblob:raise RuntimeError('EXACT_GIT_BLOB_SHA_MISMATCH')
    A=load(args.affine_engine,'source_affine_exact');E=load(args.classical_engine,'source_z3_original')
    names,defs,fns=E.parse(raw.decode())
    M,b=A.matrix_of_pre(A.parse_sexpr(defs[0])[-1],names)
    branch=A.dnf(A.parse_sexpr(defs[1])[-1])
    C=A.update_delta_rows(branch,names)
    product=C*M.T
    if M.cols!=len(names) or product.cols!=M.rows:raise RuntimeError('DIM_MISMATCH')
    rank=int(product.rank());nullity=len(product.nullspace())
    guards=[];candidates=[]
    for guard,branches in A.guarded_modes(branch,names):
        cg=A.update_delta_rows(branches,names)
        brank=int((cg*M.T).rank());bnullity=len((cg*M.T).nullspace())
        expr=A.affine_invariants(M,b,cg,names,guard=guard)
        if not expr:raise RuntimeError('MODE_WITHOUT_GENERATED_INVARIANT '+str(guard))
        candidates+=expr
        guards.append({'original_guard':str(guard),'mode_source_branch_count':len(branches),
                       'C_mode':str(cg),'rank_C_mode_Mt':brank,'nullity_C_mode_Mt':bnullity,
                       'source_only_generated_conditionals':expr})
    if len(branch)!=2 or len(guards)!=2 or nullity!=0 or any(v['nullity_C_mode_Mt']==0 for v in guards):
        raise RuntimeError('EXPECTED_GLOBAL_VS_MODE_RANK_BARRIER_NOT_PRESENT')
    expr='(and '+' '.join(candidates)+')'
    decls='\n'.join('(declare-const '+n+' Int)\n(declare-const '+n+'! Int)' for n in names)
    head='(set-logic LIA)\n'+decls+'\n'+'\n'.join(defs)+'\n'
    ivfun='(define-fun invariant ('+' '.join('('+x+' Int)' for x in names)+') Bool '+expr+')\n'
    inv='(invariant '+' '.join(names)+')';invp='(invariant '+' '.join(n+'!' for n in names)+')'
    pre='('+fns[0]+' '+' '.join(names)+')'
    trans='('+fns[1]+' '+' '.join(names+[n+'!' for n in names])+')'
    post='('+fns[2]+' '+' '.join(names)+')'
    vcs={'Init':'(and '+pre+' (not '+inv+'))',
         'Consecution':'(and '+inv+' '+trans+' (not '+invp+'))',
         'Safety':'(and '+inv+' (not '+post+'))'}
    args.smt_out.mkdir(parents=True,exist_ok=True)
    cert={}
    for name,goal in vcs.items():
        smt=head+ivfun+'(assert '+goal+')\n(check-sat)\n'
        (args.smt_out/(name+'.smt2')).write_text(smt)
        z=[x.strip() for x in E.z.run(smt) if x.strip() in ('sat','unsat','unknown')]
        cv=None
        if args.cvc5:
            p=subprocess.run(['cvc5','--lang','smt2','--tlimit=10000'],input=smt,text=True,capture_output=True,timeout=16)
            cv=[x.strip() for x in p.stdout.splitlines() if x.strip() in ('sat','unsat','unknown')]
        if z!=['unsat'] or (args.cvc5 and cv!=['unsat']):raise RuntimeError('FULL_ORIGINAL_3VC_FAIL_'+name+' '+str((z,cv)))
        cert[name]={'Z3':z[0],'cvc5':cv[0] if cv else 'NOT_RUN','script_sha256':hashlib.sha256(smt.encode()).hexdigest()}
    out={'schema':'neumann.q3.original_source_exact_affine_global_barrier_guarded_full_proof.v1',
         'source_original_gitblob':blob,'source_sha256':hashlib.sha256(raw).hexdigest(),
         'variable_order':names,'original_pre_equalities_M':str(M),'original_pre_values_b':str(b),
         'all_original_source_branch_deltas_C':str(C),'full_constraint_C_M_transpose':str(product),
         'M_row_rank':int(M.rank()),'global_constraint_rank':rank,'global_nullity':nullity,
         'guarded_modes':guards,'generated_conditional_invariant':expr,
         'original_full_dual_vcs':cert,'verified_backend_count':2 if args.cvc5 else 1,
         'scope':'unconditional affine equality w*x=k valid for every original initial state and preserved in every source transition mode',
         'scientific_boundary':'classical exact math, no neural weights, no global Q3/Q4 or universal affine impossibility',
         'elapsed_s':round(time.monotonic()-start,5)}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
    print('FIB13_RANK_BARRIER_AND_GUARDED_PROOF',blob,'GLOBAL_DIM',nullity,'MODES',[x['nullity_C_mode_Mt'] for x in guards],'VC',cert,'sha256',hashlib.sha256(args.out.read_bytes()).hexdigest(),flush=True)

if __name__=='__main__':main()