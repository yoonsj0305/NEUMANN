"""CORE-36: identical-goal fixed-probe information impossibility. No ML claims.
Use native Z3; reject every UNKNOWN, parser error or missing solver.
"""
import ctypes
import ctypes.util
import json
import time


def solve(smt):
    name = ctypes.util.find_library('z3')
    if not name:
        raise RuntimeError('native Z3 required')
    z = ctypes.CDLL(name)
    z.Z3_mk_config.restype = ctypes.c_void_p
    z.Z3_mk_context.argtypes = [ctypes.c_void_p]
    z.Z3_mk_context.restype = ctypes.c_void_p
    z.Z3_eval_smtlib2_string.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    z.Z3_eval_smtlib2_string.restype = ctypes.c_char_p
    z.Z3_del_context.argtypes = [ctypes.c_void_p]
    z.Z3_del_config.argtypes = [ctypes.c_void_p]
    cfg = z.Z3_mk_config()
    ctx = z.Z3_mk_context(cfg)
    try:
        value = z.Z3_eval_smtlib2_string(ctx, smt.encode())
        result = value.decode().strip() if value else ''
        if result not in ('sat', 'unsat'):
            raise RuntimeError('UNPROVEN: ' + result[:200])
        return result
    finally:
        z.Z3_del_context(ctx)
        z.Z3_del_config(cfg)


def clauses(k, branch):
    d = '0' if branch == 0 else f'(ite (>= n {k}) 2 0)'
    return [
        '(R 0 0)',
        f'(forall ((n Int) (s Int)) (=> (and (R n s) (>= n 0)) (R (+ n 1) (+ s 1 {d}))))',
        f'(forall ((n Int) (s Int)) (=> (and (R n s) (= n {k+2}) (= s {k+4})) false))',
    ]


def invariant(k, branch):
    return '(and (>= n 0) (= s n))' if branch == 0 else (
        f'(and (>= n 0) (= s (+ n (* 2 (ite (>= n {k}) (- n {k}) 0)))))'
    )


def interpretation(k, branch):
    return f'(set-logic ALL)\n(define-fun R ((n Int) (s Int)) Bool {invariant(k, branch)})\n'


def run_case(k):
    if not 1 <= k <= 256:
        raise ValueError('k out of test range')
    assert all(1 == 1 + (2 if n >= k else 0) for n in range(k))
    assert clauses(k, 0)[0] == clauses(k, 1)[0]
    assert clauses(k, 0)[2] == clauses(k, 1)[2]
    positives = {}
    negatives = {}
    for branch in (0, 1):
        prefix = interpretation(k, branch)
        for index, c in enumerate(clauses(k, branch)):
            key = f'P{branch}_C{index+1}'
            positives[key] = solve(prefix + f'(assert (not {c}))\n(check-sat)')
        # Substituted intentionally reachable goal is a real SAT witness.
        reachable = k+2 if branch == 0 else k+6
        negatives[f'P{branch}_reachable'] = solve(
            prefix + f'(assert (R {k+2} {reachable}))\n(check-sat)')
        wrong = clauses(k, 1-branch)[1]
        negatives[f'P{branch}_wrong_transition'] = solve(
            prefix + f'(assert (not {wrong}))\n(check-sat)')
    # Every ground instance follows from one of the original quantified rules.
    ground = ['(set-logic QF_UFLIA)', '(declare-fun R (Int Int) Bool)', '(assert (R 0 0))']
    ground += [f'(assert (=> (R {n} {n}) (R {n+1} {n+1})))' for n in range(k+1)]
    ground += [f'(assert (=> (R {k+1} {k+1}) (R {k+2} {k+4})))',
               f'(assert (not (R {k+2} {k+4})))', '(check-sat)']
    contradiction = solve('\n'.join(ground))
    assert set(positives.values()) == {'unsat'}
    assert set(negatives.values()) == {'sat'}
    assert contradiction == 'unsat'
    return {'k': k, 'original_clause_checks': positives,
            'mutations': negatives, 'no_shared_relation': contradiction}


def main():
    before = time.perf_counter_ns()
    cases = [run_case(k) for k in [1, 3, 17, 29, 64]]
    receipt = {'study':'CORE-36', 'status':'SYNTHETIC_MATHEMATICAL_NO_GO_PASS',
               'same_goal':True, 'z3_original_negations_unsat':30,
               'joint_system_ground_instance_unsat':5,
               'invalid_candidate_checks_sat':20, 'learned_model_forwards':0,
               'Q1_Q7':'OPEN', 'cases':cases,
               'wall_ns':time.perf_counter_ns()-before}
    with open('core36_receipt.json','w',encoding='utf-8') as f:
        json.dump(receipt,f,indent=2)
    print(json.dumps({k:v for k,v in receipt.items() if k!='cases'},indent=2))


if __name__ == '__main__':
    main()
