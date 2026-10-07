"""Independent Z3 translation/proofs and mathematical original-goal replay."""
import itertools
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.representation_headroom import digest,package_identity,save


def read(path):return json.loads(path.read_text(encoding="utf-8"))


def z3_expression(term,env):
    import z3
    if type(term)is bool:return z3.BoolVal(term)
    if type(term)is int:return z3.IntVal(term)
    if isinstance(term,str):return env[term]
    args=[z3_expression(t,env) for t in term[1:]]
    op=term[0]
    if op=="add":return args[0]+args[1]
    if op=="sub":return args[0]-args[1]
    if op=="max":return z3.If(args[0]>=args[1],args[0],args[1])
    if op=="min":return z3.If(args[0]<=args[1],args[0],args[1])
    if op=="ge":return args[0]>=args[1]
    if op=="le":return args[0]<=args[1]
    if op=="gt":return args[0]>args[1]
    if op=="lt":return args[0]<args[1]
    if op=="eq":return args[0]==args[1]
    if op=="and":return z3.And(*args)
    if op=="or":return z3.Or(*args)
    if op=="not":return z3.Not(args[0])
    if op=="ite":return z3.If(*args)
    raise AssertionError("Unknown independently parsed constructor")


def independent_obligations(problem,proposal):
    import z3
    width=len(proposal["empty"])
    vectors=[[z3.Int(f"{prefix}{i}") for i in range(width)] for prefix in ["z","l","r","a","b","c"]]
    v,left,right,a,b,c=vectors
    h=z3.Int("head")
    e=[z3.IntVal(i) for i in proposal["empty"]]
    def P(key,args):
        env=dict(zip(proposal[key]["inputs"],args))
        return [z3_expression(expr,env) for expr in proposal[key]["outputs"]]
    I=lambda s:P("invariant",s)[0]
    D=lambda s:P("decode",s)
    S=lambda head,s:P("step",[head]+s)
    M=lambda x,y:P("merge",x+y)
    def equality(xs,ys):
        assert len(xs)==len(ys)
        return z3.And(*[x==y for x,y in zip(xs,ys)])
    def R(s):
        env=dict(zip(problem["step"]["inputs"],[h]+s))
        return [z3_expression(expr,env) for expr in problem["step"]["outputs"]]
    return {"INITIAL_VALID":I(e),"STEP_VALID":z3.Implies(I(v),I(S(h,v))),
            "DECODE_EMPTY":equality(D(e),[z3.IntVal(x) for x in problem["empty"]]),
            "DECODE_STEP":z3.Implies(I(v),equality(D(S(h,v)),R(D(v)))),
            "MERGE_VALID":z3.Implies(z3.And(I(left),I(right)),I(M(left,right))),
            "LEFT_IDENTITY":z3.Implies(I(v),equality(M(e,v),v)),
            "RIGHT_IDENTITY":z3.Implies(I(v),equality(M(v,e),v)),
            "CONS_NATURALITY":z3.Implies(z3.And(I(left),I(right)),equality(M(S(h,left),right),S(h,M(left,right)))),
            "ASSOCIATIVE":z3.Implies(z3.And(I(a),I(b),I(c)),equality(M(M(a,b),c),M(a,M(b,c))))}


def eval_integer(expr,env):
    if type(expr)in(int,bool):return expr
    if isinstance(expr,str):return env[expr]
    op=expr[0]
    if op=="ite":return eval_integer(expr[2] if eval_integer(expr[1],env) else expr[3],env)
    args=[eval_integer(t,env) for t in expr[1:]]
    functions={"add":lambda a,b:a+b,"sub":lambda a,b:a-b,"max":max,"min":min,
               "ge":lambda a,b:a>=b,"le":lambda a,b:a<=b,"gt":lambda a,b:a>b,"lt":lambda a,b:a<b,
               "eq":lambda a,b:a==b,"and":lambda a,b:a and b,"or":lambda a,b:a or b,"not":lambda a:not a}
    return functions[op](*args)


def eval_program(program,args):
    return [eval_integer(t,dict(zip(program["inputs"],args))) for t in program["outputs"]]


def numeric_tree(proposal,tree):
    tag=tree[0]
    if tag=="nil":return list(proposal["empty"]),[]
    if tag=="single":return eval_program(proposal["step"],[tree[1]]+proposal["empty"]),[tree[1]]
    assert tag=="concat" and len(tree)==3
    left,lvals=numeric_tree(proposal,tree[1]);right,rvals=numeric_tree(proposal,tree[2])
    return eval_program(proposal["merge"],left+right),lvals+rvals


def mathematical_reference(name,values):
    # Independent definitions of the four selected reference goals,not their
    # parsed recurrence or any candidate summary formulas.
    total=sum(values)
    prefix=max(sum(values[:n]) for n in range(len(values)+1))
    suffix=max(sum(values[n:]) for n in range(len(values)+1))
    if name=="sum":return [total]
    if name=="mps":return [prefix,total]
    if name=="mts":return [suffix,total]
    if name=="lifted_prefix":return [prefix]
    assert name=="mss"
    best=max(sum(values[i:j]) for i in range(len(values)+1) for j in range(i,len(values)+1))
    return [total,suffix,prefix,best]


def replay(source,preparation,first,output):
    import z3
    reg=read(preparation/"registration.json")
    receipt=read(preparation/"first-result-receipt.json")
    assert digest(preparation/"registration.json")==read(preparation/"freeze-receipt.json")["registration_sha256"]
    assert digest(first/"report.json")==receipt["report_sha256"]
    assert digest(first/"manifest.json")==receipt["manifest_sha256"]
    assert digest(source/"manifest.json")==reg["upstream_manifest_sha256"]
    upstream=read(source/"manifest.json")
    assert all(digest(source/r["path"])==r["sha256"] for r in upstream["files"])
    assert all(digest(ROOT/p)==pin and digest(preparation/"source"/p)==pin for p,pin in reg["sources"].items())
    assert all(package_identity(p)==pin for p,pin in reg["packages"].items())
    manifest=read(first/"manifest.json")
    assert all(digest(first/p)==pin for p,pin in manifest.items())
    report=read(first/"report.json")
    proposals={};proofs=0;serialized=0;native_failures=[]
    for case in report["cases"]:
        identifier=case["id"]
        problem=read(first/("fixtures" if case["source_role"]=="F" else "public")/(identifier+".json"))
        for route in case["routes"]:
            record=read(first/"offline"/(identifier+".json")) if route=="KNOWN_OFFLINE_REFERENCE" else read(first/"native"/identifier/"result.json")
            proposal,certificate=record["proposal"],record["certificate"]
            assert certificate["accepted"] and len(certificate["obligations"])==9
            formulas=independent_obligations(problem,proposal)
            for name,formula in formulas.items():
                solver=z3.Solver();solver.set(timeout=2000);solver.add(z3.Not(formula))
                assert solver.check()==z3.unsat,(identifier,route,name)
                proofs+=1
            for obligation in certificate["obligations"]:
                solver=z3.Solver();solver.set(timeout=2000);solver.from_string(obligation["smt2"])
                assert solver.check()==z3.unsat
                serialized+=1
            proposals[(identifier,route)]=proposal
        if case["source_role"]=="D" and "PUBLIC_SYGUS_GENERATED" not in case["routes"]:
            native_failures.append({"id":identifier,"receipt":read(first/"native"/(identifier+".receipt.json")),
                                   "progress_available":(first/"native"/identifier/"progress.json").exists()})
    seen=set();numeric=0
    with (first/"witnesses.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            row=json.loads(line);proposal=proposals[(row["case"],row["route"])]
            state,flattened=numeric_tree(proposal,row["tree"])
            assert flattened==row["values"]
            actual=eval_program(proposal["decode"],state)
            assert actual==row["actual"]==row["reference"]==mathematical_reference(row["case"],row["values"])
            key=(row["case"],row["route"],tuple(row["values"]),row["shape"])
            assert key not in seen;seen.add(key);numeric+=1
    sequences=[v for n in range(reg["max_length"]+1) for v in itertools.product(reg["alphabet"],repeat=n)]
    expected={(case,route,v,shape) for case,route in proposals for v in sequences for shape in reg["tree_shapes"]}
    assert seen==expected and numeric==report["paired_numeric_queries"] and proofs==report["universal_obligations_for_accepted_routes"]
    false=read(first/"false_proposals.json")
    fixture=read(first/"fixtures/lifted_prefix.json")
    for name,control in false.items():
        last=control["check"]["obligations"][-1]
        assert last["status"]=="sat"
        solver=z3.Solver();solver.from_string(last["smt2"])
        assert solver.check()==z3.sat
        own=independent_obligations(fixture,control["proposal"])[last["obligation"]]
        solver=z3.Solver();solver.add(z3.Not(own));assert solver.check()==z3.sat
    insufficient=read(first/"insufficient_fixed_statistic.json")
    assert mathematical_reference("lifted_prefix",insufficient["left1"])==mathematical_reference("lifted_prefix",insufficient["left2"])
    assert [mathematical_reference("lifted_prefix",insufficient[key]+insufficient["right"]) for key in ["left1","left2"]]==insufficient["concat_outputs"]
    output.mkdir(parents=True,exist_ok=False)
    save(output/"replay.json",{"status":"PASS_INDEPENDENT_RECURSIVE_SUMMARY_ENGINEERING_AUDIT",
         "upstream_files_checked":len(upstream["files"]),"manifest_files_checked":len(manifest),
         "independent_Z3_AST_obligations":proofs,"serialized_CVC5_queries_replayed_in_Z3":serialized,
         "numeric_tree_interpretations_and_mathematical_references":numeric,"distinct_proposals":len(proposals),
         "false_certificate_controls_reproduced":len(false),"native_nonacceptances_retained":native_failures,
         "original_report_sha256":digest(first/"report.json"),"original_manifest_sha256":digest(first/"manifest.json"),
         "full_OCaml_or_Synduce_replayed":False,"performance_claim":False,"fresh_eligible":0,"G1_admitted":False})
    print((output/"replay.json").read_text(encoding="utf-8"))


if __name__=="__main__":replay(*(Path(p) for p in sys.argv[1:]))
