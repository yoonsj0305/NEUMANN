"""Q3 validation-calibrated edit learning: no target gold and no oracle ambiguity.

These are algorithm contract tests only, not original-author generalization
claims. The disjoint SOURCE verifier is a training signal only after an
explicitly executed candidate; sandboxes that abstain cannot provide truth.
"""
from neumann1.source_program_reviser import SourcePolicyLearner


def test_disjoint_validation_dominates_in_sample_fit():
    p=SourcePolicyLearner(adapt=True)
    variants=[
        ("overfit", "def transform(x):\n    return x[0]"),
        ("transfer", "def transform(x):\n    return x[1]"),
    ]
    # Both candidates fit exactly the same six training observations.
    p.learn("overfit",6,6,source_total=6,independent_verified=False)
    p.learn("transfer",6,6,source_total=6,independent_verified=True)
    assert p.rank(variants)[0][0]=="transfer"
    assert p.weights["overfit"]<0<p.weights["transfer"]


def test_in_sample_progress_cannot_outvote_independent_refutation():
    p=SourcePolicyLearner(adapt=True)
    p.learn("spurious_shortcut",0,6,source_total=6,
            independent_verified=False)
    assert p.weights["spurious_shortcut"]<0
    assert p.updates==1


def test_absent_oracle_evidence_is_not_negative_validation():
    p=SourcePolicyLearner(adapt=True)
    p.learn("unknown",0,6,source_total=6,
            independent_verified=None,source_executed=False)
    assert p.updates==0
    assert "unknown" not in p.weights
    p.learn("unknown",0,6,source_total=6,
            independent_verified=None,source_executed=True)
    assert 0<p.weights["unknown"]<0.02


def test_frozen_uniform_policy_does_not_learn():
    p=SourcePolicyLearner(adapt=False)
    p.learn("transfer",6,6,source_total=6,
            independent_verified=True)
    assert p.updates==0 and not p.weights


def test_policy_freeze_retains_learned_rank_without_test_updates():
    p=SourcePolicyLearner(adapt=True)
    p.learn("valid",6,6,source_total=6,independent_verified=True)
    p.learn("invalid",6,6,source_total=6,independent_verified=False)
    variants=[
        ("valid", "def transform(x):\\n    return x[0]"),
        ("invalid", "def transform(x):\\n    return x[1]"),
    ]
    prior=p.rank(variants)
    before=(dict(p.weights),p.updates)
    p.freeze()
    p.learn("valid",6,6,source_total=6,independent_verified=False)
    assert (p.weights,p.updates)==before
    assert p.rank(variants)==prior
