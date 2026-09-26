from neumann1 import TwoStageOpenSetStructureFormer, training_examples, heldout_examples, final_test_examples, IRKind


def fitted():
    m=TwoStageOpenSetStructureFormer().fit(training_examples())
    m.tune_threshold(heldout_examples())
    return m


def test_validation_selects_fail_closed_threshold():
    m=TwoStageOpenSetStructureFormer().fit(training_examples())
    metrics=m.tune_threshold(heldout_examples())
    assert metrics.unknown_false_route_rate == 0.0
    assert metrics.known_coverage >= 0.75


def test_final_test_false_route_rate_is_bounded_exploratorily():
    m=fitted()
    unknown=[x for x in final_test_examples() if x[1]==IRKind.UNKNOWN]
    false=sum(m.predict_kind(text)[0] != IRKind.UNKNOWN for text,_,_ in unknown)
    assert false/len(unknown) <= 0.25


def test_final_known_coverage_remains_useful():
    m=fitted()
    known=[x for x in final_test_examples() if x[1]!=IRKind.UNKNOWN]
    routed=sum(m.predict_kind(text)[0] != IRKind.UNKNOWN for text,_,_ in known)
    assert routed/len(known) >= 0.75
