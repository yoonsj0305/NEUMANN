#!/usr/bin/env python3
"""POST-CONTENT external SLIA PBE non-identifiability, two grammar-legal programs.

Original source pins upstream Git SHA. Reproduce ALL THREE source constraints
and witness with Z3 4.13.3 and independent official CVC5 1.4.2 SMT engine.
This proves specification non-uniqueness, not ideal human target semantics.
"""
import collections,hashlib,json,pathlib,re,resource,subprocess,time
from functools import lru_cache

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
PATH="lib/PBE_SLIA_Track/euphony/get-first-word.sl"
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("external_string_pbe_two_source_solutions")
EXPECTED_INPUTS=(
  ('"The quick brown fox."','"The"'),
  ('"quick brown fox."','"quick"'),
  ('"fox"','""'))
P1='(str.substr _arg_0 0 (str.indexof _arg_0 " " 0))'
P2='(ite (str.suffixof " " _arg_0) _arg_0 (str.substr _arg_0 0 (str.indexof _arg_0 " " 0)))'

def sha(b):return hashlib.sha256(b).hexdigest()

def parse(s):
    tokens=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',s)
    cursor=0
    def node():
        nonlocal cursor
        if cursor>=len(tokens):raise ValueError("UNEXPECTED_EOF")
        t=tokens[cursor];cursor+=1
        if t!="(":
            if t==")":raise ValueError("UNEXPECTED_CLOSE")
            return t
        sub=[]
        while cursor<len(tokens) and tokens[cursor]!=")":
            sub.append(node())
        if cursor>=len(tokens):raise ValueError("UNCLOSED_EXPR")
        cursor+=1
        return sub
    output=[]
    while cursor<len(tokens):output.append(node())
    return output

def derive(term,nonterminal,grammar):
    # Normal syntax tree membership, even with source-recursive nonterminals.
    seen=set()
    def impl(node,nt):
        key=(repr(node),nt)
        if key in seen:return False
        seen.add(key)
        def match(pattern,value):
            if isinstance(pattern,str):
                return impl(value,pattern) if pattern in grammar else pattern==value
            return isinstance(value,list) and len(pattern)==len(value) and all(
                match(a,b) for a,b in zip(pattern,value))
        ans=any(match(pattern,node) for pattern in grammar[nt])
        seen.remove(key)
        return ans
    return impl(term,nonterminal)

def do_check(smt,tag):
    import z3
    OUT.mkdir(parents=True,exist_ok=True)
    filename=OUT/(tag+".smt2")
    filename.write_text(smt)
    begin=time.process_time()
    solver=z3.Solver()
    solver.set(timeout=8000)
    solver.add(*z3.parse_smt2_string(smt))
    z=str(solver.check())
    z_cpu=time.process_time()-begin
    def cpu_cap():resource.setrlimit(resource.RLIMIT_CPU,(8,9))
    before=resource.getrusage(resource.RUSAGE_CHILDREN)
    started=time.monotonic()
    try:
        p=subprocess.run(["cvc5","--lang=smt2",str(filename)],capture_output=True,
                         text=True,timeout=10,preexec_fn=cpu_cap)
        lines=[k.strip() for k in p.stdout.splitlines() if k.strip()]
        c=lines[-1] if p.returncode==0 and lines else "HOLD_EXIT_"+str(p.returncode)
        err=p.stderr[-350:]
    except subprocess.TimeoutExpired:
        c="HOLD_WALL_TIMEOUT";err="TIMEOUT"
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
      "test":tag,"source_script_sha256":sha(smt.encode()),"z3":z,"cvc5_142":c,
      "two_formal_engines_agree":z==c,
      "z3_cpu_seconds":round(z_cpu,6),
      "cvc5_child_cpu_seconds":round(after.ru_utime-before.ru_utime+
                after.ru_stime-before.ru_stime,6),
      "cvc5_wall_seconds":round(time.monotonic()-started,6),
      "cvc5_error_excerpt":err
    }

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    assert subprocess.check_output(["cvc5","--version"],text=True).splitlines()[0].startswith("cvc5 1.4.2 ")
    raw=(ROOT/PATH).read_bytes()
    original=raw.decode("utf8")
    no_comments="\n".join(k for k in original.splitlines() if not k.lstrip().startswith(";"))
    forms=parse(no_comments)
    synth=[x for x in forms if isinstance(x,list) and x[0]=="synth-fun"]
    constraints=[x for x in forms if isinstance(x,list) and x[0]=="constraint"]
    assert len(synth)==1 and len(constraints)==3
    name,arg,ret,clauses=synth[0][1:]
    assert name=="f" and arg==[["_arg_0","String"]] and ret=="String"
    assert all(c[:2]==["constraint",["=",["f",c[1][1][1]],c[1][2]]] for c in constraints)
    exact=[(c[1][1][1],c[1][2]) for c in constraints]
    assert exact==list(EXPECTED_INPUTS)
    grammar={r[0]:r[2] for r in clauses}
    assert set(grammar)=={"Start","ntString","ntInt","ntBool"}
    assert derive(parse(P1)[0],"Start",grammar)
    assert derive(parse(P2)[0],"Start",grammar)
    # Source defines no other helpers; substitute candidate outputs with exactly
    # the source's typed signature and all constraints, not hand-selected subset.
    records=[]
    names=("f_P1","f_P2")
    bodies=(P1,P2)
    for program_name,body in zip(names,bodies):
        defined=f"(define-fun f ((_arg_0 String)) String {body})"
        prefix="(set-logic ALL)\n"+defined+"\n"
        for i,c in enumerate(constraints):
            # Render exact AST to avoid brittle raw-text parsing/comments.
            def smt(term):
                if isinstance(term,list):return "("+" ".join(smt(t) for t in term)+")"
                return term
            expr=smt(c[1])
            records.append((do_check(prefix+"(assert (not "+expr+"))\n(check-sat)\n",
                                     program_name+"_source_"+str(i+1)),"unsat"))
        expr="(and "+" ".join(smt(c[1]) for c in constraints)+")"
        records.append((do_check(prefix+"(assert (not "+expr+"))\n(check-sat)\n",
                                 program_name+"_all_3_original"),"unsat"))
    both="(set-logic ALL)\n"+\
         f"(define-fun f_P1 ((_arg_0 String)) String {P1})\n"+\
         f"(define-fun f_P2 ((_arg_0 String)) String {P2})\n"
    records.append((do_check(both+'(assert (= (f_P1 "hello ") (f_P2 "hello ")))\n(check-sat)\n',
                             "witness_both_equal_is_impossible"),"unsat"))
    records.append((do_check(both+'(assert (not (= (f_P1 "hello ") (f_P2 "hello "))))\n(check-sat)\n',
                             "witness_both_different_is_possible"),"sat"))
    records.append((do_check(both+'(assert (not (= (f_P1 "hello ") "hello")))\n(check-sat)\n',
                             "witness_f_P1_is_hello"),"unsat"))
    records.append((do_check(both+'(assert (not (= (f_P2 "hello ") "hello ")))\n(check-sat)\n',
                             "witness_f_P2_is_hello_space"),"unsat"))
    rows=[dict(x,expected=expect,passed=(x["z3"]==expect and x["cvc5_142"]==expect))
          for x,expect in records]
    for r in rows:print("POSTFIRST_EXTERNAL_SLIA_SMT",r["test"],r["z3"],r["cvc5_142"],"PASS" if r["passed"] else "HOLD",flush=True)
    report={
       "study":"POSTFIRST_TWO_DISTINCT_ORIGINAL_GRAMMAR_PROGRAMS_OBSERVATION_UNDERIDENTIFIED",
       "original_upstream_pin":PIN,"original_source_file":PATH,"original_sha256":sha(raw),
       "exact_source_ground_examples":exact,"source_n_ground_examples":3,
       "source_syntactic_grammar_checked":True,
       "P1":P1,"P2":P2,"P1_and_P2_derivable":True,
       "new_input":'hello ',"P1_output":'hello',"P2_output":'hello ',
       "new_input_desired_answer_in_original_source":"NOT_AVAILABLE",
       "demonstrates_two_distinct_solutions_to_finite_specification":all(r["passed"] for r in rows),
       "source_arbitrary_target_label_oracle":"NOT_GRANTED",
       "original_native_sygus_1_4_2_error_not_reinterpreted":True,
       "Z3":z3.get_version_string(),
       "CVC5":subprocess.check_output(["cvc5","--version"],text=True).splitlines()[0],
       "n_actual_verifier_queries":len(rows),
       "n_two_engine_agreements":sum(r["passed"] for r in rows),
       "global_Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN",
       "rows":rows
    }
    p=OUT/"EXTERNAL_SLIA_PBE_TWO_ORIGINAL_GRAMMAR_SAT_PROGRAMS_INDETERMINATE_WITNESS.json"
    p.write_text(json.dumps(report,sort_keys=True,indent=2))
    print("FINAL_JSON_SHA256",sha(p.read_bytes()))
    print("TWO_FORMAL_ENGINE_VERDICT",report["demonstrates_two_distinct_solutions_to_finite_specification"])
if __name__=="__main__":main()
