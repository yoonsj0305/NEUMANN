"""Pure helpers of the Q3/Q6 FIRST harness (no dataset access)."""
import sys
sys.path.insert(0, "research/q3")
import invention_first as f
import sequence_specialist as spec


def test_mcnemar_exact():
    assert f.mcnemar(0, 0) == 1.0
    assert abs(f.mcnemar(5, 0) - 0.0625) < 1e-12
    assert f.mcnemar(6, 0) < 0.05 < f.mcnemar(5, 0)
    assert f.mcnemar(3, 3) == 1.0


def test_example_split_rule():
    assert tuple(map(len, f.split_examples(list(range(32))))) == (8, 24)
    assert tuple(map(len, f.split_examples(list(range(15))))) == (8, 7)
    assert tuple(map(len, f.split_examples(list(range(9))))) == (6, 3)


def test_oeis_parser_and_eligibility():
    raw = (b"%I A000000\n%S A000000 0,1,1,2,3,5,8,13,21,34,\n%T A000000 55,89,144,233,377,610,"
           b"987,1597,2584,4181,6765\n%N A000000 demo\n%O A000000 0,4\n")
    t = f.load_oeis("seq/A000/A000000.seq", raw)
    assert t["in_types"] == ["I"] and len(t["train"]) == 14 and len(t["test"]) == 6
    assert t["train"][3] == ((3,), 2) and t["test"][-1] == ((19,), 4181)
    short = f.load_oeis("seq/A000/A000001.seq", b"%S A000001 1,2,3\n%O A000001 1,2\n")
    assert "unsupported" in short


def test_hash_split_is_deterministic_and_disjoint():
    ids = ["x%03d" % i for i in range(40)]
    a, b = f.order(ids, "rule"), f.order(ids, "rule")
    assert a == b and sorted(a) == ids and a != ids
    assert f.order(ids, "oeis") != a


def test_specialist_solves_cfinite_and_abstains_on_primes():
    fib = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]
    assert spec.predict(fib, 3) == [377, 610, 987]
    assert spec.predict([n * n for n in range(14)], 2) == [196, 225]
    assert spec.predict([2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43], 6) is None


def test_used_inventions_only_counts_self_invented_symbols():
    ast = ("f3", ("map", ("f12", ("v", 1)), ("m4", ("v", 0))), ("k", 2))
    assert f.used_inventions(ast, set()) == {"f3", "f12"}
