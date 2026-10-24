"""Q3 G0 new expandable executable DAG-grammar SOURCE-ONLY search.

The previous NEUMANN learned router selected one of a handful HUMAN FIXED
complete expression shapes. Here program nodes are synthesized by repeated
primitive graph edits (MUL, ADD, APPLY_UNARY, MULTIPLY_MACROS).
A named executable lambda is only accepted after exact rational coefficient
reconstruction and all 48 source-only numeric probes, then independently
graded as a WHOLE symbolic author original in a separate job.

THIS IS A STRONG, HONEST CLASSICAL EXECUTOR / GRAMMAR-HEADROOM EXPERIMENT.
No neural weights are trained here. A new neural controller may later learn
which AST edits/operands to prioritize, but that is NOT this experiment.
Nguyen first-8 has already been opened, used as development controls ONLY.
FIRST native authored external heldout = Livermore13/15/16/18..22.
"""
import argparse,collections,hashlib,json,pathlib,time,warnings
import numpy as np
import sympy as sp
from erbench_original_eleventh import sha,save
from learned_derived_power_eleventh32 import eval_action

X=sp.Symbol("x")

def numeric_valid(row):
    try:
        x=np.asarray(row["x"],float);y=np.asarray(row["y"],float)
        return x.shape==y.shape==(48,) and np.all(np.isfinite(x)) and np.all(np.isfinite(y))
    except Exception:return False

def numerical_relative(y,guess):
    with np.errstate(all="ignore"):
        err=np.abs(np.asarray(guess)-y)/(1+np.abs(y))
    return float(np.max(err)) if np.all(np.isfinite(err)) else float("inf")

def exact_source_fit(x,y,values,names,counts):
    """Fit on 32, check all48, exact-rationalize coefficients before ACCEPT."""
    counts["fitting_calls"]+=1
    try:
        A=np.column_stack(values+[np.ones(48)])
        params=np.linalg.lstsq(A[:32],y[:32],rcond=1e-11)[0]
        if not np.all(np.isfinite(params)) or max(abs(params))>1e12:return None
        coefficients=[sp.Rational(float(p)).limit_denominator(1000) for p in params]
        expr=sp.Add(*(coefficients[i]*names[i] for i in range(len(names))),coefficients[-1])
        fn=sp.lambdify(X,expr,modules="numpy")
        with np.errstate(all="ignore"):
            predicted=np.broadcast_to(np.asarray(fn(x),float),y.shape)
        e=numerical_relative(y,predicted)
        if e>=1e-8:return None
        return {"named_lambda":"lambda x: "+str(expr),
                "defined_operator_AST":str(expr),
                "source_error_after_exact_rationalization":e,
                "induced_semantic_graph_bases":[str(a) for a in names],
                "graph_contains_nested_unary":any(z.has(sp.sin,sp.cos,sp.log,sp.sqrt) for z in names),
                "graph_contains_product_of_derived_unaries":any(z.is_Mul and
                    sum(any(t.has(fn) for fn in (sp.sin,sp.cos,sp.log,sp.sqrt)) for t in z.args)>=2 for z in names),
                "source_fit_calls_so_far":counts["fitting_calls"]}
    except Exception:return None

def search(row,mode="RECURSIVE_GRAPH"):
    if not numeric_valid(row):
        return {"status":"UNKNOWN_SOURCE","source_verified_program":None,"primitive_nodes":0,
                "candidate_graphs_constructed":0,"fitting_calls":0}
    x=np.asarray(row["x"],float);y=np.asarray(row["y"],float)
    counts=collections.Counter();atoms=[];known=set()

    def add_atom(formula,action):
        sig=sp.srepr(formula)
        if sig in known:return
        try:
            fn=sp.lambdify(X,formula,modules="numpy")
            with np.errstate(all="ignore"):
                val=np.broadcast_to(np.asarray(fn(x),float),x.shape)
            if (not np.all(np.isfinite(val)) or np.max(abs(val))>=1e10 or
                np.std(val)<1e-10):return
        except Exception:return
        known.add(sig);counts["new_graph_atoms"]+=1
        counts["edit_"+action]+=1
        atoms.append((formula,val))

    power=X
    # Begin from the single input variable. Iterative graph multiplication
    # creates any requested polynomial degree, not a complete named target.
    for degree in range(1,9):
        add_atom(power,"MUL_RECURSIVE_POWER")
        power=sp.Mul(power,X)

    for degree in range(1,9):
        first=atoms[:degree]
        if len(first)!=degree:break
        p=exact_source_fit(x,y,[v for _,v in first],[q for q,_ in first],counts)
        if p:
            p["source_edit_trace"]="MUL_POWER_RECURSIVE_AND_REUSE_TERMS"
            return {"status":"SOURCE_VERIFIED","source_verified_program":p,
              "primitive_nodes":len(atoms),"candidate_graphs_constructed":counts["new_graph_atoms"],
              "fitting_calls":counts["fitting_calls"],"graph_edits":dict(counts)}

    if mode=="POLYNOMIAL_ONLY":
        return {"status":"UNKNOWN","source_verified_program":None,
                "primitive_nodes":len(atoms),"candidate_graphs_constructed":counts["new_graph_atoms"],
                "fitting_calls":counts["fitting_calls"],"graph_edits":dict(counts)}

    # Dynamic syntax edit grammar: ADD 1/-1 and pairwise monomials,
    # APPLY unary operators, then MUTLIPLY two already-built unaries.
    # No complete original Nguyen/Livermore function is hard-coded.
    power_nodes=[X**degree for degree in range(1,7)]
    candidates=list(power_nodes)
    for p in power_nodes:
        for shift in (-1,1):candidates.append(sp.Add(p,sp.Integer(shift)))
    for i in range(3):
        for j in range(i+1,4):candidates.append(sp.Add(power_nodes[i],power_nodes[j]))
    cutoff=len(atoms)
    for p in candidates:
        for op in (sp.sin,sp.cos,sp.log,sp.sqrt):
            add_atom(op(p),"APPLY_UNARY")
    unaries=atoms[cutoff:].copy()
    for i in range(len(unaries)):
        for j in range(i+1,len(unaries)):
            # Typed guard only, not a specific ready-made sin(x²)*cos(x) AST.
            if {unaries[i][0].func,unaries[j][0].func}=={sp.sin,sp.cos}:
                add_atom(sp.Mul(unaries[i][0],unaries[j][0]),"MUL_TWO_UNARY_MACROS")

    # Each learned/constructed graph atom is directly evaluated for
    # source-only ability to create a new executable named macro.
    for expr,z in atoms:
        candidate=exact_source_fit(x,y,[z],[expr],counts)
        if candidate:
            candidate["source_edit_trace"]="DEFINE_ONE_NEW_TYPED_ATOM"
            return {"status":"SOURCE_VERIFIED","source_verified_program":candidate,
              "primitive_nodes":len(atoms),"candidate_graphs_constructed":counts["new_graph_atoms"],
              "fitting_calls":counts["fitting_calls"],"graph_edits":dict(counts)}
    # Joint exact algebra of the two best source-geometry features.
    Z=np.column_stack([value for _,value in atoms])
    center=Z[:32]-Z[:32].mean(axis=0)
    norms=np.maximum(np.linalg.norm(center,axis=0),1e-12)
    V=center/norms
    yy=y[:32]-np.mean(y[:32])
    g=V.T@V;c=V.T@yy
    with np.errstate(all="ignore"):
        denominator=1-g*g
        score=np.divide(c[:,None]**2+c[None,:]**2-2*g*c[:,None]*c[None,:],
                        denominator,out=np.full_like(g,-np.inf),where=denominator>1e-11)
    score[np.tril_indices_from(score)]=-np.inf
    best=np.argsort(-score.reshape(-1),kind="stable")[:350]
    for ix in best:
        if not np.isfinite(score.flat[int(ix)]):break
        a,b=np.unravel_index(int(ix),score.shape)
        cand=exact_source_fit(x,y,[Z[:,a],Z[:,b]],[atoms[a][0],atoms[b][0]],counts)
        if cand:
            cand["source_edit_trace"]="DEFINE_NEW_TWO_ATOM_MACRO_AND_REUSE_SUBEXPRESSIONS"
            return {"status":"SOURCE_VERIFIED","source_verified_program":cand,
              "primitive_nodes":len(atoms),"candidate_graphs_constructed":counts["new_graph_atoms"],
              "fitting_calls":counts["fitting_calls"],"graph_edits":dict(counts)}
    return {"status":"UNKNOWN","source_verified_program":None,
      "primitive_nodes":len(atoms),"candidate_graphs_constructed":counts["new_graph_atoms"],
      "fitting_calls":counts["fitting_calls"],"graph_edits":dict(counts)}

def infer(sourcefile,out):
    rows=json.loads(pathlib.Path(sourcefile).read_text())["source_numeric_without_equations"]
    assert len(rows)==8
    modes=("C_OLD_SAFE_GRAPH_GRAMMAR","C_RECURSIVE_POLYNOMIAL_ONLY",
           "B_NEW_DYNAMIC_TYPED_AST_COMPOSITION")
    allm={}
    for mode in modes:
        start=time.process_time();cases=[];totals=collections.Counter()
        for row in rows:
            if mode=="C_OLD_SAFE_GRAPH_GRAMMAR":
                if not numeric_valid(row):
                    record={"status":"UNKNOWN_SOURCE","source_verified_program":None,
                            "primitive_nodes":0,"candidate_graphs_constructed":0,
                            "fitting_calls":0}
                else:
                    e,programs,calls=eval_action(row,"SAFE")
                    one=programs[0] if programs else None
                    record={"status":"SOURCE_VERIFIED" if one else "UNKNOWN",
                            "source_verified_program":one,"primitive_nodes":0,
                            "candidate_graphs_constructed":0,"fitting_calls":calls}
            else:record=search(row,"POLYNOMIAL_ONLY" if mode=="C_RECURSIVE_POLYNOMIAL_ONLY" else "RECURSIVE_GRAPH")
            record["id"]=row["id"];cases.append(record)
            totals["source_valid"]+=int(record["source_verified_program"] is not None)
            totals["source_calls"]+=record["fitting_calls"]
            totals["constructed_graph_nodes"]+=record["candidate_graphs_constructed"]
        allm[mode]={"cases":cases,"source_work":dict(totals),
                    "cpu_process_s":time.process_time()-start}
    report={"schema":"NEUMANN_Q3_LIVERMORE8_SOURCE_ONLY_CLASSICAL_RECURSIVE_GRAMMAR_HEADROOM.v1",
       "source_only_external_other_author_original_SHA256":sha(pathlib.Path(sourcefile).read_bytes()),
       "model_learns_program_search_policy":"FALSE_CLASSICAL_ALGORITHM_ONLY",
       "new_expression_AST_produced_by_typed_source_graph_edits":True,
       "human_given_base_semantics_and_graph_rewrite_rules":True,
       "external_author_full_formula_available_during_inference":False,
       "first_external_author_family":"LIVERMORE_PUBLISHED_DSO",
       "development_Nguyen_correct_8_of_8_NOT_BLIND":True,
       "methods":allm,"Q3_GLOBAL":"OPEN","G1":"HOLD"}
    receipt=save(out,report)
    print("Q3_LIVERMORE_FIRST_EIGHT_AUTHORED_SOURCE_DYNAMIC_GRAPH_PROGRAMS_SEALED",
        json.dumps({"sha256":receipt,"methods":{k:{"source":v["source_work"],
                   "CPU_s":v["cpu_process_s"]} for k,v in allm.items()}},
                   sort_keys=True),flush=True)

def grade(truthfile,predfile,out):
    true=json.loads(pathlib.Path(truthfile).read_text())["private_true_equations"]
    data=json.loads(pathlib.Path(predfile).read_text());assert len(true)==8
    target={r["id"]:r for r in true}
    methods={};cases={}
    for method,records in data["methods"].items():
        counter=collections.Counter();scored=[]
        for r in records["cases"]:
            gold=target[r["id"]];exact=False;witness=None
            if r["source_verified_program"]:
                try:
                    right=sp.sympify(gold["original_expression_sympy"],locals={"x":X})
                    left=sp.sympify(r["source_verified_program"]["defined_operator_AST"],locals={"x":X})
                    exact=bool(sp.simplify(left-right)==0)
                    if exact:witness=r["source_verified_program"]
                except Exception:pass
            counter["total"]+=1;counter["exact_author_function"]+=int(exact)
            counter["UNKNOWN"]+=int(not exact)
            scored.append({"id":r["id"],"name":gold["task_ID"],
              "true_author_expression_sha256":sha(gold["original_expression"].encode()),
              "true_full_analytic_author_equal":exact,
              "source_only_created_macro":witness,
              "status":"FULL_ORIGINAL_AUTHOR_EXACT" if exact else "UNKNOWN"})
        methods[method]=dict(counter);cases[method]=scored
    report={"schema":"NEUMANN_Q3_FIRST_LIVERMORE8_FULL_ORIGINAL_DYNAMIC_EXPR_AUTHORED_GRADE.v1",
      "sealed_first_source_proposals_SHA256":sha(pathlib.Path(predfile).read_bytes()),
      "private_published_original_formulas_SHA256":sha(pathlib.Path(truthfile).read_bytes()),
      "methods":methods,"all_original_cases":cases,
      "DYNAMIC_PLAIN_CLASSICAL_NOT_NEURAL":True,
      "Q3_STRUCTURAL_HEADROOM_SCOPED":"ONLY_IF_ACTUAL_ORIGINAL_EXACT",
      "Q3_GLOBAL":"OPEN","G1":"HOLD"}
    receipt=save(out,report)
    print("Q3_LIVERMORE8_FIRST_INDEPENDENT_ORIGINAL_AUTHOR_DYNAMIC_AST_EXACT_GRADE",
        json.dumps({"sha256":receipt,"methods":methods},sort_keys=True),flush=True)
    assert all(v["total"]==8 for v in methods.values())
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mode",required=True,choices=("infer","grade"))
    for f in ("source","truth","pred","out"):p.add_argument("--"+f)
    args=p.parse_args()
    if args.mode=="infer":infer(args.source,args.pred)
    else:grade(args.truth,args.pred,args.out)
