from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .plugin_authorization import AuthorizationEvent, AuthorizationState
from .plugin_manifest import PluginManifest


PERSISTENT_LEDGER_VERSION = "neumann.authorization.ledger.v1"
GENESIS_HASH = "0" * 64


class LedgerIntegrityError(RuntimeError):
    pass


@dataclass(frozen=True)
class LedgerCheckpoint:
    ledger_version: str
    sequence: int
    head_sha256: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "ledger_version": self.ledger_version,
            "sequence": self.sequence,
            "head_sha256": self.head_sha256,
        }


def _canonical_bytes(record: dict[str, Any]) -> bytes:
    return json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _event_hash(record_without_hash: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(record_without_hash)).hexdigest()


class HashChainedAuthorizationLedger:
    """Durable single-writer authorization ledger with a verified hash chain.

    The ledger detects record mutation, reordering, malformed sequence numbers,
    broken predecessor links, and partial-file corruption on reload.

    Full rollback/truncation to an older *valid* prefix cannot be distinguished
    from a genuinely older ledger unless a trusted expected head/checkpoint is
    supplied from outside the ledger file.
    """

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        expected_head_sha256: str | None = None,
    ):
        self.path = Path(path)
        self._events: list[AuthorizationEvent] = []
        self._current: dict[str, AuthorizationState] = {}
        self._sequence = 0
        self._head_sha256 = GENESIS_HASH

        if self.path.exists():
            self._load_and_verify()
        elif expected_head_sha256 not in (None, GENESIS_HASH):
            raise LedgerIntegrityError(
                "trusted expected head supplied but ledger file does not exist"
            )

        if expected_head_sha256 is not None and self._head_sha256 != expected_head_sha256:
            raise LedgerIntegrityError(
                "ledger head differs from trusted expected head; possible rollback or truncation"
            )

    @property
    def head_sha256(self) -> str:
        return self._head_sha256

    @property
    def sequence(self) -> int:
        return self._sequence

    def checkpoint(self) -> LedgerCheckpoint:
        return LedgerCheckpoint(
            ledger_version=PERSISTENT_LEDGER_VERSION,
            sequence=self._sequence,
            head_sha256=self._head_sha256,
        )

    def events(self) -> tuple[AuthorizationEvent, ...]:
        return tuple(self._events)

    def current(self, plugin_id: str) -> AuthorizationState | None:
        return self._current.get(plugin_id)

    def _apply_event(self, event: AuthorizationEvent) -> None:
        self._events.append(event)
        self._current[event.plugin_id] = AuthorizationState(
            plugin_id=event.plugin_id,
            manifest_digest_sha256=event.manifest_digest_sha256,
            active=(event.action == "APPROVE"),
            sequence=event.sequence,
        )
        self._sequence = event.sequence

    def _load_and_verify(self) -> None:
        raw = self.path.read_bytes()
        if not raw:
            return

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise LedgerIntegrityError("ledger is not valid UTF-8") from exc

        expected_sequence = 1
        previous_hash = GENESIS_HASH

        lines = text.splitlines()
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                raise LedgerIntegrityError(f"blank ledger record at line {line_number}")
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise LedgerIntegrityError(
                    f"invalid JSON ledger record at line {line_number}"
                ) from exc
            if not isinstance(record, dict):
                raise LedgerIntegrityError(f"ledger record {line_number} is not an object")

            required = {
                "ledger_version",
                "sequence",
                "action",
                "plugin_id",
                "manifest_digest_sha256",
                "reason",
                "prev_hash",
                "event_hash",
            }
            if set(record) != required:
                raise LedgerIntegrityError(
                    f"ledger record {line_number} has unexpected field set"
                )
            if record["ledger_version"] != PERSISTENT_LEDGER_VERSION:
                raise LedgerIntegrityError(
                    f"unsupported ledger version at line {line_number}"
                )
            if record["sequence"] != expected_sequence:
                raise LedgerIntegrityError(
                    f"non-contiguous ledger sequence at line {line_number}"
                )
            if record["action"] not in {"APPROVE", "REVOKE"}:
                raise LedgerIntegrityError(f"invalid action at line {line_number}")
            if record["prev_hash"] != previous_hash:
                raise LedgerIntegrityError(
                    f"broken predecessor hash at line {line_number}"
                )

            supplied_hash = record["event_hash"]
            body = dict(record)
            del body["event_hash"]
            computed_hash = _event_hash(body)
            if supplied_hash != computed_hash:
                raise LedgerIntegrityError(
                    f"event hash mismatch at line {line_number}"
                )

            event = AuthorizationEvent(
                sequence=int(record["sequence"]),
                action=str(record["action"]),
                plugin_id=str(record["plugin_id"]),
                manifest_digest_sha256=(
                    None
                    if record["manifest_digest_sha256"] is None
                    else str(record["manifest_digest_sha256"])
                ),
                reason=str(record["reason"]),
            )
            self._apply_event(event)
            previous_hash = supplied_hash
            expected_sequence += 1

        self._head_sha256 = previous_hash

    def _append(
        self,
        action: str,
        plugin_id: str,
        digest: str | None,
        reason: str,
    ) -> AuthorizationEvent:
        if action not in {"APPROVE", "REVOKE"}:
            raise ValueError(f"unsupported authorization action: {action}")

        sequence = self._sequence + 1
        body = {
            "ledger_version": PERSISTENT_LEDGER_VERSION,
            "sequence": sequence,
            "action": action,
            "plugin_id": plugin_id,
            "manifest_digest_sha256": digest,
            "reason": reason,
            "prev_hash": self._head_sha256,
        }
        event_hash = _event_hash(body)
        record = dict(body)
        record["event_hash"] = event_hash
        line = json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ) + "\n"

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())

        event = AuthorizationEvent(
            sequence=sequence,
            action=action,
            plugin_id=plugin_id,
            manifest_digest_sha256=digest,
            reason=reason,
        )
        self._apply_event(event)
        self._head_sha256 = event_hash
        return event

    def approve(self, manifest: PluginManifest, reason: str = "") -> AuthorizationEvent:
        manifest.validate()
        return self._append(
            "APPROVE",
            manifest.plugin_id,
            manifest.digest_sha256,
            reason,
        )

    def revoke(self, plugin_id: str, reason: str = "") -> AuthorizationEvent:
        current = self._current.get(plugin_id)
        digest = current.manifest_digest_sha256 if current else None
        return self._append("REVOKE", plugin_id, digest, reason)

    def require_manifest(self, manifest: PluginManifest) -> None:
        self.require_binding(manifest.plugin_id, manifest.digest_sha256)

    def require_binding(self, plugin_id: str, manifest_digest_sha256: str) -> None:
        state = self._current.get(plugin_id)
        if state is None:
            raise PermissionError(f"plugin has no approval: {plugin_id}")
        if not state.active:
            raise PermissionError(f"plugin authorization revoked: {plugin_id}")
        if state.manifest_digest_sha256 != manifest_digest_sha256:
            raise PermissionError(
                f"approved manifest digest differs for {plugin_id}"
            )