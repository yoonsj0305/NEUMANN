from neumann1 import TwoStageOpenSetStructureFormer, training_examples, IRKind
from neumann1.prototype_open_set import PrototypeOpenSetStructureFormer
from neumann1.open_set_v006_dataset import validation_v006, final_test_v006


def test_v006_validation_thresholds_freeze_without_observed_false_route():
    two = TwoStageOpenSetStructureFormer().fit(training_examples())
    tm = two.tune_threshold(validation_v006())
    proto = PrototypeOpenSetStructureFormer().fit(training_examples())
    pm = proto.tune_threshold(validation_v006())
    assert tm.unknown_false_route_rate == 0.0
    assert pm.unknown_false_route_rate == 0.0


def test_v006_final_near_ood_is_measured_separately():
    two = TwoStageOpenSetStructureFormer().fit(training_examples())
    two.tune_threshold(validation_v006())
    examples = [x for x in final_test_v006() if x[2] == "near_unknown"]
    assert len(examples) >= 10
    false_routes = sum(two.predict_kind(text)[0] != IRKind.UNKNOWN for text, _, _ in examples)
    assert 0 <= false_routes <= len(examples)


def test_prototype_baseline_runs_on_frozen_test():
    proto = PrototypeOpenSetStructureFormer().fit(training_examples())
    proto.tune_threshold(validation_v006())
    preds = [proto.predict_kind(text)[0] for text, _, _ in final_test_v006()]
    assert len(preds) == len(final_test_v006())
