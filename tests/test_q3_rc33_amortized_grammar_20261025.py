"""RC33 tests: scope and ambiguity must be fail-closed."""
import sys,pathlib,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc33"))
from latent_grammar import OPTIONS,SEEDS,candidate_rule_tables,after_neural_proposal,run_one,run_repeated
def test_known_true_rules_withheld_word_and_depth_generalization():
    g=("AB","C","A")
    obs=tuple(run_one(s,g) for s in SEEDS)
    options=candidate_rule_tables(obs)
    assert g in options
    assert len(options)==1
    rec=after_neural_proposal(obs,(2,1,1))
    assert rec["status"]=="CONDITIONAL_UNIQUE_RULES"
    for word in ("A","B","C","BACA","ABCABC"):
        for depth in range(1,8):
            assert run_repeated(word,rec["rules"],depth)==run_repeated(word,g,depth)
def test_ambiguous_identical_observations_are_not_false_pass():
    io=("AAAAAAA",)*3
    opts=candidate_rule_tables(io)
    assert len(opts)>1
    for g in opts:
        rec=after_neural_proposal(io,tuple(len(w) for w in g))
        assert rec["status"]=="UNKNOWN_MULTIPLE_COMPATIBLE_PROGRAMS"
def test_unknown_rule_format_or_bad_output_is_fail_closed():
    obs=("ABCA","CAAB","AABC")
    assert len(OPTIONS)==27
    assert after_neural_proposal(obs,(4,1,1))["status"]=="UNKNOWN_OUTSIDE_METAGRAMMAR"
    assert after_neural_proposal(("X","X","X"),(1,1,1))["status"]=="UNKNOWN_INVALID"
    try:run_repeated("ABC",("ABC",)*3,10,budget=4)
    except ValueError:pass
    else:raise AssertionError("excessive expansion allowed")
