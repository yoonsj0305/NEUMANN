from neumann1 import (
    LearnedKindStructureFormer, KeywordKindBaseline, training_examples, heldout_examples,
    CostLedger, Problem, IRKind,
)


def fitted():
    return LearnedKindStructureFormer().fit(training_examples())


def test_learned_kind_surface_shift_examples():
    model = fitted()
    examples = [x for x in heldout_examples() if x[2] == "known"]
    correct = 0
    for text, expected, _ in examples:
        payload = {expected.value: {"placeholder": True}}
        rep = model.form(Problem(text, {"payload_by_kind": payload}), CostLedger())
        correct += rep.kind == expected
    assert correct / len(examples) >= 0.75


def test_hard_negative_false_route_rate_bounded():
    model = fitted()
    examples = [x for x in heldout_examples() if x[2] == "hard_negative"]
    false_routes = 0
    for text, expected, _ in examples:
        payloads = {
            IRKind.BIPARTITE_MATCHING.value: {"placeholder": True},
            IRKind.SHORTEST_PATH.value: {"placeholder": True},
            IRKind.LINEAR_SYSTEM.value: {"placeholder": True},
        }
        rep = model.form(Problem(text, {"payload_by_kind": payloads}), CostLedger())
        false_routes += rep.kind != IRKind.UNKNOWN
    assert false_routes / len(examples) <= 0.50


def test_keyword_baseline_exists_for_comparison():
    b = KeywordKindBaseline()
    assert b.predict("Find the shortest route") == IRKind.SHORTEST_PATH
