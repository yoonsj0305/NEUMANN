"""Opt-in reachability-guided, fold-constrained cell Update synthesis (development only; default unchanged)."""
import json
import pathlib
import sys
import time

sys.path.insert(0, ".")
sys.path.insert(0, "research/q3")
import env_listroutines as E
from neumann1 import active as ac, latent as lt


def test_defaults_leave_the_legacy_synthesis_untouched():
    cfg = lt.Cfg(subst=True, latent=True)
    assert cfg.accept is None and cfg.reach_probes is None
    assert ac.FOLD_REACH_SYNTH is False


def test_iter_covers_yields_every_leaf_alternative_of_the_same_coverage():
    full = 0b111
    pieces = [(0b011, ("value", "a1")), (0b011, ("value", "a2")), (0b100, ("value", "b1"))]
    preds = [(0b011, "p")]
    nodes = list(lt._iter_covers(pieces, preds, full, time.process_time() + 5))
    assert ("case", "p", ("value", "a1"), ("value", "b1")) in nodes
    assert ("case", "p", ("value", "a2"), ("value", "b1")) in nodes


def test_fold_mode_returns_the_first_fit_when_it_already_folds_correctly():
    rows = [(((), 3), (3,)), (((3,), 5), (3, 5)), (((3, 5), 1), (3, 5, 1)), (((1,), 2), (1, 2)),
            (((4, 2), 7), (4, 2, 7))]
    task = {"id": "u", "in_types": [ac.T_L, ac.T_I], "out_type": ac.T_L, "train": rows, "test": []}
    first = lt.solve(task, time.process_time() + 5, ac._inv(), lt.Cfg(subst=True, latent=True))
    sol, info = lt.solve_fold(task, time.process_time() + 5, ac._inv(), lambda s: 0, lambda s: [])
    assert first is not None and repr(sol) == repr(first)
    assert info["tested"] == 1 and info["source"] == "first" and info["errors"] == 0


def test_fold_constrained_search_repairs_a_frozen_fold_failure_deterministically():
    """rotate-k(k=1) | identify-geq-k(k=2): the legacy first fit folds one initial example wrongly; the same
    enumeration continued under reachable-state refinement finds an Update that folds all of them (no query)."""
    import vclock
    import reachable_state_diagnosis_dev as D
    import fold_reach_replay_dev as F
    name = "rotate-k(k=1) | identify-geq-k(k=2)"
    rec = next(json.loads(l) for l in pathlib.Path("docs/experiments/dev/update_snapshots/lr.jsonl").read_text()
               .splitlines() if l.strip() and json.loads(l)["name"] == name)
    snap = D.Snapshot(rec["failure"])
    spec = next(s for s in E.tasks() if s.name == name)
    examples = E.Env(spec, 0, budget=60).initial()
    z = F.z_from_table(snap)
    ac._inv()
    clock = vclock.install(vclock.VirtualTime(), extra=(sys.modules[__name__],))
    try:
        rows = D.rows_of(snap.trans, 0)
        a, _ = ac.synth_cells(snap.in_types, rows, time.process_time() + 5)
        g, ast, info = ac.synth_cells_fold(snap.in_types, rows, time.process_time() + 5,
                                           lambda g: F.machine_errors(snap, [g], z, examples),
                                           lambda g: F.reach_inputs(snap, [g], z, examples))
    finally:
        vclock.uninstall()
    assert F.machine_errors(snap, [a], z, examples) >= 1
    assert info["first_errors"] == F.machine_errors(snap, [a], z, examples)
    assert info["source"] == "reach" and info["accepted"]
    assert F.machine_errors(snap, [g], z, examples) == 0
    assert all(g(i) == y for i, y in rows)            # the observed transitions stay hard constraints
