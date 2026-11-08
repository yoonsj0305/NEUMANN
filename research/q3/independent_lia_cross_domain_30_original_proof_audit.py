"""Independent SMT verifier for source-invented integer constructor transfers.

DOES NOT call research programs' original parser, compiler, program search,
mathematical task oracle, or declared evaluator. Uses a separate raw
S-expression top-level lexer, independent SMT-LIB adapter and pinned Z3.

Official SyGuS original docs at pinned upstream; every claimed positive
program is inserted into the unmodified official constraints. Z3 checks the
NEGATION of all original constraints; UNSAT establishes no Int counterexample
exists. Original SHA and frozen-ledger task IDs strictly checked.
"""
from __future__ import annotations
import hashlib,json,pathlib,re,time,urllib.request
import z3

ROOT="https://raw.githubusercontent.com/SyGuS-Org/benchmarks/13c8deb68a873635879c9a69bc78caebd340f646/comp/2019/CLIA_Track/from_2018/"
LEDGERS=[
 ("original_max/Q3_CROSS_THEORY_INTEGER_MAX_ORIGINAL_FIRST.json","target_records","max"),
 ("original_alt/Q3_INTEGER_DIVERSE_CO_12_UNSEEN_ORIGINAL_FIRST.json","rows","other_max"),
 ("original_scan/Q3_SOURCE_DISPATCH_SCAN_13_INTEGER_ORIGINAL_FIRST.json","rows","scan")]
SOURCE_FOLD="source_fold/Q3_CROSS_THEORY_INTEGER_SOURCE_POLICY_FROZEN.json"
OUTPUT="Q3_INDEPENDENT_Z3_UNBOUNDED_INTEGER_30_ORIGINAL_AUDIT.json"

def toplevel(raw):
    """Parse only top-level parenthesized SMT forms, preserving nested form
    bytes. This is intentionally NOT the typed research S-expression parser.
    """
    raw=re.sub(r";[^\n]*","",raw)
    forms=[];begin=None;depth=0
    for i,ch in enumerate(raw):
        if ch=="(":
            if depth==0:begin=i
            depth+=1
        elif ch==")":
            depth-=1
            if depth<0:raise ValueError("UNBALANCED_CLOSE")
            if depth==0 and begin is not None:
                forms.append(raw[begin:i+1].strip())
                begin=None
    if depth or begin is not None:raise ValueError("UNCLOSED_FORM")
    return forms

def synth_info(declaration):
    pat=r"^\(synth-fun\s+([^\s()]+)\s+(\((?:\s*\([^\(\)]*\)\s*)+\))\s+Int\s*\)$"
    match=re.fullmatch(pat,declaration.strip(),flags=re.S)
    if not match:raise ValueError("UNSUPPORTED_DECLARATION")
    name,arglist=match.group(1),match.group(2)
    params=re.findall(r"\(\s*([^\s()]+)\s+Int\s*\)",arglist)
    if not params or len(params)>24:raise ValueError("ARGUMENT_COUNT")
    return name,params

def compile_independent(raw,program):
    blocks=toplevel(raw)
    fun=[x for x in blocks if x.startswith("(synth-fun ")]
    if len(fun)!=1:raise ValueError("EXPECTED_ONE_PROGRAM")
    name,params=synth_info(fun[0])
    header="(define-fun "+name+" ("+" ".join(f"({x} Int)" for x in params)+") Int "+program+")"
    output=[header];clauses=[]
    for block in blocks:
        if block.startswith("(synth-fun ") or block.startswith("(set-logic ") or block.startswith("(check-synth"):continue
        if block.startswith("(declare-var "):
            mat=re.fullmatch(r"\(declare-var\s+([^\s()]+)\s+Int\s*\)",block)
            if not mat:raise ValueError("BAD_DECLARED_VARIABLE")
            output.append("(declare-const "+mat.group(1)+" Int)")
        elif block.startswith("(define-fun "):
            output.append(block)
        elif block.startswith("(constraint "):
            clauses.append(block[len("(constraint "):-1].strip())
        else:raise ValueError("UNKNOWN_TOPLEVEL")
    if len(clauses)<2:raise ValueError("TOO_FEW_ORIGINAL_CONSTRAINTS")
    output.append("(assert (not (and "+" ".join(clauses)+")))")
    return "\n".join(output),params

def prove(raw,program):
    t=time.perf_counter_ns()
    script,params=compile_independent(raw,program)
    solver=z3.Solver();solver.set(timeout=8000)
    solver.from_string(script)
    ans=solver.check()
    if ans==z3.unsat:status="INDEPENDENT_UNBOUNDED_INT_PROVED_UNSAT"
    elif ans==z3.sat:status="COUNTEREXAMPLE_SAT"
    else:status="VERIFIER_UNKNOWN"
    return {"status":status,"z3_ms":round((time.perf_counter_ns()-t)/1e6,5),
         "counterexample":str(solver.model())[:350] if ans==z3.sat else None}

def original(name):
    with urllib.request.urlopen(ROOT+name,timeout=25) as handle:raw=handle.read(250001)
    if len(raw)>250000:raise ValueError("OVERSIZE_ORIGINAL")
    return raw.decode()

def fold_program(names,constructor):
    # Fresh independent serialization of source-learned candidate; the
    # original solver's compiler/constructor is never imported.
    op,choose=constructor
    left=names[0]
    for right in names[1:]:
        guard="("+op+" "+left+" "+right+")"
        if choose=="left":left=f"(ite {guard} {left} {right})"
        elif choose=="right":left=f"(ite {guard} {right} {left})"
        else:raise ValueError("UNKNOWN_CONSTRUCTOR")
    return left

def main():
    p=json.loads(pathlib.Path(SOURCE_FOLD).read_text())
    fold=tuple(p["learned_fold_constructor"])
    claimed=[];accepted=[]
    for ledger,section,group in LEDGERS:
        original_ledger=json.loads(pathlib.Path(ledger).read_text())
        for rec in original_ledger[section]:
            name=rec.get("name",rec.get("id"))
            if group=="max":
                good=rec.get("learned",{}).get("status")=="UNBOUNDED_INT_Z3_UNSAT"
            elif group=="other_max":
                good=(rec.get("cohort")=="alternate_max_name" and
                      rec.get("memory",{}).get("status")=="UNBOUNDED_INT_Z3_UNSAT")
            else:
                good=rec.get("learned",{}).get("proof",False)
            if not good:continue
            claimed.append((name,rec,group))
    target=set(x[0] for x in claimed)
    if len(target)!=30 or len(claimed)!=30:
        raise ValueError("EXPECTED_30_DISJOINT_PROVEN_ORIGINALS")
    rows=[]
    for name,ledger,group in claimed:
        row={"id":name,"group":group}
        try:
            text=original(name)
            check=hashlib.sha256(text.encode()).hexdigest()
            if check!=ledger.get("original_sha256"):
                raise ValueError("FROZEN_ORIGINAL_FILE_HASH_MISMATCH")
            if group=="scan":
                trials=ledger["learned"]["trials"]
                good=[x for x in trials if x["status"]=="PROVED_ALL_INTEGERS"]
                if len(good)!=1:raise ValueError("SCAN_PROGRAM_NOT_UNIQUE")
                program=good[0]["program_body"]
            else:
                declaration=next(x for x in toplevel(text) if x.startswith("(synth-fun "))
                _,args=synth_info(declaration)
                program=fold_program(args,fold)
            ans=prove(text,program)
            row.update({"program":program,"original_sha256":check,**ans})
        except Exception as e:row.update({"status":"VERIFIER_ERROR","error":type(e).__name__+": "+str(e)[:200]})
        rows.append(row)
    controls=[]
    for group in ("max","scan"):
        first=next(x for x in claimed if x[2]==group)
        text=original(first[0])
        result=prove(text,"0")
        controls.append({"group":group,"status":result["status"],
                         "counterexample":result["counterexample"]})
    stats={"submitted_distinct_originals":len(rows),
           "unique_original_ids":len(set(x["id"] for x in rows)),
           "all_integer_proofs":sum(x["status"]=="INDEPENDENT_UNBOUNDED_INT_PROVED_UNSAT" for x in rows),
           "counterexamples":sum(x["status"]=="COUNTEREXAMPLE_SAT" for x in rows),
           "errors":sum(x["status"] in ("VERIFIER_ERROR","VERIFIER_UNKNOWN") for x in rows),
           "negative_control_sat":sum(x["status"]=="COUNTEREXAMPLE_SAT" for x in controls)}
    result={"schema":"neumann.q3.two-representations-independent-lia-original-check.v1",
      "official_upstream_commit":"13c8deb68a873635879c9a69bc78caebd340f646",
      "z3_version":z3.get_version_string(),
      "independent_from_research_translator":True,
      "summary":stats,"rows":rows,"negative_controls":controls,
      "limitations":"An independent SMT syntax adapter/translator and Z3 are used, but the original source constraint data and SMT solver semantics remain the common trusted mathematical basis."}
    pathlib.Path(OUTPUT).write_text(json.dumps(result,indent=2))
    print(json.dumps(stats,indent=2))
    if stats["all_integer_proofs"]!=30 or stats["negative_control_sat"]!=2 or stats["errors"]:
        raise AssertionError("INDEPENDENT_INTEGER_PROOF_VALIDATION_FAILED")
    return result

if __name__=="__main__":main()
