from neumann1 import Problem, CostLedger, IRKind
from neumann1.matching_ir import ControlledMatchingStructureFormer
from neumann1.linear_ir import ControlledLinearSystemStructureFormer
from neumann1.learned_compiler_gate import LearnedProposalCompilerGate


class FixedProposer:
    def __init__(self, kind, confidence=0.9):
        self.kind = kind
        self.confidence = confidence

    def predict_kind(self, text):
        return self.kind, self.confidence


def gate_with(kind):
    return LearnedProposalCompilerGate(
        FixedProposer(kind),
        {
            IRKind.BIPARTITE_MATCHING: ControlledMatchingStructureFormer(),
            IRKind.LINEAR_SYSTEM: ControlledLinearSystemStructureFormer(),
        },
    )


def test_matching_proposal_requires_matching_compiler_acceptance():
    rep = gate_with(IRKind.BIPARTITE_MATCHING).form(
        Problem("S1 can use A or C; S2 can use B or C"), CostLedger()
    )
    assert rep.kind == IRKind.BIPARTITE_MATCHING


def test_wrong_family_proposal_becomes_unknown_not_wrong_ir():
    rep = gate_with(IRKind.BIPARTITE_MATCHING).form(
        Problem("x + y = 5; x - y = 1"), CostLedger()
    )
    assert rep.kind == IRKind.UNKNOWN
    assert "rejected by deterministic compiler" in rep.rationale


def test_uncompiled_proposed_family_fails_closed():
    rep = gate_with(IRKind.SHORTEST_PATH).form(
        Problem("Find the shortest path from A to D."), CostLedger()
    )
    assert rep.kind == IRKind.UNKNOWN
    assert "no authorized compiler" in rep.rationale


def test_known_proposer_abstention_fails_closed():
    rep = gate_with(IRKind.UNKNOWN).form(
        Problem("S1 can use A or C; S2 can use B or C"), CostLedger()
    )
    assert rep.kind == IRKind.UNKNOWN


def test_compiler_semantic_rejection_overrides_known_proposal():
    rep = gate_with(IRKind.BIPARTITE_MATCHING).form(
        Problem("S1 can use A or C with cost 5; S2 can use B or C"), CostLedger()
    )
    assert rep.kind == IRKind.UNKNOWN
    assert "rejected by deterministic compiler" in rep.rationale
