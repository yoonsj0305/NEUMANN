"""3-E0 replay check (not part of the L1 machine): the original benchmark sample_batch (batch 1, jax.disable_jit) with
every random draw (jax.random.randint / choice, np.random.randint, random.randint) replaced by a draw from one python
random.Random, versus stage3/e_tasks.GEN with a Random of the same seed.  Inputs and outputs must be identical.

Needs jax, chex, dm-tree, tqdm (a separate environment; the original code is only imported here) and a clone of
github.com/google-deepmind/neural_networks_chomsky_hierarchy at e_tasks.SOURCE["commit"] reachable as the package
neural_networks_chomsky_hierarchy under PKG_PARENT:
  python -I stage3/e0_replay.py PKG_PARENT PER_LENGTH OUT_JSON
"""
import sys, random, json, types, pathlib
PKG, PER, OUTF = sys.argv[1], int(sys.argv[2]), sys.argv[3]
sys.path.insert(0, PKG)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np
import jax, jax.numpy as jnp
import e_tasks as E

class Stub:
    def __init__(self): self.r = None
    def randint(self, *a, **k):            # jax.random.randint(key, shape, minval, maxval)
        key, shape = a[0], a[1] if len(a) > 1 else k["shape"]
        lo = a[2] if len(a) > 2 else k["minval"]; hi = a[3] if len(a) > 3 else k["maxval"]
        n = int(np.prod(shape))
        return jnp.array([self.r.randrange(int(lo), int(hi)) for _ in range(n)]).reshape(shape)
    def choice(self, key, a, shape):
        a = [int(v) for v in np.asarray(a)]
        n = int(np.prod(shape))
        return jnp.array([self.r.choice(a) for _ in range(n)]).reshape(shape)
    def split(self, key, num=2):
        return [key] * num
    def np_randint(self, low, high=None, size=None):
        if high is None: low, high = 0, low
        if size is None: return self.r.randrange(int(low), int(high))
        n = int(np.prod(size))
        return np.array([self.r.randrange(int(low), int(high)) for _ in range(n)]).reshape(size)
    def py_randint(self, a, b): return self.r.randint(a, b)
ST = Stub()

from neural_networks_chomsky_hierarchy.tasks.regular import modular_arithmetic, parity_check, even_pairs, cycle_navigation
from neural_networks_chomsky_hierarchy.tasks.dcf import modular_arithmetic_brackets, reverse_string, solve_equation, stack_manipulation
from neural_networks_chomsky_hierarchy.tasks.cs import binary_addition, binary_multiplication, bucket_sort, compute_sqrt, duplicate_string, missing_duplicate_string, odds_first
mods = [modular_arithmetic, parity_check, even_pairs, cycle_navigation, modular_arithmetic_brackets, reverse_string,
        solve_equation, stack_manipulation, binary_addition, binary_multiplication, bucket_sort, compute_sqrt,
        duplicate_string, missing_duplicate_string, odds_first]
fake_jr = types.SimpleNamespace(randint=ST.randint, choice=ST.choice, split=ST.split)
fake_np_random = types.SimpleNamespace(randint=ST.np_randint)
for m in mods:
    if hasattr(m, "jrandom"): m.jrandom = fake_jr
    if hasattr(m, "jax"): m.jax = types.SimpleNamespace(random=fake_jr, jit=jax.jit, vmap=jax.vmap, ops=jax.ops, nn=jax.nn)
    if hasattr(m, "np"): m.np = types.SimpleNamespace(random=fake_np_random, array=np.array, int32=np.int32, concatenate=np.concatenate, ndarray=np.ndarray)
    if hasattr(m, "random"): m.random = types.SimpleNamespace(randint=ST.py_randint)
B = {"modular_arithmetic": lambda: modular_arithmetic.ModularArithmetic(),
     "parity_check": parity_check.ParityCheck, "even_pairs": even_pairs.EvenPairs,
     "cycle_navigation": cycle_navigation.CycleNavigation,
     "modular_arithmetic_brackets": lambda: modular_arithmetic_brackets.ModularArithmeticBrackets(mult=True),
     "reverse_string": reverse_string.ReverseString, "solve_equation": solve_equation.SolveEquation,
     "stack_manipulation": stack_manipulation.StackManipulation, "binary_addition": binary_addition.BinaryAddition,
     "binary_multiplication": binary_multiplication.BinaryMultiplication, "bucket_sort": bucket_sort.BucketSort,
     "compute_sqrt": compute_sqrt.ComputeSqrt, "duplicate_string": duplicate_string.DuplicateString,
     "missing_duplicate_string": missing_duplicate_string.MissingDuplicateString, "odds_first": odds_first.OddsFirst}
MAB = {'+': 5, '-': 6, '*': 7, '(': 8, ')': 9, 'x': 10, '=': 11}
SEQ = {'+': 5, '-': 6, '(': 7, ')': 8, 'x': 9, '=': 10}
def mine_ints(task, inp):
    if task == "modular_arithmetic_brackets": return [MAB.get(c, None) if c in MAB else int(c) for c in inp]
    if task == "solve_equation": return [SEQ[c] if c in SEQ else int(c) for c in inp]
    return [int(v) for v in inp]
res = {}
per_len = PER
with jax.disable_jit():
    for task in E.SUITE:
        bad = n = 0; ex = None
        for L in range(1, 41):
            for k in range(per_len):
                seed = "replay:%s:%d:%d" % (task, L, k)
                ST.r = random.Random(seed)
                b = B[task]().sample_batch(jax.random.PRNGKey(0), 1, L)
                oi = [int(v) for v in np.asarray(b["input"]).argmax(-1).reshape(-1)]
                oo = [int(v) for v in np.asarray(b["output"]).argmax(-1).reshape(-1)]
                mi, mo = E.GEN[task](L, random.Random(seed))
                mi = mine_ints(task, mi)
                n += 1
                if (oi, oo) != (mi, [int(v) for v in mo]):
                    bad += 1
                    ex = ex or {"L": L, "orig": (oi, oo), "mine": (mi, mo)}
        res[task] = {"examples": n, "mismatch": bad, "first_mismatch": ex}
        print(task, n, bad, ex if ex else "", flush=True)
json.dump(res, open(OUTF, "w"), indent=1)
