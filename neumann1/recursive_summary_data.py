"""Strict opened reference projection; no training/fresh/Oracle authority."""
from neumann1.structural_data_rights import DataUseError,authorize,load_json_view
from neumann1.recursive_summary import validate_problem


def problem_view(root,asset,purpose="development_problem"):
    authorize(asset,purpose)
    if purpose!="development_problem" or asset.get("problem_kind")!="integer_list_right_fold":
        raise DataUseError("Opened recursive reference projection required")
    problem=load_json_view(root,asset,"audit")
    validate_problem(problem)
    return problem
