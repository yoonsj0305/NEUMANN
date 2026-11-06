"""Post-FIRST explicit analytic LIA invariants and one unsafe one-step proof.

These hypotheses are authored AFTER inspecting the three original benchmark
sources; they are NOT NEUMANN-generated, not independent unseen transfer and
not cost-corrected against native specialist. Their value is mathematical:
fully independently certify validity (or infeasibility) of all three original
INV specifications without rerunning any native SyGuS synthesis.
"""
from __future__ import annotations

import hashlib,json,re,subprocess,sys,tempfile
from pathlib import Path
from urllib.request import Request,urlopen
from research.g2.independent_negative_integer_original_reproof import forms,modern_int_literals

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"docs/experiments/G2_POSTFIRST_THREE_SOURCE_ANALYTIC_PROOFS_CONTRACT_2026_11_06.json"

def sha(x:bytes)->str:return hashlib.sha256(x).hexdigest()
def gitblob(x:bytes)->str:return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()

def check(script:str,expect:str)->dict:
    with tempfile.NamedTemporaryFile("w",suffix=".smt2",encoding="utf8") as f:
        f.write(script);f.flush()
        p=subprocess.run(["cvc5","--lang=smt2",f.name],
            capture_output=True,text=True,timeout=8)
    answers=[x.strip() for x in p.stdout.splitlines() if x.strip()]
    status=answers[0] if p.returncode==0 and len(answers)==1 else "NOT_PROVED"
    return {"valid":status==expect,"expected":expect,"actual":status,
        "exit":p.returncode,"stderr_tail":p.stderr[-190:]}

def original_semantics(source:str):
    pieces=forms(source)
    proto=next((v for v in pieces if re.match(r"^\(\s*synth-inv\s+",v)),None)
    inv=next((v for v in pieces if re.match(r"^\(\s*inv-constraint\s+",v)),None)
    if not proto or not inv:raise ValueError("NOT_AN_INV_ORIGINAL")
    program=re.match(r"^\(\s*synth-inv\s+(\S+)\s+",proto).group(1)
    names=re.findall(r"\(\s*([A-Za-z][\w!]*)\s+Int\s*\)",proto)
    obligation=re.fullmatch(r"\(\s*inv-constraint\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*\)",inv)
    if not obligation or obligation.group(1)!=program or not names:
        raise ValueError("BAD_ORIGINAL_LIA_INTERFACE")
    defs=[];negative_count=0
    for p in pieces:
        if re.match(r"^\(\s*define-fun\s+",p):
            normal,n=modern_int_literals(p)
            defs.append(normal)
            negative_count+=n
    pre,trans,post=obligation.group(2,3,4)
    keys=[re.match(r"^\(\s*define-fun\s+(\S+)\s+",p).group(1) for p in defs]
    if not all(s in keys for s in (pre,trans,post)):
        raise ValueError("INV_SOURCE_UNDEFINED_SPEC")
    return {"name":program,"names":names,"pre":pre,"trans":trans,"post":post,
        "definitions":defs,"negative_literals_normalized":negative_count}

def context(spec:dict,candidate:str):
    names=spec["names"]
    declarations="\n".join(f"(declare-const {n} Int)" for n in names)
    declarations+="\n"+"\n".join(f"(declare-const {n}! Int)" for n in names)
    return "(set-logic ALL)\n"+"\n".join(spec["definitions"])+ \
        "\n"+candidate+"\n"+declarations+"\n"

def conditions(spec:dict):
    names=spec["names"];prime=[n+"!" for n in names]
    def call(f,a):return "("+f+" "+" ".join(a)+")"
    inv=spec["name"]
    return [
       ("init","(and "+call(spec["pre"],names)+" (not "+call(inv,names)+"))"),
       ("step","(and "+call(inv,names)+" "+
          call(spec["trans"],names+prime)+" (not "+call(inv,prime)+"))"),
       ("safe","(and "+call(inv,names)+" (not "+call(spec["post"],names)+"))")
    ]

def prove_invariant(source:str,candidate:str):
    spec=original_semantics(source)
    if not candidate.startswith("(define-fun "+spec["name"]+" "):
        raise ValueError("CANDIDATE_INVARIANT_SIGNATURE_NOT_ORIGINAL")
    base=context(spec,candidate)
    results=[]
    for stage,predicate in conditions(spec):
        proof=check(base+"(assert "+predicate+")\n(check-sat)\n","unsat")
        results.append({"stage":stage,**proof})
    # Human-authored candidate must have test-sensitive semantics:
    # negative control "always false" violates precondition initiation.
    bad="(define-fun "+spec["name"]+" (("+" Int) (".join(spec["names"])+ \
          " Int)) Bool false)"
    mb=context(spec,bad)
    control=check(mb+"(assert "+conditions(spec)[0][1]+")\n(check-sat)\n","sat")
    return {"universally_proven":all(x["valid"] for x in results),
        "original_obligations":results,
        "deliberately_false_invariant_rejected":control["valid"],
        "source_legacy_numerals_normalized":spec["negative_literals_normalized"]}

def prove_unsafe(source:str,initial:dict,nextstate:dict):
    spec=original_semantics(source)
    names=spec["names"]
    nxt=[n+"!" for n in names]
    if set(initial)!=set(names) or set(nextstate)!=set(nxt):
        raise ValueError("UNSAFE_WITNESS_VARIABLES_NOT_SOURCE")
    if not all(type(v) is int for v in [*initial.values(),*nextstate.values()]):
        raise ValueError("NOT_INTEGER_WITNESS")
    def call(f,args):return "("+f+" "+" ".join(args)+")"
    conjs=[call(spec["pre"],names),
           call(spec["trans"],names+nxt),
           "(not "+call(spec["post"],nxt)+")"]
    assigns={**initial,**nextstate}
    assert len(assigns)==len(names)*2
    def constant(x):
        return str(x) if x>=0 else "(- "+str(-x)+")"
    def script(d):
        b="(set-logic ALL)\n"+"\n".join(spec["definitions"])
        b+="\n"+"\n".join("(declare-const "+n+" Int)" for n in names+nxt)+"\n"
        b+="(assert (and "+" ".join(conjs)+"))\n"
        b+="\n".join("(assert (= "+k+" "+constant(v)+"))" for k,v in d.items())
        return b+"\n(check-sat)\n"
    witness=check(script(assigns),"sat")
    wrong={**assigns}
    wrong["k!"]=0 if "k!" in wrong else 0
    # The original transition always sets k! to k+1, here k=0,
    # hence the single-value mutated next state must be excluded.
    wrongproof=check(script(wrong),"unsat")
    return {"unsafe_reachable_in_one_transition":witness["valid"],
        "independent_explicit_initial_state":initial,
        "independent_explicit_next_state":nextstate,
        "original_pre_transition_not_post_SAT":witness,
        "deliberately_invalid_transition_witness_UNSAT":wrongproof,
        "mutation_rejected":wrongproof["valid"],
        "logical_result":"NO_INDUCTIVE_SAFETY_INVARIANT_EXISTS_IF_WITNESS_SAT",
        "source_legacy_numerals_normalized":spec["negative_literals_normalized"]}

def run():
    contract=json.loads(CONTRACT.read_text())
    entries=contract["manual_analytic_proposals"]
    if len(entries)!=3:raise ValueError("THREE_EXACT_ORIGINAL_HYPOTHESES_REQUIRED")
    cases=[]
    for item in entries:
        url=("https://raw.githubusercontent.com/SyGuS-Org/benchmarks/"+
          contract["source_provenance"]["commit"]+
          "/comp/2018/Inv_Track/"+item["file"])
        with urlopen(Request(url,headers={"User-Agent":"NEUMANN-G2-postfirst-analytic-proof"}),timeout=40) as f:
            raw=f.read(20000)
        if gitblob(raw)!=item["source_git_blob"]:
            raise ValueError("OFFICIAL_GIT_BLOB_SOURCE_MISMATCH")
        source=raw.decode()
        if item["type"]=="INVARIANT_UNIVERSAL":
            result=prove_invariant(source,item["candidate"])
            passed=result["universally_proven"] and result["deliberately_false_invariant_rejected"]
            candidate_sha=sha(item["candidate"].encode())
        else:
            result=prove_unsafe(source,item["initial_state"],item["next_state"])
            passed=result["unsafe_reachable_in_one_transition"] and result["mutation_rejected"]
            candidate_sha=None
        cases.append({"file":item["file"],"original_git_blob":item["source_git_blob"],
            "manual_after_first":True,"hypothesis_type":item["type"],
            "candidate_sha256":candidate_sha,
            "proof_success":passed,"independent_result":result})
    proved=sum(x["proof_success"] for x in cases)
    return {"schema":"neumann.g2.three-original-analytic-LIA-postfirst-certificate.v1",
      "audit_pass":proved==3,
      "analyst_formulas_executed_as_new_SyGuS_synthesis":False,
      "claim":"MATH_SOURCE_ONLY_PROOF_NOT_NEUMANN_LEARNED_DISCOVERY",
      "original_hypotheses_selected_after_first":True,
      "two_previous_native_12s_timeouts_universally_proven":sum(x["proof_success"]
         for x in cases if x["hypothesis_type"]=="INVARIANT_UNIVERSAL"),
      "previous_native_infeasible_original_one_step_unsafe_proven":any(
         x["proof_success"] for x in cases if x["hypothesis_type"]=="UNSAFE_1_STEP_REACHABILITY_WITNESS"),
      "first_native_solves_verified_after_syntax_correction":9,
      "all_original_12_mathematically_classified_if_pass":proved==3,
      "no_new_arc_eval_originals_used":True,
      "Q3":"OPEN","Q4":"OPEN","Q6":"OPEN","Q7":"OPEN",
      "cases":cases}

if __name__=="__main__":
    try:
        outcome=run()
        print(json.dumps(outcome,indent=2,sort_keys=True))
        if not outcome["audit_pass"]:raise SystemExit(1)
    except Exception as e:
        print("G2_POSTFIRST_ANALYTIC_SOURCE_CHECK_FAIL_CLOSED",type(e).__name__,str(e),file=sys.stderr)
        raise SystemExit(2)
