"""THIRD scoring: the registered rule, the CPU condition, ablation verdicts and the unresolved-row policy."""
import json, sys
sys.path.insert(0, "research/q3")
import spec_eval as se


def _write(tmp_path, monkeypatch, fams, drop=(), cpu=None):
    paths = {k: str(tmp_path / k) for k in ("freeze", "rows", "manifest", "result")}
    monkeypatch.setattr(se, "P", lambda kind: paths[kind])
    monkeypatch.setattr(se, "SECOND_RESULT", str(tmp_path / "none.json"))
    (tmp_path / "freeze").write_text(json.dumps({"freeze_sha256": "x"}))
    manifest, lines = {"families": {}}, []
    for fam, arms in fams.items():
        n = len(next(iter(arms.values())))
        ids = ["%s/%03d" % (fam, i) for i in range(n)]
        manifest["families"][fam] = {"tasks": n, "usable_ids": ids, "unsupported": {}, "arms": list(arms)}
        for arm, sol in arms.items():
            for tid, s in zip(ids, sol):
                key = (fam, arm, tid)
                if key in drop:
                    if drop[key]:
                        lines.append({"key": list(key), "status": drop[key]})
                    continue
                lines.append({"key": list(key), "status": "ok", "fit": bool(s), "solved": bool(s), "via": "zmap" if s else None,
                              "cpu_seconds": (cpu or {}).get(arm, 1.0), "candidates": 5, "program": "p"})
    (tmp_path / "rows").write_text("".join(json.dumps(r) + "\n" for r in lines))
    (tmp_path / "manifest").write_text(json.dumps(manifest))


def _fam(n=60, s=40, a=15, a4=20, extra=True):
    d = {"S": [i < s for i in range(n)], "A": [i < a for i in range(n)], "A@4": [i < a4 for i in range(n)]}
    if extra:
        d.update({"S_no_state": [i < a4 for i in range(n)], "S_no_inverse": [i < s - 1 for i in range(n)],
                  "S_no_split": [i < s for i in range(n)]})
    return d


def test_registered_rule_and_gate(tmp_path, monkeypatch):
    fams = {"rule": _fam(), "dc": _fam(), "oeis": dict(_fam(extra=False), D=[i >= 30 for i in range(60)])}
    _write(tmp_path, monkeypatch, fams)
    r = se.score()
    assert r["verdict"]["V_rule"] == r["verdict"]["V_dc"] == "PASS" and r["verdict"]["THIRD_gate"] == "PASS"
    assert r["families"]["rule"]["exclusive"] == 20
    assert r["families"]["oeis"]["exclusive"] == 10 and r["families"]["oeis"]["verdict"] == "PASS"
    ab = r["families"]["rule"]["ablations"]
    assert ab["S_no_state"]["necessary"] == "SHOWN" and ab["S_no_inverse"]["necessary"] == "NOT_SHOWN"
    assert ab["S_no_split"]["necessary"] == "NOT_SHOWN" and r["verdict"]["SECOND_verdicts"].startswith("UNCHANGED")
    fams["dc"] = _fam(s=22, a=15, a4=20)                       # more solved, but not significant vs A@4
    _write(tmp_path, monkeypatch, fams)
    r = se.score()
    assert r["verdict"]["V_dc"] == "FAIL" and r["verdict"]["THIRD_gate"] == "FAIL"


def test_more_cpu_than_the_equal_cap_baseline_cannot_pass(tmp_path, monkeypatch):
    fams = {"rule": _fam(), "dc": _fam()}
    _write(tmp_path, monkeypatch, fams, cpu={"S": 2.0, "A": 1.0})
    r = se.score()
    assert r["families"]["rule"]["cpu_S_le_A"] is False and r["verdict"]["V_rule"] == "FAIL"


def test_unresolved_rows_are_not_auto_failed(tmp_path, monkeypatch):
    fams = {"rule": _fam(), "dc": _fam()}
    drop = {("rule", "S", "rule/000"): "timeout", ("rule", "A", "rule/059"): "died"}
    _write(tmp_path, monkeypatch, fams, drop)
    r = se.score()
    assert len(r["unresolved"]) == 2 and r["verdict"]["V_rule"] == "PASS"       # decisive margin survives
    drop = {("rule", "S", "rule/%03d" % i): (None if i % 2 else "error") for i in range(18, 40)}
    _write(tmp_path, monkeypatch, fams, drop)
    r = se.score()
    assert r["verdict"]["V_rule"] == "INCOMPLETE" and r["verdict"]["THIRD_gate"] == "INCOMPLETE"


def test_end_to_end_on_self_authored_tasks(tmp_path, monkeypatch):
    import random
    import checkpoint_runner as cr
    paths = {k: str(tmp_path / k) for k in ("freeze", "rows", "manifest", "result")}
    monkeypatch.setattr(se, "P", lambda kind: paths[kind])
    monkeypatch.setattr(se, "SECOND_RESULT", str(tmp_path / "none.json"))
    (tmp_path / "freeze").write_text(json.dumps({"freeze_sha256": "x"}))
    rng = random.Random(3)
    xs = [tuple(rng.randint(0, 9) for _ in range(rng.randint(6, 9))) for _ in range(12)]
    mk = lambda name, f: {"id": "rule/" + name, "in_types": ["L"], "out_type": "L",
                          "train": [((x,), f(x)) for x in xs[:8]], "test": [((x,), f(x)) for x in xs[8:]]}
    seq = lambda name, f: {"id": "oeis/" + name, "in_types": ["I"], "out_type": "I",
                           "train": [((n,), f(n)) for n in range(14)], "test": [((n,), f(n)) for n in range(14, 20)]}
    fams = {"rule": [mk("drop", lambda x: x[:-2]), mk("idx", lambda x: tuple(v + j for j, v in enumerate(x))),
                     {"id": "rule/u", "unsupported": "x"}],
            "oeis": [seq("sq", lambda n: n * n), seq("pow", lambda n: 3 ** n)]}
    arms = {"rule": ["S", "A", "A@4", "S_no_state"], "oeis": ["S", "A", "A@4", "D"]}
    jobs, manifest = se.build(fams, cap=3.0, arms=arms)
    assert len(jobs) == 2 * 4 + 2 * 4
    (tmp_path / "manifest").write_text(json.dumps(manifest))
    rows = cr.run(jobs, paths["rows"], workers=2, worker=se.job)
    assert all(r["status"] == "ok" for r in rows.values())
    assert rows[("rule", "S", "rule/drop")]["solved"] and rows[("rule", "S", "rule/idx")]["solved"]
    assert rows[("oeis", "D", "oeis/sq")]["solved"] and rows[("oeis", "S", "oeis/pow")]["via"] == "rec"
    r = se.score()
    assert r["unresolved"] == [] and r["families"]["rule"]["solved"]["S"] == 2
    assert all(row["cpu_seconds"] <= 12.5 for k, row in rows.items() if k[1] != "D")
