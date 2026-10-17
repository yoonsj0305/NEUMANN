"""Independent 6-original-Horn information impossibility certificate.

Researcher-created two-case adversarial system, not a hidden benchmark.
Single shared relation interpreted in both original sources => UNSAT.
This proof does not use neural weights, candidate template, teacher label, or
the assistant's hand-written reachability assertion. Z3 executes all six
original quantified clauses directly.
"""
import ctypes as ct
import hashlib
import json
import os
import time
from pathlib import Path

OUT=Path(os.environ.get("FGSR_RESULT","frozen_17_probe_theorem_receipt.json"))

def source(which):
    sym="|PhaseUnknownA|" if which==0 else "|OtherIndependentSystem|"
    bump="1" if which==0 else "(+ 1 (ite (>= n 17) 1 0))"
    forbidden="19" if which==0 else "18"
    return (
        "(set-logic HORN)\n"
        f"(declare-fun {sym} (Int Int) Bool)\n"
        f"(assert (forall ((s Int)) (=> (= s 0) ({sym} 0 s))))\n"
        "(assert (forall ((n Int)(s Int)(n1 Int)(s1 Int))\n"
        f"(=> (and ({sym} n s) (>= n 0) (= n1 (+ n 1)) "
        f"(= s1 (+ s {bump}))) ({sym} n1 s1))))\n"
        "(assert (forall ((n Int)(s Int))\n"
        f"(=> (and ({sym} n s) (= n 18) (= s {forbidden})) false)))\n"
    )

def solver_check(text):
    import z3
    from pathlib import Path
    lib=ct.CDLL(str(Path(z3.__file__).parent/"lib/libz3.so"))
    lib.Z3_mk_config.restype=ct.c_void_p
    lib.Z3_mk_context.argtypes=[ct.c_void_p];lib.Z3_mk_context.restype=ct.c_void_p
    lib.Z3_del_config.argtypes=[ct.c_void_p];lib.Z3_del_context.argtypes=[ct.c_void_p]
    lib.Z3_eval_smtlib2_string.argtypes=[ct.c_void_p,ct.c_char_p]
    lib.Z3_eval_smtlib2_string.restype=ct.c_char_p
    cfg=lib.Z3_mk_config();ctx=lib.Z3_mk_context(cfg);lib.Z3_del_config(cfg)
    try:return (lib.Z3_eval_smtlib2_string(ctx,text.encode()) or b"").decode().strip()
    finally:lib.Z3_del_context(ctx)

def canonical_asserts(s,original):
    import z3
    forms=z3.parse_smt2_string(s)
    if len(forms)!=3 or any(not z3.is_quantifier(q) for q in forms):
        raise ValueError("not three original universal clauses")
    # Preserve original clause logic; only rename the uninterpreted predicate.
    expected=f"|{'PhaseUnknownA' if original==0 else 'OtherIndependentSystem'}|"
    return "\n".join(
        x.replace(expected,"|SharedInvariant|")
        for x in s.splitlines() if False
    ) if False else (
        s.replace(expected,"|SharedInvariant|")
        .replace("(set-logic HORN)","")
        .replace("(declare-fun |SharedInvariant| (Int Int) Bool)","")
    )

def main():
    t=time.perf_counter_ns()
    a,b=source(0),source(1)
    d=[sum(1+(1 if i>=17 else 0) for i in range(17))]
    assert d==[17]
    for k in range(17):
        assert 1==(1+(1 if k>=17 else 0))
    joint=("(set-logic HORN)\n"
           "(declare-fun |SharedInvariant| (Int Int) Bool)\n"
           +canonical_asserts(a,0)+"\n"
           +canonical_asserts(b,1)+"\n(check-sat)\n")
    outcome=solver_check(joint)
    if outcome!="unsat":raise RuntimeError("joint original six-Horn not certified "+outcome)
    report={
        "status":"SIX_AUTHENTIC_SYNTHETIC_ORIGINAL_CLAUSES_COMMON_INVARIANT_UNSAT",
        "source_category":"RESEARCHER_CREATED_ADVERSARIAL_PAIR",
        "prereg_commit":"6989ef56445d86aed8ec2b437d195d3688f83531",
        "source_sha256":[hashlib.sha256(a.encode()).hexdigest(),hashlib.sha256(b.encode()).hexdigest()],
        "shared_source_predicate_count":1,
        "original_quantified_horn_assertions":6,
        "shared_relation_joint_result":outcome,
        "identical_first_17_deltas":True,
        "deltas_at_index_17":[1,2],
        "exact_reachable_state_at_n18":[18,19],
        "model_training_in_this_study":False,
        "new_operator_invented_by_neural_model":False,
        "global_q1_q7":"OPEN",
        "elapsed_wall_ms":round((time.perf_counter_ns()-t)/1e6,3)
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2)+"\n")
    print("COMMON_17_PROBE_INVARIANT_IMPOSSIBLE",outcome)
    print("GLOBAL_Q1_Q7",report["global_q1_q7"])
if __name__=="__main__":main()
