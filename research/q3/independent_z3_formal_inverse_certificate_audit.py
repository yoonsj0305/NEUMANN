"""Independent Z3 SMT bitvector proof of Q3 previously claimed formal victories.

All official .sl tasks are translated to standard SMT-LIB using a separate
verifier. This script DOES NOT use the research solver's 4-bit evaluator,
candidate search or checked-example table. It only reads program ASTs from
immutable prior original-first artifacts. Z3 searches for a counterexample
to the official constraint; unsat certifies the candidate for ALL 256 inputs.

Scientific caveat: solver is a third-party theorem engine and confidence
depends on its correct SMT-LIB interpretation; this is stronger independent
evidence than self-testing a handwritten interpreter.
"""
from __future__ import annotations
import hashlib,json,pathlib,time,urllib.request
import z3

REV="13c8deb68a873635879c9a69bc78caebd340f646"
ROOT=f"https://raw.githubusercontent.com/SyGuS-Org/benchmarks/{REV}/comp/2019/General_Track/bv-conditional-inverses/"
LEDGERS=[
 ("historical_a/Q3_FORMAL_TARGET_FIRST.json","target_records",("learned","strong_cold")),
 ("historical_b/Q3_FORMAL_SECOND_ORIGINAL_FIRST.json","records",("memory_policy","strong_cold_same_grammar")),
 ("historical_c/Q3_FORMAL_GRAMMAR_GROWTH_NEW_FIRST.json","records",("old_fixed","full_cold_large","failure_triggered_growth")),
 ("historical_d/Q3_MACRO_GENERALIZATION_NEW_ORIGINAL_FIRST.json","records",("fixed_grammar_cold","macro_first","same_language_full_cold")),
 ("historical_e/Q3_METHOD_DELETION_EXTERNAL_FIRST.json","records",("cold","learning_policy","selected_actual"))]
def tokenize(s):
    import re
    s=re.sub(r";[^\n]*","",s)
    return re.findall(r"\(|\)|[^\s()]+",s)

def parse(raw):
    ts=tokenize(raw);frames=[];head=[]
    for token in ts:
        if token=="(":
            item=[]
            (frames[-1] if frames else head).append(item)
            frames.append(item)
        elif token==")":
            if not frames:raise ValueError("UNBALANCED_CLOSE")
            frames.pop()
        else:
            if not frames:raise ValueError("ATOM_OUTSIDE_FORM")
            frames[-1].append(token)
    if frames:raise ValueError("UNCLOSED_FORM")
    return head

def smt_type(ast):
    if isinstance(ast,list):
        if len(ast)==2 and ast[0]=="BitVec":return "(_ BitVec "+str(ast[1])+")"
        return "("+" ".join(smt_type(a) for a in ast)+")"
    return str(ast)

def p2s(ast):
    if not isinstance(ast,list) or not ast:raise ValueError("INVALID_PROGRAM_AST")
    op=ast[0]
    if op in ("s","t") and len(ast)==1:return op
    if op=="lit" and len(ast)==2:
        k=ast[1]
        if type(k) is not int or not 0<=k<=15:raise ValueError("BAD_LITERAL")
        return "#x"+format(k,"x")
    if op not in ("bvnot","bvneg","bvadd","bvsub","bvand","bvor","bvshl","bvlshr"):
        raise ValueError("ILLEGAL_PROGRAM_OPERATOR")
    if len(ast)!=(2 if op in ("bvnot","bvneg") else 3):
        raise ValueError("ILLEGAL_OPERATOR_ARITY")
    return "("+op+" "+" ".join(p2s(v) for v in ast[1:])+")"

def build_smt(original,program):
    forms=parse(original)
    if len([x for x in forms if x and x[0]=="synth-fun"])!=1:
        raise ValueError("UNEXPECTED_SYNTH_FUNCTION_COUNT")
    chunks=["(set-logic QF_BV)"]
    compiled="(define-fun inv ((s (_ BitVec 4)) (t (_ BitVec 4))) (_ BitVec 4) "+p2s(program)+")"
    chunks.append(compiled)
    constraints=0
    for f in forms:
        if not f:continue
        tag=f[0]
        if tag in ("set-logic","synth-fun","check-synth"):continue
        if tag=="declare-var":
            if len(f)!=3:raise ValueError("WRONG_DECLARATION")
            chunks.append("(declare-const "+f[1]+" "+smt_type(f[2])+")")
        elif tag=="constraint":
            if len(f)!=2:raise ValueError("WRONG_CONSTRAINT")
            chunks.append("(assert (not "+smt_type(f[1])+"))")
            constraints+=1
        elif tag=="define-fun":
            chunks.append(smt_type(f))
        else:raise ValueError("UNSUPPORTED_ORIGINAL_TOPLEVEL "+tag)
    if constraints!=1:raise ValueError("EXPECTED_SINGLE_FORMAL_CONSTRAINT")
    return "\n".join(chunks)

CACHE={}
def fetch(name):
    if name not in CACHE:
        with urllib.request.urlopen(ROOT+name,timeout=25) as f:raw=f.read(200001)
        if len(raw)>200000:raise ValueError("FILE_LIMIT")
        CACHE[name]=raw.decode("utf-8")
    return CACHE[name]

def prove(smt):
    st=time.perf_counter_ns()
    solver=z3.Solver()
    solver.set("timeout",8000)
    solver.from_string(smt)
    answer=solver.check()
    elapsed=(time.perf_counter_ns()-st)/1e6
    if answer==z3.unsat:return "PROVED_UNSAT",round(elapsed,5),None
    if answer==z3.sat:
        return "COUNTEREXAMPLE_SAT",round(elapsed,5),str(solver.model())[:500]
    return "UNKNOWN",round(elapsed,5),str(solver.reason_unknown())

def audit():
    results=[]
    for fpath,rowskey,arms in LEDGERS:
        ledger=json.loads(pathlib.Path(fpath).read_text())
        for row in ledger[rowskey]:
            name=row.get("name",row.get("id"))
            if "error" in row:continue
            parsed={}
            for arm in arms:
                slot=row.get(arm,{})
                expected=slot.get("proved",slot.get("proof",slot.get("full_256_proved",False)))
                program=slot.get("ast",slot.get("program"))
                if program is None:continue
                unique=(name,json.dumps(program,sort_keys=True))
                if unique not in parsed:
                    try:
                        raw=fetch(name)
                        source_digest=hashlib.sha256(raw.encode()).hexdigest()
                        expected_digest=row.get("original_sha256",row.get("source_sha256"))
                        if expected_digest and source_digest!=expected_digest:
                            raise ValueError("ORIGINAL_DOCUMENT_HASH_CHANGED")
                        smt=build_smt(raw,program)
                        status,ms,counterexample=prove(smt)
                        parsed[unique]={"status":status,"verify_ms":ms,
                                        "counterexample":counterexample}
                    except Exception as e:
                        parsed[unique]={"status":"VERIFIER_ERROR",
                                        "error":type(e).__name__+": "+str(e)[:170]}
                rec={"historical_ledger":fpath,"task_id":name,"arm":arm,
                     "research_claimed_proved":bool(expected),
                     "original_sha256":row.get("original_sha256",row.get("source_sha256")),
                     "ast":program,**parsed[unique]}
                results.append(rec)
    stats={
      "submitted_total":len(results),
      "independently_proved":sum(x["status"]=="PROVED_UNSAT" for x in results),
      "invalid_or_counterexample":sum(x["status"]=="COUNTEREXAMPLE_SAT" for x in results),
      "unsupported_or_verifier_error":sum(x["status"] in ("VERIFIER_ERROR","UNKNOWN") for x in results),
      "claimed_successes_without_independent_proof":sum(
        x["research_claimed_proved"] and x["status"]!="PROVED_UNSAT" for x in results)}
    report={"schema":"neumann.q3.independent-z3-cross-check-formal-original-ledgers.v1",
      "verifier":"z3-solver",
      "z3_version":z3.get_version_string(),
      "upstream_commit":REV,
      "research_original_first_results_are_immutable":True,
      "summary":stats,"rows":results,
      "interpretation":"SMT solver UNSAT of negated official constraint over QF_BV verifies all 256 input pairs; not universal Q3 evidence."}
    pathlib.Path("Q3_INDEPENDENT_Z3_FORMAL_AUDIT.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(stats,indent=2))
    if stats["claimed_successes_without_independent_proof"]>0:
        raise AssertionError("ORIGINAL_FULL_PROOF_CLAIMS_NOT_INDEPENDENTLY_CONFIRMED")
    return report

if __name__=="__main__":audit()
