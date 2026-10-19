"""Source-conditioned original SyGuS safety proof command line (Q3 engineering only).
No answer-key, target labels, training, or file-name-specific proof selection.
Frozen algorithms Q3V4/Q3V6 are imported unchanged from prior first studies.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
import z3

HERE=Path(__file__).resolve().parent
RESEARCH=HERE.parent/"research"/"evidence"
sys.path.insert(0,str(RESEARCH/"q3v6-lazy-specialist-20261019"))
from first_proof_gated_lazy_fallback import (
    measured_solve, sexprs, extract_mixed_original, native_original_relations,
    check_parity, check_formula, source_proof, houdini,
    all_exact_branch_updates, common_kernels, actual_relation,
    prove_candidate_relation, EXPECTED,
)

MAX_INPUT_BYTES=512*1024
ALLOWED_EXTENSION=".sl"

def _sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def _fail(reason,path=None):
    return {"schema":"neumann.q3-source-proof-cli.v1","status":"ABSTAIN",
            "reason":reason,"source_basename":path.name if path else None,
            "global_Q3":"OPEN","learned_new_operator":False}

def _source_invariant(selected,src,native):
    """Re-derive from source with same frozen mechanisms, never use a gold label."""
    if selected=="POST_ONLY":
        return native["post"]
    if selected=="OCTAGON_HOUDINI":
        if src["num_bool"]:raise ValueError("BOOL_STATE_NOT_IN_OCTAGON")
        i,_,_,_=houdini(native["pre"],native["trans"],src["now"],src["next"])
        return i
    if selected=="BRANCH_AFFINE_NULLSPACE":
        branches=all_exact_branch_updates(src)
        terms=[]
        for candidate in common_kernels(branches,src):
            r=actual_relation(candidate,src["now"])
            if prove_candidate_relation(src,native,r)["source_certified"]:
                terms.append(r)
        return z3.And(native["post"],*terms)
    raise ValueError("NO_SOURCE_DERIVED_INVARIANT_TO_EXPORT")

def _obligations(inv,src,native):
    nxt=z3.substitute(inv,*list(zip(src["now"],src["next"])))
    return {
        "initial":z3.And(native["pre"],z3.Not(inv)),
        "consecution":z3.And(inv,native["trans"],z3.Not(nxt)),
        "post":z3.And(inv,z3.Not(native["post"])),
    }

def prove_source(path):
    start=time.perf_counter_ns()
    path=Path(path)
    if path.suffix != ALLOWED_EXTENSION:
        return _fail("UNSUPPORTED_SOURCE_SUFFIX",path)
    if not path.is_file() or path.is_symlink():
        return _fail("SOURCE_NOT_REGULAR_FILE",path)
    if path.stat().st_size>MAX_INPUT_BYTES:
        return _fail("SOURCE_EXCEEDS_SIZE_CAP",path)
    data=path.read_bytes()
    rec={"schema":"neumann.q3-source-proof-cli.v1",
         "source_basename":path.name,"source_sha256":_sha(data),
         "source_bytes":len(data),"status":"NOT_EVALUATED",
         "neural_model_calls":0,"oracle_answers_supplied":False,
         "global_Q3":"OPEN","learned_new_operator":False,
         "proof_routes_attempted":[]}
    try:
        parsed=sexprs(data)
        src=extract_mixed_original(parsed)
        native=native_original_relations(parsed,src)
        native.update({"now":src["now"],"next":src["next"]})
        parity=check_parity(src,native)
        rec["independent_native_custom_parser_xor"]=parity
        if len(parity)!=3 or any(x!="unsat" for x in parity.values()):
            raise ValueError("NATIVE_CUSTOM_ORIGINAL_SEMANTIC_PARITY_NOT_UNSAT")
        if check_formula(native["pre"])!="sat":
            raise ValueError("ORIGINAL_PRE_NOT_SAT_OR_UNKNOWN")
        if check_formula(z3.Not(native["post"]))!="sat":
            raise ValueError("ORIGINAL_NOT_POST_NOT_SAT_OR_UNKNOWN")
        found=measured_solve(src,native)
        rec["proof_routes_attempted"]=found["attempts"]
        rec["selected_route"]=found["selected"]
        rec["verifier_authority"]="ORIGINAL_NATIVE_SYGUS_PRE_TRANS_POST"
        kind=found["certificate_kind"]
        if kind=="NATIVE_SOURCE_EXACT_ORIGINAL_3VC":
            invariant=_source_invariant(found["selected"],src,native)
            check=source_proof(invariant,native)
            if not check["accepted"] or check["vcs"]!=EXPECTED:
                raise ValueError("INDEPENDENT_RECONSTRUCTED_ORIGINAL_3VC_NOT_VALID")
            rec["original_three_vc"]=check["vcs"]
            rec["invariant_sexpr"]=invariant.sexpr()
            rec["invariant_sha256"]=_sha(invariant.sexpr().encode())
            smt2={}
            for name,bad in _obligations(invariant,src,native).items():
                solver=z3.Solver()
                solver.set(timeout=2500)
                solver.add(bad)
                if solver.check()!=z3.unsat:
                    raise ValueError("EXPORTED_ORIGINAL_"+name+"_NOT_UNSAT")
                script=solver.to_smt2()
                smt2[name]={"query":script,"sha256":_sha(script.encode()),
                    "expected":"unsat"}
            rec["original_bad_condition_smt2"]=smt2
            rec["status"]="ORIGINAL_SOURCE_THREE_VC_CERTIFIED"
            rec["certificate_scope"]="EXACT_NATIVE_SOURCE_INVARIANT_AND_3_INDUCTIVE_VCS"
        elif kind=="SOURCE_ONLY_Z3_SPACER_UNSAT" and found["fallback_spacer_status"]=="unsat":
            rec["status"]="ORIGINAL_SOURCE_ONLY_SPACER_UNSAT"
            rec["certificate_scope"]="SOURCE_ONLY_SOLVER_DECISION_NO_EXPORTED_INVARIANT"
            rec["original_three_vc"]=None
            rec["invariant_sexpr"]=None
            rec["original_bad_condition_smt2"]=None
        else:
            rec["status"]="ABSTAIN"
            rec["reason"]="NO_USABLE_ORIGINAL_SOURCE_CERTIFICATE"
        rec["unconditional_specialist_called"]=False
        rec["fallback_spacer_called"]=(kind=="SOURCE_ONLY_Z3_SPACER_UNSAT")
    except Exception as exc:
        rec["status"]="ABSTAIN"
        rec["reason"]=type(exc).__name__+":"+str(exc)[:170]
        rec.pop("original_bad_condition_smt2",None)
        rec.pop("invariant_sexpr",None)
    rec["total_wall_ms"]=round((time.perf_counter_ns()-start)/1e6,3)
    return rec

def replay_exported_queries(receipt):
    """Read-only model-free recheck of shipped solver obligations, NEVER trust a flag."""
    if receipt.get("status")!="ORIGINAL_SOURCE_THREE_VC_CERTIFIED":
        return False
    obligations=receipt.get("original_bad_condition_smt2")
    if type(obligations)!=dict or set(obligations)!=set(EXPECTED):
        return False
    for row in obligations.values():
        try:
            script=row["query"]
            if _sha(script.encode())!=row["sha256"] or row["expected"]!="unsat":
                return False
            solver=z3.Solver()
            solver.set(timeout=2500)
            solver.from_string(script)
            if solver.check()!=z3.unsat:
                return False
        except Exception:
            return False
    return True


def replay_original_source_bound(path, receipt):
    """Replay a prior 3VC receipt against the ACTUAL original source bytes.

    The legacy replay_exported_queries() checks only that three arbitrary
    queries are UNSAT. This strict method recomputes actual Pre, Trans, Post,
    source-conditioned invariant and all three real obligations from the
    trusted original input and requires exact bytes. It cannot independently
    prove *other* syntactically different but valid invariants; deliberately
    fail-closed for archival reproducibility.

    This is independent of the UNTRUSTED receipt, but it uses the SAME
    frozen generator and native verifier; not a disjoint proof assistant.
    """
    if type(receipt) is not dict:
        return False
    try:
        path=Path(path)
        if path.is_symlink() or not path.is_file() or path.suffix!=".sl":
            return False
        data=path.read_bytes()
        if len(data)>MAX_INPUT_BYTES:
            return False
        if receipt.get("source_sha256")!=_sha(data):
            return False
        if receipt.get("status")!="ORIGINAL_SOURCE_THREE_VC_CERTIFIED":
            return False
        if not replay_exported_queries(receipt):
            return False
        reconstructed=prove_source(path)
        if reconstructed.get("status")!="ORIGINAL_SOURCE_THREE_VC_CERTIFIED":
            return False
        for key in (
            "source_sha256","source_bytes","selected_route",
            "verifier_authority","certificate_scope",
            "invariant_sexpr","invariant_sha256",
            "original_three_vc","independent_native_custom_parser_xor"
        ):
            if reconstructed.get(key)!=receipt.get(key):
                return False
        expected=reconstructed.get("original_bad_condition_smt2")
        received=receipt.get("original_bad_condition_smt2")
        if type(expected) is not dict or type(received) is not dict:
            return False
        if set(expected)!=set(("initial","consecution","post")) or set(received)!=set(expected):
            return False
        for key in ("initial","consecution","post"):
            if expected[key].get("expected")!="unsat" or received[key].get("expected")!="unsat":
                return False
            # Z3 serializer may reorder let-bindings/named assertions between
            # two executions. Parse each exact query and compare its RAW
            # assertion AST structure. Never use equivalence/XOR here: two
            # UNSAT conditions would all be equivalent to arbitrary false!
            recorded=z3.Solver()
            recorded.from_string(received[key]["query"])
            reconstructed=z3.Solver()
            reconstructed.from_string(expected[key]["query"])
            actual_assertions=[term.sexpr() for term in recorded.assertions()]
            source_assertions=[term.sexpr() for term in reconstructed.assertions()]
            if actual_assertions!=source_assertions or not actual_assertions:
                return False
        return True
    except Exception:
        return False


def main():
    p=argparse.ArgumentParser(description="Safe source-to-invariant proof; never asserts global Q3.")
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    result=prove_source(args.source)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":result["status"],
          "selected":result.get("selected_route"),
          "replay_3vc":replay_exported_queries(result),
          "original_source_sha256":result.get("source_sha256")}))
    raise SystemExit(0 if (
        (result["status"]=="ORIGINAL_SOURCE_THREE_VC_CERTIFIED"
         and replay_exported_queries(result))
        or result["status"]=="ORIGINAL_SOURCE_ONLY_SPACER_UNSAT"
    ) else 2)
if __name__=="__main__":
    main()
