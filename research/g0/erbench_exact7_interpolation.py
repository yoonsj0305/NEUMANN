"""NEUMANN Q34: exact 7-query rational function identification.

First prospective on untouched ERBench hash-rank eligible 1D original tasks
2096:2128, outside previously opened train/test positions 0:2096.

Mathematics: for deg P<=4, deg Q<=2, two distinct rational functions
cannot agree at 7 finite distinct input points: P1Q2-P2Q1 deg <=6.
Six DO NOT suffice in the worst case (explicit 6-collision witness).

This is a CLASSICAL exact-algebra learner and SOURCE ORACLE experiment,
not a neural-exclusive new primitive. Exact rational oracle is qualitatively
stronger than prior 48 binary64 numerical samples and has distinct costs.
"""
import argparse,ast,collections,csv,hashlib,json,pathlib,time
import sympy as sp
from erbench_original_second import allowed_formula,domain,calc,SYM
X=sp.Symbol('x')
DATA_SHA="03c0ceb53ed0348650c0a94ed5cd1e452325d2b7c7d3be68f9a458316eda33b1"
DATA_REV="95bf15c27de68c3f170ca6140d2e4a811c60344f"
START=2096
END=2128
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,data):
    path=pathlib.Path(name);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
    return sha(path.read_bytes())
def exact_theorem_and_six_collision():
    """Symbolic proof of 7 uniqueness; 6-pt collision is constructive."""
    R=X**4/(1+X**2)
    Q=1+X**2
    P=X**4
    V6=sp.prod(X-i for i in range(1,7))
    V=-sp.rem(V6,Q,X)
    U,rem=sp.div(V6+P*V,Q,X)
    assert rem==0 and sp.degree(U,X)<=4 and sp.degree(V,X)<=2
    eps=sp.Rational(1,10)
    R2=(P+eps*U)/(Q+eps*V)
    difference=sp.factor(sp.cancel(R2-R))
    assert sp.cancel(difference-eps*V6/(Q*(Q+eps*V)))==0
    for xx in range(1,7):
        assert Q.subs(X,xx)!=0 and (Q+eps*V).subs(X,xx)!=0
        assert sp.cancel(difference.subs(X,xx))==0
    assert sp.cancel(difference.subs(X,7))!=0
    assert sp.degree(sp.fraction(sp.cancel(R2))[0],X)<=4
    assert sp.degree(sp.fraction(sp.cancel(R2))[1],X)<=2
    return {"seven_point_sufficiency_proof":
       "For f1=P1/Q1 and f2=P2/Q2 with degree P<=4 degree Q<=2, if they agree at 7 distinct non-poles then N=P1Q2-P2Q1 (degree<=6) has 7 distinct roots, hence N=0, so functions are identical in Q(x)",
      "six_point_explicit_counterexample_r1":str(sp.cancel(R)),
      "six_point_explicit_counterexample_r2":str(sp.cancel(R2)),
      "six_equal_points":[1,2,3,4,5,6],
      "seventh_disagreement_x":7,
      "seventh_difference":str(sp.cancel(difference.subs(X,7))),
      "exact_identity_and_collision_checked":True,
      "max_numerator_degree":4,"max_denominator_degree":2,
      "worst_case_query_minimum":7}
def task_order(csvrows):
    eligible=[]
    for i,r in enumerate(csvrows):
        try:
            original_tree,var=allowed_formula(r["expression"])
            low,high,provenance=domain(r.get("support",""))
            eligible.append((i,r,original_tree,var,low,high,provenance))
        except Exception:pass
    eligible.sort(key=lambda u:sha((str(u[1]["collection"])+"\x1f"+str(u[1]["task_ID"])+"\x1f"+str(u[0])).encode()))
    assert len(eligible)==5717
    return eligible
def exact_oracle(tree,var,low,high):
    """All oracle attempts are charged, including invalid/off-domain responses."""
    lo=sp.Rational(str(low));hi=sp.Rational(str(high))
    assert lo<hi
    queries=[]
    charged=0
    for j in range(1,14):
        xi=lo+(hi-lo)*sp.Rational(j,14)
        charged+=1
        try:
            result=calc(tree,{var:xi},SYM)
            answer=sp.cancel(sp.together(result))
            if answer.is_Rational and (abs(answer.p)<=10**90 and answer.q<=10**90):
                queries.append({"x":str(xi),"y":str(answer)})
                if len(queries)==7:break
        except Exception:pass
    if len(queries)<7:return {"status":"UNKNOWN_NOT_SEVEN_EXACT_RATIONAL_QUERY_REPLIES","attempted_oracle_calls":charged,"valid_replies":len(queries)}
    assert len({v["x"] for v in queries})==7
    return {"status":"SEVEN_EXACT_RATIONAL_REPLIES","attempted_oracle_calls":charged,"replies":queries}
def prepare(csv_path,source,private):
    raw=pathlib.Path(csv_path).read_bytes()
    assert sha(raw)==DATA_SHA,"AUTHOR_DATASET_REVISION_MISMATCH"
    originals=list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    assert len(originals)==10000
    ordered=task_order(originals)
    cohort=ordered[START:END]
    assert len(cohort)==32
    ids=[r["collection"]+":"+r["task_ID"] for _,r,*_ in cohort]
    print("EXACT7_FOURTH_ORIGINAL_METADATA_FROZEN_BEFORE_ORACLE",
          json.dumps({"dataset_sha256":DATA_SHA,"eligible":len(ordered),
           "start":START,"end_exclusive":END,"cohort_original_task_ids":ids}),flush=True)
    public=[];truth=[]
    for i,r,tree,var,lo,hi,provenance in cohort:
        uid=sha((r["collection"]+"\x1f"+r["task_ID"]+"\x1f"+str(i)).encode())[:24]
        numeric=exact_oracle(tree,var,lo,hi)
        public.append({"id":uid,"collection":r["collection"],
                       "task_ID":r["task_ID"],"original_domain_provenance":provenance,
                       **numeric})
        truth.append({"id":uid,"original_expr":r["expression"],"original_var":var,
                      "collection":r["collection"],"task_ID":r["task_ID"],
                      "original_formula_sha256":sha(r["expression"].encode())})
    ssha=save(source,{"schema":"NEUMANN_EXACT7_SOURCE_FOURTH32.v1","original_dataset_sha":DATA_SHA,
         "human_grammar":"rational P<=4 Q<=2 over Q",
         "original_cohort_rank":[START,END],"results":public,
         "source_oracle_type":"exact rational responses from original author formula, stronger than historical binary64 observation",
         "source_original_equations_excluded":True})
    tsha=save(private,{"schema":"NEUMANN_EXACT7_PRIVATE_TRUE_FORMULA.v1",
        "originals":truth,"original_dataset_sha":DATA_SHA})
    print("EXACT7_ORIGINAL_SOURCE_PRIVATE_SPLIT",json.dumps({
         "source_sha256":ssha,"secret_sha256":tsha,
         "oracle_available":sum(t["status"]=="SEVEN_EXACT_RATIONAL_REPLIES" for t in public),
         "total_queries_charged":sum(t["attempted_oracle_calls"] for t in public)}),flush=True)
def exact_fit(points):
    """No learning, no hidden source expression; exact rational linear algebra."""
    start=time.process_time()
    xy=[(sp.Rational(z["x"]),sp.Rational(z["y"])) for z in points]
    if len(xy)!=7 or len({x for x,y in xy})!=7:
        return {"status":"UNKNOWN_INVALID_PROBES","cpu_s":time.process_time()-start}
    for pivot in range(3):
        unknowns=[sp.Symbol("a"+str(i)) for i in range(5)]+[sp.Symbol("b"+str(j)) for j in range(3) if j!=pivot]
        mat=[];rhs=[]
        for x,y in xy:
            mat.append([x**i for i in range(5)]+[-y*x**j for j in range(3) if j!=pivot])
            rhs.append(y*x**pivot)
        try:
            A=sp.Matrix(mat);B=sp.Matrix(rhs)
            answer=sp.linsolve((A,B),unknowns)
            if answer is sp.EmptySet:continue
            sol=next(iter(answer))
            free=set().union(*(s.free_symbols for s in sol))
            possible=[]
            # All rational free variable choices, fixed before authors' ground truth.
            for val in (0,1,-1,2):
                coeff=[sp.cancel(v.subs({symbol:val for symbol in free})) for v in sol]
                if not all(c.is_Rational for c in coeff):continue
                p=sum(coeff[i]*X**i for i in range(5))
                q=X**pivot+sum(coeff[5+k]*X**j for k,j in enumerate(j for j in range(3) if j!=pivot))
                f=sp.cancel(p/q)
                if not f.is_rational_function(X):continue
                num,den=sp.fraction(f)
                if den==0:continue
                if any(sp.cancel(f.subs(X,x)-y)!=0 for x,y in xy):continue
                possible.append(f)
            if not possible:continue
            f=min(possible,key=lambda g:(sp.degree(sp.fraction(g)[0],X)+sp.degree(sp.fraction(g)[1],X),len(str(g))))
            return {"status":"SEVEN_POINT_CONDITIONALLY_UNIQUE_RATIONAL_PROGRAM",
                    "candidate_expr":str(f),"pivot":pivot,
                    "cpu_s":time.process_time()-start,
                    "exact_rational_source_matches":7,
                    "numeric_tolerance_used":False}
        except Exception:continue
    return {"status":"UNKNOWN_NO_VALID_EXACT_RATIONAL_PROGRAM",
            "cpu_s":time.process_time()-start}
def infer(source,out):
    entry=json.loads(pathlib.Path(source).read_text())
    assert entry["original_dataset_sha"]==DATA_SHA and entry["original_cohort_rank"]==[START,END]
    results=[];counts=collections.Counter()
    for case in entry["results"]:
        if case["status"]!="SEVEN_EXACT_RATIONAL_REPLIES":
            a={"status":"UNKNOWN_NO_SEVEN_EXACT_ORACLE_REPLIES","cpu_s":0}
        else:a=exact_fit(case["replies"])
        counts[a["status"]]+=1
        results.append({"id":case["id"],"attempted_oracle_calls":case["attempted_oracle_calls"],**a})
    r={"schema":"NEUMANN_FOURTH_ORIGINAL_EXACT7_PREDICTION_SEALED.v1",
       "source_original_sha256":sha(pathlib.Path(source).read_bytes()),
       "theorem":exact_theorem_and_six_collision(),"all_32_source_programs":results,
       "counts":dict(counts),"total_candidate_cpu_s":sum(x["cpu_s"] for x in results),
       "no_original_author_formula_in_this_stage":True,
       "all_seven_exact_rational_probes_accounted":True,
       "trained_neural_parameters":0,"full_cost_frontier_10x":"NOT_TESTED"}
    code=save(out,r)
    print("EXACT7_ORIGINAL_FOURTH32_SEALED",json.dumps({"sha256":code,"counts":dict(counts),
      "total_candidate_cpu_s":r["total_candidate_cpu_s"]}),flush=True)
def grade(secret,pred,out):
    p=json.loads(pathlib.Path(pred).read_text())
    t=json.loads(pathlib.Path(secret).read_text())
    assert t["original_dataset_sha"]==DATA_SHA
    preds={x["id"]:x for x in p["all_32_source_programs"]}
    counts=collections.Counter();rows=[]
    for task in t["originals"]:
        candidate=preds[task["id"]]
        counts["total_originals"]+=1
        status="UNKNOWN_ABSTAIN"
        if candidate["status"]=="SEVEN_POINT_CONDITIONALLY_UNIQUE_RATIONAL_PROGRAM":
            try:
                astnode,var=allowed_formula(task["original_expr"])
                author=calc(astnode,{var:X},SYM)
                proposed=sp.sympify(candidate["candidate_expr"],locals={"x":X})
                if sp.cancel(sp.together(author-proposed))==0:
                    status="FULL_ORIGINAL_SYMBOLICALLY_EQUIVALENT"
                    counts["original_exact"]+=1
                else:
                    status="NOT_ORIGINAL_EQUAL_REJECTED"
                    counts["original_wrong_proposals_rejected"]+=1
            except Exception as e:
                status="UNKNOWN_SYMBOLIC_GRADE_"+type(e).__name__
                counts["grader_unsupported"]+=1
        else:counts["abstain"]+=1
        rows.append({"id":task["id"],"collection":task["collection"],
                     "task_ID":task["task_ID"],"original_sha256":task["original_formula_sha256"],
                     "attempted_oracle_calls":candidate["attempted_oracle_calls"],
                     "source_candidate_status":candidate["status"],"original_grade":status})
    r={"schema":"NEUMANN_EXACT7_FOURTH_AUTHOR_ORIGINAL_GRADE.v1",
       "original_4th_source_cohort":32,
       "predictions_sha256":sha(pathlib.Path(pred).read_bytes()),
       "private_truth_sha256":sha(pathlib.Path(secret).read_bytes()),
       "theoretical_seven_sufficiency_six_insufficiency":True,
       "independent_original_full_author_expr_verification":True,
       "counts":dict(counts),"rows":rows,
       "G0_conditional_information_gain":"SCOPED_PROVED",
       "Q3_neurally_invented_operator":"NOT_TESTED",
       "Q4_total_system_10x":"NOT_PROVED",
       "benchmark_hidden_private":"NO_PUBLIC_DEVELOPMENT_ONLY",
       "full_specialist_baseline":"THIS_IS_CLASSICAL_EXACT_RATIONAL_INTERPOLATION"}
    sig=save(out,r)
    print("EXACT7_FOURTH32_ORIGINAL_AUTHOR_INDEPENDENT_GRADE",
        json.dumps({"counts":dict(counts),"sha256":sig},sort_keys=True),flush=True)
    assert counts["total_originals"]==32
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--mode",choices=("prepare","infer","grade","theorem"),required=True)
    for z in ("csv_path","source","private","pred","out"):
        a.add_argument("--"+z.replace("_","-"))
    c=a.parse_args()
    if c.mode=="prepare":prepare(c.csv_path,c.source,c.private)
    elif c.mode=="infer":infer(c.source,c.out)
    elif c.mode=="grade":grade(c.private,c.pred,c.out)
    else:print("EXACT7_SHARP_THEOREM",json.dumps(exact_theorem_and_six_collision(),sort_keys=True))
