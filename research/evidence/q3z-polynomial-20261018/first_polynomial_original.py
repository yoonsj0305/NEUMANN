"""Q3Z: oracle-free source polynomial closure / exact quadratic conservation.

No gold invariants, no extracted SPACER lemmas, and no neural training.
Original native SMT-LIB source predicates independently check all proofs.
Frozen before code: docs/research/Q3Z_FIRST_POLYNOMIAL_CLOSURE_PREREG_20261018.md
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, math, sys, time
from pathlib import Path
import sympy as sp
import z3

HERE=Path(__file__).resolve().parent
for directory in ("q3y-post-relative-20261018",
                  "q3w-oraclefree-cegis-20261018",
                  "q3t-mixed-original-20261018",
                  "q3t2-native-original-20261018",
                  "q3u-exact-transition-nullspace-20261018"):
    sys.path.insert(0,str(HERE.parent/directory))
import safety_region_cegis as q3y
import affine_hull_original_cegis as core
from first_real_affine_nullspace import exact_update_matrix

PREREG="267d8dd0d98e2d52193730ad65d4528269f27d2e"
ORIGINAL_REV="6ac90265b11431c9477dfbd33e3e3380234c0499"
NIA="benchmarks/NIA"
OPENED=[
 "benchmarks/NIA/2005.ICALP_PolyRank/poly3.pos_z.sl",
 "benchmarks/NIA/2005.ICALP_PolyRank/poly7.sl",
 "benchmarks/NIA/2018.CHI_InvGame/cube2.desugared.sl",
 "benchmarks/NIA/2018.CHI_InvGame/gauss_sum-more-rows.auto.sl",
 "benchmarks/NIA/2018.CHI_InvGame/non-lin-ineq-1.desugared.sl",
 "benchmarks/NIA/2018.CHI_InvGame/non-lin-ineq-2.desugared.sl",
]
MAX_STATE=5
MAX_GOAL_DEGREE=3
MAX_GOAL_STEPS=12
MAX_MONOMIALS=24
MAX_COEFF=10**9
SMT_MS=8000
GOAL_SUCCESS="ORIGINAL_THREE_VC_UNSAT"

class Abstain(Exception):pass

def checked(*queries, timeout=SMT_MS):
    s=z3.Solver();s.set(timeout=timeout)
    for q in queries:s.add(q)
    t=time.perf_counter_ns()
    try: r=str(s.check())
    except Exception:r="error"
    return r,round((time.perf_counter_ns()-t)/1e6,3)

def symbolic_source(now,A,b):
    symbols=sp.symbols(" ".join("S"+str(i) for i in range(len(now))))
    if not isinstance(symbols,tuple):symbols=(symbols,)
    tr={symbols[i]:sp.expand(sum(A[i,j]*symbols[j]
                              for j in range(len(now)))+b[i])
        for i in range(len(now))}
    return symbols,tr

def z3_to_sym(expr,now,symbols):
    expr=z3.simplify(expr)
    if z3.is_int_value(expr):return sp.Integer(expr.as_long())
    for i,v in enumerate(now):
        if z3.eq(expr,v):return symbols[i]
    if not z3.is_app(expr):raise Abstain("UNSUPPORTED_NON_POLYNOMIAL_Z3_NODE")
    k=expr.decl().kind()
    args=[z3_to_sym(x,now,symbols) for x in expr.children()]
    if k==z3.Z3_OP_ADD:return sp.expand(sum(args))
    if k==z3.Z3_OP_SUB:return sp.expand(args[0]-sum(args[1:]))
    if k==z3.Z3_OP_UMINUS:return -args[0]
    if k==z3.Z3_OP_MUL:return sp.expand(sp.prod(args))
    if k==z3.Z3_OP_POWER:
        if len(args)==2 and args[1].is_Integer and 0<=int(args[1])<=MAX_GOAL_DEGREE:
            return sp.expand(args[0]**int(args[1]))
    raise Abstain("NOT_POLYNOMIAL_Z3_OPERATOR_"+str(k))

def to_poly(expr,symbols,max_degree=MAX_GOAL_DEGREE):
    try: p=sp.Poly(sp.expand(expr),*symbols,domain=sp.QQ)
    except Exception as e:raise Abstain("POLYNOMIAL_PARSE_"+type(e).__name__)
    if p.total_degree()>max_degree:raise Abstain("POLYNOMIAL_DEGREE_CAP")
    if any(abs(int(v.p))>MAX_COEFF or int(v.q)>MAX_COEFF
           for v in p.coeffs()):
        raise Abstain("EXACT_POLYNOMIAL_COEFF_CAP")
    return p

def primitive_poly(expr,symbols):
    p=to_poly(expr,symbols)
    if p.is_zero:return sp.Integer(0)
    den=math.lcm(*[int(v.q) for v in p.coeffs()])
    ints=[int(v*den) for v in p.coeffs()]
    g=math.gcd(*[abs(v) for v in ints])
    out=sp.expand(p.as_expr()*sp.Rational(den,g))
    if int(sp.Poly(out,*symbols).LC())<0:out=-out
    return out

def polynomial_to_z3(expr,symbols,now):
    p=to_poly(expr,symbols)
    terms=[]
    for exps,coeff in p.terms():
        if coeff.q!=1:raise Abstain("NON_INTEGRAL_POLY_CERTIFICATE")
        product=z3.IntVal(int(coeff))
        for i,power in enumerate(exps):
            for _ in range(int(power)):
                product=product*now[i]
        terms.append(product)
    return z3.Sum(*terms) if terms else z3.IntVal(0)

def within_span(polys,test,symbols):
    allp=polys+[test]
    monoms=sorted({m for expr in allp for m in to_poly(expr,symbols).monoms()})
    if not monoms:return True
    mat=sp.Matrix([[to_poly(expr,symbols).coeff_monomial(m)
                    for expr in allp] for m in monoms])
    return mat.rank()==mat[:,:-1].rank()

def equality_leaves(expr):
    if z3.is_eq(expr):return [expr]
    if z3.is_and(expr) or z3.is_or(expr) or z3.is_implies(expr):
        out=[]
        for child in expr.children():out.extend(equality_leaves(child))
        return out
    return []

def goal_closures(post,now,symbols,tr):
    candidates=[]
    for item in equality_leaves(post)[:12]:
        a,b=item.children()
        try:
            start=primitive_poly(z3_to_sym(a,now,symbols)-
                                 z3_to_sym(b,now,symbols),symbols)
            if start==0:continue
            polys=[start]
            for step in range(MAX_GOAL_STEPS):
                nxt=sp.expand(polys[-1].xreplace(tr)-polys[-1])
                test=primitive_poly(nxt,symbols)
                if within_span(polys,test,symbols):break
                polys.append(test)
            else:raise Abstain("GOAL_CLOSURE_NOT_STABLE_WITHIN_CAP")
            candidates.append(polys)
        except (Abstain, ValueError, sp.PolynomialError):
            continue
    return candidates

def monomials_upto(syms,degree=2):
    n=len(syms)
    powers=[tuple(v) for v in itertools.product(range(degree+1),repeat=n)
            if sum(v)<=degree]
    powers.sort(key=lambda v:(sum(v),v))
    if len(powers)>MAX_MONOMIALS:
        raise Abstain("QUADRATIC_FEATURE_COUNT_CAP")
    return [sp.prod(syms[i]**power for i,power in enumerate(v)) for v in powers]

def conservation_basis(symbols,tr):
    feats=monomials_upto(symbols,2)
    deltas=[sp.expand(f.xreplace(tr)-f) for f in feats]
    mons=sorted({m for q in deltas for m in to_poly(q,symbols).monoms()})
    if not mons:return []
    mat=sp.Matrix([[to_poly(expr,symbols).coeff_monomial(m)
                   for expr in deltas] for m in mons])
    results=[]
    for raw in mat.nullspace():
        p=primitive_poly(sum(c*f for c,f in zip(raw,feats)),symbols)
        if p!=0 and to_poly(p,symbols).total_degree()>=1:
            results.append(p)
    return results

def classify(goal,now,nxt,pre,trans,post,symbols):
    uniq=[];stats={"attempts":len(goal),"pre_or_step_rejected":0}
    for expr in goal:
        try:
            znow=z3.And(*[polynomial_to_z3(p,symbols,now)==0 for p in expr])
            znxt=z3.substitute(znow,*list(zip(now,nxt)))
            first,_=checked(pre,z3.Not(znow))
            step,_=checked(znow,trans,z3.Not(znxt))
            if (first,step)!=("unsat","unsat"):
                stats["pre_or_step_rejected"]+=1
                continue
            uniq.append((znow,expr))
        except (Abstain,sp.PolynomialError):stats["pre_or_step_rejected"]+=1
    return uniq,stats

def conservation_checked(pre,trans,now,nxt,symbols,basis):
    kept=[];denied=0
    for index,poly in enumerate(basis):
        try:
            expr=polynomial_to_z3(poly,symbols,now)
            solver=z3.Solver();solver.set(timeout=SMT_MS);solver.add(pre)
            if str(solver.check())!="sat":denied+=1;continue
            val=solver.model().eval(expr,model_completion=True)
            if not z3.is_int_value(val):
                print("Q3Z_CONSERVATION_REJECT_NON_INTEGER_MODEL",index,flush=True)
                denied+=1;continue
            candidate=expr==int(val.as_long())
            base,_=checked(pre,z3.Not(candidate))
            next_candidate=z3.substitute(candidate,*list(zip(now,nxt)))
            step,_=checked(candidate,trans,z3.Not(next_candidate))
            if base==step=="unsat":kept.append((candidate,poly))
            else:
                print("Q3Z_CONSERVATION_VC_REFUTATION",index,base,step,flush=True)
                denied+=1
        except (Abstain,z3.Z3Exception) as exc:
            print("Q3Z_CONSERVATION_TYPE_REJECTION",index,type(exc).__name__,str(exc)[:80],flush=True)
            denied+=1
    return kept,denied

def full_three_vc(inv,pre,trans,post,now,nxt):
    primed=z3.substitute(inv,*list(zip(now,nxt)))
    terms=[z3.And(pre,z3.Not(inv)),
           z3.And(inv,trans,z3.Not(primed)),
           z3.And(inv,z3.Not(post))]
    outcomes=[]
    for query in terms:
        result,_=checked(query)
        outcomes.append(result)
    return outcomes

def explore(pre,trans,post,now,nxt,A,b):
    started=time.perf_counter_ns()
    syms,tr=symbolic_source(now,A,b)
    leaves=goal_closures(post,now,syms,tr)
    goal_candidates,goal_diag=classify(leaves,now,nxt,pre,trans,post,syms)
    basis=conservation_basis(syms,tr)
    conserved,conservation_rejects=conservation_checked(
        pre,trans,now,nxt,syms,basis)
    modes={}
    for kind, invparts in [
        ("GOAL", [r for r,_ in goal_candidates]),
        ("CONSERVATION",[r for r,_ in conserved]),
        ("COMBINED",[r for r,_ in goal_candidates]+[r for r,_ in conserved])
    ]:
        if not invparts:
            modes[kind]={"status":"ABSTAIN_NO_PROVEN_SOURCE_POLYNOMIAL"}
            continue
        target=z3.And(post,*invparts)
        vc=full_three_vc(target,pre,trans,post,now,nxt)
        modes[kind]={"status":GOAL_SUCCESS if vc==["unsat"]*3 else
                     "SOURCE_ORIGINAL_GOAL_NOT_PROVEN",
                     "original_vcs":vc}
    positive=any(q["status"]==GOAL_SUCCESS for q in modes.values())
    return {
        "goal_source_equalities":len(leaves),
        "exact_goal_derived_inductive_closures":len(goal_candidates),
        "goal_closure_diagnostics":goal_diag,
        "conservation_kernel_nontrivial_basis":len(basis),
        "individually_original_inductive_conserved_polynomials":len(conserved),
        "conservation_rejected":conservation_rejects,
        "candidate_mode_results":modes,
        "any_full_original_three_vc":positive,
        "algebra_and_proof_wall_ms":round((time.perf_counter_ns()-started)/1e6,3),
    }

def check_source_graph(trans,now,nxt,A,b):
    graph=z3.And(*[
        nxt[i]==z3.Sum(*[z3.IntVal(int(A[i,j]))*now[j]
                 for j in range(len(now))])+z3.IntVal(int(b[i]))
        for i in range(len(now))])
    r,_=checked(trans,z3.Not(graph))
    return r

def case(root,path,cohort):
    start=time.perf_counter_ns()
    raw=path.read_bytes()
    relative=path.relative_to(root).as_posix()
    rec={"original_path":relative,"source_git_blob":core.blobhash(raw),
         "cohort":cohort,"status":"NOT_RUN",
         "source_text_or_invariant_formula_exported":False}
    try:
        if len(raw)>500000:raise Abstain("MAX_SOURCE_BYTE_CAP")
        forms=core.sexprs(raw)
        source=core.extract_mixed_original(forms)
        if source["num_bool"]!=0 or not (2<=source["num_int"]<=MAX_STATE):
            raise Abstain("SOURCE_MIXED_SORT_OR_STATE_CAP")
        native=core.native_original_relations(forms,source)
        native.update({"now":source["now"],"next":source["next"]})
        parity={key:checked(z3.Xor(source[key],native[key]))[0]
                for key in ("pre","trans","post")}
        rec["independent_original_source_native_xor"]=parity
        if any(v!="unsat" for v in parity.values()):
            raise Abstain("ORIGINAL_SOURCE_PARSER_PARITY_UNKNOWN")
        ps,_=checked(native["pre"])
        ns,_=checked(z3.Not(native["post"]))
        rec["original_pre_sat"]=ps;rec["original_not_post_sat"]=ns
        if ps!="sat" or ns!="sat":raise Abstain("ORIGINAL_PRE_POST_NONVACUITY_FAILED")
        post_vcs=full_three_vc(native["post"],native["pre"],native["trans"],
                               native["post"],native["now"],native["next"])
        rec["original_post_only_three_vcs"]=post_vcs
        specialist=core.independent_native_bad_query(
            native,native["now"],native["next"])
        rec["direct_source_classical_spacer_status"]=specialist["status"]
        rec["direct_source_classical_spacer_ms"]=specialist["native_solver_wall_ms"]
        A,b=exact_update_matrix(source)
        if check_source_graph(native["trans"],native["now"],native["next"],A,b)!="unsat":
            raise Abstain("SOURCE_TRANSITION_NOT_CERTIFIED_EXACT_AFFINE_GRAPH")
        rec["original_transition_affine_graph_implied_by_source"]=True
        result=explore(native["pre"],native["trans"],native["post"],
                native["now"],native["next"],A,b)
        rec.update(result)
        rec["new_original_proof_beyond_source_post"]=(
            result["any_full_original_three_vc"]
            and post_vcs!=["unsat"]*3
            and result["exact_goal_derived_inductive_closures"]+
                result["individually_original_inductive_conserved_polynomials"]>0)
        rec["status"]="ORIGINAL_SOURCE_ALGEBRA_AND_FULL_VC_COMPLETE"
        if result["any_full_original_three_vc"]:
            assert any(x.get("original_vcs")==["unsat"]*3 for x in
                       result["candidate_mode_results"].values())
    except Exception as error:
        rec["status"]="ABSTAIN_NO_CERTIFIED_ORIGINAL_THEOREM"
        rec["new_original_proof_beyond_source_post"]=False
        rec["reason_type"]=type(error).__name__
        rec["reason_category"]=str(error).split(":")[0][:130]
    finally:
        rec["total_case_wall_ms"]=round((time.perf_counter_ns()-start)/1e6,3)
    return rec

def frozen_fresh(root):
    opened_groups={"2005.ICALP_PolyRank","2018.CHI_InvGame"}
    base=root/NIA
    choices=[]
    for sub in sorted(x for x in base.iterdir() if x.is_dir()):
        if sub.name in opened_groups:continue
        files=sorted((p for p in sub.rglob("*.sl")
                      if not any(s.startswith("~") for s in p.relative_to(sub).parts)),
                     key=lambda p:p.relative_to(root).as_posix())
        if len(files)>=2:choices.append((sub.relative_to(root).as_posix(),files[:4]))
    if len(choices)<2:raise RuntimeError("NO_TWO_FROZEN_NEW_NIA_ORIGINS")
    groups=[g for g,_ in choices[:2]]
    files=[f for _,fs in choices[:2] for f in fs]
    return groups,files

def synthetic():
    n,x,y,z=z3.Ints("q3z_n q3z_x q3z_y q3z_z")
    np,xp,yp,zp=z3.Ints("q3z_np q3z_xp q3z_yp q3z_zp")
    p=z3.And(n==0,x==0,y==1,z==6)
    tr=z3.And(np==n+1,xp==x+y,yp==y+z,zp==z+6)
    goal=x==n*n*n
    A=sp.Matrix([[1,0,0,0],[0,1,1,0],[0,0,1,1],[0,0,0,1]])
    b=sp.Matrix([1,0,0,6])
    proof=explore(p,tr,goal,[n,x,y,z],[np,xp,yp,zp],A,b)
    assert proof["exact_goal_derived_inductive_closures"]>=1
    assert proof["candidate_mode_results"]["GOAL"]["status"]==GOAL_SUCCESS
    bad=z3.And(np==n+1,xp==x+y,yp==y+z,zp==z+7)
    # Source-derived old polynomial formula must fail on deliberately mutated source.
    syms,mapping=symbolic_source([n,x,y,z],A,b)
    polys=goal_closures(goal,[n,x,y,z],syms,mapping)
    assert len(polys)>=1
    stale=z3.And(*[polynomial_to_z3(t,syms,[n,x,y,z])==0 for t in polys[0]])
    assert full_three_vc(z3.And(stale,goal),p,bad,goal,
                         [n,x,y,z],[np,xp,yp,zp])!=["unsat"]*3

    fixed=z3.Int("q3z_fixed_n");total=z3.Int("q3z_total");idx=z3.Int("q3z_i")
    fixedp=z3.Int("q3z_fixed_np");totalp=z3.Int("q3z_totalp");idxp=z3.Int("q3z_ip")
    pre2=z3.And(fixed==5,idx==1,total==0)
    trans2=z3.And(idx<=fixed,fixedp==fixed,idxp==idx+1,totalp==total+idx)
    goal2=z3.Or(idx<=fixed,2*total==fixed*(fixed+1))
    a2=sp.Matrix([[1,0,0],[0,1,1],[0,0,1]])
    b2=sp.Matrix([0,0,1])
    gauss=explore(pre2,trans2,goal2,
            [fixed,total,idx],[fixedp,totalp,idxp],a2,b2)
    print('Q3Z_SYNTH_GAUSS_FIRST_FAILURE_DIAGNOSTIC',json.dumps(gauss,sort_keys=True),flush=True)
    assert gauss["individually_original_inductive_conserved_polynomials"]>=1
    assert gauss["candidate_mode_results"]["CONSERVATION"]["status"]==GOAL_SUCCESS
    assert full_three_vc(goal2,pre2,trans2,goal2,
          [fixed,total,idx],[fixedp,totalp,idxp])!=["unsat"]*3

    s,sp_next=z3.Ints("q3z_unsafe q3z_unsafe_next")
    unsafe=full_three_vc(s>=0,s==0,sp_next==s-1,s>=0,[s],[sp_next])
    assert unsafe!=["unsat"]*3
    return {"strict_controls_pass":True,
            "source_cubic_polynomial_goal_closure_proven":True,
            "source_quadratic_conservation_proven":True,
            "post_alone_gauss_failed":True,
            "mutated_cubic_old_certificate_rejected":True,
            "genuinely_unsafe_rejected":True}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    start=time.perf_counter_ns()
    if core.blobhash((args.root/"LICENSE.md").read_bytes())!=core.LICENSE_BLOB:
        raise RuntimeError("PINNED_UPSTREAM_LICENSE_CHANGED")
    fresh_groups,fresh_paths=frozen_fresh(args.root)
    controls=synthetic()
    development=[case(args.root,args.root/path,"OPENED_NIA_DEVELOPMENT") for path in OPENED]
    prospective=[case(args.root,p,"FIRST_OTHER_NIA_ORIGIN") for p in fresh_paths]
    seen=[r["source_git_blob"] for r in development+prospective]
    if len(set(seen))!=len(seen):raise RuntimeError("DUPLICATE_SOURCE_GIT_BLOBS")
    group_receipts={}
    for group in fresh_groups:
        members=[r for r in prospective if r["original_path"].startswith(group+"/")]
        group_receipts[group]={
            "originals":len(members),
            "new_proof_beyond_post":sum(x["new_original_proof_beyond_source_post"] for x in members),
            "unsupported_or_unknown":sum(x["status"]!="ORIGINAL_SOURCE_ALGEBRA_AND_FULL_VC_COMPLETE" for x in members),
            "reason_categories":[x.get("reason_category") for x in members]
        }
    dev_wins=sum(r["new_original_proof_beyond_source_post"] for r in development)
    first_gate=dev_wins>=1 and controls["strict_controls_pass"]
    fresh_gate=all(group_receipts[g]["new_proof_beyond_post"]>=1 for g in fresh_groups)
    report={
       "study":"Q3Z_SOURCE_DERIVED_POLYNOMIAL_CLOSURE_ORIGINAL_NIA",
       "status":"FIRST_FROZEN_NIA_POLYNOMIAL_STUDY_EXECUTED",
       "pre_registration_commit":PREREG,
       "original_upstream":ORIGINAL_REV,
       "synthetic_controls":controls,
       "development_original_count":len(development),
       "first_other_origin_count":len(prospective),
       "first_other_origin_groups":fresh_groups,
       "development_original_receipts":development,
       "prospective_original_receipts":prospective,
       "development_original_nonpost_proofs":dev_wins,
       "first_other_origin_results":group_receipts,
       "bounded_polynomial_mechanism_gate":first_gate,
       "prospective_two_origin_gate":fresh_gate,
       "trained_neural_forwards":0,
       "original_gold_invariant_or_classical_cover_supplied":False,
       "q3f_sealed_chc_targets_opened":False,
       "global_Q1_Q7":"OPEN",
       "study_wall_ms":round((time.perf_counter_ns()-start)/1e6,3)
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+"\n")
    print("Q3Z_FIRST_FROZEN_STUDY",json.dumps({
      "development_new_nonpost":dev_wins,"development_gate":first_gate,
      "fresh_groups":fresh_groups,"fresh_new_nonpost":group_receipts,
      "cross_origin_gate":fresh_gate,"global":report["global_Q1_Q7"]
    },sort_keys=True))
if __name__=="__main__":main()
