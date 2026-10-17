"""Independent GitHub Z3Py replay: frozen Q3D six-template finite decoder no-go.
This is not learned inference and not a claim about all neural systems.
It checks every original Horn rule only until the first SAT counterexample.
"""
import hashlib
import importlib.util
import itertools
import json
import pathlib
import time
import urllib.request

HERE=pathlib.Path(__file__).resolve().parent
GATE=HERE.parent/"q3c-variable-typed-program-20261017"/"typed_program_gate.py"
SPEC=importlib.util.spec_from_file_location("q3c_full_original_verify",GATE)
q=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(q)
REV="e5a86a1ad252fe1df75e06814769ec1d14540032"
CASES={
  "inc-max-2-base3-safe.smt2":"bed91ed9ddcac635626f150b683c23329e87e7ff8ccb1b39110745d5814cf889",
  "lists-3-inc-some-safe.smt2":"caca97e89ef8cd7a089d107d7b74971a50b5135deab68d268dc7f01b0a87786d",
}
TEMPLATES=("TRUE","BOOL_POS","BOOL_NEG","INT_EQ0","INT_GE0","MUT_EQ")
GRAMMAR_SHA="6dbf2c209ca31b31d9ce8aeeae4f75c8d900c002d1d4dc38c70d1e096b4d4ddf"

def ast(t):
    arg={"op":"arg","index":0}
    zero={"op":"int","value":0}
    if t=="TRUE":return {"op":"bool","value":True}
    if t=="BOOL_POS":return arg
    if t=="BOOL_NEG":return {"op":"not","args":[arg]}
    if t=="INT_EQ0":return {"op":"eq","args":[arg,zero]}
    if t=="INT_GE0":return {"op":"le","args":[zero,arg]}
    if t=="MUT_EQ":
        return {"op":"eq","args":[
            {"op":"selector","name":"~cur<Int>","arg":arg},
            {"op":"selector","name":"~ret<Int>","arg":arg}]}
    raise ValueError(t)

def matches(t,sort):
    return (t=="TRUE" or t.startswith("BOOL_") and sort=="Bool"
       or t.startswith("INT_") and sort=="Int"
       or t=="MUT_EQ" and sort=="~Mut<Int>")

def run():
    grammar_json=json.dumps({k:ast(k) for k in TEMPLATES},
                            sort_keys=True,separators=(",",":"))
    if hashlib.sha256(grammar_json.encode()).hexdigest()!=GRAMMAR_SHA:
        raise ValueError("FROZEN_GRAMMAR_CHANGED")
    results=[]
    for filename,sha in CASES.items():
        with urllib.request.urlopen(
            f"https://raw.githubusercontent.com/chc-comp/rust-horn/{REV}/{filename}",
            timeout=30) as request:
            raw=request.read()
        if hashlib.sha256(raw).hexdigest()!=sha:
            raise ValueError("PINNED_SOURCE_SHA256_MISMATCH")
        _,declarations,assertions=q.read_source(raw)
        names=list(declarations)
        choices=[[k for k in TEMPLATES if matches(k,declarations[name][0])]
                 for name in names]
        expected=1
        for ch in choices:expected*=len(ch)
        verdicts=[]
        start=time.perf_counter_ns()
        for assignment in itertools.product(*choices):
            program={"relations":{name:ast(kind) for name,kind in zip(names,assignment)}}
            witness=q.verify_original(raw,program)
            observed=witness["verdicts"]
            if witness["accepted"]:
                verdict="ACCEPTED_CERTIFICATE_FOUND"
            elif "sat" in observed:
                verdict="SAT_COUNTEREXAMPLE"
            else:
                verdict="UNKNOWN_OR_ERROR"
            verdicts.append(verdict)
        reported={
            "source":filename,"sha256":sha,
            "relation_count":len(names),"original_clause_count":len(assertions),
            "type_correct_candidate_count":expected,
            "enumerated":len(verdicts),
            "sat_counterexamples":verdicts.count("SAT_COUNTEREXAMPLE"),
            "complete_certificates":verdicts.count("ACCEPTED_CERTIFICATE_FOUND"),
            "unknown_or_error":verdicts.count("UNKNOWN_OR_ERROR"),
            "wall_ms":(time.perf_counter_ns()-start)/1e6,
            "decoder_expressivity_scope":"ONLY_THE_FROZEN_SIX_TYPED_AST_TEMPLATES",
        }
        if reported["enumerated"]!=expected or reported["unknown_or_error"]!=0:
            raise ValueError("INCOMPLETE_FINITE_EXHAUSTION")
        results.append(reported)
    receipt={
        "study":"Q3D original-source fixed six-template finite no-go",
        "model_forward_calls":0,
        "external_originals_already_opened":True,
        "source_upstream_revision":REV,
        "grammar_sha256":GRAMMAR_SHA,
        "Q1_Q7":"OPEN",
        "cases":results,
        "status":("FINITE_DECODER_NO_GO_PROVEN" if all(
            x["complete_certificates"]==0 and
            x["sat_counterexamples"]==x["type_correct_candidate_count"]
            for x in results) else "NO_GO_NOT_ESTABLISHED"),
        "nonclaims":"No bound on a different trained model/grammar; no frontier/economic win."
    }
    return receipt

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--out",required=True,type=pathlib.Path)
    o=p.parse_args()
    result=run()
    o.out.parent.mkdir(parents=True,exist_ok=True)
    o.out.write_text(json.dumps(result,indent=2)+"\n")
    print(result["status"],
          [(x["source"],x["sat_counterexamples"],x["complete_certificates"])
           for x in result["cases"]])
    if result["status"]!="FINITE_DECODER_NO_GO_PROVEN":
        raise SystemExit(2)
