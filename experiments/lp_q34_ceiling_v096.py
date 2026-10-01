"""v0.0.96: replay-only Q34 representation ceiling over v0.0.94 evidence."""
from neumann1.lp_input_archive_v094 import load_archive
from experiments import lp_input_probe_v094 as prior

SEEDS = (87001, 87002)
MANIFEST = "docs/experiments/results/v094_first_probe.manifest.json"


def protocol():
    return {
        "schema": "neumann.q34-representation-ceiling-v096.v1",
        "source": "v094_first_probe",
        "cases": 48,
        "seeds": list(SEEDS),
        "utility_floor": 0.80,
        "full_information_certificate_gain": 4,
        "new_fitting": False,
        "new_inference": False,
        "new_solver_calls": False,
        "timing": False,
        "final_evaluation": False,
        "q34_pass_claim": False,
        "global_q3": "OPEN",
        "global_q4": "OPEN",
    }


def _recall(label, support):
    label = set(label)
    support = set(support)
    if not label:
        raise ValueError("empty label")
    return len(label & support) / len(label)


def summarize(report, sources):
    records = {(r["case_id"], r["route"]): r for r in report["records"]}
    labels = {s["id"]: tuple(s["label"]["indices"]) for s in sources}
    if len(labels) != protocol()["cases"]:
        raise ValueError("source coverage drift")

    tests = []
    for seed in SEEDS:
        on_contained = 0
        on_recall = []
        full_short_contained = 0
        full_short_recall = []
        compact_short_contained = 0
        compact_short_recall = []
        cert = {"point": 0, "full": 0, "compact": 0}
        rows = []

        for case_id, label_tuple in labels.items():
            label = set(label_tuple)
            point = records[(case_id, f"point_s{seed}")]
            full = records[(case_id, f"full_s{seed}")]
            compact = records[(case_id, f"compact_s{seed}")]

            early_on = set(point["selected"])
            early_off = set(full["selected"])
            if len(early_off) < len(early_on) or not label.issubset(early_off):
                raise ValueError("full-information authority drift")
            if set(compact["selected"]) != early_on:
                raise ValueError("early-compression support drift")

            on_hit = label.issubset(early_on)
            full_hit = label.issubset(full["shortlist"])
            compact_hit = label.issubset(compact["shortlist"])
            on_contained += int(on_hit)
            full_short_contained += int(full_hit)
            compact_short_contained += int(compact_hit)
            on_recall.append(_recall(label, early_on))
            full_short_recall.append(_recall(label, full["shortlist"]))
            compact_short_recall.append(_recall(label, compact["shortlist"]))

            for name, row in (("point", point), ("full", full), ("compact", compact)):
                cert[name] += int(row["candidate"]["accepted"])

            rows.append({
                "case_id": case_id,
                "early_on_contains_label_basis": on_hit,
                "early_on_label_recall": on_recall[-1],
                "full_shortlist_contains_label_basis": full_hit,
                "compact_shortlist_contains_label_basis": compact_hit,
                "point_certificate": bool(point["candidate"]["accepted"]),
                "full_certificate": bool(full["candidate"]["accepted"]),
                "compact_certificate": bool(compact["candidate"]["accepted"]),
            })

        adequate = on_contained / len(labels) >= protocol()["utility_floor"]
        full_gain = cert["full"] - cert["compact"]
        tests.append({
            "seed": seed,
            "early_on_full_basis_containment": on_contained,
            "early_on_containment_rate": on_contained / len(labels),
            "early_on_mean_label_recall": sum(on_recall) / len(on_recall),
            "early_off_full_basis_containment": len(labels),
            "early_off_containment_rate": 1.0,
            "full_graph_shortlist_containment": full_short_contained,
            "full_graph_mean_label_recall": sum(full_short_recall) / len(full_short_recall),
            "compact_graph_shortlist_containment": compact_short_contained,
            "compact_graph_mean_label_recall": sum(compact_short_recall) / len(compact_short_recall),
            "point_certificates": cert["point"],
            "full_certificates": cert["full"],
            "compact_certificates": cert["compact"],
            "full_information_certificate_gain": full_gain,
            "representation_ceiling_adequate": adequate,
            "full_information_rescue": full_gain >= protocol()["full_information_certificate_gain"],
            "rows": rows,
        })

    if not all(t["representation_ceiling_adequate"] for t in tests):
        decision = "EARLY_REPRESENTATION_CEILING_BELOW_Q34_FLOOR"
    elif all(t["full_information_rescue"] for t in tests):
        decision = "FULL_INFORMATION_RESCUES_CURRENT_DISCOVERER"
    else:
        decision = "DISCOVERER_BOTTLENECK_DOMINATES_EARLY_SUPPORT_LOSS"

    return {
        "protocol": protocol(),
        "decision": decision,
        "tests": tests,
        "cost_claim": False,
        "q34_pass_claim": False,
        "global_q3": "OPEN",
        "global_q4": "OPEN",
    }


def analyze():
    report = load_archive(MANIFEST)
    prior.validate(report)
    original, _ = prior.parents()
    return summarize(report, original["train_sources"])
