#!/usr/bin/env python3
"""Opened SGI development: deterministic input-only bit-guard witness, no target gold.
Refutes bounded-candidate-unanimity => version-space-uniqueness conflation.
This DOES NOT show ownweight learning or unseen-domain transfer.
"""
import hashlib,json,os,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_active_oracle_v1 import (top_level_forms,get_cmd,sha256,source_without_forms,
    proposal_function,helpers_for,io_form)
UPSTREAM="e7ae840e5546e9243ff94afb1a29064fc050011c"
FIRST_SHA="a2713cee7e4a54506501927c07ff65f78d4ad110e4c9568892d937f3a0aa8185"
SOURCE=pathlib.Path("upstream")
FIRST=pathlib.Path("previous_first")
PACK=pathlib.Path("bitguard_source_only.json")
OUT=pathlib.Path("bitguard_receipt")
IDX=(1,5,8,9,10,11)
ONE="#x0000000000000001"

def get_inputs_and_source():
    assert subprocess.check_output(["git","-C",str(SOURCE),"rev-parse","HEAD"],text=True).strip()==UPSTREAM
    firstbytes=(FIRST/"FIRST_PROPOSALS_AND_QUERY_DECISIONS_UNGRADED.json").read_bytes()
    assert sha256(firstbytes)==FIRST_SHA
    frozen=json.loads(firstbytes)
    rows=[]
    for i in IDX:
        r=frozen["rows"][i]
        assert r["index"]==i and r["query_decision"]=="SKIP_UNANIMOUS_THREE"
        raw=(SOURCE/r["path"]).read_bytes()
        assert sha256(raw)==r["original_sha256"]
        original=raw.decode()
        fs=top_level_forms(original)
        cs=[f for f in fs if get_cmd(f[2])=="constraint"]
        assert len(cs)==r["n_constraints"]
        pairs=[io_form(f[2]) for f in cs]
        assert r["probe_input"]==pairs[-2][0]
        assert r["future_input"]==pairs[-1][0]
        assert sha256(cs[-2][2].encode())==r["probe_constraint_sha256"]
        assert sha256(cs[-1][2].encode())==r["future_constraint_sha256"]
        src=source_without_forms(original,cs[-2:])
        assert sha256(src.encode())==r["source_only_sha256"]
        rows.append({"index":i,"name":r["path"],"source_sha256":r["source_only_sha256"],
             "source_only_text":src,
             "source_input_only":[x for x,_ in pairs[:-2]],
             "probe_input":r["probe_input"],"future_input":r["future_input"],
             "default_stdout_sha256":r["proposals"][0]["stdout_sha256"]})
    PACK.write_text(json.dumps({"upstream":UPSTREAM,"sealed_first":FIRST_SHA,"rows":rows},indent=2))
    print("SOURCE_PACK",[(r["index"],len(r["source_input_only"])) for r in rows],flush=True)

def greedy_bits(sources,t):
    unmatched=set(sources)
    selected=[]
    while unmatched:
        remaining=[j for j in range(64) if j not in selected]
        scores=[(sum(((x>>j)&1)!=((t>>j)&1) for x in unmatched),j) for j in remaining]
        score,j=max(scores,key=lambda z:(z[0],-z[1]))
        if not score:raise ValueError("TARGET_MATCHES_SOURCE_INPUT_OR_UNCOVERABLE")
        selected.append(j)
        unmatched={x for x in unmatched if ((x>>j)&1)==((t>>j)&1)}
    return selected

def shift_term(k):
    expression="x"
    for _ in range(k//16):expression=f"(shesh {expression})"
    k=k%16
    for _ in range(k//4):expression=f"(arba {expression})"
    for _ in range(k%4):expression=f"(ehad {expression})"
    return expression

def guard_expr(bits,t):
    exprs=[]
    for j in bits:
        part=f"(bvand {shift_term(j)} {ONE})"
        if ((t>>j)&1)==0:part=f"(bvand (bvnot {part}) {ONE})"
        exprs.append(part)
    if not exprs:return ONE
    expr=exprs[0]
    for part in exprs[1:]:expr=f"(bvand {expr} {part})"
    return expr

def mask_ref(bits,x,t):
    return int(all(((x>>j)&1)==((t>>j)&1) for j in bits))

def original_body(definefun):
    m=re.match(r'^\(\s*define-fun\s+f\s+\(\s*\(\s*x\s+\(\s*_\s+BitVec\s+64\s*\)\s*\)\s*\)\s*\(\s*_\s+BitVec\s+64\s*\)\s+',definefun,re.S)
    if m is None:raise ValueError("CVC5_CANDIDATE_NON_STANDARD_SIGNATURE")
    assert definefun.rstrip().endswith(")")
    return definefun[m.end():-1].strip()

def independent_z3_certificate(src,f0,f1,target,guard,bits,src_inputs,t):
    import z3
    def check(script):
        s=z3.Solver();s.set(timeout=10000)
        s.add(*z3.parse_smt2_string(script))
        return str(s.check())
    helpers=helpers_for(src)
    cs=[p[2] for p in top_level_forms(src) if get_cmd(p[2])=="constraint"]
    def body(form):
        m=re.fullmatch(r"\(\s*constraint\s+(.*)\s*\)",form,re.S)
        if not m:raise ValueError("NONSTANDARD_SOURCE_CONSTRAINT")
        return m.group(1)
    sourceexpr="(and "+" ".join(body(c) for c in cs)+")"
    src0=check(helpers+"\n"+f0+"\n(assert (not "+sourceexpr+"))")
    src1=check(helpers+"\n"+f1+"\n(assert (not "+sourceexpr+"))")
    f0name=re.sub(r'^\(\s*define-fun\s+f(?=\s)',"(define-fun f0",f0,count=1)
    f1name=re.sub(r'^\(\s*define-fun\s+f(?=\s)',"(define-fun f1",f1,count=1)
    difference=check(helpers+"\n"+f0name+"\n"+f1name+
                     f"\n(assert (= (f0 {target}) (f1 {target})))")
    # This checks a **single point** without any original gold target label.
    return {"f0_source_negation":src0,"f1_source_negation":src1,
            "f0_equals_f1_at_target":difference}

def actual():
    import z3
    p=FIRST/"FIRST_PROPOSALS_AND_QUERY_DECISIONS_UNGRADED.json"
    assert sha256(p.read_bytes())==FIRST_SHA
    pack=json.loads(PACK.read_text())
    assert pack["upstream"]==UPSTREAM and pack["sealed_first"]==FIRST_SHA
    OUT.mkdir(exist_ok=True)
    r0=[]
    for r in pack["rows"]:
        i=r["index"]
        a=(FIRST/f"{i:02d}_0.stdout").read_bytes()
        assert sha256(a)==r["default_stdout_sha256"]
        firstprogram=proposal_function(a.decode(errors="replace"))
        record={"index":i,"name":r["name"],"source_sha256":r["source_sha256"],
                "default_stdout_sha256":r["default_stdout_sha256"],"targets":[]}
        source_inputs=[int(x,16) for x in r["source_input_only"]]
        for key in ("probe_input","future_input"):
            t0=time.process_time()
            target=r[key]
            entry={"input_type":key,"target_input":target}
            try:
                bits=greedy_bits(source_inputs,int(target,16))
                assert all(mask_ref(bits,x,int(target,16))==0 for x in source_inputs)
                assert mask_ref(bits,int(target,16),int(target,16))==1
                guard=guard_expr(bits,int(target,16))
                body=original_body(firstprogram)
                # Every token, constant and helper is already in upstream author grammar.
                newbody=f"(im {guard} (bvnot {body}) {body})"
                rival=f"(define-fun f ((x (_ BitVec 64))) (_ BitVec 64) {newbody})"
                zcheck=independent_z3_certificate(r["source_only_text"],firstprogram,
                                rival,target,guard,bits,source_inputs,int(target,16))
                entry.update({"bit_positions":bits,"bit_count":len(bits),
                  "guard_chars":len(guard),"new_candidate_chars":len(rival),
                  "first_candidate_sha256":sha256(firstprogram.encode()),
                  "constructed_candidate_sha256":sha256(rival.encode()),
                  "Z3_checks":zcheck})
                if zcheck=={"f0_source_negation":"unsat","f1_source_negation":"unsat",
                            "f0_equals_f1_at_target":"unsat"}:
                    entry["status"]="VERIFIED_SOURCE_PRESERVING_DIFFERENT_FUNCTION"
                else:entry["status"]="HOLD_INDEPENDENT_Z3_UNCERTAIN_OR_FAILED"
            except Exception as e:
                entry["status"]="HOLD_CONSTRUCTION_OR_VERIFIER_ERROR"
                entry["reason"]=type(e).__name__+":"+str(e)[:240]
            entry["process_cpu_s"]=round(time.process_time()-t0,6)
            record["targets"].append(entry)
            print("BITGUARD",i,key,entry["status"],entry.get("bit_count"),entry["process_cpu_s"],flush=True)
        r0.append(record)
    result={"original_G0_status":"OPENED_DEVELOPMENT_NOT_PROSPECTIVE",
      "strong_native_cvc5_new_weight_runs":0,"neural_training":0,
      "original_probe_future_labels_used":False,
      "original_first_hash":FIRST_SHA,"upstream_commit":UPSTREAM,
      "global_Q1_Q7":"OPEN","G1":"HOLD","rows":r0}
    file=OUT/"POSTFIRST_CONSTRUCTIVE_64BIT_BITGUARD_WITNESS.json"
    file.write_text(json.dumps(result,sort_keys=True,indent=2))
    print("RESULT_SHA256",sha256(file.read_bytes()),flush=True)
    print("COUNTS",json.dumps({s:sum(t["status"]==s for r in r0 for t in r["targets"])
                     for s in sorted({t["status"] for r in r0 for t in r["targets"]})}))
if __name__=="__main__":
    if len(sys.argv)!=2:raise ValueError("phase")
    if sys.argv[1]=="prepare":get_inputs_and_source()
    elif sys.argv[1]=="prove":actual()
    else:raise ValueError("unknown phase")
