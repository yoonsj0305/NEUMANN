"""Exact affine source-dependency control for frozen H0 semantic OOD failures.

Post-FIRST deterministic classical check. No learned weights, original CHC,
new samples or training. Unsupported types/operations return UNKNOWN.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

CONST = ('constant',)


class OutsideAffineGrammar(ValueError):
    pass


def clean(terms: dict[tuple, int]) -> dict[tuple, int]:
    return {k: v for k, v in terms.items() if v != 0}


def add(x: dict[tuple, int], y: dict[tuple, int]) -> dict[tuple, int]:
    z = dict(x)
    for k, v in y.items():
        z[k] = z.get(k, 0) + v
    return clean(z)


def scale(x: dict[tuple, int], factor: int) -> dict[tuple, int]:
    return clean({k: v * factor for k, v in x.items()})


def parse(tree, *, allow_select: bool = True) -> dict[tuple, int]:
    if not isinstance(tree, list) or not tree or not isinstance(tree[0], str):
        raise OutsideAffineGrammar('INVALID_AST')
    op = tree[0]
    if op == 'const' and len(tree) == 2 and type(tree[1]) is int:
        return clean({CONST: tree[1]})
    if op == 'var' and len(tree) == 2 and tree[1] in ('i', 'b'):
        return {('var', tree[1]): 1}
    if op == 'add' and len(tree) == 3:
        return add(parse(tree[1], allow_select=allow_select),
                   parse(tree[2], allow_select=allow_select))
    if op == 'neg' and len(tree) == 2:
        return scale(parse(tree[1], allow_select=allow_select), -1)
    if op == 'mul' and len(tree) == 3:
        left, right = tree[1], tree[2]
        if isinstance(left, list) and len(left) == 2 and left[0] == 'const' and type(left[1]) is int:
            return scale(parse(right, allow_select=allow_select), left[1])
        if isinstance(right, list) and len(right) == 2 and right[0] == 'const' and type(right[1]) is int:
            return scale(parse(left, allow_select=allow_select), right[1])
        raise OutsideAffineGrammar('NON_AFFINE_MULTIPLICATION')
    if op == 'select' and len(tree) == 3 and tree[1] == 'S' and allow_select:
        idx = parse(tree[2], allow_select=False)
        idx_key = tuple(sorted(idx.items(), key=lambda kv: repr(kv[0])))
        return {('select', idx_key): 1}
    raise OutsideAffineGrammar('UNSUPPORTED_OR_ILL_TYPED_OP')


def dependency(tree):
    started = time.perf_counter_ns()
    try:
        coeffs = parse(tree)
    except OutsideAffineGrammar as exc:
        return {'verdict': 'UNKNOWN_UNSUPPORTED', 'reason': str(exc),
                'runtime_ms': round((time.perf_counter_ns()-started)/1e6, 5)}
    required = any(key[0] == 'select' for key in coeffs)
    return {'verdict': 'SOURCE_DEPENDENT' if required else 'SOURCE_INDEPENDENT',
            'canonical_nonzero_terms': len(coeffs),
            'source_coefficient_terms': sum(k[0]=='select' for k in coeffs),
            'runtime_ms': round((time.perf_counter_ns()-started)/1e6, 5)}


def audit(root: Path, out: Path):
    # Keep this SMT implementation separate from our exact affine reducer.
    from research.q3.collision_allindex_semantic_readonly import full_collision_script, check
    a = json.loads((root/'docs/experiments/Q3_COUNTEREXAMPLE_GROWER_FIRST_PREREG_2026_11_06.json').read_text())
    b = json.loads((root/'docs/experiments/Q3_CEX_SEMANTIC_CANCELLATION_FIRST_PREREG_2026_11_06.json').read_text())
    rows = []
    for cohort, tasks in (('previous_8_opened', a['heldout']['examples']),
                          ('adversarial_6_opened', b['preregistered_heldout_not_in_initial_first'])):
        for idx, task in enumerate(tasks):
            proposed = dependency(task['expr'])
            independent = check(full_collision_script(task))
            actual = independent['verdict']
            expected = {'sat': 'SOURCE_DEPENDENT', 'unsat': 'SOURCE_INDEPENDENT'}.get(actual)
            rows.append({'cohort': cohort, 'index': idx, 'analytic': proposed,
                         'SMT_exact_semantic_verdict': actual,
                         'agreement': expected is not None and proposed['verdict'] == expected,
                         'SMT_process_ms': independent['wall_ms']})
    report = {'schema': 'neumann.q3.postfirst-affine-semantic-control.v1',
              'sourcefree_opened_cases': len(rows),
              'analytic_matches_independent_Z3': sum(x['agreement'] for x in rows),
              'analytic_ms_sum': round(sum(x['analytic']['runtime_ms'] for x in rows),5),
              'SMT_ms_sum': round(sum(x['SMT_process_ms'] for x in rows),3),
              'SMT_reference_calls': len(rows),
              'analytic_Z3_calls': 0,
              'new_model_training': False, 'trained_self_invention': False,
              'external_original_CHC_solves': 0, 'Q3': 'OPEN', 'Q4': 'OPEN', 'Q6': 'OPEN',
              'rows': rows}
    out.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}, indent=2, sort_keys=True))
    if report['analytic_matches_independent_Z3'] != len(rows):
        raise RuntimeError('POSTFIRST_AFFINE_ANALYTIC_MISMATCH_OR_UNKNOWN')
    return report


if __name__ == '__main__':
    import argparse
    a=argparse.ArgumentParser()
    a.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    a.add_argument('--out', type=Path, required=True)
    p=a.parse_args()
    audit(p.root, p.out)
