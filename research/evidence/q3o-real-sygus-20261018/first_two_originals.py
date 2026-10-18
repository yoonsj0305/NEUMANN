"""Q3O: exact external SyGuS-INV source -> Z3 Reach/Bad + proof-backed AST cover.

Source-only original pre/trans/post. No benchmark answers, no CHC-COMP escrow.
First fixed 2016 LIA and 2018 NIA tasks, identical pinned source bytes.
"""
from __future__ import annotations
import argparse, hashlib, json, re, time
from pathlib import Path
import z3

SOURCE_REV="6ac90265b11431c9477dfbd33e3e3380234c0499"
LICENSE_BLOB="1e853cd500e1317b7c2ad0a2514b548c32c46f5e"
SOURCES={
"benchmarks/LIA/2016.SyGuS-Comp/array.sl":
 "b1c26aaddfcbab90f2dd47b6e84faaae973be200",
"benchmarks/NIA/2018.CHI_InvGame/s10.desugared.sl":
 "f066be50786c6a41bdaf0b0e2df399c579469f3f",
}
QUERY_MS=5000
MAX_SEXPR_NODES=25000

class InvalidSource(Exception):pass

def blobhash(blob):
    return hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\x00"+blob).hexdigest()

def sexprs(raw):
    text=raw.decode("utf-8",errors="strict")
    lines=[line.split(";",1)[0] for line in text.splitlines()]
    clean="\n".join(lines)
    tokens=re.findall(r"\(|\)|[^()\s]+",clean)
    if len(tokens)>MAX_SEXPR_NODES:raise InvalidSource("TOO_MANY_ORIGINAL_TOKENS")
    stack=[[]]
    for token in tokens:
        if token=="(":
            nxt=[];stack[-1].append(nxt);stack.append(nxt)
        elif token==")":
            if len(stack)<2:raise InvalidSource("UNBALANCED_RIGHT_PAREN")
            stack.pop()
        else:stack[-1].append(token)
    if len(stack)!=1:raise InvalidSource("UNBALANCED_LEFT_PAREN")
    return stack[0]

def compile_term(n,env):
    if isinstance(n,str):
        if n in env:return env[n]
        if n=="true":return z3.BoolVal(True)
        if n=="false":return z3.BoolVal(False)
        if re.fullmatch(r"-?\d+",n):return z3.IntVal(int(n))
        raise InvalidSource("UNBOUND_SYMBOL_IN_ORIGINAL_FORMULA")
    if not isinstance(n,list) or not n:raise InvalidSource("EMPTY_FORMULA_OR_ATOM")
    name=n[0]; xs=n[1:]
    if name=="let":
        if len(xs)!=2 or not isinstance(xs[0],list):raise InvalidSource("MALFORMED_LET")
        bindings=dict(env)
        rhs={}
        for pair in xs[0]:
            if len(pair)!=2 or not isinstance(pair[0],str):raise InvalidSource("MALFORMED_LET_BINDING")
            rhs[pair[0]]=compile_term(pair[1],env)
        bindings.update(rhs)
        return compile_term(xs[1],bindings)
    args=[compile_term(x,env) for x in xs]
    if name=="and":return z3.And(*args)
    if name=="or":return z3.Or(*args)
    if name=="not" and len(args)==1:return z3.Not(args[0])
    if name=="=>" and len(args)==2:return z3.Implies(*args)
    if name=="xor" and len(args)==2:return z3.Xor(*args)
    if name=="ite" and len(args)==3:return z3.If(*args)
    if name=="=" and len(args)>=2:return z3.And(*[args[i]==args[i+1] for i in range(len(args)-1)])
    if name=="distinct" and len(args)>=2:return z3.Distinct(*args)
    if name==">=" and len(args)==2:return args[0]>=args[1]
    if name=="<=" and len(args)==2:return args[0]<=args[1]
    if name==">" and len(args)==2:return args[0]>args[1]
    if name=="<" and len(args)==2:return args[0]<args[1]
    if name=="+" and len(args)>=1:return z3.Sum(*args)
    if name=="-" and len(args)==1:return -args[0]
    if name=="-" and len(args)>=2:
        out=args[0]
        for a in args[1:]:out=out-a
        return out
    if name=="*" and len(args)>=2:
        out=args[0]
        for a in args[1:]:out=out*a
        return out
    if name=="div" and len(args)==2:return args[0]/args[1]
    if name=="mod" and len(args)==2:return args[0]%args[1]
    if name=="abs" and len(args)==1:return z3.If(args[0]>=0,args[0],-args[0])
    raise InvalidSource("UNSUPPORTED_SMTLIB_OPERATOR:"+str(name)[:40])

def extract_original(forms):
    all_defs=[x for x in forms if isinstance(x,list) and x and x[0]=="define-fun"]
    synth=[x for x in forms if isinstance(x,list) and x and x[0]=="synth-inv"]
    contract=[x for x in forms if isinstance(x,list) and x and x[0]=="inv-constraint"]
    if len(synth)!=1 or len(contract)!=1:raise InvalidSource("NOT_ONE_ORIGINAL_INV_CONSTRAINT")
    signature=synth[0]
    if len(signature)!=3:raise InvalidSource("UNSUPPORTED_SYNTH_INV_SIGNATURE")
    def ensure_vars(params):
        if not isinstance(params,list):raise InvalidSource("NONLIST_ORIGINAL_VAR_PARAMS")
        if not all(isinstance(p,list) and len(p)==2 and p[1]=="Int" and isinstance(p[0],str) for p in params):
            raise InvalidSource("NONINTEGER_ORIGINAL_STATE_TYPE")
        if len({x[0] for x in params})!=len(params):raise InvalidSource("DUPLICATE_VARIABLE")
        return [p[0] for p in params]
    names=ensure_vars(signature[2])
    if not names or len(names)>15:raise InvalidSource("STATE_ARITY_CAP")
    original_inv,pre_name,trans_name,post_name=contract[0][1:]
    if original_inv!=signature[1]:raise InvalidSource("INV_REFERENCE_MISMATCH")
    defined={x[1]:x for x in all_defs if len(x)==5}
    if not all(n in defined for n in (pre_name,trans_name,post_name)):
        raise InvalidSource("SOURCE_PRE_TRANS_POST_MISSING")
    defined_names={n:ensure_vars(defined[n][2]) for n in (pre_name,trans_name,post_name)}
    if defined_names[pre_name]!=names or defined_names[post_name]!=names:
        raise InvalidSource("PRE_POST_SOURCE_SORT_MISMATCH")
    state=[z3.Int("Q3O_now_"+x) for x in names]
    following=[z3.Int("Q3O_next_"+x) for x in names]
    if len(defined_names[trans_name])!=2*len(names):
        raise InvalidSource("TRANS_ORIGINAL_ARITY_MISMATCH")
    if defined_names[trans_name][:len(names)]!=names:
        raise InvalidSource("TRANS_SOURCE_PARAMETER_MISMATCH")
    def expand(n,values):
        formal=defined_names[n]
        env=dict(zip(formal,values))
        ast=compile_term(defined[n][4],env)
        if not z3.is_bool(ast):raise InvalidSource("ORIGINAL_RELATION_NOT_BOOL")
        return z3.simplify(ast)
    pre=expand(pre_name,state)
    trans=expand(trans_name,state+following)
    post=expand(post_name,state)
    return names,state,following,pre,trans,post

def check_vcs(candidate,vars_,next_,pre,trans,post):
    if not z3.is_bool(candidate):return {"status":"NONBOOLEAN_CANDIDATE"}
    candidate=z3.simplify(candidate)
    transfer=z3.substitute(candidate,*[(x,y) for x,y in zip(vars_,next_)])
    items=(
       ("init",z3.And(pre,z3.Not(candidate))),
       ("inductive",z3.And(candidate,trans,z3.Not(transfer))),
       ("postcondition",z3.And(candidate,z3.Not(post))),
    )
    result={}
    for key,query in items:
        s=z3.Solver();s.set(timeout=3000);s.add(query)
        try:result[key]=str(s.check())
        except Exception as exc:result[key]="ERROR_"+type(exc).__name__
    result["status"]="ALL_ORIGINAL_SYGUS_VCS_UNSAT" if all(result[k]=="unsat" for k,_ in items) else "NO_FULL_ORIGINAL_INVARIANT_CERTIFICATE"
    result["candidate_nodes"]=len(z3.z3util.get_vars(candidate))+len(list(re.findall(r"\(",candidate.sexpr())))
    result["candidate_sha256"]=hashlib.sha256(candidate.sexpr().encode()).hexdigest()
    return result

def trial(path,expected):
    raw=path.read_bytes()
    if blobhash(raw)!=expected:raise ValueError("PINNED_ORIGINAL_SYGUS_SOURCE_BLOB_CHANGED")
    names,now,next_,pre,trans,post=extract_original(sexprs(raw))
    pre_sat=z3.Solver();pre_sat.set(timeout=2000);pre_sat.add(pre)
    pre_check=str(pre_sat.check())
    rel=z3.Function("Q3O_Reach",*[z3.IntSort() for _ in names],z3.BoolSort())
    bad=z3.Function("Q3O_Bad",z3.BoolSort())
    fp=z3.Fixedpoint();fp.set(engine="spacer",timeout=QUERY_MS)
    fp.register_relation(rel,bad)
    fp.declare_var(*(now+next_))
    fp.rule(rel(*now),pre)
    fp.rule(rel(*next_),z3.And(rel(*now),trans))
    fp.rule(bad(),z3.And(rel(*now),z3.Not(post)))
    begin=time.perf_counter_ns()
    try:
        verdict=str(fp.query(bad()))
        why=fp.reason_unknown() if verdict=="unknown" else None
    except Exception as exc:
        verdict="ERROR_"+type(exc).__name__
        why=str(exc)[:220]
    duration=(time.perf_counter_ns()-begin)/1e6
    covers=[]
    if verdict=="unsat":
        try:
            cover=fp.get_cover_delta(-1,rel)
            for order in ("FORWARD","REVERSED"):
                args=now if order=="FORWARD" else list(reversed(now))
                instantiated=z3.substitute_vars(cover,*args)
                vc=check_vcs(instantiated,now,next_,pre,trans,post)
                vc["binding_order"]=order
                if vc["status"]=="ALL_ORIGINAL_SYGUS_VCS_UNSAT":
                    covers.append(vc)
        except Exception as exc:
            covers.append({"status":"COVER_EXTRACT_OR_VC_ERROR","error":f"{type(exc).__name__}: {str(exc)[:160]}"})
    return {
      "path":str(path).split("external_loopinvgen/")[-1],
      "source_git_blob":expected,
      "state_variable_count":len(names),
      "original_initial_states_sat_status":pre_check,
      "spacer_original_bad_exit_verdict":verdict,
      "spacer_unknown_reason":why,
      "spacer_elapsed_ms":round(duration,3),
      "independently_original_VC_reproved_covers":covers,
      "at_least_one_independently_proven_AST_cover":any(
            x.get("status")=="ALL_ORIGINAL_SYGUS_VCS_UNSAT" for x in covers),
      "source_goal_altered":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    lic=a.root/"LICENSE.md"
    if blobhash(lic.read_bytes())!=LICENSE_BLOB:
        raise ValueError("ORIGINAL_REPO_LICENSE_NOT_PINNED")
    out=[]
    for rel,h in SOURCES.items():
        pth=a.root/rel
        try:rec=trial(pth,h)
        except Exception as exc:
            rec={"path":rel,"source_git_blob":h,
                 "status":"SOURCE_UNSUPPORTED_OR_TRANSLATOR_ERROR",
                 "error":f"{type(exc).__name__}: {str(exc)[:210]}"}
        out.append(rec)
    result={
        "study":"Q3O_FIRST_TWO_EXTERNAL_ORIGINAL_TYPED_SYGUS_REAL_SOURCE_PROOFS",
        "repo":"SaswatPadhi/LoopInvGen","pinned_upstream_revision":SOURCE_REV,
        "pinned_license_git_blob":LICENSE_BLOB,
        "source_count":len(out),"source_groups":2,
        "spacer_original_full_safety_proven":sum(
            x.get("spacer_original_bad_exit_verdict")=="unsat" for x in out),
        "full_original_VC_backchecked_inductive_AST_seeds":sum(
            x.get("at_least_one_independently_proven_AST_cover",False) for x in out),
        "model_training_calls":0,"paid_frontier_calls":0,
        "published_benchmark_answer_labels_used":False,
        "source_contents_redistributed":False,
        "q3f_sealed_benchmark_sources_read":False,
        "all_q1_q7":"OPEN",
        "records":out
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print("Q3O_REAL_EXTERNAL_TWO",[(x.get("path"),x.get("spacer_original_bad_exit_verdict"),x.get("at_least_one_independently_proven_AST_cover"),x.get("error")) for x in out])
    print("PROVEN_DIRECT",result["spacer_original_full_safety_proven"],"PROVEN_AST",result["full_original_VC_backchecked_inductive_AST_seeds"])
    print("GLOBAL",result["all_q1_q7"])

if __name__=="__main__":main()
