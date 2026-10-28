#!/usr/bin/env python3
"""POST-CONTENT two source-grammar admissible PBE-SLIA exact programs disagree.

Original *published* three examples are the only supervised target rights.
They do NOT imply an ideal function output for any unseen string.
Independent Z3 4.13.3 full supplied equations, plus concrete witness check.
"""
import json,pathlib,re,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
PATH="lib/PBE_SLIA_Track/euphony/get-first-word.sl"
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("external_pbe_source_nonidentifiability")
P1='(str.substr _arg_0 0 (str.indexof _arg_0 " " 0))'
P2='(ite (str.suffixof " " _arg_0) _arg_0 (str.substr _arg_0 0 (str.indexof _arg_0 " " 0)))'
WITNESS="hello "

def prove(script,name):
    import z3
    smt=OUT/(name+".smt2")
    smt.write_text(script+"(check-sat)\n")
    solver=z3.Solver();solver.set(timeout=10000)
    solver.add(*z3.parse_smt2_string(script))
    ans=str(solver.check())
    return {"obligation":name,"answer":ans,"input_sha256":sha256(script.encode())}

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    raw=(ROOT/PATH).read_bytes()
    forms=[(get_cmd(f[2]),f[2]) for f in top_level_forms(raw.decode())]
    original_synth=[f for c,f in forms if c=="synth-fun"]
    cs=[f for c,f in forms if c=="constraint"]
    assert len(original_synth)==1 and len(cs)==3
    assert original_synth[0].startswith("(synth-fun f ((_arg_0 String)) String")
    gram=original_synth[0]
    for op in ['(str.substr ntString ntInt ntInt)','(str.indexof ntString ntString ntInt)',
               '(str.suffixof ntString ntString)','(ite ntBool ntString ntString)',
               '_arg_0','" "','1 0 -1']:
        assert op in gram,("OP_NOT_IN_ORIGINAL_GRAMMAR",op)
    assert '(constraint (= (f "The quick brown fox.") "The"))' in cs
    assert '(constraint (= (f "quick brown fox.") "quick"))' in cs
    assert '(constraint (= (f "fox") ""))' in cs
    OUT.mkdir(exist_ok=True)
    def bound(name,body):
        return "(define-fun "+name+" ((_arg_0 String)) String "+body+")"
    code1=bound("f",P1)
    code2=bound("f",P2)
    (OUT/"EXACT_GRAMMAR_CANDIDATE_P1.smt2").write_text(code1+"\n")
    (OUT/"EXACT_GRAMMAR_CANDIDATE_P2.smt2").write_text(code2+"\n")
    checks=[]
    for name,code in (("P1_ALL_THREE_ORIGINAL_CLAUSES",code1),
                      ("P2_ALL_THREE_ORIGINAL_CLAUSES",code2)):
        conjuncts=[re.fullmatch(r"\(\s*constraint\s+(.+)\s*\)",c,re.S).group(1) for c in cs]
        script="(set-logic ALL)\n"+code+"\n(assert (not (and "+" ".join(conjuncts)+")))\n"
        result=prove(script,name)
        result["expected"]="unsat"
        result["pass"]=result["answer"]=="unsat"
        checks.append(result)
    witness=("(set-logic ALL)\n"+bound("f1",P1)+"\n"+bound("f2",P2)+"\n"
             '(assert (= (f1 "hello ") "hello"))\n'
             '(assert (= (f2 "hello ") "hello "))\n'
             '(assert (not (= (f1 "hello ") (f2 "hello "))))\n')
    result=prove(witness,"WITNESS_TWO_DIFFERENT_OUTPUTS")
    result.update(expected="sat",pass_=result["answer"]=="sat")
    result["pass"]=result.pop("pass_")
    checks.append(result)
    report={
       "research":"ORIGINAL_EXTERNAL_PBE_STRING_MULTIPLE_UNIQUE_SEMANTIC_SOLUTIONS",
       "original_repo_pin":PIN,"original_path":PATH,"original_source_sha256":sha256(raw),
       "original_source_constraints":3,"original_synth_fun_grammar_checked_operations":True,
       "P1_source_AST":P1,"P2_source_AST":P2,
       "new_input_not_in_source":"hello ",
       "P1_output_at_new_input":"hello","P2_output_at_new_input":"hello ",
       "original_three_given_examples_fully_verified_both":all(x["pass"] for x in checks),
       "original_implies_unique_output_on_new_string":False if all(x["pass"] for x in checks) else "NOT_PROVED",
       "original_provides_callable_arbitrary_target_oracle":False,
       "all_checks":checks,
       "result":"FORMAL_TWO_DISTINCT_GRAMMAR_VALID_SAME_ORIGINAL_EXAMPLES" if all(x["pass"] for x in checks) else "HOLD",
       "post_content_hypothesis":True,"ownweight_learning":False,
       "G1":"HOLD","G2":"NOT_RUN","global_Q1_Q7":"OPEN"}
    p=OUT/"EXTERNAL_STRING_PBE_FULL_SOURCE_NONIDENTIFIABILITY.json"
    p.write_text(json.dumps(report,sort_keys=True,indent=2))
    print("PBE_MULTI_SOLUTION",report["result"],[(x["obligation"],x["answer"]) for x in checks])
    print("PBE_REPORT_SHA256",sha256(p.read_bytes()))
if __name__=="__main__":main()
