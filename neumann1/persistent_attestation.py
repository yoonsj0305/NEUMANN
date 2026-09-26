from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .lifecycle_attestation import AttestationStatus, LifecycleAttestation
from .plugin_manifest import PluginManifest


PERSISTENT_ATTESTATION_LEDGER_VERSION = "neumann.lifecycle-attestation.ledger.v1"
ATTESTATION_GENESIS_HASH = "0" * 64


class AttestationLedgerIntegrityError(RuntimeError):
    pass


@dataclass(frozen=True)
class AttestationLedgerCheckpoint:
    ledger_version: str
    sequence: int
    head_sha256: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "ledger_version": self.ledger_version,
            "sequence": self.sequence,
            "head_sha256": self.head_sha256,
        }


@dataclass(frozen=True)
class AttestationLedgerEvent:
    sequence: int
    action: str
    plugin_id: str
    manifest_digest_sha256: str
    attestation_digest_sha256: str
    corpus_digest_sha256: str
    reason: str = ""


@dataclass(frozen=True)
class AttestationEvidenceState:
    plugin_id: str
    manifest_digest_sha256: str
    attestation_digest_sha256: str
    corpus_digest_sha256: str
    active: bool
    sequence: int
    attestation: LifecycleAttestation


def _canonical_bytes(record: dict[str, Any]) -> bytes:
    return json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _event_hash(record_without_hash: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(record_without_hash)).hexdigest()


class HashChainedAttestationLedger:
    """Durable exact-artifact lifecycle-evidence ledger.

    ISSUE persists a complete LifecycleAttestation. REVOKE removes that exact
    manifest's current evidence from runtime authority without deleting history.

    The local hash chain detects mutation, reordering, malformed sequence
    numbers, broken predecessor links, and partial-file corruption. As with the
    authorization ledger, rollback to an older valid prefix requires an external
    trusted expected head to detect.
    """

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        expected_head_sha256: str | None = None,
    ):
        self.path = Path(path)
        self._events: list[AttestationLedgerEvent] = []
        self._current_by_manifest: dict[str, AttestationEvidenceState] = {}
        self._manifest_digests_by_plugin: dict[str, set[str]] = {}
        self._sequence = 0
        self._head_sha256 = ATTESTATION_GENESIS_HASH

        if self.path.exists():
            self._load_and_verify()
        elif expected_head_sha256 not in (None, ATTESTATION_GENESIS_HASH):
            raise AttestationLedgerIntegrityError(
                "trusted expected head supplied but attestation ledger file does not exist"
            )

        if expected_head_sha256 is not None and self._head_sha256 != expected_head_sha256:
            raise AttestationLedgerIntegrityError(
                "attestation ledger head differs from trusted expected head; "
                "possible rollback or truncation"
            )

    @property
    def head_sha256(self) -> str:
        return self._head_sha256

    @property
    def sequence(self) -> int:
        return self._sequence

    def checkpoint(self) -> AttestationLedgerCheckpoint:
        return AttestationLedgerCheckpoint(
            ledger_version=PERSISTENT_ATTESTATION_LEDGER_VERSION,
            sequence=self._sequence,
            head_sha256=self._head_sha256,
        )

    def events(self) -> tuple[AttestationLedgerEvent, ...]:
        return tuple(self._events)

    def current_for_manifest_digest(
        self, manifest_digest_sha256: str
    ) -> AttestationEvidenceState | None:
        return self._current_by_manifest.get(manifest_digest_sha256)

    def get(self, manifest_digest_sha256: str) -> LifecycleAttestation | None:
        state = self._current_by_manifest.get(manifest_digest_sha256)
        if state is None or not state.active:
            return None
        return state.attestation

    def _apply(
        self,
        event: AttestationLedgerEvent,
        attestation: LifecycleAttestation | None,
    ) -> None:
        self._events.append(event)
        self._manifest_digests_by_plugin.setdefault(event.plugin_id, set()).add(
            event.manifest_digest_sha256
        )

        if event.action == "ISSUE":
            if attestation is None:
                raise AttestationLedgerIntegrityError("ISSUE event missing attestation")
            state = AttestationEvidenceState(
                plugin_id=event.plugin_id,
                manifest_digest_sha256=event.manifest_digest_sha256,
                attestation_digest_sha256=event.attestation_digest_sha256,
                corpus_digest_sha256=event.corpus_digest_sha256,
                active=True,
                sequence=event.sequence,
                attestation=attestation,
            )
            self._current_by_manifest[event.manifest_digest_sha256] = state
        elif event.action == "REVOKE":
            current = self._current_by_manifest.get(event.manifest_digest_sha256)
            if current is None:
                raise AttestationLedgerIntegrityError(
                    "REVOKE event has no preceding attestation for manifest"
                )
            if current.plugin_id != event.plugin_id:
                raise AttestationLedgerIntegrityError("REVOKE plugin identity mismatch")
            if current.attestation_digest_sha256 != event.attestation_digest_sha256:
                raise AttestationLedgerIntegrityError(
                    "REVOKE attestation digest does not match current evidence"
                )
            if current.corpus_digest_sha256 != event.corpus_digest_sha256:
                raise AttestationLedgerIntegrityError(
                    "REVOKE corpus digest does not match current evidence"
                )
            self._current_by_manifest[event.manifest_digest_sha256] = (
                AttestationEvidenceState(
                    plugin_id=current.plugin_id,
                    manifest_digest_sha256=current.manifest_digest_sha256,
                    attestation_digest_sha256=current.attestation_digest_sha256,
                    corpus_digest_sha256=current.corpus_digest_sha256,
                    active=False,
                    sequence=event.sequence,
                    attestation=current.attestation,
                )
            )
        else:
            raise AttestationLedgerIntegrityError(
                f"unsupported attestation action: {event.action}"
            )
        self._sequence = event.sequence

    def _load_and_verify(self) -> None:
        raw = self.path.read_bytes()
        if not raw:
            return
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AttestationLedgerIntegrityError(
                "attestation ledger is not valid UTF-8"
            ) from exc

        expected_sequence = 1
        previous_hash = ATTESTATION_GENESIS_HASH
        required = {
            "ledger_version",
            "sequence",
            "action",
            "plugin_id",
            "manifest_digest_sha256",
            "attestation_digest_sha256",
            "corpus_digest_sha256",
            "attestation",
            "reason",
            "prev_hash",
            "event_hash",
        }

        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                raise AttestationLedgerIntegrityError(
                    f"blank attestation ledger record at line {line_number}"
                )
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AttestationLedgerIntegrityError(
                    f"invalid JSON attestation ledger record at line {line_number}"
                ) from exc
            if not isinstance(record, dict):
                raise AttestationLedgerIntegrityError(
                    f"attestation ledger record {line_number} is not an object"
                )
            if set(record) != required:
                raise AttestationLedgerIntegrityError(
                    f"attestation ledger record {line_number} has unexpected field set"
                )
            if record["ledger_version"] != PERSISTENT_ATTESTATION_LEDGER_VERSION:
                raise AttestationLedgerIntegrityError(
                    f"unsupported attestation ledger version at line {line_number}"
                )
            if record["sequence"] != expected_sequence:
                raise AttestationLedgerIntegrityError(
                    f"non-contiguous attestation ledger sequence at line {line_number}"
                )
            if record["action"] not in {"ISSUE", "REVOKE"}:
                raise AttestationLedgerIntegrityError(
                    f"invalid attestation action at line {line_number}"
                )
            if record["prev_hash"] != previous_hash:
                raise AttestationLedgerIntegrityError(
                    f"broken attestation predecessor hash at line {line_number}"
                )

            supplied_hash = str(record["event_hash"])
            body = dict(record)
            del body["event_hash"]
            if supplied_hash != _event_hash(body):
                raise AttestationLedgerIntegrityError(
                    f"attestation event hash mismatch at line {line_number}"
                )

            action = str(record["action"])
            attestation = None
            if action == "ISSUE":
                if not isinstance(record["attestation"], dict):
                    raise AttestationLedgerIntegrityError(
                        f"ISSUE record missing attestation at line {line_number}"
                    )
                try:
                    attestation = LifecycleAttestation.from_dict(record["attestation"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise AttestationLedgerIntegrityError(
                        f"invalid lifecycle attestation at line {line_number}"
                    ) from exc
                if attestation.plugin_id != str(record["plugin_id"]):
                    raise AttestationLedgerIntegrityError(
                        f"attestation plugin identity mismatch at line {line_number}"
                    )
                if attestation.manifest_digest_sha256 != str(
                    record["manifest_digest_sha256"]
                ):
                    raise AttestationLedgerIntegrityError(
                        f"attestation manifest digest mismatch at line {line_number}"
                    )
                if attestation.digest_sha256 != str(
                    record["attestation_digest_sha256"]
                ):
                    raise AttestationLedgerIntegrityError(
                        f"attestation digest mismatch at line {line_number}"
                    )
                if attestation.corpus_digest_sha256 != str(
                    record["corpus_digest_sha256"]
                ):
                    raise AttestationLedgerIntegrityError(
                        f"attestation corpus digest mismatch at line {line_number}"
                    )
            elif record["attestation"] is not None:
                raise AttestationLedgerIntegrityError(
                    f"REVOKE record must not embed attestation at line {line_number}"
                )

            event = AttestationLedgerEvent(
                sequence=int(record["sequence"]),
                action=action,
                plugin_id=str(record["plugin_id"]),
                manifest_digest_sha256=str(record["manifest_digest_sha256"]),
                attestation_digest_sha256=str(record["attestation_digest_sha256"]),
                corpus_digest_sha256=str(record["corpus_digest_sha256"]),
                reason=str(record["reason"]),
            )
            self._apply(event, attestation)
            previous_hash = supplied_hash
            expected_sequence += 1

        self._head_sha256 = previous_hash

    def _append(
        self,
        *,
        action: str,
        plugin_id: str,
        manifest_digest_sha256: str,
        attestation_digest_sha256: str,
        corpus_digest_sha256: str,
        attestation: LifecycleAttestation | None,
        reason: str,
    ) -> AttestationLedgerEvent:
        sequence = self._sequence + 1
        body = {
            "ledger_version": PERSISTENT_ATTESTATION_LEDGER_VERSION,
            "sequence": sequence,
            "action": action,
            "plugin_id": plugin_id,
            "manifest_digest_sha256": manifest_digest_sha256,
            "attestation_digest_sha256": attestation_digest_sha256,
            "corpus_digest_sha256": corpus_digest_sha256,
            "attestation": None if attestation is None else attestation.to_dict(),
            "reason": reason,
            "prev_hash": self._head_sha256,
        }
        event_hash = _event_hash(body)
        record = dict(body)
        record["event_hash"] = event_hash
        line = json.dumps(
            record, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ) + "\n"

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())

        event = AttestationLedgerEvent(
            sequence=sequence,
            action=action,
            plugin_id=plugin_id,
            manifest_digest_sha256=manifest_digest_sha256,
            attestation_digest_sha256=attestation_digest_sha256,
            corpus_digest_sha256=corpus_digest_sha256,
            reason=reason,
        )
        self._apply(event, attestation)
        self._head_sha256 = event_hash
        return event

    def issue(
        self, attestation: LifecycleAttestation, reason: str = ""
    ) -> AttestationLedgerEvent:
        attestation.validate()
        return self._append(
            action="ISSUE",
            plugin_id=attestation.plugin_id,
            manifest_digest_sha256=attestation.manifest_digest_sha256,
            attestation_digest_sha256=attestation.digest_sha256,
            corpus_digest_sha256=attestation.corpus_digest_sha256,
            attestation=attestation,
            reason=reason,
        )

    register = issue

    def revoke_manifest(
        self, manifest: PluginManifest, reason: str = ""
    ) -> AttestationLedgerEvent:
        manifest.validate()
        state = self._current_by_manifest.get(manifest.digest_sha256)
        if state is None:
            raise KeyError(
                f"no lifecycle attestation for manifest: {manifest.digest_sha256}"
            )
        if state.plugin_id != manifest.plugin_id:
            raise ValueError("attestation plugin identity mismatch")
        return self._append(
            action="REVOKE",
            plugin_id=state.plugin_id,
            manifest_digest_sha256=state.manifest_digest_sha256,
            attestation_digest_sha256=state.attestation_digest_sha256,
            corpus_digest_sha256=state.corpus_digest_sha256,
            attestation=None,
            reason=reason,
        )

    def revoke_attestation(
        self, attestation_digest_sha256: str, reason: str = ""
    ) -> AttestationLedgerEvent:
        matches = [
            state
            for state in self._current_by_manifest.values()
            if state.active
            and state.attestation_digest_sha256 == attestation_digest_sha256
        ]
        if len(matches) != 1:
            raise KeyError(
                "active lifecycle attestation digest not found or not unique"
            )
        state = matches[0]
        return self._append(
            action="REVOKE",
            plugin_id=state.plugin_id,
            manifest_digest_sha256=state.manifest_digest_sha256,
            attestation_digest_sha256=state.attestation_digest_sha256,
            corpus_digest_sha256=state.corpus_digest_sha256,
            attestation=None,
            reason=reason,
        )

    def require_manifest(self, manifest: PluginManifest) -> LifecycleAttestation:
        manifest.validate()
        state = self._current_by_manifest.get(manifest.digest_sha256)
        if state is None:
            known = self._manifest_digests_by_plugin.get(manifest.plugin_id, set())
            if known:
                raise PermissionError(
                    "lifecycle attestation is stale or bound to a different manifest digest"
                )
            raise PermissionError(
                "passing lifecycle attestation required for persistent execution"
            )
        if state.plugin_id != manifest.plugin_id:
            raise PermissionError("lifecycle attestation plugin identity mismatch")
        if not state.active:
            raise PermissionError("lifecycle attestation revoked")
        attestation = state.attestation
        attestation.validate()
        if attestation.status != AttestationStatus.PASS:
            raise PermissionError("lifecycle attestation did not pass")
        if attestation.manifest_digest_sha256 != manifest.digest_sha256:
            raise PermissionError("lifecycle attestation manifest identity mismatch")
        if attestation.worker_state_class != manifest.worker_state_class:
            raise PermissionError("lifecycle attestation state-class mismatch")
        if attestation.digest_sha256 != state.attestation_digest_sha256:
            raise PermissionError("lifecycle attestation digest mismatch")
        return attestation
