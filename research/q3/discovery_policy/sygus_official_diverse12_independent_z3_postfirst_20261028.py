#!/usr/bin/env python3
"""POST-FIRST independent original SyGuS12 native-program semantic checker.

For standard universal (constraint ...) check no violating interpretation exists.
For SyGuS (synth-inv I) (inv-constraint I pre trans post), verify ALL three
full inductive VCs, not just a returned define-fun: pre→I, I∧trans→I', I→post.
Native first original/weights/source SHA unchanged; no re-synthesis at grade.
"""
import collections,hashlib,json,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_official_diverse_new12_strong_c_first_20261028 import PIN,LOCKED

FIRST_SHA="bde9d71dc8e9120a4178e29cb1e758014c2f7effcade3ccec1e75fdc1c1505ba"
ROOT=pathlib.Path("official_repo")
FIRST=pathlib.Path("official_diverse12_sealed_first")
OUT=pathlib.Path("official_diverse12_independent_z3_grade")

def form_name(form,cmd):
    m=re.match(r"^\(\s*"+re.escape(cmd)+r"\s+([^\s()]+)",form)
    if not m:raise ValueError("MISSING_"+cmd+"_NAME")
    return m.group(1)

def unwrap_native(raw):
    text=raw.strip()
    for i in range(4):
        forms=top_level_forms(text)
        if forms and all(get_cmd(f[2])=="define-fun" for f in forms):
            return [f[2] for f in forms]
        if len(forms)==1 and text.startswith("(") and get_cmd(forms[0][2]) is None:
            text=forms[0][2][1:-1].strip()
            continue
        raise ValueError("NATIVE_NOT_A_PURE_DEFINE_FUN_LIST")
    raise ValueError("NATIVE_OUTPUT_NESTED_TOO_DEEP")

def parameter_signature(definition,command,name):
    h=re.match(r"^\(\s*"+re.escape(command)+r"\s+"+re.escape(name)+r"\s+",definition)
    if h is None:raise ValueError("HEADER_MISMATCH_"+command)
    remaining=definition[h.end():]
    # The surrounding define-fun closes AFTER its body. Only extract the FIRST
    # balanced parameter group; parsing the remainder as standalone SMT-LIB
    # would see the outer parenthesis and raise extra-closing.
    if not remaining.startswith("("):raise ValueError("MISSING_PARAM_GROUP")
    depth=0
    end=None
    for k,c in enumerate(remaining):
        if c=="(":depth+=1
        elif c==")":
            depth-=1
            if depth==0:
                end=k+1
                break
    if end is None:raise ValueError("PARAM_GROUP_NOT_CLOSED")
    parameter_group=remaining[:end]
    params=top_level_forms(parameter_group[1:-1])
    out=[]
    for p in params:
        m=re.fullmatch(r"\(\s*([^\s()]+)\s+(.+?)\s*\)",p[2],re.S)
        if m is None:raise ValueError("INVALID_TYPED_BINDER")
        out.append((m.group(1),re.sub(r"\s+"," ",m.group(2)).strip()))
    return out

def symbol_call(name,identifiers):
    return "("+name+(" "+" ".join(identifiers) if identifiers else "")+")"

def source_prefix(terms):
    parts=["(set-logic ALL)"]
    for cmd,form in terms:
        if cmd=="define-fun":parts.append(form)
        elif cmd=="declare-var":
            parts.append(re.sub(r"^\(\s*declare-var\b","(declare-const",form,count=1))
    return parts

def check_z3(script):
    import z3
    start=time.monotonic()
    solver=z3.Solver()
    solver.set(timeout=10000)
    solver.add(*z3.parse_smt2_string(script))
    answer=str(solver.check())
    return {"z3_answer":answer,"proof_counterexample_unsat":answer=="unsat",
            "independent_wall_seconds":round(time.monotonic()-start,6),
            "formal_script_sha256":sha256(script.encode())}

def independent_grade(row,body,stdout):
    terms=[(get_cmd(f[2]),f[2]) for f in top_level_forms(body)]
    defs=unwrap_native(stdout)
    synths=[form for cmd,form in terms if cmd in ("synth-fun","synth-inv")]
    synth_names=[form_name(f,get_cmd(f)) for f in synths]
    def_names=[form_name(x,"define-fun") for x in defs]
    if len(def_names)!=len(synths) or set(def_names)!=set(synth_names):
        raise ValueError("RETURNED_FUNCTION_NAME_OR_COUNT_MISMATCH")
    # Reject function renaming, binder type or arity mismatches via original source.
    orig_sig={form_name(f,get_cmd(f)):parameter_signature(f,get_cmd(f),form_name(f,get_cmd(f)))
              for f in synths}
    for d in defs:
        key=form_name(d,"define-fun")
        actual=parameter_signature(d,"define-fun",key)
        if [s for _,s in orig_sig[key]]!=[s for _,s in actual]:
            raise ValueError("CANDIDATE_SORT_ARITY_MISMATCH_"+key)
    prefixes=source_prefix(terms)+defs
    cons=[f for cmd,f in terms if cmd=="constraint"]
    invcon=[f for cmd,f in terms if cmd=="inv-constraint"]
    tests=[]
    if cons and not invcon:
        for k,formula in enumerate(cons):
            m=re.fullmatch(r"\(\s*constraint\s+(.+)\s*\)",formula,re.S)
            if m is None:raise ValueError("SOURCE_CONSTRAINT_PARSE")
            script="\n".join(prefixes)+"\n(assert (not "+m.group(1)+"))\n"
            test=check_z3(script)
            test["obligation"]="ordinary_original_constraint_"+str(k+1)
            tests.append(test)
    elif invcon and not cons and len(invcon)==1 and len(synths)==1 and get_cmd(synths[0])=="synth-inv":
        invname=synth_names[0]
        names=re.findall(r"(?<=\s)[^\s()]+",invcon[0])
        # Instead of fragile token extraction match entire original inv-constraint form.
        m=re.fullmatch(r"\(\s*inv-constraint\s+([^\s()]+)\s+([^\s()]+)\s+([^\s()]+)\s+([^\s()]+)\s*\)",invcon[0])
        if m is None or m.group(1)!=invname:raise ValueError("INVALID_ORIGINAL_INV_CONSTRAINT")
        _,pre,trans,post=m.groups()
        original_helpers={form_name(f,"define-fun"):f for cmd,f in terms if cmd=="define-fun"}
        if not all(x in original_helpers for x in (pre,trans,post)):
            raise ValueError("INV_CONSTRAINT_REFERENCES_MISSING_HELPER")
        sig=orig_sig[invname]
        n=len(sig)
        if n<1:raise ValueError("EMPTY_INVARIANT_SIGNATURE")
        pre_sig=parameter_signature(original_helpers[pre],"define-fun",pre)
        trans_sig=parameter_signature(original_helpers[trans],"define-fun",trans)
        post_sig=parameter_signature(original_helpers[post],"define-fun",post)
        sorts=[t for _,t in sig]
        if [t for _,t in pre_sig]!=sorts or [t for _,t in trans_sig]!=sorts+sorts or [t for _,t in post_sig]!=sorts:
            raise ValueError("STANDARD_Sygus_INV_HELPER_SORT_ARITY_MISMATCH")
        s=["__n1vc_s_"+str(i) for i in range(n)]
        sp=["__n1vc_t_"+str(i) for i in range(n)]
        declarations=["(declare-const "+k+" "+t+")" for k,t in
                      zip(s+sp,sorts+sorts)]
        pfx="\n".join(prefixes+declarations)+"\n"
        violations=(
            "(and "+symbol_call(pre,s)+" (not "+symbol_call(invname,s)+"))",
            "(and "+symbol_call(invname,s)+" "+
                     symbol_call(trans,s+sp)+" (not "+symbol_call(invname,sp)+"))",
            "(and "+symbol_call(invname,s)+" (not "+symbol_call(post,s)+"))",
        )
        for v,kind in zip(violations,("INIT_IMPLIES_INVARIANT",
                                       "INDUCTIVE_CONSECUTION",
                                       "INVARIANT_IMPLIES_POST")):
            test=check_z3(pfx+"(assert "+v+")\n")
            test["obligation"]=kind
            tests.append(test)
    else:
        raise ValueError("UNSUPPORTED_MIXED_OR_ABSENT_ORIGINAL_CONSTRAINT_KIND")
    assert tests,"NO_ORIGINAL_OBLIGATIONS_CHECKED"
    passed=all(x["proof_counterexample_unsat"] for x in tests)
    return {"grade":"VERIFIED_FULL_ORIGINAL_SEMANTIC_CONSTRAINTS" if passed else
                     "HOLD_COUNTEREXAMPLE_OR_UNKNOWN",
            "original_formal_proof_obligations":tests,
            "source_original_constraint_count":len(cons),
            "source_original_inv_constraint_count":len(invcon),
            "typed_native_return_names":def_names,
            "native_cvc5_grammar_membership_independently_proved":False}

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    first_bytes=(FIRST/"FOUR_FAMILY_NEW12_OFFICIAL_CVC5_142_FIRST.json").read_bytes()
    assert sha256(first_bytes)==FIRST_SHA
    first=json.loads(first_bytes)
    assert len(first["rows"])==12
    assert [r["original_filename"] for r in first["rows"]]==LOCKED
    OUT.mkdir(exist_ok=True)
    graded=[]
    for row in first["rows"]:
        index=row["index"];path=row["original_filename"]
        record={"index":index,"path":path,"source_sha256":row["source_file_sha256"],
                "original_native_status":row["status"],
                "postfirst_semantic_grade":"HOLD"}
        original=(ROOT/path).read_bytes()
        assert sha256(original)==row["source_file_sha256"]
        if row["status"]=="C_NATIVE_BUDGET_HOLD":
            record["postfirst_semantic_grade"]="ORIGINAL_C_BUDGET_HOLD_UNCHANGED"
        elif row["status"]=="C_NATIVE_PROGRAM_RETURNED_UNVERIFIED":
            frozen=(FIRST/("%02d.native.stdout"%index)).read_bytes()
            assert sha256(frozen)==row["native_cost"]["stdout_sha256"]
            try:
                result=independent_grade(row,original.decode("utf8"),frozen.decode("utf8","replace"))
                record.update(result)
                record["postfirst_semantic_grade"]=result["grade"]
            except Exception as e:
                record["postfirst_semantic_grade"]="HOLD_Z3_PARSER_OR_UNSUPPORTED"
                record["checker_error"]=type(e).__name__+":"+str(e)[:200]
        else:record["postfirst_semantic_grade"]="HOLD_ORIGINAL_NATIVE_UNGRADED"
        graded.append(record)
        print("NEW12_INDEPENDENT",index,record["postfirst_semantic_grade"],flush=True)
    out={
      "intent":"Post-FIRST independent semantics for all 12 official original tasks without re-synthesis",
      "original_source_pin":PIN,"first_json_sha256":FIRST_SHA,
      "actual_external_originals":12,"z3_version":z3.get_version_string(),
      "ordinary_universal_contra_check":"all original source constraints",
      "invariant_check":"SyGuS pre-I/I-trans-Iprime/I-post 3 VCs",
      "native_program_grammar_membership_independently_proved":False,
      "summary":dict(collections.Counter(x["postfirst_semantic_grade"] for x in graded)),
      "not_ownweight_neural":True,"G1":"HOLD","G2":"NOT_RUN","global_Q1_Q7":"OPEN",
      "rows":graded}
    p=OUT/"FOUR_FAMILY_ORIGINAL12_CLASSICAL_POSTFIRST_Z3_FULL_PROOF.json"
    p.write_text(json.dumps(out,indent=2,sort_keys=True))
    print("POSTFIRST_Z3_SHA256",sha256(p.read_bytes()),flush=True)
    print("POSTFIRST_SUMMARY",json.dumps(out["summary"],sort_keys=True),flush=True)
if __name__=="__main__":main()
