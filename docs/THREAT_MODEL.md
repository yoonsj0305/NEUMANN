# NEUMANN 1 Threat Model v1

## Purpose

This document defines what the NEUMANN plugin trust plane currently protects, detects, contains, and explicitly does not protect.

The threat model is intentionally narrower than a generic application-security checklist. It covers the plugin discovery, activation, authorization, and execution path implemented through v0.0.17.

## Protected assets

- execution authority
- exact manifest identity
- authorization history
- host integrity
- solver-result integrity
- external checkpoint integrity

## Trust boundaries

1. Static discovery
2. Activation
3. Managed runtime dispatch
4. Local authorization ledger file
5. Trusted external expected-head checkpoint
6. Python process boundary

## Threat actors

- malicious plugin publisher
- installed-package tamperer
- local authorization-ledger tamperer
- host administrator capable of rollback
- approved plugin compromised after activation
- compromised NEUMANN process
- compromised checkpoint authority

## Current assurance matrix

| Scenario | Prevent | Detect | Contain | Recover | Key boundary |
|---|---|---|---|---|---|
| Unapproved activation | ENFORCED | DETECTED | ENFORCED | ENFORCED | Exact manifest approval before import |
| Manifest substitution after approval | ENFORCED | DETECTED | ENFORCED | PARTIAL | Approval bound to canonical manifest SHA-256 |
| Ledger event mutation/reordering | OUT OF SCOPE | DETECTED | ENFORCED | PARTIAL | Hash-chain verification before state reconstruction |
| Valid-prefix ledger rollback | OUT OF SCOPE | PARTIAL | PARTIAL | PARTIAL | Trusted external expected head required |
| Post-activation arbitrary plugin code | OUT OF SCOPE | OUT OF SCOPE | OUT OF SCOPE | PARTIAL | Same Python process |
| Compromised NEUMANN process | OUT OF SCOPE | OUT OF SCOPE | OUT OF SCOPE | OUT OF SCOPE | In-process controls cannot defend against process owner |
| Compromised checkpoint authority | OUT OF SCOPE | OUT OF SCOPE | OUT OF SCOPE | OUT OF SCOPE | Current trusted-head assumption |

## What NEUMANN can currently claim

- Static discovery does not import plugin code.
- Unapproved exact manifests cannot activate through the managed activation path.
- Changed manifests are not covered by old digest-bound approvals.
- Use-time revocation prevents future managed solver dispatch.
- Post-revocation solver actions are zero in the tested managed path.
- Persisted authorization event mutation and reordering are detected on reload.
- Valid-prefix rollback can be detected when an uncompromised expected head is supplied externally.

## What NEUMANN must NOT currently claim

- Publisher authenticity.
- Safe execution of approved plugin code.
- Sandboxing or capability enforcement after Python import.
- Defense against a compromised NEUMANN process.
- Rollback-proof authorization storage without an external trust anchor.
- Tamper-proof storage.
- Multi-host or distributed revocation consistency.

## Why signatures are not automatically the next step

A signature can establish who signed a package or manifest. It does not contain what the signed code can do after import.

Today, an approved plugin runs inside the NEUMANN Python process. A correctly signed but malicious or compromised plugin could still access process-level capabilities available to ordinary Python code.

Therefore the highest-impact uncovered runtime boundary is **post-activation containment**.

## v0.0.18 recommendation

Next implementation priority:

**Out-of-process plugin isolation**

Minimum target properties for the next experiment:
- plugin compiler/solver/verifier execute outside the NEUMANN core process
- explicit request/response protocol
- bounded message schema
- crash/timeout fails closed
- revocation stops new requests
- plugin process cannot directly mutate core in-memory authorization state

Publisher signatures remain important, but they should follow or accompany a clear execution-isolation boundary rather than substitute for one.

## Claim discipline

Threat-model statements are represented in code in `neumann1.threat_model`.

Strong assurance labels (`ENFORCED`, `DETECTED`) require explicit evidence identifiers. This does not prove formal verification, but it prevents unsupported security language from becoming part of the project contract.