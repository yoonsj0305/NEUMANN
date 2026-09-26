# NEUMANN 1 Threat Model v2

## Why v2 exists

Threat Model v1 was frozen before v0.0.19.

v0.0.19 changed a major trust boundary: external plugin compiler, solver, and verifier code can now execute in child Python processes rather than inside the NEUMANN core process.

v2 preserves v1 for historical reproducibility and reassesses only the changed boundary.

## New distinction

v1 grouped post-activation arbitrary plugin code under one broad host-integrity risk.

v2 separates:

1. **Direct core Python-runtime mutation**
2. **Host capability abuse from a same-user child process**

## Direct core runtime mutation

Current status:
- process boundary: present
- plugin module imported into core process on isolated path: no
- JSON RPC boundary: present
- direct shared Python module/global state: separated

Assurance:
- PREVENT: ENFORCED for direct in-process Python-state mutation
- DETECT: DETECTED
- CONTAIN: ENFORCED for this narrow runtime-state threat
- RECOVER: PARTIAL

This is deliberately narrow. It does not claim the parent process is protected from every OS-level interaction a same-user child might attempt.

## Host capability abuse

Current status:
- same OS user: yes
- filesystem restriction: no
- network restriction: no
- subprocess restriction: no
- syscall/capability policy: no

Assurance:
- PREVENT: OUT OF SCOPE
- DETECT: OUT OF SCOPE
- CONTAIN: OUT OF SCOPE
- RECOVER: PARTIAL

Therefore the next security control priority is:

`os_level_capability_sandbox`

## Performance is a separate axis

v0.0.20 does not equate a security priority with a performance priority.

The fresh-process design can be safe relative to direct Python-runtime coupling while still being too expensive for practical repeated reasoning.

Performance instrumentation therefore measures:

`dispatch total = child service + outside-service time`

where outside-service time is a lower-bound proxy for interpreter startup, imports, scheduling, and IPC.

## Claim boundary

Process separation is now supported by evidence.

Hostile-code-safe sandboxing is still not supported.

A future persistent worker may improve latency but must not be described as a security control unless it also adds independently enforced capability restrictions.