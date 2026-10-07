"""D0 reuse views and declared equivalence-lineage guard.

Enforces the provided loader API; not a security boundary for arbitrary Python.
Historical metadata is not fresh evaluation. No sealed payload is read, hashed or
decoded. Training activation is a separate G0/G1 contract requirement.
"""
import gzip
import hashlib
import json
from pathlib import Path


class DataUseError(ValueError):
    pass


PURPOSES = {
    "H": {"audit"}, "D": {"audit", "development_problem"},
    "F": {"audit", "fixture"}, "B": {"audit"},
    "O": {"audit", "offline_oracle"}, "S": set(),
}


def authorize(asset, purpose):
    role = asset.get("role")
    if role not in PURPOSES or purpose not in PURPOSES[role]:
        raise DataUseError("reuse role/purpose denied before payload access")
    if asset.get("allowed_use") != "opened_development_only" and purpose != "audit":
        raise DataUseError("not opened development authority")
    if purpose == "offline_oracle" and asset.get("runtime") is not False:
        raise DataUseError("oracle is offline only")


def load_json_view(root, asset, purpose):
    authorize(asset, purpose)
    root = Path(root).resolve()
    path = (root / asset["path"]).resolve()
    if not path.is_relative_to(root) or path == root:
        raise DataUseError("payload escapes declared root")
    packed = path.read_bytes()
    if hashlib.sha256(packed).hexdigest() != asset["sha256"]:
        raise DataUseError("payload identity mismatch")
    raw = gzip.decompress(packed) if asset.get("format") == "gzip-json" else packed
    if len(raw) > 128 * 1024 * 1024:
        raise DataUseError("payload exceeds bounded view")
    obj = json.loads(raw)
    for key in asset.get("pointer", []):
        obj = obj[key]
    if purpose == "development_problem":
        # LP public view has exactly original coefficients: no oracle labels,
        # optimal basis/dual, seeds, accepted flags or test feedback.
        arrays = obj.get("arrays", obj)
        if not all(key in arrays for key in ("A", "b", "c")):
            raise DataUseError("original LP public coefficients unavailable")
        return {key: arrays[key] for key in ("A", "b", "c")}
    return obj


class LineageGuard:
    """Check producer-declared equivalence groups and transform compositions.

    Does not claim to discover arbitrary mathematical equivalence or graph
    isomorphism. Missing group/ancestry declarations block new evaluation.
    """
    def __init__(self):
        self.groups = {}
        self.training_compositions = set()

    def register(self, record, partition):
        group = record.get("equivalence_group")
        if not group or not record.get("source_artifact_sha256"):
            raise DataUseError("lineage identity is required")
        if partition not in {"opened_development", "train", "unseen_composition", "novel_motif"}:
            raise DataUseError("unsupported or sealed partition")
        if record.get("training_exposure") and partition not in {"opened_development", "train"}:
            raise DataUseError("historically exposed problem cannot become fresh")
        prior = self.groups.get(group)
        # Train/opened development share an exposure region, not fresh evidence.
        region = "opened" if partition in {"opened_development", "train"} else partition
        if prior is not None and prior != region:
            raise DataUseError("equivalent original/views cross partition boundary")
        composition = record.get("transformation_ancestry")
        if partition == "unseen_composition":
            if not composition or tuple(composition) in self.training_compositions:
                raise DataUseError("composition absent or already exposed in training")
        if partition in {"opened_development", "train"} and composition:
            token = tuple(composition)
            # Validate against earlier evaluation declarations too, independent
            # of registration order.
            if hasattr(self, "evaluation_compositions") and token in self.evaluation_compositions:
                raise DataUseError("training composition collides with declared evaluation")
            self.training_compositions.add(token)
        if partition == "unseen_composition":
            if not hasattr(self, "evaluation_compositions"):
                self.evaluation_compositions = set()
            self.evaluation_compositions.add(tuple(composition))
        self.groups[group] = region
