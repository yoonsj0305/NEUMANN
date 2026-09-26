from __future__ import annotations

import json
from pathlib import Path
import tempfile

from neumann1.plugin_manifest import PLUGIN_MANIFEST_VERSION, PluginManifest
from neumann1.persistent_authorization import (
    HashChainedAuthorizationLedger,
    LedgerIntegrityError,
)


def make_manifest():
    return PluginManifest.from_dict({
        "manifest_version": PLUGIN_MANIFEST_VERSION,
        "plugin_id": "benchmark.persistent_plugin",
        "plugin_version": "0.1.0",
        "family_id": "benchmark.persistent",
        "kind": "benchmark.persistent",
        "family_contract_version": "neumann.family.v1",
        "entry_point": "benchmark_persistent:factory",
        "capabilities": ["compile", "solve", "verify", "cpu"],
    })


def run():
    m = make_manifest()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "authorization.jsonl"
        ledger = HashChainedAuthorizationLedger(path)
        ledger.approve(m, "approve")
        ledger.revoke(m.plugin_id, "revoke")
        ledger.approve(m, "reapprove")
        trusted = ledger.checkpoint()

        reloaded = HashChainedAuthorizationLedger(
            path, expected_head_sha256=trusted.head_sha256
        )
        restart_state_preserved = (
            reloaded.sequence == 3
            and reloaded.current(m.plugin_id) is not None
            and reloaded.current(m.plugin_id).active
        )

        original_lines = path.read_text(encoding="utf-8").splitlines()

        # Mutation proof.
        mutated_path = Path(tmp) / "mutated.jsonl"
        mutated_records = [json.loads(line) for line in original_lines]
        mutated_records[0]["reason"] = "tampered"
        mutated_path.write_text(
            "\n".join(json.dumps(r, sort_keys=True) for r in mutated_records) + "\n",
            encoding="utf-8",
        )
        mutation_detected = False
        try:
            HashChainedAuthorizationLedger(mutated_path)
        except LedgerIntegrityError:
            mutation_detected = True

        # Whole-event truncation is a valid old prefix without an external checkpoint.
        truncated_path = Path(tmp) / "truncated.jsonl"
        truncated_path.write_text(
            "\n".join(original_lines[:2]) + "\n", encoding="utf-8"
        )
        prefix_loads_without_checkpoint = True
        try:
            old = HashChainedAuthorizationLedger(truncated_path)
            prefix_sequence = old.sequence
        except LedgerIntegrityError:
            prefix_loads_without_checkpoint = False
            prefix_sequence = None

        truncation_detected_with_checkpoint = False
        try:
            HashChainedAuthorizationLedger(
                truncated_path, expected_head_sha256=trusted.head_sha256
            )
        except LedgerIntegrityError:
            truncation_detected_with_checkpoint = True

        return {
            "events_persisted": len(reloaded.events()),
            "restart_state_preserved": restart_state_preserved,
            "trusted_sequence": trusted.sequence,
            "trusted_head_sha256": trusted.head_sha256,
            "mutation_detected": mutation_detected,
            "valid_prefix_loads_without_checkpoint": prefix_loads_without_checkpoint,
            "valid_prefix_sequence": prefix_sequence,
            "truncation_detected_with_trusted_checkpoint": truncation_detected_with_checkpoint,
            "boundary": (
                "The local hash chain detects mutation/reordering/corruption. A complete "
                "rollback to an older valid prefix requires an externally trusted head/checkpoint "
                "to detect. This is durable tamper-evidence, not tamper-proof storage."
            ),
        }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))