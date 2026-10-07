"""Strong C comparator: cost-sensitive reuse of public native tensor programs.

No neural model, invented abstraction or global-optimality claim. Paths come only
from prior public native search; supplied Oracle paths cannot enter this catalog.
An incidence key permits label renaming and dimension rebinding with fixed
operand order. It is not full graph-isomorphism or unseen-topology discovery.
"""
from collections import Counter
import hashlib
import json
from time import perf_counter

from neumann1.contraction_structure import certify_path, validate_public


def topology_key(public):
    inputs, output, _ = validate_public(public)
    labels = {}
    for term in inputs:
        for label in term:
            if label not in labels:
                labels[label] = len(labels)
    # Axis order is represented conservatively; diagonal multiplicity is retained.
    payload = {"inputs": [[labels[x] for x in term] for term in inputs],
               "output_set": sorted(labels[x] for x in output)}
    packed = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(packed).hexdigest()


class NativePerspectiveCatalog:
    def __init__(self, records):
        self.entries = {}
        self.records = []
        seen = set()
        for record in records:
            if set(record) != {"public", "path", "source", "oracle_used", "learned"} or record["oracle_used"] is not False or record["learned"] is not False:
                raise ValueError("Public native prior only; Oracle/learned authority denied")
            if not isinstance(record["source"], dict) or not record["source"].get("sha256"):
                raise ValueError("Prior procedure provenance required")
            certify_path(record["public"], record["path"])
            key = topology_key(record["public"])
            pathkey = json.dumps(record["path"], separators=(",", ":"))
            if (key, pathkey) not in seen:
                seen.add((key, pathkey))
                # Private immutable JSON copy; caller mutation cannot alter accepted authority.
                owned = json.loads(json.dumps(record))
                self.entries.setdefault(key, []).append(owned)
                self.records.append(owned)

    def propose(self, public, *, max_work, max_intermediate_elements):
        if type(max_work) is not int or max_work <= 0 or type(max_intermediate_elements) is not int or max_intermediate_elements <= 0:
            raise ValueError("Explicit positive integer resource model budgets required")
        start = perf_counter()
        key = topology_key(public)
        entries = self.entries.get(key, [])
        choices, rejected = [], []
        for entry in entries:
            # Original goal and every dimension are checked again after rebinding.
            certificate = certify_path(public, entry["path"])
            if certificate["dense_arithmetic_work_model"] > max_work or certificate["largest_intermediate_elements"] > max_intermediate_elements:
                rejected.append({"source": entry["source"], "work_model": certificate["dense_arithmetic_work_model"],
                                 "peak_elements_model": certificate["largest_intermediate_elements"]})
            else:
                choices.append((certificate["dense_arithmetic_work_model"], certificate["largest_intermediate_elements"], entry, certificate))
        result = {"status": "CACHE_MISS" if not entries else "RESOURCE_MODEL_REJECTED",
                  "candidate_count": len(entries), "rejected": rejected, "learned": False,
                  "oracle_used": False, "novel_representation_generated": False,
                  "global_optimum_proven": False, "actual_speed_measured": False}
        if choices:
            _, _, selected, certificate = min(choices, key=lambda x: (x[0], x[1]))
            result.update(status="CERTIFIED_NATIVE_PRIOR", path=json.loads(json.dumps(selected["path"])),
                          certificate=certificate, source=json.loads(json.dumps(selected["source"])))
        result["lookup_rebind_certificate_seconds"] = perf_counter() - start
        return result

    def summary(self):
        return {"native_unique_programs": len(self.records), "topology_groups": len(self.entries),
                "programs_per_group": dict(Counter(len(v) for v in self.entries.values())),
                "learned": False, "oracle_used": False}
