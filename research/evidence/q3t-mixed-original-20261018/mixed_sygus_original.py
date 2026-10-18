"""Q3T independently typed mixed Int/Bool original SyGuS frontend and proof.

IMPORTANT: This is a classical semantic/proof correctness upgrade and re-check
of ten already opened, formerly unsupported Q3S original benchmark files.
It is NOT a first blind neural generalization trial or a new learned operator.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,re,sys,time
from pathlib import Path
import z3

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3o-real-sygus-20261018"))
from first_two_originals import sexprs,blobhash
UPSTREAM="6ac90265b11431c9477dfbd33e3e3380234c0499"
FIRST_Q3S_SHA256="f4e290a38a44aa7ba7cd03979ea74149df5f0d4241391d5a2302ada3876b6192"
LICENSE_BLOB="1e853cd500e1317b7c2ad0a2514b548c32c46f5e"
MAX_HELPERS=400
MAX_STATE_VARS=200
MAX_DEPTH=200
SPACER_TIMEOUT_MS=3000
VC_TIMEOUT_MS=2500
MAX_SOURCE_SIZE=250000

class UnsupportedOriginal(Exception):
    pass

SORTS={"Int":z3.IntSort(),"Bool":z3.BoolSort()}

def parse_signature(params):
    if not isinstance(params,list):
        raise UnsupportedOriginal("BAD_FORMAL_ARGUMENT_LIST")
    out=[]
    for item in params:
        if not (isinstance(item,list) and len(item)==2 and
                isinstance(item[0],str) and item[1] in SORTS):
            raise UnsupportedOriginal("UNSUPPORTED_ORIGINAL_TYPED_PARAMETER")
        out.append((item[0],item[1]))
    if len({name for name,_ in out})!=len(out):
        raise UnsupportedOriginal("DUPLICATE_FORMAL_ARGUMENT")
    return out

def compile_original(fr,orig_env,functions):
    function_calls=collections.Counter()
    def tc(expr,expected,where):
        if expr.sort()!=SORTS[expected]:
            raise UnsupportedOriginal("SORT_MISMATCH_"+where)
        return expr

    def unpack_expr(form,env,stack,depth=0):
        if depth>MAX_DEPTH:raise UnsupportedOriginal("HELPER_OR_TERM_RECURSION_CAP")
        if isinstance(form,str):
            if form in env:return env[form]
            if form=="true":return z3.BoolVal(True)
            if form=="false":return z3.BoolVal(False)
            if re.fullmatch(r"-?\d+",form):return z3.IntVal(int(form))
            if form in functions and not functions[form]["args"]:
                return invoke(form,[],stack,depth+1)
            raise UnsupportedOriginal("UNBOUND_ORIGINAL_SYMBOL")
        if not isinstance(form,list) or not form:
            raise UnsupportedOriginal("INVALID_ORIGINAL_FORMULA")
        op=form[0]
        if not isinstance(op,str):raise UnsupportedOriginal("NONATOM_OPERATOR")
        parts=form[1:]
        if op=="let":
            if len(parts)!=2 or not isinstance(parts[0],list):
                raise UnsupportedOriginal("BAD_ORIGINAL_LET")
            # Simultaneous, not sequential bindings as SMT-LIB requires.
            rhs={}
            for pair in parts[0]:
                if (not isinstance(pair,list) or len(pair)!=2 or
                    not isinstance(pair[0],str) or pair[0] in rhs):
                    raise UnsupportedOriginal("DUPLICATE_OR_BAD_LET_BINDING")
                rhs[pair[0]]=unpack_expr(pair[1],env,stack,depth+1)
            return unpack_expr(parts[1],{**env,**rhs},stack,depth+1)
        args=[unpack_expr(p,env,stack,depth+1) for p in parts]
        if op in functions:
            return invoke(op,args,stack,depth+1)
        n=len(args)
        # Refuse malformed arity before constructing a Z3 formula.
        if op=="and" and n>=1:return z3.And(*[tc(a,"Bool","AND") for a in args])
        if op=="or" and n>=1:return z3.Or(*[tc(a,"Bool","OR") for a in args])
        if op=="not" and n==1:return z3.Not(tc(args[0],"Bool","NOT"))
        if op=="=>" and n==2:return z3.Implies(tc(args[0],"Bool","IMPLIES"),tc(args[1],"Bool","IMPLIES"))
        if op=="xor" and n==2:return z3.Xor(tc(args[0],"Bool","XOR"),tc(args[1],"Bool","XOR"))
        if op=="ite" and n==3:
            tc(args[0],"Bool","ITE_CONDITION")
            if args[1].sort()!=args[2].sort():raise UnsupportedOriginal("ITE_BRANCH_SORT_MISMATCH")
            return z3.If(args[0],args[1],args[2])
        if op in ("=","distinct") and n>=2:
            if any(a.sort()!=args[0].sort() for a in args[1:]):
                raise UnsupportedOriginal("EQUALITY_MIXED_SORTS")
            return (z3.And(*[args[i]==args[i+1] for i in range(n-1)])
                    if op=="=" else z3.Distinct(*args))
        if op in ("<","<=",">",">=") and n==2:
            a,b=[tc(x,"Int","ORDER") for x in args]
            return {"<":lambda:a<b,"<=":lambda:a<=b,
                    ">":lambda:a>b,">=":lambda:a>=b}[op]()
        if op in ("+","-","*","div","mod","abs") and (
            (op in ("+","*") and n>=2) or
            (op=="-" and n>=1) or (op in ("div","mod") and n==2) or
            (op=="abs" and n==1)
        ):
            ints=[tc(a,"Int","ARITHMETIC") for a in args]
            if op=="+":return z3.Sum(*ints)
            if op=="-":
                v=ints[0]
                if n==1:return -v
                for a in ints[1:]:v=v-a
                return v
            if op=="*":
                v=ints[0]
                for a in ints[1:]:v=v*a
                return v
            if op=="div":return ints[0]/ints[1]
            if op=="mod":return ints[0]%ints[1]
            if op=="abs":return z3.If(ints[0]>=0,ints[0],-ints[0])
        raise UnsupportedOriginal("UNSUPPORTED_ORIGINAL_OPERATOR_OR_ARITY_"+op[:40])

    def invoke(name,actuals,stack,depth):
        if name in stack:raise UnsupportedOriginal("RECURSIVE_HELPER_FUNCTION_NOT_SUPPORTED")
        if name not in functions:raise UnsupportedOriginal("UNKNOWN_HELPER_FUNCTION")
        f=functions[name]
        if len(actuals)!=len(f["args"]):
            raise UnsupportedOriginal("ORIGINAL_HELPER_ARITY_MISMATCH")
        bound={}
        for (param,sort),value in zip(f["args"],actuals):
            bound[param]=tc(value,sort,"FORMAL_PARAMETER")
        function_calls[name]+=1
        result=unpack_expr(f["body"],bound,stack+(name,),depth+1)
        return tc(result,f["output"],"FUNCTION_RETURN")

    result=unpack_expr(fr,orig_env,(),0)
    return result,function_calls

def extract_mixed_original(forms):
    defs={}
    for form in forms:
        if not isinstance(form,list) or not form:continue
        if form[0]!="define-fun":continue
        if len(form)!=5 or not isinstance(form[1],str):
            raise UnsupportedOriginal("MALFORMED_DEFINE_FUN")
        if form[1] in defs:raise UnsupportedOriginal("DUPLICATE_NAMED_ORIGINAL_FUNCTION")
        if form[3] not in SORTS:raise UnsupportedOriginal("UNSUPPORTED_ORIGINAL_RETURN_SORT")
        defs[form[1]]={
           "args":parse_signature(form[2]),
           "output":form[3],
           "body":form[4]
        }
    if len(defs)>MAX_HELPERS:raise UnsupportedOriginal("TOO_MANY_ORIGINAL_HELPERS")
    synth=[x for x in forms if isinstance(x,list) and x and x[0]=="synth-inv"]
    contracts=[x for x in forms if isinstance(x,list) and x and x[0]=="inv-constraint"]
    if len(synth)!=1 or len(contracts)!=1:
        raise UnsupportedOriginal("NEED_EXACT_ONE_ORIGINAL_SYNTH_INV_AND_CONSTRAINT")
    if len(synth[0])!=3 or len(contracts[0])!=5:
        raise UnsupportedOriginal("ORIGINAL_SYNTH_INV_SHAPE_INVALID")
    inv_name=synth[0][1]
    states=parse_signature(synth[0][2])
    if not states or len(states)>MAX_STATE_VARS:
        raise UnsupportedOriginal("ORIGINAL_STATE_ARITY_OUTSIDE_CAP")
    if contracts[0][1]!=inv_name:
        raise UnsupportedOriginal("WRONG_SYNTH_INV_REFERENCE")
    pre_name,tr_name,post_name=contracts[0][2:]
    if any(x not in defs for x in (pre_name,tr_name,post_name)):
        raise UnsupportedOriginal("MISSING_ORIGINAL_SOURCE_CONSTRAINT_DEF")
    if defs[pre_name]["args"]!=states or defs[post_name]["args"]!=states:
        raise UnsupportedOriginal("ORIGINAL_PRE_POST_ARGUMENTS_CHANGED")
    trargs=defs[tr_name]["args"]
    if len(trargs)!=2*len(states) or trargs[:len(states)]!=states:
        raise UnsupportedOriginal("ORIGINAL_TRANSITION_CURRENT_ARGUMENTS_CHANGED")
    if [s for _,s in trargs[len(states):]]!=[s for _,s in states]:
        raise UnsupportedOriginal("ORIGINAL_TRANSITION_NEXT_ARGUMENT_SORT_CHANGED")
    now=[z3.Const("q3t_now_"+str(i),SORTS[sort]) for i,(_,sort) in enumerate(states)]
    nxt=[z3.Const("q3t_next_"+str(i),SORTS[sort]) for i,(_,sort) in enumerate(states)]
    c1,c2,c3=collections.Counter(),collections.Counter(),collections.Counter()
    pre,c1=compile_original(defs[pre_name]["body"],
        dict(zip((s for s,_ in defs[pre_name]["args"]),now)),defs)
    trans,c2=compile_original(defs[tr_name]["body"],
        dict(zip((s for s,_ in trargs),now+nxt)),defs)
    post,c3=compile_original(defs[post_name]["body"],
        dict(zip((s for s,_ in defs[post_name]["args"]),now)),defs)
    if not all(z3.is_bool(x) for x in (pre,trans,post)):
        raise UnsupportedOriginal("ORIGINAL_BOOLEAN_RELATION_RETURN_INVALID")
    callers=(c1+c2+c3)
    return {
      "now":now,"next":nxt,"pre":pre,"trans":trans,"post":post,
      "num_bool":sum(s=="Bool" for _,s in states),
      "num_int":sum(s=="Int" for _,s in states),
      "defined_function_count":len(defs),
      "helper_calls_expanded":sum(v for k,v in callers.items()
          if k not in (pre_name,tr_name,post_name)),
      "function_call_names":sorted(callers),
    }

def check_formula(formula,timeout=VC_TIMEOUT_MS):
    s=z3.Solver();s.set(timeout=timeout);s.add(formula)
    try:return str(s.check())
    except Exception:return "error"

def check_cover(inv,original):
    if not z3.is_bool(inv):return {"status":"UNSUPPORTED_NONBOOL_COVER"}
    now,nxt=original["now"],original["next"]
    if set(z3.z3util.get_vars(inv))-set(now):
        return {"status":"UNBOUND_VARIABLE_IN_COVER"}
    iv_next=z3.substitute(inv,*list(zip(now,nxt)))
    queries={
      "initial":z3.And(original["pre"],z3.Not(inv)),
      "consecution":z3.And(inv,original["trans"],z3.Not(iv_next)),
      "post":z3.And(inv,z3.Not(original["post"])),
    }
    outcomes={k:check_formula(q) for k,q in queries.items()}
    outcomes["status"]="ORIGINAL_FULL_3VC_CERTIFIED" if all(
        outcomes[x]=="unsat" for x in queries) else "NO_THREE_VC_CERTIFICATE"
    outcomes["proof_expression_sha256"]=hashlib.sha256(inv.sexpr().encode()).hexdigest()
    return outcomes

def run_original(source):
    start=time.perf_counter_ns()
    record={"frontend_status":"UNKNOWN","source_goal_not_modified":True}
    try:
        original=extract_mixed_original(sexprs(source))
        rec={
          "original_int_vars":original["num_int"],
          "original_bool_vars":original["num_bool"],
          "original_defined_functions":original["defined_function_count"],
          "named_helper_calls_expanded":original["helper_calls_expanded"],
        }
        record.update(rec)
        presat=check_formula(original["pre"])
        postnon=check_formula(z3.Not(original["post"]))
        record["original_pre_sat"]=presat
        record["original_not_post_sat"]=postnon
        record["frontend_status"]="PARSED_ORIGINAL_MIXED_SORT"
        if presat!="sat" or postnon!="sat":
            record["status"]="ABSTAIN_EMPTY_OR_UNKNOWN_PRE_OR_TRIVIAL_POST"
            return record
        now,nxt=original["now"],original["next"]
        relation=z3.Function("q3t_Reach",*[x.sort() for x in now],z3.BoolSort())
        bad=z3.Function("q3t_Bad",z3.BoolSort())
        fp=z3.Fixedpoint();fp.set(engine="spacer",timeout=SPACER_TIMEOUT_MS)
        fp.register_relation(relation,bad)
        fp.declare_var(*(now+nxt))
        fp.rule(relation(*now),original["pre"])
        fp.rule(relation(*nxt),z3.And(relation(*now),original["trans"]))
        fp.rule(bad(),z3.And(relation(*now),z3.Not(original["post"])))
        wall0=time.perf_counter_ns()
        try:
            ans=str(fp.query(bad()))
            reason=fp.reason_unknown() if ans=="unknown" else None
        except Exception as e:
            ans="error"
            reason=type(e).__name__+":"+str(e)[:110]
        record["direct_original_bad_exit"]=ans
        record["solver_reason_if_not_decided"]=reason
        record["direct_original_chc_wall_ms"]=round((time.perf_counter_ns()-wall0)/1e6,3)
        record["original_direct_safety_proven"]=ans=="unsat"
        record["status"]="FULL_ORIGINAL_CLASSICAL_SAFETY_PROVEN" if ans=="unsat" else "ORIGINAL_SAFETY_NOT_PROVEN"
        record["original_inductive_cover_three_vc"]=[]
        if ans=="unsat":
            try:
                cover=fp.get_cover_delta(-1,relation)
                for order in ("FORWARD","REVERSED"):
                    variables=now if order=="FORWARD" else list(reversed(now))
                    expr=z3.substitute_vars(cover,*variables)
                    proof=check_cover(expr,original)
                    proof["variable_binding"]=order
                    if proof["status"]=="ORIGINAL_FULL_3VC_CERTIFIED":
                        record["original_inductive_cover_three_vc"].append(proof)
            except Exception as exc:
                record["cover_error_type"]=type(exc).__name__
        record["original_proof_carried_typed_ast"]=any(
            x["status"]=="ORIGINAL_FULL_3VC_CERTIFIED"
            for x in record["original_inductive_cover_three_vc"])
        return record
    except Exception as exc:
        record["frontend_status"]="ABSTAIN_UNSUPPORTED_SOURCE_OR_BACKEND"
        record["status"]="NO_ORIGINAL_PROOF"
        record["reason_type"]=type(exc).__name__
        record["reason_category"]=str(exc).split(":")[0][:110]
        return record
    finally:
        record["total_case_wall_ms"]=round((time.perf_counter_ns()-start)/1e6,3)

def controls():
    header="(set-logic LIA)\n(synth-inv inv ((x Int) (flag Bool)))\n"
    pre="(define-fun pre ((x Int) (flag Bool)) Bool (and (= x 0) (= flag false)))\n"
    tr="(define-fun trans ((x Int) (flag Bool) (x! Int) (flag! Bool)) Bool (and (= x! (+ x 1)) (= flag! (or flag (< x 0)))))\n"
    post_good="(define-fun post ((x Int) (flag Bool)) Bool (and (>= x 0) (= flag false)))\n"
    post_bad="(define-fun post ((x Int) (flag Bool)) Bool (and (<= x 0) (= flag false)))\n"
    end="(inv-constraint inv pre trans post)\n(check-synth)\n"
    good=(header+pre+tr+post_good+end).encode()
    bad=(header+pre+tr+post_bad+end).encode()
    extra="(define-fun notnegative ((v Int)) Bool (>= v 0))\n"
    good_helper=(header+extra+pre+tr+post_good.replace("(>= x 0)","(notnegative x)")+end).encode()
    # Side-effect-free macro expansion has to preserve original meaning exactly.
    orig=extract_mixed_original(sexprs(good))
    helper=extract_mixed_original(sexprs(good_helper))
    parity=check_formula(z3.Xor(orig["post"],helper["post"]))
    results={
      "mixed_int_bool_safe_original":run_original(good),
      "mixed_int_bool_unsafe_original":run_original(bad),
      "named_helper_safe_original":run_original(good_helper),
      "named_helper_expansion_equivalent_original_post":parity,
      "wrong_original_invariant_rejected":check_cover(z3.BoolVal(True),orig),
    }
    correct=(
      results["mixed_int_bool_safe_original"].get("direct_original_bad_exit")=="unsat"
      and results["mixed_int_bool_unsafe_original"].get("direct_original_bad_exit")=="sat"
      and results["named_helper_safe_original"].get("direct_original_bad_exit")=="unsat"
      and parity=="unsat"
      and results["wrong_original_invariant_rejected"].get("status")!="ORIGINAL_FULL_3VC_CERTIFIED"
    )
    results["controls_all_pass"]=correct
    return results

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--q3s-first",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    source_report=a.q3s_first.read_bytes()
    if hashlib.sha256(source_report).hexdigest()!=FIRST_Q3S_SHA256:
        raise ValueError("IMMUTABLE_FIRST_Q3S_RECEIPT_NOT_MATCHING")
    prior=json.loads(source_report)
    if prior["status"]!="COMPLETE_FIRST_FROZEN_AFFINE_STUDY":
        raise ValueError("HISTORIC_Q3S_ORIGINAL_RECEIPT_NOT_COMPLETE")
    lic=blobhash((a.root/"LICENSE.md").read_bytes())
    if lic!=LICENSE_BLOB:raise ValueError("EXTERNAL_REPO_LICENSE_IDENTITY_CHANGED")
    fixed=[
        r for r in prior["all_first_exact_original_receipts"]
        if r["status"]=="ABSTAIN_UNSUPPORTED_OR_EMPTY_ORIGINAL_PRE"
    ]
    if len(fixed)!=10 or len({r["original_source_sha"] for r in fixed})!=10:
        raise ValueError("PREDECLARED_Q3S_10_UNSUPPORTED_ORIGINALS_MISMATCH")
    controls_result=controls()
    if not controls_result["controls_all_pass"]:
        raise ValueError("MIXED_SORT_SEMANTIC_ADVERSARIAL_CONTROLS_FAILED")
    records=[]
    for entry in fixed:
        pth=a.root/entry["original_path"]
        raw=pth.read_bytes()
        sourcehash=blobhash(raw)
        if sourcehash!=entry["original_source_sha"]:
            raise ValueError("MISMATCH_IMMUTABLE_ORIGINAL_SOURCE_BYTES")
        if len(raw)>MAX_SOURCE_SIZE:
            result={"frontend_status":"ABSTAIN_OVERSIZED_ORIGINAL",
                    "status":"NO_ORIGINAL_PROOF"}
        else:result=run_original(raw)
        records.append({"source_path":entry["original_path"],
            "original_source_git_blob":sourcehash,**result})
    returnval={
       "study":"Q3T_MIXED_BOOL_INT_ORIGINAL_SYGUS_SEMANTIC_CORRECTNESS_HARDENING",
       "first_original_Q3S_receipt_SHA256":FIRST_Q3S_SHA256,
       "frozen_upstream_revision":UPSTREAM,
       "original_source_count":len(records),
       "adversarial_mixed_original_controls":controls_result,
       "originals_parsed_with_mixed_semantics":sum(
           r["frontend_status"]=="PARSED_ORIGINAL_MIXED_SORT" for r in records),
       "independently_classically_proven_original_programs":sum(
           r.get("original_direct_safety_proven",False) for r in records),
       "original_proof_backchecked_3VC_typed_AST_seeds":sum(
           r.get("original_proof_carried_typed_ast",False) for r in records),
       "source_failure_types":dict(collections.Counter(
           r.get("reason_category","NONE") for r in records
           if r["frontend_status"]!="PARSED_ORIGINAL_MIXED_SORT")),
       "trained_neural_inference_calls":0,
       "learned_new_math_operator":False,
       "chc_comp_Q3F_sealed_originals_opened":False,
       "source_or_formula_text_redistributed":False,
       "global_Q1_Q7":"OPEN",
       "first_original_file_receipts":records
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(returnval,indent=2)+"\n")
    print("Q3T_MIXED_SOURCE_CONTROLS",controls_result["controls_all_pass"])
    print("Q3T_FIXED_TEN_ORIGINAL_FRONTEND",returnval["originals_parsed_with_mixed_semantics"],"OF",len(records))
    print("Q3T_TRUE_ORIGINAL_CLASSICAL_PROOFS",returnval["independently_classically_proven_original_programs"])
    print("Q3T_VERIFIED_TRAINABLE_COVER_AST",returnval["original_proof_backchecked_3VC_typed_AST_seeds"])
    print("Q3T_ORIGINAL_DIAGNOSTICS",[(x["source_path"],x["frontend_status"],x.get("reason_category"),x.get("direct_original_bad_exit")) for x in records])
    print("Q3T_Q1_Q7",returnval["global_Q1_Q7"])
if __name__=="__main__":main()
