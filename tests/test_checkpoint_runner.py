import json, sys
sys.path.insert(0, "research/q3")
import checkpoint_runner as cr
from neumann1 import invention_core as ic


def _jobs():
    import invention_dev_family
    src, _ = invention_dev_family.tasks()
    un = ic.untrained_costs()["*"]
    return [(("dev", "A", t["id"]), t, (), un, 2000, None) for t in src[:6]]


def test_checkpoint_restart_skips_done_and_matches_fresh(tmp_path):
    jobs = _jobs()
    part = tmp_path / "part.jsonl"
    cr.run(jobs[:3], part, workers=2)
    assert len(cr.done_keys(part)) == 3
    cr.run(jobs, part, workers=2)                      # restart: only the 3 missing run
    rows = [json.loads(l) for l in part.read_text().splitlines()]
    assert len(rows) == 6 and len({tuple(r["key"]) for r in rows}) == 6
    fresh = tmp_path / "fresh.jsonl"
    cr.run(jobs, fresh, workers=2)
    strip = lambda r: {k: v for k, v in r.items() if k not in ("wall_seconds", "cpu_seconds", "maxrss_kb")}
    a = {tuple(r["key"]): strip(r) for r in rows}
    b = {tuple(json.loads(l)["key"]): strip(json.loads(l)) for l in fresh.read_text().splitlines()}
    assert a == b


def test_errors_and_timeouts_are_recorded(tmp_path):
    bad = {"id": "bad", "in_types": ["L"], "out_type": "L", "train": None, "test": []}
    jobs = [(("x", "A", "bad"), bad, (), None, 100, None)] + _jobs()[:1]
    out = tmp_path / "e.jsonl"
    cr.run(jobs, out, workers=2)
    rows = {json.loads(l)["key"][2]: json.loads(l) for l in out.read_text().splitlines()}
    assert "error" in rows["bad"] and "error" not in rows[_jobs()[0][1]["id"]]
    noise = {"id": "noise", "in_types": ["L"], "out_type": "L",       # no short program exists
             "train": [((tuple(range(i, i + 4)),), (7 * i % 11, 3, i * i % 13)) for i in range(8)],
             "test": []}
    out2 = tmp_path / "t.jsonl"
    cr.run([(("x", "A", "noise"), noise, (), ic.untrained_costs()["*"], 10 ** 9, None)],
           out2, workers=1, wall_cap_s=1.0)
    row = json.loads(out2.read_text().splitlines()[0])
    assert row == {"key": ["x", "A", "noise"], "timeout": 1.0}
