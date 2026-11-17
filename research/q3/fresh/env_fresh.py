"""FRESH environment: MBPP + HumanEval tasks selected by `registry.py`, answered by the independent authors'
reference implementations running in `sandbox.Oracle`.  Same agent interface as env_listroutines.Env.

Observation protocol (fixed in the FRESH pre-registration, before any task is run):
  T3  the reference must reproduce every published test of the task; otherwise the task is reported as
      "reference inconsistent" and not run (mechanical, decided before any agent sees it)
  initial observation: the published tests, then generated inputs answered by the reference, up to 8
  hidden test: 10 further generated inputs (distinct from the initial ones), never queryable
  generator: elements drawn from the integers that occur in the published test inputs and their +-1
      neighbours; lengths uniform in [max(0, min_len - 1), max_len + 1]; seed = sha256 of the task id;
      an input is kept only if the reference returns a value of the published output type
  queries: any input list; errors / wrong type / timeouts return None and are charged; an input equal to a
      hidden test input is blocked and charged
"""
from __future__ import annotations
import hashlib, random, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sandbox


def _type(v):
    return "B" if isinstance(v, bool) else "I" if isinstance(v, int) else "L"


def _norm(v):
    return tuple(v) if isinstance(v, list) else v


class Inconsistent(Exception):
    pass


class Env:
    def __init__(self, task, seed=0, n_train=8, n_test=10, budget=60):
        self.name = task["id"]
        self._oracle = sandbox.Oracle(task["code"], task["entry"])
        tests = [(tuple(a), _norm(y)) for a, y in task["tests"]]
        out_t = _type(tests[0][1])
        for a, y in tests:
            if self._oracle.call(a) != y:
                self._oracle.close()
                raise Inconsistent(self.name)
        rng = random.Random(int(hashlib.sha256(("fresh:%s:%d" % (self.name, seed)).encode()).hexdigest(), 16))
        pool = sorted({v for a, _ in tests for e in a for v in (e - 1, e, e + 1)}) or [0, 1, 2]
        lens = [len(a) for a, _ in tests]
        lo, hi = max(0, min(lens) - 1), max(lens) + 1
        seen = {a for a, _ in tests}
        train = list(tests)
        test = []
        for _ in range(2000):
            if len(train) >= n_train and len(test) >= n_test:
                break
            x = tuple(rng.choice(pool) for _ in range(rng.randint(lo, hi)))
            if x in seen:
                continue
            seen.add(x)
            y = self._oracle.call(x)
            if y is None or _type(y) != out_t:
                continue
            if len(train) < n_train:
                train.append((x, y))
            else:
                test.append((x, y))
        self._train = [((x,), y) for x, y in train[:max(n_train, len(tests))]]
        self._test = [x for x, _ in test]
        self._answers = {x: y for x, y in test}
        self.out_type = out_t
        self.budget, self.used, self.log = budget, 0, []

    def initial(self):
        return list(self._train)

    def query(self, x):
        if self.used >= self.budget:
            return None
        self.used += 1
        x = tuple(x)
        if x in self._answers:
            self.log.append((x, "blocked"))
            return None
        y = self._oracle.call(x)
        if y is not None and _type(y) != self.out_type:
            y = None
        self.log.append((x, y if y is not None else "invalid"))
        return y

    def _score(self, predict):
        if len(self._test) < 1:
            return False
        try:
            return all(predict((x,)) == self._answers[x] for x in self._test)
        except Exception:
            return False

    def close(self):
        self._oracle.close()
