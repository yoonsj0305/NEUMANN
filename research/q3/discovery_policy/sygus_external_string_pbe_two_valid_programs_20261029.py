#!/usr/bin/env python3
"""Post-content, preregistered external String PBE: TWO DIFFERENT full-source
program solutions. Exact authored source grammar and three examples, two SMT
backends Z3 4.13.3/CVC5 1.4.2, new input not given a target label oracle.
"""
import hashlib,json,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
PATH="lib/PBE_SLIA_Track/euphony/get-first-word.sl"
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("external_string_spec_ambiguity")
INPUT='"hello "'
P1='(str.substr _arg_0 0 (str.indexof _arg_0 " " 0))'
P2='(ite (str.suffixof " " _arg_0) _arg_0 (str.substr _arg_0 0 (str.indexof _arg_0 " " 0)))'
EXPECTED=(("The quick brown fox.","The"),("quick brown fox.","quick"),("fox",""))

def exact_source():
    data=(ROOT/PATH).read_bytes()
    fs=[(get_cmd(p[2]),p[2]) for p in top_level_forms(data.decode("utf8"))]
    synth=[f for c,f in fs if c=="synth-fun"]
    terms=[f for c,f in fs if c=="constraint"]
    assert len(synth)==1 and len(terms)==3
    assert re.search(r"\(\s*synth-fun\s+f\s+\(\(_arg_0\s+String\)\)\s+String",synth[0])
    # A finite explicit derivation in the author-provided grammar.
    required=(
        "_arg_0",'" "',"(str.substr ntString ntInt ntInt)",
        "(str.indexof ntString ntString ntInt)","(str.suffixof ntString ntString)",
        "(ite ntBool ntString ntString)"
    )
    assert all(t in synth[0] for t in required), "ORIGINAL_GRAMMAR_MISSING_PRODUCTION"
    assert re.search(r"\b1\s+0\s+-1\b",synth[0])
    for c,(x,y) in zip(terms,EXPECTED):
        assert c.strip()==f'(constraint (= (f "{x}") "{y}"))'
    return data,terms

def code(name,expr):
    return f'(define-fun {name} ((_arg_0 String)) String {expr})'

def check_z3(source):
    import z3
    t=time.monotonic()
    solver=z3.Solver();solver.set(timeout=12000)
    solver.add(*z3.parse_smt2_string(source))
    value=str(solver.check())
    return {"backend":"Z3 "+z3.get_version_string(),
            "result":value,"seconds":round(time.monotonic()-t,6)}

def check_cvc5(source):
    start=time.monotonic()
    r=subprocess.run(["cvc5","--lang=smt2","-"],input=source+"\n(check-sat)\n",
                     capture_output=True,text=True,timeout=15,errors="replace")
    answer=[s.strip() for s in r.stdout.splitlines() if s.strip()]
    return {"backend":subprocess.check_output(["cvc5","--version"],text=True).splitlines()[0],
            "result":answer[-1] if r.returncode==0 and answer else "HOLD",
            "exit":r.returncode,"stderr":r.stderr[-220:],
            "seconds":round(time.monotonic()-start,6)}

def main():
    assert subprocess.check_output(
        ["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    original,clauses=exact_source()
    assert subprocess.check_output(["cvc5","--version"],text=True).startswith("cvc5 1.4.2 ")
    OUT.mkdir(exist_ok=True)
    all_defs=[code("p1",P1),code("p2",P2)]
    scripts={}
    # Original exact authored constraints with syntax-preserving function rename.
    for fn in ("p1","p2"):
        named=[text.replace("(f ",f"({fn} ") for text in clauses]
        terms=[re.fullmatch(r"\(\s*constraint\s+(.+)\s*\)",text,re.S).group(1)
               for text in named]
        query="\n".join(["(set-logic ALL)",*all_defs,
                        "(assert (not (and "+" ".join(terms)+")))" ])
        scripts[fn+"_all_authored_constraints"]=(query,"unsat")
    # Author never gave "hello " => target output. These two programs differ.
    witness="\n".join([
        "(set-logic ALL)",*all_defs,
        '(assert (= (p1 "hello ") "hello"))',
        '(assert (= (p2 "hello ") "hello "))',
        '(assert (not (= (p1 "hello ") (p2 "hello "))))',
    ])
    scripts["previously_unlabeled_different_output"]=(witness,"sat")
    results=[]
    for name,(script,expected) in scripts.items():
        p=OUT/(name+".smt2");p.write_text(script+"\n(check-sat)\n")
        # For Z3, check-sat is not needed for parse_smt2_string.
        z=check_z3(script);c=check_cvc5(script)
        status="FORMALLY_CONFIRMED" if z["result"]==c["result"]==expected else "HOLD"
        results.append({"obligation":name,"expected":expected,"z3":z,"cvc5":c,
                        "result":status,"SMTLIB_full_sha256":sha256(p.read_bytes())})
        print("EXTERNAL_SLIA_TWO_PROGRAM_PROOF",name,z["result"],c["result"],status,flush=True)
    passed=all(x["result"]=="FORMALLY_CONFIRMED" for x in results)
    record={
       "original_source_git":PIN,
       "original_file":PATH,"original_sha256":sha256(original),
       "original_explicit_examples_count":len(clauses),
       "original_synth_grammar_token_membership":"EXPLICIT_DERIVATION_FOR_P1_P2_CHECKED",
       "two_source_accepted_programs_sha":[sha256(x.encode()) for x in all_defs],
       "two_programs":[{"name":"p1","expr":P1},{"name":"p2","expr":P2}],
       "unlabelled_new_input":"hello ",
       "not_an_external_target_oracle":True,
       "question":"Are original finite PBE constraints sufficient for unique all-input semantics?",
       "verdict":"NO_NONIDENTIFIABLE_TWO_FORMAL_PROGRAMS" if passed else "HOLD_PROOF_FAILED",
       "unbounded_strings":"Yes, SMT String / SLIA",
       "does_not_prove_human_intent":"True",
       "first_native_cvc5_sygus_parser":"UNSUPPORTED_NOT_SYNTHESIS_FAILURE",
       "original_problem_previously_opened_dev":True,
       "global_Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN",
       "obligations":results}
    f=OUT/"G1_EXTERNAL_STRING_PBE_TWO_PROGRAMS_SOURCE_AMBIGUITY.json"
    f.write_text(json.dumps(record,sort_keys=True,indent=2))
    print("ORIGINAL_STRING_AMBIGUITY_SHA256",sha256(f.read_bytes()))
    print("ORIGINAL_STRING_AMBIGUITY_VERDICT",record["verdict"])
if __name__=="__main__":main()
