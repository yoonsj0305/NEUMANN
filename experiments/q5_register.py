"""Model-free Q5 per-case registration. CLI invocation is explicit, never CI.

The atomic attempt reservation precedes scientific imports and any new source.
Failed generation/labels and all completed files survive; there is no reseed.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import sys
from pathlib import Path

# Import this via a standalone stdlib module in main, before legacy package init.


def evidence_module():
    import importlib.util
    import types
    root = Path(__file__).resolve().parents[1] / "neumann1"
    package = "_q5_stdlib"
    if package not in sys.modules:
        namespace = types.ModuleType(package)
        namespace.__path__ = [str(root)]
        sys.modules[package] = namespace
    name = package + ".q5_evidence"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, root / "q5_evidence.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def runtime():
    versions = {key: importlib.metadata.version(dist) for key, dist in (
        ("numpy", "numpy"), ("scipy", "scipy"), ("scikit_learn", "scikit-learn"),
        ("torch", "torch"), ("highspy", "highspy"), ("threadpoolctl", "threadpoolctl"))}
    return {"python": list(sys.version_info[:2]), **versions}


def hardware():
    cpu = "unavailable"
    if Path("/proc/cpuinfo").is_file():
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
    return {"system": platform.system(), "machine": platform.machine(),
            "release": platform.release(), "cpu_model": cpu,
            "logical_cpus": os.cpu_count(),
            "affinity": sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None}


def preflight():
    ev = evidence_module()
    if runtime() != ev.RUNTIME or os.environ.get("OPENBLAS_CORETYPE") != "HASWELL":
        raise RuntimeError("Q5 exact runtime / HASWELL dispatch required")
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise RuntimeError("Q5 registered hardware envelope is Linux x86_64")
    from threadpoolctl import threadpool_info
    pools = threadpool_info()
    if not pools or any(p["num_threads"] != 1 for p in pools):
        raise RuntimeError("Q5 one-thread numerical execution required")
    return {"runtime": runtime(), "hardware": hardware(), "threadpools": pools,
            "openblas_coretype": os.environ["OPENBLAS_CORETYPE"]}


def parent_authority():
    """Actually replay pinned bytes and original witnesses, not just metadata."""
    ev = evidence_module()
    from neumann1.lp_expand4_holdout_archive_v102 import load_first_evaluation
    path = Path("docs/experiments/results/v102_first_evaluation.manifest.json")
    manifest = json.loads(path.read_text())
    report = load_first_evaluation(path)
    ev.contract.validate_authority(manifest, report["training_identity"])
    return manifest, report["training_identity"]


def raw_source(source):
    from neumann1 import lp_portfolio_v084 as storage
    m, n = source["rows"], source["cols"]
    raw = {k: storage.decode_array(source["arrays"][k], shape)
           for k, shape in (("A", (m, n)), ("b", (m,)), ("c", (n,)))}
    if storage.input_digest(raw) != source["sha256"]:
        raise ValueError("Q5 original input digest drift")
    return raw


def validate_source(source, metadata, *, oracle=True):
    ev = evidence_module()
    if {k: source[k] for k in metadata} != metadata or type(source["surface"]) is not bool:
        raise ValueError("Q5 source metadata drift")
    raw = raw_source(source)
    if oracle:
        from neumann1.lp_certificate_v081 import verify_standard_form_certificate
        basis = source["label"]["indices"]
        if (source["label"]["accepted"] is not True or len(basis) != metadata["rows"]
                or len(set(basis)) != len(basis)
                or any(type(i) is not int or not 0 <= i < metadata["cols"] for i in basis)
                or not verify_standard_form_certificate(**raw, **source["label"]["witness"])["accepted"]):
            raise ValueError("Q5 original oracle witness/basis rejected")
    return raw


def load_registered(directory, *, verify=True):
    ev = evidence_module()
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    if (manifest["schema"] != "neumann.q5-sources.v1" or manifest["status"] != "sources_frozen"
            or manifest["contract"] != ev.contract.protocol() or manifest["rerun"] is not False
            or manifest["model_access"] is not False or manifest["route_evaluation"] is not False):
        raise ValueError("Q5 registered source contract drift")
    ev.head_sha(manifest["frozen_head"])
    if (manifest["seed_collision_audit_head"] != manifest["frozen_head"]
            or manifest["environment"]["runtime"] != ev.RUNTIME
            or manifest["environment"]["openblas_coretype"] != "HASWELL"
            or not manifest["environment"]["threadpools"]
            or any(p["num_threads"] != 1 for p in manifest["environment"]["threadpools"])
            or manifest["environment"]["hardware"]["system"] != "Linux"
            or manifest["environment"]["hardware"]["machine"] != "x86_64"):
        raise ValueError("Q5 source runtime/hardware/collision-audit drift")
    entries = manifest["cases"]
    ev.contract.validate_source_metadata([e["metadata"] for e in entries])
    if len({e["identity"]["file"] for e in entries}) != len(entries):
        raise ValueError("Q5 duplicate source archive")
    rows, terminal = ev.read_events(directory)
    if terminal["status"] != "sources_frozen" or terminal["manifest_sha256"] != ev.digest(ev.canonical(manifest)):
        raise ValueError("Q5 source completion identity drift")
    reservation = json.loads((directory / "reservation.json").read_text())
    if reservation != {"schema": "neumann.q5-attempt.v1", "stage": "source_registration",
                        "frozen_head": manifest["frozen_head"], "rerun": False}:
        raise ValueError("Q5 source first reservation drift")
    frozen = [r["payload"] for r in rows if r["kind"] == "source"]
    if frozen != entries:
        raise ValueError("Q5 first source ledger/manifest drift")
    if verify:
        seen = set()
        base_raw = None
        for entry in entries:
            source = ev.unpack_case(directory, entry["identity"])
            raw = validate_source(source, entry["metadata"])
            if source["sha256"] in seen:
                raise ValueError("Q5 original digest collision")
            seen.add(source["sha256"])
            if source["surface"]:
                from experiments.lp_expand4_holdout_register_v102 import _surface
                from neumann1 import lp_portfolio_v084 as storage
                equivalent = _surface(base_raw, source["seed"] + ev.contract.protocol()["surface_seed_offset"])
                if storage.input_digest(equivalent) != source["sha256"]:
                    raise ValueError("Q5 retained base/surface equivalence drift")
                base_raw = None
            else:
                base_raw = raw
    return manifest


def register(directory, frozen_head, *, collision_check_head):
    ev = evidence_module()
    attempt = ev.Attempt(directory, "source_registration", frozen_head)
    completed = []
    try:
        # Explicit publication checkpoint: the caller must audit latest repository
        # seed use, and pin that audited head. No automatic outcome-based reseed.
        ev.head_sha(collision_check_head)
        if collision_check_head != frozen_head:
            raise ValueError("latest seed collision audit must pin execution head")
        from threadpoolctl import threadpool_limits
        from neumann1 import lp_portfolio_v084 as storage
        from neumann1.lp_basis_headroom_v082 import generate_q5_case
        from experiments.lp_expand4_holdout_register_v102 import _surface
        with threadpool_limits(1):
            environment = preflight()
            authority, training = parent_authority()
            attempt.append("preflight", {**environment, "authority_gzip_sha256": authority["gzip_sha256"],
                                         "seed_collision_audit_head": collision_check_head})
            specs = ev.contract.planned_views()
            for offset in range(0, len(specs), 2):
                base = specs[offset]
                case = generate_q5_case({"id": base["pair_id"], "pair_id": base["pair_id"],
                    "rows": base["rows"], "cols": base["cols"], "width_factor": base["width_factor"],
                    "condition_number": base["condition"], "replicate": base["replicate"], "seed": base["seed"]})
                A, b, c = storage.normalized(case["A"], case["b"], case["c"])
                raw = {"A": A, "b": b, "c": c}
                for metadata in specs[offset:offset+2]:
                    view = (_surface(raw, base["seed"] + ev.contract.protocol()["surface_seed_offset"])
                            if metadata["surface"] else raw)
                    label = storage.candidate_once(view, case["oracle_basis"], "q5_registration_oracle_only")
                    source = {**metadata, "sha256": storage.input_digest(view),
                              "arrays": {k: storage.encode_array(v) for k, v in view.items()}, "label": label}
                    # Retain rejected labels and arrays BEFORE stopping registration.
                    identity = ev.pack_case(attempt.path, metadata["id"] + ".json.gz", source)
                    entry = {"metadata": metadata, "identity": identity}
                    attempt.append("source", entry)
                    completed.append(entry)
                    validate_source(source, metadata)
            manifest = {"schema": "neumann.q5-sources.v1", "status": "sources_frozen",
                "frozen_head": frozen_head, "seed_collision_audit_head": collision_check_head,
                "contract": ev.contract.protocol(), "environment": environment,
                "model_access": False, "route_evaluation": False, "timing_evidence": False,
                "research_label_costs_retained_not_inference": True,
                "authority_gzip_sha256": authority["gzip_sha256"], "training_identity": training,
                "cases": completed, "rerun": False}
            ev.write_json(attempt.path / "manifest.json", manifest)
            attempt.finish("sources_frozen", manifest_sha256=ev.digest(ev.canonical(manifest)))
            return manifest
    except BaseException as exc:
        attempt.finish("registration_failed_no_reseed", completed_views=len(completed),
                       error=f"{type(exc).__name__}: {exc}")
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--frozen-head", required=True)
    parser.add_argument("--seed-collision-audit-head", required=True)
    args = parser.parse_args()
    manifest = register(args.output, args.frozen_head, collision_check_head=args.seed_collision_audit_head)
    print(json.dumps({"status": manifest["status"], "views": len(manifest["cases"])}, sort_keys=True))


if __name__ == "__main__":
    main()
