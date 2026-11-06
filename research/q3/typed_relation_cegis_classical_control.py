"""Source-free Q3 classical control: typed counterexample-driven relation discovery.

The solver is GIVEN ground traces and a verification interface for a synthetic
array update. It is NOT told the source variable, coefficient or offset.
It searches a fixed human-designed grammar, so neither learning nor open-ended
operator invention is claimed. Independent original CHC sources are untouched.
"""
from __future__ import annotations

import itertools
import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

SCHEMA = 'neumann.q3.classical-relational-cegis.source-free.v1'
SOURCES = ('left', 'right')
COEFFS = (-1, 1, 2)
BIASES = (-1, 0, 1)


@dataclass(frozen=True)
class Candidate:
    source: str
    coefficient: int
    bias: int


@dataclass(frozen=True)
class Observation:
    left: tuple[int, ...]
    right: tuple[int, ...]
    out: tuple[int, ...]
    cursor: int


def candidates():
    for symbol, a, b in itertools.product(SOURCES, COEFFS, BIASES):
        yield Candidate(symbol, a, b)


def consistent(candidate: Candidate, observations: list[Observation]) -> bool:
    for trace in observations:
        source = getattr(trace, candidate.source)
        for j in range(trace.cursor):
            if trace.out[j] != candidate.coefficient * source[j] + candidate.bias:
                return False
    return True


def expr(c: Candidate, k: str) -> str:
    return f'(+ (* {c.coefficient} (select {c.source} {k})) {c.bias})'


def smt_script(c: Candidate, actual: Candidate, *, corruption: bool = False) -> str:
    # The actual transition is supplied only to the separate verification side.
    write = expr(actual, 'i')
    if corruption:
        write = f'(+ {write} 1)'
    pred = f"""(define-fun Prefix ((left (Array Int Int)) (right (Array Int Int))
         (out (Array Int Int)) (cursor Int)) Bool
      (forall ((j Int)) (=> (and (<= 0 j) (< j cursor))
          (= (select out j) {expr(c, 'j')}))))"""
    header = """(set-logic AUFLIA)
(declare-const left (Array Int Int))
(declare-const right (Array Int Int))
(declare-const out (Array Int Int))
(declare-const i Int)
"""
    conditions = """(assert (>= i 0))
(assert (Prefix left right out i))
"""
    if corruption:
        conditions += '(assert (= i 0))\n'
    return (header + pred + '\n' + conditions
            + f'(assert (not (Prefix left right (store out i {write}) (+ i 1))))\n'
            + '(check-sat)\n')


def query_z3(script: str, timeout_s: float = 7.0):
    if not shutil.which('z3'):
        return 'UNKNOWN_NO_Z3', 0.0
    start = time.perf_counter_ns()
    try:
        res = subprocess.run(['z3', '-smt2', '-in'], input=script, text=True,
                             capture_output=True, timeout=timeout_s)
        lines = [x.strip() for x in res.stdout.splitlines() if x.strip()]
        result = lines[0] if res.returncode == 0 and len(lines) == 1 and lines[0] in ('sat', 'unsat') else 'UNKNOWN_CHECKER'
    except subprocess.TimeoutExpired:
        result = 'UNKNOWN_TIMEOUT'
    return result, round((time.perf_counter_ns() - start) / 1e6, 3)


def source_free_traces(program: Candidate) -> list[Observation]:
    # Only this synthetic demonstration oracle knows update semantics.
    # The proposer receives observations, not 'program' or task names.
    left = (8, -7, 6, -9)
    right = (0, 1, -2, 3)
    traces = []
    for cursor in (1, 2, 3, 4):
        out = tuple((program.coefficient * getattr(
            Observation(left, right, (), 0), program.source)[j] + program.bias)
            if j < cursor else 919 for j in range(4))
        traces.append(Observation(left, right, out, cursor))
    return traces


def h0_collision_for_program(actual: Candidate) -> bool:
    # Same destination observation, different source-dependent labels.
    initial = {'left': [0], 'right': [0]}
    output = [actual.bias]
    def truth(src):
        return output[0] == actual.coefficient * src[actual.source][0] + actual.bias
    different = {k: list(v) for k, v in initial.items()}
    different[actual.source][0] += 1
    return truth(initial) != truth(different)


def discover(observations: list[Observation], h0_collision: bool, verify):
    if not h0_collision:
        return None, {'verdict': 'ABSTAIN_NO_H0_COLLISION'}
    start = time.perf_counter_ns()
    tests = 0
    calls = 0
    proof_ms = 0.0
    for candidate in candidates():
        tests += 1
        if not consistent(candidate, observations):
            continue
        # The verifier is an injected interface. The candidate generator sees
        # only its verdict, never the transition program used by that verifier.
        calls += 1
        result, elapsed_ms = verify(candidate, False)
        proof_ms += elapsed_ms
        if result != 'unsat':
            continue
        negative, elapsed_ms = verify(candidate, True)
        proof_ms += elapsed_ms
        calls += 1
        if negative != 'sat':
            continue
        return candidate, {'verdict': 'SCOPED_CLASSICAL_PROOF',
            'grammar_candidates_tested': tests, 'z3_calls': calls,
            'z3_process_wall_ms': round(proof_ms, 3),
            'total_process_wall_ms': round((time.perf_counter_ns()-start)/1e6, 3),
            'proof_status': result, 'mutant_status': negative}
    return None, {'verdict': 'ABSTAIN_NO_INDUCTIVE_CANDIDATE',
        'grammar_candidates_tested': tests, 'z3_calls': calls,
        'z3_process_wall_ms': round(proof_ms, 3),
        'total_process_wall_ms': round((time.perf_counter_ns()-start)/1e6, 3)}


def run(out_dir: Path):
    if out_dir.exists():
        raise ValueError('NO_OVERWRITE_FIRST_RECEIPT')
    out_dir.mkdir(parents=True)
    cases = [('t0', Candidate('right', 1, 0)),
             ('t1', Candidate('right', 1, 1)),
             ('t2', Candidate('right', 2, 0))]
    rows = []
    for name, private_program in cases:
        observed = source_free_traces(private_program)
        proposal, receipt = discover(observed, h0_collision_for_program(private_program),
            lambda c, mutant: query_z3(smt_script(c, private_program, corruption=mutant)))
        rows.append({'case': name,
                     'H0_collision': h0_collision_for_program(private_program),
                     'proposed_typed_relation': None if proposal is None else vars(proposal),
                     'scope': 'SYNTHETIC_SOURCE_FREE_SAME_ARRAY_FORMALISM', **receipt})
    report = {'schema': SCHEMA, 'task_count': len(rows),
              'classical_proofs': sum(x['verdict']=='SCOPED_CLASSICAL_PROOF' for x in rows),
              'trained_model_used': False, 'grammar_human_designed': True,
              'original_external_CHC_checked': False, 'cross_formalism_transfer': False,
              'Q3': 'OPEN', 'Q4': 'OPEN', 'Q6': 'OPEN', 'Q7': 'OPEN', 'cases': rows}
    (out_dir/'classical_control.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps(report, indent=2, sort_keys=True))
    if report['classical_proofs'] != report['task_count']:
        raise RuntimeError('CLASSICAL_CONTROL_PROOF_FAILED_OR_UNKNOWN')
    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
