"""Opened structural experience access, never an activated training pipeline.

Uses the existing D0 rights gate before payload I/O. Public runtime projections
exclude candidate paths, certificates, success labels and cost observations.
This Python API enforces its own access, not arbitrary filesystem access.
"""
from neumann1.structural_data_rights import DataUseError, authorize, load_json_view


def problem_view(root, asset, purpose="development_problem"):
    authorize(asset, purpose)  # Train/fresh/sealed rejected before payload I/O.
    if purpose != "development_problem":
        raise DataUseError("problem projection requires opened development authority")
    source = load_json_view(root, asset, "audit")
    kind = asset.get("problem_kind")
    if kind == "contraction":
        from neumann1.contraction_structure import validate_public
        public = source["public"]
        validate_public(public)
        return {"kind": kind, "equation": public["equation"], "shapes": public["shapes"]}
    if kind == "proof":
        from neumann1.representation_program import validate
        original = source["original"]
        validate(original)
        return {"kind": kind, "original": original, "bindings": source["bindings"]}
    raise DataUseError("unsupported public structural domain")


def offline_experience(root, asset, purpose="offline_oracle"):
    authorize(asset, purpose)
    if purpose != "offline_oracle":
        raise DataUseError("cost/validity/proposal supervision is offline only")
    return load_json_view(root, asset, "audit")
