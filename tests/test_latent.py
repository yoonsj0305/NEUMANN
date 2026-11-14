"""Formation of intermediate representations: residual and transport latents, minimal description, and the
separation of substrate (R1), formation (R2) and learned prior (R3)."""
import random, sys, time
sys.path.insert(0, ".")
from neumann1 import invention_core as ic, spec_core as sc, latent as lt, discovery_core as dc

INV = sc.load_inverses()
R1, R2 = lt.Cfg(subst=True), lt.Cfg(subst=True, latent=True)
RNG = random.Random(3)
XS = [tuple(RNG.randint(0, 9) for _ in range(RNG.randint(5, 9))) for _ in range(16)]


def _lt(f):
    ex = [((x,), f(x)) for x in XS]
    return {"id": "l", "in_types": ["L"], "out_type": "L", "train": ex[:8], "test": ex[8:]}


def _seq(f):
    ex = [((n,), f(n)) for n in range(20)]
    return {"id": "s", "in_types": ["I"], "out_type": "I", "train": ex[:14], "test": ex[14:]}


def _ok(t, cfg):
    sol = lt.solve(t, time.process_time() + 6, INV, cfg)
    return sol, sol is not None and all(lt.run(sol, lt.library(cfg), i, t) == o for i, o in t["test"])


def test_residual_latent_is_formed_and_solved_recursively():
    t = _seq(lambda n: sum(bin(k).count("1") for k in range(n + 1)))
    sol, ok = _ok(t, R2)
    assert ok and lt.kinds(sol)[0] == "residual" and not _ok(t, R1)[1]
    assert {c for c, _, _ in lt.programs(sol, t)} == {"seq"}


def test_transport_latent_reads_the_correspondence_from_the_input_side():
    t = _lt(lambda x: tuple(dict.fromkeys(x)))
    sol, ok = _ok(t, R2)
    assert ok and lt.kinds(sol) == ["transport"] and not _ok(t, R1)[1]


def test_minimal_description_rejects_a_representation_longer_than_its_cells():
    assert lt._size(("case", ("lt", ("v", 0), ("k", 1)), ("value", ("k", 3)), ("copy", "self", ("v", 0)))) == 8
    assert lt._simpler((1, 2, 1, 2), (3, 5, 8, 9)) and not lt._simpler((3, 5, 8, 9), (1, 2, 1, 2))


def test_prior_is_fitted_from_verified_representations_and_plugs_into_the_pipeline():
    t = _seq(lambda n: sum(bin(k).count("1") for k in range(n + 1)))
    sol, _ = _ok(t, R2)
    cfg = lt.fit_prior([(lt.kinds(sol), lt.programs(sol, t))])
    assert cfg.order[0] == "residual" and "seq" in cfg.prior and cfg.cost("seq")["mod"] <= cfg.cost("seq")["foldrI"]
    dc.LATENT_CFG.update({"R1": R1, "R2": R2})
    on = dc.solve(t, 6, dc.Policy(), INV, cells="R2")
    off = dc.solve(t, 6, dc.Policy(), INV, cells="R1")
    assert on["solved"] and on["via"].startswith("latent:residual") and not off["solved"]
