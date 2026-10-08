"""Opened recurrence projections through the existing D0 data-use gate.

These API checks precede payload I/O; they are not an OS security boundary.
No training or fresh evaluation is activated by registering a public problem.
"""
from neumann1.structural_data_rights import DataUseError, authorize, load_json_view
from neumann1.inductive_perspective import validate_problem


def problem_view(root, asset, purpose="development_problem"):
    authorize(asset, purpose)
    if purpose != "development_problem" or asset.get("problem_kind") != "exact_integer_recurrence":
        raise DataUseError("opened recurrence development projection required")
    public = load_json_view(root, asset, "audit")
    validate_problem(public)  # Strict schema excludes Oracle/cost/lineage labels.
    return public
