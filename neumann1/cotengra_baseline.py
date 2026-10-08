"""Mature strong public structural-search comparator, never a learned NEUMANN."""
import random
from time import perf_counter
from neumann1.contraction_structure import certify_path, validate_public


def plan(public, variant, seed, *, repeats=None, reconfigure_iterations=64):
    import cotengra as ctg
    if ctg.__version__ != "0.8.2" or variant not in {"GREEDY128", "RECONF32"} or type(seed) is not int:
        raise ValueError("Pinned comparator and explicit stochastic seed required")
    inputs, output, sizes = validate_public(public)
    random.seed(seed)
    begin = perf_counter()
    optimizer = ctg.HyperOptimizer(methods=["greedy"], minimize="flops",
        max_repeats=repeats if repeats is not None else (128 if variant == "GREEDY128" else 32),
        parallel=False, optlib="random", optlib_opts={"seed": seed}, progbar=False,
        simulated_annealing_opts=None, slicing_opts=None, slicing_reconf_opts=None,
        reconf_opts=None if variant == "GREEDY128" else
                     {"subtree_size": 8, "maxiter": reconfigure_iterations, "seed": seed},
        on_trial_error="raise")
    tree = optimizer.search(inputs, output, sizes)
    path = [list(step) for step in tree.get_path()]
    check = certify_path(public, path)
    import opt_einsum as oe
    _, info = oe.contract_path(public["equation"], *map(tuple, public["shapes"]),
                              shapes=True, optimize=[tuple(step) for step in path])
    if check["dense_arithmetic_work_model"] != int(info.opt_cost):
        raise ValueError("Independent cost model disagreement")
    return {"path": path, "certificate": check, "planner_and_check_seconds": perf_counter() - begin,
            "trials": len(optimizer.costs_flops), "seed": seed, "variant": variant,
            "oracle_used": False, "learned": False, "methods": ["greedy"],
            "global_best_path_proven": False}
