#!/usr/bin/env python3
"""Postfirst (OPENED source) classical comma name swap original SyGuS PBE.

Prove exact source grammar AST membership and ALL original author example
clauses with independent Z3 4.13.3 and official native CVC5 1.4.2.
This is NOT neural ownweight discovery, NOT a blind train/test result.
"""
import collections,hashlib,json,pathlib,re,resource,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_sortingnaive_boolean_cnf_cfg_z3_postfirst_20261028 import parse_s_expr

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
REL="lib/PBE_SLIA_Track/euphony/get-last-name-from-name-with-comma.sl"
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("postfirst_lastname_classical_smt")
SOURCE_PROGRAM=(
  '(define-fun f ((_arg_0 String)) String '
  '(str.++ (str.substr _arg_0 (+ (str.indexof _arg_0 "," 0) 1) (str.len _arg_0)) '
  '(str.++ "," (str.substr _arg_0 0 (str.indexof _arg_0 "," 0)))))'
)

def actual_source_grammar_accepts(synth,code):
    source=parse_s_expr(synth)
    candidate=parse_s_expr(code)
    assert source[0]=="synth-fun" and source[1]=="f"
    assert candidate[0]=="define-fun" and candidate[1]=="f"
    assert source[2]==candidate[2] and source[3]==candidate[3]
    assert source[2]==[["_arg_0","String"]] and source[3]=="String"
    actual=candidate[4]
    assert len(source)==5
    g={rule[0]:rule[2] for rule in source[4]}
    assert set(g)=={"Start","ntString","ntInt","ntBool"}
    cache={}
    active=set()
    def accepts(nt,exp):
        key=(nt,repr(exp))
        if key in cache:return cache[key]
        if key in active:return False
        active.add(key)
        answer=any(match(p,exp) for p in g[nt])
        active.remove(key)
        cache[key]=answer
        return answer
    def match(p,exp):
        if isinstance(p,str):
            return accepts(p,exp) if p in g else p==exp
        return isinstance(p,list) and isinstance(exp,list) and len(p)==len(exp) and all(
           match(a,b) for a,b in zip(p,exp))
    result=accepts("Start",actual)
    return result,len(cache),list(g)

def native_cvc5(script):
    path=OUT/"LASTNAME_ORIGINAL_EXAMPLES_CVC5.smt2"
    path.write_text(script+"(check-sat)\n")
    def limits():
        resource.setrlimit(resource.RLIMIT_CPU,(10,11))
    t=time.monotonic()
    before=resource.getrusage(resource.RUSAGE_CHILDREN)
    run=subprocess.run(["cvc5","--lang=smt2",str(path)],capture_output=True,
                       text=True,errors="replace",timeout=13,preexec_fn=limits)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    stdout=run.stdout.strip()
    return {
       "solver":"published_official_cvc5_1.4.2",
       "result":stdout.splitlines()[-1] if stdout else "NO_OUTPUT",
       "returncode":run.returncode,
       "wall_seconds":round(time.monotonic()-t,6),
       "child_cpu_seconds":round((after.ru_utime+after.ru_stime)-(before.ru_utime+before.ru_stime),6),
       "stdout_sha256":sha256(run.stdout.encode()),
       "stderr_excerpt":run.stderr[-400:],
       "script_sha256":sha256((script+"(check-sat)\n").encode())}

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    version=subprocess.check_output(["cvc5","--version"],text=True).splitlines()[0]
    assert version.startswith("cvc5 1.4.2 "),version
    raw=(ROOT/REL).read_bytes()
    parts=[(get_cmd(f[2]),f[2]) for f in top_level_forms(raw.decode())]
    orig_synth=[v for c,v in parts if c=="synth-fun"]
    original_constraints=[v for c,v in parts if c=="constraint"]
    assert len(orig_synth)==1 and len(original_constraints)==3
    is_legal,states,nodes=actual_source_grammar_accepts(orig_synth[0],SOURCE_PROGRAM)
    assert is_legal, "EXACT_ORIGINAL_GHAST_AST_NOT_DERIVABLE"
    # The source PBE may be underspecified outside these exact examples; prove
    # only ALL author constraints, not behavior on arbitrary unseen strings.
    terms=[]
    for row in original_constraints:
        form=parse_s_expr(row)
        assert form[0]=="constraint" and len(form)==2
        terms.append(row[row.find("(constraint")+len("(constraint"):].strip()[:-1].strip())
    assert len(terms)==3
    script="(set-logic ALL)\n"+SOURCE_PROGRAM+"\n(assert (not (and " + " ".join(terms) + ")))\n"
    OUT.mkdir(exist_ok=True)
    (OUT/"LASTNAME_CLASSICAL_ORIGINAL_TYPED_PROGRAM.smt2").write_text(SOURCE_PROGRAM+"\n")
    (OUT/"LASTNAME_ORIGINAL_EXAMPLES_Z3.smt2").write_text(script+"(check-sat)\n")
    solver=z3.Solver();solver.set(timeout=12000)
    t=time.process_time()
    solver.add(*z3.parse_smt2_string(script))
    independent=str(solver.check())
    z3cpu=time.process_time()-t
    classic=native_cvc5(script)
    passed=(independent=="unsat" and classic["result"]=="unsat" and
            classic["returncode"]==0 and is_legal)
    report={
      "task":"POSTFIRST_GRAMMAR_ADMISSIBLE_CLASSIC_NAME_SWAP_F_FULL_ORIGINAL_AUTHOR_EXAMPLES",
      "original_upstream":PIN,"original_file":REL,"original_sha256":sha256(raw),
      "original_constraints":3,"original_grammar_derivable":is_legal,
      "original_grammar_proof_search_states":states,"original_nonterminals":nodes,
      "classic_candidate":SOURCE_PROGRAM,
      "classic_candidate_sha256":sha256(SOURCE_PROGRAM.encode()),
      "Z3_solver":"4.13.3.0","Z3_result":independent,
      "Z3_process_cpu_seconds":round(z3cpu,6),
      "independent_CVC5":classic,
      "strict_claim_original_PBE_examples_only":True,
      "unseen_target_oracle_provided":False,
      "original_native_untranslated": "PARSER_ERROR",
      "original_native_compatible_modern_source":"CPU12_BUDGET_HOLD",
      "status":"POSTFIRST_CLASSICAL_TWO_BACKENDS_FORMAL_PBE_PASS" if passed else "HOLD_OR_FAILED_PROOF",
      "neural_model_trained":False,"Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN"}
    f=OUT/"LASTNAME_CLASSICAL_EXACT_GRAMMAR_TWO_INDEPENDENT_SMT_PROOFS.json"
    f.write_text(json.dumps(report,sort_keys=True,indent=2))
    print("LASTNAME_ORIGINAL_CLASSIC",report["status"],"Z3",independent,"CVC5",classic["result"],flush=True)
    print("LASTNAME_PROOF_SHA256",sha256(f.read_bytes()),flush=True)
if __name__=="__main__":main()
