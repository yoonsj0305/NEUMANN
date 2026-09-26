from __future__ import annotations

import json

from neumann1.threat_model import (
    assurance_counts,
    default_threat_model,
    next_control_priority,
    unresolved_host_integrity_scenarios,
)


def run():
    scenarios = default_threat_model()
    unresolved = unresolved_host_integrity_scenarios(scenarios)
    return {
        "threat_model_version": "neumann.threat-model.v1",
        "scenario_count": len(scenarios),
        "assurance_counts_across_prevent_detect_contain_recover": assurance_counts(scenarios),
        "uncontained_host_integrity_scenarios": [s.scenario_id for s in unresolved],
        "next_control_priority": next_control_priority(scenarios),
        "key_boundaries": {
            "publisher_authenticity": "not established",
            "post_activation_plugin_containment": "not enforced",
            "compromised_neumann_process": "out of scope",
            "rollback_detection": "requires trusted external head for valid-prefix rollback",
        },
        "interpretation": (
            "Current trust controls are strongest around discovery, exact-manifest approval, "
            "managed dispatch revocation, and persisted-ledger integrity. The largest remaining "
            "runtime gap is that approved plugin code executes inside the NEUMANN Python process. "
            "Therefore process isolation is the next control priority before claiming a stronger plugin trust plane."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))