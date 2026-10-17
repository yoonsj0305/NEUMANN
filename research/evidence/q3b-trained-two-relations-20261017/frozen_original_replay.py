"""Frozen Q3B 40-weight synthetic two-predicate original-rule replay.

Reads the actual trained checkpoint; no model fitting or external benchmark.
The local archive includes complete original training, first receipts and
independent source-AST reparse. This GitHub replay uses the *same Z3 backend*.
"""
import ctypes as C
import hashlib
import json
import random
from ctypes.util import find_library
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKPOINT_SHA256 = "2d557d5d92f4627749ded23c762ec0faf343ee20db679cee0b3222f15bf1b360"
COUNT = 24
SEED = 20261017
def num(x):return str(x) if x >= 0 else f"(- {-x})"

def rules(a,b,p,q):
    a,b,p,q=map(num,(a,b,p,q))
    return [
       "(forall ((x Int)(y Int)) (=> (and (= x 0) (= y 0)) (A x y)))",
       f"(forall ((x Int)(y Int)) (=> (A x y) (A (+ x {a}) (+ y {b}))))",
       f"(forall ((x Int)(y Int)) (=> (A x y) (B (+ x {p}) (+ y {q}))))",
       f"(forall ((x Int)(y Int)) (=> (B x y) (B (+ x {a}) (+ y {b}))))",
       f"(forall ((x Int)(y Int)) (=> (and (B x y) (= y {q}) (not (= x {p}))) false))",
    ]

def query(original,w):
    a,b,c,d,k=map(int,w)
    definitions=(
        f"(define-fun A ((x Int)(y Int)) Bool (= (+ (* {num(a)} x) (* {num(b)} y)) 0))\n"
        f"(define-fun B ((x Int)(y Int)) Bool (= (+ (* {num(c)} x) (* {num(d)} y)) {num(k)}))\n"
    )
    return "(set-logic ALL)\n"+definitions+"(assert (not "+original+"))\n(check-sat)\n"

def native(q):
    lib=C.CDLL(find_library("z3"))
    lib.Z3_mk_config.restype=C.c_void_p
    lib.Z3_mk_context.argtypes=[C.c_void_p]
    lib.Z3_mk_context.restype=C.c_void_p
    lib.Z3_del_config.argtypes=[C.c_void_p]
    lib.Z3_del_context.argtypes=[C.c_void_p]
    lib.Z3_eval_smtlib2_string.argtypes=[C.c_void_p,C.c_char_p]
    lib.Z3_eval_smtlib2_string.restype=C.c_char_p
    lib.Z3_get_error_code.argtypes=[C.c_void_p]
    lib.Z3_get_error_code.restype=C.c_int
    cfg=lib.Z3_mk_config()
    ctx=lib.Z3_mk_context(cfg)
    lib.Z3_del_config(cfg)
    try:
        answer=(lib.Z3_eval_smtlib2_string(ctx,q.encode()) or b"").decode().strip()
        return answer if lib.Z3_get_error_code(ctx)==0 else "ERROR"
    finally:lib.Z3_del_context(ctx)

def run():
    raw=(HERE/"frozen_checkpoint.json").read_bytes()
    if hashlib.sha256(raw).hexdigest()!=CHECKPOINT_SHA256:
        raise ValueError("CHECKPOINT_BYTES_CHANGED")
    frozen=json.loads(raw)
    W=frozen["weights"]
    if len(W)!=5 or any(len(row)!=8 for row in W):
        raise ValueError("WRONG_MODEL_SHAPE")
    rng=random.Random(SEED+17)
    cases=[]
    for i in range(COUNT):
        a=rng.choice([-8,-7,-6,5,6,7,8])
        b=rng.randint(1,8);p=rng.randint(-9,9);q=rng.randint(-9,9)
        x=[a,b,p,q,a*p,a*q,b*p,b*q]
        proposal=[round(sum(c*t for c,t in zip(row,x))) for row in W]
        classical=[-b,a,-b,a,-b*p+a*q]
        original=rules(a,b,p,q)
        checked=[native(query(c,proposal)) for c in original]
        exact=[native(query(c,classical)) for c in original]
        ablated=native(query(original[-1],[0,0,0,0,0]))
        if proposal!=classical or checked!=["unsat"]*5 or exact!=["unsat"]*5 or ablated!="sat":
            raise AssertionError("Q3B_FROZEN_MODEL_PROOF_OR_CONTROL_FAILED")
        cases.append({"case":i,"original_rule_checks":checked,
           "source_bytes_sha256":hashlib.sha256(("".join(original)).encode()).hexdigest()})
    return {"status":"FROZEN_Q3B_SYNTHETIC_PROOF_REPLAY_PASS",
         "trained_parameters":40,"actual_train_closure_evaluations":33,
         "synthetic_cases":COUNT,"learned_certified_original_rules":5*COUNT,
         "classical_certified_original_rules":5*COUNT,"zero_head_safety_rejections":COUNT,
         "source_group":"RESEARCHER_AUTHORED_SYNTHETIC_ONLY",
         "trained_model_classical_advantage":False,"global_q1_q7":"OPEN",
         "cases":cases}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=run()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+"\n")
    print(result["status"],result["learned_certified_original_rules"],result["global_q1_q7"])
