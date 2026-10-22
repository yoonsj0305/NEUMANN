#!/usr/bin/env python3
"""Posthoc autonomous (non-neural) source-affine and guard-split invariant synthesizer.

Original source Pre/Trans/Post only, no source basename/expected formula/magic target rules.
Derive linear conservation by exact rational row-space intersection:
   Pre implies Mx=b; source transition imposes Cw=0.
   Find alpha in ker(C M.T), emit w=M.T alpha, k=b.T alpha.
Where an explicitly source-guarded mode changes the affine transition,
repeat per observed branch guard and only accept source-original 3VC.
This is a source-general classical baseline, NOT evidence for learned uniqueness.
"""
import argparse, collections, hashlib, importlib.util, itertools, json, math, pathlib, re, time
import sympy as S

ROOT='/mnt/data/NEUMANN_Q3_CLASSICAL_AUTO_HOUDINI_20261022.py'

def import_engine(path):
    spec=importlib.util.spec_from_file_location('neumann_classic',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def parse_sexpr(src):
    tokens=re.findall(r'\(|\)|[^\s()]+',src)
    def read(pos):
        if tokens[pos]!='(': return tokens[pos],pos+1
        values=[];pos+=1
        while pos<len(tokens) and tokens[pos]!=')':
            val,pos=read(pos);values.append(val)
        if pos>=len(tokens):raise ValueError('unbalanced')
        return values,pos+1
    expr,end=read(0)
    if end!=len(tokens):raise ValueError('extraneous tokens')
    return expr

def conjunction(e):
    if isinstance(e,list) and e and e[0]=='and':
        return list(itertools.chain.from_iterable(conjunction(s) for s in e[1:]))
    return [e]

def dnf(e,limit=32):
    if isinstance(e,list) and e:
        if e[0]=='or':
            total=list(itertools.chain.from_iterable(dnf(v,limit) for v in e[1:]))
            if len(total)>limit: raise ValueError('DNF_LIMIT')
            return total
        if e[0]=='and':
            p=[[]]
            for v in e[1:]:
                child=dnf(v,limit)
                p=[a+b for a in p for b in child]
                if len(p)>limit:raise ValueError('DNF_LIMIT')
            return p
    return [[e]]

def as_linear(node,symbols):
    if isinstance(node,str):
        if node.lstrip('-').isdigit():return S.Integer(node)
        if node in symbols:return symbols[node]
        raise ValueError('nonlinear or unknown symbol '+node)
    if not isinstance(node,list) or not node:raise ValueError('invalid AST')
    op,*v=node
    if op=='+':return S.expand(sum(as_linear(i,symbols) for i in v))
    if op=='-':
        if len(v)==1:return -as_linear(v[0],symbols)
        return S.expand(as_linear(v[0],symbols)-sum(as_linear(i,symbols) for i in v[1:]))
    if op=='*':
        out=S.Integer(1)
        for n in v:out*=as_linear(n,symbols)
        out=S.expand(out)
        if S.Poly(out,*symbols.values()).total_degree()>1:raise ValueError('NON_AFFINE')
        return out
    raise ValueError('not affine: '+str(op))

def matrix_of_pre(pre,vars_):
    syms={v:S.Symbol(v) for v in vars_};rows=[];bs=[]
    for a in conjunction(pre):
        if isinstance(a,list) and len(a)==3 and a[0]=='=':
            try:
                v=S.expand(as_linear(a[1],syms)-as_linear(a[2],syms))
                p=S.Poly(v,*syms.values());co=[p.coeff_monomial(syms[x]) for x in vars_]
                const=p.coeff_monomial(1)
                if any(co):rows.append(co);bs.append(-const)
            except (ValueError,S.PolynomialError):pass
    return S.Matrix(rows) if rows else S.zeros(0,len(vars_)),S.Matrix(bs) if bs else S.zeros(0,1)

def update_delta_rows(branches,vars_):
    # Preserve original branch semantics by allowing updates to depend on any current state,
    # and requiring an unconstrained primed coordinate to have coefficient zero.
    syms={v:S.Symbol(v) for v in vars_}
    for v in vars_:syms[v+'!']=S.Symbol('_next_'+v)
    symbols=list(syms.values());n=len(vars_)
    result=[]
    for branch in branches:
        equations={}
        for atom in branch:
            if isinstance(atom,list) and len(atom)==3 and atom[0]=='=':
                for u,v in [(atom[1],atom[2]),(atom[2],atom[1])]:
                    if isinstance(u,str) and u.endswith('!') and u[:-1] in vars_:
                        try:
                            e=as_linear(v,syms)
                            if not e.has(*[syms[x+'!'] for x in vars_]):equations[u[:-1]]=e
                        except ValueError:pass
        changes=[]
        for var in vars_:
            e=equations.get(var,syms[var+'!'])
            changes.append(S.expand(e-syms[var]))
        poly=[S.Poly(d,*symbols) for d in changes]
        coefficients=set().union(*(set(p.monoms()) for p in poly))
        for monomial in sorted(coefficients):
            row=[p.coeff_monomial(monomial) for p in poly]
            if any(row):result.append(row)
    return S.Matrix(result) if result else S.zeros(0,n)

def branch_guard(a):
    if isinstance(a,list):
        if len(a)==3 and a[0]=='=' and isinstance(a[1],str) and isinstance(a[2],str) and a[2].lstrip('-').isdigit():return ('eq',a[1],int(a[2]))
        if len(a)==2 and a[0]=='not':
            x=branch_guard(a[1]);return ('neq',x[1],x[2]) if x and x[0]=='eq' else None
    return None

def guarded_modes(branches,vars_):
    marks=collections.Counter()
    for b in branches:
        for a in b:
            g=branch_guard(a)
            if g and g[1] in vars_ and -3<=g[2]<=3:marks[g]+=1
    pairs=set((v,n) for op,v,n in marks if ('eq',v,n) in marks and ('neq',v,n) in marks)
    for v,n in sorted(pairs):
        for op in ('eq','neq'):
            key=(op,v,n)
            matched=[b for b in branches if any(branch_guard(a)==key for a in b)]
            if matched:yield key,matched

def smt_int(n):
    assert int(n)==n
    return str(int(n)) if n>=0 else '(- '+str(-int(n))+')'

def var_expr(coeff,vars_):
    pieces=[]
    for c,v in zip(coeff,vars_):
        if c==0:continue
        elif c==1:pieces.append(v)
        elif c==-1:pieces.append('(- '+v+')')
        else:pieces.append('(* '+smt_int(c)+' '+v+')')
    if len(pieces)==1:return pieces[0]
    return '(+ '+' '.join(pieces)+')'

def affine_invariants(M,b,C,vars_,guard=None,extra_basis=True):
    if M.rows==0:return []
    # all w=M.T*alpha are consequences of the actual Pre equalities
    eq=C*M.T;basis=eq.nullspace() if eq.rows else list(S.eye(M.rows).columnspace())
    combos=basis[:]
    # Exact rational span combination can unhide short support expressions.
    if extra_basis and len(basis)<=5:
        for i,j in itertools.combinations(range(len(basis)),2):
            combos.extend([basis[i]+basis[j],basis[i]-basis[j]])
    out=[]
    for a in combos:
        w=M.T*a;k=(b.T*a)[0]
        lcm=S.ilcm(*[int(S.denom(x)) for x in list(w)+[k]])
        full=[int(x*lcm) for x in list(w)+[k]]
        gcd=math.gcd(*full)
        if gcd==0:continue
        full=[u//gcd for u in full]
        if next((x for x in full if x),0)<0:full=[-u for u in full]
        w=full[:-1];k=full[-1]
        if not any(w) or max(abs(x) for x in full)>100000:continue
        candidate='(= '+var_expr(w,vars_)+' '+smt_int(k)+')'
        if guard:
            op,v,n=guard
            cond='(= '+v+' '+smt_int(n)+')'
            if op=='neq':cond='(not '+cond+')'
            candidate='(=> '+cond+' '+candidate+')'
        out.append(candidate)
    return sorted(set(out))

def unary_bounds(tree,vars_):
    # Conservative overapproximate grammar from source constants: all candidates tested against actual Pre/Trans.
    nums={0,1,2,3}
    def walk(t):
        if isinstance(t,str) and t.lstrip('-').isdigit():
            n=int(t)
            if abs(n)<=200:nums.add(n)
        if isinstance(t,list):
            for a in t:walk(a)
    walk(tree)
    nums|={-x for x in list(nums) if abs(x)<=3}
    out=[]
    for v in vars_:
        for val in sorted(nums):
            out.extend([f'(<= {v} {smt_int(val)})',f'(>= {v} {smt_int(val)})'])
    # Source-agnostic three-variable octagon extension: low-coefficient
    # relational facets not reducible to a conjunction of unary constraints.
    # These are candidates only, NEVER accepted without whole ORIGINAL 3VC.
    for support in (2,3):
        for group in itertools.combinations(vars_,support):
            for signs in itertools.product((-1,1),repeat=support-1):
                coeffs=(1,)+signs
                term=var_expr(coeffs,group)
                for bound in (-2,-1,0,1,2):
                    for op in ('<=','>='):
                        out.append(f'({op} {term} {smt_int(bound)})')
    return sorted(set(out))

def discover(raw,engine):
    names,defs,fns=engine.parse(raw)
    trees=[parse_sexpr(d) for d in defs]
    pre=trees[0][-1];trans=trees[1][-1]
    M,b=matrix_of_pre(pre,names)
    if M.rows==0:return [],{'error':'NO_PRE_AFFINE_EQUALITIES'}
    branches=dnf(trans)
    pool=affine_invariants(M,b,update_delta_rows(branches,names),names)
    modes=[]
    for guard,branchset in guarded_modes(branches,names):
        cands=affine_invariants(M,b,update_delta_rows(branchset,names),names,guard=guard)
        pool+=cands
        modes.append({'guard':guard,'branches':len(branchset),'num_candidates':len(cands)})
    return sorted(set(pool)),{'pre_equalities':M.rows,'branches':len(branches),'modes':modes,'affine_candidates':len(set(pool))}

def synthesize_one(raw,engine,include_inequalities=True):
    names,defs,fns=engine.parse(raw)
    decls='\n'.join(f'(declare-const {v} Int)\n(declare-const {v}! Int)' for v in names)
    source='(set-logic LIA)\n'+decls+'\n'+'\n'.join(defs)+'\n'
    pre='('+fns[0]+' '+' '.join(names)+')';trans='('+fns[1]+' '+' '.join(names+[v+'!' for v in names])+')';post='('+fns[2]+' '+' '.join(names)+')'
    postp='('+fns[2]+' '+' '.join([v+'!' for v in names])+')'
    metrics={'calls':0}
    post_attempt=engine.check_batch(source,[f'(and {pre} (not {post}))',f'(and {post} {trans} (not {postp}))']);metrics['calls']+=2
    if post_attempt==['unsat','unsat']:
        keep=[post];metrics['post_only']=True
    else:
        structural,meta=discover(raw,engine);metrics.update(meta);metrics['structural_candidates']=structural
        candidates=list(dict.fromkeys(structural+(unary_bounds(parse_sexpr(defs[0]),names)+unary_bounds(parse_sexpr(defs[1]),names) if include_inequalities else [])+[post]))
        statuses=engine.check_batch(source,[f'(and {pre} (not {c}))' for c in candidates]);metrics['calls']+=len(statuses)
        keep=[c for c,s in zip(candidates,statuses) if s=='unsat'];metrics['initial_pool']=len(candidates);metrics['after_init']=len(keep)
        for loop in range(16):
            if not keep:break
            premise=engine.conj(keep)
            attempts=[f'(and {premise} {trans} (not {engine.ren(c,names)}))' for c in keep]
            statuses=engine.check_batch(source,attempts);metrics['calls']+=len(statuses)
            nxt=[c for c,s in zip(keep,statuses) if s=='unsat']
            if len(nxt)==len(keep):break
            keep=nxt
        metrics['rounds']=loop+1
    inv=engine.conj(keep)
    checks=[f'(and {pre} (not {inv}))',f'(and {inv} {trans} (not {engine.ren(inv,names)}))',f'(and {inv} (not {post}))']
    vc=engine.check_batch(source,checks);metrics['calls']+=3
    metrics.update({'original_3vc':vc,'safe':vc==['unsat']*3,'num_kept':len(keep),'invariant':inv if vc==['unsat']*3 else None})
    return metrics

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--engine',default=ROOT);ap.add_argument('--source-dir',type=pathlib.Path,required=True);ap.add_argument('--manifest',type=pathlib.Path);ap.add_argument('--out',type=pathlib.Path,required=True);ap.add_argument('--exclude-inequalities',action='store_true');args=ap.parse_args()
    e=import_engine(args.engine);start=time.monotonic();cases=[]
    manifest=json.loads(args.manifest.read_text())['cases'] if args.manifest else [{'name':p.name,'sha':None} for p in sorted(args.source_dir.glob('*.sl'))]
    for m in manifest:
        st=time.monotonic();p=args.source_dir/m['name'];x={'file':p.name}
        try:
            b=p.read_bytes();sha=hashlib.sha1(('blob '+str(len(b))+'\0').encode()+b).hexdigest()
            if m.get('sha') and sha!=m['sha']:raise ValueError('SOURCE_SHA_MISMATCH')
            x.update(synthesize_one(b.decode(),e,not args.exclude_inequalities))
            x['git_blob']=sha
        except Exception as er:x.update({'safe':False,'error':type(er).__name__+': '+str(er)})
        x['wall_s']=round(time.monotonic()-st,4);cases.append(x)
        print(p.name,x['safe'],x.get('calls'),x.get('num_kept'),x.get('error'),flush=True)
    output={'schema':'neumann.q3.posthoc_source_affine_guard_structural_synth.v1','model_training':0,'human_target_formula_supplied':False,'first_blind':False,'cases':cases,'success_count':sum(x['safe'] for x in cases),'total_wall_s':round(time.monotonic()-start,4)}
    args.out.write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print('VERDICT',output['success_count'],'/',len(cases),'wall',output['total_wall_s'])
if __name__=='__main__':main()
