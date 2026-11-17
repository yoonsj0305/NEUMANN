"""Executor changes are semantics-preserving: differential tests against the frozen FIRST executor,
plus the specific call-by-name blow-up pattern diagnosed on 2026-11-11."""
import importlib.util, json, pathlib, subprocess, sys, time
import pytest
sys.path.insert(0, "research/q3")
from neumann1 import invention_core as ic

FROZEN_COMMIT = "0954ed5"


def _frozen(tmp_path):
    src = subprocess.run(["git", "show", FROZEN_COMMIT + ":neumann1/invention_core.py"],
                         capture_output=True, text=True)
    if src.returncode != 0:
        pytest.skip("frozen commit not available")
    p = tmp_path / "ic_frozen_test.py"
    p.write_text(src.stdout)
    spec = importlib.util.spec_from_file_location("ic_frozen_test", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _trace(mod):
    seq = []
    orig = mod.Search._keep

    def keep(self, ctx, out, e, t):
        seq.append((ctx.depth, e.ast(), e.vec))
        return orig(self, ctx, out, e, t)
    mod.Search._keep = keep
    return seq, orig


def _dev():
    import invention_dev_family
    src, tgt = invention_dev_family.tasks()
    return src + tgt


FROZEN_CORE = json.loads(pathlib.Path("docs/experiments/results/invention_core_frozen.json").read_text())
MEMORY = [(ic._tup(a), tuple(i), o) for a, i, o in FROZEN_CORE["memory"]]
SPEC = [tuple(x) for x in FROZEN_CORE["spec"]]


@pytest.mark.parametrize("arm", ["A", "B", "C"])
def test_search_trace_identical_to_frozen(tmp_path, arm):
    old = _frozen(tmp_path)
    tasks = _dev()[::8]
    for t in tasks:
        spec = SPEC if arm == "C" else ()
        mem = MEMORY if arm in ("B", "C") else None
        costs = ic.cost_for(FROZEN_CORE["costs"] if arm == "C" else ic.untrained_costs(), t)
        so, ko = _trace(old)
        ro = old.solve(t, spec, costs, 3000, mem)
        old.Search._keep = ko
        sn, kn = _trace(ic)
        rn = ic.solve(t, spec, costs, 3000, mem)
        ic.Search._keep = kn
        assert so == sn, t["id"]
        for f in ("fit", "solved", "via", "candidates", "ast"):
            assert ro[f] == rn[f], (t["id"], f)


def _nested_memory(depth):
    """The largest stored L->L program (33 nodes, references its input 5x inside loops) nested
    `depth` times: the shape found by profiling the stalled FIRST worker."""
    lib = ic.base_library()
    big = max((m for m in MEMORY if m[1] == ("L",)), key=lambda m: ic.size(m[0]))
    ic.add_invention(lib, "mbig", "L", [("L", ())], ic._to_body(big[0], 1))
    e = ("v", 0)
    for _ in range(depth):
        e = ("mbig", e)
    return lib, e


def test_call_by_need_equal_outputs_and_less_work():
    xs = [(), (3,), (1, 2, 3), (5, 1, 4, 1, 5), (9, 8, 7, 6, 5, 4), (2, 7, 1, 8, 2, 8, 1, 8)]
    for depth in (1, 2, 3):
        outs = {}
        for need in (False, True):
            ic.CALL_BY_NEED = need
            lib, prog = _nested_memory(depth)
            w0 = ic.WORK[0]
            outs[need] = ([ic.run_program(prog, lib, (x,)) for x in xs], ic.WORK[0] - w0)
        ic.CALL_BY_NEED = True
        assert outs[False][0] == outs[True][0]
        assert outs[True][1] <= outs[False][1]
        if depth == 3:
            assert outs[False][1] > 50 * outs[True][1]


def test_lazy_failure_semantics_kept():
    """An argument that would Fail but is never referenced must not make the call fail."""
    # g(?0, ?1) = if (isnil ?1) nil ?0  -- ?0 referenced only on one branch
    prog = ("g", ("tail", ("nil",)), ("v", 0))          # tail nil fails
    for need in (False, True):
        ic.CALL_BY_NEED = need
        lib2 = ic.base_library()
        ic.add_invention(lib2, "g", "L", [("L", ()), ("L", ())],
                         ("ifL", ("isnil", ("h", 1, ())), ("nil",), ("h", 0, ())))
        assert ic.run_program(prog, lib2, ((),)) == ()      # unreferenced failing arg: success
        assert ic.run_program(prog, lib2, ((1,),)) is None  # referenced failing arg: failure
    ic.CALL_BY_NEED = True
