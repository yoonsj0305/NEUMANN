# 全 연구 문서 근거 발췌 / Historical documentary inventory

원본 문서의 가설·결과·진단·다음 결정 발췌다. 실행 원본을 대신하지 않는다. 동일 문서/입력의 여러 기록을 독립 실험으로 합산하지 않는다.

## v0.0.5

Source: git:603b252:README.md
SHA256: cf5d66cf092d11db5dc57c18fd61341d39423bd8f1d54377e069c3b34e03b43b

### Current research questions

1. When does representation-first hybrid execution actually beat direct solving after representation, routing, solving, verification, and recovery costs are all counted?
2. Can the system recognize when a problem is outside its supported structural competence?
3. Can a learned Structure Former eventually produce complete, semantically faithful IRs from natural language?
4. How often do directly reusable reasoning structures occur in naturally occurring heterogeneous task streams?

## v0.0.6

Source: docs/experiments/v0.0.6.md
SHA256: 7e572e4a89f1403b931afe6fe80f328d63d3464da6927e44941632f9eb5e3dae

### Question

Can NEUMANN reduce false routing on unseen-but-nearby structures without collapsing useful auto-route coverage?

### Frozen final-test result

| Model | Known auto-route coverage | Routed-known precision | Unknown false-route | Near-unknown false-route |
|---|---:|---:|---:|---:|
| Two-stage logistic | 80.0% | 100% | 9.52% | 13.33% |
| Prototype centroid | 33.33% | 100% | 0% | 0% |

Knownness diagnostics:

- two-stage Brier: 0.2128
- two-stage ECE, 5 bins: 0.2804
- two-stage AUROC: 0.9270
- prototype similarity AUROC: 0.8286

### Interpretation

The distance-style gate is safer on this fixture but rejects too many supported problems. The two-stage gate preserves much more useful coverage but still confuses some nearby unseen structures.

The result argues against optimizing only classification accuracy. NEUMANN needs an explicit selective-risk policy that chooses coverage according to an acceptable false-route budget.

Examples from the selective curve:

- two-stage threshold 0.60: 93.3% known coverage, 19.0% unknown false-route
- two-stage threshold 0.65: 66.7% known coverage, 9.5% unknown false-route
- two-stage threshold 0.70: 20% known coverage, 0% observed unknown false-route
- prototype threshold 0.30: 53.3% known coverage, 4.76% unknown false-route
- prototype threshold 0.35: 46.7% known coverage, 0% observed unknown false-route

These are descriptive results on tiny synthetic fixtures, not guarantees.

### Decision

KEEP:
- explicit competence gate
- structurally-near OOD benchmark
- selective-risk curve
- fail-closed UNKNOWN

MODIFY:
- calibration
- risk objective
- training diversity

DO NOT YET ADD:
- general LLM routing
- full arbitrary IR generation

### Next question

Can a controlled Structure Former generate a complete solver-ready IR for one structural family, while an independent semantic checker catches extraction mistakes?

## v0.0.7

Source: docs/experiments/v0.0.7.md
SHA256: e0a6491ef5b1a00e849e1a2bfcb1966cbe63852060c2f8b6b3c31c038094e341

### Question

Can NEUMANN compile raw text into a complete solver-ready representation for one structural family and independently check semantic fidelity?

### Important finding

v0.0.7 is the first NEUMANN version where a raw-text path no longer requires an oracle solver payload for the supported family.

However semantic fidelity is still checked by an independent benchmark contract. Production semantic checking remains unsolved.

### Decision

KEEP:
- controlled compiler path
- separation between extraction fidelity and answer correctness
- family-by-family capability expansion

MODIFY NEXT:
- broaden matching surface forms
- inject malformed/ambiguous relation statements
- measure extraction precision/recall at edge level
- replace benchmark-only semantic contract with a more independent semantic checker when possible

DO NOT CLAIM:
- arbitrary matching-language understanding
- general IR generation
- production semantic verification

## v0.0.8

Source: docs/experiments/v0.0.8.md
SHA256: 2942815e48259d651a9114e2adfb8f955d1593ade7dd3e9eb4848014f7cc4783

### Question

Can the first complete matching compiler fail closed on partial, conflicting, or semantically richer statements instead of silently producing a plausible but incomplete IR?

### Interpretation

v0.0.8 intentionally narrows accepted language. The goal is not higher language coverage. The goal is to make silent semantic loss harder.

A correct solver is not evidence that the extracted IR represents the original problem.

### Decision rule

KEEP if:
- all valid controlled fixtures preserve exact edge semantics
- all explicit reject fixtures fail closed
- existing v0.0.7 behavior remains green

MODIFY if:
- safety hardening rejects too many previously valid controlled forms
- diagnostics are not actionable

## v0.0.9

Source: docs/experiments/v0.0.9.md
SHA256: dc148d354c70743348822f5268dd434b08aa8c9ea9654af2d80c03c23df37aa9

### Question

Can NEUMANN compile raw text into complete solver-ready IRs for two different structural families and route each to the correct deterministic solver without an oracle payload?

## v0.0.10

Source: docs/experiments/v0.0.10.md
SHA256: ec6dd8521d30e677e925aed3dfbdcaf3e20756ff7f295ff22a243198c99fcbf5

### Question

Can a learned high-level structure recognizer select a deterministic family compiler without allowing the learned prediction itself to become solver-ready authority?

## v0.0.11

Source: docs/experiments/v0.0.11.md
SHA256: 42efc937e64ecd31bc45ad53e42744075bee78f852618459c6f0bad0f67a3f77

### Question

Can NEUMANN turn family-specific compilers, solvers, and verifiers into a stable runtime contract instead of hard-coding them into one monolithic engine?

### Next question

Can NEUMANN migrate from a closed IRKind enum to namespaced string family / IR identifiers without breaking existing runtime safety and tests?

## v0.0.12

Source: docs/experiments/v0.0.12.md
SHA256: 87f9756c30d8246734383f575cb33fa4773c79262a39a0dfdf29d0af26c0776e

### Question

Can a third-party reasoning family register and execute through NEUMANN without editing the closed core IRKind enum?

## v0.0.13

Source: docs/experiments/v0.0.13.md
SHA256: fb02c13dafc8446200779cf9ea2750dd1986d0cdf4353fbf8aabb38b5f57b959

### Question

Can NEUMANN discover and inspect a plugin's declared identity and capabilities before importing or executing plugin code?

## v0.0.14

Source: docs/experiments/v0.0.14.md
SHA256: 15f7ae7661d66f860f87c70de091513c10d2f13aa96f33ace947c1d6a6ec6d8a

### Question

Can NEUMANN discover manifests shipped by installed Python distributions without importing the plugin module?

## v0.0.15

Source: docs/experiments/v0.0.15.md
SHA256: fb372d711801105741bd4755317932820811564845a3498c4b03003a6e343b37

### Question

Can NEUMANN core and an external reasoning family operate as separate Python distributions inside a fresh environment?

## v0.0.16

Source: docs/experiments/v0.0.16.md
SHA256: c61adae812fda6abf0d0d67f4935fb2c42cf0c5187f23d82eaa1be5a19ef9a74

### Question

Can plugin execution authority be checked at use time so revocation stops the next solver action even if plugin code is already imported and registered?

## v0.0.17

Source: docs/experiments/v0.0.17.md
SHA256: ea45a6965eff161f1aa191f9e38428b6f91738ccc9eec444eefe16e668b517db

### Question

Can NEUMANN preserve plugin authorization state across process restarts while detecting persisted-ledger mutation and making rollback detection explicit?

## v0.0.18

Source: docs/experiments/v0.0.18.md
SHA256: 2773b3be622baa43266058ad2c4095b8ad6acc6227dac5793dde37c69138efa9

### Question

Before adding more security mechanisms, what attacker and failure model is NEUMANN actually trying to defend against?

### Main architectural result

The current system has increasingly strong evidence around:
- static discovery
- exact-manifest approval
- use-time managed revocation
- persistent-ledger integrity

But it has no containment boundary after an approved plugin is imported.

Therefore the threat model chooses:

**out_of_process_plugin_isolation**

as the next control priority.

## v0.0.19

Source: docs/experiments/v0.0.19.md
SHA256: 634f1aa720109ec1e304922eff96f76a233906aba7844a5be0131b85352d0167

### Question

Can NEUMANN execute external compiler/solver/verifier code outside the core Python process while preserving authorization, fail-closed behavior, and the existing Family Adapter contract?

## v0.0.20

Source: docs/experiments/v0.0.20.md
SHA256: d563c6a20dfa989121db56adc3b0d13effeb47f38e26cfddf6960915bd750da9

### v0.0.20 — Runtime Cost Audit + Threat Model v2



### Question

After v0.0.19 introduced process separation, what is the next bottleneck: fresh-process lifecycle cost or missing OS-level containment?

### Decision rule

Performance and security priorities are allowed to diverge.

If lifecycle overhead dominates:
- next performance experiment: persistent worker

Regardless of that performance result, hostile-code containment still requires:
- OS capability restriction / sandbox boundary

Persistent workers must not be described as a security improvement by themselves.

### CI result — run #35

Test suite:
- **93 PASS / 0 FAIL**

Runtime-cost benchmark:
- dispatches: 9
- median out-of-process full pipeline: ~2227.8 ms
- median in-process trivial-family pipeline: ~0.004639 ms
- total dispatch time: ~6693.3 ms
- total measured child service time: ~1.618 ms
- total outside-service time: ~6691.7 ms
- outside-service fraction: **0.999758 (~99.976%)**
- median dispatch: ~748.25 ms
- median child service: ~0.178 ms
- median outside-service: ~748.07 ms

Pre-registered diagnosis:

`fresh_process_lifecycle_dominated`

Next performance experiment:

`persistent_worker_lifecycle`

Threat Model v2 next security control:

`os_level_capability_sandbox`

### Interpretation

The 50% lifecycle-dominance gate was exceeded by a very large margin.

The enormous OOP/in-process ratio (~480k×) should **not** be generalized because the in-process probe intentionally performs almost no useful work. It is a latency lower bound, not a representative production workload.

The more robust observation for this experiment is that the child-reported useful service interval was tiny relative to the parent-observed dispatch interval. This provides direct evidence that the current fresh-process-per-operation architecture is dominated by lifecycle/import/IPC cost for lightweight reasoning families.

Therefore:
- **performance track:** test a persistent worker lifecycle next
- **security track:** retain OS-level capability sandboxing as the gate before hostile code can be called contained

A persistent worker must preserve authorization-before-request, revocation semantics, timeout/crash recovery, protocol bounds, and parent-process non-import guarantees.

## v0.0.21

Source: docs/experiments/v0.0.21.md
SHA256: 0d0335b412edb89aa03e579a958a2f5cd1511119fdd74dd2f9b5e3aeaf3a30ca

### Question

Can NEUMANN remove the fresh-process lifecycle bottleneck without giving up the v0.0.19 process boundary and v0.0.16 revocation semantics?

### CI result — PR #16 first full run

Test suite:
- **99 PASS / 0 FAIL**

Lifecycle benchmark:
- fresh-process pipeline median: **~2457.74 ms**
- persistent-worker cold first pipeline: **~742.67 ms**
- persistent-worker warm pipeline median: **~1.027 ms**
- measured warm speedup vs fresh-process probe: **~2394×**
- persistent worker start count before revoke: 1
- worker startup: **~741.41 ms**
- plugin requests before revoke: 18
- post-revocation requests: **0**
- worker running after revoke: **NO**
- revoked execution verified: **NO**
- pre-registered keep gate: **PASS**

### Fresh-venv external wheel result

- core distribution: `neumann1 0.0.21`
- external plugin distribution: `neumann-example-scalar-sum 0.1.2`
- plugin module imported in parent: **NO**
- first two solves reused same worker: **YES**
- post-revocation requests: **0**
- worker survives revoke: **NO**
- re-approval starts replacement worker: **YES**
- restored execution verified: **YES**

### Interpretation

The pre-registered performance gate was exceeded by a large margin in this lightweight probe.

The ~2394× ratio must **not** be generalized to representative reasoning workloads. The benchmark family intentionally performs almost no useful computation, so it magnifies lifecycle cost.

The robust engineering result is narrower:

> Once startup/import cost is amortized, the same out-of-process plugin boundary can serve repeated lightweight compile/solve/verify requests with approximately millisecond-scale warm pipeline latency in this CI environment while preserving the tested revocation invariants.

The cold path remains dominated by worker startup (~741 ms). Therefore a production lifecycle policy must consider:
- when to prewarm workers
- how long to retain idle workers
- when to recycle stateful workers
- how many workers per plugin/family to permit
- how crash recovery affects outstanding requests

### Decision

**KEEP persistent-worker direction as the preferred performance path.**

Security remains a separate track:

`os_level_capability_sandbox`

Persistent state reuse is not itself a security improvement.

## v0.0.22

Source: docs/experiments/v0.0.22.md
SHA256: 606f28b4a23c79e3dafbe641ada8ac960d84abbd2900db96fd669b127a771611

### Question

Can NEUMANN retain persistent-worker performance while making hidden in-process plugin state explicit, auditable, and resettable?

### CI result — PR #17 first full run

Test suite:
- **105 PASS / 0 FAIL**

State-hygiene benchmark:
- poison visible in same generation: **YES**
- poison visible after recycle: **NO**
- generation changed after recycle: **YES**
- manual recycle recorded: **YES**
- warm same-generation pipeline: **~1.044 ms**
- post-recycle cold pipeline: **~847.39 ms**
- warm clean pipeline median: **~0.955 ms**
- strict three-generation pipeline: **~2576.82 ms**
- worker starts in strict probe: 3
- unique generations in strict probe: 3
- semantic result across three generations verified: **YES**
- keep state-hygiene contract: **YES**

Fresh-venv external-wheel proof:
- core: `neumann1 0.0.22`
- external plugin: `neumann-example-scalar-sum 0.1.2`
- plugin imported in parent: **NO**
- first solve verified: **YES**
- answer: `sum = 9.5`
- compile/solve/verify unique generations: **3**
- worker starts for first solve: 3
- automatic recycle events: 2
- manual recycle event recorded: **YES**
- second solve after manual recycle verified: **YES**

### Main finding

> **Hidden Python worker state can influence later requests inside one generation, and process recycling demonstrably removes that in-memory state for the test fixture. At the same time, the explicit RPC/Representation contract is sufficient for the tested family to remain correct even when compile, solve, and verify run in separate generations.**

### Decision

**KEEP generation IDs, explicit recycle events, and configurable request-count recycling.**

Do not make hidden worker state semantic authority.

### Next research-engineering question

The remaining lifecycle problem is policy selection:

> **How should NEUMANN decide when a worker is safe to reuse, must be recycled, or should never be persistent at all?**

A candidate next milestone is a **Worker State Declaration / Lifecycle Class** that distinguishes:
- stateless semantic families
- cache-only retained state
- explicitly stateful families
- non-persistent-only families

and maps those declarations to enforceable lifecycle policy rather than relying on one global request-count threshold.

## v0.0.23

Source: docs/experiments/v0.0.23.md
SHA256: fdca024947d37f2ace960846897239ec3be8ab1c55488dea35a6488abfb7f2de

### Question

Can NEUMANN replace one global persistent-worker policy with a plugin-declared lifecycle class that the runtime actually enforces?

### CI result — PR #19 first full run

Test suite:
- **113 PASS / 0 FAIL**

Lifecycle-policy benchmark:
- persistent allowed: `STATELESS`, `CACHE_ONLY`
- `NON_PERSISTENT` rejected from persistent path: **YES**
- `NON_PERSISTENT` allowed on fresh path: **YES**
- `STATEFUL_EXPLICIT` rejected from persistent path: **YES**
- `STATEFUL_EXPLICIT` rejected from fresh path: **YES**
- undeclared legacy manifest rejected from persistent path: **YES**
- undeclared legacy manifest allowed on fresh path: **YES**
- changing only `worker_state_class` changes manifest digest: **YES**

Fresh-venv external-wheel proof:
- core distribution: `neumann1 0.0.23`
- external plugin: `neumann-example-scalar-sum 0.1.3`
- declared class: `CACHE_ONLY`
- persistent reuse verified: **YES**
- same worker reused: **YES**
- plugin module imported in parent: **NO**
- lifecycle declaration changes manifest digest: **YES**
- manifest digest: `976281128192b7fe71167c7b44418099ea541070aa732f0bb340c96dcee1e54c`

### Main finding

> **Persistent reuse is now an explicit manifest-level privilege rather than an implicit runtime default.**

The runtime can reject incompatible lifecycle choices before launching plugin code.

### Backward-compatibility decision

Legacy manifests without a lifecycle declaration keep the safer capability:

`fresh-process execution`

but do not silently inherit the stronger privilege:

`persistent worker reuse`

This preserves old packages while making reuse opt-in.

### Decision

**KEEP**
- explicit lifecycle declarations
- persistent reuse as opt-in privilege
- legacy fresh-only fallback
- STATEFUL_EXPLICIT fail-closed until a real state protocol exists
- lifecycle class bound into manifest digest

### Next candidate milestone

The next missing piece is not another class.

It is **behavioral attestation for the declared class**:

> Can NEUMANN automatically test whether a plugin that declares STATELESS or CACHE_ONLY actually behaves consistently across worker recycle/generation boundaries?

Candidate v0.0.24:
**Lifecycle Conformance Attestation**

Possible gates:
- repeat same corpus across warm/recycled generations
- compare semantic outputs independent of PID/cache metadata
- poison/reset probes where supported
- produce attestation evidence bound to plugin manifest digest
- refuse persistent privilege when attestation is absent or stale

This would connect declaration to measured evidence instead of trusting manifest metadata alone.

## v0.0.24

Source: docs/experiments/v0.0.24.md
SHA256: dffd8823a5bbc269b48d3f86c417cae2f8d14e6ffee4861a157b234d0b6e6e86

### Question

Can NEUMANN require measured behavioral evidence before granting a plugin persistent-worker privilege?

### CI result — PR #20 first full run

Test suite:
- **119 PASS / 0 FAIL**
- pytest duration: ~95.95 s

Core lifecycle-attestation benchmark:
- attestation status: **PASS**
- case count: 3
- warm repetitions: 2
- warm mode: **PASS**
- recycled mode: **PASS**
- cross-generation mode: **PASS**
- semantic equivalence rate: **1.0**
- warm generation count: 1
- recycled generation count: 3
- cross-generation count: 9
- missing attestation blocked: **YES**
- persistent execution after attestation verified: **YES**
- stale attestation blocked after manifest change: **YES**
- keep attestation gate: **YES**

Core benchmark artifact identities:
- manifest SHA-256: `6d680503018fc8a0a784d7855e8500372c29965c6e122fdb7bd7a4bc8d8bd9e2`
- corpus SHA-256: `6d2b5f2c3ca0530529fbb461ac2f256410cee19aade4ee98c7145106e0954f73`
- attestation SHA-256: `971c3ade19e7a1ed8b629c705fb2d03929d9849a91d011e9b3162fc6db1876b8`

Fresh-venv external-wheel proof:
- core distribution: `neumann1 0.0.24`
- external plugin: `neumann-example-scalar-sum 0.1.3`
- manifest SHA-256: `976281128192b7fe71167c7b44418099ea541070aa732f0bb340c96dcee1e54c`
- attestation SHA-256: `e2ca705db4aab526f71d81eaadcc9bb3d159bc5a3be7cf56227b2655432be983`
- attestation status: **PASS**
- cases: 3
- warm repetitions: 2
- semantic equivalence rate: **1.0**
- warm / recycled / cross-generation: **all PASS**
- missing attestation blocked before plugin execution: **YES**
- persistent execution after attestation verified: **YES**
- same worker reused after attestation: **YES**
- plugin module imported in parent: **NO**

### Main finding

> **Persistent reuse can now be conditioned on measured behavior of the exact approved plugin artifact, rather than on lifecycle metadata alone.**

The authorization chain is now conceptually:

`exact artifact → explicit lifecycle declaration → behavioral attestation → persistent privilege`

Changing the manifest breaks both the authorization identity and the attestation identity.

### Decision

**KEEP**
- exact-manifest attestation identity
- corpus digest
- attestation digest
- minimum evidence gates
- internal conformance-only bootstrap path
- public persistent gate requiring PASS evidence
- stale/FAIL/missing attestation rejection

### Next candidate milestone

The largest new weakness is that the attestation registry is process-local memory.

Recommended next question:

> **Can lifecycle attestations become durable, auditable, revocable evidence without turning a stale PASS into permanent authority?**

Candidate v0.0.25:
**Durable Attestation Ledger + Use-Time Evidence Revocation**

Possible requirements:
- persisted canonical attestation records
- exact manifest + corpus + attestation digest identity
- ACTIVE / REVOKED evidence state
- use-time attestation check before every persistent dispatch or generation start
- restart persistence
- stale/revoked evidence fail closed
- append-only/tamper-evident history aligned with the authorization ledger

Do not treat a historical PASS as permanent authority if its evidence has been revoked or superseded.

### CI result — PR #20 first full run

Test suite:
- **119 PASS / 0 FAIL**

Lifecycle-attestation benchmark:
- attestation version: `neumann.lifecycle-attestation.v1`
- attestation status: **PASS**
- case count: 3
- warm repetitions: 2
- warm mode: **PASS**
- recycled mode: **PASS**
- cross-generation mode: **PASS**
- semantic equivalence rate: **1.0**
- warm generation count: 1
- recycled generation count: 3
- cross-generation count: 9
- missing attestation blocked: **YES**
- persistent execution after PASS attestation verified: **YES**
- stale attestation blocked: **YES**
- keep attestation gate: **YES**

Benchmark exact-artifact evidence:
- manifest digest: `6d680503018fc8a0a784d7855e8500372c29965c6e122fdb7bd7a4bc8d8bd9e2`
- attestation digest: `971c3ade19e7a1ed8b629c705fb2d03929d9849a91d011e9b3162fc6db1876b8`
- corpus digest: `6d2b5f2c3ca0530529fbb461ac2f256410cee19aade4ee98c7145106e0954f73`

Fresh-venv external-wheel proof:
- core distribution: `neumann1 0.0.24`
- external plugin: `neumann-example-scalar-sum 0.1.3`
- manifest digest: `976281128192b7fe71167c7b44418099ea541070aa732f0bb340c96dcee1e54c`
- attestation digest: `e2ca705db4aab526f71d81eaadcc9bb3d159bc5a3be7cf56227b2655432be983`
- attestation status: **PASS**
- case count: 3
- warm repetitions: 2
- semantic equivalence rate: **1.0**
- warm / recycled / cross-generation: **all PASS**
- missing attestation blocked before execution: **YES**
- persistent execution after attestation: **VERIFIED**
- same worker reused after attestation: **YES**
- external plugin imported in parent: **NO**

### Main finding

> **NEUMANN can now make persistent-worker privilege depend on measured behavioral evidence bound to the exact plugin artifact, rather than trusting lifecycle metadata alone.**

### Important negative result / boundary

The attestation passes only for the explicit corpus and execution modes that were tested.

It does not establish:
- universal semantic correctness
- safety on unseen inputs
- absence of adversarial trigger behavior
- publisher authenticity
- OS-level containment

### Decision

**KEEP lifecycle conformance attestation as a required gate for public persistent reuse.**

### Next candidate milestone

The largest remaining attestation weakness is durability and provenance.

v0.0.24 keeps the trusted attestation registry only in memory.

Recommended next question:

> **Can attestation evidence be persisted, audited, revoked, and freshness-checked without turning the evidence store itself into a new weak trust anchor?**

Candidate v0.0.25:
**Durable Attestation Ledger + Freshness / Revocation Contract**

Potential targets:
- persisted append-only attestation records
- exact manifest / corpus / attestation digests
- issuance and invalidation events
- revocation by plugin ID or attestation digest
- stale-evidence rejection after manifest or corpus changes
- reload integrity checks
- trusted-head boundary clearly separated from local tamper evidence

This should reuse lessons from the authorization ledger rather than invent a second weaker evidence store.

## v0.0.25

Source: docs/experiments/v0.0.25.md
SHA256: 61d1a4e02d8dd983f72effe6747dea6b4a124eda8b11c486ce10d6468475a96d

### Question

Can NEUMANN persist lifecycle attestations as auditable evidence and revoke a historical PASS so that an already-running persistent worker loses privilege before its next plugin RPC?

### Candidate next questions

After this milestone, the next work should be selected by measured bottleneck rather than version momentum.

Two live tracks remain:

### Decision rule

v0.0.25 should be marked **KEEP** only after CI and fresh-venv evidence satisfy the pre-registered gate above.

### CI result — PR #21

Final GitHub Actions result:
- workflow run: **#56**
- test suite: **125 PASS / 0 FAIL**
- pytest duration: **126.47 s**
- all historical benchmark smokes: **PASS**
- v0.0.25 durable-attestation benchmark: **PASS**
- core + external plugin wheel build: **PASS**
- all fresh-venv interop gates: **PASS**
- fresh-venv durable-attestation revocation proof: **PASS**

Core v0.0.25 benchmark evidence:
- manifest SHA-256: `d48aa97aad555e3248aa5fd031031bd34d2d30ed3a63defe6ff62a174a1fca3c`
- attestation SHA-256: `541da53e524b24c71acd3ca529bb978b953e6bfc69bdd3f94668c2e35bef6dc1`
- issued ledger head: `34cec755909d8303a3ebdf9cf74faac1bc66ac6b553043c340d4763ab8e4dfad`
- revoked ledger head: `e769fd7efea0443d8c969c0332d0938dffa5baafb035b03545ce117fc3ebb0c7`
- active evidence survived restart: **YES**
- use-time revocation blocked next dispatch: **YES**
- post-revocation plugin RPC count: **0**
- worker terminated after evidence revoke: **YES**
- revocation survived restart: **YES**
- `keep_durable_attestation_gate`: **true**

Fresh-venv external-wheel evidence:
- core distribution: `neumann1 0.0.25`
- external plugin: `neumann-example-scalar-sum 0.1.3`
- manifest SHA-256: `976281128192b7fe71167c7b44418099ea541070aa732f0bb340c96dcee1e54c`
- attestation SHA-256: `e2ca705db4aab526f71d81eaadcc9bb3d159bc5a3be7cf56227b2655432be983`
- issued ledger head: `738cb556b336a9f88e28c4563852d5b11478f78bdab6822551e0a04dedd3ddef`
- revoked ledger head: `d283a54c9d21bde74823c0f954efb03feb446f666197ef7e802c53b3447aa3a6`
- same worker reused before revoke: **YES**
- use-time evidence revocation blocked: **YES**
- post-revocation plugin RPC count: **0**
- revocation survived restart: **YES**

### Main finding

> **Lifecycle evidence is now durable and revocable without allowing an already-running persistent worker to continue using stale PASS authority.**

The authority chain is now:

```
exact artifact authorization
+ persistent-compatible lifecycle declaration
+ exact behavioral attestation
+ current ACTIVE durable evidence state
→ persistent reuse
```

A historical PASS is therefore evidence, not permanent authority.

### Decision

**KEEP v0.0.25.**

The pre-registered keep gate is satisfied, including the strongest runtime criterion:

```
revoke evidence while worker is alive
→ next actual plugin dispatch blocked
→ post-revoke plugin RPC = 0
→ worker terminated
```

### Next research priority

The infrastructure/security substrate has now advanced substantially beyond the original structural-intelligence experiment.

The recommended next milestone is **not another control-plane feature by default**.

Return to the central NEUMANN 1 hypothesis and measure whether representation-first computation actually buys intelligence per unit compute:

- task quality
- model parameters / active parameters
- input and output tokens
- wall-clock latency
- peak RAM / VRAM
- energy proxy where measurable
- representation compression ratio
- verifier pass rate
- out-of-distribution generalization

A security milestone such as OS-level capability containment should remain a parallel track only when the next experiment requires executing less-trusted external code.

## v0.0.26

Source: docs/experiments/v0.0.26.md
SHA256: d7f250874dcd4488b4105e22fa0582405313a4b57fe77583d2bbee4eb9d29001

### Question

Can NEUMANN demonstrate a real, measurable benefit from making structure a reusable intermediate asset before claiming broader compute efficiency?

### Expected exact structural result

With 8 repetitions and a deterministic one-step family compiler:

    compile every time representation steps = 8
    compile once reuse representation steps = 1

Therefore, if the contract behaves as designed:

    representation-step reduction factor = 8.0

This is an instrumented amortization fact, not an 8x end-to-end compute claim.

Solver and verification work should remain unchanged because v0.0.26 deletes only repeated representation formation.

### Failure interpretations



### Next milestone candidate

If v0.0.26 passes, the next experiment should move one layer closer to the central model hypothesis.

Candidate v0.0.27:

**Model-Side Structural Proposal Cost Benchmark**

Compare, on a fixed corpus:

    direct learned prediction / solution attempt

against:

    small learned structural proposal
      → deterministic compiler
      → solver
      → verifier

with explicit accounting for:
- model feature/input size
- confidence / abstention
- task accuracy
- false-route rate
- representation byte size
- CPU time
- model parameter count where available

The project should not claim LLM-scale efficiency until an actual language model is placed under the same paired measurement contract.

### CI result — PR #22 first full run

Test suite:
- **130 PASS / 0 FAIL**
- pytest duration: **128.43 s**

Structural-efficiency benchmark:
- repetitions per fixture: **8**
- fixture count: **4**
- mean representation-step reduction factor: **8.0**
- mean representation / raw-text byte ratio: **3.8571**
- mean observed wall-time ratio (compile-every-time / compile-once-reuse): **4.0674**
- keep_structural_efficiency_contract: **true**

Per-fixture byte results:

| Fixture | Raw text bytes | Representation bytes | Rep / raw ratio | Observed wall-time ratio |
|---|---:|---:|---:|---:|
| matching_3 | 55 | 229 | 4.1636 | 5.4379 |
| matching_5 | 93 | 277 | 2.9785 | 2.6266 |
| linear_2 | 20 | 107 | 5.3500 | 4.6498 |
| linear_3 | 47 | 138 | 2.9362 | 3.5551 |

All fixtures satisfied:
- compile-every-time verified rate = **1.0**
- compile-once-reuse verified rate = **1.0**
- paired answer equivalence = **1.0**
- canonical representation identity stable = **YES**
- representation steps = **8 vs 1**
- solver-step count unchanged between modes
- verification-step count unchanged between modes

All historical benchmark smokes, wheel build, and fresh-venv interop regressions also passed.

### Main finding

> **In this controlled benchmark, structural reuse produced measurable execution savings even though the solver-ready representation was substantially larger than the raw input text.**

This separates two ideas that should not be conflated:

1. **representation compression**
2. **representation reuse**

v0.0.26 found no byte-level compression advantage on these small fixtures. The canonical representation averaged **3.86× the raw-text byte size**.

Yet compiling the structure once instead of eight times reduced instrumented representation work from **8 steps to 1 step**, while leaving solver and verification work unchanged and preserving answers exactly.

The observed mean wall-time ratio was **4.07×** in favor of reuse on this CI run. This is a measured diagnostic for these Python fixtures only. It is not a portable speedup claim.

### Interpretation

The first useful NEUMANN efficiency mechanism is therefore not:

> make every problem representation smaller than language.

It is:

> convert interpretation into an explicit reusable artifact so downstream execution does not pay the interpretation cost repeatedly.

That suggests a sharper decomposition of the central hypothesis:

    Intelligence cost
      = interpretation / structure formation
      + execution on structure
      + verification

NEUMANN can only gain if one or more of these terms is reduced or amortized without lowering verified task quality.

v0.0.26 demonstrates amortization of the first term in a narrow deterministic setting.

### Negative result retained

The representation layer is currently byte-heavy.

Likely contributors include:
- JSON field names
- repeated/derived fields
- explicit diagnostic payloads
- small raw fixtures where structural encoding overhead dominates

This is not automatically a defect. Solver-ready structure may be larger while still being cheaper to reuse.

However, for edge-memory goals, representation minimality remains an open measurement target.

### Decision

**KEEP v0.0.26.**

The structural-efficiency measurement contract is useful because it:
- preserves semantic equivalence as the first gate
- isolates representation work from solver/verifier work
- exposes negative byte results
- avoids converting a noisy wall-clock observation into a correctness criterion
- creates a reusable framework for later model-side experiments

### Recommended next milestone

v0.0.27 should move closer to actual structural intelligence rather than optimizing the current JSON format in isolation.

Recommended question:

> **Can a small learned model spend less learned inference work by proposing reusable structure, while deterministic compilation/solving preserves task quality?**

Candidate measurements:
- learned-model parameter count
- sparse feature activations / model operation proxy
- CPU inference time
- coverage and abstention
- false-route rate
- final verified accuracy
- representation bytes
- repeated-use amortization

Separately, representation minimality can be audited as an optimization sub-experiment, especially for redundant matching fields, but it should not replace the main model-efficiency track.

## v0.0.27

Source: docs/experiments/v0.0.27.md
SHA256: 10bf2a2df80c64b0d58be1fcea6e96a129114856d052400f48c5c6bfcc7eb965

### Question

Can NEUMANN measure the learned work used to propose a reusable structural family without confusing that proxy with FLOPs, energy, or LLM efficiency?

v0.0.26 established that a solver-ready representation can amortize repeated interpretation work. v0.0.27 moves one layer upstream and measures the current learned proposer itself.

### Results

First full GitHub Actions run on the v0.0.27 branch:

- pytest: **136 passed**; the first run exposed one docstring escape warning, which was then removed before merge
- validation threshold: **0.48**
- validation known coverage: **1.0**
- known feature dimension: **1,322**
- supported-family feature dimension: **638**
- fitted logistic coefficient/intercept scalars: **1,962**
- TF-IDF IDF-state scalars: **1,960**
- measurement/public predictor parity: **1.0**
- known proposal coverage: **1.0**
- known deterministic compiler acceptance: **1.0**
- known end-to-end verified coverage: **1.0**
- unsupported proposal false-route rate: **0.10** (1 of 10 unsupported final-corpus items)
- unsupported final false-route rate after compiler gate: **0.0**
- compiler-rescued false proposals: **1**
- mean learned stages executed: **1.5**
- mean sparse active features: **60.17**
- mean score dot-product term proxy: **60.17**
- mean observed proposal wall time in this CI run: **0.00239 s**
- repeated score-term reduction for 8 exact repeated uses: **8.0×**
- `keep_model_side_cost_contract = true`

The proposal-layer 10% false-route rate is intentionally retained rather than hidden. The deterministic compiler rejected that bad learned proposal, so it did not become solver authority.

The wall-clock value is a single controlled CI observation and is not a keep gate or a general speed claim.

## v0.0.28

Source: docs/experiments/v0.0.28.md
SHA256: 7f6f6f04639968ac6268835e07ad94f059c246c0c97abe9eb355abcd534c81bf

### Question

Can NEUMANN replace the linear/logistic proposal heads with a genuinely nonlinear learned proposer while preserving the same deterministic authority boundary and the same auditable cost vocabulary?

v0.0.27 measured the current TF-IDF + logistic proposer.

v0.0.28 adds a deliberately tiny neural alternative:

    TF-IDF features
      -> 4-unit ReLU hidden layer
      -> open-set / family output
      -> deterministic compiler gate
      -> deterministic solver
      -> deterministic verifier

This is the first nonlinear learned proposer in the NEUMANN measurement track.

### Results

First full GitHub Actions run on the v0.0.28 branch:

- pytest: **142 passed**, no pytest or convergence warnings
- logistic validation threshold: **0.48**
- neural validation threshold: **0.25**
- both validation known coverages: **1.0**
- logistic fitted coefficient/intercept scalars: **1,962**
- neural fitted weight/bias scalars: **7,858**
- neural/logistic parameter ratio: **4.005x**
- TF-IDF IDF-state scalars for each proposer: **1,960**
- neural known proposal coverage: **1.0**
- neural known family accuracy: **1.0**
- neural deterministic compiler acceptance: **1.0**
- neural end-to-end verified coverage: **1.0**
- logistic proposal false-route rate on unsupported final cases: **0.10**
- neural proposal false-route rate on unsupported final cases: **0.0**
- both compiler-gated final false-route rates: **0.0**
- logistic mean score-term proxy: **60.17**
- neural mean weighted-sum term proxy: **243.78**
- neural/logistic arithmetic-proxy ratio: **4.052x**
- neural mean active TF-IDF features: **59.5**
- neural 8-use repeated weighted-sum reuse factor: **8.0x**
- `keep_tiny_neural_proposer_contract = true`

The central negative result is deliberate: the tiny nonlinear proposer used about four times the fitted classifier parameters and about four times the arithmetic proxy of the logistic proposer.

The central quality result is also clear: on this small controlled corpus, the neural proposer removed the logistic model's one proposal-layer false route while preserving 100% known-task routing and verified execution. Both architectures still reached a final unsupported false-route rate of zero because the deterministic compiler gate remained authoritative.

Observed mean wall-clock times were roughly 2.15 ms for logistic and 2.10 ms for neural in this CI run. That near-equality conflicts with the arithmetic-proxy ratio because these models are tiny and Python/vectorization overhead dominates. Wall-clock is therefore retained only as a diagnostic and is not interpreted as evidence that the neural model is cheaper.

### Boundary and next step

This MLP is neural, but it is still not a language model. It consumes TF-IDF features rather than learned token embeddings.

The next milestone should introduce a direct learned task-solving baseline or a genuinely token-based small model under the same quality and cost contract. That is where NEUMANN can begin testing whether structure-first computation beats a learned system asked to solve the task directly.

## v0.0.29

Source: docs/experiments/v0.0.29.md
SHA256: 3fc093a7b4ab2504cbb66477583754166f4e9c0ad5fb583dc7198fbe1ed4212a

### Research question

At the same small learned inference capacity, does a structure-first path preserve verified problem-solving quality better than asking the learned model to produce the numeric answer directly?

This is the first NEUMANN benchmark that compares:

    Direct learned path
    raw token sequence
      -> tiny neural model
      -> (x0, x1)
      -> evaluation verifier

against:

    Structural path
    raw token sequence
      -> same-capacity tiny neural model
      -> LINEAR / ABSTAIN
      -> deterministic compiler
      -> deterministic solver
      -> deterministic verifier

The experiment is intentionally limited to generated, controlled, nonsingular 2x2 linear systems.

### First CI result

GitHub Actions run #69 executed the full branch from a clean runner.

Regression status:

- pytest: **149 passed in 85.80 s**
- no pytest warning summary
- no `ConvergenceWarning`
- all earlier benchmark smokes passed
- wheel build passed
- all fresh-venv interoperability checks passed

Matched learned capacity:

- encoder input dimension: **640**
- hidden units: **8**
- structural parameters: **5,146**
- direct parameters: **5,146**
- parameter ratio, structural/direct: **1.0**
- structural dense weighted-sum proxy: **5,136**
- direct dense weighted-sum proxy: **5,136**
- learned proxy ratio, structural/direct: **1.0**
- layer shapes for both: **640 -> 8 -> 2**

Structural path:

- validation decision threshold: **-0.3319000009**
- final positive proposal coverage: **1.0**
- final verified coverage: **1.0**
- final near-negative proposal false-route rate: **0.0**
- final near-negative false-route after compiler: **0.0**
- mean deterministic solver steps: **9**

Direct path:

- final verified coverage: **0.0**
- solution RMSE: **3.1234163666**
- mean maximum equation residual: **12.7648562848**
- median maximum equation residual: **11.3277278797**

Paired observed delta:

    structural verified coverage - direct verified coverage = 1.0

Measurement contract:

    keep_paired_measurement_contract = true

### Interpretation

This is the first NEUMANN result in which the learned inference architecture is held constant while the learned objective changes.

On this controlled corpus:

- asking the 8-unit model to directly approximate the two numeric answers did not produce a single answer that passed the strict deterministic equation verifier;
- asking the matched-capacity model only to identify whether deterministic linear structure was applicable preserved all 64 final tasks, after which the deterministic compiler and Gaussian-elimination solver produced verified answers.

That is evidence for a **matched-learned-capacity quality effect**:

> under this narrow setup, spending learned capacity on selecting valid structure was more effective for verified task completion than spending the same learned capacity on direct numeric answer regression.

It is **not yet evidence of lower total computation**.

The Structural path pays additional deterministic compiler, solver, and verifier work. The current learned arithmetic proxy and `CostLedger` steps have different units and are deliberately not added together.

It is also not evidence that direct learning fundamentally cannot solve 2x2 systems. The direct model is deliberately tiny, uses a hand-designed fixed-position encoder, and was not subjected to a capacity/data sweep. Its 0% verified rate may reflect insufficient capacity, unsuitable inductive bias, insufficient training data, or all three.

### Next falsification step

The next experiment should not simply celebrate the 64/64 versus 0/64 gap.

It should try to erase it.

A v0.0.30 capacity/data sweep should increase the direct model's:

- hidden width
- training-set size
- possibly depth, while recording the exact added state and arithmetic proxy

and ask:

> At what learned capacity, if any, does the direct path reach the same strict verified coverage as the structure-first path?

The scientifically useful quantity is then a **break-even frontier**, not a single win/loss result.

## v0.0.30

Source: docs/experiments/v0.0.30.md
SHA256: e63a5bdf7baaee684e06d12c8df99fdcde2454dee9a7de539ad57d4ac210a3c5

### Research question

v0.0.29 observed a large matched-learned-capacity quality gap:

- Structural path: 64/64 strict verified answers
- Direct 8-unit regression: 0/64 strict verified answers

v0.0.30 is designed to attack that result.

The question is no longer:

> Does the matched tiny Direct model lose?

It is:

> How much learned capacity and training data must Direct receive before it reaches the fixed Structural reference, if it reaches it at all?

The desired output is a break-even frontier, not a winner label.

### First CI result

GitHub Actions run #73 executed the complete v0.0.30 branch from a clean runner.

Regression status:

- pytest: **155 passed in 143.00 s**
- all earlier benchmark smokes passed
- v0.0.30 frontier benchmark passed
- wheel build passed
- all fresh-venv interoperability checks passed

The full frontier benchmark itself took approximately **91 s** in this CI run. Training wall-clock remains diagnostic only.

### Final result for the validation-selected Direct candidate

On the untouched 243-system final split:

- rounded-regression strict verified coverage: **0.082305**
- Structural strict verified coverage: **1.0**

Again, no break-even.

### Interpretation

v0.0.30 strengthens the v0.0.29 finding, but it still does not establish a total-compute advantage.

Three alternative explanations were directly weakened:

1. **The Direct model was merely too small.**  
   Direct was expanded from 8 to 64 hidden units, reaching about 8x the Structural learned inference proxy in the validation-selected configuration.

2. **The Direct model merely lacked data.**  
   Direct was expanded from 128 to 2048 positive systems.

3. **Strict floating-point verification unfairly punished regression.**  
   Rounded regression and an exact 81-class output head were both added.

None reached Structural break-even inside the pre-registered frontier.

The narrow result is therefore:

> On this controlled 2x2 linear-system benchmark, a small learned model used to identify applicable structure plus deterministic execution preserved verified generalization far better than substantially larger Direct learned mappings from tokenized equations to answers.

The result still has major boundaries.

- The Structural path has a hand-written compiler and exact Gaussian-elimination solver.
- Direct and Structural do not have matched training objectives.
- Structural sees paired negative supervision for abstention.
- Deterministic solver work is additional computation.
- The fixed-position token encoder is not a language model.
- The Direct sweep is still finite. A larger or architecturally different Direct model may eventually close the gap.

Therefore the result should not be stated as:

    NEUMANN is 8x more compute-efficient.

What is supported is:

    No Direct break-even was observed
    within the pre-registered frontier up to
    2048 training examples and 64 hidden units.

### Next falsification target

The next experiment should stop scaling the same shallow MLP indefinitely.

The current frontier suggests that the bottleneck may be **inductive bias**, not only parameter count.

A stronger falsification target is therefore a Direct model with a more appropriate sequence architecture, for example:

- learned token embeddings
- a small recurrent or attention-based sequence model
- explicit positional encoding
- enough capacity to represent multi-step coefficient interactions

The Structural path should then be moved to the same learned backbone so the comparison remains about **what the learned system is asked to produce**, not merely model family.

That would turn the next milestone from a width sweep into an architecture-controlled test.

### First CI result

GitHub Actions run #73 executed the complete pre-registered frontier from a clean runner.

Regression status:

- pytest: **155 passed in 143.00 s**
- all earlier benchmark smokes passed
- v0.0.30 frontier benchmark passed
- wheel build passed
- all fresh-venv interoperability checks passed
- `keep_direct_break_even_frontier_contract = true`

### Final result for the validation-selected candidate

Without retuning on final:

- training size: **2048**
- hidden width: **64**
- method: **rounded regression**
- strict verified coverage: **0.08230452675** = 20/243

The fixed Structural final path verified:

- **243/243 = 1.0**

Therefore:

    final break-even for the validation-selected Direct candidate = not reached

### Interpretation

v0.0.30 did not find a break-even point inside the pre-registered Direct frontier.

This is stronger than the single v0.0.29 matched-capacity result because Direct was explicitly given several advantages:

- up to 16x more positive training systems
- up to 8x the learned inference arithmetic proxy
- an integer-support rounding prior
- an 81-class exact-solution formulation
- every training prefix covered all 81 solution classes

Despite those changes, the best validation-selected Direct model remained far below the fixed Structural path on strict verified task completion.

The narrow inference supported by this experiment is:

> within this fixed-position-token MLP family and generated 2x2 linear-system distribution, the measured Direct break-even frontier lies beyond the tested range.

This is still not a total-compute comparison. The Structural path pays deterministic compiler, solver, and verifier work after learned inference. Training-data size is also not inference cost.

It is also not evidence that neural systems cannot learn linear-system solving. The tested Direct family is shallow MLP-based and may have poor algorithmic inductive bias. A sequence model, recurrent architecture, transformer, explicit arithmetic module, curriculum, or much larger corpus could move the frontier substantially.

That observation defines the next falsification step more sharply than simply expanding the same grid again.

## v0.0.31

Source: docs/experiments/v0.0.31.md
SHA256: f5982e3ab645a6372dcbcc0786ec355af0f5cb65db35e627b1372f306ffeaf90

### Research question

v0.0.30 failed to find a Direct break-even point inside a shallow MLP frontier.

That leaves a major alternative explanation:

> perhaps Direct failed because the fixed-position MLP has poor sequence and algorithmic inductive bias.

v0.0.31 attacks that explanation with a small learned sequence model.

The experiment compares two models with the exact same architecture:

    token categories + numeric scalar channel
      -> learned token embedding
      -> learned positional embedding
      -> 2-layer Transformer encoder
      -> masked mean pooling
      -> identical 82-way output head

The only intended difference is the learning objective.

### Results

GitHub Actions run #81 executed both the unchanged core regression lane and the isolated PyTorch sequence-experiment lane from the corrected branch head.

### Interpretation

v0.0.31 substantially weakens the simplest alternative explanation for v0.0.29-v0.0.30:

> the Direct path lost only because a fixed-position shallow MLP had the wrong sequence inductive bias.

That explanation is insufficient for this controlled experiment.

The Direct challenger now has attention, learned embeddings, learned positional embeddings, the same 75,538-parameter architecture as the Structural model, the same learned arithmetic proxy on the same inputs, the same total training cardinality, and twice as many positive solved examples. Yet its final exact verified coverage is **31/243**, while the matched Structural model reaches **243/243**.

The narrow supported result is:

> in this generated 2x2 linear-system setting, with the specific pre-registered Tiny Transformer and training protocol, allocating the matched learned model to recognize executable structure produced much higher verified task completion than training the identical learned architecture to classify the final exact solution directly.

This still does **not** establish lower total computation. Structural execution additionally pays deterministic compilation, Gaussian elimination, and verification. Those deterministic costs are intentionally not collapsed into the learned weighted-sum proxy.

It also does not establish that Transformers cannot learn the algorithm. The Direct model is still tiny and receives only final-answer supervision. Larger/deeper models, curricula, autoregressive intermediate steps, coefficient extraction, program supervision, scratchpads, arithmetic modules, or other algorithmic inductive biases could move the Direct frontier dramatically.

That is now the most important falsification direction: improve the **Direct learning objective and intermediate supervision**, rather than simply increasing another shallow capacity grid.

## v0.0.32

Source: docs/experiments/v0.0.32.md
SHA256: 55dc22c9d799bc3d778bb113d8c70f8c19792c9f64580854c36a89f8ce9e0e73

### Next step after v0.0.32

If the oracle contract shows a real verified scaling opportunity:

### Implementation freeze before first result

The implementation fixes the remaining unspecified benchmark details before any v0.0.32 quality/scaling result is read.

### First measured result

GitHub Actions run #86 executed the full 256-example oracle benchmark and the complete existing regression suite.

### Representation bytes: positive and negative result

The solver-facing compressed core becomes much smaller.

At (k=2,n=32):

- raw full solver payload: **2,416.5 bytes**
- compressed core payload: **56.4 bytes**
- raw / compressed payload ratio: **42.87x**

At (k=4,n=32):

- raw full solver payload: **2,450.2 bytes**
- compressed core payload: **107.4 bytes**
- raw / compressed payload ratio: **22.81x**

However, the explicit v0.0.32 certificate is deliberately verbose because it duplicates original/core constraint evidence.

At (k=2,n=32):

- certificate: **7,360.6 bytes**
- certificate / raw payload: **3.05x**
- compressed payload + certificate / raw payload: **3.07x**

At (k=4,n=32):

- certificate: **8,401.3 bytes**
- certificate / raw payload: **3.43x**
- compressed payload + certificate / raw payload: **3.47x**

So v0.0.32 does **not** demonstrate end-to-end byte compression when the full explicit certificate is transmitted/stored alongside the reduced IR.

That negative result is retained.

A future certificate format may reference original constraints by identity/hash and encode only reduction evidence, but changing certificate compactness is a separate experiment and must not be retroactively used to improve v0.0.32.

### Interpretation

The oracle benchmark establishes three narrow facts.

### Decision

**KEEP — oracle Structural Compression benchmark contract is valid.**

The measured solver-work scaling opportunity is large enough to justify proceeding to a learned compression proposal experiment.

This decision does **not** mean learned compression has been demonstrated.

The next gate should ask:

> Can a small learned model recover a useful fraction of the oracle eliminations while every proposed reduction remains subject to deterministic certificate checking and full original-problem verification?

The primary learned-compression metric should be:

    oracle compression recovered
        at fixed verified retention

with false or unverifiable reductions failing closed.

## v0.0.33

Source: docs/experiments/v0.0.33.md
SHA256: 418e1ad3d247eab52a8e61203fd5834b24fefc9174d453b7bea0c6446aa5a184

### Next gate

If v0.0.33 shows meaningful learned recovery, the next experiment should remove at least one oracle scaffold.

Preferred next target:

    learned stopping / retained-dimension prediction

so the system must decide not only **what** to eliminate but also **how far** to compress.

### Post-result diagnostic-control amendment

After the first learned benchmark result was observed but **before merge**, one methodological gap was identified:

> learned recovery is not interpretable without knowing how much recovery comes from the candidate universe plus deterministic checker alone.

The primary endpoint and KEEP contract above are unchanged.

Two additional **diagnostic, not pre-registered primary** controls are therefore added:

1. deterministic random ranking of the same candidate universe,
2. a fixed non-learned heuristic ranking using only:
   - row density,
   - target-column incidence.

Both controls receive the same oracle-cardinality proposal budget B = n-k and the same deterministic checker.

They report:

- verified retention,
- elimination-count recovery,
- exact-oracle-rule recovery,
- fail-closed rejection count.

Because these controls were added after seeing the first learned result, they must be labeled post-result diagnostics in every report. They may challenge the interpretation of the learned result, but they do not retroactively become pre-registered endpoints.

### First measured result

GitHub Actions run #90 executed the complete pre-registered v0.0.33 experiment and the existing regression suite.

### Final aggregate result

Across all 256 final examples:

- examples with a real compression opportunity: **224**
- examples with any accepted learned compression: **224 / 224**
- final verified retention: **1.0**
- unsafe accepted reductions: **0**
- fail-closed rejected proposals: **1,209**
- mean elimination-count recovery: **0.7011**
- mean exact oracle-rule recovery: **0.7008**
- mean oracle solver-savings recovery: **0.8365**

Therefore, under the v0.0.33 oracle-cardinality control:

> the fixed tiny learned candidate scorer recovered about 70% of the oracle elimination count while the deterministic checker preserved 100% verified retention, and the resulting accepted reductions recovered about 84% of the oracle solver-operation savings.

### Per-cell final result

| k | n | mean accepted eliminations | elimination recovery | exact oracle-rule recovery | oracle solver-savings recovery | verified retention |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 4 | 1.844 / 2 | **92.19%** | **92.19%** | **95.73%** | 100% |
| 2 | 8 | 4.063 / 6 | **67.71%** | **67.71%** | **79.47%** | 100% |
| 2 | 16 | 8.469 / 14 | **60.49%** | **60.27%** | **79.74%** | 100% |
| 2 | 32 | 16.156 / 30 | **53.85%** | **53.85%** | **78.89%** | 100% |
| 4 | 4 | 0 / 0 | control | control | control | 100% |
| 4 | 8 | 3.531 / 4 | **88.28%** | **88.28%** | **90.75%** | 100% |
| 4 | 16 | 8.813 / 12 | **73.44%** | **73.44%** | **84.80%** | 100% |
| 4 | 32 | 15.344 / 28 | **54.80%** | **54.80%** | **76.20%** | 100% |

The recovery rate declines as apparent dimension grows.

This is important: v0.0.33 does not show scale-invariant learned compression discovery.

At n=32, the model still recovers roughly half of the oracle eliminations, but its recovery fraction is lower than at n=4 or n=8.

### Interpretation

v0.0.33 provides the first learned Structural Compression signal in NEUMANN, but only under a deliberately scaffolded controlled setting.

The strongest supported statement is:

> A 289-parameter shallow MLP candidate scorer, using a fixed 16-feature matrix-statistics representation and receiving the oracle elimination cardinality as its proposal budget, recovered about 70% of oracle eliminations and about 84% of oracle solver savings on held-out generated affine-linear systems, while deterministic checking and original-problem verification kept unsafe accepted reductions at zero.

This is narrower than saying that an AI discovered minimal sufficient structure.

The model still receives a major oracle scaffold:

    B = n - k

It knows how many elimination proposals it is allowed to make.

It does not infer:

- the true retained dimension,
- when compression should stop,
- whether no more safe compression exists,
- a globally minimal representation.

The input is also not raw natural language or a general sequence representation. It is a hand-designed 16-dimensional candidate feature contract.

### Decision

**KEEP — learned compression proposal contract is valid and produces a nonzero, substantial certified recovery signal.**

Proceeding is justified, but the immediate next scientific priority should be to attack the result rather than merely remove another scaffold.

Recommended next falsification gate:

1. add random and simple deterministic heuristic ranking controls,
2. compare them against the frozen v0.0.33 learned scorer,
3. then remove the oracle-cardinality budget only if the learned scorer retains a meaningful advantage.

If the learned scorer does not beat simple heuristics, the correct conclusion is that v0.0.33 primarily discovered a hand-engineerable structural statistic rather than a need for learned Structural Compression.

### Post-result deterministic random control

Using the same oracle-cardinality budget and deterministic checker, but ranking candidates by a SHA-256-derived deterministic pseudo-random score:

- elimination-count recovery: **24.3994%**
- exact oracle-rule recovery: **22.9114%**
- verified retention: **100%**
- fail-closed rejected proposals: **2,396**

### Post-result simple heuristic control

A deliberately simple non-learned score ranks candidates by lower:

    row density + target-column incidence

with the same oracle-cardinality budget and deterministic checker.

Result:

- elimination-count recovery: **61.5529%**
- exact oracle-rule recovery: **61.4785%**
- verified retention: **100%**
- fail-closed rejected proposals: **1,349**

### Final v0.0.33 decision

**KEEP — with a sharpened next falsification target.**

v0.0.33 establishes a reproducible certified learned-compression signal under an oracle-cardinality scaffold.

The next experiment should not simply celebrate the learned-vs-heuristic gap.

It should pre-register a stronger heuristic/control suite and then remove the oracle-cardinality scaffold.

The most informative next gate is:

1. freeze the current learned scorer,
2. pre-register stronger deterministic structural heuristics,
3. add a learned stopping / retained-dimension estimator,
4. compare quality and solver savings without supplying (n-k),
5. preserve deterministic reduction checking and full original-problem verification.

## v0.0.34

Source: docs/experiments/v0.0.34.md
SHA256: afee29a0cd3787de87e24194c84258ef6fbb483e9518e68269ab514faa621b7d

### Central questions



### Decision rule for the next milestone

If learned stopping remains competitive with or exceeds the strongest deterministic heuristic:

    proceed to harder structural families
    and/or learned retained-dimension modeling

If a deterministic heuristic matches or beats learned scoring:

    preserve that result
    and treat the heuristic as the new baseline architecture.

NEUMANN should absorb the cheapest mechanism that works rather than defend learned components for their own sake.

### Final measured result

Release-candidate execution used the immutable v0.0.33 checkpoint described in the pre-merge reproducibility amendment.

Two independent GitHub Actions executions of the same exact branch head reproduced the same:

- checkpoint SHA-256,
- calibration threshold,
- final learned aggregate,
- deterministic baseline aggregates.

Canonical frozen learned checkpoint:

    f9c1dccd0bda28619cb74c6fd6e8a457cde96944cbe5bfa65c9665859da3cc69

### Primary falsification result

The learned scorer has the highest raw dependency-reference F1:

    learned F1      = 92.63%
    Markowitz F1    = 77.86%

Descriptive difference:

    +14.77 percentage points

But the pre-registered Markowitz-style heuristic produces **more downstream solver savings**:

    learned solver savings    = 1,529.42
    Markowitz solver savings  = 1,584.34

Difference:

    learned - Markowitz = -54.92 solver arithmetic ops

Markowitz also has:

- lower retained-dimension MAE: **4.086 vs 4.508**
- higher exact generator-k match: **35.94% vs 31.25%**
- lower mean post-compression solver work: **387.31 vs 442.23**

This is a negative result for the idea that higher dependency-classification quality automatically yields better Structural Compression.

### Interpretation

v0.0.34 changes the research target.

The previous learned-compression framing implicitly treated generator dependency recovery as the main learning objective.

The gauntlet shows that this proxy can be misaligned with the actual computational objective.

A method may match fewer generator-reference rules yet remove more expensive solver work.

The more appropriate hierarchy is now:

    valid reduction
        ↓
    verified original-problem equivalence
        ↓
    marginal computational utility
        ↓
    reference-certificate similarity

Reference recovery remains useful for diagnostics, but it should no longer be the primary optimization objective.

### Final decision

**KEEP — v0.0.34 methodology and safety contract are valid.**

But the learned-compression hypothesis is narrowed.

The experiment does **not** justify treating the learned scorer as the preferred compression policy.

The strongest empirical lesson is:

> **The best predictor of a reference compression certificate is not necessarily the best policy for reducing verified computation.**

For the next milestone, NEUMANN should absorb the cheapest mechanism that works.

A natural v0.0.35 target is therefore **utility-directed Structural Compression**:

- freeze deterministic Markowitz / target-leaf baselines,
- measure marginal solver-work reduction per candidate,
- train or design policies against verified downstream computational utility rather than reference-rule labels,
- preserve deterministic checking and original-problem verification,
- include checker / reconstruction / verification costs explicitly before making any total-compute claim.

## v0.0.35

Source: docs/experiments/v0.0.35.md
SHA256: 312169791912d49a8308a30e8ee178c602b4ee2a44a0a38e5507cf0aba85d061

### Primary research question

> Does selecting certified reductions by measured Value-of-Reduction reduce downstream solver work more than selecting them by reference-label similarity or fixed local heuristics?

### Interpretation rules

If dynamic utility materially beats static isolated utility:

    next learned model should be state-aware.

If static utility is close to dynamic utility and beats structural heuristics:

    first learn the static utility target with the smallest adequate model.

If target-leaf / Markowitz remain competitive with the utility oracle:

    preserve them as first-class architecture components
    and do not add learned complexity without a measured benefit.

If utility targeting improves solver work but oracle-search cost is large:

    treat v0.0.35 as teacher-signal validation only.

### Planned next milestone

If v0.0.35 validates a useful utility target:

    v0.0.36 = learned Value-of-Reduction proposal

The learned model should be compared against:

- target-leaf
- Markowitz
- static exact utility teacher
- dynamic greedy utility oracle

and should retain the same validity / utility / stopping separation.


---

### Post-result record

This section was added only after the first full v0.0.35 execution completed.

Canonical first full run:

- GitHub Actions run: **141**
- PR: **#35**
- full benchmark start: **2026-09-28T06:03:14Z**
- full benchmark result emitted: **2026-09-28T06:13:33Z**
- benchmark wall interval: approximately **618.9 s**
- calibration systems: **192**
- final systems: **256**
- prior-signature disjointness: **PASS**
- calibration/final disjointness: **PASS**
- all calibrated methods verified retention: **1.0**
- utility oracle verified retention: **1.0**
- unsafe accepted reductions: **0**
- `KEEP = true`

### Central result

Dynamic minus static mean solver-savings gain:

    +618.51953125

Per-cell interaction gain:

| k | n | dynamic - static solver savings |
|---:|---:|---:|
| 2 | 4 | 11.90625 |
| 2 | 8 | 75.125 |
| 2 | 16 | 489.5625 |
| 2 | 32 | 2094.75 |
| 4 | 4 | 0 |
| 4 | 8 | 56.59375 |
| 4 | 16 | 399.09375 |
| 4 | 32 | 1821.125 |

This validates the pre-registered branch:

> if dynamic utility materially beats static isolated utility, the next utility model must be state-aware.

However the strongest cheap heuristic remains unusually competitive:

    target-leaf savings / dynamic savings
        = 0.972828...

Thus target-leaf recovered about **97.28%** of the dynamic greedy savings.

Dynamic greedy lowered the remaining retained-system solver ops from target-leaf's **210.37** to **161.50**, a **23.23%** reduction in remaining solver ops, but only **2.79%** additional solver savings relative to target-leaf's already-large savings.

### Cost interpretation

Dynamic teacher search is far more expensive than the work it removes.

Successful trial solver work alone is:

    104298.703125 / 1960.09375
        ≈ 53.21 × full baseline solver work

and:

    104298.703125 / 161.49609375
        ≈ 645.83 × final dynamic retained-system solver work

This excludes partial work performed inside invalid materializations.

Therefore no end-to-end efficiency claim is permitted.

## v0.0.36

Source: docs/experiments/v0.0.36.md
SHA256: 7b5ac03f36d9bd519d9526c6b8ce96e730dcf1fb48148624e1178a69bcb8168a

### Pre-registered decision rule

Proceed to a learned residual policy only if **all three** conditions hold on the untouched final set:

1. residual_headroom_recovery >= 0.50
2. positive_residual_rate >= 0.25
3. teacher_materialization_reduction >= 0.50

Interpretation:

- all three PASS -> proceed to a state-aware learned residual model,
- one or two PASS -> HOLD; inspect scale-conditioned routing before adding learned complexity,
- zero PASS -> DELETE the learned residual branch and retain deterministic target-leaf only.

These thresholds are research continuation gates, not claims of economic break-even or total-compute superiority.

### Next milestone

Only after a PASS continuation result:

    v0.0.37 = smallest adequate state-aware residual predictor

If the gate returns HOLD:

    v0.0.37 = pre-registered scale/router residual test

If DELETE:

    freeze target-leaf as the current cheap compression component
    and move to a harder structural family.


---

### Post-result record

This section was added after the first full v0.0.36 execution completed.

Canonical first full run:

- GitHub Actions run: **146**
- PR: **#37**
- final systems: **256**
- eight scale cells x **32** systems
- prior-signature disjointness: **PASS**
- core pytest: **189 passed, 1 skipped**
- sequence lane: **PASS**
- verified retention: **1.0**
- unsafe accepted reductions: **0**
- `KEEP = true`

### Aggregate result

Full-system baseline:

    mean solver ops = 1928.9609375

Frozen target-leaf @ 0.10:

    mean solver ops       = 202.32421875
    mean solver savings   = 1726.63671875
    mean accepted count   = 9.59375

Empty-start dynamic greedy teacher:

    mean solver ops       = 144.625
    mean solver savings   = 1784.3359375
    mean trials           = 282.7890625
    successful trial solver ops
                          = 103621.67578125

Cheap-first residual dynamic teacher:

    mean solver ops       = 47.23828125
    mean total savings    = 1881.72265625
    mean residual added   = 2.6015625 reductions
    mean residual trials  = 29.453125
    successful trial solver ops
                          = 1073.4296875

### Central result

The important result is stronger than "residual value exists."

The cheap-first residual path outperformed both components alone.

Relative to frozen target-leaf, residual search reduced the remaining retained-system solver work by approximately:

    76.65%

Relative to empty-start dynamic greedy, the cheap-first residual path reduced retained-system solver work by approximately:

    67.34%

Teacher trial materializations fell by approximately:

    89.58%

Successful trial solver work fell by approximately:

    98.96%

The hybrid therefore reached a lower final solver-work state while exploring far fewer expensive teacher states.

### Path-dependence result

The aggregate residual headroom recovery exceeded 1 because:

    cheap-first residual solver ops
        < empty-start dynamic greedy solver ops

This does not imply that the residual path exceeded a global optimum.

The empty-start dynamic teacher is only greedy with respect to immediate marginal solver-work gain.

The result instead shows that the greedy trajectory is path-dependent.

A cheap structural prior can place the system in a state from which subsequent marginal-utility search reaches a better solution than empty-start greedy search.

This changes the architectural interpretation.

The current candidate architecture is no longer:

    expensive utility search from raw structure

It is:

    cheap deterministic structural prior
        ↓
    certified compression
        ↓
    state-aware residual policy
        ↓
    deterministic checker
        ↓
    exact execution
        ↓
    original-problem verification

## v0.0.37

Source: docs/experiments/v0.0.37.md
SHA256: c11e496f81b6ccb87ba175845d16147ae094f84aca241bea3eae0fa4a951259f

### Learned-value decision rule

Let:

    learned_recovery
        = learned additional savings
          / teacher additional savings

and:

    learned_advantage_fraction
        = (learned additional savings
           - best deterministic additional savings)
          / teacher additional savings

Pre-registered decision:

### Next milestone

If KEEP_LEARNED_RESIDUAL:

    v0.0.38 = harder-family generalization and out-of-family residual transfer

If KEEP_DETERMINISTIC_RESIDUAL:

    freeze the deterministic residual policy and move to a harder family

If HOLD_RESIDUAL_MODELING:

    analyze residual state representation before adding capacity



---

### Post-result record

This section was added only after the first full v0.0.37 run completed.

Canonical first full run:

- GitHub Actions run: **159**
- PR: **#40**
- benchmark start: **2026-09-28T07:56:48Z**
- benchmark result emitted: **2026-09-28T08:09:16Z**
- benchmark wall interval: approximately **747.3 s**
- core pytest: **196 passed, 1 skipped**
- sequence lane: **PASS**
- train / validation / final: **96 / 64 / 192 systems**
- all v0.0.37 splits disjoint from prior data and one another: **PASS**
- verified retention for every deployable method: **1.0**
- unsafe accepted reductions: **0**
- `KEEP = true`

### Untouched final result

Frozen target-leaf first stage:

    mean solver ops = 209.40625

Exact one-step-greedy residual teacher:

    mean final solver ops          = 53.2083333
    mean additional savings        = 156.1979167
    mean attempted materializations= 30.5

Selected Tiny MLP:

    mean final solver ops          = 59.9270833
    mean additional savings        = 149.4791667
    teacher-savings recovery       = 0.9569857
    mean attempted proposals       = 2.4895833
    mean candidate scores computed = 31.1041667

Selected Markowitz residual:

    mean final solver ops          = 46.2239583
    mean additional savings        = 163.1822917
    teacher-savings recovery       = 1.0447149
    mean attempted proposals       = 8.5572917

Primary learned-value comparison:

    learned recovery           = 0.9569857
    learned advantage fraction = -0.0877292

Pre-registered gates:

    learned recovery >= 0.70           -> PASS
    learned advantage >= 0.10          -> FAIL
    verified retention = 1.0           -> PASS
    unsafe accepted reductions = 0     -> PASS

Decision:

    KEEP_DETERMINISTIC_RESIDUAL

### Central result

The Tiny MLP is not a failed learner.

It recovered approximately **95.70%** of the exact greedy teacher's residual
solver savings on untouched final data.

It is nevertheless unnecessary on this structural family.

The validation-selected deterministic Markowitz residual policy is simpler and
better on the primary final comparison:

    Markowitz additional savings - Tiny MLP additional savings
        = +13.703125 solver ops

Thus increasing learned capacity on this family would violate the project
sequence:

    question requirements
        -> delete
        -> simplify
        -> accelerate
        -> automate

The learned residual component is deleted.

### Next milestone

v0.0.38 should be a **Harder Structural Family Gate**.

It should introduce valid compression motifs that cannot be recovered reliably
from one local leaf/incidence statistic, for example:

- coupled multi-row / block dependencies,
- relation-level redundant constraints,
- equivalence or symmetry classes,
- adversarial local-incidence decoys,
- mixtures of easy local and non-local compression.

The frozen target-leaf + Markowitz pipeline remains a mandatory cheap baseline.

A learned component may return only if it creates pre-registered downstream
value beyond deterministic structural algorithms on an untouched harder
family.

## v0.0.38

Source: docs/experiments/v0.0.38.md
SHA256: 43b225e83397b9286b9f5ce6e1c87ae2ef0ac8852eb830f488a80a4a5e16fb33

### Interpretation

If all H1-H5 pass:

    family_status = HARDER_FAMILY_VALIDATED

and v0.0.39 may test discovery/routing among block candidates.

If safety passes but one or more H gates fail:

    family_status = FAMILY_NOT_HARD_ENOUGH

Do not train a model.

Redesign the generator or structural primitive first.

If safety fails:

    family_status = INVALID_FAMILY_OR_CHECKER

Stop and repair correctness before any learning experiment.

### Post-result record

This section was added after the first full v0.0.38 execution completed.

Canonical first full run:

- GitHub Actions run: **171**
- PR: **#42**
- final systems: **256**
- active compression systems: **224**
- no-compression controls: **32**
- prior-signature disjointness: **PASS**
- core tests: **PASS**
- sequence lane: **PASS**
- one-row verified retention: **1.0**
- block-oracle verified retention: **1.0**
- unsafe one-row reductions: **0**
- unsafe block reductions: **0**
- `KEEP = true`

### Aggregate result

Exact 2x2 block oracle:

    mean retained-dimension error = 0

Frozen v0.0.37 one-row pipeline:

    mean elimination recovery     = 0.0735119048
    mean solver-savings recovery  = 0.1151981768
    active progress rate          = 0.5625

Breadth:

    broad hard cells = 7 / 7 active cells

### Why H4 is not changed post-result

The motivation text for H4 mentioned avoiding a parser-blind benchmark, but the
pre-registered gate itself explicitly required:

    old pipeline still makes real progress

measured as:

    active examples with accepted one-row eliminations > 0

Changing that criterion to candidate visibility after seeing v0.0.38 would
change the confirmatory contract.

Candidate visibility is therefore retained only as a diagnostic.

The failed H4 remains binding.

### Important positive result

The exact 2x2 block primitive behaved correctly.

Across all active cells:

- the block checker re-derived exact algebra from original rows,
- retained dimension reached the declared core exactly,
- original-problem verification remained 100%,
- unsafe block reductions remained zero,
- the retained-dimension gap was broad in all 7 active cells.

So v0.0.38 validates the **need and correctness of a multi-row compression
primitive**, while rejecting the pure-coupled generator as the next discovery
benchmark.

### Next milestone

v0.0.38.1 = Mixed Local + Coupled Harder-Family Gate

Use a new untouched audit set.

Keep H1-H5 unchanged.

If all five gates pass on the new family, only then proceed to block
discovery/routing in v0.0.39.

## v0.0.39

Source: git:origin/research/v0.0.39-coupled-block-replication-clean:docs/experiments/v0.0.39.md
SHA256: 4c830a77fb2755663168ad5d501e57a146d0468c452c0b21eb618c7bb95ba464

### Fresh audit data

Use the same scale grid:

    k in {2, 4}
    n in {4, 8, 16, 32}
    n >= k

Per cell:

    32 fresh systems

Total:

    256 systems

Use new seeds not used by v0.0.38.

Every v0.0.39 signature must be:

- unique within v0.0.39,
- disjoint from v0.0.38,
- disjoint from all comparable prior generated signatures.

The final set is opened only after this specification and implementation are
committed.

### Family decision

If safety passes and all of:

    H1
    H2
    H3
    H4a
    H4b
    H5

pass on the fresh set:

    family_status = HARDER_FAMILY_VALIDATED

If safety passes but any gate fails:

    family_status = FAMILY_NOT_HARD_ENOUGH

If safety fails:

    family_status = INVALID_FAMILY_OR_CHECKER

No thresholds or gates may be changed after the v0.0.39 final set is opened.

### Next milestone if validated

Only after:

    HARDER_FAMILY_VALIDATED

may the next version test block discovery.

The first discovery experiment must compare:

1. deterministic exact 2x2 row-pair / target-pair enumeration,
2. sparse row-pair heuristics,
3. graph / connected-component pairing,
4. a learned block scorer only if cheaper deterministic methods leave
   pre-registered downstream headroom.

The optimization target remains:

    verified downstream solver work

not generator block-label imitation.

## v0.0.40

Source: docs/experiments/v0.0.40.md
SHA256: a75add74189c5094c615b585cb86146e61b8af6fab8e31a92f07843b6c5d7ece

### Next milestone

If:

    KEEP_DETERMINISTIC_DISCOVERY

then the next research move is a harder anti-shortcut family, not a larger
model.

If:

    LEARNED_DISCOVERY_HEADROOM

then v0.0.41 may test the smallest adequate learned block scorer.

If:

    REDESIGN_DISCOVERY_REPRESENTATION

then redesign the structural representation before adding capacity.


---

### Post-result record

This section was added after the first full v0.0.40 execution completed.

Canonical first full run:

- GitHub Actions run: **192**
- PR: **#48**
- final systems: **256**
- final systems per cell: **32**
- fresh signature disjointness: **PASS**
- all methods verified retention: **1.0**
- unsafe accepted reductions: **0 for every method**
- controls unchanged: **PASS**
- frozen local thresholds unchanged: **PASS**
- `KEEP = true`

### Pre-registered primary decision

The selected deterministic method was:

    D4_incidence_component_graph

with:

    mean solver-savings recovery = 1.0
    mean elimination recovery    = 1.0
    block precision              = 1.0
    block recall                 = 1.0
    block F1                     = 1.0
    verified retention           = 1.0
    unsafe accepted reductions   = 0

All deterministic-sufficiency gates passed:

    solver-savings recovery >= 0.95   PASS
    elimination recovery >= 0.95      PASS
    block recall >= 0.95              PASS
    verified retention = 1.0          PASS
    unsafe reductions = 0             PASS

Therefore:

    decision = KEEP_DETERMINISTIC_DISCOVERY

No learned block scorer is justified on this frozen family.

### Important tie interpretation

D2, D3, and D4 are **performance-equivalent** on this audit set.

The pre-registered method-selection rule chose D4 because, after equal recovery,
equal final solver work, and equal discovered-block counts, it used fewer
reported row-pair examinations.

This does **not** establish that D4 has lower total discovery cost.

D4 reports graph-edge examinations instead of row-pair examinations, and the
experiment explicitly forbids combining unlike cost units into a synthetic
score.

Therefore the valid conclusion is:

> D2, D3, and D4 all recover the full verified compression value on this
> family; D4 is the formal selected method under the frozen tie-break, not a
> demonstrated universal cost winner.

### Central structural result: routing before discovery

The strongest v0.0.40 result is the D1 -> D2 transition.

D1:

    coupled targets consumed locally = 0.7109 / system on average
    block recall                     = 86.46%

D2:

    coupled targets consumed locally = 0
    block recall                     = 100%

The exact same block-overlap discovery primitive changes from incomplete to
perfect when target incidence is used to reserve multi-row structure before
local elimination.

The causal architecture suggested by this family is therefore:

    raw exact system
        ↓
    cheap structural routing
        ├── incidence 1 -> local one-row path
        └── incidence >1 -> reserve for multi-row path
        ↓
    deterministic structure discovery
        ↓
    exact algebra checker
        ↓
    retained solve
        ↓
    reconstruction
        ↓
    original-problem verification

This is stronger than a "better block scorer" story.

The main failure mode was consuming the wrong structural degrees of freedom too
early.

### Next research direction

The next version should be a harder anti-shortcut structural family.

It should be designed so that:

    cheap local routing still has value

but:

    incidence / exact 2x2 component topology alone is insufficient.

Only if deterministic methods leave pre-registered verified downstream
headroom should learned structural discovery be reconsidered.

## v0.0.41

Source: docs/experiments/v0.0.41.md
SHA256: 5c8ed566c8fb61ce2e27fe3597a15b98fe38593d824c7dd301a3be9b57f9146a

### v0.0.41 — Anti-shortcut family, first causal audit

Status: pre-registered protocol. Commit this specification before running the
final audit. No learned block model is trained in this version.

### Question

The v0.0.40 family was saturated by deterministic discovery. Is its success
dependent on unit target coefficients, or on isolated two-row components?
Separate these two interventions so a failed discoverer is not mistaken for
evidence that a neural model is needed.

### Decision gates

KEEP_AUDIT requires 224 unique fresh systems, exact oracle materialization
and original-system verification for all 224, verified retention for all
methods, and zero unsafe accepted reductions. If a frozen method violates
this, diagnose and fix the safety path, then regenerate a new final split;
do not edit the method and reuse the same final split for the main result.

If COEFFICIENT candidate visibility is below 95%, label its discovery gap
**REPRESENTATION_LIMIT**. A failed unit-only parser does not justify a learned
block scorer. If OVERLAP candidate visibility is at least 95% and the best
deterministic method recovers under 95% of oracle solver savings with 100%
verified retention, label **DISCOVERY_HEADROOM**. Otherwise label
**DETERMINISTIC_SUFFICIENT** for that arm. COMBINED is interaction evidence,
not an independent neural-model gate. If no arm preserves verified oracle
savings above zero in each active cell, label **INVALID_FAMILY**.

No decision in this version claims general reasoning, total-compute savings,
or 10x performance. An isolated synthetic family is a failure probe.

---

### First full audit record (post-result)

Executed from frozen implementation commit `58aeb43`, with
`PYTHONHASHSEED=0`, `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`.
The machine-readable result is `results/v041_first_audit.json`.

The 224 systems were unique and disjoint from prior signatures; all 14 cells
contained 16 systems. All 224 oracle reconstructions verified the original
system. All 1,120 method outputs (224 × 5) verified and zero unsafe accepted
reductions were recorded. `KEEP_AUDIT = true`.

| Arm | Systems | Coupled candidate visibility | Best D0-D4 mean solver-savings recovery | Decision |
| --- | ---: | ---: | ---: | --- |
| COEFFICIENT | 64 | 0% | 16.35% (D4 tie-break) | REPRESENTATION_LIMIT |
| OVERLAP | 64 | 100% | 30.96% (D3) | DISCOVERY_HEADROOM |
| COMBINED | 64 | 0% | 16.29% (D4 tie-break) | Interaction evidence only |
| No-reduction control | 32 | n/a | n/a; 0 reductions | Control |

OVERLAP D1 and D2 each produced joint candidate sets that failed exact
materialization on all 64 examples. They safely fell back to the verified
full solve, for 0% recovered savings. D3 kept a valid but incomplete subset:
its block recall was 10.53%, versus 30.96% mean solver-savings recovery.
No claim is made that the generator's block identity is the unique valid
decomposition.

The COEFFICIENT result identifies the old unit-only parser boundary. The
OVERLAP result identifies a discovery/selection bottleneck with the declared
blocks fully visible. Neither result demonstrates neural headroom: a
deterministic conflict-aware selector and candidate-visibility repair have
not yet been tested. The next experiment should freeze those deterministic
baselines before deciding whether learned proposal scoring is useful.

These are solver arithmetic-operation counts only. Discovery, exact checking,
reconstruction, verification, training, memory, and energy have separate
costs. This audit makes no total-compute or edge-efficiency claim.

## v0.0.42

Source: docs/experiments/v0.0.42.md
SHA256: 33fb8ad746504e26d144a54d9cc2e3bd7d389df5b46de4848c54da2c133d5eb4

### Question

v0.0.41 found two distinct failures on generated exact linear systems:

- generic nonunit block targets had 0% visibility to the unit-only parser;
- in the overlap arm, declared targets were 100% visible but D1/D2 selected
  incompatible candidate sets and fell back to full solving on 64/64 cases.

Can a simple deterministic parser and a residual-incidence selector close
those gaps while retaining original-problem verification? This is an explicit
test of an engineered motif; it is not a general structure-discovery test.

### Fresh audit

Reuse v0.0.41 arm definitions, 16 examples per (arm,k,n) cell, arms
COEFFICIENT/OVERLAP/COMBINED and (k,n) in {(2,16),(2,32),(4,16),(4,32)}.
Use 16 examples each for no-reduction (2,2) and (4,4) controls. Total 224.
Final seeds start at 1,010,000 + 1,000*k + n, plus fixed arm offsets
0/100,000/200,000; control seeds start at 1,310,000 + 1,000*k + n.
Validation fixtures use seeds outside those ranges. Reject duplicates and
signatures seen in v0.0.41 and all its predecessors. Freeze methods before
the first full final run. No reusing v0.0.41 final examples as final data.

### Measurements and decisions

Report by arm and cell: verified retention, unsafe accepted reductions,
nonunit candidate visibility, mean verified solver-savings and elimination
recovery relative to the exact generator reference, accepted block-label
recall only as a diagnostic, mean exact solver arithmetic ops, row-pair
examinations, 2x2 derivation/checker calls, final materialization attempts,
and rejected joint materializations. Measure checker arithmetic, wall time,
memory, and energy separately before claiming total efficiency; solver
savings alone cannot establish it.

KEEP_AUDIT requires all 224 unique fresh systems; all 224 oracle references
verified; all 448 E1/E2 final answers verified; zero unsafe accepted
reductions; 16 examples in each of 14 cells; and no accepted reductions
on controls. A method may safely fall back and still satisfy KEEP_AUDIT.

For each active arm, label **DETERMINISTIC_SUFFICIENT** only if E2 achieves
at least 95% mean solver-savings recovery, at least 95% mean elimination
recovery, 100% verified retention and zero unsafe reductions. Otherwise
label **RESIDUAL_HEADROOM**. If COEFFICIENT E1 misses its declared block
row-target incidences, label **PARSER_REPAIR_FAILED**. If any oracle has no
positive solver savings, label **INVALID_FAMILY** for that cell. A headroom
result does not itself justify a neural model.

This family still exposes an engineered small-degree motif. Success cannot
establish optimal decomposition, total-compute savings, edge AI savings, or
transfer to natural-language and real engineering tasks.

---

### First full audit record (post-result)

Executed from frozen implementation commit `c7602b0` with
`PYTHONHASHSEED=0`, `OMP_NUM_THREADS=1`, and `OPENBLAS_NUM_THREADS=1`.
Machine-readable output: `results/v042_first_audit.json`.

The audit contained 224 fresh, disjoint systems in 14 complete cells. All
224 oracle references, all 448 E1/E2 outputs, and all 1,120 unchanged D0-D4
outputs verified the original full system. Unsafe accepted reductions: zero.
All 32 controls remained uncompressed. `KEEP_AUDIT = true`.

| Arm | E1 candidate visibility | E1 mean solver-savings recovery | E2 candidate visibility | E2 mean solver-savings recovery | E2 mean elimination recovery |
| --- | ---: | ---: | ---: | ---: | ---: |
| COEFFICIENT (64) | 100% | 100% | 100% | 100% | 100% |
| OVERLAP (64) | 10.53% | 29.60% | 100% | 100% | 100% |
| COMBINED (64) | 10.53% | 31.90% | 100% | 100% | 100% |

All three active arms meet the frozen `DETERMINISTIC_SUFFICIENT` gate. E2
matched the generator oracle's declared blocks in all 192 active systems.
This does not establish that those blocks are globally optimal or unique.

## v0.0.43

Source: docs/experiments/v0.0.43.md
SHA256: 04ff20db2ba1e9479a431bbcd91c298199648ec641b32d08e4bb486b80bb3dc8

### Fresh audit

The three v0.0.41 arm definitions remain COEFFICIENT, OVERLAP and COMBINED.
Cells (k,n): (2,16), (2,32), (4,16), (4,32). Sixteen fresh systems per
cell and arm: 192 active. No-reduction controls (2,2) and (4,4): 16 each.
Total 224. Final seeds begin at 1,410,000 + 1000*k + n with the frozen
arm offsets 0/100,000/200,000. Control seeds begin at 1,710,000 + 1000*k+n.
Validation fixtures use other seeds. Reject duplicate signatures and any
signature in v0.0.42 or its predecessors. Freeze implementation before the
first full final result.

### First and only final audit

`docs/experiments/results/v043_first_audit.json` records the first 224-system
result. All signatures were unique and disjoint from prior frozen audits;
every cell was complete. All 224 old and new solutions verified against the
original equations. All 192 active cases matched on exact accepted local
and block keys, full rational answer, retained dimension, and solver
arithmetic operations. Each active arm recovered 100% of its oracle solver
savings and declared eliminations. No unsafe accepted reductions occurred.

| Arm (64 each) | F0 pairs / system | F1 pairs / system | F1/F0 | F1 posting edges / updates | F0/F1 derivations and checkers | Median paired runtime F1/F0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| COEFFICIENT | 1,305.5 | 58 | 4.44% | 38 / 19 | 58 / 58 | 0.877 |
| OVERLAP | 1,305.5 | 9.5 | 0.73% | 72 / 36 | 9.5 / 9.5 | 0.855 |
| COMBINED | 1,305.5 | 9.5 | 0.73% | 72 / 36 | 9.5 / 9.5 | 0.893 |

The 32 controls remained uncompressed and verified. F1 made zero joint
materialization attempts or rejections; F0 attempted and rejected 16
whole-system (2,2) proposals. The indexed method did not reduce derivation
or exact checker calls in the active arms; it reduced repeated unproductive
pair enumeration. Index construction and posting updates are additional
work, so pair counts must not be interpreted as total compute.

Three paired measurements per method and example included routing, discovery,
checking, materialization/retained solve, reconstruction and original
verification. Per-arm medians of the per-example medians, F0 → F1, were
11.007 → 9.073 ms (COEFFICIENT), 14.322 → 11.081 ms (OVERLAP), and
11.113 → 8.996 ms (COMBINED). Paired ratios above are medians of each
example's F1/F0 median, not ratios of arm-level medians. These are noisy
single-machine wall times, not energy, peak RAM or deployment latency.

Decision: **KEEP_INDEXED** under the registered equivalence, safety,
controls and per-arm ≤10% search-work gates. The evidence is specific to
these generated low-degree exact systems; it does not establish a faster
general-purpose solver or learned structural intelligence. Run
`python benchmark_v043_smoke.py` for the contract and
`python benchmark_v043.py` to reproduce the deterministic audit (timings
will vary).

## v0.0.44

Source: docs/experiments/v0.0.44.md
SHA256: 4b2ee2be2d9ade1a2255483ceb8a8b13cd15969c26a0b4829d09471d1a6890dd

### Question and construction

Can an exactly valid elimination become invisible under either of F1's
restrictions: original target incidence at most four, or exactly two eligible
targets shared by a row pair? Construct two intervention arms:

1. HIGH_DEGREE: start with a fresh, shuffled coefficient-variant mixed
   system. Add the final oracle block's *two* targets, with nonzero
   coefficients, to both rows of each of the first two independent oracle
   blocks; recompute their right-hand sides from the fixed ground truth.
   Each selected target now occurs in exactly six original rows, but the
   complete oracle elimination is still an acyclic, verified certificate.
   These variables are excluded by F1's original incidence bound.
2. ALTERNATIVES: create a square system with k=2 or 4 dense, nonsingular
   core variables and four coupled variables. All four coupled variables
   occur in the same four coupled rows; every such row pair has four eligible
   targets. On one fixed row pair derive two *different* 2x2 certificates
   eliminating disjoint pairs of targets. Each must materialize separately
   by exact substitution into the retained equations, solve, reconstruct
   and verify the same original answer with positive *retained-solver*
   arithmetic savings. F1's exact-two-target gate should miss both.
   No claim is made that both alternatives can be accepted together.

Control: unmodified (2,2) and (4,4) nonsingular no-reduction systems. The
generator may use oracle labels and ground truth to construct or evaluate
examples; the frozen discovery method receives only the full system and
the frozen local scorer. Shuffle rows and columns in both active arms.

### Measurements and decision

On all 224 examples report F1 original-equation verification and rejected
joint materializations; any incorrect accepted answer is a safety failure.
For HIGH_DEGREE report per-cell variable-elimination recovery, solver
arithmetic savings recovery versus the full oracle, number of 6-incidence
targets, and pair/derivation/checker/posting counts. Oracle solver savings
must be positive in every example. For ALTERNATIVES report count of
systems with two different independently valid positive-savings witnesses,
F1 accepted reductions, F1 final solver operations versus full and each
witness, and pair/derivation/checker/posting counts. Also report the Schur
construction's scalar multiplication/addition count separately; the
retained-solver savings exclude this work. Controls must retain
their full dimension and verify with no rejected proposals. Do not treat
solver arithmetic as total computation; index, routing and checks cost work.

`BOUNDARY_CONFIRMED` requires all freshness, construction, reference,
safety, and control conditions, plus at least one HIGH_DEGREE example with
lower than full oracle recovery and at least one ALTERNATIVES example with
no reduction despite both verified witnesses. Otherwise record
`BOUNDARY_NOT_REPRODUCED` or `INVALID_FAMILY`, with the failure details.
Report exact rates by arm regardless of the decision. A positive boundary
finding does not authorize retrofitting F1 against these final examples and
calling the result a fresh confirmation.

This audit does not test natural-language parsing, real workloads, learned
structure discovery, energy or peak memory. The two witnesses demonstrate
nonuniqueness of valid local eliminations, not global optimality.

### First and only final audit

`docs/experiments/results/v044_first_audit.json` records 224 unique systems
with signatures disjoint from all prior frozen audits. All cells were complete.
All F1 results and benchmark baselines verified the original equations;
there were zero rejected joint materializations and zero unsafe accepted
answers. Both high-degree targets occurred in exactly six original rows in
each of the 96 HIGH_DEGREE examples. All 96 full oracles were verified and
gave positive solver arithmetic savings.

| HIGH_DEGREE cell | Count | Mean variable elimination recovery | Mean oracle solver-savings recovery | Missed ≥1 elimination |
| --- | ---: | ---: | ---: | ---: |
| 2×16 | 24 | 85.71% | 96.05% | 24/24 |
| 2×32 | 24 | 93.33% | 98.95% | 24/24 |
| 4×16 | 24 | 83.33% | 93.26% | 24/24 |
| 4×32 | 24 | 92.86% | 98.51% | 24/24 |

Across HIGH_DEGREE, F1 recovered 88.81% of declared eliminations and
96.69% of reference solver arithmetic savings on average. It examined
48.5 indexed row pairs, made 48.5 derivations and exact checker calls,
constructed 34 posting edges, and updated 17 variable postings per system.
The two missed targets account for the per-system elimination gap. Solver
savings recovery is high because these are mostly large n systems and only
one two-variable block was deliberately hidden.

All 96 ALTERNATIVES systems had **two distinct independently valid** exact
Schur witnesses on a fixed row pair. Each retained two fewer variables,
reconstructed the same verified answer, and saved retained solver arithmetic
relative to the full solve. F1 made zero pair examinations and accepted zero
reductions in all 96, solving the full systems. Their mean full-solve cost
was 388.44 arithmetic operations; the two witness retained solves averaged
160.77 and 164.35, with **additional** Schur-construction counts averaging
47.96 and 45.21 scalar multiplication/additions. These figures omit candidate
search, exact checking, reconstruction and original verification, so they
do not prove end-to-end or energy savings. The current production materializer
cannot enact these dense witnesses: it lacks substitution into retained
equations. The 32 controls stayed uncompressed and verified without rejection.

Decision: **BOUNDARY_CONFIRMED**. The original-incidence cap hides exact
high-degree targets, and the pair index's exact-two-target rule hides
alternative dense certificates. This is a reproducible limitation of the
frozen deterministic proposal and its current materializer on constructed
systems, not evidence that a learned model will solve the issue. A next
repair should implement algebraically valid retained-equation substitution
and bound its full cost before revisiting candidate search on *new* data.
Run `python benchmark_v044_smoke.py` for contract checks, or
`python benchmark_v044.py` for this deterministic audit.

## v0.0.45

Source: docs/experiments/v0.0.45.md
SHA256: a7976bc7cac348040c102f271adb90316562cf6bd880889bd500883b60dfc7c1

### Fresh adversarial audit

Reuse the v0.0.44 HIGH_DEGREE and ALTERNATIVES construction mechanisms, but
not any prior final system. HIGH_DEGREE: (2,16),(2,32),(4,16),(4,32),
24 each, seeds 2,110,000+1000*k+n. ALTERNATIVES: (2,6),(4,8), 48 each,
seeds 2,210,000+1000*k+n. Controls (2,2),(4,4), 16 each, seeds
2,310,000+1000*k+n. Total 224. Fixtures start at 2,090,000. Signatures
must be unique and disjoint from v0.0.44 and all predecessors. Freeze
implementation, evaluator and contracts before the first full final audit.

The HIGH_DEGREE complete oracle and the two independent dense witnesses
must again verify the original system. Both F0 and F2 must verify all 224
answers against original equations with zero unsafe accepted reductions.
The 32 controls must remain full dimension, with no rejected proposals.

### First and only final audit

`docs/experiments/results/v045_first_audit.json` contains 224 unique fresh
systems with complete cells. F0, F2 and the benchmark baseline verified
the original answer on all 224; there were zero rejected joint proposals.
The reference oracle in HIGH_DEGREE and both exact dense witnesses in
ALTERNATIVES were valid on all corresponding examples. Controls remained
uncompressed and verified.

| Arm | F0 → F2 variables removed (mean) | F0 → F2 retained solver ops (mean) | F0 → F2 indexed/scan pairs (mean) | F2 extra work | Median paired full-path F2/F0 |
| --- | ---: | ---: | ---: | --- | ---: |
| HIGH_DEGREE (96) | 19 → 21 | 149.81 → 55.77 | 48.5 → 56 | Posting edges 34 → 46; updates 17 → 23; exact checks 48.5 → 56 | **1.060** |
| ALTERNATIVES (96) | 0 → 2 | 393.54 → 168.44 | 0 → 4.55 | Mean Schur construction 44.96 scalar operations; 2 checker calls | **1.487** |
| Controls (32) | 0 → 0 | 55.75 → 55.75 | 0 → 0 | No materialization or rejection | 1.004 |

The HIGH_DEGREE F2 result equaled the full oracle retained dimension and
solver arithmetic in **96/96**, including 24/24 in every cell. ALTERNATIVES
F2 eliminated exactly two variables with positive retained-solver arithmetic
savings in **96/96**. The production F1 method remained untouched. The
diagnostic runtime instead became slower: high-degree paired ratio 1.060,
with each cell above 1.04, and dense paired ratio 1.487. Per-arm median
per-example times were 15.747 → 17.653 ms (HIGH_DEGREE), 0.641 → 0.950 ms
(ALTERNATIVES). These medians can vary on a different machine; all measured
F2/F0 ratios above one are reported as negative local runtime outcomes.

Decision under the registered structural gates: **STRUCTURAL_REPAIR_CONFIRMED**.
Deployment/performance decision: **do not promote F2**. Its narrower
retained solves did not pay for discovery, exact checking, substitution and
verification on these cases. Even the 44.96 counted Schur scalar operations
omit candidate-search overhead and rational bit complexity. The next
research question is whether a *selective*, cost-aware gate can predict
when structural work actually reduces the verified end-to-end path on new
data. No model improvement, energy saving, general-purpose speedup or
real-world scaling is established. Reproduce with `python benchmark_v045.py`
or run the small contract with `python benchmark_v045_smoke.py`.

## v0.0.46

Source: docs/experiments/v0.0.46.md
SHA256: fc76bf24020401dca8dc68ac6ce7fd07360b491b25f7721d89115f3dac0494bd

### Fresh audit

HIGH_DEGREE: (k,n)=(2,16),(2,32),(4,16),(4,32), 24 each, seeds
2,410,000+1000*k+n. ALTERNATIVES: (2,6),(4,8), 48 each, seeds
2,510,000+1000*k+n. Controls: (2,2),(4,4), 16 each, seeds
2,610,000+1000*k+n. Total 224. Separate contract seeds begin at
2,390,000. Generator mechanisms are v0.0.44's but system signatures
must be unique and disjoint from every prior final audit. Freeze generator,
method, evaluator and contracts before first full final result.

### Gates, cost and decision

All three methods must verify original equations on all 224; zero unsafe
accepted reductions. The full HIGH_DEGREE reference must verify with
positive solver arithmetic savings in all 96. F3's exact accepted local
and block keys, full rational answer, retained dimension and solver
arithmetic must equal F2 in all 96; both must match the oracle dimension and
solver operations. F3 must exactly equal F1's keys, answer, dimension and
solver operations on all 96 ALTERNATIVES and 32 controls; controls must
remain uncompressed with no rejected joint proposals.

Count initial posting edges, posting-removal updates, eligible pair
evaluations (on creation/change, plus priority-queue stale pops), candidate
derivations, exact checker calls, materialization attempts and rejections.
The primary cache-work gate is mean F3 derivations and checker calls no
more than 50% of F2 in HIGH_DEGREE. Do not equate these counts with total
computation; heap maintenance and construction have cost.

Diagnostic end-to-end wall time: three paired repetitions each for F1,
F2 and F3 per example, alternating order by example and repetition; use
`perf_counter_ns`. Include routing, indexing, derivation, checking, heap
maintenance, materialization, retained solve, reconstruction and original
verification. Exclude frozen scorer fit, data creation and benchmark-only
baseline/oracle solves. Report median per-example F3/F2 and F3/F1 ratios
by arm; ratios above one are negative results. The runtime threshold is
not a structural PASS gate because local timing is noisy. No energy,
memory or general-workload claims.

`CACHE_CORRECT` requires freshness, exact equivalence, safety, controls and
the ≤50% cache-work gate. Otherwise record `CACHE_FAILED` or
`INVALID_FAMILY` with details. Even `CACHE_CORRECT` is not promotion to a
performance baseline if full-path time is worse than F1. F3's dense
abstention trades away two possible exact eliminations to avoid a measured
cost regression; this is not a universal cost-optimal policy.

### First and only final audit

`docs/experiments/results/v046_first_audit.json` contains the first 224
fresh unique systems, disjoint from every prior frozen audit and complete
in all declared cells. F1/F2/F3 verified the same original answer in every
case; the HIGH_DEGREE oracle and both independent ALTERNATIVES witnesses
were also valid. There were zero rejected joint proposals or unsafe
accepted answers. The 32 controls stayed uncompressed.

| Arm | Count | F2 → F3 checker calls / system | F2 → F3 eligible pair work | F3/F2 paired full-path time | F3/F1 paired full-path time |
| --- | ---: | ---: | ---: | ---: | ---: |
| HIGH_DEGREE | 96 | 56 → 9.5 | 56 → 9.5 | 0.696 | **0.764** |
| ALTERNATIVES | 96 | 2 → 0 | 5.98 → 0 | 0.656 | 1.017 |
| Controls | 32 | 0 → 0 | 0 → 0 | 1.010 | 1.015 |

F3 matched F2's exact local/block keys, answer, retained dimension and
oracle solver arithmetic on all 96 HIGH_DEGREE cases. Derivations and
checker calls fell to **16.96% of F2**, meeting the pre-registered ≤50%
gate. Posting construction edges (46) and updates (23) per system were
unchanged. The observed stale-heap-pop count was zero in this constructed
family, so conflicting candidate churn remains untested. Mean retained
solver arithmetic was 56.06 for F2/F3 versus 148.29 for F1.

F3 exactly matched F1 on all 96 ALTERNATIVES and 32 controls, as intended
by abstention. It did *not* achieve the two available dense eliminations.
Compared with F2 it avoided a costly path, but compared with F1 it still
built the broader index and ran marginally slower in the dense and control
arms. Per-arm medians of per-example median time were F1/F2/F3
8.792/9.431/5.578 ms (HIGH_DEGREE), 0.312/0.496/0.324 ms
(ALTERNATIVES), and 0.060/0.063/0.061 ms (controls). Paired ratios in
the table are medians of within-example ratios, not arm-median ratios.

Decision: **CACHE_CORRECT**, with a *conditional* local runtime improvement
on this high-incidence constructed family. Do not claim global F3 dominance
or promote it as a general structural policy: the dense and control costs
are neutral-to-negative, the benefits rely on a reusable exact low-degree
motif, and no real workloads, energy, peak memory or learned proposal were
tested. Next challenge: conflicting candidates and perturbations that make
the cache invalidate/rebuild, plus a cost-aware abstention rule that avoids
index construction when the structural motif is absent. Run
`python benchmark_v046_smoke.py` or `python benchmark_v046.py`.

## v0.0.47

Source: docs/experiments/v0.0.47.md
SHA256: 0b9deacb81a179ce44c4fd1a66b08dab52a8f1ecbfe3a006bac212d761ec508d

### Contract and audit

Implement a small support-pair analyzer independent of F3's heap. For a
square integer matrix, identify support pairs with exactly two target
columns and nonsingular 2x2 pivot, then classify whether any two pairs
share a row. Check exact rank using rational elimination, not floating
point. A row-overlap fixture has four columns supported in three rows; it
must have rank less than four, even though each local 2x2 pivot is valid.
Repair the fourth column by adding support in a fourth row; the matrix
must become full-rank while the second pair ceases to be eligible. A
disjoint-pair fixture must be full-rank with both pairs eligible. Run 128
fresh seeded integer variants of each of these three arms (384 total),
with distinct matrix signatures. Contracts use separate seeds. The result
file records the first and only complete audit, arm counts, rank, eligible
pairs and overlap. No oracle labels enter the analyzer.

PASS requires 128/128 in each declared arm: the overlap arm is singular
with two individually valid overlapping pivot pairs; repaired arm is
nonsingular with exactly one eligible pair; disjoint arm is nonsingular
with two eligible disjoint pairs. Every audit signature must be unique.
Any failed assertion is a boundary counterexample to investigate, not an
invitation to adjust the generated examples after seeing the audit.

### First and only complete audit

`docs/experiments/results/v047_first_audit.json` records all 384 distinct
matrices: 128/128 overlap fixtures had rank three and two individually
valid overlapping 2x2 pivots; 128/128 repaired fixtures had rank four and
only one eligible pair; 128/128 disjoint fixtures had rank four and two
disjoint eligible pairs. All signatures were unique. Decision:
**BOUNDARY_CONFIRMED**. This is a constructive control alongside the
general rank argument, not a claim that testing 384 matrices alone proves
the theorem. The intentionally singular overlap fixtures are not valid
original solving tasks; do not score a compressor on them. No throughput,
learned-model quality, energy, or memory improvement was measured.

## v0.0.48

Source: docs/experiments/v0.0.48.md
SHA256: 9d36cf1a629cd8d74553828b3d471b30deff5e51101bb312b6789c3aa07897b3

### v0.0.48 — Cost-gate opportunity audit before model training

Status: pre-registered and evaluator frozen in `9ef9a18` before the first
complete audit. F1 (v0.0.43) and F3 (v0.0.46) remain frozen.
No model is trained in this step. The question is whether any useful
decision boundary remains after a cheap deterministic gate, not whether
a classifier can fit synthetic generator labels.

### Decision

`OPPORTUNITY_VISIBLE` only if the exact safety/freshness conditions hold,
both F1 and F3 have at least 16 robust wins each, and at least 16 cases
where the cheaper measured route conflicts with the static gate's route.
Otherwise `NO_LEARNED_GATE_JUSTIFIED` (or `INVALID_FAMILY` on failed
safety/freshness). Even an opportunity is not a model performance claim:
timing labels can be noisy, and a learned model in a following version
must beat this static gate on held-out generator mechanisms including its
feature/inference cost. Do not promote a model solely on this dataset.

No energy, peak memory or real-workload claims. This is a synthetic local
cost feasibility check, not a 10x gain or proof of general intelligence.

### First and only complete audit

The [raw summary](results/v048_first_audit.json) records 128/128 distinct,
fresh, exact systems with both paths and the static gate verifying the
same original answers. No gate fallback was needed. The paired medians
and robust-win counts were:

| Arm | Count | F3/F1 full-path median | Gate/F1 full-path median | Robust F1 / F3 / neutral |
| --- | ---: | ---: | ---: | ---: |
| High-degree | 48 | 0.881 | 0.893 | 1 / 30 / 17 |
| Dense | 48 | 1.007 | 1.016 | 2 / 1 / 45 |
| Control | 32 | 0.997 | 0.991 | 3 / 3 / 26 |

Across all systems, 6 were robust F1 wins, 34 robust F3 wins and 88
neutral under the pre-registered 10% filter. Only five robust winners
conflicted with the static gate; all high-degree systems had an original
degree-six column and none of the dense/control systems did. Decision:
**NO_LEARNED_GATE_JUSTIFIED**. This is not proof that learning cannot help
on other families. The few opposite-arm robust wins could reflect local
timing noise; no repeat audit, model fit or threshold tuning follows this
result. The next family must break the original-incidence shortcut and
show independently verified residual headroom before fitting a model.

## v0.0.49

Source: docs/experiments/v0.0.49.md
SHA256: 2df7c41acd857892b12e3208d455d39b4ef8c940a75a9fa27a8aedda37a27b18

### First and only complete audit

`docs/experiments/results/v049_first_audit.json` records 96/96 matched
structural contrasts, 192 unique exact systems, all original answers
verified and no static-gate fallback. F3 retained two fewer variables
in the recoverable member of every pair, but the fixed one-feature gate
selected F3 on both members. The paired full-path F3/F1 medians by cell
were recoverable/retained-support: 2x16 **0.816/0.813**, 2x32
**0.615/0.615**, 4x16 **0.904/0.895**, 4x32 **0.677/0.695**.
The median within-pair differences were respectively +0.002, +0.008,
-0.030 and +0.008 (negative-member ratio minus positive-member ratio).
These are local timing diagnostics, not stable hardware or energy gains.

There were 81 robust F3 wins in recoverable members, zero robust F1
wins in retained-support members, zero robust cost reversals and zero
static-gate robust mistakes. Decision:
**STRUCTURAL_CONTRAST_NO_COST_HEADROOM**. Matched incidence successfully
removed the v0.0.48 feature shortcut, but shifting one target's support
did not remove the other reusable candidates, so F3 remained favorable
on the negative member. Do not train a gate on these labels. A further
family must remove the cache's remaining repeated-work benefit while
retaining cheap-feature matching and exact safety, or pivot toward a
learned *proposal* task instead of forcing cost-route classification.

## v0.0.50

Source: docs/experiments/v0.0.50.md
SHA256: 40ec79bb188f5fd459fdff2714b571c2037848322affe8d0e7bb214d2c566065

### Final audit and decision

Contract seeds begin 3,700,000. First final audit uses 24 new examples
per degree with seeds `3,710,000 + 1000*degree + i`, 48 total. All graph
and system signatures must be distinct. Freeze generator, solver,
ordering methods, evaluator and thresholds before the final audit. On
every example, exact answers from natural, min-degree, min-fill and
optimal orders must equal the known ground truth and verify all original
equations; the teacher's count must equal exact ordered-solver count
and not exceed either greedy count. No unsafe accepted answer.

Define headroom as `(best_greedy_ops - optimum_ops) / best_greedy_ops`.
`ORDERING_HEADROOM_VISIBLE` requires at least 8/48 systems with headroom
>=10%, at least two in each degree arm, plus all validity/freshness
conditions. Otherwise `SPARSE_ORDER_SATURATED`, or `INVALID_FAMILY` on
contract failure. Even a visible gap is only permission to preregister
a subsequent small learned orderer against min-degree, min-fill and a
topology-aware deterministic rule on a separate holdout graph mechanism.
No neural performance claim or cross-domain transfer is made here.

### First and only complete audit

`docs/experiments/results/v050_first_audit.json` records 48 distinct
graphs/systems, all four orderings returning the same verified exact
answer. The globally optimal symbolic teacher matched its exact ordered
solver count and did not exceed either greedy baseline.

| Degree | Count | Mean best-greedy headroom | Maximum headroom | Cases >=10% | Median teacher search |
| --- | ---: | ---: | ---: | ---: | ---: |
| 3 | 24 | 0.188% | 4.52% | 0 | 159.9 ms |
| 4 | 24 | 1.191% | 7.21% | 0 | 175.5 ms |

The optimum search visited 4,096 states per system, the full subset
state space for 12 vertices. The teacher ordered solve itself took a
local median of 0.464 ms and 0.535 ms respectively. These timings are
one environment's diagnostics; comparing teacher search directly with
solver execution shows why the teacher cannot be deployed as-is.

Decision: **SPARSE_ORDER_SATURATED**. Min-degree/min-fill nearly
saturated the declared operation objective on these cycle-plus-matching
graphs, so a learned orderer trained on their optimum labels has no
pre-registered downstream value to recover. Do not train or promote a
model on this family. This is not a general impossibility result for
sparse elimination ordering or other graph distributions.

The next move should not be another version bump with a cosmetic random
generator. Require a grounded workload or a stronger, preregistered
adversarial structural family where exact verified solutions remain
available and cheap deterministic orderers leave material headroom.

## v0.0.51

Source: docs/experiments/v0.0.51.md
SHA256: e5e05973294a14d9dde722a16b23a693f075a4f395a7da26496a454ee0d03f5c

### First and only full audit decision

Require 28 distinct file SHA-256 values, exactly 11 sparse cases, valid
permutations and independent reference equality for every evaluated order.
Define arithmetic headroom `(best_baseline_ops - best_bounded_ops) /
best_baseline_ops`. `BOUNDED_OPPORTUNITY_VISIBLE` requires **at least four
of 11 sparse graphs** to show >=10% improvement. Otherwise report
`NO_BOUNDED_OPPORTUNITY`, or `INVALID_CORPUS` for a contract failure. This
threshold only allows a future, separately preregistered learner investigation
using actual solves and proposal/fallback work. It does not promote a model.
Also report all 28 rows, dense cases, fill, and measured search time.

### First complete audit (after preregistration commit `7f205cf`)

`docs/experiments/results/v051_first_audit.json` contains all 28 original
file hashes and every case. Independent bitset/set structural counters agreed
on all 18 evaluated orders per graph (two greedies and 16 restarts); all
permutations were valid. The 11 sparse graphs had mean arithmetic headroom
0.252%, median 0%, and **0/11** reached 10% (required: at least 4/11).
Only four sparse graphs improved at all: `11.graph` 0.679%, `13.graph`
0.730%, `31.graph` 0.562%, and `5.graph` 0.804%. The maximum across all
28 was 0.804%. Median two-greedy ordering search was 24.1 ms per graph;
the 16 additional restarts cost a further 196.4 ms median (local diagnostic,
not a portable timing claim). The per-instance best-of-two and best-of-18
are diagnostic comparisons; choosing the best order incurs the searches.

**Decision: NO_BOUNDED_OPPORTUNITY.** Do not train an orderer on these
near-greedy labels or describe them as a compute win. This is only a negative
result for this bounded 16-restart search and selected public subset; it
does not prove globally optimal orderings are close, nor that the remaining
PACE graphs or actual sparse matrix workloads lack headroom. No matrix was
solved in this iteration. The next credible experiment would need to replace
the objective/workload or provide an independently stronger search reference,
then measure end-to-end proposal, solve, and original-equation verification
against deployable deterministic ordering. Do not unlock the released hidden
graphs for training on the basis of this failed opportunity gate.

## v0.0.52

Source: docs/experiments/v0.0.52.md
SHA256: 62061ca20f07cca5518ec9ad90414c876b0cacfc22b08e6213b1e53f9cedfd51

### v0.0.52 — Real numerical matrix ordering audit

Status: **preregistered protocol; freeze before first full audit**. No learned
model or Structural Compression claim. This experiment checks whether a cheap
external structural ordering can beat mature solver-internal presolve/ordering
on an actual solve after paying its own discovery and verification costs.

### Fixed decision

`DETERMINISTIC_OPPORTUNITY_VISIBLE` requires RCM's *complete-path median*
to beat the per-instance strongest native median by at least **20% on at
least two of four matrices**. Otherwise report `NO_RCM_OPPORTUNITY` and stop
this candidate; do not train an orderer on four cases. Even a pass is only a
reason to test more matrices and deployable routing with its selection cost,
not evidence that a learner, Structural Compression or favorable scaling won.
No threshold, matrix or candidate change may be made after seeing rows from
the first full audit. Different workload questions need separate protocols.

### First full audit (after preregistration commit `b1b99f1`)

The complete 140 raw trials, hashes, version information, and all original
residual checks are in `docs/experiments/results/v052_first_audit.json`.
Four matrices × five policies × seven repetitions passed both original
equation and known-solution tolerances. Local SciPy was 1.17.0 and NumPy
2.3.5; timings are one-machine diagnostics in milliseconds:

| Matrix | n / nnz | COLAMD | best of three native | NATURAL | RCM | RCM vs best of three |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| bcsstk05 | 153 / 2,423 | 0.388 | 0.388 | 0.319 | 0.438 | −12.95% |
| bcsstk06 | 420 / 7,860 | 1.707 | 1.707 | 1.113 | 1.510 | +11.53% |
| bcsstk09 | 1,083 / 18,437 | 4.525 | 3.811 | 2.968 | 5.714 | −49.94% |
| bcsstk10 | 1,086 / 22,070 | 1.648 | 1.648 | 1.102 | 1.624 | +1.44% |

**Decision: `NO_RCM_OPPORTUNITY` (0/4 reached 20%, required ≥2/4).**
Stop this RCM candidate and do not train an orderer from these four cases.
The predeclared best-of-three native comparator deliberately excluded
`NATURAL` as a negative control. The data contradicted that expectation:
`NATURAL` was faster than every other policy on all four, despite sometimes
producing more L+U nonzeros. Reporting this observation does not revise the
fixed threshold or turn the best per-instance choice into a deployable policy.
The four related structural-engineering matrices and small local timing
differences do not establish a universal ordering rule. In this sample there
is no measured total-compute case for an external RCM stage; the next study
needs a genuinely different workload or computation bottleneck and its own
frozen protocol.

## v0.0.53

Source: docs/experiments/v0.0.53.md
SHA256: 854920e46c38389c78959cbf515afe466165d9c058d5c14820a0fe6fec61058b

### Decision before outcomes

`REUSE_OPPORTUNITY_VISIBLE` requires at least **three of four** large cases
(two bases × k=8,16) to beat fixed NATURAL by >=20% in full-path median
time. Otherwise `NO_REUSE_OPPORTUNITY`; do not add reuse to runtime. Even a
pass is only evidence for this exact repeated-block workload. Report k=1
overhead and all other cases, native diagnostic, verification errors and the
descriptive log-log slopes over five k values. No slope comparison alone
establishes a changed complexity class. A runtime promotion would require
a separate, representative workload and deployment cost gate.

### First full audit (after preregistration commit `c44a668`)

`docs/experiments/results/v053_first_audit.json` preserves all 210 timed
trials, verified errors, source hashes and environment. Every original
assembled equation and planted solution passed; each REUSE trial created
exactly one numerical factor for each k. Median complete-path times (ms):

| Base | k | NATURAL | COLAMD | REUSE | REUSE vs best native (diagnostic) |
| --- | ---: | ---: | ---: | ---: | ---: |
| bcsstk05 | 1 | 0.371 | 0.410 | 0.642 | −72.8% |
| bcsstk05 | 2 | 0.647 | 0.757 | 0.782 | −20.9% |
| bcsstk05 | 4 | 1.196 | 1.239 | 1.107 | +7.5% |
| bcsstk05 | 8 | 2.704 | 2.031 | 1.743 | +14.2% |
| bcsstk05 | 16 | 6.569 | 3.932 | 3.256 | +17.2% |
| bcsstk09 | 1 | 2.864 | 4.400 | 3.287 | −14.7% |
| bcsstk09 | 2 | 11.506 | 9.231 | 4.594 | +50.2% |
| bcsstk09 | 4 | 28.191 | 20.610 | 6.680 | +67.6% |
| bcsstk09 | 8 | 59.802 | 40.900 | 10.216 | +75.0% |
| bcsstk09 | 16 | 144.579 | 74.246 | 13.161 | +82.3% |

**Decision: `REUSE_OPPORTUNITY_VISIBLE`.** All 4/4 large cases met the
preregistered 20% reduction against *fixed NATURAL*. NATURAL was 11.0×
slower than REUSE for `bcsstk09`, k=16. The stricter per-instance best of
NATURAL and COLAMD is an unpaid diagnostic oracle: REUSE beat it by >=20%
in only 2/4 large cases, both `bcsstk09`. REUSE has material overhead at
k=1 and is worse for `bcsstk05` at k=2. The log-log fits over these five
sizes were respectively 1.035 and 0.584 (NATURAL, REUSE) for `bcsstk05`,
and 1.369 and 0.516 for `bcsstk09`; they are descriptive local slopes,
not asymptotic complexity claims.

**Mechanism boundary:** The speedup combines component splitting, exact
factorization reuse, favorable data layout, and native policy differences.
This experiment cannot attribute the gain to reuse alone. The next fixed
comparison must charge identical component detection and extraction while
factorizing each component separately without caching. No learned model or
general runtime route follows from this controlled repeated-copy result.

## v0.0.54

Source: docs/experiments/v0.0.54.md
SHA256: 0ff70c2f258c164e7fddb1da562ea19bdfe3f1d0232092f700051e0c86ae9992

### v0.0.54 — Factorization reuse mechanism ablation

Status: **preregistered before first full audit**. v0.0.53 established a
controlled full-path win over native SuperLU on exact repeated components,
but mixed component splitting with reuse. This ablation tests the incremental
reuse benefit against a stronger baseline that already splits the matrix.

Reuse exactly the v0.0.53 derived workload: original pinned NIST `bcsstk05`
and `bcsstk09`, each interleaved with k=1,2,4,8,16 exact copies, different
planted right-hand side per block. Two policies run in the same process:

- `SPLIT_NO_REUSE`: find connected components, extract each matrix, then
  factor each separately with SuperLU NATURAL and solve its own RHS.
- `EXACT_REUSE`: perform the same component detection and extraction, hash
  CSR shape, pointers, indices and values, confirm exact equality on hits,
  factor each distinct block once and solve every RHS.

The split baseline pays no hashing/equality work because it has no need for
it. Each complete-path time includes detection, extraction, relevant cache
work, all numerical factorizations and solves, reconstruction and the
original unpermuted assembled-equation verification. Common data generation
and original file I/O are excluded from both. Cache lifetime is one trial.
Require the split path to create k factors and the reuse path exactly one.
Report factor nonzeros and discovery time separately. This isolates numeric
factorization reuse beyond the decomposition both share; it does not prove
benefit on naturally occurring repeated components, arbitrary component
permutations, or other solver implementations.

Use one complete discarded warmup and seven fixed-seed shuffled repetitions
per policy on all ten cases, with `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`.
Abort on any original-equation backward error >1e-10, planted-solution
relative infinity error >1e-7, nonfinite value or wrong factor count.
Preserve all 140 timed trials and per-case medians.

`REUSE_MECHANISM_SUPPORTED` requires the reuse full-path median to beat
the split full-path median by **>=20% on at least three of four** k=8,16
cases. Otherwise report `REUSE_MECHANISM_NOT_SUPPORTED`. No threshold
changes or data edits after the first audit. A positive result supports
reuse for these exact replicated blocks only; it is not a deployment or
scaling-law claim. v0.0.53 native baselines remain contextual, not paired
measurements of this ablation.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python benchmark_v054.py \
  --data-root /path/to/bcsstruc1 --output docs/experiments/results/v054_first_audit.json
```

### First full audit (after preregistration commit `280f11e`)

The complete 140 timed trials, hashes, environment, factor counts and
original-equation checks are in
`docs/experiments/results/v054_first_audit.json`. Every case passed; split
created k factors per trial while reuse created one. Maximum backward error
was 2.91e-16, maximum planted-solution relative error was 1.98e-13.
Complete-path median times in milliseconds:

| Base | k | Split, no reuse | Exact reuse | Reuse reduction |
| --- | ---: | ---: | ---: | ---: |
| bcsstk05 | 1 | 0.511 | 0.553 | −8.2% |
| bcsstk05 | 2 | 0.851 | 0.791 | +7.1% |
| bcsstk05 | 4 | 1.699 | 1.003 | +41.0% |
| bcsstk05 | 8 | 2.896 | 1.650 | +43.0% |
| bcsstk05 | 16 | 5.427 | 2.590 | +52.3% |
| bcsstk09 | 1 | 3.956 | 4.123 | −4.2% |
| bcsstk09 | 2 | 7.786 | 5.053 | +35.1% |
| bcsstk09 | 4 | 14.736 | 6.177 | +58.1% |
| bcsstk09 | 8 | 30.134 | 8.837 | +70.7% |
| bcsstk09 | 16 | 58.425 | 14.957 | +74.4% |

**Decision: `REUSE_MECHANISM_SUPPORTED` (4/4 large cases met 20%).**
The shared decomposition does not account for this incremental difference:
the split baseline does not pay the reuse path's hash/equality overhead,
yet repeat factorization is costlier at large k. This is the controlled
mechanism that v0.0.53 could not isolate. Exact repeated submatrices with
the same local row ordering are deliberately constructed; no benefit has
been established for approximate, permuted, or naturally occurring repeats.
For k=1, reuse overhead dominates. A deployable runtime needs a cost gate
that chooses a cheap path before paying discovery costs, and a representative
external workload rather than a repeated-copy construction.

## v0.0.55

Source: docs/experiments/v0.0.55.md
SHA256: 1bf8e49a1ec35191b1b1def0753842dae2ea74f4d283feccab28d6a36f1c1926

### Corpus and mechanism

Use **all 13** K/stiffness matrices `bcsstk01`–`bcsstk13` from NIST's
Harwell–Boeing BCSSTRUC1 set, in name order. Original compressed Matrix
Market URL and SHA-256 for every file, and expected n=48–2003, are pinned
in `neumann1/natural_reuse_v055.py`. No rearrangement, replication, density
filter or file exclusion is allowed. The set is one related historical
structural-engineering collection, not a random cross-domain sample. Files
remain external and are never redistributed with the code.

The candidate `GATED_REUSE` scans connected components of the untouched
matrix. If one component exists, it immediately uses one full original
SuperLU NATURAL factorization; no component extraction or hashing. If there
are multiple components, it extracts all, hashes exact CSR shapes/pointers/
indices/values, checks exact equality on a matching digest, and **abstains
back to a full original NATURAL solve** if all components differ. Only if
at least two identical components exist does it factor each distinct block
once and solve the component RHSs, reconstructing the original answer.
The scanner, failed checks, factoring, RHS solves, reconstruction and
original-equation verifier are all within each timed trial. There is no
cross-trial cache, and a hash alone never authorizes reuse.

Compare fixed full-matrix SuperLU NATURAL and default COLAMD. NATURAL is a
deployable fixed baseline motivated by v0.0.52, but the per-instance faster
of NATURAL and COLAMD is a **diagnostic oracle**, not free routing. All
policies share external I/O, parsing and one planted RHS `b=A@sin(i+1)`;
these common inputs are excluded from timed paths. Record policy timing and
candidate gate timing separately, along with component and distinct-block
counts. Run one discarded full-path warmup and seven fixed-seed shuffled
repetitions on each of the 13 matrices (273 timed trials), single process,
`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`. Require backward error on the
original matrix <=1e-10 and planted-solution relative infinity error <=1e-7
for every trial; any failure invalidates the audit.

As a **descriptive, untimed** secondary corpus statistic, compare complete
canonical CSR matrices across the 13 filenames for exact equality. This
does not count as within-instance repeated components or measured stream
amortization; a subsequent preregistration would be required for either.

### Fixed decision

`NATURAL_REUSE_OPPORTUNITY_VISIBLE` requires at least **two of 13** original
matrices with identical nontrivial components, each with >=20% complete-path
median improvement versus even the diagnostic per-instance faster native
policy, and zero >10% slowdown versus fixed NATURAL on all matrices with
no repeats. Otherwise `NO_NATURAL_REUSE_OPPORTUNITY` and no generic reuse
runtime promotion. If this gate fails, stop whole-matrix component reuse
as a general strategy for this corpus; keep the v0.0.54 positive controlled
mechanism as a distinct observation. No new subset, threshold, or model
may be chosen after inspecting the first complete results.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python benchmark_v055.py \
  --data-root /path/to/bcsstruc1 --output docs/experiments/results/v055_first_audit.json
```

CI runs only a small exact reuse/abstention contract test; no external
dataset fetch is required.

### First full audit: INVALID_NUMERICAL_VERIFICATION

After the preregistration commit `5cd97d6`, the first run aborted at
`bcsstk13/COLAMD` during the discarded complete warmup; no 273-trial result
was generated. A separate postmortem diagnostic on that original matrix
measured backward error 3.48e-16 but planted-solution relative infinity
error 1.0526e-7, just above the frozen 1e-7 threshold. NATURAL measured
7.55e-8 forward error, and GATED_REUSE abstained on the single connected
component, following NATURAL. The numerical invalidity is not a reuse gate
failure or a pass; it cannot support either incidence conclusion. The abort
and diagnostic are preserved in `results/v055_invalid_audit.json`.

Do not relax v0.0.55's threshold or omit `bcsstk13` after seeing this row.
A separately versioned, openly corrective protocol may use a justified
forward-error threshold while preserving original-equation verification,
all 13 source files, and the original opportunity criterion. That next
audit is no longer a blind first look at the corpus.

## v0.0.56

Source: docs/experiments/v0.0.56.md
SHA256: 9189c2916fe9c42e75fc7027d90cf9fc82a5022b392de60aea5ae5104144eb15

### v0.0.56 — Corrective natural-matrix reuse audit

Status: **corrective preregistration before its first complete audit**.
v0.0.55 aborted at `bcsstk13/COLAMD` during warmup. The postmortem showed
an original-equation backward error 3.48e-16 and planted-solution error
1.0526e-7, above the earlier frozen 1e-7 forward threshold. This corpus
is no longer unseen: do not describe this as an independent holdout or
claim that the new tolerance was chosen blind to that failing result.

Keep **all** v0.0.55 data sources, SHA-256 values, original unmodified
matrices, exact component equality, scanner and fallback, NATURAL/COLAMD
comparators, one warmup plus seven fixed-seed shuffled repetitions,
cross-file descriptive comparison, complete-path timing, and original
equation verification unchanged. Only the common planted-solution relative
infinity error tolerance becomes **1e-6**. The original-equation backward
error remains **<=1e-10**. These explicit bounds apply equally to all
policies and 13 source matrices. Abort again on any violation; never drop a
case. Store `valid_v055_stricter_forward_gate` and `valid_v056` distinctly
in every trial for transparency. v0.0.55's invalid result remains recorded.

The v0.0.55 opportunity threshold is carried over unchanged:
`NATURAL_REUSE_OPPORTUNITY_VISIBLE` requires at least two of 13 original
matrices with repeated, exactly identical connected components, each with
>=20% full-path median improvement versus the diagnostic per-instance
faster native order, and no >10% slowdown versus fixed NATURAL on matrices
without repeats. Otherwise `NO_NATURAL_REUSE_OPPORTUNITY`; do not promote
whole-matrix exact-component reuse into a generic runtime route. A pass
would still apply only to this related historical engineering collection.
The secondary cross-file exact-duplicate statistic is untimed and cannot
substitute for a measured stream cache.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python benchmark_v056.py \
  --data-root /path/to/bcsstruc1 --output docs/experiments/results/v056_first_audit.json
```

CI performs a numerical-tolerance contract smoke without fetching data.

### First complete corrective audit (after preregistration commit `2ebe8d2`)

`results/v056_first_audit.json` preserves all 273 timed trials, original
file hashes, environments, residuals and candidate gate times. All trials
met backward error <=1e-10 and planted-solution relative infinity error
<=1e-6. The maximum measured backward error was 9.33e-16 and maximum
solution error 1.0526e-7; seven timed rows would have failed the older
v0.0.55 forward gate. This is a corrective result after a seen failure.

| Original matrix | Components / distinct | NATURAL ms | COLAMD ms | Gate ms | Gate vs best native |
| --- | ---: | ---: | ---: | ---: | ---: |
| bcsstk01 | 1 / 1 | 0.150 | 0.167 | 0.200 | −33.0% |
| bcsstk02 | 1 / 1 | 0.178 | 0.205 | 0.261 | −46.7% |
| bcsstk03 | 2 / 2 | 0.150 | 0.191 | 0.395 | −163.8% |
| bcsstk04 | 1 / 1 | 0.403 | 0.479 | 0.424 | −5.1% |
| bcsstk05 | 1 / 1 | 0.293 | 0.370 | 0.327 | −11.7% |
| bcsstk06 | 1 / 1 | 1.018 | 1.761 | 1.177 | −15.6% |
| bcsstk07 | 1 / 1 | 0.998 | 1.723 | 1.192 | −19.5% |
| bcsstk08 | 4 / 3 | 43.457 | 18.820 | 44.607 | −137.0% |
| bcsstk09 | 1 / 1 | 2.810 | 4.227 | 2.992 | −6.5% |
| bcsstk10 | 2 / 2 | 1.039 | 1.607 | 1.786 | −71.8% |
| bcsstk11 | 9 / 5 | 6.179 | 5.177 | 7.927 | −53.1% |
| bcsstk12 | 9 / 5 | 6.147 | 5.229 | 7.927 | −51.6% |
| bcsstk13 | 1 / 1 | 69.750 | 60.244 | 68.431 | −13.6% |

**Decision: `NO_NATURAL_REUSE_OPPORTUNITY`.** Three of 13 originals
(`bcsstk08`, `bcsstk11`, `bcsstk12`) contain at least one exactly identical
connected component, but **0/3** beat the per-instance best native median
by >=20% (required >=2). Among ten no-repeat matrices, **7/10** exceeded
the preregistered 10% slowdown limit versus fixed NATURAL (required zero).
Do not insert a global component scan into the default solve path on this
evidence. The v0.0.54 constructed-copy win remains a separate positive
mechanism, not a deployment justification.

The untimed, purely descriptive cross-file comparison found exact complete
matrix pairs `bcsstk06`/`bcsstk07` and `bcsstk11`/`bcsstk12`. This corpus
contains repeated artifacts across filenames; their presence does not
measure any real problem-stream frequency or the compute cost of discovering
and reusing them. The entire set is one small related historical engineering
collection. Millisecond medians on one machine are diagnostic; the large
negative percentage for small `bcsstk03` reflects a cheap native solve and
extra gate work, not a general scaling law.

## v0.0.57

Source: docs/experiments/v0.0.57.md
SHA256: f4719743b08b74e4120d95b5aa32e2c40c2b255ca1a9c9c72fccc0747d81e17b

## v0.0.58

Source: docs/experiments/v0.0.58.md
SHA256: 382f6b77b3c63eb531bc4c840d16f70aa1508c506b36d3ca335899efcaa22ef9

### Decision and next gate

**Do not use original-minus-trivial-presolve variable count as a headroom
estimate.** It substantially exaggerates the unexplored opportunity on the
one inspected native-presolver instance. A future numerical experiment must
start from an independently specified and checkable reduction witness,
measure the full path (discovery, checking, translation, solution,
reconstruction and original-model feasibility/objective), and compare to
HiGHS with its own presolve enabled. It must preserve the original integrality
and numerical acceptance contract. If the native presolver already captures
the witness, delete the extra path. Failure of one solver or one instance
does not imply a general impossibility result.

Reproduce the selection and optional native probe with:

```sh
python benchmark_v058.py --raw-zip /path/to/raw_data.zip \
  --benchmark-html /path/to/set_benchmark.html \
  --beasley-mps /path/to/beasleyC3.mps.gz \
  --output docs/experiments/results/v058_miplib_presolver_screen.json
```

`highspy==1.15.1` is needed only for the optional probe; it is not an
NEUMANN runtime dependency. `results/v058_miplib_presolver_screen.json`
records each of the 240 source feature counts, the shortlisting fields,
the three SHA-256 values and the native-presolve shape.

## v0.0.59

Source: docs/experiments/v0.0.59.md
SHA256: 554260d1c6eefb25b6e8c354f4c838364cc5281cc1542b4fb6903582e3d5464d

### First complete audit (after local freeze `22d745a`)

`results/v059_first_audit.json` contains seven alternating paired runs and
each original-model objective, bound/row violation, reduced shape and full
path duration. All 14 solutions were optimal for the **LP relaxation**,
with objective `6637.1880269437515` on the original objective and maximum
scaled original violation `5.56e-17`. No candidate fallback occurred.

| Path | Variables sent to HiGHS | Rows | Nonzeros | Median complete path |
| --- | ---: | ---: | ---: | ---: |
| Original LP + native presolve | 2,298 | 1,026 | 4,496 | 15.890 ms |
| Affine reduction + native presolve | 1,535 | 1,026 | 3,733 | 161.737 ms |

The candidate removed **763 variables and their 763 equalities**, but had
to rewrite **763 bound rows**; the constraint count did not fall. The paired
median candidate/native ratio was **10.179**, so the frozen decision is
`NO_LOCAL_ADVANTAGE`. A smaller solver input is not a smaller total compute
path on this instance. Do not deploy the Python reduction or train a model
to suggest the same eliminations.

A separate **post-result diagnostic**, outside the frozen seven-run audit,
split three candidate runs into reduction construction (142.4–145.3 ms),
HiGHS passModel/solve (11.1–11.3 ms) and reconstruction/original verification
(3.46–3.94 ms). This explains the local bottleneck but is not a new paired
performance result, proof of a solver-independent limit, or permission to
relabel an optimized rerun as the first audit. Even if a lower-level
implementation reduces construction cost, it must beat a strong native
presolver at the complete-path gate on separately chosen workloads.

```sh
python -m pip install highspy==1.15.1  # optional audit-only dependency
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python benchmark_v059.py \
  --mps /path/to/binkar10_1.mps.gz \
  --output docs/experiments/results/v059_first_audit.json
```

## v0.0.60

Source: docs/experiments/v0.0.60.md
SHA256: bb687b6d8f64cb4952ad2040168c4e4c05c5b68a455ef45aecd2721dc7f4b6e7

### First complete paired audit (after local freeze `15540e4`)

`results/v060_first_audit.json` preserves all three alternating pairs.
All six returned original-MIP feasible incumbents with scaled primal and
integrality violations at most `1.11e-15`; the candidate removed 763
continuous variables while retaining all 170 original integer variables.
No candidate fallback occurred. **But none of the six met the frozen
capability target.** Native HiGHS stopped at its requested 0.003 gap with
original objective `6747.310015` (three times); the candidate stopped at
the same gap threshold with original objective `6746.760023` (three times).
Both exceed the required 6742.21 ceiling.

The native/candidate complete-path medians were 7.893/10.028 seconds, a
candidate/native ratio of 1.271. This is a recorded diagnostic, **not a
valid fixed-capability cost ratio**, since the conjunction of objective
ceiling and dual-bound gap was never reached by either path. The evaluator's
frozen label `NO_LOCAL_MIP_ADVANTAGE` means the pass condition failed; it
must not be read as evidence that the candidate loses at the intended
capability. The earlier 20-second native exploratory objective was obtained
without the new 0.003 early-stop rule, making the chosen conjunction
internally mismatched. Do not silently edit this result or cherry-pick one
of the six runs.

Decision: **CAPABILITY_GATE_UNREACHED** (interpretation of the frozen
fail-to-pass label). A separately versioned and openly corrective protocol
is needed to assess iso-capability cost. Any threshold selected after these
observations must be identified as post-result calibration.

## v0.0.61

Source: docs/experiments/v0.0.61.md
SHA256: e24dc5a10a4505d9d43f3f4414df513140524ca40e84e71c127f81b2767631ec

### First corrective paired audit (after local freeze `808c7a9`)

`results/v061_first_corrective_audit.json` records three new alternating
pairs after one discarded warmup per arm. All six achieved the corrected
objective ceiling and 0.003 dual-bound gap within the 20-second total-path
budget. All six original-model primal and integrality checks were at most
`1.11e-15`, with no fallback. The old v0.0.60 objective ceiling remained
unreached in all six, as recorded separately in each row.

Native HiGHS returned original objective `6747.310015` and relative gap
`0.002995475` in each trial. The affine candidate returned `6746.760023`
and gap `0.002996930`, eliminating 763 continuous variables while retaining
the 170 integer variables. Its constraint count stayed 1,026: the removed
variables' bounds became rows. These are feasible bounded-gap incumbents,
not proofs of exact optimality.

Median complete-path times were **7.520 s native** and **9.871 s candidate**;
candidate/native = **1.313**. The candidate was about 31% slower despite
its slightly better incumbent objective. Decision:
`NO_CORRECTIVE_LOCAL_ADVANTAGE`. This ratio is an iso-capability comparison
under the *post-result-calibrated* threshold on one already inspected MIP,
not an independent holdout or a general result. Keep native HiGHS presolve
as the default; do not deploy this affine candidate for this workload.

The next structural-compression proposal should target an identified
native-presolve or solver-search bottleneck and be evaluated against native
presolve at a fresh, attainable, frozen capability gate. Variable count
reduction alone is not the relevant success criterion.

## v0.0.62

Source: docs/experiments/v0.0.62.md
SHA256: 6d28cddf3a5e76d292d59bb9071e6a757ec86f948a43d4926f16f4158e633fe1

## v0.0.63

Source: docs/experiments/v0.0.63.md
SHA256: 4a6cf13035881fd8ce2318f0dfddbcdb8931f8ebd6bfcd8a41b34a7e567bed6b

### Decision and next direct test

**INTERFACE_READY, CAPABILITY_NOT_TESTED.** The new workload gives a
problem-specified two-stage structure and an independent answer checker.
It does not yet establish a compression mechanism. The next direct test
must identify one exact scenario/recourse reduction with a checkable
sufficiency certificate, compare its whole path to native HiGHS presolve
and deterministic-equivalent MIP, and freeze a reachable objective-plus-gap
capability before timing. Existing decomposition algorithms (for example
classical Benders) are baselines or reusable components, not a NEUMANN
novelty claim. If the candidate cannot produce a certifiable feasible
original solution or the baseline cannot meet a shared gate within the
budget, report an unreached/invalid gate and do not claim a speed ratio.

The SEMI2/3/4 instances share one core and are not independent holdouts.
If a mechanism is selected using SEMI2, SEMI3/4 can test scenario-count
behavior but cannot establish cross-family generalization. A distinct
source family is required for that claim.

## v0.0.64

Source: docs/experiments/v0.0.64.md
SHA256: b8f88a12c1f1fea1e507a6e6142189982f8ee27aa41d273207e0750aade936ab

### First exploratory result

`results/v064_first_exploratory.json` preserves the first 20-second
candidate execution. The master completed six iterations, adding two
feasibility cuts per iteration. No original-feasible complete solution was
produced before the budget expired (19.838 seconds recorded within the
candidate function). The master objectives progressed 0, 3, 10, 11, 15,
19 but are **not** valid original objectives; recourse remained infeasible
at those master proposals. Its JSON reports `best_original_feasible: null`.

`results/v064_native_diagnostic.json` records a fresh native diagnostic
with a 19-second solver cap inside the 20-second total-path allowance.
At 19.089 seconds complete path, native returned a feasible original
objective `1711.3473359053723`, dual bound `1362.9874613768761`, gap
`0.2035588377`; independent original normalized primal error was
`1.98e-12`, integrality error zero and objective agreement `2.27e-13`.
Native timed out rather than proving exact optimality. The independent
verification succeeds despite timeout. The candidate yielded no accepted
answer, so **there is no candidate/native iso-capability time ratio**.

Decision: **NO_20S_DECOMPOSITION_OPPORTUNITY_ON_SEMI2** for this simple
from-scratch cut policy. Do not deploy, train a router for, or tune more
parameters on the same inspected instance. The safe default remains the
native path. This does not invalidate decomposition generally; a mature
solver, different initialization or stronger cuts could behave differently,
but those would need a separately frozen protocol and fresh data.

Reproduce the exploratory modes with the hash-pinned local source archive:

```sh
python benchmark_v064.py --archive /path/to/semi.ZIP --budget-s 20 \
  --mode candidate --output docs/experiments/results/v064_first_exploratory.json
python benchmark_v064.py --archive /path/to/semi.ZIP --budget-s 20 \
  --mode native --output docs/experiments/results/v064_native_diagnostic.json
```

Next direct core gate: choose a family and **one verified structure witness**
with a cheap enough construction path, establish a target both paths can
reach, then freeze the complete-path cost and accuracy protocol before the
paired runs. If no candidate can generate a valid answer within the budget,
record gate failure rather than a speed ratio. Avoid further SEMI2-only
post-result tuning. The current experiment tests a known decomposition
strategy, not a learned structure finder or cross-domain scaling law.

## v0.0.65

Source: docs/experiments/v0.0.65.md
SHA256: 7dd45d165928e401aefebbcd261cddde21eeb626ff86edc26fecec3a72d87863

## v0.0.66

Source: docs/experiments/v0.0.66.md
SHA256: d204dcd9e6901e3934cda6eb14d788b7066a6dcb683ef388ff987cba93bc9002

### Single hypothesis and gate

With injections and slack fixed, removing one active branch changes the
reduced DC bus matrix by one rank-one term. Reusing one factorization across
all connected single-branch outages should lower the total verified solve
time compared with rebuilding and factoring each outage independently.
Require the candidate median complete-path time to be at least **20% lower**
than the repeated SciPy SuperLU baseline over seven alternating trials,
with all connected outages satisfying the same original-outage relative
residual <=1e-10 and angle difference <=1e-8 radians. Otherwise record
`NO_LOCAL_REUSE_ADVANTAGE`. This is a mechanism gate only; the stronger
MATPOWER PTDF/LODF specialized method is established prior art and is not
timed in this study. Passing cannot establish NEUMANN novelty or supremacy
over that specialized comparator.

### First complete audit (after protocol commit `554d6d5`)

`results/v066_case118_first_audit.json` preserves all seven paired trial
times and numerical checks. Nine outages disconnect the graph and were
excluded from both arms' defined capability. For each of the remaining
177, both paths produced an angle vector satisfying the independently
scattered original branch-flow residual. The largest recorded normalized
residual was 7.46e-17; the maximum angle disagreement between paths was
2.78e-15 radians. The reuse path needed no fallback.

| Path | Seven complete-path times (ms) | Median (ms) |
| --- | --- | ---: |
| Repeated sparse factorization | 94.409, 100.777, 93.308, 90.368, 91.155, 97.376, 94.423 | 94.409 |
| One factorization plus rank-one reuse | 20.779, 20.624, 21.812, 25.473, 21.677, 20.742, 19.335 | 20.779 |

The candidate/native median ratio is **0.2201** (77.99% less measured
wall time, or 4.54 times faster against this particular generic baseline).
Decision: `LOCAL_REUSE_MECHANISM_SUPPORTED`, because the predeclared 20%
threshold and numerical gate were met. This measures a single standard DC
network and a full batch of contingencies with a common base case. It is
not a comparison with a mature LODF implementation, an AC safety proof,
an unseen network generalization or a NEUMANN-specific innovation. The
unavoidable input reading and 177 output verifications prevent arbitrary
sublinear total work under this explicit-output contract.

Reproduction requires the original externally obtained, hash-matching
MATPOWER case file and pinned single-thread execution:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python benchmark_v066.py \
  --case /path/to/case118.m \
  --output docs/experiments/results/v066_case118_first_audit.json
```

Next gate: a separately frozen comparison against MATPOWER-style PTDF/LODF
or another strong deployable contingency evaluator on untouched networks.
If that comparator absorbs the gain, delete the NEUMANN-specific runtime
path and retain only the general compute-aware routing lesson.

## v0.0.67

Source: docs/experiments/v0.0.67.md
SHA256: 1fb3102d87c0da95889c57c280f582466f328f60b6cea652e02d6444db26a80e

### Question, interface and strong comparator

For each network, query deterministic subsets of its connected single-line
outages of sizes `1, 8, 32, all`, selected by SHA-256-seeded pseudorandom
sampling from the sorted connected list. Return the full DC angle vector
for each outage, with slack angle zero, and check each result by an
independent scatter of the original surviving branch flows. Require
normalized original residual <=1e-10 and pairwise angle difference <=1e-8
radians. Islanding outages are counted, but not part of the defined
connected-outage capability. An unsafe denominator degrades to a direct
outage factorization and charges the fallback; a singular direct solve
invalidates the run.

Compare three fully charged paths:

1. `SCALAR`: one sparse base factorization and one triangular solve per
   queried outage, v0.0.66's classical rank-one update.
2. `BATCHED`: one sparse base factorization and a multiple-RHS solve for
   all queried incidence columns at once, followed by PTDF-style outage
   sensitivity updates. This is an independent Python implementation of a
   known specialized method, **not** a timing of MATPOWER's own code.
3. `ROUTER`: a constant-time rule choosing `SCALAR` or `BATCHED` from query
   count using only a threshold selected from the 118-bus development
   medians. Its dispatch overhead is charged. It may choose one fixed path
   everywhere if no crossover exists.

Each arm pays for graph bridge screening, incidence/base construction,
factorization, update preparation, all outputs and independent original
checks. Only external fetch, case syntax parsing and shared query selection
are excluded; charge their measured time separately for context. Report
time breakdown for topology/setup, sensitivity work, and verification.
Use one discarded complete warmup per mode and seven alternating trial
orders with single-thread BLAS. Source-file checks and selected query IDs
are preserved. No inference on AC power flow or security limits follows.

### Decision before observing timing

On case118, choose the threshold among `0, 1, 8, 32, all` that minimizes
the sum of its four medians; ties go to the simpler fixed path. This is
explicit nonblind policy development. Then freeze that threshold before
running *any* case300 timing. On case300, `ADAPTIVE_ROUTING_ADVANTAGE`
requires all numerical contracts, router's sum of four complete-path
medians <=0.90 times the better **fixed** mode's corresponding sum, and
no workload's router median >1.10 times the per-workload best of the two
fixed methods. Otherwise report `NO_ROUTING_ADVANTAGE`. The better fixed
mode selected from case300 outcomes is a conservative diagnostic comparator,
not a deployable free selector. Report also a per-workload oracle, its
selection cost excluded, only to show remaining headroom.

Even a pass would demonstrate a narrow compute-aware *policy* result,
not a new LODF algorithm, 10× result or general scaling law. A failure
means use the cheaper established method and delete an extra NEUMANN route.

## v0.0.68

Source: docs/experiments/v0.0.68.md
SHA256: 9673dacc55f8b6d972a15b4149a07d08693dd5fd3ff17aceca04c903bcb5f427

### Question and scope

Can the frozen 289-parameter learned affine dependency scorer beat both exact direct
solving and the frozen target-leaf heuristic in **total verified inference time**?
This is a gate for one synthetic exact-linear family, not a claim that NEUMANN 1
is already a general high-efficiency model. The follow-on program must also
test semantic parsing, other domains, memory, and matched neural baselines.

### Decision rule (registered before final measurement)

Capability: 32/32 exact original-system verification and ground-truth
agreement for each method; no unsafe accepted reduction.

Evidence for a *local learned compute advantage* requires learned total
median per-case time <= 0.8 × cheap time in **both** n=16 and n=32 for each
k, while never more than 1.1 × cheap on either n=4 or n=8 cell, and less
than direct time in both n=32 cells. Otherwise the learned branch fails this
gate and is not promoted on this family. This is not a statistical proof
of performance on unseen distributions; 4 cases per cell are exploratory.

The primary measurement is end-to-end wall time. Solver arithmetic counts
are a separate diagnostic, not added to model FLOPs or elapsed time as if
these were interchangeable units. A purported scaling advantage requires
separate larger-n replication with complete-path measurement.

## v0.0.69

Source: docs/experiments/v0.0.69.md
SHA256: 728850a3af3250703477e88f414bf73832d7c9ed06aa1e9cfde14c542da96657

### Question

The v0.0.68 direct comparator is an interpreted Fraction Gauss–Jordan solve.
Does the affine-linear family still offer a structural-compression opportunity
once direct execution is allowed a fast numerical proposal that must pass
exact verification on the **original** integer system?

This is a stronger direct-comparator audit, not a new NEUMANN model or a
claim about general-purpose reasoning.

### Decision

On all 32 cases exact verification must pass. Structural opportunity on
this family requires either learned or target-leaf total median latency
at most 0.8 × the **faster** of the two direct methods in both `n=32`
cells with no >1.1× regressions in the four `n≤8` cells. If not, label
`NO_AFFINE_FAMILY_COMPRESSION_OPPORTUNITY` for this studied n≤32 range.
Do not pursue a learned proposer on these scales after a negative result.

The tiny synthetic corpus cannot establish a population guarantee, a
cross-domain result, or a scaling law. A direct numerical method's success
here is a verifier-mediated *exact answer*, not a theorem that floating
point by itself is exact. More informative next candidates must specify
their cost regime and strong baseline before inspecting final outcomes.

### First audit — 2026-09-30

The protocol, baseline implementation, and fallback tests were committed at
`eb15360` before this audit. Reproduce with
`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python benchmark_v069.py`.
Python 3.12.14, NumPy 2.3.5, Linux x86_64; one BLAS/OMP thread.

All 32 cases gave identical exactly verified answers under each method.
The numeric direct route made zero fallbacks among 160 timed invocations.
The exact verifier is the authority; the zero-fallback result applies to
these planted-integer synthetic cases, not arbitrary rational systems.

| k | n | Exact direct ms | Verified numeric direct ms | Learned compression ms | Target-leaf ms |
|---:|---:|---:|---:|---:|---:|
| 2 | 4 | 0.058 | 0.057 | 0.647 | 0.347 |
| 2 | 8 | 0.170 | 0.081 | 2.536 | 1.845 |
| 2 | 16 | 0.821 | 0.184 | 14.997 | 16.199 |
| 2 | 32 | 4.180 | 0.334 | 115.625 | 127.037 |
| 4 | 4 | 0.081 | 0.051 | 0.685 | 0.182 |
| 4 | 8 | 0.204 | 0.077 | 2.375 | 2.801 |
| 4 | 16 | 0.920 | 0.188 | 15.739 | 18.882 |
| 4 | 32 | 3.866 | 0.313 | 110.161 | 156.925 |

Cell entries are median of four per-case medians over five interleaved
repetitions, not confidence bounds. At n=32, learned/full direct latency
ratio is ~346× (k=2) and ~352× (k=4); the target-leaf route is also
hundreds of times slower than verified direct. Faster direct numerical
execution erases the appearance of structural opportunity even more
decisively than the v0.0.68 interpreted exact comparator.
An immediate same-corpus rerun (not independent data) gave 0.321 vs
112.266 ms at k=2,n=32 and 0.318 vs 105.644 ms at k=4,n=32, again all
verified with zero numeric fallbacks and the same negative gate decision.

**Decision: `NO_AFFINE_FAMILY_COMPRESSION_OPPORTUNITY` for n≤32 under this
implementation and capability contract.** This is not evidence against
structural compression in general. Do not tune thresholds, batch checkers,
or introduce a larger model on these studied cells. Search next for a
predefined task where direct *verified* computation remains expensive after
the strongest applicable reuse, batching, and numerical shortcuts. If
none exists, the project should explicitly reject a general efficiency
claim instead of polishing a proxy win.

## v0.0.70

Source: docs/experiments/v0.0.70.md
SHA256: 0450c83cf12366609c2091a11f6359da4f4d8159f200226a67076dc8c783813e

### Question

Does exact structural compression have a positive *complete-cost* regime
in a combinatorial problem, unlike the cheap affine systems in v0.0.68–69?
Solve maximum independent set (MIS): maximize selected vertices subject
to selecting no endpoints of any original edge together.

Prior art: twin/data reductions and branch-and-reduce for MWIS are existing
methods. See Lamm et al., *Exactly Solving the Maximum Weight Independent
Set Problem on Large Real-World Graphs*, ALENEX 2019,
https://arxiv.org/abs/1810.10834. This test implements the elementary
equal-open-neighborhood quotient with weight equal to class cardinality.
It does not claim to reproduce all reductions or the paper's solver.
HiGHS options: https://ergo-code.github.io/HiGHS/stable/options/definitions/.
Reuse type: ideas only; no source code, weights, or datasets copied.

### Single hypothesis and pass rule

Hypothesis: exact twin compression creates a complete-cost opportunity.
Pass requires equal independently certified optimum on every invocation,
quotient/direct median total cost <=0.5 in **all four** multiplicity>1
cells, and <=1.2 in both multiplicity=1 control cells. Else FAIL, or
CAPABILITY_UNREACHED if a required answer/optimality certificate is absent.
The weaker descriptive 10x ratio is reported only if measured; it is not
the primary gate. Even a pass establishes only a classical constructed
combinatorial mechanism. Natural twin frequency, specialized graph solvers,
learned discovery, cross-domain generalization, memory and power remain open.

### First frozen audit and reporting correction — 2026-09-30

Preregistration and executable were committed as `6c64e31` before timing.
Command: `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python
benchmark_v070.py --output docs/experiments/results/v070_first_audit.json`.
Python 3.12.14, HiGHS 1.15.1, Linux x86_64, BLAS/OMP and solver threads=1.
The archive preserves all 108 timed trials and every failure.

| Base k | Multiplicity | Original n | Direct full median ms | Quotient full median ms | Certified direct / quotient timed calls | Valid speed factor |
|---:|---:|---:|---:|---:|---:|---:|
| 16 | 1 | 16 | 5.545 | 5.687 | 9 / 9 | 0.975× |
| 16 | 4 | 64 | 15.373 | 6.066 | 9 / 9 | 2.53× |
| 16 | 8 | 128 | 103.747 | 7.500 | 9 / 9 | 13.83× |
| 32 | 1 | 32 | 33.463 | 33.799 | 9 / 9 | 0.990× |
| 32 | 4 | 128 | 2048.964 | 35.634 | 9 / 9 | 57.50× |
| 32 | 8 | 256 | capability failure | 32.307 | 0 / 9 | not defined |

Reported medians are medians of 3 per-case medians, each from 3 timings.
The full raw-direct latency in the last cell was ~5.50s including model
build, but is **not** an observed latency to verified optimality. First
summary code incorrectly displayed a ratio using this censored denominator.
It was fixed after the audit, with a regression test, and
`v070_corrected_summary.json` was generated from the same archived rows
without any new timing. The first archive is deliberately not overwritten.
The corrected last-cell ratio is `null`. The final gate decision was
`CAPABILITY_UNREACHED` before and after this correction.

The first failure message was generic `HiGHS solve failed`. Error reporting
was improved; a **post-result diagnostic** on k=32,m=8,index=0 confirmed
`Time limit reached` and `HighsStatus.kWarning` under the unchanged 5s
solver budget. That diagnostic does not substitute for a new frozen audit.

Across all 18 cases, quotient execution certified all 54 timed calls;
direct certified 45/54. All completed paths matched the independent DP
optimum. Both no-expansion control cells were within the 20% no-regression
limit; all three expanded cells with completed direct answers met the 2×
cost gate. The fourth expanded cell is missing equal-capability cost
evidence, so **do not turn this into a global gate PASS**.

The positive *bounded mechanism* is that structural compression can remove
expensive combinatorial work even after full certificate and original
verification cost. At k=32,m=4 the quotient median components were ~1.18ms
planning, ~32.20ms MIP/model execution and ~2.40ms verification (component
medians need not sum to median total). This is qualitatively different from
the affine cases whose direct solver was already cheaper than discovery.

Remaining critical boundary: exact twin discovery is deterministic and the
reduction is classical. A specialized graph solver or the independent DP
already used for verification may be a substantially stronger executor than
MIP. Benchmark that before claiming a NEUMANN advantage. Also measure natural
problem frequencies and non-twin controls beyond constructed m=1. There is
no evidence yet that a learned component, cross-domain model, or model-level
scaling advantage is necessary or established.

## v0.0.71

Source: docs/experiments/v0.0.71.md
SHA256: 0c1abb82c93c378500c9c296790aaee5da0eb4a1bf2ef182a5d6a818dd4016ef

### v0.0.71 — Delete redundant MIP execution in the twin MIS mechanism

Status: first frozen audit completed; follow-up independent-checker holdout
preregistered in v0.0.72. This is a
classical constructed-graph implementation audit, not a learned-model claim.

### Question and alternatives

v0.0.70's independent integer DP already computed an exact optimum after
the MIP solve. Can the DP instead produce a checkable optimality proof and
remove the MIP? Compare full paths: (A) direct graph DP with proof,
(B) checked false-twin quotient DP with proof, (C) checked quotient HiGHS MIP
with the independent integer DP verifier from v0.0.70. A and B use the same
DP and proof checker; C retains its original verifier. This asymmetric
verifier cost reflects the DP's emitted proof and is explicitly reported.
HiGHS retains presolve, native symmetry detection, one thread, zero gap,
and 5s limit. Do not claim state-of-the-art MIS competitiveness.

### Gate and interpretation

Promote B over C only if all B and C calls certify and B median full cost
is at most 0.8 C in both k=32 expanded cells (m=4,8), with no >20%
regression in either k=16,m=1 or k=32,m=1 controls. But promote structural
compression itself only if B and A both certify all calls and B median
full cost is at most 0.8 A in both k=32 expanded cells. Otherwise the
MIP removal may pass but the compression advantage does not. If A cannot
certify under its fixed cap, record `DIRECT_CAPABILITY_UNREACHED` and no
same-capability compression claim for that cell. If B or C fails, record
`CAPABILITY_UNREACHED`. Any measured 10x advantage is descriptive only.
Report per-cell paired medians and failures rather than a single pooled win.

This tests one redundant computation on constructed inputs. It does not
show real-world twin frequency, strong specialized graph solver comparison,
learned structure discovery, model-level total compute, or scaling-law
improvement. No external code or dataset is reused.

### First frozen audit — 2026-09-30

Protocol and executable were committed at `da63885` before the first
holdout. Raw 162 timed rows, including every proof size and exact result,
are preserved in `results/v071_first_audit.json`. Python 3.12.14, HiGHS
1.15.1, Linux x86_64, BLAS/OMP and solver threads=1. All 162 calls
verified with matching optimum, so every displayed ratio has equal
certified capability. Median of three per-case medians (ms):

| k | m | Direct DP | Quotient DP | Quotient MIP | Direct DP / quotient DP |
|---:|---:|---:|---:|---:|---:|
| 16 | 1 | 0.338 | 0.414 | 6.582 | 0.82× |
| 16 | 4 | 4.903 | 0.729 | 6.965 | 6.72× |
| 16 | 8 | 16.539 | 1.594 | 7.662 | 10.38× |
| 32 | 1 | 4.601 | 4.950 | 34.085 | 0.93× |
| 32 | 4 | 115.391 | 6.094 | 42.694 | 18.93× |
| 32 | 8 | 633.184 | 10.940 | 35.679 | 57.88× |

The preregistered cost gates passed in the first audit. However, code
review after this result found that the DP proof checker reused the
executor's transition helper. Its Bellman-table audit and exhaustive
small-graph brute tests passed, but shared code poses a common-mode risk.
Also `reconstruct_ms` mistakenly included proof checking while `total_ms`
correctly included all work. Do not silently replace or relabel the first
archive. v0.0.72 separately preregisters a new-seed replication after
implementing the checker with original adjacency sets and correcting
component attribution. This is a bounded, classical constructed result;
no model-level claim follows from it.

## v0.0.72

Source: docs/experiments/v0.0.72.md
SHA256: 992351287c0af4d293b967d5f72af585f1f93953c71b5a64a3b8b39ec3064ddf

### v0.0.72 — Independent-checker replication of the DP compression audit

Status: preregistered holdout completed. The v0.0.71 first audit
is retained verbatim as `v071_first_audit.json`. Its DP proof checker reused
the executor's bitset transition helper and its component timing assigned
proof checking to reconstruction. Both issues were caught during code review
after seeing those results. The total times in that archive did include the
checker, but the common-mode correctness risk warrants a fresh holdout.

Use the same three full-path methods, capability contract, graph sizes,
multiplicities, three cases/cell, warmups, three rotating timed repetitions,
HiGHS options, 5s execution caps, 2m DP state cap, end-to-end accounting,
and two 0.8 cost gates as preregistered in v0.0.71. No adaptive threshold
changes. New base seeds are `720000+1000*k+i`, with shuffle seed+100*m.
The checker now uses original adjacency sets and a separate Bellman
transition implementation (not the executor's bitset transition helper).
Check every emitted state, all branch children, and the root, and reject
missing or forged states. The proof-check time is assigned to verification,
not reconstruction; total elapsed includes the same work. Keep raw failures
and reject speed ratios without equal certified capability.

Interpretation remains narrow: constructed false twins and a classical
specialized graph DP, not natural incidence or a learned NEUMANN model.
Any positive compression gate means this exact quotient helps this exact
DP on this artificial distribution, not that structural compression beats
the strongest unknown graph solver or improves general reasoning scaling.

### Frozen audit — 2026-09-30

Frozen code and rules were committed at `69ca1d1` before timing. Command:
`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python
benchmark_v071.py --seed-base 720000 --output
docs/experiments/results/v072_first_audit.json`.
Python 3.12.14, HiGHS 1.15.1, Linux x86_64. Raw archive retains all
162 timed calls. All paths certified all cases, with exactly matching
optima. Median of three per-case medians, end-to-end ms:

| k | m | Direct DP | Quotient DP | Quotient MIP | Direct DP / quotient DP | Quotient MIP / quotient DP |
|---:|---:|---:|---:|---:|---:|---:|
| 16 | 1 | 0.485 | 0.575 | 6.354 | 0.84× | 11.04× |
| 16 | 4 | 8.942 | 0.941 | 7.494 | 9.50× | 7.96× |
| 16 | 8 | 44.504 | 1.831 | 8.047 | 24.30× | 4.39× |
| 32 | 1 | 5.702 | 6.138 | 27.081 | 0.93× | 4.41× |
| 32 | 4 | 180.848 | 7.518 | 46.541 | 24.06× | 6.19× |
| 32 | 8 | 1085.497 | 11.353 | 40.903 | 95.62× | 3.60× |

Both preregistered cost gates **pass** on this fresh constructed holdout.
The k=32,m=8 DP proof median is 1,023,279 serialized bytes / 12,525
states directly versus 9,056 bytes / 609 states on the quotient. These
are serialized proof sizes, **not** measured process peak memory. At m=1
compression is unnecessary and costs 18.7% / 7.7% more than direct DP in
the two controls; a production router should skip this work when cheap
tests find no promising redundancy. The hard-cell gain includes proof
checking and original graph feasibility and certificate checks, not just
search. No training cost or learned component exists in this experiment.

The important deletion is MIP as an unnecessary executor for this family;
even the quotient MIP path paid for exact DP verification. The evidence
supports an efficient exact *classical* subroutine on this data generator.
It does not compare against state-of-the-art branch-and-reduce MIS software,
which may perform identical or stronger reductions internally. On natural
graphs with few exact twins, this quotient may be a net overhead. Do not
infer a NEUMANN model advantage or changed general scaling law.

## v0.0.73

Source: docs/experiments/v0.0.73.md
SHA256: da7f598b48a57ea3a1d15938fe8c1bda68d82742ab638eb520accc39496890fe

### v0.0.73 — Small non-planted graph sanity audit

Status: frozen audit completed; negative cost gate. This is a deliberately small incidence
and routing check, **not** a real-world distribution estimate or an advanced
MIS solver comparison.

### The one question

Does a cheap exact-twin test preserve complete verified cost on small
non-planted networks, while exploiting useful real redundancy when present?
No learned discovery, caching, or neural inference is involved. v0.0.72's
large synthetic speedups cannot be extrapolated from these four cases.

### Frozen first audit — 2026-09-30

Protocol, dataset and executable were committed as `b710840` before
timing. Command: `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python
benchmark_v073.py --output docs/experiments/results/v073_first_audit.json`.
Python 3.12.14, Linux x86_64. The archive retains all 60 timed rows; all
60 independently checked proof paths agreed on each graph's exact optimum.
No run was removed or censored. Median complete-path milliseconds:

| Graph | Vertices/edges | Retained | Direct DP | Always quotient | Routed DP | Routed/direct |
|---|---:|---:|---:|---:|---:|---:|
| Karate | 34/78 | 29 | 1.496 | 1.428 | 1.390 | 0.929 |
| Davis | 32/89 | 30 | 1.748 | 1.583 | 1.601 | 0.916 |
| Florentine | 15/20 | 15 | 0.264 | 0.338 | 0.292 | 1.103 |
| Les Misérables | 77/254 | 66 | 80.219 | 68.794 | 70.338 | 0.877 |

Pre-registered decision: **`NO_SMALL_GRAPH_ROUTING_ADVANTAGE`**. All
verification and no-regression conditions passed, but no twin-bearing
graph met the required routed/direct ratio <=0.8. Small exact twin classes
exist in three of the four graphs, but complete-cost gains here are below
the 20% threshold, and scanning has measurable overhead where no class
merges. The large speedups of the deliberately blown-up graph family in
v0.0.72 therefore do not establish an opportunity on these small graphs.
On Les Misérables the routed medians were ~25.70 ms for DP execution and
~41.78 ms for independently checked proof/edge/certificate verification
(component medians need not sum to the total median). This is required
verification work, not automatically removable waste. The proof size
fell from 120,926 to 101,474 serialized bytes, far less dramatic than
the planted-family reduction.

This is not evidence that all natural networks lack substantial twins or
that the technique is useless in production. Four heterogeneous examples
are far too few to estimate workload incidence. More importantly, the
direct comparator remains our proof-DP rather than mature graph software;
even a positive result would not establish superiority to graph-SOTA.
Do **not** tune a threshold or retrain a discoverer on these four graphs
and then call a rerun an independent holdout. Next opportunity search
must use new distributions and stronger executors, with training/inference
costs included if a learned component is proposed.

## v0.0.74

Source: docs/experiments/v0.0.74.md
SHA256: 06b96ea8e1582cda36097b0988b9a103863010044cfd0c373fd14de7825d18c4

### Question and scope

Does spending more on elimination-order planning create complete verified
cost savings that a future cheap learned planner could plausibly exploit?
Count independent sets exactly in binary factor graphs. This differs from
the previous maximum-independent-set optimization task. No planted twins,
compression labels, answer oracle, natural-language parsing, or cache is used.

Classical variable elimination and iterative stochastic min-fill are prior
art: [Kask et al., AAAI 2011](https://ojs.aaai.org/index.php/AAAI/article/view/7828).
Learned tree decomposition is directly prior art:
[Khakhulin et al., 2019](https://arxiv.org/abs/1910.08371).
Learned variable ordering is also an established direction (e.g. CSP search,
[Song et al.](https://arxiv.org/abs/1912.10762)); that is not the same as this
sum-product executor. NEUMANN's open question is complete iso-capability cost.
All implementation here is local; no external code/data/weights are imported.
The initial protocol citation incorrectly said 2010 for Kask et al.; the
publisher metadata confirms 2011. This correction changes no experiment rule.

### Result

The initial timed run accidentally overlapped the full test suite. Its
unaltered raw archive is `results/v074_contaminated_concurrent_tests.json`;
it is retained but its latency measurements are not admissible. This is an
execution-environment failure, not a timing-based outlier exclusion. Repeat
the exact frozen inputs, methods, and thresholds **after** tests terminate;
do not tune using the contaminated run.

The sequential audit is `results/v074_sequential_audit.json`. All 243 timed
calls independently verified exact counts; all methods/repetitions agreed
on all 27 graphs, with no failures. Best-eight/reference geometric mean
ratio is **1.7567936611**, and 0/27 graphs reached a 20% complete-cost gain.
The zero-planning diagnostic ratio is **0.8823730019**, with 2/27 reaching
20% gains. Both frozen cost screens fail. Decision:
`NO_LEARNED_PLANNER_HEADROOM_ON_FROZEN_DISTRIBUTION`.

Interpretation is restricted to the frozen n=16–32 distribution and the
eight candidate orders. The diagnostic is not a bound on all possible
orders or models. No learned model, real-world deployment, 10× result,
cross-domain reuse, or improved compute-scaling slope was demonstrated.
No training budget will be spent imitating this selected-order policy here.
Timing ratios are latency evidence, not FLOPs, joules, or dollar estimates.
Table/proof entry counts are not peak-process-memory measurements.

The next central task is a genuinely matched model-level comparison that
includes a same-budget direct program/IR predictor, not answer-only
classification. See `docs/research/core_question_gates.md`. This iteration
adds a bounded rejector, not a general high-efficiency model capability.

## v0.0.75

Source: docs/experiments/v0.0.75.md
SHA256: 12e888df5bc29b0d73f2429909d193622cf0f1e84cd699c6317112e1906c5b3b

### v0.0.75 — Proof-DP lifetime hygiene recovery audit

Status: frozen first audit completed; correctness/lifetime fix retained, first timing no-regression gate failed. Identical-tree replication is recorded separately.

### Pre-registered decision



### Frozen first audit and identical-tree replication — 2026-09-30

The first frozen CI timing audit ran in GitHub Actions workflow
`36668589533`, test job `109738512524`, on source tree
`a4aec3292adc8a670966518640065573898b5a99`. The complete workflow
succeeded, all correctness/lifetime contracts passed, and the timing summary
was:

| Group | Cases | Geometric-mean cycle-free / legacy | Maximum cell ratio | Frozen <=1.20 every-cell gate |
|---|---:|---:|---:|---:|
| independent / direct | 25 | 1.0018729269 | **1.2093935539** | **FAIL** |
| independent / quotient | 25 | 1.0014231565 | 1.1363508683 | PASS |
| proof / direct | 25 | 1.0032670750 | 1.1146335790 | PASS |
| proof / quotient | 25 | 0.9747170565 | 1.1331442845 | PASS |

The pre-registered first-audit decision is therefore
**`LIFETIME_FIX_CORRECT_BUT_PERF_REGRESSION`**. The threshold is not relaxed:
one independent/direct cell exceeded 1.20.

After v0.0.74 was merged to `main`, the same v0.0.75 content was replayed
on clean PR #81. Its head and the first audit have the **identical Git tree
SHA** `a4aec3292adc8a670966518640065573898b5a99`; only commit ancestry differs.
Workflow `36668960996`, test job `109739639628`, produced:

| Group | Cases | Geometric-mean cycle-free / legacy | Maximum cell ratio | Frozen <=1.20 every-cell gate |
|---|---:|---:|---:|---:|
| independent / direct | 25 | 0.9953617122 | 1.0673157375 | PASS |
| independent / quotient | 25 | 0.9931198848 | 1.0424183497 | PASS |
| proof / direct | 25 | 1.0002717495 | 1.0355050226 | PASS |
| proof / quotient | 25 | 0.9957611651 | 1.0558642702 | PASS |

That second run would independently classify as `LIFETIME_FIX_VALIDATED`,
but it **does not replace the first frozen result**. Selecting the later run
because it passes would be post-result selection. Instead it is retained as
an identical-tree replication showing that these short lifecycle timings have
enough run-to-run variance to move a maximum-cell statistic across the 1.20
boundary.

The clean PR #81 repository suite reported **302 passed, 3 skipped**, and
both CI jobs plus all smoke and fresh-venv interoperability steps succeeded.

### Engineering disposition versus research verdict

The mathematical recurrence, optimum, state counts, full proof records,
budget failures, and verifier behavior are unchanged. Weak-reference tests
show that per-call memo state is released without cyclic GC after both normal
and budget-exceeded exits.

Therefore the cycle-removal change is retained as an **engineering lifetime
hygiene fix**, not as a performance result. The research gate remains the
first-audit failure above. No speedup, lower-compute, memory-peak, or scaling
claim follows from v0.0.75.

## v0.0.76

Source: docs/experiments/v0.0.76.md
SHA256: 51617a959a7ac7ecfc042cef32b563b4f82ad464ffe0c7dc89b7dd87d4a23416

### Question

Does v0.0.31 distinguish structural compression from a same-budget direct
executable-program learner? Its structural model emits class 0 (LINEAR) or
abstains. The compiler subsequently extracts **all** coefficients, then the
solver executes the unchanged system. There is no structural compression in
this route. A direct tool-program learner can emit the atomic trusted program
`solve_controlled_linear(input)` or `abstain`, using the **same** checkpoint
and training labels with only an output-label rename.

Construct that missing admissible comparator rather than training another
model on an already cheap-deterministically-solvable grammar. This is a
bounded equivalence witness, not a new model performance experiment.

### Frozen contract audit

Use the existing 243 v0.0.31 final positives and their 243 documented
near-negatives. They are already opened, not a new blind holdout. Enumerate
all 82 valid model head outputs for each of the 486 texts: 39,852 paired
post-head checks. Feed the **same hypothetical head output** to both paths.
Do not claim these are the outputs of a trained model or 39,852 learned
inferences. Do not pass target solutions to either inference path.

Structural path: output 0 -> compiler -> solver -> existing verifier;
other valid outputs -> abstention.
Direct tool-program path: output 0 -> trusted atomic solver call; other
valid outputs -> explicit abstain opcode. The runtime uses the same compiler,
solver and verifier contract. No arbitrary Python evaluation or tool access.

Require identical status, answer and individual bookkeeping counters for
every paired case/head. On head 0, all 243 positives must solve and match
independently generated known solutions within the existing float tolerance;
all 243 near-negatives must fail closed. Invalid head IDs and opcodes must
be rejected. Record per-text SHA-256, paired-case count and mismatch count,
plus a SHA-256 digest of the full comparison stream. No timing samples exist
in this audit; do not fabricate a full-model timing or FLOPs result.

Pin/check v0.0.31's gate definition so the witness cannot silently drift from
the source it explains. Sharing the executor/verifier is intentional parity,
not independent verification of a natural-language semantic parser. The
generated known-solution check is benchmark-only and never inference input.

### Result

Frozen contract audit completed. Archive:
`results/v076_program_parity.json`. All **39,852** paired post-head checks
on **486** texts had **0** mismatches. All **243** positive head-0 programs
were verified and matched generated known solutions; all **243** negative
head-0 programs were compiler-rejected. Full comparison-stream SHA-256:
`2efd696b96533e3b22af56c5d520393f462aa9627de21a4b147040eb6b3352ef`.
Decision: `POST_HEAD_EQUIVALENCE_ONLY_NOT_Q4_PASS`.

Three focused standard-library contract tests passed. The restored local
runtime has no pytest or PyTorch installation, so no full local pytest run
or trained-model benchmark is claimed. Existing GitHub CI remains required
before merge. This audit uses no neural checkpoint at runtime: equality is
conditional on sharing the same head outputs, and checkpoint/label reuse
is the admissible comparator construction, not a newly measured model.

## v0.0.77

Source: docs/experiments/v0.0.77.md
SHA256: e2cf8620cb16454cd4eaf5cb31eb073146eabedf777c8d4880db8a274414588d

### One question

Is the existing v0.0.29–v0.0.31 generated 2x2 linear-system text task
admissible for Q4's matched **model-level** Direct-program versus
Structural-IR comparison, or does a zero-learned-parameter deterministic
path already saturate the task?

This version deliberately does **not** train a new model. Q4 must not be
tested on a benchmark whose semantic work is already solved by a cheap
hand-written compiler.

### Frozen candidate and fresh audit split

Candidate family: the existing controlled 2x2 integer linear-system grammar.

Fresh audit positives:

- 243 deterministic systems
- seed: 7602
- all 81 ordered integer solution pairs in [-4, 4]^2 represented
- text must be disjoint from every v0.0.29, v0.0.30 and v0.0.31 corpus

Each positive receives one paired near-negative using the already frozen
three-mode transformation cycle:

1. inequality,
2. nonlinear variable multiplication,
3. underspecified one-equation system.

No audit text is used for training because this version trains nothing.

### Pre-registered decision



### Consequence for the next experiment

If the existing task is rejected, the next Q4 benchmark must satisfy all of:

- raw input requires nontrivial learned semantic inference,
- strongest cheap deterministic processing does not already saturate it,
- Direct and Structural models receive the same raw input,
- Direct predicts an executable program/IR, not merely an answer class,
- both paths receive identical executor and original-task verifier authority,
- deterministic semantic work available to one path is also available to the
  other, or to neither,
- architecture/parameter/training-cardinality budgets are frozen before
  training,
- model inference, deterministic tooling, retries/fallback, memory, and
  training amortization are reported separately,
- final Q4 judgment uses matched independently verified capability and total
  compute.

### Frozen first-audit result

Canonical first CI evaluation:

- pull request: #82
- preregistered head: `ac9f85d2e6412eddebcedf45b15fda23d2507290`
- workflow run: `36671289602`
- test job: `109746626654`
- full repository suite in the same run: **305 passed, 3 skipped**
- sequence lane, wheel builds, and fresh-venv interoperability: **PASS**

All 486 required observations were present: 243 positives and 243 paired
near-negatives. The zero-learned-parameter path produced:

| Metric | First audit |
| --- | ---: |
| learned parameters | 0 |
| positive compile rate | 1.000 |
| positive verifier rate | 1.000 |
| positive hidden-solution equivalence rate | 1.000 |
| positive exact-verified rate | 1.000 |
| paired-negative fail-closed rate | 1.000 |
| median positive total path | 0.070342 ms |
| median negative rejection | 0.028774 ms |
| mean positive representation steps | 1 |
| mean positive solver steps | 9 |
| mean positive verification steps | 5 |
| mean negative representation steps | 1 |

Every preregistered rejection condition passed. The frozen decision is
therefore:

`REJECT_EXISTING_LINEAR_TASK_FOR_Q4`

The controlled 2x2 linear-text task is no longer admissible as the central
Q4 matched-model benchmark. A cheap deterministic compiler plus exact solver
already achieves complete verified capability on the fresh audit while
failing closed on all three paired unsupported forms. Training another model
on this task would not establish that learned structural discovery pays for
itself.

The diagnostic timing values above are not a Q4 speed result and have no
decision threshold.

## v0.0.78

Source: docs/experiments/v0.0.78.md
SHA256: 005fd2e0c511cd7ece33c46f5f7b4fb3a760397bdd47c6bb1efd4b64438410e3

### Single question

Does the authors' SVAMP arithmetic-program workload contain enough executable
computational redundancy to justify a learned Structural Compression experiment,
after granting Direct the same short trusted arithmetic-program interface?
This is task admission, not a model experiment. NL parsing difficulty and
execution compression are separate. Zero learning will occur unless this
screen admits this bounded *numeric execution compression* target.

### Degraded mode and next action

Malformed/unsupported or arithmetic budget failure -> UNKNOWN with recorded
reason; no successful summary ratio for rejected/unequal-capability rows.
If rejected, no model is trained on this numeric target. The next substantive
Q3/Q4 candidate must target residual *model discovery/planning* cost with an
actual same-budget executable Direct learner, shared optimized runtime,
no-compression ablation, held-out data and identical evaluation authority.
Do not select a weaker answer-only Direct route to manufacture a win.

### First local audit (preserved)

Preregistered local protocol commit: `0adac3a8b5b41ad4ec2449be112d1f1f151ddad5`.
Implementation fixed before the first measurement: `55aa55be612de73a0fe469f9d3205febc64326c5`.
Raw archive: `results/v078_first_audit.json`. No final rerun occurred.

- 1,000/1,000 reference equations supported; both implementations agreed exactly.
- 999/1,000 exact source-answer matches; one LABEL_DISAGREEMENT (`chal-680`):
  reference expression evaluates to 5 while the source Answer field is 1.
  This identifies an annotation disagreement, not which field matches the prose.
- Arithmetic-operation histogram: 0: 1 row; 1: 762 rows; 2: 237 rows.
- >=20% CSE gain: 0/1,000 rows; identical reference subtrees did not lower work.
- Nine repeats across both paths: all 18,000 expression-level runs verified.
- Per-row median, then corpus median: Direct 0.040462 ms, shared 0.041069 ms.
  These exclude raw-text semantic inference and are not model speed ratios.
- Exact-Body groups with distinct verified program signatures: 0 in this audit.
  This does not validate Body-only predictors or refute the paper's other tests.
- One row has a reference literal value not appearing in numeric observable tokens;
  six rows have duplicated literal values with unresolved role binding.
  Numeric-value occurrence is not semantic provenance or a sufficiency certificate.

All three numerical gate conditions failed. Frozen disposition:
`REJECT_SVAMP_NUMERIC_COMPRESSION_TARGET`.
No training, learned-parameter or model-level efficiency result follows.
Do not generalize the absence of CSE to every algebraic transformation, input
compression or latent semantic/reasoning compression. Keep this candidate out
of the runtime. A hand-written compiler for these reference expressions is
not a raw-natural-language solver.

## v0.0.79

Source: docs/experiments/v0.0.79.md
SHA256: 4240563b732de7996a0cfeecd1293a1888dc6619e1a7d0e23bc6619fc6575384

### One engineering hypothesis

The next real model comparison can retain every attempted operation and
enforce a complete matched comparator matrix without confusing equation
checking or source-label agreement with original-task verification.

Pass criterion: focused fault-injection contracts all pass, existing CI
remains successful, and earlier archived research measurements stay unchanged.
No latency improvement target is tested. Tests use fixtures, not trained models.

## v0.0.80

Source: docs/experiments/v0.0.80.md
SHA256: 53b5710debb513931e41f3e176fef6b79bb04a7f4562c3feb85c16ec6fcf976d

### One question and fixed admission rule

Can even a non-deployable, zero-model-cost choice among the declared plans
reduce complete verified query cost by >=20% against the strongest fixed
cheap Direct policy? If not, do not train a planner on this bounded family.

Require all timed calls to agree exactly with a separately executed SQLite
original query, mean per-case oracle total / strongest fixed Direct total
<=0.8, and >=4/12 cases with >=20% total savings. These thresholds are
engineering assumptions, not observed results or a power calculation.
Timeouts/mismatches are CAPABILITY_UNREACHED, never speedup evidence.
The oracle is selected after measurement and excludes learned planning;
it is a diagnostic lower-bound candidate, not deployable policy or Q3/Q4.

### Preserved first audit

Protocol commit: `3e6355126b94ff2c759b996853d9fef7406d6221`.
Timed implementation fixed at `45f250efc47dc332ad49cfa13a5697c3987e9d8b`.
Archive: `results/v080_first_audit.json`, SHA-256
`9a3027c935a815b0640a7f6e1c11794b745dad3d9f838f02f83d86be434f8601`.
The post-audit completeness validator was added afterwards; it does not change
the measurement methods, archive bytes or first summary. No final rerun occurred.

- 72 correctness warmups and 216 timed calls all matched SQLite exactly.
- Strongest fixed policy: grouped_counts, mean of 12 per-case total medians
  26.492110 ms; native 27.232105 ms. These include independent verification.
- Non-deployable zero-model choice across the six measured policies:
  0.966425 times the strongest fixed policy, only 3.3575% lower total cost.
- >=20% per-case wins: 3/12, below the required 4/12. Both cost gates failed.
- For grouped_counts, mean per-case checker median was 23.268744 ms versus
  3.209827 ms engine/control time and 26.492110 ms total: approximately
  87.83% of observed total was original-query recomputation. Component
  medians are separate descriptive summaries, not a universal lower bound.
- Mean database/setup time: 1253.568821 ms per case, recorded separately.
  Setup does not become a free cost in any future deployment/amortization claim.

Frozen decision: `REJECT_BOUNDED_RELATIONAL_PLANNER_TRAINING`.
No learner, frontier comparison, peak-memory, energy or Q3/Q4 result follows.
Do not generalize this rejection to larger/cyclic queries, alternative plans
outside the finite six-policy set, or all learned query optimization.

The multiplicity rewrite is exact classical algebra and available to Direct.
It is not evidence that learned compression is needed. Re-executing the
original problem dominated this particular verification contract; the next
task must have an independently checkable witness cheaper than independently
resolving the task. Such a contract must be fixed before new measurements,
remain equally available to Direct, and must not replace checks by a free
answer lookup or waive the original capability requirement. This is the
next design decision, rather than training a planner on the rejected cases.

## v0.0.81

Source: docs/experiments/v0.0.81.md
SHA256: 1bcca6ef9c20c1d2ce8e2e0939a3dbce7deaa2c880f852d7c34a76786ede2a98

### Next gate: v0.0.82

Before training any active-set or basis predictor, run a non-deployable
zero-model headroom screen:

1. freeze fresh standard-form LP instances and a strong HiGHS Direct path;
2. give a diagnostic oracle the optimal basis/support for free only to measure
   the maximum plausible structural-compression headroom;
3. reconstruct a full primal/dual certificate and run this exact original-LP
   verifier on every path;
4. charge basis-system solve, reconstruction, verification and all failures;
5. reject the target before training unless the oracle-compressed complete path
   clears the predeclared cost gate against Direct.

Even a positive v0.0.82 would establish only mechanism headroom.  Q3 would
still require learned discovery to beat cheap deterministic basis/active-set
tests, and Q4 would require a matched runnable Direct learner, a no-compression
ablation, equal training authority and complete cost accounting.

## v0.0.82

Source: docs/experiments/v0.0.82.md
SHA256: f9c8c1bba58a6f6c2e68952fe454c8f772ecac0e7e13258b63ab94b00e3ae732

### Research question

If the exact optimal LP basis/support were supplied for free, would enough
**complete verified compute headroom** remain to justify any later attempt to
discover that structure?

The screen compares:

1. a deliberately strong Direct diagnostic: the per-case fastest verified
   median among SciPy/HiGHS `highs`, `highs-ds`, and `highs-ipm`;
2. a non-deployable oracle route that receives the exact optimal basis for free,
   factors only that basis, reconstructs the full primal/dual witness, and then
   pays the identical v0.0.81 original-LP verifier.

Both sides receive the same raw observable `A,b,c`. Only the oracle diagnostic
receives the hidden basis indices. The best-of-three Direct choice is selected
after measurement with zero routing cost, so it is also non-deployable and
intentionally favors the Direct lower bound.

A positive result is **not** Q3 or Q4 and is not evidence that a learned basis
predictor is useful. It only says that the residual structural decision may be
worth studying.

### Next step if admitted

Do **not** immediately train a neural basis predictor.

First compare against cheap deterministic and classical structure discovery:

- obvious active/nonbasic tests available from raw observables;
- presolve and scaling information available to Direct under equal authority;
- basis/warm-start heuristics and applicable classical optimization methods;
- any strong prior work that predicts active sets or LP bases.

Only residual headroom that survives those baselines can motivate Q3 learned
discovery. Q4 would still require a matched runnable Direct learner,
NEUMANN-without-compression ablation, equal training budget, fresh held-out
structures, full failure/fallback accounting and training amortization.

### First retained audit result

The first retained audit was executed after the protocol implementation passed
the repository CI. The audited Git SHA was
`710cb4e908aae397c85d461953cd0cd36a336a07`; that commit differs from the
canonical v0.0.82 main merge only by the one-shot audit workflow. The preserved
result SHA-256 is
`f1af7c37f3042dad60c43b0c4a80fe1ab95f011710f26a6abe499458d5589847`.

All frozen capability requirements were reached. The retained result is:

- decision: `ADMIT_BASIS_DISCOVERY_SEARCH_NOT_MODEL_TRAINING`;
- expanded-case geometric mean
  `oracle complete median / best-Direct complete median = 0.0087784284`;
- expanded cases with at least 20% complete-cost reduction: `12/12`;
- matched control/expanded pairs with structural scaling amplification
  `>= 2.0`: `12/12`;
- observed scaling amplification range: approximately `3.86x` to `13.75x`;
- Q3: `OPEN`;
- Q4: `OPEN`.

The reciprocal of the aggregate expanded ratio is approximately `113.9x`,
but this is **not a deployable NEUMANN speedup**. The diagnostic receives the
exact optimal basis at zero discovery cost on an author-generated constructed
family. It establishes only that enough residual mechanism headroom survives
the original-LP verifier to justify testing whether the basis/support can be
found cheaply from admissible observables.

The matched `n=m` controls matter: the oracle route is already faster than a
generic LP solve with no width compression. Therefore the admission result is
not based on the raw oracle/HiGHS gap alone; every one of the 12 matched pairs
also cleared the frozen width-scaling-amplification gate.

Preserved evidence:

- `docs/experiments/results/v082_first_audit.json`
- `docs/experiments/results/v082_first_audit_meta.json`

The first retained audit is not rerun by ordinary CI.

### Next gate

Proceed to a **deterministic/classical basis-discovery shortcut screen before
any model training**. The next stage must ask whether cheap observable-only
rules, solver-native information available under equal authority, or classical
basis/warm-start heuristics consume the oracle headroom. Only residual value
that survives those baselines can justify a learned discovery experiment for
Q3. Q4 remains downstream of an actual matched runnable Direct learner,
NEUMANN no-compression ablation, equal training authority, fresh held-out
structures, and complete failure/fallback/training-amortization accounting.

## v0.0.83

Source: docs/experiments/v0.0.83.md
SHA256: ad8488905321e54b79779f54c72aec949d457c86f3e1beca6517d7a8422bf409

### Hypothesis and design disclosure

Reading the opened v082 generator suggests an observable shortcut: orthogonal
basis columns have equal norm at condition 1; at condition 1000 basis columns
are often shorter than Gaussian nonbasic columns. This is an analytical
generator-aware hypothesis, not blind discovery or a representative LP claim.
We test whether two cheap deterministic proposals consume that family's
oracle headroom, before considering learning.

### Frozen decisions

All 48 cases need one native method and the deterministic route to pass
warmup plus every timed repetition; otherwise CAPABILITY_UNREACHED.
For each form, evaluate 12 expanded-case complete-cost ratios to best native
Direct, plus count cases with no fallback in warmup or any repeat.

Raw shortcut gate: geometric mean ratio <=0.50, at least 8/12 ratios <=0.80,
and at least 8/12 expanded cases never requiring fallback.
If it passes: CHEAP_DISCOVERY_CONSUMES_RAW_FAMILY_HEADROOM; do not train a
model merely to replace these rules. Otherwise: RESIDUAL_HEADROOM_UNRESOLVED,
which still does not authorize neural training: two rules are not exhaustive.
Report the identical normalized gate separately as a sensitivity test. A raw
pass with normalized failure marks normalization-sensitive generator structure,
not a learned opportunity or proof every deterministic method fails.
These are engineering thresholds, not power calculations.

Keep Q3/Q4 OPEN regardless of outcome. A future learned experiment needs
stronger classical comparisons, residual value, matched executable Direct,
no-compression ablation, explicit budgets and disjoint final structures.

Pre-audit fixture correction: SciPy 1.17.1 warns that the earlier v082
string `parallel="off"` is invalid and falls back to its default. v083 uses
the supported Boolean `False` on native and fallback calls, with threads=1.
The first v082 archive/code is unchanged. This correction was made before
any v083 timing, not after inspecting performance.

### First retained audit (no timing rerun)

The protocol was committed locally at `5542162`; the pre-audit implementation
tree was `606fbd3569dde29295cd1935a253d9fa33547297`, published in PR #92 at
`4b866df46ece287663dd3eef64c4fb13a190a873`. Python was 3.11.16 with the
pinned packages above. All 576 timed and 192 warmup records passed the original
numerical certificate. No learned model was trained.

| Expanded form (12 cases) | Geomean complete-cost/native ratio | >=20% wins | No fallback | Gate |
| --- | ---: | ---: | ---: | --- |
| Raw | 0.018227686347123885 | 11/12 | 11/12 | Pass |
| Column-normalized | 1.1156167302934963 | 0/12 | 0/12 | Fail |

Decision: `CHEAP_DISCOVERY_CONSUMES_RAW_FAMILY_HEADROOM`;
`normalization_sensitive=true`. The sole raw expanded fallback was
`m32_c1000_r0_w16_raw` (ratio 1.0337876730298092).
Cheap observable norm structure explains much of this planted family's raw
headroom. Erasing this cue removes this rule's benefit; it does not establish
that every classical method fails. Keep Q3/Q4 OPEN and do not train a model
to imitate this shortcut. A future gate needs stronger norm-invariant classical
comparisons and residual value on disjoint structures.

Archive: `results/v083_first_audit.json.gz` (gzip is storage only).
Decompressed first JSON SHA256:
`a9693593bf1869b6148edf1f06e1ec5e7c5d641da439b592735b90980d42b09f`.
Compressed SHA256:
`f002c016873ca11f25830df7d34be48b90aae483bfca736c35e87947d6e6c54a`.
The original bytes and observations were not edited after inspection.

### Validation and limitations found after the audit

Source regeneration and archive validation passed in the original runtime.
A later generation-only check (no timing audit) under CI's
`OPENBLAS_CORETYPE=HASWELL` reproduced none of the 48 byte-level input hashes.
Package pins and seeds alone are therefore insufficient for byte-identical
cross-BLAS reconstruction. A post-audit runtime diagnostic reported SkylakeX
dispatch, NumPy OpenBLAS 0.3.30 and SciPy OpenBLAS 0.3.31.188.0, one thread;
this diagnostic was not part of the frozen measurement metadata.
CI checks the first JSON checksum, metadata, coverage, complete-cost accounting,
stored certificate acceptance and recomputed summary with source regeneration
disabled. It does not independently re-solve/re-verify archived witnesses or
claim input-byte reproduction across CPU dispatches. The default validator
still regenerates sources. Future protocols should pin dispatch and retain
input arrays for portable reproduction.

The first PR CI also exposed HiGHS process-global thread-scheduler interference:
a prior default-thread solve makes a later `threads=1` solve return status 4.
This was reproduced separately after the audit. The native-fallback integration
fixture now runs in a fresh subprocess, matching the audit process boundary.
The measured policy and first audit were not changed or rerun to repair CI.

## v0.0.84

Source: docs/experiments/v0.0.84.md
SHA256: fc6d66dd419e6692c8aa71bcda68f07591f53ea45f1ad83d55449888836128a3

### Hypothesis and limits

v083's raw column-norm shortcut vanished under column normalization. A richer
classical portfolio using normalized coefficients, cost residuals, primal
scores and rank-revealing QR may recover verified basis candidates cheaply.
This is an opened, generator-aware development screen, not blind/natural LP
evidence or an exhaustive test of classical methods. These are ordinary
linear-algebra heuristics, not learned NEUMANN contributions.

### Capability and frozen decisions

Both forms must have an eligible native and portfolio path on all cases
(warmup and all repeats), else CAPABILITY_UNREACHED. A failure of the v083
control is retained but does not hide the new route's capability.
For each form use its 12 expanded cases. Require geometric mean complete-cost
ratio ≤0.50, at least 8/12 ratios ≤0.80, and at least 8/12 never falling back.
Both forms must pass for CLASSICAL_PORTFOLIO_CONSUMES_MATCHED_HEADROOM.
Raw-only pass: RAW_ONLY_CLASSICAL_GAIN. Otherwise:
RESIDUAL_HEADROOM_UNRESOLVED_NOT_LEARNING_ADMISSION.
No outcome authorizes neural training or closes Q3/Q4. These engineering
thresholds are not confidence bounds or statistical power calculations.

### First retained audit — 2026-10-01 (Asia/Seoul)

Local protocol commit `9e2cb50c46da6784fb1ffc7118d56d6d1134f0f8` preceded
all v084 generated-case solves. Pre-audit implementation was published in
PR #93 at `a1efa72a2fa7590b49174de2a3f9326d8c633ef9`, tree
`ae17ce6bf65fe2cb17a0d05d030fd40d04f79a60`. Before measurement, pinned Python
3.11.16 fixture tests passed 12/12 and full local regression passed 372 tests
(3 skipped). No learned model was trained; no timing audit was repeated.

All 720 timed and 240 warmup observations passed original-LP numerical
verification. The portable witness replay also passed without optimizer calls
or regenerated inputs. The expanded results are:

| Form (12 expanded cases) | Portfolio/native geomean ratio | >=20% wins | No fallback | Gate |
| --- | ---: | ---: | ---: | --- |
| Raw | 1.3553861823376552 | 0/12 | 0/12 | Fail |
| Column-normalized | 1.3559506382970672 | 0/12 | 0/12 | Fail |

Decision: `RESIDUAL_HEADROOM_UNRESOLVED_NOT_LEARNING_ADMISSION`.
On these expanded cases the geometric-mean complete latency is about 35.5%
higher than the post-hoc best eligible native. Every expanded portfolio path
falls back; the n=m controls do not require fallback. These are descriptive
case-median ratios, not an arithmetic-average speedup or significance claim.

The norm control retains the earlier pattern on fresh seeds: raw expanded
geomean ratio 0.020192106031887903 (12/12 >=20% wins), normalized 1.156154900615199
(0/12 wins). This is only a sensitivity control and not neural evidence.
Do not tune and re-audit these opened final records or interpret failed
residual/QR heuristics as proof that all classical LP discovery fails.
Keep native execution as default on the normalized family. Q3/Q4 stay OPEN;
no learned training is admitted. Next requires a justified different classical
mechanism or a principled new family, not retrospective threshold adjustment.

## v0.0.85

Source: docs/experiments/v0.0.85.md
SHA256: d45f57de6b58afaa7825b02ce3108a1f99618c56c8cec97723e1152ca0cdc8c9

### Question and advance/stop rule

Can a basis-only NEUMANN output establish a structural-compression advantage
over an equal-authority Direct **executable-program** learner? Basis prediction
is known prior art (Fan et al., ICML 2023;
https://proceedings.mlr.press/v202/fan23d.html). Algorithmic novelty is not
required, but comparator authority cannot be withheld to create a win.

Construct a Direct program interpretation of the *same* supplied head output.
Both receive A,b,c and the same candidate indices, share one checked basis
executor, original numerical verifier and paid native fallback. A model head
is supplied for this diagnostic, not predicted or trained. This is a
downstream expressiveness comparison, not a new benchmark-quality claim.

If every tested outcome, primal/dual witness and execution/verification call
ledger agrees, record `LP_BASIS_ONLY_Q4_ATTRIBUTION_REJECTED`: merely comparing
basis prediction plus LU to a cold full solver cannot attribute a Q4 win to
NEUMANN. The Direct comparator must be allowed the identical checked basis
operation. If any disagreement appears, `PARITY_BUG_OR_CONTRACT_MISMATCH`;
repair the interface before relying on it. Do not declare a global Q4 failure
or any Q3 result. No performance ratio is a decision input.

### Constructive interpretation and scope

NEUMANN head: `{basis: [m distinct column indices]}`.
Direct program: `{op: "solve_basis_checked", basis: same indices}`.
The operation solves original A[:,basis] for primal/dual, reconstructs all
coordinates and verifies original A,b,c, exactly as the NEUMANN adapter.
An explicit ABSTAIN head maps to the same native fallback operation. Invalid
syntax, duplicate/out-of-range/noninteger indices, singular or rejected basis
produce the same rejection and, if enabled, the same charged fallback.
No Python eval/exec, oracle indices, gold answers or inference metadata enter
either executor. These are closed typed operations, not unrestricted programs.

Because the valid-output conversion preserves the basis arguments and calls
the same runtime, semantic equality follows by construction for the declared
operation contract. Finite checks falsify implementation mistakes, not prove
that every floating-point platform has identical runtime or costs.
Both adapters may have different real overhead; no latency win/loss follows
from equality of calls. Sharing the execution backend is required equal
authority, not an independent validation implementation.

This does NOT show that different learned architectures, curricula, routing,
retrieval or cross-domain systems cannot differ in total efficiency. It shows
that renaming this particular head as a minimal IR is not a sufficient Q4
experimental distinction. Compression still genuinely reduces the basis
solve width; Direct's access to the same reduction removes the attribution.

### Q3/Q4 next experiment requirements

Q3 remains OPEN: no learned prediction or inference costs are tested here.
Q4 remains OPEN at the system level; this basis-only attribution route is
stopped, not the broader LP research line. Do not spend another training
budget only to recreate these two adapter labels.
The next real model experiment must freeze a difference in actual learned
computation or paid search that a Direct executable learner cannot reproduce
merely by relabeling the same checkpoint output. Freeze runnable equal-budget
learners, identical intermediate supervision/tool access, no-compression
ablation, independent final structure/surface splits, full verifier/fallback
costs and training amortization before fitting. A failed heuristic is not
learning admission. Native warm starts and published learned-basis baselines
remain mandatory if LP is revisited; do not compare only to cold SciPy wrappers.

### First completed result

The immutable v084 source selected 210 unique case/basis pairs across all
48 inputs. Both adapters were executed once per pair, with native fallback
disabled, after the metadata fix was committed locally. All 210/210 stable
outcomes, full primal/dual witnesses and call ledgers agreed exactly.
Each adapter accepted 36 and rejected 174; each made 210 basis calls,
210 original-certificate calls and zero native calls. Every paired witness
is retained, including rejected ones. Decision:
`LP_BASIS_ONLY_Q4_ATTRIBUTION_REJECTED`.

The completed gzip is 454,037 bytes, SHA-256
`8347302cd83c2e2de36642a7a539fcd87f2333597166c728e152f9026fba0fec`;
its JSON is 3,692,291 bytes, SHA-256
`ba29b88cb62dae39b6282d06636fc7ac3903d50c8120915a61c5080a3675e86e`.
`results/v085_diagnostic.manifest.json` links both retained attempts and the
exact source identity. `load_source` checks the preregistered v084 JSON hash;
`load_diagnostic` checks completed storage/JSON integrity before loading.

Runtime: Python 3.11.16, NumPy 2.4.6, SciPy 1.17.1, threadpoolctl 3.7.0;
actual Haswell BLAS pools and OpenMP pool were all single-threaded. Adapter
latency was not measured. Call counts are separate work indicators, not
FLOPs, total compute or proof of equal overhead. Equality follows by sharing
the declared checked basis executor; this is not independent algorithm code.

Focused fixtures pass 15 tests, including fresh-process native fallback,
singular/nonoptimal bases, strict syntax, counted failed verifier calls,
negative controls, runtime preflight and preservation of failed attempts.
CI only replays the retained comparison through the original verifier; it
never re-solves these 210 pairs or regenerates the source. Run safe replay:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OPENBLAS_CORETYPE=HASWELL \
  python -m pytest tests/test_lp_program_parity_v085.py -q
```

The explicit `benchmark_v085.py NEW.json.gz` is a new, reserved untimed solve
diagnostic, not archive replay; do not run it to replace either retained file.
Q3 remains OPEN because no learned discovery was tested. Q4 remains OPEN
because no matched trained-model/full-cost experiment was performed. Stop
this basis-only attribution route, not the broader compression hypothesis.

## v0.0.86

Source: docs/experiments/v0.0.86.md
SHA256: 9b4618cf791dac3ad96f263f15c0fcf504340338cd45bd9152b2a3b3f41c1bef

### Hypothesis and one acceptance criterion

An equal-authority Direct comparator can supply a candidate basis to native
HiGHS simplex and let it repair an incorrect/singular proposal, rather than
discard it and restart through a cold SciPy wrapper. The criterion is original
primal/dual certificate acceptance on cold, optimal, nonoptimal and singular
basis fixtures, and fail-closed handling of malformed inputs, denied
certificates, infeasibility, unboundedness and budget expiry. This is a
correctness hypothesis, not a claim that warm starts are faster.

### Next substantive gate

This fills a mandatory comparator gap identified in v085. It does not select
or admit a new learned LP task. Before fitting any model, freeze actual
runnable distinct learners/inductive biases, equal intermediate supervision
and tools, a no-compression ablation, a residual-headroom screen against
native warm starts and applicable published learned-basis baselines, sealed
structure/surface final sets and full inference/training amortization.
Normalized v084 inputs remain opened development data and native remains the
default. Do not infer learning value from a failed heuristic or correctness
fixtures. Q3/Q4 remain OPEN.

## v0.0.87

Source: docs/experiments/v0.0.87.md
SHA256: b5f270cc3848699427e3e0b5f70ff8c0fe1188648d3a1b4f76ac897c71e10229

### Retained sole corrective result

All 864 observations (648 timed, 216 warmup) passed original-LP certificate
verification. Solver/model-free archive replay passed after bytes were saved.
On 12 expanded cases, perfect-compact/fastest-real-classical complete-cost
geomean is **0.31189160125943305**, with 12/12 >=20% wins and 0/12 cases exactly
solved by the three registered cheap proposals across every repeat. Actual
compact/full16 forward-time geomean is **0.7374609638851579**; compact is slower
in one cell, so no every-cell reduction is claimed. Parameter counts: compact16
5,156; full16 5,156; point16 611; full128 299,268.

Decision: `ADMIT_BOUNDED_MODEL_FITTING_NOT_Q3_Q4_PASS`. This admits the registered
candidate-specific fitting budget, not general learned-LP superiority. The
predictions were discarded and a certified basis was injected; neither learned
accuracy nor Q3/Q4 has been evaluated. The first confounded archive is missing,
not silently deleted or reconstructed; its notice accompanies the manifest.
The correction archive was published at `d5811a900e7022144ea2ccfa7cae5a1ee869ab74`
before further model work. No favorable timing rerun or threshold change occurred.

Next: separately freeze fresh training data, equal supervision/tool authority,
actual runnable learned Direct comparisons, sealed final size/surface shifts,
training costs/amortization, and original-verification/fallback charges before
any fitting. The implemented wider GNN is a budget-adapted candidate, not a
validated published-method reproduction; global Q3/Q4 remain OPEN.

## v0.0.88

Source: docs/experiments/v0.0.88.md
SHA256: 9ef76e7903b6dfb2933b5f292dc601d5d0a34d98c39921f8143d1eabc4f541cd

### First actual learned result — frozen negative

All eight first fits completed 12 epochs within the 240s/model cap. Recorded
shared setup was 319.710286 ms; sum of fit times was 42,907.660722 ms. This
excludes experiment archival/logging, and is not total experiment elapsed time.
All 768 original-LP certificates passed (576 timed, 192 warmup). The completion
archive also contains every failed predicted answer and LU witness, paid native
repair, the exact 48 train/12 final arrays, all eight weights and epoch losses.
It was published at `ac311ed659bde2053727c9f4ff6f24aa512f5748` before maintenance.
No fit, timing or final data rerun; no favorable seed or checkpoint selection.

Complete-cost ratios are geometric means, smaller is better. Gate requires <=.8
in every comparison for both seeds/groups; at least four exact-basis cells/group
are also required.

| Seed | Group | /best classical | /best learned Direct | /own full16 | Exact basis /6 | Verdict |
|---|---|---:|---:|---:|---:|---|
| 87001 | IID | 1.0937901571 | 1.0860835926 | 0.9585928500 | 0 | fail |
| 87001 | size/surface | 0.9487543148 | 1.1164133555 | 0.9617247818 | 0 | fail |
| 87002 | IID | 0.8168832945 | 0.8111277446 | 0.6431269534 | 1 | fail |
| 87002 | size/surface | 0.7249416396 | 0.8530496418 | 0.7123395863 | 0 | fail |

10,000-query training-amortized classical ratios, in table order, are
1.1045513257, 0.9505606510, 0.8267480171, 0.7263819658. Break-even is undefined
for seed87001 IID (no positive mean savings), then 657/700/50 queries for the
remaining rows. Break-even alone does not satisfy matched capability/cost gates.

Post-audit descriptive analysis of the first timed repeat gives compact top-m
basis-support recall 0.9329427083 / 0.9609375 for seeds 87001/87002. This is
NOT solve accuracy: native repair was needed on 12/12 / 11/12 cases respectively.
The wider full128 candidates' recalls were 0.9596354167 / 0.94921875 and both
needed native on 12/12 cases. Partial support recovery often fails an exact
entire-basis certificate. These diagnostics did not change the preregistered gate.

Decision: **`FIRST_LEARNED_CANDIDATE_GATE_FAILED`**. The registered bounded
candidate is rejected; global Q3/Q4 remain OPEN. Keep native as deployment
default. Actual model-side compaction is demonstrated by changed state/edge
counts, but stable complete-system superiority is not. Investigate why missing
basis columns dominate repair on opened development evidence; do not tune or
remeasure this final set, or promote one favorable seed as a pass. Published
trained-method comparisons and natural problem coverage are still absent.

The original 44,660,548-byte gzip is split into six ordered byte-exact parts;
manifest checks every part, combined bytes and decoded JSON. Gzip SHA256
`3a77a1dc66bbfd911536e2f9f55e66fe3da9088e3fd0955d4b0e1326b855761a`, JSON SHA256
`9fa7e160a0264cb22475c98eae9ce8b43d8de4c31146ee1c2004476efe349661`.
Retained replay decodes exact arrays/weights and verifies original equations and
cost/identity ledgers without solving, fitting, model inference or input generation.

## v0.0.89

Source: docs/experiments/v0.0.89.md
SHA256: c0a07e5276059ae0eae88fb69432f78fca9ea35612450f619af423939fcdccee

### Contract and first result

All eight v088 checkpoints were restored byte-exact. Every learner could use
the same restricted native LP executor, full original-LP primal/dual certificate,
and paid cold rescue within a shared five-second deadline. Twelve old/new
classical controls include a thin signed-residual shortlist and paid portfolio
union. The twelve fresh constructed inputs use seeds 89900–89911: six IID m64
and six size/surface-shift m128, n=16m. Twenty routes, one warmup and three timed
repeats produced 960 accepted original-problem certificates: 240 warmup and
720 timed. Numerical certification uses the fixed v081 float64 contract;
this is not exact-rational or formal verification.

The gate required BOTH seeds and BOTH groups to have geometric mean complete
cost <=0.8 of best per-case classical, best per-case noncompact learner across
both seeds, and own full16. Each comparison required >=4/6 individual 20% wins;
>=4/6 cases must avoid full rescue on every repeat. Attributed old setup/fit
amortized over 10,000 queries must also retain <=0.8 classical ratio.

| Seed | Group | /best classical | /best learned Direct | /own full16 | No full rescue /6 | Wins classical/Direct/full16 | Verdict |
|---|---|---:|---:|---:|---:|---|---|
| 87001 | IID | 2.6744122994 | 2.1758053406 | 1.9123619180 | 3 | 1/0/0 | fail |
| 87001 | size/surface | 0.8923777000 | 0.9673994836 | 0.7178481279 | 6 | 3/1/1 | fail |
| 87002 | IID | 1.6897452356 | 1.3747157492 | 1.2935270034 | 5 | 1/0/0 | fail |
| 87002 | size/surface | 1.2076863770 | 1.3092160163 | 0.9995431996 | 5 | 2/0/0 | fail |

Training-amortized classical ratios at 10,000 queries, in table order, are
2.7016675195, 0.8949070823, 1.7086558594, 1.2100244783. Original checkpoint loading
was separately measured at 1103.390385 ms; it is not included in online ratios.
No extra training was performed. The paid old fitting remains attributed.

Decision: **`FROZEN_CHECKPOINT_SHORTLIST_GATE_FAILED`**. All four cells fail the
frozen conjunction. A single no-compression ratio below 0.8 does not offset
failure against strong classical and learned Direct. Global Q3/Q4 remain OPEN.
Keep the native solver as the deployed default; do not promote this shortlist
learner or tune/remeasure these opened final inputs. These are constructed LPs
and budget-adapted models, not published trained-baseline reproductions,
natural-problem generalization, memory/energy measurements or frontier parity.

### Retention and interruption recovery

The first completed 28,369,992-byte gzip is retained in four ordered byte-exact
parts with manifest checks. Gzip SHA256:
`c61ef75d101067d735c4c12440993bedcb99cc556d1ab20f93b8fd71430a9311`.
Decoded 67,743,599-byte JSON SHA256:
`4dcc2047e06d2bc6af91912221446b74a12414f631f77adc375f9b023c34e8ee`.
First archive publication completed at
`0f5661f01671b496e7ed53cec0de7c3805dc3a92` before this completion work.
All exact new inputs, old checkpoint states, failed answer/restricted witnesses,
full rescue ledgers and shuffled observations are retained.

After all 960 observations and the completed report were written, the initial
replay validator raised `KeyError: subset_accepted` on legacy exact-basis controls,
whose execution schema differs from the new shortlist schema. The notice
`results/v089_post_measurement_validation.notice.json` preserves this failure.
The validator now handles both schemas; inference, solver, thresholds and first
measurement bytes were unchanged. Replay verifies the same retained certificates,
weights, coverage, cost ledgers and summary without fitting, solving or regenerating
inputs. The separate opened-training-only shortlist screen is compressed with its
original bytes; it does not count as final accuracy or a timing result.

Interruption recovery used a replacement runtime for correctness tests only.
No final benchmark was run in that environment. Focused executor/archive/gate
checks: 25 PASS. Full local regression: 469 PASS, 0 FAIL. CI includes retained
shortlist replay in the torch job and never invokes benchmark_v089.py.

### Next admissible research step

Reject this frozen candidate rather than relaxing its thresholds. Analyse only
opened training data when considering a different candidate. Before another final
run, independently register a measurable source of advantage, equally executable
strong Direct/classical controls, the complete-cost gate and a new sealed split.
Published trained-method reproduction and natural workload coverage remain missing
for global Q3/Q4 closure. A smaller model or restricted solver alone is insufficient.

## v0.0.90

Source: docs/experiments/v0.0.90.md
SHA256: c62aa83b69a7e91fb9e5b71832b162b256821f0a3ee8cb86663a921d4ae67994

### Hypothesis and equal access

The compact graph model selects 2m column states after its first graph update.
The later two updates cannot alter that internal retained set. The alternative
executor therefore uses its paid coarse head immediately and omits the later
updates and optional predicted primal/dual answer. All original paid observable
features remain. Full16/full128 Direct can also stop at their supervised coarse
heads; pointwise Direct can omit its answer heads. All eight old learned routes
and twelve classical routes remain available with their original answer proposals.
Every new route shares the restricted native solve, full original numerical
certificate and paid full rescue under one five-second deadline.

Important distinction: internal retained-set equality is NOT equality of ordered
solver input. Old compact v089 uses refined-score column order; the early route
uses coarse order. All 16/16 ordered inputs differ for each compact seed. Thus
this screen measures the entire registered alternative including ordering and
answer-proposal deletion, not an isolated late-layer FLOP ablation. No claim
that native solve time is invariant to column ordering is made.

The early coarse routine is the SAME code for compact and full Direct; it has
no inference-time state-pruning advantage over that early full Direct route.
Different frozen trained coarse heads can differ, but renaming their output
cannot establish an architectural Q4 attribution.

### First retained result

Only the first 16 v088 training sources are used, balanced across m32/m64 and
condition 1/1000. All eight checkpoints are restored byte-exact. Twenty-eight
routes, 16 cases, one warmup and three timed repeats yield 1792/1792 original-LP
certificate approvals (448 warmup, 1344 timed). All 32 compact internal-retained
set/early-index comparisons agree exactly. No withheld final arrays or records
are used for inference, selection or this screen's summary.

Both seeds must have complete-cost geomeans <=0.8 against per-case best classical,
per-case best noncompact learner including every early Direct alternative, and
own original compact. Each requires >=12/16 individual 20% wins, >=12/16 cases
without full rescue on every repeat, and attributed old fitting amortized over
10,000 queries <=0.8 classical ratio. These thresholds were not changed.

| Seed | /best classical | /best learned Direct | /original compact | Training-amortized /classical | Wins classical/Direct/original | No full rescue /16 | Verdict |
|---|---:|---:|---:|---:|---|---:|---|
| 87001 | 1.5901095996 | 1.8274023399 | 1.0889738409 | 1.6170166136 | 6/0/4 | 13 | fail |
| 87002 | 1.1488932062 | 1.3203430342 | 0.9480046324 | 1.1700263713 | 4/0/6 | 16 | fail |

Decision: **`STOP_ONE_PASS_CANDIDATE`**. Do not spend a fresh final-evaluation
budget on this frozen candidate. Native remains default. Q3/Q4 remain OPEN;
v088/v089 negative final decisions remain unchanged. No memory, energy,
frontier, published-baseline or natural-problem performance claim follows.

Descriptive post-result medians across 48 timed records per route (not a new
measurement or a new selection gate):

| Route | Proposal ms | Execution ms | Complete ms |
|---|---:|---:|---:|
| compact16 seed87001 | 7.865671 | 12.015342 | 21.048778 |
| early compact16 seed87001 | 7.096384 | 11.845657 | 20.562524 |
| early point16 seed87001 | 6.341257 | 10.390285 | 17.146479 |
| compact16 seed87002 | 7.899220 | 9.320174 | 17.621842 |
| early compact16 seed87002 | 7.315783 | 9.486819 | 17.095258 |
| early point16 seed87002 | 6.184688 | 8.447649 | 14.876644 |

Component medians do not add to the complete median. Medians of pooled records
and geometric means of paired per-case medians are different statistics; the
small pooled median gain does not overturn either registered paired failure.
Late-layer deletion alone does not create the required system-level advantage.

### Next boundary

Stop attempting to establish Q4 by relabeling identical early-head computation.
A further candidate needs a separately justified source of predictive advantage
and lower paid input-processing cost, with equally optimized Direct access and
fresh preregistered evaluation only after opened-development admission. Shared
least-squares features and native execution remain in the paid path; their
presence is not itself evidence that deleting them preserves useful accuracy.
No new learner or cheap-feature candidate is admitted by this failed screen.
Published trained baselines and natural-workload coverage remain necessary for
global Q3/Q4 closure.

## v0.0.91

Source: docs/experiments/v0.0.91.md
SHA256: 7b9205cb1bf54ab3633b87d36b9a71eab161842d38e378353d7b2c6e6c4329df

### Frozen hypothesis and execution

Both least-squares feature fits were removed. Column-normalized A,b,c provide
cost, centered cost, b correlation and matrix moments/extrema instead. This
changes information and input semantics, so all four architectures and both
seeds were retrained from the original initialization with the same 48 opened
v088 training examples, 12 epochs, Adam .001, original basis/primal/dual loss,
last-epoch selection and 240-second/model cap. No old final inputs or newly
generated inputs were used. All eight first fits completed.

[Preregistration](v0.0.91-preregistration.md) and executable source were public
at head `a58f55b0b436eea6696d03cb6698d62c27a33686`, tree
`a5e550151bc63034c3e065956eedd8496e81acda`, before any new fit or timing.
Runtime: Python3.12/numpy2.3.5/scipy1.17.0/torch2.14.0+cpu/highspy1.15.1;
single-thread HASWELL BLAS. Tests were completed before timing, then resumed
afterwards. The screen used only train0–train15, balanced m32/m64 and condition
1/1000, width16m. These are training inputs, not a generalization result.

Fourteen deterministic/native routes (all 12 prior classical controls plus
cheap cost/correlation selectors) and eight newly trained routes each pay the
complete original-task path. Learned models all receive the same refined top2m
restricted native executor, omitted-column dual check, full original numerical
certificate, paid cold rescue and five-second deadline. No new model gets an
answer shortcut. Full16 retains all states through three updates; compact16
retains only2m after update zero. Both have5156 parameters; point16 has611,
full128 has299268. Neither parameter count nor reduced edge count proves Q4.

### First results

22 routes ×16 cases ×(1 warmup+3 timed repeats)=1408/1408 original-LP answers
certified, including352 warmup and1056 timed calls. Labels only enter training
and offline scoring; no label is passed to inference or execution.

Ratios use geometric means of paired per-case median complete costs. The best
classical and learned Direct are chosen per case, with Direct allowed both
seeds. Every listed ratio must be<=.8; every first-three comparison must have
>=12/16 individual20% wins, and no-full-rescue must be>=12/16 on every repeat.

| Compact seed | /best classical | /best learned Direct | /own full16 | /classical incl. training at10k queries | 20% wins classical/Direct/full | No full rescue | Gate |
|---|---:|---:|---:|---:|---|---:|---|
|87001|3.6445247778|3.5576552312|2.4804855339|3.6775203070|0/0/0|0/16|FAIL|
|87002|3.7773521192|3.6873165491|2.2314164523|3.8101614992|0/0/1|0/16|FAIL|

Training setup116.970753ms is charged with each compact's own fitting time
for the amortized comparison. Input/archive loading is outside the measured
online proposal and is not represented as free execution work.
The amortization records new data preparation plus each own fit. Model
initialization, checkpoint I/O and prior corpus construction were not separately
timed here; this is a partial training-lifecycle ledger, not an all-in cost
claim. Adding those costs cannot reverse this negative gate. Any future positive
Q4 evidence must close those accounting gaps before claiming a lifecycle win.

| Model | seed87001 first fit ms | seed87002 first fit ms |
|---|---:|---:|
|compact16|2471.568637|2486.663245|
|full16|3326.960878|2933.902187|
|point16|928.422889|910.582814|
|full128|24184.919662|24307.252160|

The following pooled48-timed-observation medians are descriptive only; they
do not replace the paired gate, and medians of components need not sum.

| Route | Proposal ms | Complete ms | Cases without full rescue |
|---|---:|---:|---:|
|compact16 seed87001|2.496718|47.991260|0/16|
|full16 seed87001|2.815250|10.871514|11/16|
|point16 seed87001|1.376023|49.360226|0/16|
|full128 seed87001|17.850907|27.015671|15/16|
|compact16 seed87002|2.369012|46.685162|0/16|
|full16 seed87002|3.116534|14.986589|10/16|
|point16 seed87002|1.285363|43.161195|0/16|
|full128 seed87002|18.082973|25.957642|16/16|
|centred thin classical|1.698712|13.226725|10/16|
|cheap cost|0.697144|43.603631|0/16|
|cheap correlation|0.653288|45.095109|0/16|

Offline scoring of the already-recorded selected columns finds complete label
basis coverage0/16 for both compact seeds and pointwise seeds,11/16 and10/16
for full16,15/16 and16/16 for full128, and10/16 for the centred thin control.
This supports testing a later or less aggressive pruning decision. It does
not isolate the cause: separately trained coarse/refined heads, supervision,
hard selection and graph depth all differ in effect. It does not prove that
cheap features are unlearnable; full models use them successfully on these
opened inputs. Their in-sample coverage is not a Q3/Q4 pass or a holdout license
for the failed compact candidate. New pruning choices require a new frozen
development budget and the strongest same-input executable Direct controls.

### Retention and verification

The first completed gzip was preserved without rewriting, including all48
training source byte arrays/labels, all eight weights and their hashes, all
fit costs/losses, the16 screened sources,1408 records, rejected restricted
witnesses, paid rescue ledgers and the first verdict. First archive publication
head `c38db4f4f0f4579705f9a3b9d3b82cc0b5750a23` predates replay maintenance.

- gzip27,722,149bytes in four ordered parts; SHA256
  `78cd6c8be5c0cad9dbab746aea3b2ff97fe388244ae2bdb2c350f5753e7d5516`.
- decoded JSON58,496,642bytes; SHA256
  `6a47bd6c37ef492f50bc41d77ae0b4eb853694f5d74170003c4e88140a128534`.
- [Manifest](results/v091_first_screen.manifest.json), bounded hash-checked
  loader `neumann1/lp_cheap_archive_v091.py`, replay
  `experiments/lp_cheap_screen_v091.py:validate`.

Replay checks source identity, fit metadata, checkpoint hashes, state/edge
metadata, original and rejected restricted/native witnesses, coverage, cost
ledgers and verdict. It never fits, generates a case, runs model inference or
calls a solver. CI only runs contract fixtures and retained replay; the explicit
first runner `benchmark_v091.py` reserves its output directory and never runs
in CI. Numerical backward-error certificates are not formal exact proofs.

No new claim about natural workload coverage, published-trained baselines,
energy, memory, scaling, or global Q3/Q4 closure is made. Previous negative
v088–v090 results are unchanged.

## v0.0.92

Source: docs/experiments/v0.0.92.md
SHA256: 030a26a8b54787ca3e347a9c07c3d132e5d9cee201e930a7645e38b8cac7684d

### Frozen hypothesis

Keep v091's cheap target-free features, but gather information in two full
graph updates before the coarse head removes columns down to2m. Only the
third update operates on compact states/edges. Full16/full128 receive the same
late coarse head and supervision while retaining all columns. Compact/full16
still have5156 parameters, point16 has611 and full128 has299268. Total update
count remains three; the change is not a new parameter-budget advantage.

All eight candidates were fitted once on the same48 opened v088 train sources:
seeds87001/87002, twelve epochs, Adam .001, original basis/primal/dual loss,
last epoch only,240-second cap/model. No tuning, widened shortlist, favorable
rerun, old final input or new generated input was used. Moving supervision
and retraining changes optimization too, so this is not an isolated causal
ablation of one inference operation.

[Preregistration](v0.0.92-preregistration.md) and executable source were public
at head `154ca566e70f3c87e2bdb0a4267e8185e46c9414`, tree
`e005428222a2d8d3695f14ca10c6c6f085ec83d7`, before fitting or timing. The old
session's venv was gone; matching Python3.12/numpy2.3.5/scipy1.17.0/
torch2.14.0+cpu/highspy1.15.1 was restored before running. A preflight collection
attempt lacked sklearn while dependency installation was still finishing;
after installation the four architecture/gate contracts passed. No study
fitting/timing had started at that point. Single-thread HASWELL BLAS was pinned.

### Descriptive components and interpretation

Pooled48-timed-observation medians below are descriptive only; components do
not necessarily add and cannot override the paired gate above.

| Route measured in this screen | Proposal ms | Complete ms | No full rescue |
|---|---:|---:|---:|
|new compact16 seed87001|1.703131|14.439655|2/16|
|new full16 seed87001|1.972433|10.644080|11/16|
|retained v091 compact16 seed87001|1.512489|35.709605|0/16|
|retained v091 full16 seed87001|2.004231|7.703245|11/16|
|new compact16 seed87002|1.746432|35.058957|0/16|
|new full16 seed87002|2.148494|12.176057|9/16|
|retained v091 compact16 seed87002|1.666887|34.250216|0/16|
|retained v091 full16 seed87002|1.909698|10.663249|10/16|
|new full128 seed87001|12.788799|18.277428|15/16|
|new full128 seed87002|11.349940|16.721399|15/16|
|centred thin classical|0.911786|9.505333|10/16|

One seed's pooled complete median improves relative to the older compact;
the other does not, and neither beats the protected strongest Direct. A
pooled14.44ms median is not a3.34x paired win: paired casewise ratios against
the fastest applicable Direct are the registered authority. Later selection
alone is still insufficient under this exact architecture/loss/fit budget.
Do not conclude all cheap features or all delayed selection mechanisms fail.
Hard selection quality, coarse/refined supervision and optimization remain
confounded. Before spending another fit budget, diagnose the selector itself
against strong cheap observable-only approximation controls rather than keep
moving the cut point or relaxing the gate. No speculative next candidate is
treated as admitted by this result.

## v0.0.93

Source: docs/experiments/v0.0.93.md
SHA256: 11ccc5c52b8435ee978192e0861899de4ddaaf545655e9b2bcd663f12f9c5afd

### v0.0.93 — Untimed selector diagnosis: keep the no-new-fit verdict



### Question and frozen scope

Can cheap observable approximations preserve the useful shortlist information
of the original learned selector before another paid training or timing study?
The protocol was published at `c1f004ed10f5c293781707643f54fc8471e8451a`.
Only the 48 already-opened v088 training inputs and frozen v088/v091/v092
weights are used. Four eight-model conditions and six classical controls
produce 1,824 records in one first inference pass. No training, optimizer,
rescue, new inputs, final evaluation, or timing comparison is performed.
See [the preregistration](v0.0.93-preregistration.md).

All proposals use A,b,c only. Labels are inspected after proposals are fixed
for offline exact-basis/shortlist coverage. Each exact-m basis receives an
original-LP numerical primal/dual certificate. A rejected basis is retained;
there is no optimizer repairing it into an answer in this diagnosis.

### First result

Decision: `SELECTOR_GAP_UNRESOLVED_NO_NEW_FIT`.
All 1,824 records are present, with zero proposal errors. Only 82 exact-m
bases certify (1,742 rejected); this is not 1,824 successful LP answers.
Every classical exact-m control certifies 0/48. The strongest classical
shortlist coverage is 32/48, below the frozen 46/48 near-saturation threshold.

CG3 pointwise shortlist coverage falls from 46 to 44 for seed87001 and from
46 to 45 for seed87002. The first seed exceeds the allowed loss of one case;
the second seed passes its parity conjunction. Both must pass, so no paid
CG3-point timing screen is admitted. These are opened-training diagnostics,
not generalization evidence or a new efficiency result.

| Route | Certified exact-m bases /48 | Label basis contained in top2m /48 | Coarse top2m /48 |
|---|---:|---:|---:|
| `qr_affine` | 0 | 32 | — |
| `gram_affine` | 0 | 32 | — |
| `gram_trim` | 0 | 7 | — |
| `cg3_affine` | 0 | 31 | — |
| `cg5_affine` | 0 | 32 | — |
| `cg3_primal` | 0 | 0 | — |
| `v088_exact_compact16_s87001` | 3 | 39 | 39 |
| `v088_exact_full16_s87001` | 0 | 46 | 45 |
| `v088_exact_point16_s87001` | 1 | 46 | 46 |
| `v088_exact_full128_s87001` | 15 | 48 | 48 |
| `v088_exact_compact16_s87002` | 10 | 47 | 47 |
| `v088_exact_full16_s87002` | 0 | 47 | 47 |
| `v088_exact_point16_s87002` | 0 | 46 | 46 |
| `v088_exact_full128_s87002` | 12 | 48 | 47 |
| `v088_cg3_compact16_s87001` | 2 | 40 | 40 |
| `v088_cg3_full16_s87001` | 0 | 46 | 46 |
| `v088_cg3_point16_s87001` | 0 | 44 | 44 |
| `v088_cg3_full128_s87001` | 18 | 48 | 48 |
| `v088_cg3_compact16_s87002` | 9 | 47 | 47 |
| `v088_cg3_full16_s87002` | 0 | 47 | 48 |
| `v088_cg3_point16_s87002` | 0 | 45 | 45 |
| `v088_cg3_full128_s87002` | 12 | 48 | 47 |
| `v091_cheap_compact16_s87001` | 0 | 3 | 3 |
| `v091_cheap_full16_s87001` | 0 | 31 | 3 |
| `v091_cheap_point16_s87001` | 0 | 0 | 0 |
| `v091_cheap_full128_s87001` | 0 | 46 | 2 |
| `v091_cheap_compact16_s87002` | 0 | 3 | 3 |
| `v091_cheap_full16_s87002` | 0 | 32 | 1 |
| `v091_cheap_point16_s87002` | 0 | 0 | 0 |
| `v091_cheap_full128_s87002` | 0 | 47 | 3 |
| `v092_late_compact16_s87001` | 0 | 8 | 8 |
| `v092_late_full16_s87001` | 0 | 37 | 22 |
| `v092_late_point16_s87001` | 0 | 0 | 0 |
| `v092_late_full128_s87001` | 0 | 46 | 35 |
| `v092_late_compact16_s87002` | 0 | 1 | 1 |
| `v092_late_full16_s87002` | 0 | 32 | 6 |
| `v092_late_point16_s87002` | 0 | 0 | 0 |
| `v092_late_full128_s87002` | 0 | 46 | 34 |

### Interpretation and next boundary

The v091 compact shortlist covers all required columns on only 3/48 cases
for either seed; delayed v092 compact reaches 8/48 and 1/48. Full128 cheap
models reach 46/48 and 47/48 in v091, and 46/48 for both seeds in v092.
This localizes a selector/early-state information gap, but does not isolate
one causal mechanism: checkpoints, losses, heads and pruning differ.

CG3 substitutes approximate least-squares feature slots into the SAME v088
weights. It is an intentional input distribution shift, not a retrained
model or feature equivalence result. Approximation errors are retained in
the archive. Classical Gram and CG work remains real computation even
though this diagnosis shares preparation and makes no cost claim.

Do not train another depth/keep-size variant or promote CG3 from the favorable
seed. Any successor needs a separately registered hypothesis and must keep
strong classical and learned Direct comparators with identical authority.
Native remains default; Q3 and Q4 remain OPEN. No speed, memory, energy,
frontier capability or complete-lifecycle advantage is established here.

## v0.0.94

Source: docs/experiments/v0.0.94.md
SHA256: 7d3eb1a13f808132bb4c3b0c4317d55aa3bc2f033bf4bed05a338dd00c4720e0

### Hypothesis and first diagnosis

A frozen pointwise selector with exactly five matrix-free CG steps replaces
both least-squares feature fits, then removes columns BEFORE all three graph
updates. Full original observable slots are kept; no subset feature refresh,
new training, checkpoint selection or hidden labels enter proposals.
Both seeds use the exact v088 point16/full16 weights. The separate point-only
Direct route remains entitled to the same certificate/native runtime.

[Untimed preregistration](v0.0.94-preregistration.md) was published at
`f9951a814c2ddfd8bdbdeabec79ad68bd2ef1d33` before the first pass. All48
already-opened train inputs produce288 records, without timing or optimizer.

| Seed | CG5 point shortlist /48 | Full16 shortlist /48 | Compacted shortlist /48 | Compacted exact-m certificates /48 |
|---|---:|---:|---:|---:|
| 87001 | 46 | 46 | 46 | 0 |
| 87002 | 46 | 47 | 46 | 1 |

Both point parity and transfer conjunctions pass. Actual graph input columns
are2m instead of16m, so three-update graph multiply terms are1/8 of full16.
This is an operation ledger, not an elapsed-time/energy or memory measurement.
The compacted top2m set equals the point-only shortlist by construction;
refined column order and exact-m bases can differ. Thus point-only is essential
for testing whether the graph contributes sufficient additional information.
First decision: `ADMIT_SEPARATELY_REGISTERED_COMPLETE_COST_SCREEN_NOT_Q3_Q4`.

### Decision and recovery

Native stays default. Q3 and Q4 remain OPEN. Useful-column coverage is recovered,
but model-level complete-cost superiority has not been established. The frozen
point-only path already supplies the same retained set, so adding graph updates
cannot earn a Q4 pass merely by shrinking their state counts. Do not shift pruning
again or retrain another variant on these opened inputs based on this result.
A successor must justify additional graph work or choose a different principled
target; no frontier, natural-workload, scaling, memory or energy claim follows.

First source arrays and weights remain hash-pinned in v088; the v093 comparison
reference is unchanged. The first probe and cost gzip bytes, source/checkpoint
identities, rejected witnesses, complete costs, first verdict and explicit
contamination notice are retained. Replay never fits, runs inference, regenerates
inputs, calls an optimizer or reruns timing. CI runs fixtures/replay only.

- [First probe manifest](results/v094_first_probe.manifest.json)
- [First cost manifest](results/v094_first_cost.manifest.json)
- [Timing notice](results/v094_timing_notice.json)

Validation:6 focused PASS; complete local regression536 PASS·0 FAIL in238.56s;
diff checks pass. Remote CI and merge are recorded in the PR and restart
checkpoint when complete. First diagnosis and first cost bytes are unchanged.


First remote CI #347 stopped at general-suite collection because the new
model fixture imported optional torch before checking availability. Add the
same `pytest.importorskip` guard used by existing model fixtures; the separate
torch CI still executes every new test. This fixes dependency routing only;
first experiment/archive/protocol/decision bytes remain unchanged.

## v0.0.95

Source: docs/experiments/v0.0.95.md
SHA256: a60b063d666b1adcd6d5636c4458d05ebb4248e556a0322472c846bf01c14894

### Question

Does the v0.0.94 compact graph discover a new compressed variable support, or
does it only re-rank columns that the pointwise selector already chose?

No new model fitting, inference, solver execution, timing, input generation, or
holdout is used in this version. This is a code/authority closure over the
already-published v0.0.94 route.

### Next admissible target

A successor must create structural authority that the strong cheap Direct path
does not already possess. Before fitting, require at least one of:

- a learned/graph route that can change the retained support under equal
  verifier/executor authority;
- an independently verifiable transformation that reduces downstream degrees
  of freedom beyond the point selector;
- a different problem family where a zero-model or deterministic headroom
  screen leaves enough complete verified cost budget.

Strong deterministic and matched executable Direct comparators remain
mandatory. Native stays default. Q3/Q4 remain OPEN.

## v0.0.96

Source: docs/experiments/v0.0.96.md
SHA256: ddf8a8be5e39ed357b43d1233fb5fea38dfb0bba70de4e31df28034a75321459

### First retained result

CI #358, sequence job `110414946608`, replayed the frozen archive at head
`109e82dfa3e2d81ec5a85678a58193750217c73c`.

| Seed | 2m contains full reference basis | Mean basis recall in 2m | Full graph top2m contains basis | Point exact cert. | Full-info graph exact cert. | Compact exact cert. | Full-info cert. gain |
|---|---:|---:|---:|---:|---:|---:|---:|
| 87001 | 46/48 (95.83%) | 99.935% | 46/48 | 1 | 0 | 0 | 0 |
| 87002 | 46/48 (95.83%) | 99.935% | 47/48 | 0 | 0 | 1 | -1 |

Both early-compressed representations clear the 80% ceiling floor by a large
margin. In the two missed cases per seed, mean basis recall still remains
0.99935 overall: early compression usually omits at most a very small fraction
of the reference basis.

Turning early compression OFF does **not** rescue the existing exact-m
discoverer. The full-information graph produces zero original-LP-certified
exact-m proposals on both seeds and does not reach the frozen +4 threshold.

Decision:

`DISCOVERER_BOTTLENECK_DOMINATES_EARLY_SUPPORT_LOSS`

### Interpretation

This is not a Q34 pass and not a general statement that compression timing
never matters. It is a routing result for the current LP family and frozen
models.

The high-value conclusion is that another version spent moving the pruning
point is unlikely to answer the central question. The 2m support already
contains almost all of the useful reference structure, while the exact-m
proposal head fails even when all columns are available.

That exposes a target mismatch:

> **support discovery is already much easier than exact-basis generation.**

NEUMANN does not need to predict the final basis perfectly if it can cheaply
identify a small support on which a restricted solver succeeds, verify the
original LP, and fall back safely when it does not.

Therefore the next architecture tournament evaluates complete
`support proposal -> restricted solve -> original verification -> fallback`
systems, not isolated exact-m basis accuracy.

No clean timing, memory, energy, generalization, Q3 closure or Q4 closure is
claimed here. Native remains default until a candidate clears Q34.

## v0.0.97

Source: docs/experiments/v0.0.97.md
SHA256: 670552c0a403dfdee94c74300c3db5da0af41244102b3ad162efa3f55d077ed8

### Question

After v0.0.96 showed that the 2m representation already preserves almost all
reference-basis information, can a complete support-discovery system recover
most oracle structural savings cheaply enough to beat Direct under equal
original-problem verification?

The preregistered gate is in
`v0.0.97-preregistration.md`. No new model fitting, checkpoint selection,
final data, or hyperparameter sweep is used.

### First valid result

| Family | Utility recovery | Discovery burden | Amortized complete / Direct | Fallback-free cases | Gate |
|---|---:|---:|---:|---:|---|
| A deterministic | 0.320260 | 0.091266 | 0.735660 | 10/16 | FAIL |
| B point support | **0.909057** | **0.045977** | **0.212278** | **16/16** | PASS |
| C full graph | 0.908692 | 0.097887 | 0.254732 | 16/16 | PASS |
| D adaptive | 0.826285 | 0.050573 | 0.287452 | 16/16 | PASS |

Both frozen B_POINT seeds pass independently:

- seed87001: utility 0.909057, burden 0.045977, amortized ratio 0.212278;
- seed87002: utility 0.910781, burden 0.045277, amortized ratio 0.210206.

C and D also clear the development conjunction but are Pareto-dominated by
B_POINT. A reduces complete cost but recovers only 32.0% of oracle structural
utility, below the frozen 0.80 floor.

Decision:

`ADMIT_FRESH_Q34_HOLDOUT`

The sole Pareto Q34 development survivor is:

`B_POINT`

This is the first clean evidence in the current LP line that a small learned
support proposer can be cheap enough relative to the structural savings it
unlocks **when the solver is asked to finish the problem rather than the model
being forced to predict the exact basis**.

## v0.0.98

Source: docs/experiments/v0.0.98.md
SHA256: ffa7cff7f64744a40db5e953279d5a79a5eba229f1b2f87566e9c035ae9538ea

### v0.0.98 — Fresh Q34 holdout result



### Question

Does the sole v0.0.97 Pareto survivor, frozen `B_POINT`, retain the joint
Q34 advantage on separately registered fresh cases without any new fitting,
checkpoint selection, support-factor tuning, fallback tuning, or threshold
change?

### Result



### Decision

`Q34_FRESH_HOLDOUT_FAIL_NO_Q5`

`advance_q5 = false`

`lp_q34_mechanism_pass = false`

No holdout tuning is authorized.

This is a useful failure rather than a cost failure. On IID64, the frozen
support proposer reproduces the development result. On the larger
size+surface-equivalent group, inference remains cheap, but the proposal fails
to capture enough of the available Oracle structural savings.

## v0.0.99

Source: docs/experiments/v0.0.99.md
SHA256: fe8202c91b973c1473d2df346a84a16355564d8b1dae26152964049baf8d92e4

### Frozen equivalence audit

For each opened input, three label-free equivalent views are generated:

- signed row permutation,
- positive column scaling with matched objective scaling,
- their composition.

The current CG5 representation is compared with a preregistered quotient
representation. No label, oracle basis, solver, fitting, optimizer, timing,
fallback or Q34 performance metric is used.

The quotient representation keeps the first four CG5 column observables and
replaces two surface-sensitive slots with:

- `|D_j|^T |b| / max(1, ||b||_2)`;
- `||D_j||_1 / sqrt(m)`.

### First retained audit

Dedicated workflow: `36943890918`  
Job: `110641411909`  
Frozen head: `b9299e382d516b6d26669d1134f763f20a3367d4`

### Decision

`ADMIT_QUOTIENT_POINT_REFIT_ON_OPENED_DEV`

The representation gate passes before training.

This does **not** show that a model trained on the quotient representation will
recover more structural utility, does not pass Q34, and does not advance to Q5.
It authorizes exactly one next step: a separately preregistered refit/evaluation
using opened development + metamorphic data only.

The sealed v0.0.98 24-case holdout remains unavailable for tuning or re-test.
Any future confirmation after development must use a newly registered holdout
with new seeds.

## v0.0.100

Source: docs/experiments/v0.0.100.md
SHA256: a2f4d8c46156c4073b77d8612615af7b47a89d408a0ed9238733dd3c30d7ed1d

### Result



### Decision

`STOP_QUOTIENT_REFIT_NO_FRESH_HOLDOUT`

- no second fit;
- no threshold rescue;
- no new fresh holdout;
- no reuse of the v0.0.98 holdout;
- no Q5 advance.

### Interpretation

v0.0.99–100 successfully separate two effects that were previously entangled.

1. **Surface representation defect:** real, and fixed. Quotient features reduce
   the known equivalence drift to numerical roundoff and the trained selector
   becomes exactly support-invariant on all 16 paired development problems.
2. **m128 structural recovery:** still incomplete. One 2m-support miss per
   eight cases is enough for a full Direct fallback to pull cell utility below
   the frozen 0.80 floor.

The next experiment must not train the model again. A higher-information next
question is whether the already-frozen quotient ranking contains the missed
structure at a modest larger support such as 4m. That can be tested as a
conditional fallback/authority ceiling before any additional learning.

If a small verifier-triggered support expansion cannot recover the misses
cheaply, stop this fixed point-support formulation and move one level up.

## v0.0.101

Source: docs/experiments/v0.0.101.md
SHA256: 798f346785dd7204719b607825caea1fd37505cb40ea943c758d98618fb79066

### Result

FIXED2 reproduces the residual problem on the new development sample. Its
worst-cell utility is 0.78324 and it falls back on four of 32 views per seed
(28/32 fallback-free), so it does not clear the frozen per-cell Q34 floor.

EXPAND4 clears every frozen cell and combined gate for both seeds:

| Metric | Conservative EXPAND4 value |
|---|---:|
| minimum utility recovery | **0.866994** |
| maximum discovery burden | **0.030060** |
| maximum amortized complete / Direct | **0.221243** |
| fallback-free | **32/32 for both seeds** |
| exact base/surface top2m invariance | **16/16 for both seeds** |

The 4m stage is not continuously paid. Each seed expands on exactly four of 32
views and all four expansions certify successfully. No full Direct fallback is
needed.

On the two m128 cells together, the preregistered authority test is satisfied
for both seeds:

- seed100001: full fallbacks 2→0, worst utility 0.783586→0.870975,
  worst complete ratio 0.261910→0.179194;
- seed100002: full fallbacks 2→0, worst utility 0.783242→0.872480,
  worst complete ratio 0.262249→0.178880.

Therefore the improvement is not merely a favorable resample of FIXED2. The
verifier-triggered expansion earns new authority under the preregistered test.

### Decision

`ADMIT_NEW_FRESH_Q34_HOLDOUT_FOR_FROZEN_SUPPORT_SYSTEM`

Freeze **EXPAND4 only**.

Do not refit, calibrate thresholds, tune support factors or reuse the v0.0.98
holdout. The next permitted step is a newly registered fresh Q34 holdout with
new seeds and the exact frozen EXPAND4 contract.

This is still development evidence. It does not itself pass global Q34, close
Q3/Q4, or authorize Q5.

If the new holdout confirms the frozen Q34 conjunction, stop local Q3/Q4
polishing and carry the verified support system into Q5 scaling/cross-domain
tests.

## v0.0.102

Source: docs/experiments/v0.0.102.md
SHA256: 0450120a7f36ead1edd1fb84e8c78f1dff2d0d0579a3a7cd7a8bda447ad7c6ad

### Result

v0.0.102 is the final Q34 confirmation for the current constructed LP
mechanism. The frozen EXPAND4 system passes the separately registered fresh
holdout under the preregistered per-cell and combined gate.

Decision:

`Q34_EXPAND4_FRESH_HOLDOUT_PASS_ADVANCE_Q5`

The retained summary sets:

- `advance_q5 = true`;
- `lp_q34_mechanism_pass = true`;
- `development_tuning_on_holdout = false`;
- `v098_holdout_access = false`;
- global Q3 and Q4 remain analytically `OPEN`.

This is a Q34 pass for the **constructed LP mechanism**, not a domain-general
closure of Q3/Q4.

### Combined results

| Route | Utility recovery | Discovery burden | Amortized complete / Direct | Fallback-free | 4m expansions |
|---|---:|---:|---:|---:|---:|
| EXPAND4_s100001 | 0.821688 | 0.021855 | 0.238921 | 48/48 | 8/48 |
| EXPAND4_s100002 | 0.822772 | 0.021960 | 0.237998 | 48/48 | 8/48 |

Across the fresh set:

- Direct median-total sum: **12,210.338884 ms**;
- free-oracle post total: **647.954452 ms**;
- available oracle structural savings: **11,562.384432 ms**;
- both seeds have exact paired top2m invariance **24/24**;
- every 4m expansion certifies;
- Direct fallback is used on **0/48** views for both seeds.

### Cell results

| Seed | Cell | Utility | Burden | Complete / Direct | Fallback-free | Expanded |
|---|---|---:|---:|---:|---:|---:|
| 100001 | m64_base | 0.907109 | 0.034349 | 0.193529 | 12/12 | 0 |
| 100001 | m64_surface | 0.906390 | 0.032177 | 0.187678 | 12/12 | 0 |
| 100001 | m128_base | 0.807256 | 0.021386 | 0.251306 | 12/12 | 4 |
| 100001 | m128_surface | 0.812945 | 0.019024 | 0.240453 | 12/12 | 4 |
| 100002 | m64_base | 0.904959 | 0.034522 | 0.195585 | 12/12 | 0 |
| 100002 | m64_surface | 0.907219 | 0.032229 | 0.186979 | 12/12 | 0 |
| 100002 | m128_base | **0.805591** | 0.021420 | **0.252877** | 12/12 | 4 |
| 100002 | m128_surface | 0.816951 | 0.019205 | 0.236850 | 12/12 | 4 |

Conservative coordinates over all preregistered cells:

- minimum utility recovery: **0.8055909773**;
- maximum discovery burden: **0.0345223207**;
- maximum amortized complete/Direct: **0.2528766544**;
- minimum fallback-free coverage: **12/12**.

The weakest cell therefore still clears the frozen 0.80 utility floor.

### Interpretation

The important result is not that a model predicts the exact optimal basis.
It does not need to.

The successful contract is:

```
quotient observable representation
  -> small frozen point support ranking
  -> 2m restricted native solve
  -> original-problem verifier
  -> 4m expansion only on verifier failure
  -> charged Direct fallback if still necessary
```

On this constructed LP family, that complete system recovers more than 80% of
available oracle structural savings on every fresh cell while discovery remains
well below 20% of those savings and complete cost remains below Direct.

That is sufficient for the project's development objective:

> Q3/Q4 do not need further local polishing before Q5.

### Boundary and next step

Do **not** interpret v0.0.102 as proving that NEUMANN is generally superior to
large models, that Q3/Q4 are globally solved, or that the mechanism transfers
to natural or unrelated problem families.

What is now established is narrower:

`constructed LP mechanism Q34 PASS -> Q5 authorized`.

No further refit, support-width search, threshold rescue or local Q3/Q4 tuning
is authorized on this family. Q5 must now stress the frozen mechanism on
scaling, distribution/task-family transfer and complete end-to-end cost under
the same original-problem verification authority.

The retained evaluation is replayed in CI without model inference, fitting,
solver execution or timing.

## v0.0.103

Source: docs/experiments/v0.0.103.md
SHA256: b15605367224b77d58c2a7008c3e6551d6d0b624db8c7e77fda02837b867f341

### Decision

`Q5_SCALING_CAPABILITY_OR_ACCOUNTING_UNREACHED`

The first constructed-LP scaling slice is complete, but does not pass Q5.
All 1536 observations are retained and accounted. The 5-second verified
capability gate fails on 32 Direct observations, including warmups. There
are also independent cost failures. Neither partial favorable slopes nor
candidate success can rescue the preregistered conjunction. `global_q5_closed`
and `cross_domain_pass` remain false. v102's narrower Q34 finding is unchanged.

No fitting, checkpoint selection, support-width search, threshold change,
source replacement, repeat selection or measurement rerun occurred.

## v0.0.104

Source: docs/experiments/v0.0.104.md
SHA256: aa78a1144c396e845aef18763bda1a3da56dc08dd865daa3c8abdf13299ff17c

### 1. Decision and scope

First frozen decisions:
- assignment: `STOP_FAMILY_NO_ORACLE_HEADROOM`.
- basis_pursuit: `ADMIT_FROZEN_CHECKPOINT_TRANSFER_NOT_LEARNING`.

All448 observations certify original LP answers within the complete5s budget;
zero failures. Assignment fails all four cost cells, including the small
control. Basis-pursuit passes all four. This is ZERO-model optimistic Oracle
headroom, not an actual transfer result, a fitting admission or globalQ5 pass.
The free Oracle receives BOTH exact support AND original optimal dual. It is
not deployable and is more privileged than v103's basis-only diagnostic.

Both construction classes share the LP backend and certificate. They are not
independent computational domains or natural workloads. `global_q5_closed=false`
and `cross_domain_pass=false`; v103's negative first Q5 gate is unchanged.

### 9. Next authority and global Q5 boundary

Assignment is stopped for this protocol, without threshold relaxation or
replacement. Basis-pursuit admits ONLY a separately preregistered first test
of BOTH existing frozen checkpoints on NEW unobserved sources, with no training,
no choice between seeds, strongest applicable declared Direct, paid fallback,
and matched original-task certificates/complete costs. These opened32 sources
cannot be recycled as a favorable final set or used for checkpoint tuning.

GlobalQ5 remains OPEN. v103's first larger-size gate failed and is unchanged.
This study supplies neither actual learned task transfer nor computational
cross-domain reuse, cache invalidation, held-out surface robustness or slope
uncertainty. Do not replace Q5 closure with an Oracle admission label.

## v0.0.105

Source: docs/experiments/v0.0.105.md
SHA256: c9a0f18d26ffa1255f397cc1db66901922df25cd11c99f4ba614b3f7e7d690d0

### 2. Question namespace and history

Current namespace is `north_star_2026_10_02`: Q5 complete end-to-end cost,
Q6 unseen/open-set/new-family/scaling, Q7 actual frontier gap recovery.
The exact v104 historical gate text is retained in a legacy annex (SHA256
`d48101642e48f8878ac35d94a303c5c9fef3bc14d9a3f3a12da2b00f43277c94`).
No first source/result bytes or historical `global_q5_closed` decision strings
are replaced or retrospectively mapped to new Q5 closure.

PR117's publication is merged at `0f58be1e205f04c54c6d32506fba64bf6f74ca27`.
v104 retains 448 original-LP-certified observations, no failed observations and
zero model forwards: assignment STOP; basis-pursuit frozen-transfer admission
only. Both classes share the LP backend. Its free exact-support/optimal-dual
Oracle is NOT a deployable small system or evidence of frontier capability.

### 6. Next gate — UNARMED

First actual Frontier Gap execution needs a concrete approved small/frontier pair,
provider/process interface, licensed original tasks, independent task checker,
NEUMANN candidate freeze and bounded call/spending authority. No configured
frontier adapter was found in the inspected repository. Do not infer account
access, extract credentials or launch paid calls without the required authority.
No automatic basis-pursuit follow-up replaces this primary surface.

## v0.0.106

Source: docs/experiments/v0.0.106.md
SHA256: 7b5c63ef7bf3fca7b61f307bc26162bbb37bf7d409785ce9491d3bf747cd68bd

## v0.0.38.1

Source: docs/experiments/v0.0.38.1.md
SHA256: dd9689d95283ed1f6d418a7321382af4f17673f0c01e450ea71a938a78af5ffc

### Fresh audit set

Per cell:

    32 systems

Total:

    256 systems

Use new seeds not used by the merged v0.0.33-v0.0.38 corpora.

Every v0.0.38.1 signature must be:

- unique within v0.0.38.1,
- disjoint from merged prior comparable corpora.

The audit set is opened only after this specification and implementation are
committed.

### Family decision

If safety passes and all H1-H5 pass:

    family_status = HARDER_FAMILY_VALIDATED

If safety passes but any H gate fails:

    family_status = FAMILY_NOT_HARD_ENOUGH

If safety fails:

    family_status = INVALID_FAMILY_OR_CHECKER

No threshold, gate, generator rule, or checker rule may change after the first
full result is observed.

### Next milestone if validated

Only after:

    HARDER_FAMILY_VALIDATED

proceed to block discovery/routing.

The next experiment must compare, before any learned method is privileged:

1. deterministic exact 2x2 algebraic enumeration,
2. sparse row-pair heuristics,
3. graph / connected-component pairing,
4. smallest-adequate learned block scorer only if deterministic discovery leaves
   pre-registered downstream headroom.

### Post-result record

This section was added after the first full v0.0.38.1 execution completed.

Canonical first full run:

- GitHub Actions run: **183**
- PR: **#45**
- final systems: **256**
- active systems: **224**
- mixed active systems: **192**
- no-compression controls: **32**
- final cells complete: **PASS**
- fresh signature disjointness: **PASS**
- motif contract: **PASS**
- candidate-count contract: **PASS**
- one-row verified retention: **1.0**
- exact mixed-reference verified retention: **1.0**
- unsafe one-row reductions: **0**
- unsafe reference reductions: **0**
- `KEEP = true`

### Aggregate result

Frozen local one-row pipeline:

    mean elimination recovery
        = 0.2542517006802721

    mean solver-savings recovery
        = 0.33530849727438206

    active progress rate
        = 0.8883928571428571

Bridge diagnostic:

    mean easy-leaf recovery
        = 1.0

Exact mixed reference:

    mean retained-dimension error
        = 0

Breadth:

    broad hard cells
        = 7 / 7 active cells

Candidate visibility:

    exact candidate-count rate
        = 1.0

### Central result

The redesign achieved the bridge that v0.0.38 failed to establish.

On every mixed active cell, the frozen local pipeline recovered the declared
easy leaves at:

    100%

Yet aggregate total elimination recovery remained only:

    25.43%

and aggregate solver-savings recovery remained only:

    33.53%

This means the residual gap cannot be explained by a generally broken local
pipeline.

The local primitive succeeds on the structure it is designed to handle, then
saturates while substantial multi-row structure remains.

The measured architecture is therefore:

    raw exact system
        ↓
    frozen local one-row compression
        ↓
    genuine verified local progress
        ↓
    local primitive saturation
        ↓
    large residual multi-row headroom
        ↓
    exact 2x2 block compression reference
        ↓
    declared core

This is the intended harder Structural Compression testbed.

## M106

Source: docs/research/bp_frozen_transfer_m106.md
SHA256: 6f394bd86395768bb18b1769ce771da23864ae39cf043e48393708b436fd6ee8

## Runtime-0.1

Source: docs/research/general_runtime_repair_v1061.md
SHA256: e9f4d2a1d1939b3ad974626f07459c76cef6e0ce73867cb47b33746e8b4a0939

## Runtime-0.2-Decision1

Source: docs/research/general_runtime_compact_v1062.md
SHA256: f47043112ed3f3e9c3e4e5e084057136a6a76d2112c74ef38842afd47c51b6b0

### First actual result

Source run: `37013632396`.

Source trigger head: `7a47dba21934675e7f6a1c44c67ee9326bd30db3`.

Retained evidence commit: `0185661132822e7b62c37dc8a24d64ca45af1d75`.

The one-shot first actual Runtime-0.2 run completed all 15 retained observations
and preserved the frozen-core audit, but **Decision 1 FAILED**.

Measured replay:

- 15/15 prompts passed the 240-token admission gate,
- observed prompt range: 159-229 tokens,
- 15/15 model-token accounting complete,
- 5/15 actual query timeouts,
- only 1/9 B2/B3/N observations executed any deterministic tool,
- only 7/15 observations reached the original checker,
- 7/15 observations produced a retained candidate answer,
- 2/15 observations were accepted by the checker.

By arm:

- B0: 0 timeouts, 3/3 checker reached, 1/3 accepted,
- B1: 0 timeouts, 3/3 checker reached, 0/3 accepted,
- B2: 0 timeouts, 0/3 tool calls, 0/3 checker reached,
- B3: 2/3 timeouts, 1/3 tool path, 1/3 checker reached, 1/3 accepted,
- N: 3/3 timeouts, 0/3 tool calls, 0/3 checker reached.

The compact prompt successfully removed native-schema inflation. That means this
failure must not be reclassified as another prompt-length problem. Instead, the
frozen E2B core frequently failed to obey the compact control grammar on the
first attempt, while a second model call was physically too expensive inside the
120 s single-thread CPU query budget. First calls already consumed roughly
70-109 s on the opened controls.

This is still **NOT** a General Capability verdict. The run does not establish
that NEUMANN helps or hurts the same core on a matched capability task. It shows
that the current single-thread CPU harness is no longer an efficient scientific
surface for obtaining that answer.

### Decision after first actual v1062

Per the frozen critical-path contract:

```
Decision 1 = FAIL
CPU runtime mainline = STOP_MICROTUNING_MOVE_ACCELERATOR
General Capability Gate = NOT_EVALUATED
Q1-Q7 = OPEN
```

Do **not** create Runtime-0.3 to tune prompt wording, compact grammar, parser
heuristics, token caps or single-thread CPU latency.

The next execution environment must preserve:

- the same frozen Gemma 4 E2B revision,
- matched baseline vs NEUMANN rights,
- original-checker authority,
- complete resource accounting,
- bounded tool and model calls,

while moving the capability experiment to accelerator-class execution. Edge
efficiency remains a later Reality Gate and must not be inferred from that
accelerated capability run.

The byte-identical first-run files are retained under
`docs/experiments/results/v1062_general_compact_first/`. The independent
`replay.json` is recomputed in CI without loading model weights or re-running
tools.

## Decision2

Source: docs/research/decision2_first_actual_result_2026-10-03.md
SHA256: 3f2d5732bd94c4bc0ef4c746a31539d826e5f50071f6f10261ce522fe0fc5d46

### Decision 2 first actual accelerator result — retained FAIL

Date: 2026-10-03

### Frozen verdict

```
Decision 2 = FAIL
next = ARCHITECTURE_PIVOT
Decision 3 = BLOCKED
```

This verdict is retained exactly as produced by the preregistered evaluator.
It must not be relabeled as NOT_EVALUATED merely because the failure mode is
shared across all three arms.

Results:

| Arm | Successes | Model calls | Tool calls | Output tokens | Complete ms |
|---|---:|---:|---:|---:|---:|
| DIRECT | 0/12 | 24 | 0 | 6144 | 438365.942284 |
| TOOL | 0/12 | 24 | 0 | 6144 | 435523.924754 |
| NEUMANN | 0/12 | 24 | 0 | 6144 | 437706.011753 |

The strongest baseline under the frozen tie-break is TOOL. Because baseline
capability is zero, the architecture multiplier is undefined. NEUMANN's latency
ratio to that baseline is 1.0050102575.

### Interpretation boundary

This result falsifies the tested AM1 architecture:

```
free-form generative reasoning
  -> compact JSON control action
  -> tool / structural executor
```

under the frozen Gemma E2B, tasks and budgets.

It does **not** show that structural compression, structure discovery, executor
selection, or minimum-necessary-computation are globally false. Those
mechanisms were not exercised in this run because neither TOOL nor NEUMANN
entered an executor path.

Likewise, this result does not justify a favorable rerun with a larger token
budget, parser rescue, different prompt, hidden-thought extraction, or altered
PASS threshold. The one-shot Decision-2 result is final.

## Decision3

Source: docs/research/decision3_sealed_gate.md
SHA256: d6fd270f495bc26998043ec3774ed69b2f3f2586495b7dda66d897a552d21d79

### NEUMANN 1 — Decision 3 Sealed General Evaluation

Status: **PREREGISTERED / UNARMED / SEALED DATA UNOPENED.**

Decision 3 is prepared in advance so a positive Decision-2 result cannot trigger
post-hoc benchmark shopping, task cherry-picking, or a new answer-capable
architecture after seeing sealed data.

No gated task row, answer, rationale, frontier response, paid API call or new
training is opened by this preparation.

### Decision

Possible terminal states include:

- `PASS_ADMIT_EDGE_CLOUD_ENGINEERING`
- `FAIL_SEALED_MULTIPLIER_DID_NOT_PERSIST`
- `FAIL_FRONTIER_GAP_RECOVERY`
- `NOT_EVALUATED_NO_SUFFICIENT_VERIFIED_FRONTIER_GAP`
- `NOT_EVALUATED_FRONTIER_RESOURCE_SIGNAL`
- infrastructure/provenance blockers.

Even PASS keeps global Q1-Q7 formally open. It authorizes the next engineering
surface; it does not turn one sealed case set into a universal claim.

## P1

Source: docs/research/control_plane_p1_first_result_2026-10-03.md
SHA256: bc39057163842d4abc1e60d2e25597d2959e2d2960d3115cce0b4100d6325bc2

### P1 first real non-generative controller result — retained FAIL

Date: 2026-10-03

### Frozen result

- Frozen head: `81d004cf91251ef523e734756548c6cd694ac54e`
- Model: `google/gemma-4-E2B-it` at revision `3e22461f65e89153144f8adb70e3b8c2cc9845a7`
- BF16, Tesla T4, frozen weights
- 12/12 opened public tasks complete
- 144 scoring rows, 72 forward calls
- generated calls: 0
- tool calls: 0
- accounting complete: true
- core audit unchanged: true
- replay integrity valid: true

Archive: `NEUMANN_P1_FIRST_EVIDENCE.zip`
- bytes: 22,762
- SHA-256: `38d489dde092e86eea6a9f2276bc15fcfa574c463e18ececf161037dfd95cb38`

Frozen verdict:

```
P1 = FAIL
reason = DEGENERATE_ROUTE_SELECTION
P2 admitted = false
Decision 3 admitted = false
```

Winner counts are ARITHMETIC 12, DIRECT 0, CSP 0, PYTHON 0. This is a valid
first result and must not be rescued by changing labels, thresholds or rerunning
the same P1.

### Post-result diagnosis

The candidate verbalizers are not tokenization matched:

- DIRECT: one token, 35357
- ARITHMETIC: four tokens, 1425 / 13655 / 54849 / 2011
- CSP: one token, 210396
- PYTHON: one token, 185267

P1 used mean per-token log likelihood. That removes a simple summed-length
penalty but does not remove verbalizer/tokenization prior. The route prompt also
does not provide an explicit legend binding each candidate string to an executor
contract.

There is nevertheless context-sensitive movement below the dominant offset:
math has ARITHMETIC first on 4/4, code has PYTHON second on 4/4, and planning
has CSP second on 3/4. Mean PYTHON-minus-ARITHMETIC changes from about -11.08
nats on math to -7.22 on code; mean CSP-minus-ARITHMETIC changes from about
-14.83 on math to -7.21 on planning.

As an explicitly post-hoc diagnostic only, subtracting each route's mean across
these same twelve tasks yields PYTHON on all four coding tasks, CSP on all four
planning tasks, and a DIRECT/ARITHMETIC 2/2 split on math. This is not
confirmatory evidence, not a P1 rescue, and not grounds to admit P2.

### Next architecture candidate

Do not merely rename the bare labels. The next opened-development controller
should remove arbitrary verbalizer identity from the routing statistic.

A principled candidate is permutation-marginalized coded choice:

1. include an explicit semantic legend for the four executor contracts;
2. use four neutral single-token codes;
3. rotate route-to-code mapping through a balanced deterministic permutation set;
4. teacher-force only the code token, with no generation;
5. aggregate each route after it has occupied every code equally.

For balanced permutations π_k:

```
S(route | x) = mean_k log P(code_{π_k(route)} | x, legend_{π_k})
```

A fixed additive code-token prior then cancels by construction rather than being
estimated from task labels. Any such change is a new architecture version and
requires a new preregistered opened-development diagnostic, followed by fresh
opened validation before P2. P2 and Decision 3 remain blocked.

## P1.1

Source: docs/research/control_plane_p11_first_result_2026-10-04.md
SHA256: 0638e78e0eb394d9b003cb16aa87e17baa7ff7985d40b4fb3126593d8e811804

### P1.1 first actual balanced-coded controller result — retained FAIL

Date: 2026-10-04

### Frozen verdict

```
P1.1 = FAIL
reason = NUMERIC_OR_PERMUTATION_INSTABILITY
P2 admitted = false
Decision 3 admitted = false
fresh validation registered = false
```

The run is complete and accounting-complete. It is not a setup failure.

### Recommended next architecture candidate

A clean next development revision is a **fully permutation-marginalized coded
router** over all 24 bijections between the four executor semantics and the
four frozen one-token codes:

```
S(r | x) = (1 / 24) * sum_{pi in S4}
           log P(code[pi(r)] | x, legend_pi)
```

This is stronger than choosing another favorable Latin subset. Averaging over
the complete permutation group makes the route statistic invariant to which
balanced schedule subset happened to be selected and marginalizes each route
over every code and every assignment of the other routes.

The current 12 tasks may be used only as opened development data for this
revision. A new preregistration must freeze:

- all 24 maps before scoring;
- exact tokenizer/model/runtime identity;
- complete controller cost and wall limits;
- batch/unbatched/reversed numerical checks;
- a decision-stability diagnostic that is specified before the new run;
- no P2 or Decision 3 admission from development;
- fresh opened validation still created only after architecture freeze.

Do not rerun P1.1. Preserve this result as the immutable first actual P1.1
outcome.

Q1–Q7 remain globally OPEN.

## P1.2-dev

Source: docs/research/control_plane_p12_first_result_2026-10-04.md
SHA256: df0c3efc3443fa4d0ac1289ad79e90091f3617998abd1da6d1291661e82ff102

### P1.2 first actual full-S4 controller result — retained development PASS

Date: 2026-10-04

### Frozen development verdict

```
P1.2 = PASS
reason = DEVELOPMENT_DIAGNOSTIC_ONLY
P2 admitted = false
Decision 3 admitted = false
fresh validation registered = false
next = FREEZE_ARCHITECTURE_THEN_REGISTER_FRESH_OPENED_VALIDATION
```

The PASS is only the preregistered opened-development gate. It is not a
capability, efficiency, unseen-generalization, frontier-gap, P2, Decision-3 or
global-Q result.

### Interpretation

The progression is now:

```
P1   FAIL  bare verbalizer collapsed to ARITHMETIC 12/12
P1.1 FAIL  semantic winners recovered but 8-map subset score geometry unstable
P1.2 PASS  full-S4 mean robust to every registered balanced leave-4-out orbit
```

This is evidence that full permutation marginalization is a viable controller
representation on the opened development set. It is not evidence yet that the
same routing behavior generalizes to unseen tasks or improves end-to-end
capability/cost.

### Required next step

Freeze P1.2 unchanged. Do not tune it further on the original twelve.

Then register a **fresh opened validation** before viewing any new scores:

1. new task identities and source/provenance hashes;
2. explicit deduplication against P1/P1.1/P1.2 development inputs;
3. original independent answer/checker authority;
4. unchanged P1.2 model/tokenizer/codes/all-24 statistic and robustness rules;
5. complete controller and later executor/verifier cost accounting;
6. first-result retention with no favorable rerun;
7. validation PASS may admit P2 registration only, never Decision 3 directly.

P2 and Decision 3 remain BLOCKED. Q1–Q7 remain globally OPEN.

## P1.2-validation

Source: docs/research/control_plane_p12_validation_first_result_2026-10-04.md
SHA256: 8cdfe022cc8ca5812a63dadb7c99cebf2f59a17650a23b061825acbbb1bb43c8

### Frozen verdict

```
P1.2 fresh validation = FAIL
reason = TYPED_ROUTE_COMPATIBILITY_FAILURE
P2 registration admitted = false
P2 admitted = false
Decision 3 admitted = false
next = PRESERVE_FIRST_VALIDATION_FAILURE
```

This is a complete study, not a setup or numerical failure.

### Typed compatibility result

Frozen compatibility gate:

- >=10/12 overall
- >=3/4 in every domain

Observed:

```
overall               10/12  PASS
math_logic             4/4   PASS
coding                 4/4   PASS
constraint_planning    2/4   FAIL
```

Task-level result:

| task | registered compatible route | full24 winner | margin (nats) | max centered LOO20 delta | compatible |
|---|---|---|---:|---:|---|
| p12v_01 | ARITHMETIC | ARITHMETIC | 3.885742 | 0.112101 | yes |
| p12v_02 | ARITHMETIC | ARITHMETIC | 5.858073 | 0.154264 | yes |
| p12v_03 | ARITHMETIC | ARITHMETIC | 6.592122 | 0.154968 | yes |
| p12v_04 | ARITHMETIC | ARITHMETIC | 6.106771 | 0.141488 | yes |
| p12v_05 | PYTHON | PYTHON | 6.609721 | 0.064859 | yes |
| p12v_06 | PYTHON | PYTHON | 8.954102 | 0.111466 | yes |
| p12v_07 | PYTHON | PYTHON | 8.534261 | 0.097770 | yes |
| p12v_08 | PYTHON | PYTHON | 6.756299 | 0.091997 | yes |
| p12v_09 | CSP | **ARITHMETIC** | 0.614583 | 0.174674 | **no** |
| p12v_10 | CSP | CSP | 4.184896 | 0.197030 | yes |
| p12v_11 | CSP | CSP | 1.617187 | 0.074609 | yes |
| p12v_12 | CSP | **ARITHMETIC** | 1.246094 | 0.101237 | **no** |

The two misses are not marginal numerical flips. Every registered LOO20
perturbation keeps the same wrong winner on both tasks.

For p12v_09:

```
ARITHMETIC -3.355686
CSP        -3.970270
PYTHON     -4.062717
DIRECT     -5.043186
```

For p12v_12:

```
ARITHMETIC -4.335712
DIRECT     -5.581806
PYTHON     -5.663837
CSP        -5.731545
```

Thus P1.2 full-S4 successfully stabilizes the statistic, but stabilization does
not guarantee that the statistic represents executor compatibility.

### Scientific interpretation

The progression is now:

```
P1        FAIL  bare verbalizer collapse
P1.1     FAIL  balanced schedules recover signal but score geometry unstable
P1.2 dev PASS  full-S4 statistic robust on opened development tasks
P1.2 val FAIL  robust statistic misroutes 2/4 fresh CSP tasks
```

This is an important distinction. The current failure is **semantic**, not
numerical or permutation instability.

It also exposes a first-principles inefficiency in the current experiment.
These interfaces already carry explicit public executor contracts:

- arithmetic rows expose `expression` + `bindings`
- coding rows expose `requirement` + `examples`
- constraint rows expose `domains` + `constraints`

For such unambiguous typed inputs, spending 24 permutations and 432 forwards
to infer an executor that the public interface contract can determine
deterministically is unnecessary computation.

This observation does **not** rescue the failed validation. It is a
post-failure architecture diagnosis and any replacement architecture requires a
new preregistration and new fresh validation.

### Recommended next architecture pivot

Do not tune code tokens, margins or the old twelve/fresh twelve.

Candidate: **contract-first hierarchical routing**.

```
public problem
    |
    v
deterministic executor-admissibility test
    |-- exactly one typed executor is admissible --> execute it directly
    |                                      (zero neural routing forwards)
    |
    |-- ambiguous / untyped / multiple admissible
                                           --> semantic fallback router
                                               --> cheapest safe executor
                                               --> original verifier
```

The deterministic layer must use executor interface contracts, never hidden
family labels or private references. P1.2 full-S4 can remain an expensive
diagnostic/fallback baseline, not the default typed router.

The current 24 opened tasks may now be used only for development/diagnosis.
Any revised router needs a new fresh validation frozen before new scores. A
future P2 should include a genuinely ambiguous/generic stratum so a trivial
schema dispatch cannot by itself establish the end-to-end NEUMANN claim.

P2 registration, P2 actual admission and Decision 3 remain BLOCKED.
Q1-Q7 remain globally OPEN.

## P1.3

Source: docs/research/control_plane_p13.md
SHA256: 36cbfffdc215865c801e89d89ffe9fe2056a101ad475770b9225f3a89c9fcdb7

### Problem and hypothesis

The first P1.2 fresh result remains FAIL / TYPED_ROUTE_COMPATIBILITY_FAILURE:
10/12 compatible, planning 2/4; p12v_09 and p12v_12 select ARITHMETIC stably
although their public representation is a CSP contract. Original ZIP SHA256
362b13d7d7006ea1c55ad33788acd11d1712e94c081d59d52b28581d3abe3444.
Stability gates passed on that registered set. This does not establish global
stability, semantic correctness, capability, economic routing or Q1-Q7.

Hypothesis: if one public representation satisfies exactly one supported
executor interface, derive its route without model work. The invariant is
SelectedRoute in AdmissibleRoutes(original public input). The arithmetic,
Python and CSP tools and the original verifier remain unchanged.

### Next capability interface

Before P2, register genuinely ambiguous/generic problems and an obligation-
preserving representation path. Validate real fallback behavior on new problems;
do not count abstentions as solved capability. DIRECT, full-input TOOL and
NEUMANN must share the same deterministic type-admission layer, tools, frozen
weights and context cap. Only certified evidence elimination, computation
allocation and original verification can differentiate NEUMANN. Coding still
needs real generated source; answering still needs a strong normal DIRECT path.
Complete discovery+execution+verification+retry+routing costs decide Q5.

Each iteration retains one hypothesis, one preregistered gate and one first
result. Current work packages: contract/P0, new CPU interface diagnostic, then
new semantic representation/fallback validation, then matched capability/cost.
No date or GPU-runtime estimate is asserted for the latter two packages.

## P1.4

Source: docs/research/control_plane_p14_first_result_2026-10-04.md
SHA256: 4532f1827883fc63dde31d6164ba1360f2b7297a2adfd2448f033b9ca3de0091

### P1.4 first actual semantic-development result — retained FAIL

Date: 2026-10-04

### Frozen first-result verdict

The actual experiment completed all 12 observations. Its frozen evaluator wrote:

```
P1.4 = FAIL
reason = RAW_ACCOUNTING_INCOMPLETE
P2 registration admitted = false
P2 admitted = false
Decision 3 admitted = false
```

The outer Kaggle bootstrap reported `FAILED_OR_INTERRUPTED` only because the subsequent **model-free replay process failed**. This does not mean the model experiment was partial: `report.json` is COMPLETE, `observations=12`, `error=null`, and `terminal.json` records `complete=true`, `decision=FAIL`.

The first result is not rerun or replaced.

### Mixed typed fallback result

All four mixed typed tasks passed the original verifier:

```
p14d_09 -> ARITHMETIC -> ACCEPTED
p14d_10 -> ARITHMETIC -> ACCEPTED
p14d_11 -> CSP        -> ACCEPTED
p14d_12 -> CSP        -> ACCEPTED
```

Each fallback used 36 neural forward calls, for 144 total. All six registered LOO winners were stable on all four tasks. Worst observed:

- numeric batch/order delta: `4.76837158203125e-07` nats
- centered full24/LOO20 sensitivity: `0.1659505218075843` nats
- minimum full24 winner margin: `1.2057291658517593` nats

Thus the mixed masked-full-S4 path worked on this opened development diagnostic, although it remains expensive and does not establish economic advantage.

### Scientific interpretation

The progression is now:

```
P1       FAIL  verbalizer prior collapse
P1.1    FAIL  subset permutation interaction
P1.2dev PASS  full-S4 representation stability on opened development
P1.2val FAIL  stable semantic compatibility error on typed CSP
P1.3    PASS  deterministic contract-first typed dispatch, zero neural forwards
P1.4    FAIL  raw semantic representation construction
```

P1.4 gives a sharper localization:

1. **route-family identification is not the current raw bottleneck** on these eight items; all eight proposals chose the intended ARITHMETIC/CSP family.
2. **surface-valid executable IR construction is the bottleneck**:
   - exact arithmetic sequencing can be semantically changed by ordinary expression generation;
   - equivalent numeric surface forms can violate a strict exact grammar;
   - constraint relations can drift from the registered IR syntax.
3. The original verifier correctly rejects semantic mistakes, and P1.3 correctly rejects malformed typed representations.
4. Therefore simply retrying the same free-form JSON generator is not the preferred next step.

### Next architecture candidate

The next candidate should move one layer further toward NEUMANN's structural thesis:

```
raw language
    ↓
semantic sketch / typed atoms
    ↓
deterministic canonical compiler
    ↓
P1.3 admissibility
    ↓
specialist executor
    ↓
original verifier
```

The model should identify **minimal semantic structure**, not write the final executable expression/constraint JSON freely when deterministic compilation can guarantee representation validity.

A new version must be preregistered on new opened development inputs before model scores. The current P1.4 twelve are now opened diagnostic evidence. P1.4 is not rerun.

P2 registration remains BLOCKED.
P2 actual remains BLOCKED.
Decision 3 remains BLOCKED.
Q1-Q7 remain globally OPEN.

## P1.5

Source: docs/research/control_plane_p15_first_result_2026-10-04.md
SHA256: 7040f8a2357cf11ea3d6f3a99eba84423270210255562572f95de3b33ed339de

### P1.5 first actual typed-sketch result — retained FAIL

Date: 2026-10-04

### Frozen result

The first actual P1.5 study completed all eight registered obligations and the independent model-free replay passed.

```
study status = COMPLETE
observations = 8/8
P1.5 verdict = FAIL
reason = SEMANTIC_PATH_CAPABILITY_FAILURE

raw semantic accepted = 4/8
raw arithmetic accepted = 4/4
raw CSP accepted = 0/4

P2 registration admitted = false
P2 actual admitted = false
Decision 3 admitted = false
```

This is a clean capability FAIL, not an accounting, replay, identity or infrastructure failure.

### Task-level result

| task | domain | raw learned sketch | result | failure locus |
|---|---|---|---|---|
| p15d_01 | arithmetic | `START 30 /5 -2 *9` | ACCEPTED | none |
| p15d_02 | arithmetic | `START 17 +7 /3 -5/2` | ACCEPTED | none |
| p15d_03 | arithmetic | `START 19 -7 +1/4 /7` | ACCEPTED | none |
| p15d_04 | arithmetic | `START 6 *4 /8 -3/2` | ACCEPTED | none |
| p15d_05 | CSP | bare assignments + prefix relations | FAILED | strict sketch parser: unsupported CSP atom |
| p15d_06 | CSP | bare domains + infix word relations | FAILED | strict sketch parser: unsupported CSP atom |
| p15d_07 | CSP | brace domains + symbolic infix relations | FAILED | strict sketch parser: unsupported CSP atom |
| p15d_08 | CSP | brace domains + symbolic infix relations | FAILED | strict sketch parser: unsupported CSP atom |

All four arithmetic items compiled to exact nested Fraction expressions and passed the original verifier:

```
p15d_01 -> 36
p15d_02 -> 11/2
p15d_03 -> 7/4
p15d_04 -> 3/2
```

This directly removes the P1.4 failure modes that motivated P1.5 on the new opened arithmetic set: sequential operation scope is preserved, rational literals remain exact, and executable expression syntax is deterministic.

All four CSP items failed **before canonical compilation, specialist execution or original verification**. Their records have:

```
proposal = null
selected_route = null
tool_calls = 0
verifier_calls = 0
accounting_complete = true
semantic_budget_valid = true
error = ValueError: unsupported CSP atom
```

Therefore the frozen 0/4 CSP result does not show that the deterministic CSP compiler produced wrong IR. The strict P1.5 wire parser never admitted a CSP sketch.

### Candidate next architecture, not preregistered here

The next candidate should explicitly separate **semantic hypothesis** from **surface normalization**.

One possible P1.6 shape:

```
raw language
    ↓
bounded semantic hypothesis
    ↓
deterministic ambiguity-rejecting surface normalizer
    ↓
typed atoms
    ↓
canonical compiler
    ↓
P1.3 admission
    ↓
specialist
    ↓
original verifier
```

The normalizer may canonicalize predeclared equivalent notation classes, for example prefix/infix relation notation and brace/space domain notation. It must not infer omitted facts from the original query, repair a failed candidate, add relations, expand domains, reverse operands, or retry the model. Any semantic narrowing remains the model's charged hypothesis and is accepted only through the original verifier.

A stronger future option is constrained decoding or anchored/coded semantic choices so the model never spends probability mass on deterministic syntax at all. This should be evaluated against complete cost before adoption.

Because P1.5 outputs are now opened, they may be used only for diagnosis and architecture design, never as fresh confirmatory evidence.

## P1.6

Source: docs/research/control_plane_p16_first_result_2026-10-04.md
SHA256: 699e07f2d6d152f9e79281aca0b8f780b3869631e694ec1a9aa7bb34baff563c

### P1.6 first actual semantic-surface result — retained FAIL

Date: 2026-10-04

### Frozen result

The first actual P1.6 study completed all eight registered obligations and the model-free replay passed.

```
study status = COMPLETE
observations = 8/8
P1.6 verdict = FAIL
reason = SEMANTIC_PATH_CAPABILITY_FAILURE

raw semantic accepted = 1/8
raw arithmetic accepted = 0/4
raw CSP accepted = 1/4

P2 registration admitted = false
P2 actual admitted = false
Decision 3 admitted = false
```

This is a clean capability FAIL. It is not an accounting, identity, timeout, replay, or packaging failure.

### Task-level result

| task | domain | status | accepted | immediate failure locus |
|---|---|---|---|---|
| p16d_01 | arithmetic | FAILED | false | generated comma-separated single-line hypothesis; exact header/END framing rejected |
| p16d_02 | arithmetic | FAILED | false | same framing failure; generated content also contains a wrong/ambiguous divisor |
| p16d_03 | arithmetic | FAILED | false | generated comma-separated single-line hypothesis; exact header/END framing rejected |
| p16d_04 | arithmetic | FAILED | false | same framing failure; generated content also contains an ambiguous/wrong divisor expression |
| p16d_05 | CSP | FAILED | false | generated comma-separated single-line hypothesis; exact header/END framing rejected |
| p16d_06 | CSP | FAILED | false | generated comma-separated single-line hypothesis; exact header/END framing rejected |
| p16d_07 | CSP | FAILED | false | first line is comma-packed and followed by a candidate-assignment suffix; framing rejected |
| p16d_08 | CSP | ACCEPTED | true | normalizer -> P1.5 compiler -> P1.3 -> solver -> original verifier all succeeded |

Seven of eight failures stop in `normalize_hypothesis` with:

```
ValueError: exact hypothesis header and END required
```

They therefore have `proposal=null`, `selected_route=null`, `tool_calls=0`, and `verifier_calls=0`.

The one admitted item, p16d_08, normalized:

```
CSP
D { -3, -2, -1, 0 }
E { -3, -2, -1, 0 }
D < E
E = -1
D != -2
END
```

to the canonical P1.5 wire and produced the original-valid answer `{"D":-3,"E":-1}`.

### Scientific interpretation

P1.6 shows two distinct residual failure classes.

## P1.7

Source: docs/research/control_plane_p17_first_result_2026-10-05.md
SHA256: 8799ed1c562dff0025594f4e079b96713db41800edcfbc7b367185e58c32238f

### P1.7 first actual source-bound development result — retained FAIL

Date: 2026-10-05

### Frozen study result

The actual study completed all 12 registered obligations:

```
study status = COMPLETE
observations = 12
core unchanged = true
report error = null

P1.7 verdict = FAIL
reason = TASK_WALL_CAP

P2 registration admitted = false
P2 actual admitted = false
Decision 3 admitted = false
```

The outer bootstrap reported `FAILED_OR_INTERRUPTED` only because the subsequent model-free replay process exited nonzero. That replay failure is secondary and does not change the frozen study verdict.

### Strong positive result: unique source-bound path

All eight unique obligations passed end to end with **zero model calls and zero neural forward calls**:

```
p17d_01 arithmetic  ACCEPTED  model_calls=0  forwards=0
p17d_02 arithmetic  ACCEPTED  model_calls=0  forwards=0
p17d_03 arithmetic  ACCEPTED  model_calls=0  forwards=0
p17d_04 arithmetic  ACCEPTED  model_calls=0  forwards=0
p17d_05 CSP         ACCEPTED  model_calls=0  forwards=0
p17d_06 CSP         ACCEPTED  model_calls=0  forwards=0
p17d_07 CSP         ACCEPTED  model_calls=0  forwards=0
p17d_08 CSP         ACCEPTED  model_calls=0  forwards=0
```

Each reached the specialist and independent original verifier:

- tool calls: 8
- verifier calls: 8
- accepted: 8/8

This is opened-development evidence that, inside the P1.7 bounded grammar, deterministic source-span evidence extraction plus exact compilation can eliminate neural control work entirely when interpretation is unique.

It does **not** establish open-set/general semantic competence, P2 readiness, or global Q1-Q7 closure.

### Scientific interpretation

P1.7 materially changes the localization of the problem.

Previous failures were dominated by generated representation syntax and regenerated operand drift. P1.7's source-bound deterministic path removes those failure modes on all eight unique opened obligations:

```
source evidence
-> complete bounded interpretation
-> exact compiler
-> specialist
-> original verifier
```

with neural work = 0.

The remaining first-result bottleneck is now:

```
bounded ambiguity
-> expensive neural selector
```

rather than raw semantic serialization.

More importantly, the four registered ambiguous tasks themselves expose an architectural inefficiency. Their public rule is to select the pronoun binding that makes the stated finite constraints jointly satisfiable. Candidate satisfiability can be tested deterministically from the candidate IR without private references or the original verifier.

Thus the cheapest safe cascade should test deterministic feasibility **before** invoking a neural selector:

```
source-bound candidate set
        ↓
deterministic candidate feasibility pruning
        ↓
0 candidates -> reject
1 candidate  -> select with zero neural work
2..K viable  -> bounded neural choice only if ambiguity genuinely remains
        ↓
canonical compiler
        ↓
specialist
        ↓
independent original verifier
```

This is not a post-hoc rescue of P1.7. The P1.7 ambiguous tasks are opened and may only inform the next architecture.

A future fresh study should include both:
1. ambiguities that deterministic feasibility uniquely resolves, and
2. ambiguities where multiple candidates remain feasible and a neural semantic choice is genuinely necessary.

Otherwise a new benchmark would merely encode the answer into deterministic satisfiability.

## P1.8

Source: docs/research/control_plane_p18_first_result_2026-10-05.md
SHA256: 7d66b454df9d8351619f6130bd2bc2999a25c24719940e3b7f77725e93ad99e3

### P1.8 first actual opened-development result — retained FAIL

Date: 2026-10-05

This is a post-result retention note. It does not modify or reinterpret the frozen P1.8 source, registration, tasks, gates, model, runtime, or first-attempt evidence.

### Immutable first-result identity reported by the original Kaggle session

- archive: `NEUMANN_P18_FIRST_EVIDENCE.zip`
- bytes: `87,402`
- SHA-256: `a1545091f858d8b573183ea1b52157a8e52a677a2d5d85c51e41fe919e8239c8`
- frozen source head: `4e48320c2c67f15f8a41b0b4721caabd0c9b6df3`
- frozen bootstrap SHA-256: `19de12d24316b7122720404f0c4252f1b2c1fa3f179958e28e597ac75c18a49c`
- runner exit: `2`
- model-free replay exit: `0`
- study: `COMPLETE`, 8 observations, report error = null
- frozen verdict: **FAIL / CONTROL_WORK_ACCOUNTING_FAILURE**
- no favorable rerun or replacement

The archive bytes have not been independently ingested into this repository. The identity above is the original-session reported identity. The copied receipt bundle reports terminal complete=true, no_replacement=true, and model-free replay `integrity_valid=true`, `cost_replayed=true`.

### Aggregate first-result accounting

- model calls: 4
- neural forwards: 138
- generation: 0
- evaluated tokens: 257,088
- padded tokens: 257,088
- feasibility calls: 24
- feasibility nodes: 213
- feasibility constraint checks: 469
- tool calls: 5
- original-verifier calls: 5
- witness cache hits: 5
- selector startup: 154,144.665133 ms
- whole study: 856,605.532426 ms

The preregistered path required 144 B forwards and 8 tool/verifier calls. Because B02/B03/B04 did not reach admitted execution, aggregate control-work accounting was incomplete and the frozen evaluator correctly returned **CONTROL_WORK_ACCOUNTING_FAILURE** before the later capability gate.

### Research interpretation

P1.8 separates two claims that must remain distinct.

**Supported in this opened bounded mechanism:** deterministic feasibility can eliminate residual candidate ambiguity at zero neural cost when all but one source-bound candidate are proven impossible.

**Not supported:** the inherited 36-forward full-S4 residual semantic selector is a viable NEUMANN control mechanism. It is both expensive and, on the one clean completed semantic observation, wrong.

The important architecture lesson is therefore not to relax the wall again. P1.7 used 120 s and P1.8 prospectively used 180 s; two P1.8 receipts still completed just beyond 180 s and one did not finish. Increasing the cap again would preserve a diagnostic but move away from the NEUMANN objective.

The next development mechanism should instead reduce the residual semantic decision itself: fewer forward passes, fewer coded permutations, or a different bounded representation that removes arbitrary code-label effects without paying full-S4 cost. Any new mechanism must preserve source-bound evidence, feasibility pruning, no free numeric/entity regeneration, no hidden reference access, no generation retry, independent original verification, complete partial-work accounting, and first-result discipline.

P1.8 is not rerun or rescued. Fresh validation remains unregistered. P2 registration=false. P2 actual=false. Decision3=false. Q1-Q7 globally OPEN.

## P1.9

Source: docs/research/control_plane_p19_first_result_2026-10-05.md
SHA256: 5b2dfe643f90838732ad2444694226d1e505e8508a3d3266329f09cc8856f410

### P1.9 first actual opened-development result — retained FAIL

Date: 2026-10-05

This note retains the immutable first P1.9 result reported by the original Kaggle session. It does not rerun, rescue, replace or reinterpret the frozen historical verdict.

### Immutable first-result identity

- archive: `NEUMANN_P19_FIRST_EVIDENCE.zip`
- bytes: `66,795`
- SHA-256: `3493421fca63f1a2155a0ed21265a4f1b2c799f91cb20bcc0d1a57269ea9a759`
- frozen source head: `d5811f44a018e86660769ba9bebb542168ee97fd`
- bootstrap SHA-256: `a37e29f91a98d183e3f6906fd53643096eab2baae4a7bb5af034c3f1c8ee36a6`
- runner exit: `2`
- model-free replay exit: `0`
- study status: `COMPLETE`, 8 observations
- accounting complete: true
- frozen verdict: **FAIL / P19_SEMANTIC_CAPABILITY_FAILURE**
- no favorable rerun or replacement

The copied receipt bundle reports terminal complete=true, no_replacement=true and unchanged frozen-core identity.

### P1.10 development hypothesis

Prospective only, no P1.10 model score yet:

```
source-bound evidence
-> deterministic feasibility
-> one candidate: zero neural
-> multiple candidates:
     derive minimal semantic contrast IR
     {original semantic instruction, ambiguous mention, candidate source-bound entity bindings}
-> symmetric pairwise preference scoring
-> independent original verifier
```

For candidate pair i,j, score both orientations with fixed output semantics:

- A = LEFT binding is more faithful
- B = RIGHT binding is more faithful

Let

`L(i,j) = log P(A | i-left,j-right) - log P(B | i-left,j-right)`

and symmetrize:

`D(i,j) = (L(i,j) - L(j,i)) / 2`.

This removes a global A/B token preference and first-order left/right presentation bias. Candidate selection should be based on pairwise source-bound semantic contrast, not independent absolute FAITHFUL calibration.

P1.9's exact batch/unbatched/reverse equality on all eight tasks is development evidence that repeated per-candidate unbatched scoring is not buying useful numerical robustness on this frozen backend. A P1.10 P0 may therefore prospectively retain only two opposite batch-order passes while still failing closed on numerical drift.

P1.9 is never rerun or rescued. P1.9 tasks may be used only as model-free/synthetic regression fixtures for architecture construction. Any actual P1.10 score requires newly authored, independently checked and preregistered tasks.

Fresh validation remains unregistered. P2 registration=false. P2 actual=false. Decision3=false. Q1-Q7 globally OPEN.

## P1.10

Source: docs/research/control_plane_p110_first_interrupted_2026-10-05.md
SHA256: 7114dbd181157dfc82e1b48989eed0f226c207de6c293894d353ab15f417cbe6

### P1.10 first actual — interrupted first-result retention

Date: 2026-10-05

This note retains the first P1.10 actual attempt exactly as observed. It does not rerun, rescue, replace, or complete the interrupted study.

### Current next step

Read the six retained task receipts and the partial start marker without model inference or evidence mutation. Determine whether the minimal semantic contrast + symmetric pairwise mechanism showed useful partial signal before interruption. Any architectural change must be based on that retained partial evidence and prospective reasoning, not on selectively rerunning the same first attempt.

## P1.11

Source: docs/research/control_plane_p111_first_nonevaluated_2026-10-05.md
SHA256: c25a149e95f08e31af6a753ae67772bd6d65ae08d7f1f56df700b708eda87dbe

### P1.11 first actual — retained NOT_EVALUATED first result

Date: 2026-10-05

This note retains the immutable first P1.11 actual result exactly as reported by
the original Kaggle session. It does not rerun, rescue, replace, or reinterpret
the historical result.

### Immutable first-result identity

- archive: `NEUMANN_P111_FIRST_EVIDENCE.zip`
- bytes: `23,620`
- SHA-256: `d75aeeccbd54e5c96041a41f4c40c1df17a5504d44c026336c53fab2b247e5e0`
- frozen source head: `8094b4ea90fc48f4d3c0d8142ff378dbe73afc59`
- bootstrap SHA-256: `07d3f606ba9fe5beb9c79f4181e1525731a2699e9b77b361042158794ca120de`
- model artifact manifest SHA-256: `f961e60f6f7352d756e7addf8d7887be199c81facd2ae93950bc03d1e52d7292`
- setup status: `FINISHED_NONPASS`
- runner exit: `2`
- model-free replay exit: `0`
- development verdict: **NOT_EVALUATED**
- development_only: true
- no_replacement: true

The model-free replay succeeding means the retained receipts and historical
decision are internally replayable. It does **not** explain why the evaluator
returned NOT_EVALUATED.

### Historical interpretation boundary

P1.11 is not PASS and is not semantic-capability FAIL on the information above.
The frozen evaluator can return NOT_EVALUATED only before the normal cost and
capability gates, e.g. for incomplete/coverage drift or reference/core identity
drift. The exact frozen reason must be read from the retained `report.json`
before any diagnosis or next architecture decision.

No favorable rerun or replacement is permitted. The first archive remains the
historical first result.

Fresh validation remains unregistered. P2 registration=false. P2=false.
Decision3=false. Q1-Q7 globally OPEN. The North Star claim of overwhelming
iso-capability advantage/category change is not affected or established by this
result.

## P1.11.1

Source: docs/research/control_plane_p1111_first_fail_2026-10-05.md
SHA256: 146084296667362713a540a1df58a7388053ff835148cb50e8278ff92f33977d

### Interpretation boundary

The successful model-free replay establishes that the retained P1.11.1 receipt
set and terminal decision are replayable. The top-level output alone does not
identify which frozen FAIL reason fired.

Do not yet classify this as semantic-capability failure, cost failure, timing
failure, accounting failure, or control-path drift until the retained
`report.json` and task receipts are read.

No favorable rerun or replacement is permitted.

Fresh validation remains unregistered. P2 registration=false. P2=false.
Decision3=false. Q1-Q7 globally OPEN. The North Star claim of overwhelming
iso-capability advantage plus category change is not established by this result.

## P1.12

Source: docs/research/control_plane_p112_development_2026-10-06.md
SHA256: b570cbc0c697d1b609d19c4bb84c9787f5a1e02230bb85f458e360735eac643e

## P1.13

Source: docs/research/control_plane_p113_paired_2026-10-06.md
SHA256: 05be63e6788b39021f5ed3fbd737d47e438fa1a161912ac6ba545f56d51494ee

## G0-Graph-SPD

Source: docs/research/g0_first_2026-10-06.md
SHA256: 71976504a878e0aafef9c94cf5f0cd1de0f4f9513fd46d569f81b3567a1e99f2

### Decision and next architecture compression

Do not train a neural true-twin selector or low-rank selector on this evidence.
Keep their cheap deterministic implementations as building blocks and strong
comparators. No new Gemma/MiniLM/model-size swap is justified by this outcome.

One prospective core remains: **cost-aware synthesis of composed representation
programs with explicit semantic preservation**, rather than selecting a single
known reduction. It must learn/generate bindings, compositions and reusable
abstraction definitions, reject false analogies, and beat symbolic search and a
fixed representation selector under matching permissions and investment budgets.
It is a hypothesis, NOT implemented learned LPS and NOT admitted to training.

The existing e-graph engine is reused for the symbolic comparator instead of
rewritten: `neumann1/perspective_symbolic_baseline.py`, egglog 14.0.0 MIT,
Windows wheel/native/library hashes and license in
`Continuation/EGRAPH_REUSE_PREPARATION`. It already accepts typed exact-integer
ASTs, generates/factors equivalent compositions, and checks equivalence under
declared ring axioms. Three correctness/negative-control tests pass; this is
baseline infrastructure only. Extracted tree size is NOT execution FLOPs or
proof of speedup. Floating-point ring rewrites are explicitly rejected.

[egglog](https://github.com/egraphs-good/egglog-python) supplies equality-saturation
infrastructure. [DreamCoder](https://arxiv.org/abs/2006.08381) and
[Stitch](https://github.com/mlb2251/stitch) already address learned abstractions
and program libraries; composition/library generation alone is not a novelty
claim. DreamCoder/Stitch were researched here, not installed or experimentally
outperformed. Future novelty and speed must be measured against relevant strong
implementations and the same original tasks.

Next mainline work: a new BEFORE-RUN contract for genuinely expensive composition
discovery, with original-goal checks, false-analogy controls and strong symbolic
optimization. No broad new dataset or GPU training until headroom is demonstrated.
G1/G2 remain unexecuted; old Decision3 remains sealed.

Reused primary implementations: [NetworkX weighted clique](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.clique.max_weight_clique.html),
[SciPy MILP](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html),
[LAPACK dpstrf](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.lapack.dpstrf.html),
[CG](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.cg.html).

## G0-Composed

Source: docs/research/g0_composition_2026-10-06.md
SHA256: 45d377c328857229d7f5caac13818e0520fc5966d1a886336566433c789bf365

## Polynomial-Representation

Source: docs/research/representation_generation_2026-10-07.md
SHA256: 6774bb9a49f6e384701e2f88cf3ae51e8d65f6681000c61b37974789f0fa789f

## Inductive-Complete-Cost

Source: docs/research/inductive_complete_cost_2026-10-07.md
SHA256: 0f69cde36e390c052972e8eabe4eb8d58cf0842ff4d0d086f1a342b0c7abaaad

## Recursive-Summary

Source: docs/research/recursive_summary_engineering_2026-10-07.md
SHA256: b7d49c0a5b1fbacd050a9406f559718f44362fb2968719970e7a87e21b34dc45

## Compressed-Recursive-Cost

Source: docs/research/compressed_recursive_cost_2026-10-07.md
SHA256: ce3b82a97e7aaeecf46e9bdb52f050c071fb01b8693f3daa3c3615e82016b088

## Symbolic-Decoder-OCaml

Source: docs/research/symbolic_decoder_source_binding_2026-10-07.md
SHA256: b46e8b407ca3de09c4997970ed3077ede23c998721a049edcfe7ccaf9febc51f

## Full-Synduce

Source: docs/research/full_synduce_baseline_2026-10-07.md
SHA256: 08f760734f6068ed6b52237de8222d2971c8091b4c9d56d2da5a5e1dd44ebd5a

## SuFu-Official-Tensors

Source: docs/research/sufu_and_official_tensors_2026-10-07.md
SHA256: 7c0154014ed06092826faff8025979bcab188e5924aefcfb9ade07af2a52d85a

## Perspective-Transfer

Source: docs/research/perspective_transfer_headroom_2026-10-07.md
SHA256: 6116d798f21f95c5a74e28825bedcfddbf7ddac97d8648b808f57dd59566e5ba

## Structural-Experience

Source: docs/research/structural_experience_2026-10-07.md
SHA256: 31331fcf8bf047ce4e02620f4275087ac70ac022c36020c3c2a401793ad9ba36

## Structural-Mechanism

Source: docs/research/structural_mechanism_screen_2026-10-06.md
SHA256: bdba4768612f10f63a2b81efccfe998b60b62bd52176672165338dc44ce96838

## REUSE-R0

Source: docs/research/reacomp_reuse_2026-10-06.md
SHA256: a805773fee43ce53fa8cd5894774c7c269eaa12d358af6be0a84f92852842238

## CODE-C0

Source: docs/research/code_gate_c0_2026-10-06.md
SHA256: 9c9f279a5a3f4204ca555001743f2a0ffc4c6050415938ff9caf950cf61ec7fb

## Guarded

Source: docs/research/guarded_perspective_2026-10-08.md
SHA256: 93c660209310b3f3781d2185b185857737694eb48d7016eb4f16fd742ae8a78b

### B. Scientific Hypothesis

초기 상태에서만 유효한 충분 표현은 전역 동등성에 실패할 수 있지만, 초기
조건과 귀납적 불변량에 의해 안전하게 승인될 수 있다. 반증 조건은 잘못된
초기값·전이·목표·증명 승수가 승인되거나, 원래 목표와 출력이 달라지거나,
UNKNOWN/변조된 제안이 실행되는 것이다. 기존 Universal 회귀도 실패다.

비용 질문은 이 engineering fixture에서 무료 유효 표현이 강한 공개 기호
방식에 큰 여유를 주는지다. 유효성 성공은 경제성 성공이 아니다.

### H. Next Decision

**HOLD**: 이 좌표·다항식 fixture 계열의 학습된 생성기에 투자하지 않는다.
검증기만 더 빨리 만드는 것으로 10×를 얻겠다는 후속 실험도 중단한다.
Guarded 기능과 반례는 재사용 가능한 Core/Fixture로 보존한다.

기존 G0 A(Storm 기반 goal-dependent probabilistic sufficient state),
B(D4/CPOG/Ganak 기반 certified Boolean counting circuit)는 그대로 유지한다.
실제 원래 목표를 보존하는 free 표현과 강한 같은 환경 baseline의 큰 비용
여유가 먼저 필요하다. B의 toolchain 준비가 과도하면 환경 상태를 기록하고
중단한다. 새 큰 IR·범용 prover·학습 모델·GPU pipeline을 만들지 않았다.
G1/G2 미진입, Decision 3 봉인 미접근, North Star/Q1–Q7 및 과거 판정 불변이다.

증거: [최초 비용 관측](guarded_fixture_probe_first_2026-10-08.json),
[독립 검증·원본 보존 감사](guarded_engineering_audit_2026-10-08.json),
`tests/test_guarded_perspective.py`. 원본 결과를 재실행으로 교체하지 않았다.

## Candidate-Compression

Source: docs/research/candidate_compression_2026-10-06.md
SHA256: 59713d5f12ebd4274364791738737f211705cb93ff7b532dfff74309164ae195

## AM1-local

Source: docs/research/am1_local_execution.md
SHA256: b37cb50c0b9d576604764ec61b21167e61cc6267928459c9bff21a911992ab54

## BP-Certificate-Economics

Source: docs/research/bp_certificate_diagnostic_2026-10-08.md
SHA256: 39ee0f9838f961aa6a9d4c431beacbaa04c954bcc53728fe68929bc27fe54d8c

### Opened BP certificate economics — v2.0 Phase 2 first result

**ENGINEERING PASS / NO REGISTERED TENFOLD HEADROOM / HOLD_LEARNING.**

이 판정은 아래16개 opened source와 등록한 실행·인증 방법에 한정된다.
v102 Q34 PASS, Q5/M106/Decision2 FAIL은 그대로다. 새 G0·G1·G2 성공,
학습된 표현 생성 또는 프런티어 성능을 입증한 결과가 아니다.

### B. Hypothesis and authority

목표: 원래 최적 support를 알면 dual을 무료로 받지 않고도 강한 Native보다
충분히 저렴하게 원래 문제를 풀 수 있는가? fixed2m/4m의 표현 제약과
full-goal certificate acquisition 비용을 구별한다.

이미 열린 M106 원본16개(k8/16/32/64각4개)를 그대로 읽었다. 재생성하거나
planted feasible support를 정답으로 사용하지 않았다. 원래 Native witness가
변경 없는 original verifier를 통과한 후 그 witness의 정확 nonzero support를
Oracle label로 사용했다. 유일한 최적 support라고 가정하지 않는다.

Nine routes,1warmup+3timed repeats=576관측. 독립 원본은16개이고 fresh는0개다.

- A: 기존 Highs primal simplex, SciPy highs-ipm, 고전적 explicit dual LP,
  SPGL1 BP+동일 sparse/KKT/dual repair. 모든 경로에 동일 목표 검증 권한.
- B: 두 frozen checkpoint의 **보존된 ranking**+기존2m->4m+full fallback.
  새 forward 없이 discovery를 무료로 준 LOWER BOUND. 실제 모델 총비용 아님.
- C: 정확 optimal support를 먼저 놓고 원래 column 순서로 padding한 ranking,
  기존2m->4m+fallback. optimal dual 없음.
- D: free support+sparse least-squares primal+minimum-norm KKT dual. 거절되면
  기존 HiGHS로 full original dual feasibility를 구한다. free dual 없음.
- E: D와 같은 sparse primal, free retained optimal dual. 낙관적 Oracle 진단.

각A variant의 모든 반복이 인증된 경우의 가장 빠른 비용을 원본별 envelope로
비교했다. 이 optimistic envelope는 실제로 무료 router를 배포했다는 뜻이 아니다.
실제로 이번16개에서는 기존A_NATIVE가 모두 가장 빨랐다. SPGL1도 실행·실패·
fallback을 보존했으며 사후에 비교군에서 삭제하지 않았다.

### D. First actual results

**576/576 final original-valid within5s**, 독립 original-goal replay576/576PASS.
새 model forward0, training0, new task generation0. CPU solver 호출은 이 별도
Phase2 계약에서 실행됐다. Phase1의 zero-solver audit와 구분한다.

아래는16 source별 median에 common startup/dependency setup을Q10000으로
상각한 operational cost의 **StrongNative / 경로** 기하평균이다.
1보다 작으면 해당 경로가 Native보다 비싸다. 전체 lifecycle cost는 UNKNOWN다.

| 경로 | 기하평균 | 10배 원본 | full Native fallback 요청 |
|---|---:|---:|---:|
| B frozen ranking seed100001, discovery free |0.6943×|0/16|60/64|
| B frozen ranking seed100002, discovery free |0.6978×|0/16|60/64|
| C free optimal support+old2m/4m |0.7254×|0/16|64/64|
| D free optimal support+paid original dual |0.4837×|0/16|0/64|
| E free optimal support+free optimal dual |4.0913×|0/16|0/64|

E의 원본별 최대 비율은7.5494×다. 등록 조건(전16개 능력 유지,
geomean>=10,13/16>=10)을 충족하지 못했다. D는 원래 문제의 유효한
certificate를 생성했지만 전체 비용은 약2.07배 높았다. E는 저렴하지만
원래 optimal dual을 무료로 공급한 진단이다.

### F. Causal decision and Phase 3

**HOLD_LEARNING**. 고정 support ranking의 refit,larger model,sparse executor를
저렴하게 만들기 위한 학습,새 P1변형에 투자하지 않는다. 확인한 사실은 이
표현·인증 어댑터에서 full-goal dual 획득이 실제 비용의 병목이라는 것이다.
모든 cheap certificate가 불가능하다는 증명으로 확대하지 않는다.

원래 goal을 보존하면서 optimal dual을 무료로 제공해도 등록 operational10배에
미달했다. D와C 모두 Native를 전체에서 능가하지 못하므로 v2.0의 중단 규칙을
적용한다. **Phase3 architecture change를 시작하지 않는다.** variable-cardinality,
relational model,learned certificate generation,compute-aware neural policy를
동시에 구현하지 않는다. IR/verifier/native/guarded/structural experience를 유지한다.

G0후보A/B는 별도의 기존 후보로 유지하며 학습 허가로 바꾸지 않는다. Counting의
INCOMPLETE도 유지한다. Q1–Q7과Decision3/v098/v107 봉인도 그대로다. 이번
반례와 비용은 opened diagnostic experience이며 fresh 평가나576개 독립 학습
문제가 아니다. 더 강한 계산 원리의 추가 근거가 나오기 전까지 같은 계열의
성능 재시도와 새 모델 교체는HOLD한다.

## G0-Probabilistic-Native

Source: docs/research/g0_probabilistic_native_2026-10-08.md
SHA256: ffb0f231848582c1e9a8b721123713894b5de96d6f511256446e2cc955936cf1

### Frozen question, sources and comparison rights

Can an exact free goal-preserving quotient leave tenfold discovery/execution
headroom against strong tested native methods, with equal reuse rights?
Before performance measurement, a cost-blind rule selected 13 public requests
from 9 QVBS families and 11 unique JANI files. Some source files are reused with
different parameters. Formats and repeats are not independent problems; these
are opened development requests, not 13 fresh independent evaluations.

Pinned [QVBS source](https://github.com/ahartmanns/qcomp/tree/c7324a311475ba1a3f40e36a324e32f91e766540/benchmarks/dtmc)
is commit `c7324a311475ba1a3f40e36a324e32f91e766540`, CC-BY4.0. Existing authors and
model metadata are preserved. Sparse exact/default and topological, rational
bisimulation, and symbolic DD-to-sparse paths were tested in Stormpy1.14.0.
Both original PRISM and JANI were allowed when supported; Coupon was JANI-only
because its original PGCL compiler was absent. This is a limitation, not an
equivalent full native coverage claim.

The free arm gets the quotient already built by Native, then actually solves
it. Native can reuse that SAME compiled quotient and also solves it again.
Neither arm reads an answer cache. Exact Fraction outputs are compared with
public parent-only exact references; the worker cannot read those references.
All initial values or the original maximum over them are retained. Trust is
the existing Storm implementation and exact checker, not a new independent
proof checker for arbitrary quotient programs.

Three conditions were frozen: first cold request, resident process with a newly
parsed/rebuilt request, and repeated solve of the same compiled quotient.
Each path has one cold and three fresh resident requests; compiled arms each
have one warmup and three measured solves. One worker, numerical thread1,
75s/job, 8GiB virtual address limit, free Kaggle CPU4, Python3.13.15/Linux.
The positive rule requires both fixed size bins and at least10x geometric
optimistic resident-new-request advantage. Singletons cannot pass a family.
No such flag would automatically admit learning.

### Stronger source-level controls and decision

Subsequent source-only review derived exact classical controls for Coupon,
EGL and both Crowds requests, and bound the published Herman15 maximum theorem
to its source. Five original exact outputs agree; transition/goal/property/
parameter mutations are refused.10 engineering tests passed. No analytic-control
performance measurement or machine-formal source proof was performed.
[Proof scope and engineering evidence](probabilistic_analytic_controls_2026-10-08.md).

These controls expose gaps in a Storm-only strongest-comparator claim. They do
not change the first screen's costs or verdict, nor establish a numerical global
no-headroom theorem. The large singleton warm floors and the large Crowds cell
do not supply learning admission while cheaper applicable goal-specific native
methods remain unmeasured and no independent structural transfer is tested.

**HOLD_LEARNING** for the tested acquisition/reuse setting. No G0 family PASS,
no GPU, learned generator, G1/G2 or sealed evaluation. The existing G0 B counting
cohort remains separately INCOMPLETE12/17 with its first timeouts preserved.
Other probabilistic abstraction families are not ruled out by this diagnostic.

Evidence: local `Continuation/G0_PROBABILISTIC_2026-10-08/` retains contract,
first source selection, runner,125 raw jobs, export, failed audit attempt,
independent analysis and session-stop screenshot. Portable derivatives are
`research/audit/G0_PROBABILISTIC_NATIVE_ANALYSIS.json/.csv`. Contract SHA256:
`9694bd5031d6a08e265d112922eeb67c3e3bd72ea51bf4c4beaf2082bea05a1c`;
runner SHA256:`102c647cb82b1b498dc667c8befb35375bb680cec36349b45873e6a83c3cb303`.
Kaggle CPU session was stopped after export. New work remains local; GitHub
CI belongs to the unchanged existing PR HEAD, not these local additions.

## Probabilistic-Analytic-Controls

Source: docs/research/probabilistic_analytic_controls_2026-10-08.md
SHA256: b46a21f538335f8c93d21f3cace7d186fe4b5181dccd212ee0ebbb4c7e88797e

### Trust, economics and next decision

Trust consists of the published Herman theorem, manually inspected program
semantics, exact Fraction arithmetic, and the source hash binding. No formal
machine proof of these source abstractions was executed. Exact arithmetic and
agreement with retained Native outputs are engineering evidence; they do not
replace that missing formal proof or establish independent generalization.

Coupon and EGL were the first screen's strongest singleton optimistic warm
floors (22.55x and53.09x against its Storm portfolio). Crowds large showed16.21x,
but its registered two-size geometric mean was9.678x and failed the10x criterion.
All three have simpler applicable classical goal-specific methods. Herman15's
Storm timeouts likewise do not establish a native capability gap.
Operational timing of these analytic controls, full source-proof acquisition,
energy, memory and lifecycle costs have **not** been measured. Therefore this
report does not numerically replace any first ratio or claim a new no-headroom
theorem. It removes Storm-only gaps as sufficient grounds for learning admission.

10 engineering tests passed in0.023s: exact arithmetic, original outputs,
transition/goal/property/parameter mutations, rejected N7 bound, and caller
verdict rejection. Test suite wall time is not a performance benchmark. First
7-test code/receipt are retained separately, followed by the hardening and
Crowds contract. No GPU, new solver or model forward was used. **No G1/G2.**

Pinned QVBS source: [c7324a3 DTMC benchmarks](https://github.com/ahartmanns/qcomp/tree/c7324a311475ba1a3f40e36a324e32f91e766540/benchmarks/dtmc).
Portable original fixtures and negative tests are in
`tests/fixtures/probabilistic_native_controls` and
`tests/test_probabilistic_analytic_controls.py`. The four original source-pair
hashes are explicit in `SOURCE_PINS`; no original evidence was modified.

## Notion-⚙️ Engineering Track _ NEUMANN Core v0.0.1

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\⚙️ Engineering Track _ NEUMANN Core v0.0.1 -- 3e67830ff334815dabc5d96e1edb6fcd.md
SHA256: 4cb6f1964a34f3741dcf99acf423d09b767b87a55f0ca7d5b4c646ef00172e48

### 4. Test result

Command: `pytest -q`
Result:
**6 PASS / 0 FAIL**
Covered cases:
1. satellite-slot assignment → matching
2. employee-job assignment → same structural solver under different surface semantics
3. shortest path → Dijkstra
4. linear equations → Gaussian elimination
5. UNKNOWN representation → fail closed
6. low-confidence representation → fail closed

### 6. First engineering research finding

v0.0.1에서 이미 다음 원칙이 경험적으로 드러남:
> **A better solver is not enough. Representation formation and verification overhead can erase the gain.**
따라서 장기 router objective는 단순 solver accuracy가 아니라:
$$
m^*=\arg\min_m C_{total}(m,x)
$$
subject to:
$$
Correctness(m,x)\ge A_{required}
$$
이며:
$$
C_{total}=C_{repr}+C_{route}+C_{solve}+C_{verify}+C_{recovery}
$$
로 측정해야 한다.

### 8. Next engineering milestone — v0.0.2

1. benchmark runner를 정식 metric contract로 확장
2. wall-clock timing 추가
3. baseline interface 추가
4. representation overhead를 별도 측정
5. solver execution overhead 분리
6. verifier overhead 분리
7. hard-negative / wrong-IR test 추가
8. wrong representation이 verification에서 차단되는지 테스트
9. 이후에만 첫 model-backed Structure Former adapter를 연결

## Notion-📐 Annotation Schema v0.1 _ Structural Equivalence

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\📐 Annotation Schema v0.1 _ Structural Equivalence -- 3e67830ff3348161b87bf7e9a3c2f8aa.md
SHA256: 0a10e836620d6f2f10db8c2c51fdcc9909fc12e1fc259a2f89bc46d224310abb

### 14. Decision rule after pilot

**PASS:** Level S/P 각각 κ ≥ 0.60이고 disagreement가 소수의 명시 가능한 boundary rule로 설명됨.
**MODIFY:** κ \< 0.60이지만 원인이 granularity/annotation rule로 국소화됨.
**KILL CURRENT DEFINITION:** 반복 수정에도 구조 동일성 판단이 안정화되지 않음.

### 15. Result record template

```plain text
Date:
Schema version:
Candidate registry version:
N included:
N excluded/replaced:
κ Level S:
κ Level P:
Raw agreement:
Same-pair agreement:
Different-pair agreement:
UNCERTAIN rate:
Top disagreement categories:
Decision: PASS / MODIFY / KILL
Next action:
```

## Notion-🧠 NEUMANN 1 _ Structural Intelligence Research

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🧠 NEUMANN 1 _ Structural Intelligence Research -- 3e67830ff33481248c61f279712953fb.md
SHA256: c6a6dae2a513e97961dae188e082c424c2158293cef544a2909dc57c919fda87

### Latest restart checkpoint — P1.8 latent diagnosis closes “timing-only” hypothesis; P1.9 P0 opened · 2026-10-05

**Post-hoc read-only diagnosis:** P1.8 history unchanged. B01 expected1 but latent full-S4 choice0 with stable1.013020835-nat eligible margin. B02 raw eligible winner1 (correct direction) but margin0.228515626\< frozen0.5, so even without the180s wall the frozen selector would abstain/fail. B03 incomplete30/36 forwards, no latent choice. B04 expected1 but latent choice0 with stable5.178629555-nat margin. Therefore P1.8 B was not a timing-only failure: among three complete matrices, two strongly/stably prefer the wrong semantic candidate and one is too weak for the preregistered confidence gate.
**Architecture consequence:** do not relax the full-S4 wall again. Candidate-slot A/B/C/D permutation is now a likely representation/control liability, not just a cost liability.
**P1.9 P0:** PR155 opened as a stacked prospective architecture. Retain source-bound extraction + deterministic feasibility; if2+ candidates remain, score each candidate independently under fixed output semantics A=FAITHFUL, B=NOT_FAITHFUL. Candidate identity exists only in the prompt; candidate/code permutations=0. Stability modes=batch-all, unbatched1, reverse-batch-all. Planned forward count per item=k+2. For the P1.8 B shape2/3/4/3 this is20 forwards rather than144 (planned count only, not measured performance).
**P1.9 guards:** cross-mode log-odds drift\<=0.05nats; selected candidate must have nonnegative faithful-vs-not log odds; top-vs-second margin\>0.5nats; all modes same winner; generation/retry hidden reference access forbidden. Machine-readable contract and dedicated CPU CI added. No actual P1.9 Gemma score or new development registration yet.
**Boundary:** P1.8 permanent FAIL and no rerun/rescue. P2 registration=false;P2=false;Decision3=false;Q1-Q7 globally OPEN.

### Historical checkpoint — P1.2 bootstrap publication before its first real result · 2026-10-04

The NOT RUN and next-action statements below record publication-time history and are superseded above. P1.2 development is completed as PASS; do not execute its old development cell again.
**P1.1 first actual result verified:** original ZIP 52833 bytes, 36 members, SHA256 `6bdc2cc9435cefd8a3e99d1d0bc3589bd3b6ad84e50be83db877b1dde769e3ec`. All archive/member pins and independent offline replay passed. Original frozen verdict remains FAIL / NUMERIC_OR_PERMUTATION_INSTABILITY: 7/12 violate the original 0.50-nat centered two-schedule gate, maximum 0.9896240348252832 nats. Numerical batch/order delta \<=5.960464477539063e-8 nats. Both schedule winners agree on all twelve; pooled winners match the constructed math/coding/planning family pattern after the fact (4 ARITHMETIC, 4 PYTHON, 4 CSP). This is opened-development diagnosis, not verified answers, cheapest routing, calibrated confidence or unseen capability.
**FAIL publication COMPLETE:** [PR136](https://github.com/yoonsj0305/NEUMANN/pull/136) merged main `53e1c39468065be660656e167c72ee57b1e4ad15`, identical tested/merged tree `c33db305b23545ceb8534045b9375c3be9138952`, main verified. Full CI37168579168 SUCCESS: 706 PASS, 34 optional-environment SKIP, 7 subtests PASS; Frozen North Star SUCCESS. Original P1 and P1.1 FAILs stay unchanged; no historical rerun, threshold rescue or score reuse.
**P1.2 implementation and first-run publication COMPLETE:** [PR137](https://github.com/yoonsj0305/NEUMANN/pull/137), tested source/bootstrap head `75d9843e0d893e1a34394258b14c984d461cec1c`, tree `bb4deba6ec23bb5923b2d1ab2dfd4dc5b2e874c5`, bootstrap SHA256 `c8f66d3f05a672377376cb92f8d4e39f7669cd8e55a88d58a08bfaa430c5bdfe`. Squash-merged main `daa74c852eff5fa8c86e1cbe74282bc7f3eb2dae`, identical tested/merged tree verified; main and merged PR verified. All ten published blobs match local bytes. Original P1.1 ZIP is retained byte-for-byte as base64 and CI replays its unchanged FAIL.
**New development estimand:** equal mean over all 24 S4 bijections, same frozen Gemma/revision/vocabulary/BF16/codes/public inputs. Six pre-fixed balanced four-map deletions yield six leave-four-out20 means: all winners must equal full24, full24 margin \>0.50 nats, centered full24/leave-four-out20 delta \<=0.50 nats, numerical batch/order delta \<=0.05 nats. Residual orbit-pair and per-mapping interactions remain reported. Full-group reindexing is algebraic; marginalization does not prove interactions absent. A new P1.2 PASS may coexist with the old P1.1 gate failing.
**Complete budget:** twelve opened development tasks, all24 in batch4/unbatched1/reverse-batch4, 432 forwards, 864 input rows, 3456 scoring rows/tokens; evaluated/padded cap589824 each, controller540000ms, task120000ms, whole study1800000ms. Increased diagnostic work is charged. Linear estimate only: controller\~7.39min, study with old startup\~9.66min excluding bootstrap; actual execution/cost must be remeasured. Energy/FLOPs/money UNKNOWN.
**Validation status:** dedicated CI37169399285 SUCCESS: 23 P1.2 tests and 15 unchanged P1.1 tests PASS, zero skips, registration and actual original tokenizer-only readiness PASS (IDs236776/236799/236780/236796), no Gemma weights or task inference. P1, P1.1, Frozen North Star and Sequence checks passed. [Full CI37169399309](https://github.com/yoonsj0305/NEUMANN/actions/runs/37169399309) SUCCESS: 728 PASS, 35 optional-environment SKIP, 19 subtests PASS; both test and Sequence jobs, benchmark smoke, wheel build and fresh-venv package integrations passed. All five final-head workflows SUCCESS before merge.
**Current boundary:** actual P1.2 Gemma NOT RUN. Original twelve tasks DEVELOPMENT ONLY. Fresh validation UNREGISTERED/UNOPENED. P2/Decision3 BLOCKED regardless of development result. Q1-Q7 globally OPEN. No frontier/sealed-data study or new Gemma training.
**Next action:** run the immutable P1.2 first-development cell once in the original registered Tesla T4 runtime with Internet and existing model access. Pre

### Historical checkpoint — P1.1 bootstrap publication before the first real result · 2026-10-04

This section records PR134/135 publication-time facts. Its NOT RUN and next-action statements are historical and superseded above. The P1.1 first attempt is completed: do not execute the old P1.1 cell below again.
**P1 resolved:** original uploaded ZIP SHA256 `38d489dde092e86eea6a9f2276bc15fcfa574c463e18ececf161037dfd95cb38`, 22762 bytes. Independent offline replay confirms integrity, 12/12 complete, unchanged core, zero generation/tools, 72 forwards, 144 scoring rows, ARITHMETIC 12/12. Frozen verdict remains FAIL / DEGENERATE_ROUTE_SELECTION; P2=false, Decision3=false. No P1 rerun, relabel or post-hoc rescue.
**FAIL publication COMPLETE:** [PR133](https://github.com/yoonsj0305/NEUMANN/pull/133) tested head `436b7d32bb9357684c5dd5ebe1cd819c120e61a3`, merged main `4d680a722f95bd26b0e791d727a74b440bb4a59d`, identical tested/merged tree `309c6bfed0fbb17715acc7417d520a61041ad5b1`. Full CI37129142181 and Frozen North Star37129142182 SUCCESS before merge.
**P1.1 implementation:** [PR134](https://github.com/yoonsj0305/NEUMANN/pull/134) COMPLETE: tested head `d53adccc2d8f58b01b6f020fb8627f6e8ecc40b7`, squash-merged main `4e6db9926a27c94f63c8d539d0c6e57c34b49336`, identical tested/merged tree `9edde3693e0effbbff3a8678c9351d8e1459192b`; main and merged PR verified. Initial dedicated CI37130063490 passed all 15 contracts but vocabulary readiness failed. The initial tokenizer-construction explanation was premature: the confirmed implementation mismatch was Unicode hash serialization (new UTF-8 JSON versus original ASCII-escaped JSON). Readiness now reuses and pins the original core hash helper and the same original Gemma4Processor.tokenizer, with a Unicode-vocabulary regression and matching CPU vision import dependency. Original model/vocabulary pins, code strings and thresholds stay unchanged; no Gemma inference/task scoring occurred. Explicit executor contracts, frozen-vocabulary audited distinct single-token A/B/C/D codes, two disjoint balanced four-map Latin-square schedules, one prefix evaluation for four next-code probabilities. Fixed additive code priors cancel under the stated additive assumption; code/problem interactions may remain and must be tested. All eight maps, both schedules and all batch/unbatched/reversed layouts are mandatory, with full attempt cost and independent replay. Original 32 uploaded archive members are retained byte-for-byte with size/SHA pins in the merged implementation.
**Current boundary:** P1.1 real Gemma scoring has NOT run; no GPU study is armed here. Final-head dedicated CI37130406778 SUCCESS: all 15 P1.1 contracts PASS, no skips, source registration valid. Actual original processor/tokenizer readiness PASS without model weights or task scoring: A/B/C/D IDs 236776/236799/236780/236796, distinct single non-special tokens; vocabulary SHA256 unchanged. [Full final-head CI37130406799](https://github.com/yoonsj0305/NEUMANN/actions/runs/37130406799) SUCCESS: 697 PASS, 34 optional-environment SKIP; both test and sequence jobs passed, including smoke/wheel/fresh-venv checks. Original P1 contracts CI37130406768 and Frozen North Star CI37130406773 also SUCCESS before merge. Original 12 P1 views are DEVELOPMENT ONLY; development PASS always leaves P2/Decision3 false. Fresh opened validation remains UNREGISTERED/UNOPENED until actual development PASS and architecture freeze. Fresh validation must be frozen before scores, distinct from development, and pass before P2. Global Q1-Q7 OPEN; no new training, frontier or sealed data.
**First-run bootstrap publication COMPLETE:** [PR135](https://github.com/yoonsj0305/NEUMANN/pull/135), tested bootstrap head `5aa9795ef525018d409d6a147579e2521f4012fd`, merged current main `269dad84900abbbf3276bfbc9e86479a0992800a`, identical tested/merged tree `2e397e98f566bd9cd53922aae56b879124078a3d`; main and merged PR verified. Bootstrap SHA256 `a2372bb34ba76a50e92eca3d3e6cecaa60d10606d05a332329a0b17c347d610c`. The experiment checkout stays unchanged at PR134 `4e6db9926a27c94f63c

### Historical checkpoint — P1 contract + runner + CI COMPLETE; first real Gemma diagnostic next · 2026-10-03

**Publication COMPLETE:** [PR132](https://github.com/yoonsj0305/NEUMANN/pull/132), tested head `7110dbb228bd01896d99d2ff7c92634fd3d12634`, squash-merged main `81d004cf91251ef523e734756548c6cd694ac54e`. Tested/merged tree `9783887ddcc3245fbfb845f9677f5c94f1e4107b` is identical; current main verified. [P1 CI37127011987](https://github.com/yoonsj0305/NEUMANN/actions/runs/37127011987) SUCCESS: P1 15 PASS, prior P0 23 PASS including CPU tensor/archive contracts, zero skips, frozen source registration valid. [Full CI37127011897](https://github.com/yoonsj0305/NEUMANN/actions/runs/37127011897) SUCCESS: both test and sequence jobs, all smoke/wheel/fresh-venv checks. Frozen North Star CI37127011966 SUCCESS.
**Frozen P1 scope:** existing 12 opened AM1 public views only, SHA256 `c883a44136817bf2501549a42c268b29577b8f153b3ca95b807e7ab245fdd2f0`; private answers/tests and task-family metadata never enter the model. Same `google/gemma-4-E2B-it`, revision `3e22461f65e89153144f8adb70e3b8c2cc9845a7`, BF16, frozen weights and original artifact/vocabulary pins. Registered Tesla T4 / torch2.11.0+cu128 / torchvision0.26.0+cu128 / transformers5.16.1. Route-only teacher-forced likelihood for DIRECT / ARITHMETIC / CSP / PYTHON; normal batch4, unbatched1 and reverse batch4 on every task. No generation, answer execution, tools, new training, frontier or sealed data.
**Diagnostic gate:** 12/12 completion, exact unchanged identity and complete cost; finite scores; batch/order deltas \<=0.05 nats; margin \>0.10 nats requires stable winner; \>=2 winning routes, dominant route \<=10/12, centered score range \>=0.001 nats. Numeric tolerances are preregistered diagnostic choices, not routing-accuracy evidence. 144 score rows / 72 forwards maximum; context4096, label16, evaluated/padded tokens196608 each, task120000ms, study1800000ms including load/audit. Incomplete costs remain UNKNOWN. A model-free replay checks original receipt bytes, public identities, all three modes, token/padding/forward totals, score summaries and verdict.
**Actual evidence boundary:** real P1 scoring has NOT been run. CI uses only synthetic fixtures, not Gemma weights or actual model observations. Original Decision2 FAIL and first uploaded bytes remain immutable. P1 PASS only permits P2 preparation/registration; operational strongest normal DIRECT / full-input TOOL / minimal-evidence NEUMANN must still pass a matched original-answer capability/resource gate. Decision3 remains blocked, including the generic-interface requirement; Q1-Q7 remain globally OPEN.
**Next exact action:** in a Kaggle Tesla T4 notebook with Internet enabled, execute the published pinned bootstrap once. Script SHA256 `389eb4dd88a2759425e93692a505a23ca2e7d6844e3e80af3573809ee2f4345d`. Exclusive first-attempt paths refuse reuse; partial failures are packaged, never replaced. Preserve `NEUMANN_P1_FIRST_EVIDENCE.zip` and `NEUMANN_P1_FIRST_EVIDENCE.sha256.json`, then independently replay before admitting P2. Do not delete first files or silently change runtime/model to obtain a favorable run.
```python
import os, hashlib, urllib.request

COMMIT = "81d004cf91251ef523e734756548c6cd694ac54e"
os.environ["NEUMANN_P1_FROZEN_HEAD"] = COMMIT
url = f"https://raw.githubusercontent.com/yoonsj0305/NEUMANN/{COMMIT}/scripts/control_plane_p1_kaggle.py"
code = urllib.request.urlopen(url, timeout=60).read()
if hashlib.sha256(code).hexdigest() != "389eb4dd88a2759425e93692a505a23ca2e7d6844e3e80af3573809ee2f4345d":
    raise RuntimeError("P1 script hash mismatch")
exec(compile(code, url, "exec"))
```

### Historical checkpoint — Non-Generative Control Plane P0 COMPLETE; P1 route scoring next · 2026-10-03

**Actual Decision-2 evidence:** the user's uploaded first Tesla T4 study completed 36 observations. DIRECT / TOOL / NEUMANN each scored 0/12. All 72 model calls exhausted 256 generated tokens in the thought channel; none reached the final channel; tool calls were 0. The original verdict is FAIL, next ARCHITECTURE_PIVOT. This supersedes the execution-waiting checkpoint below, which is retained as history.
**New user-authorized architecture:** route choice and KEEP/DROP relevance are selected from teacher-forced fixed-candidate likelihoods rather than freely generated JSON control. Generation is reserved for normal answers or coding source. Original verification drives bounded route/evidence expansion and immediate stopping on accepted original answers. Same frozen Gemma weights; no new training.
**P0 publication COMPLETE:** [PR131](https://github.com/yoonsj0305/NEUMANN/pull/131), tested final head `dd967b2a4257de26e55bc6bb6bf964e7773fb283`, squash-merged main `fe185da5b8a1f04b5fe2cd0c3599d0b4d089aa83`; tested/merged trees identical. [Dedicated P0 CI37125027563](https://github.com/yoonsj0305/NEUMANN/actions/runs/37125027563) SUCCESS: all 23 pure/archive/synthetic CPU tensor contracts PASS, no skips, independent first-failure replay PASS. [Full CI37125027528](https://github.com/yoonsj0305/NEUMANN/actions/runs/37125027528) SUCCESS: 670 PASS / 31 optional-environment SKIP, both test and sequence jobs, all smoke/wheel/fresh-venv checks PASS. Frozen North Star/Frontier Gap CI37125027751 SUCCESS. Initial dedicated CI import failure was missing declared package dependencies and was corrected. No actual Gemma weights/model inference, new training, frontier/paid calls or sealed data in this P0 implementation.
**Original preservation:** all 78 uploaded JSON files retained byte-identically with size/SHA256 pins; ZIP SHA256 `468893d7be2ac5587edee3b7f87ad4310919f8c883800df8e1f8d41150556355`. Independent offline replay verifies original terminal hashes, 36-query order, core/trace identities, token cutoffs and arm totals. Prior failed verdicts/AM1 code remain unchanged.
**Remaining boundary:** P0 callbacks/tensor fixtures are not capability evidence or proof of an operational stronger Direct baseline. Next is separately preregistered P1 route-only scoring on the 12 opened tasks; P2 normal-answer/executor/original-checker integration and a new matched capability test follow only after that diagnostic. Scoring forwards, repeated input, retries and verification are charged; no compute savings assumed. Decision 3 remains blocked, including the generic-interface blocker. Q1-Q7 remain globally OPEN.

### Historical checkpoint — Decision 3 preregistered without unsealing; D2 local run remained next · 2026-10-03

**Decision-3 publication:** [PR128](https://github.com/yoonsj0305/NEUMANN/pull/128) final head `be880c27706bf68ae5289cc4be9fc175355e2344`, squash-merged main `30cdf1c6404c87636e72ace0ee2c5dbb2fa04ba2`. Dedicated Decision-3 no-unseal contracts, Frozen North Star/Frontier Gap contracts, sequence regression and full repository test job all SUCCESS before merge.
**What was frozen in advance:** pure Decision-3 PASS/FAIL/NOT_EVALUATED evaluator; provider-neutral frontier receipt schema; metadata-only deterministic sealed-task selector; source registry/census; current-interface readiness marker; model-free readiness checker; Windows `D3_READINESS_CHECK.cmd`. Decision-3 preparation opened **0 gated task rows**, performed **0 model inference**, **0 frontier/provider calls**, **0 paid compute**, and **0 training**. No sealed question/answer/rationale was committed or used for selection.
**Source census:** HLE-Rolling is the strongest current text-reasoning candidate under a future stable-ID/base-HLE exclusion rule; HLE-Diamond is a gated 2026 contamination-control candidate but its later release date alone cannot prove underlying questions are unseen because it refines the broader HLE collection. GPQA is retained only as verifier/science sanity because it is too old/public for primary 2026 unseen evidence. ARC-AGI-2 private tiers are strong leakage-control candidates but require a grid/ARC interface. LiveCodeBench remains a future date-tagged coding candidate when an official post-frozen-model task slice is available.
**Critical blocker:** current AM1 NEUMANN interface remains task-specific: math `expression+bindings -> m`, planning `domains+constraints -> c`, coding `requirement -> solve(items) -> p`. Decision-3 readiness is therefore `BLOCKED_CURRENT_TASK_SPECIFIC_INTERFACE`. A Decision-2 PASS does **not** authorize adding a benchmark-specific/new-family answer-capable executor after sealed data is seen. Any generic-interface change must return to opened matched validation first.
**Next exact action:** Decision 2 is still ACTIVE and no valid AM1 GPU capability run exists yet. On the local PC, run `AM1_LOCAL_SETUP.cmd` then `AM1_LOCAL_RUN.cmd`. If the independently replayed Decision-2 verdict is FAIL, pivot architecture and keep sealed data closed. If it is PASS, run `D3_READINESS_CHECK.cmd`; the current marker will still block unsealing until the task-agnostic interface issue has been resolved on opened matched data. Q1-Q7 remain globally OPEN.

### Latest restart checkpoint — Decision 2 local zero-cost execution ready; actual AM1 not yet run · 2026-10-03

**Critical path:** Decision 1 is closed as CPU-harness FAIL, not capability FAIL. Single-thread CPU micro-tuning remains stopped. Decision 2 is the active scientific gate: opened Architecture Multiplier on the same frozen Gemma 4 E2B core. Q1–Q7 remain globally OPEN.
**Decision-2 contract:** [PR126](https://github.com/yoonsj0305/NEUMANN/pull/126) merged main `28ff412ee73370f63e632c006fbe8301d5e7c2be`. Frozen three-arm comparison: DIRECT / TOOL / NEUMANN; 12 opened tasks = 4 math + 4 bounded coding + 4 finite planning. Same original checker, same core, no training, no frontier calls. Strongest matched baseline is selected by verified successes then complete wall time. PASS only through the frozen capability or efficiency path; valid FAIL requires architecture pivot; infrastructure invalidity is NOT_EVALUATED.
**Zero-cost local execution preparation:** [PR127](https://github.com/yoonsj0305/NEUMANN/pull/127) final head `3e8a894cd3dfed6b8d6104f360be5955a9a0175a`, squash-merged main `73942521f5a01d5917662c4eae149be1b1a7505d`. Added NVIDIA CUDA/BF16/VRAM preflight, Windows-safe bounded coding checker/RSS handling, isolated local setup, double-click `AM1_LOCAL_SETUP.cmd` / `AM1_LOCAL_RUN.cmd`, complete 36-observation evidence packaging, and model-free integrity/verdict replay. Frozen local runner requires CUDA + BF16 + \>=14 GiB VRAM; no quantization and no CPU fallback. Hardware that fails this boundary creates no negative capability evidence.
**Verification:** AM1/local dedicated contracts SUCCESS run37082705778; Frozen North Star SUCCESS run37082705806; General Runtime-0/frozen-transfer SUCCESS run37082705734; full CI SUCCESS run37082705799. Local-prep focused suite reached 24 PASS before full repository regression. PR127's first dedicated-CI failure was only squash-merge provenance ancestry bookkeeping; preregistration content hashes stayed unchanged and the CI now pins authoritative PR126 merge ancestry.
**Actual evidence boundary:** no valid AM1 GPU capability run has been performed yet. No Decision-2 PASS/FAIL is claimed. The next scientific action is exactly one first valid local AM1 execution on admissible hardware. Preserve every first-run receipt; no favorable rerun. v107 sealed evaluation, frontier execution, 4B/7B scaling, Edge optimization, new training, large benchmark expansion and LP polishing remain blocked until Decision 2 resolves.

### 2. Core Hypothesis

더 좋은 표현으로 문제를 바꾸고 불필요한 계산을 제거하며 필요한 계산만 선택하는 능력이 높은 지능의 중요한 부분일 수 있다. Problem → Structure → Minimal Sufficient Representation → Eliminate → Cheapest Sufficient Compute → Verify.

### 8. Fixed Core Questions

<table header-row="true">
<tr>
<td>ID</td>
<td>고정 질문</td>
</tr>
<tr>
<td>Q1</td>
<td>구조를 이용하면 실제 계산량을 줄일 수 있는가?</td>
</tr>
<tr>
<td>Q2</td>
<td>계산을 줄여도 원문제 correctness/capability가 보존되는가?</td>
</tr>
<tr>
<td>Q3</td>
<td>oracle 없이 유용한 숨은 구조를 발견할 수 있는가?</td>
</tr>
<tr>
<td>Q4</td>
<td>그 구조를 충분히 싸게 발견할 수 있는가?</td>
</tr>
<tr>
<td>Q5</td>
<td>discovery+execution+verification+retry+routing을 포함한 전체 end-to-end가 strong Direct보다 실제 싼가?</td>
</tr>
<tr>
<td>Q6</td>
<td>이득이 unseen/new-family/open-set/scaling에서도 유지되는가?</td>
</tr>
<tr>
<td>Q7</td>
<td>작은 완전한 NEUMANN 시스템이 실제 frontier capability gap을 회수하는가?</td>
</tr>
</table>
Namespace `north_star_2026_10_02`. 과거 v104까지의 Q5=scaling/cross-domain은 새 Q6 관련 역사적 질문이며, raw report의 `global_q5_closed` 문자열은 바꾸지 않는다. 과거 bounded Q34 통과는 새 global Q3/Q4/Q5/Q7 closure가 아니다.

### Latest restart checkpoint — first new-class result retained; v104 publication under CI · 2026-10-02

**First actual decisions:** [run36974426284](https://github.com/yoonsj0305/NEUMANN/actions/runs/36974426284) attempt1 SUCCESS;32 sources,448/448 original-LP-certified observations,0 failures. Assignment STOP_FAMILY_NO_ORACLE_HEADROOM: all four cells fail, ratios1.575965/1.216452/1.047592/0.993206,0/16 source20% wins. Basis-pursuit ADMIT_FROZEN_CHECKPOINT_TRANSFER_NOT_LEARNING: all four cells pass,0.633142/0.377829/0.217160/0.137875,16/16 source20% wins. Optimistic exact support AND original dual are free; zero models and shared LP backend mean no actual transfer or globalQ5 pass.
**Immutable first evidence:** execution17d83a4dd22faf8a5799b68a82c8ef2456d414fa; archive dc575e8b794ff97cf9a22ddac75c396f6fe5e148; raw sources SHA256 aeefb46c2814a1886520adf9ea6f1ab862efa2c2166f1bf8c18ce4edcb066473; raw report97884fa0c0093e3e6b96931fc9fd359a34a07c67eb0b87d2bd5a5a51f644697a; canonical report64c17943f05216c58901dedfb1bd90537f3097ad5f7d39d230cea2bfd6a3d6f4; last eventc6b0430da9be00ad3747d2529c638e655c13716dc8a6f58f2475cd70c8c2f239,941 events. All489 first files retained, no rerun/refit/replacement.
**Publication:** [PR117](https://github.com/yoonsj0305/NEUMANN/pull/117) head `40ccf7a2ae98b3ef3681b3d6d874dc240c4d6863`, version104 candidate; local53 pure/first-byte guards PASS. Full CI plus original-Q5 and new-class dedicated CI running. New independent replay must check all448 original certificates/native-child ledgers/complete costs with generators, queries/workers, all optimizers and model forwards forbidden; do not merge on metadata alone. Main remains5f9b3044de13e4a0a47b0446692b44d651e666b8/version103 until all final-head checks pass. [Scientific record](https://github.com/yoonsj0305/NEUMANN/blob/research/q5-transfer-admission/docs/experiments/v0.0.104.md).
**Resume/stop:** assignment transfer/fitting stopped under this exact executor. Basis-pursuit only admits a separately frozen first transfer test of BOTH existing checkpoints on NEW sources with no fitting/tuning or seed selection, strong applicable Direct and full verification/fallback costs. Do not recycle these opened32 sources as favorable final inputs. v103 first negative Q5 gate remains unchanged; globalQ5/cross-domain OPEN.

### Latest restart checkpoint — admission executor merged; exclusive first audit armed · 2026-10-02

**Merged implementation:** [PR116](https://github.com/yoonsj0305/NEUMANN/pull/116) at main `5f9b3044de13e4a0a47b0446692b44d651e666b8`. Final implementation head `0ab83d360ec638c2d2f758443366d088bac8f4ee` passed [CI467](https://github.com/yoonsj0305/NEUMANN/actions/runs/36973293235), original-Q5 contracts12 and admission contracts4. Generic497 PASS·28 SKIP; pinned-runtime8/8 including all four fresh workers actually executed with no skip. Original1536 first Q5 observations replay successfully with no new generation/forward/solver. All smoke/build/wheel/fresh-venv checks succeed. Release remains103.
**One-shot first execution:** head `17d83a4dd22faf8a5799b68a82c8ef2456d414fa`, [first admission36974426284](https://github.com/yoonsj0305/NEUMANN/actions/runs/36974426284), attempt1 in progress. Marker pins merged main and executor;32 sources/seeds104000..104031,448 frozen serial observations. Before arming, all1753 existing evidence blobs were checked unchanged and no v104 archive existed; prior literal seed searches found no matches. Original v103 first result and failures unchanged.
**Restart boundary:** wait for this first terminal and retained archive on research/q5-transfer-admission. Never rerun, generate replacements or change5s/cell gates. After completion, pin raw source/report/head/terminal identities and independently replay ALL original witnesses/accounting with every generator, optimizer and model forward forbidden. Then publish actual positive/negative family decisions, final CI and merge. Zero-model optimistic support+dual headroom cannot itself establish frozen-model transfer, computational cross-domain reuse or globalQ5 closure.

### Latest restart checkpoint — v0.0.94 input compaction first result · 2026-10-01

**Status:** 사전 규약→첫288진단→별도 비용 사전규약→첫1984관측→원본 게시→replay·문서·로컬536 PASS 완료. [PR #103](https://github.com/yoonsj0305/NEUMANN/pull/103). 최초 실험 재실행·새fit·final 없음. 최신 head `2f396224700be614b8de88f0bb0e78e08bcc1510`, local/remote tree `bc71808c7faee64e7a10c065b1fcbec8a681d128` 동일.
**Hypothesis / First diagnostic:** 고정v088 point16 선별기와 CG5 features로 첫 graph message 전에2m열만 남겨 기존full16의3 updates를 수행. 입력48개·양seed·point/full/compact=288기록. point와compact shortlist coverage 양seed46/48; full46/47. 실제 graph multiply terms는 full의1/8. labels는 모든제안 고정후 coverage에만 사용. 두seed 사전 parity conjunction 통과로 별도 paid screen만 허용했다. 비용·일반화·Q3/Q4 통과가 아니다.
**First cost result / limitation:** 고전14+retained학습8+CG5학습8+CG5고전1=31경로×16 opened train×4=1984/1984 원문제 certificate 승인. 최초 비용 summary의 최강학습Direct ratio1.128744/1.157334, point-only ratio1.077504/1.041160, 양seed frozen gate FAIL. 작은focused pytest가 timing중 겹친 실행순서 오류가 있어 전체first timing을 `CONCURRENT_FOCUSED_TEST_CONTAMINATION`으로 명시했다. 정량 clean 성능·양성비용주장은 금지, 첫기록/판정변경·유리한재실행 없음. no-full-rescue는 양seed16/16. fulloriginal8모델 fit+setup+loading44766.885127ms를10000query로 각candidate에과금해도 상각비1.590589/1.620508. global모든연구비장부는 별도다.
**Decision / Next boundary:** `STOP_FROZEN_INPUT_COMPACTION_COST_CANDIDATE`. 새학습·holdout 허용하지 않고 native기본·Q3/Q4 OPEN. point-only가 동일2m집합을 이미선택하므로 그래프의잔존상태축소만으로Q4를주장할수없다. 추가graph가 단독선별기보다 어떤정보를추가하는지 먼저입증하거나 principled별도target이필요하다.
**Evidence:** probe규약head `f9951a814c2ddfd8bdbdeabec79ad68bd2ef1d33`; 비용규약head `7e4b58ea2051ba0bec567c9f37f448854b69f057`. [결과](https://github.com/yoonsj0305/NEUMANN/blob/research/v094-input-compaction/docs/experiments/v0.0.94.md) · [probe manifest](https://github.com/yoonsj0305/NEUMANN/blob/research/v094-input-compaction/docs/experiments/results/v094_first_probe.manifest.json) · [cost manifest](https://github.com/yoonsj0305/NEUMANN/blob/research/v094-input-compaction/docs/experiments/results/v094_first_cost.manifest.json) · [timing notice](https://github.com/yoonsj0305/NEUMANN/blob/research/v094-input-compaction/docs/experiments/results/v094_timing_notice.json). 원본 해시·거부witness·상태항·전체cost·첫판정 보존. CI는 replay/fixtures만수행한다.
**CI / Recovery:** 첫CI #347은 PyTorch없는general에서optional fixture를바로import해 collection오류. 기존과같은 importorskipguard로수정했고 모델CI는 새6검사 전부실행한다. 수정후 [CI #348](https://github.com/yoonsj0305/NEUMANN/actions/runs/36858168016)의 모델suite108 PASS·작업success, 일반회귀pass후 기존smoke·package검사진행중. 모두성공후main병합예정. Notion기본fetch가일시500을내었으나 discussions포함읽기로복구했다.

### v0.0.82 First Retained Audit Result

**Decision:** `ADMIT_BASIS_DISCOVERY_SEARCH_NOT_MODEL_TRAINING`.
**Result:** expanded 12 case의 `oracle complete median / best-Direct complete median` geometric mean = **0.0087784284**. 20% 이상 complete-cost 절감은 **12/12**, matched `n=m→16m` pair에서 scaling amplification ≥2×도 **12/12**. amplification 범위는 약 **3.86×–13.75×**.
**Boundary:** 역수 약 **113.9×**는 exact optimal basis를 무료로 주는 constructed oracle diagnostic의 headroom일 뿐 배포 가능한 NEUMANN speedup이 아니다. basis inferability·natural incidence·learned model advantage는 아직 증명하지 않았다.
**Discovery cost envelope:** 20% complete-path win을 유지하기 위한 discovery 최대 예산 `0.8×Direct−oracle`은 expanded cases에서 최소 **9.895 ms**, 중앙 **52.453 ms**, 최대 **363.679 ms**.
**Evidence:** protocol PR #90 merge `2279c9af4ca4e7f050014b9df1cffc0b13626761`; audit execution SHA `710cb4e908aae397c85d461953cd0cd36a336a07`; retained JSON SHA-256 `f1af7c37f3042dad60c43b0c4a80fe1ab95f011710f26a6abe499458d5589847`; result PR #91 merge `70be058326e88eeb2f18c4c65eb5d7b74d2a00dc`.
**Next — v0.0.83:** 신경망 학습 금지. admissible `A,b,c`만 쓰는 deterministic/classical basis-discovery shortcut screen을 먼저 사전등록한다. cheap rules·solver-native information·classical warm-start/basis heuristics가 oracle headroom을 얼마나 먹는지 측정하고, verified residual headroom이 충분히 남을 때만 Q3 learned discovery를 검토한다.

### Iteration v0.0.41 — Anti-shortcut causal audit

**Hypothesis:** v0.0.40의 결정론적 성공은 단위계수와 분리된 2×2 블록에 의존한다.
**Pass criterion:** 224개 신규·중복 없는 시스템, 참조 풀이와 D0–D4 원문제 검증 100%, 잘못 승인된 축약 0.
**Change / Data:** 비단위 계수, 블록 간 겹침, 결합의 세 활성 조건 각 64개와 통제군 32개. 사전등록 규약을 결과 전에 커밋했다.
**Result:** 224/224 참조 풀이와 1,120/1,120 방법별 최종 답이 검증됐다. 비단위 계수 조건의 기존 후보 가시성은 0%, 최고 평균 solver 연산 절감 회수율 16.35%였다. 겹침 조건은 후보 가시성 100%였으나 최고 회수율 30.96%였다. D1·D2의 결합 후보는 64/64개에서 거절되어 전체 풀이로 안전하게 복귀했다.
**Decision:** KEEP_AUDIT. 입력 표현과 충돌 선택을 분리해 수정한다. 학습형 발견기의 필요성은 입증되지 않았다.
**Evidence:** [v0.0.41 규약·결과](https://github.com/yoonsj0305/NEUMANN/blob/main/docs/experiments/v0.0.41.md) · [원시 JSON](https://github.com/yoonsj0305/NEUMANN/blob/main/docs/experiments/results/v041_first_audit.json) · [PR #49](https://github.com/yoonsj0305/NEUMANN/pull/49)

### Iteration v0.0.44 — Adversarial structural boundary audit

**Date:** 2026-09-28
**Hypothesis:** v0.0.43 저차수 인덱스는 등장 횟수가 6인 유효한 제거 표적과 복수의 정당한 조밀한 2×2 축약을 놓친다.
**Pass criterion:** 기존과 겹치지 않는 224개 시스템·각 참조 증명 검증·원문제 해 검증 100%, 위험하게 승인된 축약 0, 통제군 무축약; 두 공격 조건에서 각각 1개 이상 유효한 축약 누락.
**Change / Data:** HIGH_DEGREE 96개에서 목표 두 변수의 원래 등장 횟수를 정확히 6으로 증가. ALTERNATIVES 96개에서 동일 문제에 서로 다른 두 정당한 2×2 제거를 정확한 Schur 대입으로 별도 검증. 통제군 32개. 생산 F1은 동결했고 학습 모델은 사용하지 않았다. 계약 예제에서 기존 materializer가 조밀한 잔여 방정식에 대입하지 못한다는 사실이 드러나, 최종 데이터 실행 전 독립적 Schur 참조를 규약에 명시했다.
**Result:** 전체 224/224의 최종 해가 원문제와 일치하고 거절된 결합 축약 0. HIGH_DEGREE 96/96에서 2변수 블록을 놓쳤고 평균 변수 제거 회수율 88.81%, oracle solver 연산 절감 회수율 96.69%. ALTERNATIVES 96/96에서 서로 다른 두 참조 증명이 각각 유효하고 잔여 solver 연산을 줄였으나 F1 제거는 0. 통제군 32/32 무축약·검증.
**Failure / anomaly:** 생산 materializer는 제거 변수가 남긴 방정식에도 등장할 때 정확한 대입을 하지 않아 조밀한 증명을 실행할 수 없다. Schur 참조의 잔여 solver 연산 감소는 후보 탐색·대입·검사·재구성·원문제 검증의 총비용 우위를 뜻하지 않는다. 로컬 전체 테스트에서 기존 플러그인 프로세스의 3초 기동 제한으로 2건 실패했고, 원격 CI #204는 전체 성공했다.
**Decision:** BOUNDARY_CONFIRMED. 저차수에서의 이전 성공 범위를 명시적으로 제한한다. 학습형 모델의 필요성이나 총 계산비 개선은 아직 입증되지 않았다.
**Next test:** 정확한 Schur 대입 구현과 후보 검색의 모든 비용을 함께 측정한 뒤, 신규 데이터에서만 탐색 규칙을 비교한다.
**Evidence:** [v0.0.44 규약·결과](https://github.com/yoonsj0305/NEUMANN/blob/main/docs/experiments/v0.0.44.md) · [원시 JSON](https://github.com/yoonsj0305/NEUMANN/blob/main/docs/experiments/results/v044_first_audit.json) · [PR #52](https://github.com/yoonsj0305/NEUMANN/pull/52)
**Repository status:** v0.0.44 main 병합 SHA `e9f7b81321e25da07e43c5736552bf3604629d05`, CI #204 두 작업 전체 성공.

### Iteration v0.0.48 — Cost-gate opportunity audit before training

**Date:** 2026-09-29
**Hypothesis:** 같은 16차원에서도 F3가 이득인 고차수 sparse 문제와 F1이 유리한 조밀·통제 문제가 공존하지만, 단순 원래 열 등장 횟수 규칙이 이를 충분히 분리하면 학습형 게이트의 비용을 정당화할 잔여 신호가 없다.
**Pass criterion:** 신규 exact 128개(고차수 48, 조밀 48, 통제 32)의 F1/F3/정적 게이트 원문제 해 검증과 서명 분리. 예제당 3회 교차 전체 경로 실행시간에서 10% 이상 차이를 robust win으로 분류한다. F1·F3 각 16개 이상 robust win, 정적 게이트와 충돌 16개 이상일 때만 OPPORTUNITY_VISIBLE.
**Change / Data:** 사전등록·구현·평가기를 첫 전체 감사 전에 동결했다(로컬 `9ef9a18`, 원격 사전등록 커밋 `b133f466dd1bb3b0a28cd30203bae67beb309f8e`, 동일 트리 `b4cece6cd4a4854356e0574429284368734f7666`). F1/F3는 동결; original incidence=6 열이 있으면 F3, 아니면 F1인 단일 특징 게이트를 비교했다. F3 검증 실패 시 F1 검증 경로로 돌아가도록 설계했다. 학습 모델은 훈련하지 않았다.
**Result:** 128/128 서로 다른 신규 exact 시스템의 F1/F3/게이트 최종 원문제 해 검증. robust F1 6개, F3 34개, 중립 88개. 정적 게이트와 robust winner 충돌은 5개, fallback 0개. 고차수 48개만 degree-six 특징을 가졌다. 고차수 paired F3/F1 전체 경로 중앙값 0.881; 조밀 1.007; 통제 0.997. 관련 로컬 22개 테스트와 CI #212 두 작업 성공.
**Decision:** NO_LEARNED_GATE_JUSTIFIED. 사전 기준을 충족하지 못하므로 이 데이터로 학습 게이트를 훈련하거나 성능 업그레이드로 승격하지 않는다. 이는 다른 문제군에서도 학습이 쓸모없다는 증명이 아니다.
**Limitation / next test:** 원래 열 등장 횟수가 생성기 라벨을 완전히 분리해 데이터 지름길 위험이 크다. 단일 환경의 실행시간은 잡음에 민감하다. 다음에는 차원·밀도·등장 횟수 등 싼 특징을 맞추고도 실제 비용 우위가 갈리는 유효 문제군을 먼저 입증한다. 이후에만 홀드아웃 생성기에서 모델의 추론 비용까지 포함해 정적 규칙을 넘는지 시험한다.
**Evidence:** [v0.0.48 규약·결과](https://github.com/yoonsj0305/NEUMANN/blob/main/docs/experiments/v0.0.48.md) · [원시 JSON](https://github.com/yoonsj0305/NEUMANN/blob/main/docs/experiments/results/v048_first_audit.json) · [PR #56](https://github.com/yoonsj0305/NEUMANN/pull/56)
**Repository status:** v0.0.48 main 병합 SHA `731fa47564b2d869408a4a186c2492386d3684df`, CI #212 두 작업 전체 성공.

### Iteration v0.0.52 — Real numerical sparse-matrix ordering audit

**Date:** 2026-09-29
**Hypothesis:** 외부 RCM 순서가 실제 수치 행렬에서 solver 내장 정렬보다 제안·인수분해·풀이·원문제 검증을 포함한 전체 시간을 줄일 여지가 있다.
**Pass criterion:** NIST BCSSTRUC1 원본 네 행렬(153–1086차원)의 SHA-256을 고정하고, RCM 전체 경로 중앙값이 사전 지정한 native 세 정렬 중 가장 빠른 값보다 20% 이상 빠른 사례가 2/4개 이상. 각 정책 7회, 원문제 잔차와 심은 해 모두 검증.
**Change / Data:** 원본 파일은 별도 내려받고 코드와 임계값을 첫 전체 실행 전 로컬 `b1b99f1`, 원격 `3ef0ac4`로 동결했다. SuperLU의 COLAMD, MMD_AT_PLUS_A, MMD_ATA, NATURAL과 외부 RCM을 비교했다.
**Result:** 140/140회 원문제 검증. RCM의 20% 이상 개선 0/4개. 대조군 NATURAL이 네 행렬 모두에서 가장 빨랐다. 로컬 전체 260 PASS·1 SKIP.
**Decision:** NO_RCM_OPPORTUNITY. 네 행렬에서 외부 RCM이나 학습형 순서 모델을 추가하지 않는다. NATURAL의 우위는 작은 관련 행렬군에서 관찰된 결과이며 일반 규칙이 아니다.
**Evidence:** [규약·결과](https://github.com/yoonsj0305/NEUMANN/blob/main/docs/experiments/v0.0.52.md) · [원시 JSON](https://github.com/yoonsj0305/NEUMANN/blob/main/docs/experiments/results/v052_first_audit.json) · [PR #60](https://github.com/yoonsj0305/NEUMANN/pull/60)
**Repository status:** v0.0.52 main 병합 SHA `756723cba62e46f65a8588e0d7f1559386f6627f`, CI #220 두 작업 전체 성공.

### Iteration v0.0.55 — Natural component reuse first audit

**Date:** 2026-09-29
**Hypothesis:** 원본 행렬의 동일 연결 성분을 찾아 인수분해를 재사용하면 탐색·포기·원문제 검증 비용을 포함해 기본 solver보다 유리할 수 있다.
**Pass criterion:** NIST BCSSTRUC1 강성 행렬 13개 전체, 7회 교차 측정. 2개 이상에서 실제 동일 성분을 발견하고 각 행렬에서 native 최선의 진단 중앙값보다 전체 시간이 20% 이상 짧으며, 무반복 행렬의 NATURAL 대비 10% 초과 회귀는 0개. 원문제 역방향 오차 \<=1e-10, 심은 해 상대 오차 \<=1e-7.
**Change / Data:** 전체 13개 원본 압축 해시 고정, 성분 하나면 바로 원행렬 풀이, 여러 성분은 정확한 CSR 동일성 확인, 중복이 없으면 원행렬 풀이로 돌아가는 경로를 결과 전에 로컬 `5cd97d6`, 원격 `99977ba`로 동결.
**Result:** 첫 전체 실행이 bcsstk13/COLAMD warmup에서 중단. 원문제 역방향 오차는 3.48e-16이나 심은 해 오차 1.0526e-7이 고정 임계값 1e-7을 초과했다. 273회 결과 파일은 생성되지 않았다.
**Decision:** INVALID_NUMERICAL_VERIFICATION. 반복 구조 기회의 통과·실패 어느 쪽도 주장하지 않는다. bcsstk13을 삭제하거나 임계값을 이 버전 안에서 바꾸지 않는다.
**Evidence:** [규약·무효 기록](https://github.com/yoonsj0305/NEUMANN/blob/main/docs/experiments/v0.0.55.md) · [오류 JSON](https://github.com/yoonsj0305/NEUMANN/blob/main/docs/experiments/results/v055_invalid_audit.json) · [PR #62](https://github.com/yoonsj0305/NEUMANN/pull/62)
**Repository status:** v0.0.55–56 main 병합 SHA `eae1bb08f91e3c3329d5ef82cc7070f5a52a5e8a`, CI #225 두 작업 전체 성공.

### Iteration v0.0.56 — Corrective unmodified-matrix audit

**Date:** 2026-09-29
**Hypothesis:** v0.0.55의 수치 임계값 문제를 명시적으로 보정하고도 원본 13개에서 반복 성분 재사용의 전체 비용 기회가 남는가.
**Pass criterion:** 데이터·정렬 기준·결정 임계값·7회 측정은 동일. 심은 해 상대 오차만 \<=1e-6으로 선언하고 원문제 역방향 오차 \<=1e-10 유지. 첫 실패 사례를 이미 봤으므로 독립 holdout이라 부르지 않는다.
**Change / Data:** 보정 규약을 첫 전체 실행 전 로컬 `2ebe8d2`, 원격 `8152fae`로 별도 동결. 각 trial에 옛 임계값 통과 여부와 새 임계값 통과 여부를 모두 저장했다.
**Result:** 13개 원본 × 3정책 × 7회 = 273회 모두 수정된 수치 기준 통과. 실제 동일 연결 성분이 있는 행렬은 bcsstk08/11/12의 3개였으나 20% 이상 전체 시간 우위 0개. 무반복 10개 중 7개에서 탐색 후 포기로 NATURAL보다 \>10% 느렸다. 원본 전체 행렬 자체가 정확히 동일한 파일 쌍 06/07, 11/12도 발견했으나 이는 시간 미측정의 데이터셋 중복 기술 통계다. 로컬 전체 268 PASS·1 SKIP.
**Decision:** NO_NATURAL_REUSE_OPPORTUNITY. 원본 행렬을 전부 검사하는 성분 탐색 경로는 기본 runtime에 넣지 않는다. v0.0.54의 복제 통제 실험 이득은 그대로 보존하지만 일반 배포 이득으로 승격하지 않는다.
**Current priority / Next test:** 원본 입력 전부에 검사 단계를 붙이는 요구를 삭제한다. 상위 문제 명세에 구조 정보가 이미 존재하는 경우만 재사용을 검토하고, 별도 실제 문제군에서 자유도 제거형 축약이 강한 solver 기본 경로보다 고정 검증 정확도에서 총비용을 줄이는지 시험한다. 지금까지의 정확한 인수분해 재사용 성능을 구조적 자유도 제거 성능으로 해석하지 않는다.
**Evidence:** [규약·결과](https://github.com/yoonsj0305/NEUMANN/blob/main/docs/experiments/v0.0.56.md) · [273회 원시 JSON](https://github.com/yoonsj0305/NEUMANN/blob/main/docs/experiments/results/v056_first_audit.json) · [PR #62](https://github.com/yoonsj0305/NEUMANN/pull/62)
**Repository status:** v0.0.55–56 main 병합 SHA `eae1bb08f91e3c3329d5ef82cc7070f5a52a5e8a`, CI #225 두 작업 전체 성공.

### Iteration v0.0.61 — Corrective original-MIP affine audit

**Date:** 2026-09-29
**Change:** v0.0.60 결과를 보고 목적값 상한만 6747.32로 사후 보정했다. 첫 새 실행 전 로컬 `808c7a9`로 별도 규약을 동결했으며, 이는 독립 holdout이 아니다. solver gap·원본·변환·20초 예산·3쌍 검증은 유지.
**Result:** 여섯 실행 모두 새 목적값·gap 및 원문제·정수성 검증 통과. 예전 6742.21 상한은 모두 미달. 중앙값 native 7.520초, 축약 후보 9.871초(후보/native 1.313). 후보 목적값 6746.760023은 native 6747.310015보다 조금 좋았으나, 축약 후보의 동일 기준 총시간은 약 31% 길었다. 정확 최적해 증명은 아니다. 로컬 회귀 268 PASS·1 SKIP.
**Decision:** NO_CORRECTIVE_LOCAL_ADVANTAGE. 이 Python affine 축약기를 runtime에 넣지 않는다. 변수 수 감소만을 기회로 간주하지 말고 강한 native presolve가 놓치는 구조와 총비용 병목을 새로운 문제군에서 찾아야 한다.
**Evidence:** [규약·결과](https://github.com/yoonsj0305/NEUMANN/blob/experiment/v0.0.61-corrective-mip-gate/docs/experiments/v0.0.61.md) · [원시 JSON](https://github.com/yoonsj0305/NEUMANN/blob/experiment/v0.0.61-corrective-mip-gate/docs/experiments/results/v061_first_corrective_audit.json) · [PR #66](https://github.com/yoonsj0305/NEUMANN/pull/66).
**Repository status:** PR #66 main 병합 SHA `05a59d3260dc32f5680c1da3729007a8a3a3902e`, CI #233 성공(두 작업), 로컬 268 PASS·1 SKIP.

### Latest checkpoint — P1.4 semantic interpretation MERGED and first T4 run READY

**Date:** 2026-10-04
PR #142 `P1.4: bounded semantic interpretation before verified execution` is merged.
- tested head: `bba2e6a6420581edddeafdba94fbd8b60f540e56`
- tested tree: `94b88cb154a102764bea6fc5d5d0a6da133b6ad6`
- merged main: `66004e3e7c8e0bd69a506f43bdde21c13a9eed3c`
- merged main tree: `94b88cb154a102764bea6fc5d5d0a6da133b6ad6` (identical to tested tree)
- final-head workflows: 7/7 SUCCESS
- full CI: **779 PASS, 35 SKIP, 57 subtests PASS**
- dedicated P1.4 semantic contract workflow: SUCCESS
- no actual P1.4 Gemma inference has run yet

### Frozen first-result gate

A first actual P1.7 PASS requires all integrity/accounting/wall gates plus:
- observations exactly 12
- total accepted \>= 11/12
- unique accepted exactly 8/8
- ambiguous accepted \>= 3/4
- unique model calls exactly 0
- ambiguous model calls exactly 4
- unique neural forwards exactly 0
- ambiguous neural forwards exactly 144
- generated calls exactly 0
- complete known-work accounting
- \<=180,000 ms per item
- \<=1,800,000 ms whole study
- frozen core identity unchanged
- independent model-free full receipt replay PASS
The 144 ambiguous forwards are a diagnostic fallback cost, **not** an efficiency claim or production target. Energy/FLOPs/money remain UNKNOWN unless measured.
A PASS is only `OPENED_SOURCE_BOUND_DIAGNOSTIC_ONLY`. It does not admit P2. It must be followed by architecture freeze + newly registered fresh semantic validation.

## Notion-🧩 Pilot 50 _ First Canonical IR Drafts v0.1

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🧩 Pilot 50 _ First Canonical IR Drafts v0.1 -- 3e77830ff334814abb9bfb0c8aa18eb9.md
SHA256: 9665eb1f9498334e60944f845d29c9e20d408ff94e0fb3eb2b1e3127977c9a9c

### 5. First IR-pass findings

1. **Source ≠ problem instance.** One page can contain several solver structures.
2. Add `instance_span / subproblem_id` to the annotation schema.
3. Add `task_type`: CALCULATION / FORMULATION / MODEL_VALIDITY / OTHER.
4. Add `external_context_required`: NONE / IMAGE / TABLE / LINKED_SOURCE.
5. Define structural equivalence **after semantic parameter extraction**, but separately record extraction complexity.
6. Same-source related subparts must not inflate recurrence estimates.

## Notion-🧪 Pilot 50 _ Candidate Registry v0.1

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🧪 Pilot 50 _ Candidate Registry v0.1 -- 3e67830ff334817f8654e9bd42375c5b.md
SHA256: 5c49d8c105e16fca0be301c809b1859d9014a0f2858a3281ccf1a240430d0cf5

## Notion-🧱 Annotation Schema v0.2 _ Source → Instance → Solver IR

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🧱 Annotation Schema v0.2 _ Source → Instance → Solver IR -- 3e77830ff3348128a33afc3c841209ad.md
SHA256: 899cc305f392900ab558693afedafe0b2798916df03e677e1d2eb1ba0a33b4f4

### 12. Decision

**v0.2 supersedes v0.1 for the next annotation pass.**
Reason: v0.1 assumed too strongly that one source item maps cleanly to one calculation structure. Real forum data already falsified that assumption.

## Notion-⏱️ v0.0.20 _ Runtime Cost Audit + Threat Model v2-3e77830ff3348139a1d0f2cab20adbbe

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\⏱️ v0.0.20 _ Runtime Cost Audit + Threat Model v2 -- 3e77830ff3348139a1d0f2cab20adbbe.md
SHA256: c4f33ce0eb24a2a4047c7f6f91f037dceb24ec4afb4023b2c59e741221400f08

### ⏱️ v0.0.20 | Runtime Cost Audit + Threat Model v2

원본: https://app.notion.com/p/3e77830ff3348139a1d0f2cab20adbbe?pvs=204

> **Status:** MERGED
> **Version:** v0.0.20
> **GitHub PR:** [https://github.com/yoonsj0305/NEUMANN/pull/15](https://github.com/yoonsj0305/NEUMANN/pull/15)
> **Merge SHA:** 0582f79386ff432dc5d5eacd829088b6adef9c44

### Question

After v0.0.19 introduced process separation, what is the next bottleneck: fresh-process lifecycle cost or missing OS-level containment?

### Runtime-cost result

Final CI run:
- dispatch count: 9
- OOP full-pipeline median: \~2198.74 ms
- in-process trivial-family median: \~0.0046105 ms
- total dispatch time: \~6583.56 ms
- total child service time: \~1.542 ms
- total outside-service time: \~6582.02 ms
- outside-service fraction: **0.999766 (\~99.977%)**
- median dispatch: \~730.22 ms
- median child service: \~0.173 ms
- median outside-service: \~730.06 ms
- dispatch/service ratio: \~4270.7×

### Important interpretation boundary

The \~476,898× OOP/in-process ratio should not be generalized.
The in-process probe intentionally performs almost no useful work and is only a latency lower bound. It is not security-equivalent and not representative of production workloads.
The stronger result is:
> Parent-observed dispatch median \~730 ms while child-reported plugin service median was \~0.173 ms.
This directly shows that the current fresh-process-per-operation architecture is dominated by process lifecycle/import/IPC cost for lightweight reasoning families.

### Split decision

NEUMANN now has two different next priorities:
**Performance track**
→ `persistent_worker_lifecycle`
**Security track**
→ `os_level_capability_sandbox`
These should not be conflated.

### Next milestone

Recommended v0.0.21:
**Persistent Worker Lifecycle Experiment**
Target:
- start one child worker once
- import/activate plugin once
- reuse the same RPC channel for compile/solve/verify
- preserve authorization-before-request
- revoke prevents subsequent requests
- worker crash/timeout causes fail-closed recovery
- parent still never imports plugin module
- compare latency directly against v0.0.20 fresh-process baseline
Persistent workers are a performance optimization only. They must not be presented as stronger sandboxing.

## Notion-♻️ v0.0.21 _ Persistent Worker Lifecycle Experiment-3e77830ff334818c92a1d144dfa540e9

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\♻️ v0.0.21 _ Persistent Worker Lifecycle Experiment -- 3e77830ff334818c92a1d144dfa540e9.md
SHA256: 0109fb3508cd73f5cb61826ee6f2ee0a34894ea7a57d13900b61a9828fc38689

### Question

Can NEUMANN remove the fresh-process lifecycle bottleneck while preserving process separation, exact-manifest authorization, revocation semantics, and fail-closed recovery?

### Main finding

> **The v0.0.20 lifecycle bottleneck was real. Reusing the isolated child process reduced the warm lightweight-pipeline latency from seconds to approximately 1 ms in this CI microbenchmark while preserving the tested authorization/revocation invariants.**

### Important interpretation boundary

The \~2548× ratio must not be generalized to representative reasoning workloads.
The probe family intentionally performs almost no useful computation, which magnifies process-start/import overhead.
The stronger engineering conclusion is:
- fresh process creation is unacceptable for every lightweight compiler/solver/verifier operation
- persistent process reuse is a valid performance direction
- cold worker startup remains expensive (\~990 ms in final CI)

### Decision

**KEEP persistent-worker execution as the preferred performance path.**

### Recommended next milestone

Before adding more throughput optimization, the next runtime correctness question should be:
> **Can persistent worker state be made explicit, bounded, and resettable so reuse does not introduce hidden cross-request coupling?**
Candidate v0.0.22:
**Worker State Hygiene + Recycling Contract**
Possible gates:
- deterministic repeated-request equivalence
- explicit worker generation ID
- max-request recycling
- reset/restart boundary
- poisoned-state test
- crash/recycle evidence
- retained-state declaration in plugin contract
OS-level sandboxing remains a parallel security track and must not be conflated with state hygiene.

## Notion-⛓️ v0.0.17 _ Durable Hash-Chained Authorization Ledger-3e77830ff33481a9873aeb518e4c4dc5

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\⛓️ v0.0.17 _ Durable Hash-Chained Authorization Ledger -- 3e77830ff33481a9873aeb518e4c4dc5.md
SHA256: 571ddae6762bb9a8e757f1dcd05e612ace803a53c56dec965c828e5e6f5a25ae

### Question

Can NEUMANN preserve plugin authorization across process restarts while detecting persisted-ledger tampering and keeping rollback detection honest about its trust boundary?

### Result

GitHub CI:
**71 PASS / 0 FAIL**
Persistent-ledger benchmark:
- events persisted: 3
- restart state preserved: YES
- trusted sequence: 3
- mutation detected: YES
- valid older prefix loads without external checkpoint: YES
- valid older prefix sequence: 2
- same truncation detected with trusted expected head: YES

### Main finding

> **NEUMANN authorization state can now survive restart and detect persisted record mutation/reordering, while rollback detection is explicitly tied to an external trusted head.**

### Crucial negative result / boundary

A complete rollback or truncation to an older valid prefix is still a valid hash chain by itself.
Therefore:
```plain text
hash chain alone
    ≠
rollback-proof state
```
With a trusted expected head SHA-256 from outside the ledger file, the rollback/truncation is detected.
Correct claim:
> **tamper-evident relative to the checkpoint trust boundary, not tamper-proof.**

### Decision

**KEEP**
- persistent JSONL authority state
- canonical hash-chain records
- full-chain verification before use
- external expected-head checkpoint hook
- explicit rollback limitation

### Next candidate

The next trust-layer milestone should avoid immediately piling on crypto without a threat model.
Recommended next question:
> **What exact threat model should NEUMANN's plugin trust plane defend against, and which guarantees belong in-process, on-host, or outside the host?**
That should determine whether v0.0.18 becomes:
- signed operator approvals / publisher identities,
- isolated plugin execution,
- or external checkpoint / policy service.
Do not choose the next security mechanism only because it sounds stronger; choose it against a defined attacker and failure model.

## Notion-🎚️ v0.0.6 _ Structural-Near OOD + Selective Risk-3e77830ff33481e3bf64e2559717ac16

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🎚️ v0.0.6 _ Structural-Near OOD + Selective Risk -- 3e77830ff33481e3bf64e2559717ac16.md
SHA256: b10770dd923095e4c76d444e88cdf1aae8b76318f99fe2774bcd7351418f74e9

### Question

Can NEUMANN reject structurally-near unsupported problems more safely without collapsing useful routing coverage?

### Frozen final-test result

<table fit-page-width="true" header-row="true">
<tr>
<td>Model</td>
<td>Known coverage</td>
<td>Routed-known precision</td>
<td>Unknown false-route</td>
<td>Near-OOD false-route</td>
</tr>
<tr>
<td>Two-stage logistic</td>
<td>80.0%</td>
<td>100%</td>
<td>9.52%</td>
<td>13.33%</td>
</tr>
<tr>
<td>Prototype centroid</td>
<td>33.33%</td>
<td>100%</td>
<td>0%</td>
<td>0%</td>
</tr>
</table>

### Interpretation

Prototype distance rejection is safer on the tiny fixture but too conservative. Two-stage gating gives much more useful coverage but still routes some structurally-near unsupported tasks.
Therefore NEUMANN should not optimize plain classification accuracy. It needs a **selective-risk policy** in which allowable routing coverage depends on an explicit false-route budget.

### Decision

**KEEP:** competence gate, UNKNOWN, near-OOD benchmark, selective-risk curve.
**MODIFY:** calibration, risk objective, training diversity.
**NEXT:** controlled full solver-ready IR generation for one structural family, with independent semantic checking.

## Notion-📈 v0.0.3 _ Break-Even Envelope-3e67830ff33481d5b931d3f427d2e75d

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\📈 v0.0.3 _ Break-Even Envelope -- 3e67830ff33481d5b931d3f427d2e75d.md
SHA256: 8e96512035d064ce92d6c541d5e2a06734221153c0aa2fc9276e406a52a51976

### 3. Assignment break-even results

<table fit-page-width="true" header-row="true">
<tr>
<td>n</td>
<td>Baseline steps median</td>
<td>Hybrid steps median</td>
<td>Representation budget median</td>
<td>Hybrid step win rate</td>
<td>Wall-clock ratio H/B</td>
</tr>
<tr>
<td>4</td>
<td>8.5</td>
<td>18</td>
<td>-11</td>
<td>0%</td>
<td>3.709×</td>
</tr>
<tr>
<td>5</td>
<td>35</td>
<td>24</td>
<td>11.5</td>
<td>60%</td>
<td>1.096×</td>
</tr>
<tr>
<td>6</td>
<td>127</td>
<td>29.5</td>
<td>95.5</td>
<td>90%</td>
<td>0.692×</td>
</tr>
<tr>
<td>7</td>
<td>1324.5</td>
<td>33</td>
<td>1295.5</td>
<td>100%</td>
<td>0.057×</td>
</tr>
<tr>
<td>8</td>
<td>17959.5</td>
<td>43</td>
<td>17912</td>
<td>100%</td>
<td>0.0065×</td>
</tr>
</table>
Interpretation:
- n=4: hybrid is clearly wasteful.
- n=5: primitive-step advantage begins but Python framework overhead still erases it.
- n=6: median wall-clock crosses below direct baseline.
- n≥7: direct exhaustive cost grows sharply while matching remains small.
**Observed toy wall-clock crossover: around n≈6 for this family and implementation.**

### 4. Shortest-path stress break-even results

<table fit-page-width="true" header-row="true">
<tr>
<td>k</td>
<td>Nominal paths</td>
<td>Baseline steps</td>
<td>Hybrid steps</td>
<td>Representation budget</td>
<td>Wall-clock ratio H/B</td>
</tr>
<tr>
<td>2</td>
<td>4</td>
<td>21</td>
<td>38</td>
<td>-17</td>
<td>2.741×</td>
</tr>
<tr>
<td>3</td>
<td>8</td>
<td>45</td>
<td>58</td>
<td>-13</td>
<td>3.306×</td>
</tr>
<tr>
<td>4</td>
<td>16</td>
<td>93</td>
<td>82</td>
<td>11</td>
<td>1.962×</td>
</tr>
<tr>
<td>5</td>
<td>32</td>
<td>189</td>
<td>110</td>
<td>79</td>
<td>2.775×</td>
</tr>
<tr>
<td>6</td>
<td>64</td>
<td>381</td>
<td>142</td>
<td>239</td>
<td>1.132×</td>
</tr>
<tr>
<td>7</td>
<td>128</td>
<td>765</td>
<td>178</td>
<td>587</td>
<td>0.396×</td>
</tr>
<tr>
<td>8</td>
<td>256</td>
<td>1533</td>
<td>218</td>
<td>1315</td>
<td>0.217×</td>
</tr>
</table>
**Observed toy wall-clock crossover: around k≈7 for this stress family.**

### 7. Research ↔ Engineering result

Engineering produced a new research object:
**Break-even Envelope**
향후 NEUMANN 연구는 단순 average speedup보다 다음을 측정:
- task family
- problem scale
- representation cost
- verifier cost
- solver cost
- direct-reasoning cost
- crossover boundary
즉 성능을 한 숫자로 요약하지 않고:
$$
\mathcal{E}(family,scale,representation\ cost)
$$
형태의 envelope를 구축.

### 9. Decision

v0.0.3: **PASS as methodology scaffold.**
다음 단계는 두 축을 병행:

## Notion-📜 v0.0.13 _ Static Plugin Manifest + Explicit Activation-3e77830ff33481f2b329e9183972e34d

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\📜 v0.0.13 _ Static Plugin Manifest + Explicit Activation -- 3e77830ff33481f2b329e9183972e34d.md
SHA256: abb588166ae6994bb9cb4c4fe7f02d2b023d6e81a1c545fbcf6543b081ca644b

### Question

Can NEUMANN inspect plugin identity and declared capabilities before importing or executing plugin code?

### Result

GitHub CI:
**53 PASS / 0 FAIL**
Plugin-manifest benchmark:
- catalog count: 1
- code-load calls after discovery: **0**
- code-load calls after explicit activation: **1**
- risky declared capability blocked before code load: **YES**
- canonical manifest SHA-256 generated: YES

### Decision

KEEP:
- static manifest
- code-free catalog
- explicit activation
- manifest/adapter identity check
- pre-import capability policy
NEXT:
1. installed-package discovery that reads metadata without loading plugin code
2. activation/revocation ledger
3. then evaluate signature/publisher trust and isolation boundaries
The design principle remains: **do not let convenience silently collapse discovery, trust, and execution into one operation.**

## Notion-📦 v0.0.14 _ Static Installed-Package Discovery-3e77830ff334814796b1c31364f566fd

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\📦 v0.0.14 _ Static Installed-Package Discovery -- 3e77830ff334814796b1c31364f566fd.md
SHA256: f26fcd0442ceb7279b8a551f22316be6b9260f846811b0f8c2cc83f194add5af

### Question

Can NEUMANN discover manifests shipped by installed Python distributions without importing plugin code?

### Result

GitHub CI:
**58 PASS / 0 FAIL**
Static discovery benchmark:
- discovered manifests: 1
- issues: 0
- distribution provenance captured: YES
- manifest digest captured: YES
- catalog built: YES
- plugin module imported during discovery: **NO**

### Main finding

> **Installed-package discovery can remain a metadata operation rather than an implicit code-execution operation.**

### Next

The strongest next milestone is no longer another parser.
Next evidence should be:
1. independently packaged external NEUMANN family
2. install into a clean environment
3. static discovery without import
4. explicit activation
5. conformance execution
6. uninstall / absence check
This would be the first real cross-package interoperability proof.

## Notion-🔌 v0.0.12 _ Open Namespaced IR Kind Runtime-3e77830ff3348142a547f56d6d771706

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🔌 v0.0.12 _ Open Namespaced IR Kind Runtime -- 3e77830ff3348142a547f56d6d771706.md
SHA256: 329de1ea8396c3d432f216b41745d9e8b2303992d1bfa5e7973ad710f8b76c70

### Question

Can a third-party reasoning family register and execute through NEUMANN without editing the closed core `IRKind` enum?

### Result

GitHub CI:
**48 PASS / 0 FAIL**
External-family benchmark:
- external kind: `example.scalar_sum`
- registered kind IDs: `core.bipartite_matching`, `core.linear_system`, `example.scalar_sum`
- core `IRKind` enum unchanged: YES
- external execution verified: YES
- external answer: 9.5
- external valid compile rate: 100%
- external solved+verified rate: 100%
- external reject fail-closed rate: 100%

### Main finding

> **NEUMANN now has a real runtime extension point: an external family can add a new representation kind, compiler, solver, and verifier without adding an enum member to core.**

### Decision

KEEP:
- namespaced kind IDs
- legacy core compatibility layer
- registry keyed by canonical IDs
- common conformance contract for external families
NEXT:
> **Define a static plugin manifest and discovery contract that can be inspected before plugin code is imported or executed.**
The next milestone should keep discovery separate from trust and execution.

## Notion-🔒 v0.0.8 _ Matching IR Fidelity Hardening-3e77830ff33481b79768dd1b0191c459

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🔒 v0.0.8 _ Matching IR Fidelity Hardening -- 3e77830ff33481b79768dd1b0191c459.md
SHA256: e3f75b78611b00e8c831dc6a9fb01964727f823f2ab97742f37840bd85059d43

### Question

Can the first complete matching compiler fail closed on partial, conflicting, or semantically richer statements instead of silently producing a plausible but incomplete IR?

### Engineering finding

v0.0.7 parser had two important silent-failure risks:
- an unsupported statement could be ignored while the rest of the text still produced a matching IR
- a repeated left-side relation could overwrite a previous relation
v0.0.8 changes the contract:
- every nonempty statement must parse
- conflicting repeated left-side relations → UNKNOWN
- identical repeated relations are allowed but recorded in diagnostics
- negation / exception / capacity / cost / weight semantics → UNKNOWN
- right-side tokens must stay inside the controlled identifier grammar
- edge-level precision / recall / F1 are now measurable

### GitHub CI result

GitHub Actions:
**27 PASS / 0 FAIL**
Benchmark smoke:
- valid exact-match rate: **100%**
- explicit reject fail-closed rate: **100%**
- edge TP: 22
- edge FP: 0
- edge FN: 0
- edge precision: **1.0**
- edge recall: **1.0**

### Interpretation

These results are from a tiny controlled fixture and are not evidence of general language understanding.
The important result is architectural:
> **Partial parsing must be treated as semantic failure, not partial success.**
Because:
$$
Correct(Solver(IR)) \not\Rightarrow Faithful(IR, RawProblem)
$$
Therefore the Structure Former contract becomes stricter:
1. parse all supported semantic content, or
2. return UNKNOWN / escalate.

### Decision

**KEEP**
- controlled complete-IR path
- fail-closed parser
- edge-level fidelity metrics
- independent semantic contract in benchmarks
**NEXT**
- broaden matching language only after ambiguity tests
- start real Pilot-50 Canonical IR annotation
- compare controlled compiler IR fields with real-world problems
**DO NOT CLAIM**
- arbitrary matching understanding
- production semantic verification
- general natural-language IR compilation

## Notion-🔗 v0.0.7 _ First Complete Matching IR Path-3e77830ff334815e8b3bff671d2fac81

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🔗 v0.0.7 _ First Complete Matching IR Path -- 3e77830ff334815e8b3bff671d2fac81.md
SHA256: c5d137dbc73dbfe3a9271aeb86e77c0ec45d030ba2bf6d5c22ec1a361e5763a6

### Main finding

v0.0.7 is the first NEUMANN version in which the supported family does **not** require an oracle solver payload.
However:
$$
\text{controlled compiler} \neq \text{general semantic understanding}
$$
The semantic checker is still benchmark-side and contract-based.

### Decision

**KEEP:** family-by-family full IR generation, independent representation-fidelity check, fail-closed behavior.
**NEXT:** stress matching IR extraction with malformed and structurally-near variants before adding a second full-IR family.

## Notion-🛂 v0.0.10 _ Learned Proposal, Deterministic Authority-3e77830ff3348185ad68f8e0b2115acf

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🛂 v0.0.10 _ Learned Proposal, Deterministic Authority -- 3e77830ff3348185ad68f8e0b2115acf.md
SHA256: 7fcc3576c70f93c28a161eb877b3eae91efac5e290c422260551d651e2aa7519

### Question

Can a learned structure recognizer propose a solver family while deterministic family compilers prevent classifier mistakes from becoming semantic execution errors?

### Main finding

On the small controlled benchmark, the learned layer made at least one unsafe family proposal that the deterministic compiler rejected before it became solver-ready IR.
Therefore the architecture demonstrated the intended separation:
$$
Proposal \neq Authority
$$
and:
$$
LearnedProposal \rightarrow DeterministicAcceptance \rightarrow Execution
$$

### Interpretation

This is not evidence of production safety or broad natural-language understanding.
But it is a useful architectural result:
> **A learned router can be allowed to be imperfect if downstream family-specific acceptance is strict enough to turn some prediction errors into abstentions rather than executions.**

### Decision

**KEEP**
- learned proposer
- deterministic compiler authority
- authorized-compiler registry concept
- fail-closed proposal/compiler disagreement
**NEXT**
Do not add another solver family merely for feature count.
Next engineering problem:
> **Turn family-specific compilers/solvers/verifiers into a stable plugin contract with conformance tests, so NEUMANN can scale as an open ecosystem rather than a monolithic codebase.**
This is the first step toward NEUMANN behaving as infrastructure rather than a single model demo.

## Notion-🛑 v0.0.16 _ Digest-Bound Activation + Revocation Authority-3e77830ff33481a18393c33fa64f8e0e

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🛑 v0.0.16 _ Digest-Bound Activation + Revocation Authority -- 3e77830ff33481a18393c33fa64f8e0e.md
SHA256: 7046264a3062fffca2a5119887e9705334cac26d26e0764532fb7829bcbd4c76

### Question

Can plugin execution authority be checked at use time so revocation stops the next solver action even if plugin code is already imported and registered?

### Result

GitHub CI:
**64 PASS / 0 FAIL**
Authorization benchmark:
- first execution verified: YES
- solver calls after first execution: 1
- revoked execution verified: NO
- revoked solver path: `fallback_required`
- post-revocation solver calls: **0**
- changed manifest digest blocked: YES
- same manifest re-approved: execution restored
Fresh-venv external package proof:
- core: `neumann1 0.0.16`
- external plugin: `neumann-example-scalar-sum 0.1.1`
- plugin imported after discovery: NO
- unapproved activation blocked before import: YES
- plugin imported after approved activation: YES
- first external execution verified: YES
- revoke event recorded: YES
- revoked execution verified: NO
- post-revocation solver calls: **0**
- re-approval restores verified execution: YES

### Main finding

> **Activation is no longer permanent authority. Runtime execution authority can be revoked independently of whether plugin code remains imported in memory.**
This directly produced the target metric:
**Post-Revocation Solver Actions = 0**

### Decision

**KEEP**
- digest-bound approvals
- append-only event semantics
- use-time authorization
- managed registry path
- fail-closed authorization denial

### Next milestone

The next trust-layer question is:
> **Can the authorization ledger become durable and tamper-evident across process restarts, while still detecting rollback, truncation, and event mutation?**
Candidate v0.0.17:
- canonical event serialization
- hash-chain ledger
- persisted head/root identity
- reload verification
- mutation/truncation detection
- rollback detection boundary explicitly defined
This would move authority from process-local state toward auditable runtime state.

## Notion-🛡️ v0.0.18 _ Threat Model + Assurance Contract-3e77830ff334810a8ca0f034bd07c955

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🛡️ v0.0.18 _ Threat Model + Assurance Contract -- 3e77830ff334810a8ca0f034bd07c955.md
SHA256: 4b4eafa172b1ffc3180a7ca88a56c2212b98b2d9e5d4597ddb040b4aeb99a5ff

### Question

Before adding more security mechanisms, what attacker and failure model is NEUMANN actually trying to defend against?

### Result

GitHub CI:
**78 PASS / 0 FAIL**
Threat Model benchmark:
- version: `neumann.threat-model.v1`
- scenarios: 7
- enforced assurance labels across prevent/detect/contain/recover: 6
- detected assurance labels: 3
- partial assurance labels: 6
- out-of-scope labels: 13
- uncontained host-integrity scenario: `plugin.post_activation_arbitrary_code`
- next control priority: **`out_of_process_plugin_isolation`**

### Main finding

> **The largest remaining runtime trust gap is post-activation containment.**
An approved or compromised plugin currently executes inside the same Python process as NEUMANN core.
A signature would establish identity, but it would not prevent correctly signed malicious/buggy code from exercising ordinary Python process authority.

### Decision

**NEXT CONTROL PRIORITY:** `out_of_process_plugin_isolation`
Minimum target for v0.0.19:
- plugin compiler / solver / verifier execute outside core process
- bounded request/response schema
- timeout/crash fail closed
- revocation checked before dispatch
- plugin process cannot directly mutate core in-memory authorization state
- clearly state that a child process alone is not a full OS sandbox

## Notion-🛡️ v0.0.5 _ Two-Stage Open-Set Gate-3e77830ff33481818a04f0dd766af696

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🛡️ v0.0.5 _ Two-Stage Open-Set Gate -- 3e77830ff33481818a04f0dd766af696.md
SHA256: 1bfd060a6d3b0fbe15eefcd5ad99a3f6bd4d4cd98f667a42b3c61e14d01d08f7

### 5. Interpretation

v0.0.5는 v0.0.4의 문제를 완전히 해결하지 못했다.
그러나 다음 구조가 더 명확해짐:
```plain text
raw problem
  ↓
competence / knownness gate
  ↓ yes
structure-family classifier
  ↓
solver route

  ↓ no
fallback / unknown
```
핵심 finding:
> **NEUMANN needs an explicit competence model, not just a good classifier.**

### 10. Next engineering milestone

v0.0.6:
- structural-near OOD benchmark expansion
- calibration metrics
- selective-risk curve
- compare two-stage detector vs prototype/distance rejection
- only after this: controlled full-IR generation for one family

### 11. Decision

**KEEP and continue.**
현재 learned path의 목적은 높은 자동화율이 아니라:
> **route only when the system has evidence that it understands the structural family.**

## Notion-🧠 v0.0.4 _ First Learned Structure Former-3e77830ff33481198b3fcee26e35068a

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🧠 v0.0.4 _ First Learned Structure Former -- 3e77830ff33481198b3fcee26e35068a.md
SHA256: a137e5feac48ea0240c64682ef25fb9233b60534cbd38e643d3e0518166e37cb

### 3. Test result

**11 PASS / 0 FAIL**

### 5. Overall result

- overall learned accuracy: **17/20 = 85%**
- keyword baseline: **4/20 = 20%**
- learned false-route rate across all unsupported examples: **3/8 = 37.5%**
Important:
> **Good surface generalization is not enough. Open-set rejection is currently the weak link.**

### 8. Main finding

> **The first learned model can recognize coarse structure across surface changes, but the system does not yet know reliably when it is outside its competence.**
This directly motivates the original UNKNOWN / fail-closed design.

### 10. Decision

**KEEP:**
- learned kind-recognition boundary
- confidence gating
- hard-negative benchmark
- UNKNOWN as explicit output
**MODIFY:**
- open-set recognition
- confidence calibration
- evaluation size/diversity
**DO NOT CLAIM:**
- general structure understanding
- real-world compute savings
- production-ready routing

### 11. Next v0.0.5 question

> **Can NEUMANN reduce false routing on unseen-but-nearby structures without collapsing useful auto-route coverage?**
Candidate next methods:
- distance-to-class prototype / metric rejection
- calibrated probability threshold
- explicit out-of-distribution training
- two-stage `known family?` → `which family?` classifier
Complete IR generation remains after this gate.

## Notion-🧩 v0.0.11 _ Family Adapter Registry + Conformance-3e77830ff334819d84c2c9965258f30c

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🧩 v0.0.11 _ Family Adapter Registry + Conformance -- 3e77830ff334819d84c2c9965258f30c.md
SHA256: 98043ac464aca8404aabac5b78ae03f4bc8f21097a21887141244a554056ebed

### Question

Can NEUMANN move from hard-coded family logic to a stable runtime contract for family-specific compilers, solvers, and verifiers?

### Result

GitHub CI:
**43 PASS / 0 FAIL**
Family conformance benchmark:
- `core.bipartite_matching`: valid compile 100%, valid solve+verify 100%, reject fail-closed 100%
- `core.linear_system`: valid compile 100%, valid solve+verify 100%, reject fail-closed 100%
- all registered families conform: YES

### Decision

KEEP:
- Family Adapter Contract v1
- Family Registry
- family-owned execution
- conformance harness
NEXT:
- replace the closed kind boundary with open namespaced identifiers
- preserve backward compatibility for existing core families
- prove a third-party dummy family can register and execute without editing the core enum

## Notion-🧪 v0.0.15 _ Fresh-Venv Cross-Package Interoperability-3e77830ff33481cabae6dfc3b74824d8

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🧪 v0.0.15 _ Fresh-Venv Cross-Package Interoperability -- 3e77830ff33481cabae6dfc3b74824d8.md
SHA256: bb0b2b2a102871cc18c8d0422b0c8f6c4c486669ff51f01a48a76679a4037fdf

### Question

Can NEUMANN core and an external reasoning family interoperate as separate installed Python distributions inside a fresh environment?

### Result

GitHub CI:
**59 PASS / 0 FAIL**
Fresh-venv cross-distribution proof:
- core distribution: `neumann1 0.0.15`
- external distribution: `neumann-example-scalar-sum 0.1.0`
- core imported from fresh venv site-packages: YES
- external manifest discovered from installed distribution metadata: YES
- plugin imported after discovery: **NO**
- plugin imported after explicit activation: **YES**
- external namespaced kind registered: `example.scalar_sum`
- execution verified: YES
- result: `sum = 9.5`
- valid compile conformance: 100%
- solve+verify conformance: 100%
- reject fail-closed conformance: 100%

### Important implementation finding

Adding the external package source under `interop/` initially broke setuptools automatic package discovery because the root build saw multiple top-level packages.
The fix was to make the core distribution boundary explicit:
- include `neumann1*`
- exclude `interop*`
This is a useful packaging lesson: ecosystem modularity requires the core artifact boundary to be explicit, not inferred.

### Decision

**KEEP**
- separate wheel interoperability
- static discovery before import
- explicit activation
- external family conformance
- clean-environment CI proof

### Next

With cross-package execution established, the next core infrastructure question is:
> **Can activation state, manifest identity, approval, and revocation be made authoritative and auditable so a discovered plugin cannot remain executable after its authorization is withdrawn or its manifest changes?**
Candidate next milestone: Activation / Revocation Ledger with digest binding and fail-closed execution.

## Notion-🧬 v0.0.23 _ Worker State Declaration + Lifecycle Classes-3e77830ff334813ba883de990130f464

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🧬 v0.0.23 _ Worker State Declaration + Lifecycle Classes -- 3e77830ff334813ba883de990130f464.md
SHA256: fa87f42952e20109160f7ca2baac6d83fb5bfdd7aa218880b8dc91281d298fbd

### Question

Can NEUMANN replace one global persistent-worker policy with explicit plugin lifecycle classes that the runtime actually enforces?

### Main finding

> **Persistent reuse is now an explicit manifest-level privilege rather than an implicit runtime default.**
The runtime can reject incompatible lifecycle choices before launching plugin code.

### Decision

**KEEP**
- explicit lifecycle classes
- persistent reuse as opt-in privilege
- legacy fresh-only fallback
- `STATEFUL_EXPLICIT` fail-closed until an actual state protocol exists
- lifecycle declaration bound to manifest approval identity

### Next milestone

Recommended:
**v0.0.24 \| Lifecycle Conformance Attestation**
Research-engineering question:
> **Can NEUMANN automatically test whether a plugin that declares STATELESS or CACHE_ONLY actually behaves consistently across worker recycle and generation boundaries?**
Candidate evidence:
- same corpus over warm and recycled generations
- semantic-output equivalence after removing non-semantic PID/cache metadata
- multiple recycle seeds/generations
- class-specific conformance rules
- attestation report bound to exact plugin manifest digest
- persistent privilege refused when attestation is absent, stale, or mismatched
This would connect lifecycle declaration to measured evidence rather than trusting metadata alone.

## Notion-🧭 v0.0.2 _ Semantic Fidelity + Wall-Clock Experiment-3e67830ff33481238749eacdbbbe76e3

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🧭 v0.0.2 _ Semantic Fidelity + Wall-Clock Experiment -- 3e67830ff33481238749eacdbbbe76e3.md
SHA256: 4da657760fc7ec2914d4a2faa5fe05bffe4eef66f2e790e67aee0d8c806f2df2

### 2. Test result

**8 PASS / 0 FAIL**
New tests prove two different facts:
1. **Internal answer verification can pass a semantically wrong representation.**
	- raw problem asks for shortest path
	- injected IR says bipartite matching
	- deterministic verifier can still verify the matching answer against that wrong IR.
2. **Independent semantic contract blocks the wrong IR.**
	- benchmark oracle expects shortest_path
	- matching IR is rejected before the result can count as semantically valid.

### 3. Research finding — verification separation

Confirmed engineering distinction:
$$
Correct(answer\mid IR)\neq Faithful(IR\mid RawProblem)
$$
A deterministic solver may perfectly solve the wrong formal problem.
Therefore NEUMANN requires two conceptually separate checks:
```plain text
Raw problem → Representation fidelity
Representation → Solver answer correctness
```
The v0.0.2 ReferenceSemanticVerifier is only a benchmark oracle. It is **not** the production solution to semantic fidelity.

### 5. Interpretation

Toy tasks are too small for solver-algorithm savings to amortize framework overhead.
Important conclusion:
> **A better algorithm does not imply a faster NEUMANN system. The problem must be large/hard enough for solver savings to exceed representation, routing, and verification overhead.**
이 결과는 실패가 아니라 NEUMANN의 routing condition을 구체화한다.

### 7. New research question from engineering failure

> **At what problem size / complexity does representation-first hybrid execution cross the break-even point and become cheaper than direct solving?**
즉 이제 단일 toy 문제의 승패가 아니라 **crossover curve**를 측정해야 한다.
예:
- assignment size n = 4, 6, 8, 10, ...
- graph size \|V\| / \|E\| 증가
- linear-system dimension n 증가
각 규모에서:
- direct baseline cost
- representation overhead
- routing overhead
- solver cost
- verification overhead
- total wall-clock
을 분리 측정한다.

### 9. Decision

**KEEP**:
- typed IR
- solver router
- deterministic solvers
- fail-closed behavior
- separate semantic fidelity and answer correctness concepts
**MODIFY**:
- cost model
- benchmark scale
- routing decision
**DO NOT ADD YET**:
- learned Structure Former
- LLM provider integration
- structure memory
Reason: first find the break-even envelope of the hybrid architecture.

## Notion-🧱 v0.0.19 _ Out-of-Process Plugin Execution Boundary-3e77830ff33481b9bec6eb221441c82b

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🧱 v0.0.19 _ Out-of-Process Plugin Execution Boundary -- 3e77830ff33481b9bec6eb221441c82b.md
SHA256: 4225a63991ded1c269bd0998449850da3d5b5a511a1427e25b0b7ee0a140ba85

### Question

Can NEUMANN remove direct Python-runtime coupling between external plugin code and core while preserving authorization, fail-closed execution, and cross-package interoperability?

### Result

GitHub CI:
**86 PASS / 0 FAIL**
Isolation benchmark:
- plugin imported in parent before execution: NO
- plugin imported in parent after execution: NO
- first execution verified: YES
- worker PIDs all differ from parent PID: YES
- child environment mutation changed parent environment: NO
- child launches for compile/solve/verify: 3
- revoked execution verified: NO
- post-revocation child launches: **0**
- compile timeout fail-closed: YES
- solver timeout fail-closed: YES
- compile crash fail-closed: YES
- verifier crash fail-closed: YES
Fresh-venv external wheel proof:
- core distribution: `neumann1 0.0.19`
- external plugin: `neumann-example-scalar-sum 0.1.2`
- external plugin module imported in parent: NO
- unapproved proxy creation blocked: YES
- worker PIDs outside parent: YES
- first execution verified: YES
- result: `sum = 9.5`
- revoke causes zero new child launches: YES
- re-approval restores execution: YES
- external family conformance: compile / solve+verify / reject = 100%

### Main finding

> **External plugin code no longer needs to enter the NEUMANN core Python runtime in order to participate in the Family Adapter architecture.**
The process boundary removes direct shared Python memory and module-state coupling.

### Important timeout finding

Initial isolation tests incorrectly used 0.2–1.0 second dispatch timeouts.
Because the current prototype launches a fresh Python interpreter and imports NEUMANN/plugin code per operation, startup cost is included in the timeout.
The contract was corrected:
- normal path gets a startup-aware timeout
- hang probes sleep longer than the attack-test timeout
This is an important performance issue for future runtime design. A persistent worker may eventually be needed to reduce process startup overhead.

### Decision

**KEEP**
- out-of-process compiler/solver/verifier proxies
- explicit RPC protocol
- authorization-before-dispatch
- timeout/crash fail-closed behavior
- fresh-venv external-wheel proof

### Next architectural questions

1. Recalibrate Threat Model v1 after this new process boundary.
2. Measure process-startup overhead against in-process execution.
3. Decide between:
	- persistent worker process with lifecycle control,
	- OS-level sandbox/capability restrictions,
	- publisher identity/signatures,
	- or a sequence combining them.
Do not call the child-process boundary a sandbox until OS capabilities are actually restricted.

## Notion-🧱 v0.0.9 _ First Multi-Family Complete IR Routing-3e77830ff33481ef8d77d0e1df9a73b4

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🧱 v0.0.9 _ First Multi-Family Complete IR Routing -- 3e77830ff33481ef8d77d0e1df9a73b4.md
SHA256: a66a2cf8b35a0fc9bf27edbf4eeb009d60366adb8a81b7f478a0a398ed622f69

### Question

Can NEUMANN expand from one complete solver-ready IR family to multiple solver families while preserving fail-closed routing?

### GitHub CI result

**32 PASS / 0 FAIL**
Benchmark v0.0.9:
- supported route accuracy: **100%**
- unsupported fail-closed rate: **100%**
- complete IR families: **2**
Supported fixtures included:
- two matching surface forms
- simple linear system
- linear system with explicit coefficients
Reject controls included:
- minimum spanning tree
- nonlinear equation system
- matching statement with unsupported capacity semantics

### Main finding

> **NEUMANN can now route between two distinct solver-ready representation families without an oracle solver payload, inside controlled syntax.**
This is the first step where the system begins to resemble a representation layer rather than a single-domain parser.

### Decision

**KEEP**
- CompositeStructureFormer
- family-specific complete-IR compilers
- fail-closed multi-family routing
- independent semantic verification per family
**NEXT**
1. add a third complete IR family only if it tests a new architectural property
2. connect controlled complete-IR compilers to the learned competence gate
3. measure whether learned family prediction + deterministic family compiler can safely coexist
4. continue Pilot-50 Canonical IR annotation and map real problem families onto executable IR schemas

### Next research question

> **Can a learned high-level structure recognizer select a deterministic family compiler safely enough that NEUMANN can accept broader surface language without giving up fail-closed semantics?**

## Notion-🧼 v0.0.22 _ Worker State Hygiene + Recycling Contract-3e77830ff334814fa719cabe516f9f65

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🧼 v0.0.22 _ Worker State Hygiene + Recycling Contract -- 3e77830ff334814fa719cabe516f9f65.md
SHA256: c64feff0b4db630418fffb3b067edc66fbe784051cde3c75457d1984171b48e1

### Question

Can NEUMANN retain persistent-worker performance while making hidden in-process plugin state explicit, auditable, and resettable?

### Poisoned-state result

Final CI benchmark:
- poison visible in same generation: **YES**
- poison visible after recycle: **NO**
- generation changed after recycle: **YES**
- semantic result across three worker generations verified: **YES**
- keep state-hygiene contract: **YES**
Final-run timing:
- warm same-generation pipeline: \~2.15 ms
- post-recycle cold pipeline: \~1059.6 ms
- warm clean pipeline median: \~1.81 ms
- strict compile/solve/verify across three generations: \~3084.0 ms

### Main finding

> **Persistent worker memory is real and can contaminate later requests, but process recycling demonstrably clears the test plugin's Python in-memory state.**
At the same time:
> **A properly structured family can remain semantically correct even when every operation occurs in a different worker generation.**

### Decision

**KEEP**
- generation IDs
- response-generation validation
- explicit recycle events
- configurable request-count recycling
- semantic independence from hidden worker state

### Recommended next milestone

The next lifecycle question is no longer simply how often to recycle.
> **What state class should each plugin declare, and what lifecycle policy should NEUMANN enforce from that declaration?**
Candidate v0.0.23:
**Worker State Declaration + Lifecycle Classes**
Candidate classes:
- `STATELESS_SEMANTICS`
- `CACHE_ONLY`
- `EXPLICIT_STATEFUL`
- `NON_PERSISTENT_ONLY`
Goal:
Map plugin-declared state semantics to enforceable runtime behavior instead of relying on one global request-count threshold.
Parallel security track remains:
`os_level_capability_sandbox`.

## Notion-🧼 v0.0.22 _ Worker State Hygiene + Recycling Contract-3e77830ff33481868f6fd5b401c27cd1

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🧼 v0.0.22 _ Worker State Hygiene + Recycling Contract -- 3e77830ff33481868f6fd5b401c27cd1.md
SHA256: 66e56395adb370558d7df2ca74d6cc9782f999773eefe0f64268172ba7296a1c

### Question

Can NEUMANN preserve persistent-worker performance while making hidden in-process plugin state explicit, auditable, and resettable?

### Main finding

> **Hidden Python state can influence later requests inside one worker generation, but process recycling removes that in-memory state for the test fixture. The explicit RPC / Representation contract is sufficient for the tested families to remain correct even when compile, solve, and verify execute in different worker generations.**

### Decision

**KEEP**
- explicit generation IDs
- response-to-generation binding
- manual recycle
- request-count recycle
- recycle event evidence
- hidden-state semantic prohibition

### Next candidate milestone

The next lifecycle question is no longer whether workers can be recycled, but **which families are allowed to persist and under what policy**.
Recommended next version:
**v0.0.23 \| Worker State Declaration + Lifecycle Classes**
Candidate classes:
- `STATELESS` — no semantic or optimization state required
- `CACHE_ONLY` — retained state may accelerate work but must not affect semantics
- `STATEFUL_EXPLICIT` — persistent state is part of an explicit protocol contract
- `NON_PERSISTENT` — must run in fresh/recycled process boundaries
Target:
- make lifecycle class part of the plugin/family contract
- map class to enforceable runtime policy
- reject incompatible runtime configurations
- preserve current generation/recycle evidence
- do not rely on one global request-count threshold for all plugins
Security-track priority remains separate:
**`os_level_capability_sandbox`**

## Notion-🧾 v0.0.24 _ Lifecycle Conformance Attestation-3e77830ff33481de94c2c6c996d60e0f

Source: C:\Users\Seojun\Desktop\NEUMANN 1\Notion\pages\🧾 v0.0.24 _ Lifecycle Conformance Attestation -- 3e77830ff33481de94c2c6c996d60e0f.md
SHA256: 6f5afa21a77539af2e71b6bf28714a266fac113ef64bc64e3d101139d5f763c1

### Question

Can NEUMANN require measured behavioral evidence before granting a plugin persistent-worker privilege?

### Final benchmark result

- attestation version: `neumann.lifecycle-attestation.v1`
- status: **PASS**
- case count: 3
- warm repetitions: 2
- warm: PASS
- recycled: PASS
- cross-generation: PASS
- semantic equivalence rate: **1.0**
- warm generation count: 1
- recycled generation count: 3
- cross-generation count: 9
- missing attestation blocked: YES
- persistent execution after attestation: VERIFIED
- stale attestation blocked: YES
- keep attestation gate: YES

### Main finding

> **Persistent-worker privilege can now be tied to measured behavior bound to the exact plugin artifact, rather than lifecycle metadata alone.**

### Decision

**KEEP lifecycle conformance attestation as a mandatory gate for public persistent reuse.**

### Next milestone

Recommended:
**v0.0.25 \| Durable Attestation Ledger + Freshness / Revocation Contract**
Research-engineering question:
> **Can lifecycle attestation evidence be persisted, audited, invalidated, and freshness-checked without making the evidence store itself a new weak trust anchor?**
Targets:
- append-only persisted attestation events
- exact manifest / corpus / attestation digests
- issuance and invalidation events
- revocation by plugin ID or attestation digest
- stale-evidence rejection after manifest or corpus changes
- reload integrity checking
- trusted-head boundary explicitly separated from local tamper evidence
The authorization-ledger lessons should be reused rather than inventing a second weaker trust mechanism.

## PR47-v0.0.40

Source: git:4868c0a9a7e7eeb2684c602da025ea6ffed1e6a7:docs/experiments/v0.0.40.md
SHA256: 1a4522a9382981f54745bafdb4455749297142ea777b305a22ab0e5270b0429e

### Expected interpretation

If M1 already satisfies the adequacy target, that is a strong deletion result:

> the current mixed family requires a multi-row compression primitive, but its
> routing/discovery structure is still cheaply identifiable from exact local
> incidence, so learned discovery is unnecessary.

That result would motivate the next harder family to hide block membership while
preserving the same verified local-progress -> multi-row-headroom bridge.

If deterministic discovery leaves real verified headroom, only then is a small
learned discovery model justified.

## PR46-v0.0.38.1

Source: git:e9609941c4ae166ce5cc0816212a812a390d8e11:docs/experiments/v0.0.38.1.md
SHA256: 3f5849d378d703d233a92721595543805c6a1efcb2a7806c8ffea4826f83d57c

### Research question

> Can a generated exact family contain both genuine one-row compression and
> genuine coupled multi-row compression such that the frozen local pipeline
> makes broad verified progress but still leaves substantial solver-relevant
> structure for an exact block primitive?

The intended sequence is:

    local compression makes real progress
        ↓
    local primitive saturates
        ↓
    coupled multi-row structure remains
        ↓
    exact block compression removes the residual structure

### Family decision

If safety passes and H1-H5 all pass:

    family_status = HARDER_FAMILY_VALIDATED

Then v0.0.39 may compare block discovery/routing methods.

If safety passes but any H gate fails:

    family_status = FAMILY_NOT_HARD_ENOUGH

Do not train a discovery model.

Revise the family again.

If safety fails:

    family_status = INVALID_FAMILY_OR_CHECKER

Repair correctness before any discovery experiment.

## PR44-v0.0.39

Source: git:ebf7a0bb1bc96883c3373b5e1f45ff20e7dd5402:docs/experiments/v0.0.39.md
SHA256: 4c830a77fb2755663168ad5d501e57a146d0468c452c0b21eb618c7bb95ba464

### Fresh audit data

Use the same scale grid:

    k in {2, 4}
    n in {4, 8, 16, 32}
    n >= k

Per cell:

    32 fresh systems

Total:

    256 systems

Use new seeds not used by v0.0.38.

Every v0.0.39 signature must be:

- unique within v0.0.39,
- disjoint from v0.0.38,
- disjoint from all comparable prior generated signatures.

The final set is opened only after this specification and implementation are
committed.

### Family decision

If safety passes and all of:

    H1
    H2
    H3
    H4a
    H4b
    H5

pass on the fresh set:

    family_status = HARDER_FAMILY_VALIDATED

If safety passes but any gate fails:

    family_status = FAMILY_NOT_HARD_ENOUGH

If safety fails:

    family_status = INVALID_FAMILY_OR_CHECKER

No thresholds or gates may be changed after the v0.0.39 final set is opened.

### Next milestone if validated

Only after:

    HARDER_FAMILY_VALIDATED

may the next version test block discovery.

The first discovery experiment must compare:

1. deterministic exact 2x2 row-pair / target-pair enumeration,
2. sparse row-pair heuristics,
3. graph / connected-component pairing,
4. a learned block scorer only if cheaper deterministic methods leave
   pre-registered downstream headroom.

The optimization target remains:

    verified downstream solver work

not generator block-label imitation.

## PR41-v0.0.38

Source: git:9b1fea5302031fe41db9a5fa523c9742e4cce859:docs/experiments/v0.0.38.md
SHA256: fe948044135e9af0b4033131fb69cc6510682f9438111ab259326089da34742f

### Planned next milestone

If the continuation gate passes:

    v0.0.39 = Coupled Block Discovery Gauntlet

v0.0.39 should compare:

- exhaustive deterministic block enumeration,
- cheap pairwise structural heuristics,
- generator oracle,
- and only then, if deterministic discovery leaves meaningful verified
  headroom, a learned block proposal mechanism.

## PR39-v0.0.37

Source: git:9e763273e946d9c73627d5c4ce868459cd1000d3:docs/experiments/v0.0.37.md
SHA256: 00e927262b9c7c64fb3553837b4137c565e4a5d4defa5e844ea23e65fe575b5b

### Next milestone

If deterministic residual policy is selected:

    v0.0.38 = harder structural family / distribution shift

If Ridge or MLP-8 is selected and final-confirmed:

    v0.0.38 = cross-family residual generalization + total-cost instrumentation

If HOLD:

    v0.0.38 = failure analysis before any larger model.

## PR38-v0.0.37

Source: git:8600aca565ee9eedb5a170c6189bc0f2fc26ed12:docs/experiments/v0.0.37.md
SHA256: ca53c93f25991a6a3fbe37ea796a24220b795bc026cefecb4f5a2bc4ec31ce76

### Interpretation of teacher recovery

Define:

    teacher_residual_gain
        = target_leaf_ops - exact_residual_teacher_ops

    method_residual_gain
        = target_leaf_ops - method_ops

Aggregate recovery:

    mean(method_residual_gain)
        / mean(teacher_residual_gain)

This may exceed 1 because greedy teacher trajectories are path-dependent and are not globally optimal.

### Learned-component retention rule

A learned residual component is retained only if all safety conditions hold and at least one of these two performance conditions holds:

### Next milestone

If KEEP_LEARNED_RESIDUAL:

    test the hybrid architecture on a harder structural family.

If KEEP_DETERMINISTIC_RESIDUAL:

    freeze the deterministic residual component
    and move to a harder structural family.

If ESCALATE_MODEL_CLASS:

    test one strictly bounded nonlinear model class,
    preferably a tiny MLP,
    without changing the first-stage architecture.

If DELETE_RESIDUAL_MODEL:

    retain target-leaf only
    and move to a harder structural family.

## PR36-v0.0.36

Source: git:68e7082447b1351c372242df2d635a46ea496789:docs/experiments/v0.0.36.md
SHA256: 0a6ac3aa23094e7b22e77a4f0673905428073d55b5b526bfffe8ef8acdf19db1

### Interpretation branches



### Planned next milestone

Only on GO:

    v0.0.37 — Learned Residual Value-of-Reduction

On NO-GO:

    freeze target-leaf as the current affine-linear policy
    and move to a harder structural family before adding model capacity.

## PR34-v0.0.35

Source: git:f6c94a3c43b4c86596b266d90c4bf2ae7597c2ff:docs/experiments/v0.0.35.md
SHA256: 11e63550fd9c157d0dd5512848b6e8a751db1fd991ea21832171885fc684c672

### v0.0.35 — Compression Economics Audit

Status: pre-registered research specification

### Central question

> Does the current certified Structural Compression path save arithmetic work once a conservative lower bound on successful checker materializations is included?

This is a prerequisite question for later Value-of-Reduction learning.

### Decision rule



### Architecture consequence if the audit fails

The preferred redesign target is not weaker verification.

It is:

```
score / rank candidates
    -> cheap local structural admission
    -> accumulate a candidate batch
    -> bounded final exact materialization
    -> reconstruction
    -> original-problem verification
    -> fail closed / fallback if final batch is invalid
```

The design goal is to remove repeated full reduced-system solves from the inner proposal loop.

Candidate future mechanisms include:

- incremental rank / factorization certificates,
- batch validation,
- bounded rollback,
- divide-and-conquer subset recovery,
- cached elimination state,
- solver-state reuse.

These are future work and are not part of the v0.0.35 result.

### Measured result — 2026-09-28

The pre-registered audit produced a decisive negative result for the current per-candidate rematerialization checker.

Contract checks:

- checker parity with frozen v0.0.34: **100%**
- verified retention: **100% for every method**
- unsafe accepted reductions: **0 for every method**
- thresholds: unchanged and on the frozen grid
- final examples: unchanged v0.0.34 set of **256 systems**
- `KEEP = true`

The no-compression baseline averaged:

- solver arithmetic: **1971.66**
- solve + original-problem verification arithmetic: **2047.99**

Mean successful-materialization lower-bound ratios:

| Method | Final solver ops | Final solver savings | Accepted eliminations | Successful materializations | Lower-bound arithmetic | Mean LB / baseline | Median | P90 | Fraction >= 1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| learned_mlp | 442.23 | 1529.42 | 7.49 | 8.49 | 16773.67 | **4.62x** | 3.79x | 9.75x | **100%** |
| target_leaf | **325.13** | **1646.52** | 7.68 | 8.68 | 17366.61 | **4.50x** | 3.26x | 10.17x | **100%** |
| markowitz | 387.31 | 1584.34 | 7.96 | 8.96 | 17022.93 | **4.68x** | 3.70x | 9.82x | **100%** |
| structural_combo | 462.18 | 1509.47 | 6.29 | 7.29 | 16944.47 | **4.24x** | 2.85x | 9.91x | **100%** |
| sparsity_incidence | 418.91 | 1552.75 | 6.70 | 7.70 | 17353.39 | **4.34x** | 3.17x | 10.26x | **100%** |
| dependency_contrast | 533.78 | 1437.88 | 6.71 | 7.71 | 15622.06 | **4.35x** | 3.31x | 9.00x | **100%** |
| row_sparsity | 572.09 | 1399.57 | 5.82 | 6.82 | 15551.89 | **4.11x** | 3.33x | 9.03x | **100%** |
| deterministic_random | 601.53 | 1370.13 | 6.21 | 7.21 | 14636.72 | **4.09x** | 3.11x | 8.49x | **100%** |

The mean-ratio statistic is the pre-registered primary diagnostic. It is the mean of per-example lower-bound / baseline ratios, not the ratio of aggregate means.

### Interpretation

The final compressed solve is substantially cheaper than the full solve, but obtaining that compressed state through the current checker is not.

For the learned scorer, for example:

```
final retained-system solver
    = 442.23 arithmetic events on average

but successful checker materializations alone
    = 16773.67 arithmetic events on average
```

The latter is still an optimistic lower bound because it excludes:

- scorer work,
- candidate enumeration,
- conflict checking,
- all hidden work inside failed materialization attempts,
- Python/runtime overhead,
- memory traffic,
- certificate serialization.

Therefore the result is stronger than merely saying the checker is "somewhat expensive."

> **The current per-candidate exact rematerialization loop is economically incompatible with the Structural Compression objective on this benchmark.**

This does not invalidate Structural Compression itself. It localizes the next bottleneck.

v0.0.32 showed that a correctly compressed retained problem can have much lower solver work. v0.0.33–v0.0.34 showed that learned and deterministic proposal mechanisms can find useful reductions safely. v0.0.35 shows that repeatedly re-solving the reduced problem after every tentative candidate destroys those gains.

## PR33-v0.0.35

Source: git:7d9087c09caaf3e3bbfeccfbb4d5b2b369527747:docs/experiments/v0.0.35.md
SHA256: 865ce740004c81a287843ece0af8c815b951efd697d650026e9b6a3f2577d09e

### Central research question

> Does direct supervision on certified marginal solver utility produce a better verified compression policy than matched reference-label supervision and deterministic structural heuristics?

### Decision rule after v0.0.35

If utility supervision beats matched reference supervision but not deterministic heuristics:

    absorb the deterministic utility heuristics
    and keep learning only where residual value remains.

If utility supervision beats both matched reference and deterministic baselines:

    proceed to dynamic / state-dependent marginal utility.

If deterministic heuristics remain strongest:

    promote them into the core architecture
    and shift learning toward residual prediction,
    family routing,
    or harder structural domains.

NEUMANN optimizes verified computation, not the prestige of learned components.

## PR32-v0.0.35

Source: git:0262f72105e274976a68c45328f3307b8b0bcefa:docs/experiments/v0.0.35.md
SHA256: 30d4fa7b0f2de54455815610b77401a9ea809b590e83eff11d45ef3707c45da8

### Core research question

> Can a small utility predictor rank certified reductions by downstream computational value better than a reference-label imitation model and strong deterministic heuristics?

### Next decision

If utility-directed ranking improves final solver savings:

    advance toward state-dependent / sequential utility prediction.

If deterministic heuristics remain superior:

    absorb the strongest heuristic as the default policy
    and use learning only where it adds measurable marginal value.

If checker lower-bound arithmetic dominates the saved solver work:

    the next milestone should prioritize cheap compression certificates
    and checker algorithms before improving the learned policy.

## PR18-v0.0.23

Source: git:f0d5cd4c87655ee76861fed034dfacc6bcbb73c4:docs/experiments/v0.0.23.md
SHA256: d42f3b2fce91a8314deb4bc05a66bda3aa6be370f1122c73ae39ff2f11752b2b

### Question

Can NEUMANN map plugin-declared state semantics to enforceable worker lifecycle behavior instead of relying on one global recycling threshold?
