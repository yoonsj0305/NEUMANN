#!/usr/bin/env python3
"""External source-authored SLIA: two distinct grammar-derivable satisfying
programs with identical published examples and conflicting unseen input.
POSTCONTENT. Independent Z3 *and* native CVC5 SMT-LIB original checks.
No invented callable intended-output oracle or learned ownweight neural credit.
"""
import json,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
SOURCE="lib/PBE_SLIA_Track/euphony/get-first-word.sl"
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("original_external_pbe_underidentification")
TERM_A='(str.substr _arg_0 0 (str.indexof _arg_0 " " 0))'
TERM_B='(ite (str.suffixof " " _arg_0) _arg_0 (str.substr _arg_0 0 (str.indexof _arg_0 " " 0)))'
TYPED_A='(define-fun f ((_arg_0 String)) String '+TERM_A+')'
TYPED_B='(define-fun f ((_arg_0 String)) String '+TERM_B+')'
KNOWN={
'"The quick brown fox."':'"The"',
'"quick brown fox."':'"quick"',
'"fox"':'""'
}

def native_prove(filename):
    cmd=["cvc5","--lang=smt2",str(filename)]
    proc=subprocess.run(cmd,capture_output=True,text=True,timeout=20)
    lines=[x.strip() for x in proc.stdout.splitlines() if x.strip()]
    return {'exit_code':proc.returncode,'stdout_sha256':sha256(proc.stdout.encode()),
            'stderr_sha256':sha256(proc.stderr.encode()),
            'verdict':lines[-1] if lines else 'NO_OUTPUT',
            'stderr_tail':proc.stderr[-500:]}
def z3_prove(script):
    import z3
    solver=z3.Solver();solver.set(timeout=15000)
    solver.add(*z3.parse_smt2_string(script))
    return str(solver.check())

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    cvc5ver=subprocess.check_output(["cvc5","--version"],text=True).splitlines()[0]
    assert cvc5ver.startswith("cvc5 1.4.2 ")
    raw=(ROOT/SOURCE).read_bytes()
    parsed=[(get_cmd(f[2]),f[2]) for f in top_level_forms(raw.decode())]
    synths=[f for cmd,f in parsed if cmd=="synth-fun"]
    constraints=[f for cmd,f in parsed if cmd=="constraint"]
    assert len(synths)==1 and len(constraints)==3
    original_synth=synths[0]
    assert re.search(r"^\(\s*synth-fun\s+f\s+\(\s*\(_arg_0\s+String\)\s*\)\s+String",original_synth)
    for lex in ('_arg_0','" "',' 0 ','str.substr','str.indexof','str.suffixof','ite'):
        assert lex.strip() in original_synth,("MISSING_ORIGINAL_GRAMMAR_SYMBOL",lex)
    assert '"hello "' not in original_synth
    bodies=[]
    for form in constraints:
        m=re.fullmatch(r"\(\s*constraint\s+(.+)\s*\)",form,re.S)
        assert m
        bodies.append(m.group(1))
    for literal,out in KNOWN.items():
        assert any(('"'+literal.strip('"')+'"') in s and out in s for s in bodies)
    OUT.mkdir(exist_ok=True)
    results=[]
    for label,definition in (("P1",TYPED_A),("P2",TYPED_B)):
        (OUT/(label+"_ORIGINAL_GRAMMAR_PROGRAM.smt2")).write_text(definition+"\n")
        assertion='(and '+' '.join(bodies)+')'
        script='(set-logic ALL)\n'+definition+'\n(assert (not '+assertion+'))\n(check-sat)\n'
        fn=OUT/(label+"_ORIGINAL3_SOURCE_COUNTEREXAMPLE_QUERY.smt2")
        fn.write_text(script)
        z=z3_prove(script)
        c=native_prove(fn)
        results.append({'candidate':label,'candidate_sha256':sha256(definition.encode()),
                        'original_example_constraints':3,
                        'original_source_all_example_violations_Z3':z,
                        'original_source_all_example_violations_CVC5':c,
                        'full_original_examples_pass':z=="unsat" and c['verdict']=="unsat" and c['exit_code']==0})
        print("ORIGINAL_SLIA_PBE",label,"Z3",z,"CVC5",c['verdict'],flush=True)
    fn=OUT/"TWO_GRAMMAR_LEGAL_PROGRAMS_DISTINGUISH_UNSEEN_INPUT.smt2"
    diff='(set-logic ALL)\n'+TYPED_A.replace('(define-fun f ','(define-fun f_P1 ')+'\n'+TYPED_B.replace('(define-fun f ','(define-fun f_P2 ')+'''
(assert (= (f_P1 "hello ") "hello"))
(assert (= (f_P2 "hello ") "hello "))
(assert (not (= (f_P1 "hello ") (f_P2 "hello "))))
(check-sat)
'''
    fn.write_text(diff)
    z=z3_prove(diff);c=native_prove(fn)
    print("ORIGINAL_SLIA_UNSEEN_WITNESS",z,c['verdict'],flush=True)
    passall=all(r['full_original_examples_pass'] for r in results) and z=="sat" and c['verdict']=="sat" and c['exit_code']==0
    receipt={
       'kind':'EXTERNAL_ORIGINAL_SOURCE_PBE_SEMANTIC_NONIDENTIFIABILITY',
       'retrospective_after_opening_source':True,
       'original_repository':'SyGuS-Org/benchmarks','original_commit':PIN,
       'source_original_path':SOURCE,'source_original_sha256':sha256(raw),
       'source_original_example_count':len(constraints),
       'both_candidates_grammar_derivation':'CONSTRUCTIVE_SOURCE_OPERATOR_AND_TERMINAL_CHECK',
       'arbitrary_target_output_oracle_from_source':False,
       'hypothesis_witness_input':'hello ','P1_output':'hello','P2_output':'hello ',
       'witness_z3':z,'witness_native_cvc5':c,
       'independent_z3_version':z3.get_version_string(),'native_cvc5_version':cvc5ver,
       'same_source_all_original_examples_proved':passall,
       'scientific_verdict':'TWO_DISTINCT_SOURCE_CONSISTENT_PROGRAMS' if passall else 'HOLD',
       'not_a_hidden_expected_target_label':True,
       'not_learned_neumann_policy':True,
       'global_Q1_Q7':'OPEN','G1':'HOLD','G2':'NOT_RUN',
       'candidates':results}
    p=OUT/"ORIGINAL_SLIA_TWO_SOURCE_CONSISTENT_EXECUTABLE_PROGRAMS_Z3_CVC5.json"
    p.write_text(json.dumps(receipt,sort_keys=True,indent=2))
    print("PROOF_SHA256",sha256(p.read_bytes()),flush=True)
    print("PROOF_VERDICT",receipt['scientific_verdict'])
if __name__=="__main__":main()
