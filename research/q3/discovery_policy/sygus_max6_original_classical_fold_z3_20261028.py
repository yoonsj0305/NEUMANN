#!/usr/bin/env python3
"""Postfirst original max6 strong classical specialist typed fold formal proof.
Not a learned NEUMANN model: a deliberately cheap matched-grammar classical
baseline to decide whether learning that structure is a waste of computation.
"""
import json,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_official_diverse12_independent_z3_postfirst_20261028 import parameter_signature,check_z3

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
PATH="lib/General_Track/from_2018/max6.sl"
SOURCE_SHA="04c4f22a8ccfb85dfdfe05f9aedfd710985578f8a5cb195da239176aab43331c"
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("official_max6_specialist")

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    b=(ROOT/PATH).read_bytes()
    assert sha256(b)==SOURCE_SHA
    orig=b.decode("utf8")
    forms=[(get_cmd(f[2]),f[2]) for f in top_level_forms(orig)]
    assert [c for c,_ in forms].count("constraint")==7
    synth=[f for c,f in forms if c=="synth-fun"]
    assert len(synth)==1 and re.match(r"^\(\s*synth-fun\s+max6\s+",synth[0])
    sig=parameter_signature(synth[0],"synth-fun","max6")
    assert len(sig)==6 and all(sort=="Int" for var,sort in sig)
    assert "(ite StartBool Start Start)" in synth[0]
    assert "(>= Start Start)" in synth[0]
    names=[x for x,t in sig]
    for name in names:
        assert re.search(r"(?<![A-Za-z0-9_])"+re.escape(name)+r"(?![A-Za-z0-9_])",synth[0])
    start=time.process_time()
    accum=names[0]
    for x in names[1:]:
        accum="(ite (>= "+accum+" "+x+") "+accum+" "+x+")"
    header="(define-fun max6 ("+" ".join("("+n+" Int)" for n in names)+") Int "+accum+")"
    (OUT).mkdir(exist_ok=True)
    (OUT/"SPECIALIST_CLASSICAL_MAX6_EXECUTABLE.smt2").write_text(header+"\n")
    built_cpu=time.process_time()-start
    constraints=[]
    for command,form in forms:
        if command=="constraint":
            m=re.fullmatch(r"\(\s*constraint\s+(.+)\s*\)",form,re.S)
            assert m
            constraints.append(m.group(1))
    assert len(constraints)==7
    source_prefix=["(set-logic ALL)"]
    source_prefix+=[re.sub(r"^\(\s*declare-var\b","(declare-const",form,count=1)
                     for command,form in forms if command=="declare-var"]
    source_prefix.append(header)
    prefix="\n".join(source_prefix)+"\n"
    results=[]
    for i in range(8):
        body=constraints[i] if i<7 else "(and "+" ".join(constraints)+")"
        script=prefix+"(assert (not "+body+"))\n"
        name="original_constraint_"+str(i+1) if i<7 else "original_full_conjunction"
        (OUT/(name+".smt2")).write_text(script)
        try:
            r=check_z3(script)
            r["status"]="PASS_FORMAL_UNSAT" if r["z3_answer"]=="unsat" else "HOLD_OR_FALSIFIED"
        except Exception as e:
            r={"status":"HOLD_EXECUTOR_OR_PARSE","error":type(e).__name__+":"+str(e)[:230]}
        r["name"]=name
        results.append(r)
        print("MAX6_CLASSIC_FORMAL",name,r["status"],flush=True)
    passed=all(r["status"]=="PASS_FORMAL_UNSAT" for r in results)
    report={
        "task":"POSTFIRST_CHEAP_CLASSICAL_STRUCTURAL_FOLD",
        "original_upstream_sha":PIN,"original_filename":PATH,
        "original_exact_source_sha256":SOURCE_SHA,
        "original_typed_function_arity":len(sig),
        "specialist_program_actual_bytes":len(header.encode()),
        "specialist_program_sha256":sha256((header+"\n").encode()),
        "specialist_program":header,
        "grammar_membership":"CHECKED_ALLOWED_TERMINALS_PLUS_ITE_AND_GE",
        "specialist_construction_process_cpu_seconds":round(built_cpu,7),
        "z3_version":z3.get_version_string(),
        "original_constraints":7,
        "independent_semantic_test_obligations":8,
        "verdict":"CLASSICAL_SPECIALIST_FULL_ORIGINAL_SEMANTIC_PASS" if passed else "HOLD",
        "strong_native_cvc5_142_previous":"C_CPU12_BUDGET_HOLD",
        "neural_ownweight_trained":False,
        "global_Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN",
        "obligations":results}
    p=OUT/"MAX6_ORIGINAL_GRAMMAR_SPECIALIST_CLASSICAL_Z3_FULL.json"
    p.write_text(json.dumps(report,indent=2,sort_keys=True))
    print("RESULT_SHA256",sha256(p.read_bytes()))
    print("VERDICT",report["verdict"])
if __name__=="__main__":main()
