"""Scoring of the checkpointed evaluations: registered rules unchanged, unresolved rows never auto-failed."""
import json, random, sys
sys.path.insert(0, "research/q3")
import invention_eval2 as ev
import invention_first as first


def _write(tmp_path, monkeypatch, plan, fams, drop=()):
    """fams: {family: {arm: [solved bools per task]}}; drop: keys written as non-ok or omitted."""
    paths = {k: str(tmp_path / ("%s_%s" % (plan, k))) for k in ("freeze", "rows", "manifest", "result")}
    monkeypatch.setattr(ev, "P", lambda p, kind: paths[kind])
    (tmp_path / ("%s_freeze" % plan)).write_text(json.dumps({"freeze_sha256": "x"}))
    manifest = {"plan": plan, "families": {}}
    lines = []
    for fam, arms in fams.items():
        n = len(next(iter(arms.values())))
        ids = ["%s/%03d" % (fam, i) for i in range(n)]
        manifest["families"][fam] = {"tasks": n + 1, "usable_ids": ids,
                                     "unsupported": {"%s/u" % fam: "x"}, "arms": list(arms)}
        for arm, sol in arms.items():
            for tid, s in zip(ids, sol):
                key = [fam, arm, tid]
                if tuple(key) in drop:
                    if drop[tuple(key)] is not None:
                        lines.append({"key": key, "status": drop[tuple(key)]})
                    continue
                row = {"key": key, "status": "ok", "fit": bool(s), "solved": bool(s), "n_train": 8, "n_hidden": 8}
                if arm != "D":
                    row.update({"via": "search" if s else None, "candidates": 10, "cpu_seconds": 0.1, "work": 5,
                                "size": 3, "program": "(f0 $0 nil)" if s else None,
                                "ast": ["f%d" % (hash(tid) % 4), ["v", 0], ["nil"]] if s else None})
                lines.append(row)
    (tmp_path / ("%s_rows" % plan)).write_text("".join(json.dumps(r) + "\n" for r in lines))
    (tmp_path / ("%s_manifest" % plan)).write_text(json.dumps(manifest))


def _second(rng, n=40, c_bonus=0.35):
    def fam(extra=()):
        base = [rng.random() < 0.3 for _ in range(n)]
        d = {"A": base, "A4": [b or rng.random() < 0.1 for b in base],
             "B": [b or rng.random() < 0.1 for b in base],
             "C": [b or rng.random() < c_bonus for b in base]}
        for e in extra:
            d[e] = [rng.random() < 0.4 for _ in range(n)]
        return d
    rule = fam(("C_no_inventions", "C_no_learned_prior"))
    rule["A"] = [True] * 25 + [False] * 15          # integrity counts: A = 25, A4 = 34
    rule["A4"] = [True] * 34 + [False] * 6
    return {"rule": rule, "dc": fam(), "oeis": fam(("D",))}


def test_p2_is_the_registered_rule(tmp_path, monkeypatch):
    for seed in range(8):
        rng = random.Random(seed)
        fams = _second(rng, c_bonus=rng.choice([0.0, 0.2, 0.5]))
        _write(tmp_path, monkeypatch, "second", fams)
        rep, unresolved = ev.report("second", "adverse")
        assert unresolved == []
        s, v = first.summarize(rep, ev.load_core(ev.FROZEN)[0])
        for fam in fams:
            mine = ev.p2(list(rep["families"][fam]["rows"].values()))
            assert mine["verdict"] == v["P2_" + fam]
            key = [k for k in s[fam] if k.startswith("C_exclusive_vs_")][0]
            assert mine["exclusive"] == s[fam][key]
            assert mine["vs_A"]["mcnemar_p"] == s[fam]["C_vs_A"]["mcnemar_p"]


def test_complete_run_gives_registered_verdict_and_integrity(tmp_path, monkeypatch):
    fams = _second(random.Random(1), c_bonus=0.6)
    _write(tmp_path, monkeypatch, "second", fams)
    res = ev.score("second")
    assert res["unresolved"] == [] and res["integrity"]["status"] == "OK"
    assert res["verdict"]["P2_rule"] in ("PASS", "FAIL") and res["verdict"]["global_Q1_Q7"] == "OPEN"
    fams["rule"]["A"][0] = False                                     # A no longer reproduces 25
    _write(tmp_path, monkeypatch, "second", fams)
    res = ev.score("second")
    assert res["integrity"]["status"] == "VOID" and set(res["verdict"].values()) == {"VOID"}


def test_unresolved_rows_are_never_auto_failed(tmp_path, monkeypatch):
    n = 40
    rule = {"A": [True] * 25 + [False] * 15, "A4": [True] * 34 + [False] * 6,
            "B": [True] * 25 + [False] * 15, "C": [True] * 39 + [False],
            "C_no_inventions": [False] * n, "C_no_learned_prior": [False] * n}
    fams = {"rule": rule, "dc": dict((a, list(v)) for a, v in rule.items() if not a.startswith("C_")),
            "oeis": dict({a: list(v) for a, v in rule.items() if not a.startswith("C_")}, D=[False] * n)}
    # (a) a decisive margin survives a few unresolved rows -> still PASS
    drop = {("rule", "C", "rule/000"): "timeout", ("rule", "B", "rule/039"): "died"}
    _write(tmp_path, monkeypatch, "second", fams, drop)
    res = ev.score("second")
    assert len(res["unresolved"]) == 2 and res["verdict"]["P2_rule"] == "PASS"
    # (b) many unresolved C rows: neither PASS nor FAIL can be concluded -> INCOMPLETE, not FAIL
    drop = {("rule", "C", "rule/%03d" % i): ("error" if i % 2 else None) for i in range(25, 39)}
    _write(tmp_path, monkeypatch, "second", fams, drop)
    res = ev.score("second")
    assert res["verdict"]["P2_rule"] == "INCOMPLETE" and res["verdict"]["Q3_scoped"] != "PASS"
    # (c) integrity is PENDING while an A/A4 row is unresolved
    _write(tmp_path, monkeypatch, "second", fams, {("rule", "A", "rule/030"): "timeout"})
    assert ev.score("second")["integrity"]["status"] == "PENDING"


def test_fresh_plan_scores_both_hypotheses(tmp_path, monkeypatch):
    n = 60
    base = [i < 15 for i in range(n)]
    fams = {"oeis_reserve": {"A": base, "A4": [i < 20 for i in range(n)], "B": base,
                             "C": [i < 40 for i in range(n)], "B_L": base, "C_L": base,
                             "D": [20 <= i < 28 for i in range(n)]}}
    _write(tmp_path, monkeypatch, "fresh", fams)
    res = ev.score("fresh")
    assert res["verdict"]["F1_Q3_sequences_first_exposure"] == "PASS"       # C: 25 over A/B, 12 exclusive
    assert res["verdict"]["F2_Q6_cross_semantic_zero_shot"] == "FAIL"       # C_L == A
    assert res["summary"]["F1_Q3_sequences_frozen_core"]["exclusive"] == 12


def test_end_to_end_smoke_on_dev_tasks(tmp_path, monkeypatch):
    """build -> checkpoint runner -> score -> checklist, with tiny budgets and self-authored tasks only."""
    import invention_dev_family, invention_eval2_report as rp
    import checkpoint_runner as cr
    paths = {k: str(tmp_path / ("second_%s.json" % k)) for k in ("freeze", "rows", "manifest", "result")}
    monkeypatch.setattr(ev, "P", lambda p, kind: paths[kind])
    monkeypatch.setattr(first, "N_TARGET", 400)
    monkeypatch.setattr(first, "N_STRONG", 1600)
    (tmp_path / "second_freeze.json").write_text(json.dumps({"freeze_sha256": "x"}))
    src, tgt = invention_dev_family.tasks()
    lists = [dict(t, id="rule/" + t["id"]) for t in (src + tgt)[:6]]
    seq = lambda name, f: {"id": "oeis/" + name, "in_types": ["I"], "out_type": "I",
                           "train": [((n,), f(n)) for n in range(14)], "test": [((n,), f(n)) for n in range(14, 20)]}
    fams = {"rule": lists + [{"id": "rule/u", "unsupported": "x"}],
            "dc": [dict(t, id="dc/" + t["id"]) for t in (src + tgt)[6:9]],
            "oeis": [seq("sq", lambda n: n * n), seq("lin", lambda n: 2 * n + 1), seq("fib", lambda n: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181][n])]}
    jobs, manifest = ev.build("second", fams)
    assert len(jobs) == 6 * 6 + 3 * 4 + 3 * 5 and manifest["families"]["oeis"]["arms"][-1] == "D"
    (tmp_path / "second_manifest.json").write_text(json.dumps(manifest))
    rows = cr.run(jobs, paths["rows"], workers=2, worker=ev.job)
    assert all(r["status"] == "ok" for r in rows.values())
    res = ev.score("second")
    assert res["unresolved"] == [] and res["integrity"]["status"] == "VOID"      # dev tasks: A != 25
    d = res["families"]["oeis"]["rows"]
    assert d["oeis/sq"]["D"]["solved"] and d["oeis/fib"]["D"]["solved"]          # specialist arm wired
    assert all("work" in r["C"] and r["C"]["n_hidden"] == 8 for k, r in res["families"]["rule"]["rows"].items()
               if "unsupported" not in r)
    rp.main("second")
    chk = json.loads((tmp_path / "second_checklist.json").read_text())
    assert set(chk["families"]) == {"rule", "dc", "oeis"} and "P3_compute_wording" in chk["families"]["rule"]
