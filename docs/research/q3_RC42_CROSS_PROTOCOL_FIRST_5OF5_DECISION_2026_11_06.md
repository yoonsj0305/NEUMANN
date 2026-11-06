# NEUMANN 1 | RC42 cross-protocol source-only portability: FIRST 5/5 and independent audits

Date 2026-11-06. Status: **SCOPED CLASSICAL EXTERNAL PROTOCOL MODEL PORTABILITY PASS**. Global Q3 neural invention, Q4 strongest-classical lifecycle cost, Q6 cross-formalism generalization and Q7 frontier all **OPEN**.

## 1. Problem restatement

Given a deterministic complete resettable finite-state I/O source, a known upper bound `N` on its state count, fixed input/output alphabet, and only `membership(input_word)->output_word` access, recover an executable state machine and prove agreement on **every finite input word**. Crucially, reuse the identical frozen learning policy and verifier on independently authored models without editing the learner based on their outputs.

This is about **formal state-machine transfer**, not autonomous invention of the finite-state representation itself.

## 2. Assumptions, boundaries and deletions

| Assumption | Decision |
|---|---|
| The source is deterministic and outputs are resettable/truthful | **Necessary theorem premise** |
| A correct public upper bound on target states is supplied | **Necessary theorem premise**; not inferable from finite source queries alone |
| Human authors have already chosen finite-state Mealy representation | **Retained for this experiment**, not evidence of spontaneous representation discovery |
| Existing L* learner needs further tuning on external protocol | **Deleted:** exact original RC39 code remains untouched |
| Different protocols imply different mathematical formalism | **Rejected:** MQTT and TLS are both represented as Mealy machines |
| Exhaust public ARC evaluation to check portability | **Deleted:** zero original ARC IDs consumed |

## 3. Frozen implementation

Original classical learner Git blob `83bd15d98b8fa02f4427b26c27264d35c0ec261e`, original classical W-method Git blob `86a413ff5e002995e0c79e625abe22d5877ae424`. Both existed prior to these external models. The files are checked at runtime and are never changed.

Two different, previously public external model corpora:

- **MQTT models**: `mtappler/mut-learn@24b5535f37ca92745ddb4c3a5a5381b6ccfa87ce`. Mosquitto, ActiveMQ, HBMQTT, three distinct locked Git blobs.
- **Legacy TLS models**: `damascenodiego/DynamicLstarM@5095464d597c68a4899cc81e3d415e3696a00242`. miTLS 0.1.3 and OpenSSL 1.0.2 server, two distinct locked Git blobs. Original DOT syntax uses numeric state nodes, unlike the MQTT source. A strict source-interface adapter was added **outside** the frozen learner/W.

**Disclosure:** both public model groups were examined by the researcher prior to their respective preregistration. They are independent **authored** examples, but not blind-to-researcher test suites. Raw external model text is not committed.

## 4. FIRST source execution (unmodified learner)

| Externally authored model | Reference states | Inputs / outputs | Distinct source membership queries | Independent all-word proof |
|---|---:|---:|---:|---|
| MQTT Mosquitto | 3 | 7 / 7 | 154 | PASS |
| MQTT ActiveMQ | 4 | 7 / 7 | 203 | PASS |
| MQTT HBMQTT | 5 | 7 / 8 | 252 | PASS |
| TLS miTLS 0.1.3 server | 6 | 8 / 8 | 392 | PASS |
| TLS OpenSSL 1.0.2 server | 7 | 7 / 7 | 350 | PASS |
| **Total** | | | **1,351** | **5/5** |

- MQTT first [#42139496328](https://github.com/yoonsj0305/NEUMANN/actions/runs/42139496328) SUCCESS; original JSON SHA256 `87adfee0cd1dc19b4cff1f364d9db71a2c6a9dd6ed623af3cdcdc645a6b78690`.
- TLS first [#42140318676](https://github.com/yoonsj0305/NEUMANN/actions/runs/42140318676) SUCCESS; original JSON SHA256 `e577dc6547c5de3d18befaa811d0032074be1b49772475fe376d73b4a573614f`.
- Membership only during learning. Published exact model graph accessed in a source-output callback and in the product-state proof **after compiled model freezing**, never as a direct model input or perfect equivalence oracle.
- Five explicit erroneous output mutations rejected; six opened negative parser controls per protocol PASS.

## 5. Independent non-relearning verification

- MQTT alternate source parser and product checker [#42139793229](https://github.com/yoonsj0305/NEUMANN/actions/runs/42139793229): **PASS**, original sha locked, independently all-word equivalent **3/3**, mutants rejected **3/3**, re-learning zero, favorable result forgery rejected.
- TLS alternate numeric-DOT parser and product checker [#42140511727](https://github.com/yoonsj0305/NEUMANN/actions/runs/42140511727): **PASS**, original sha locked, independently all-word equivalent **2/2**, mutants rejected **2/2**, re-learning zero, favorable result forgery rejected.

Both independent checkers are different codepaths from the original source adapters and do not import the L* learner or W-method.

## 6. Cost and physical interpretation

**Measured:** 1,351 distinct complete membership queries across five models. These are total source-query events, not electrical power, API prices, hardware cost, or full intelligent-system operating cost.

`C_total = C_preparation + C_discovery + C_source_queries + C_independent_proof + C_failures`.

Source calls can dominate physical testing, yet that has not been demonstrated with a latency or power measurement on live TLS/MQTT products. **Do not** apply the earlier 36.32x RC39 classical verifier reduction to these different external models as though it had been measured here. The product-cost-based `Idiot Index` is **NOT MEASURABLE** without material/power and lifecycle cost data.

## 7. Risks and degraded mode

- **Incorrect state bound:** finite observations cannot certify an arbitrary larger hidden automaton. The audit validates a *published finite model*, not the underlying live TLS/MQTT implementation.
- **Different output semantics or nondeterminism:** a timed, probabilistic or nonresettable system falls outside the theorem; return `UNKNOWN`.
- **Source transformation mistakes:** strict two-format parsers, unique transition check, raw Git SHA pins, independent alternate parser and product audit.
- **Cherry picking/data leakage:** explicitly separate synthetic RC39, opened-author MQTT/TLS external models, and future blind external-authored fresh validation.
- **Overfitting:** five external models from two protocol classes are not an unbiased sample of arbitrary software problems.
- **Wrong incentives:** do not promote these classical 5/5 portability results to frontier neural invention Q3/Q6.
- **Fail-safe:** unknown source, missing or false state bounds, exceeded membership budget or wrong external hash means no proof certificate and no production authorization.

## 8. Four possible next research paths

1. **Cross-formalism discovery:** synthesize verified loop invariants or compositional array/string transformations from a generic, learned proposal policy, evaluated on externally authored new families with independent SMT/Lean-style proof.
2. **Strongest-classical headroom gate:** require that an equal-rights classical portfolio cannot solve a significant set of externally authored test cases within the registered total compute/energy limits before spending on training.
3. **Learned policy rather than hand-supplied L*:** a model may propose new structures, but verify each candidate and evaluate against frozen L*/L#/Kearns-Vazirani alternatives under matched source-query budgets and unseen independent families.
4. **Hybrid certified interface:** where finite-state assumptions are satisfied, invoke this proven classical module and suppress redundant model calls. Otherwise `UNKNOWN` and route to a different independently proven domain solver.

## 9. Recommendation

**Keep** the 5/5 external source-learning pipeline as a small classical *proof-carrying state abstraction tool*, NOT as the defining achievement of NEUMANN 1.

**STOP** more very similar finite-state protocol variants until a learned proposal policy demonstrates novel structure and real independent cross-formalism transfer over a powerful classical baseline, with source queries + neural training/serving + verification fully metered.

Stacked provenance: #650 global evaluation ledger -> #651 RC39 initial learning -> #653 W cost verification -> #655 MQTT external FIRST -> RC42 TLS FIRST. Preserve all first artifacts. Do not merge a stacked draft out of order.
