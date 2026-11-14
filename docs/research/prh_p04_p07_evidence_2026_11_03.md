# NEUMANN 1 · P0.4–P0.7 structural-program discovery decision

**2026-11-03 KST · opened-development only · Draft PR #617**

Authority: `docs/research/frozen_north_star.md`. The project's goal remains **frontier-level problem solving with minimum necessary computation**. **All global Q1–Q7 remain OPEN.** This branch does **not** change P1.11.1's retained FAIL, P1.12 model status, any sealed gate, or Decision 3.

## Completed first experiments

| Pilot | Result | Scientific boundary |
|---|---|---|
| P0.4 | Human-specified typed relational composition solves public ARC-AGI-1 opened task `05f2a901`, 1/1 exact; leave-one-training-example-out 3/3, rotations/recolorings 8/8 | The developer **pre-inspected** the public data and designed the spatial grammar accordingly. No novel primitive invented; not blind ARC evidence. |
| P0.5 | First parameterized clearance induction **FAIL 109/128**, unseen left direction 42/48 | Preserve first failed receipt. A reference-generator error used nominal 3×3 size for some actually occupied 2×3 shapes, giving contradictory clearances. |
| P0.5.1 | **Separate** repaired generator with independent actual occupied-bbox reference audits and disjoint seeds 951001–951004: **128/128** synthetic test exact, 48/48 unobserved left direction; fixed zero-gap P0.4 baseline **32/128** | Source-contract repair with new seeds, **not** relabeling or a favorable retry of P0.5. Known generator family and human-designed grammar only. |
| P0.6 | Cheap classical-first cascade returns **4/4** on four pre-inspected public ARC-AGI-1 development cases: 3 from P0.3, one from P0.4; **0 neural forwards** | Route only on ABSTAIN, never inspect test reference before choosing. No unbiased benchmark accuracy or strong Direct matched result. |
| P0.7 | New independent advisory module `neumann1/prh_relational_macro_p07.py` fits typed data-derived AST with parameters, checks training originals and abstains on unsupported test inputs; **45/45** extended tests locally | The module induces instances of a **human-written language** and is **not yet integrated into mainline**. No JEPA run or autonomous new opcode invention. The GitHub core has a portable 5-test subset. |

All extended source, receipts, tests, the full first P0.5 failure and P0.5.1 separate result are in the locally generated evidence archive **NEUMANN1_PRH_P0_to_P07_Evidence_2026-11-03.zip** (76,093 bytes, SHA-256 `81bcad59801ae4c442a0dab706cc1af097e6a300bf7dabf370f676ec0e953035`). The archive includes an SHA256 manifest and the original Apache-2.0 license/attribution for copied ARC-AGI-1 examples. The archive is delivered as a conversation artifact, **not** embedded in GitHub; the GitHub core and tests are separately reviewable.

## Cost result (not iso-capability)

On the same **16 repaired-source study cells**, P0.5.1 summed **19.962212 ms** in study-region CPU wall time and solved 128/128. The fixed zero-clearance P0.4 baseline summed **8.733932 ms** and solved 32/128. These differ in solved capability, and exclude system-level overhead. They do **not** demonstrate a faster complete system, a 10× improvement, or measured FLOPs/energy/memory/currency savings. Those fields remain UNKNOWN, not zero. On zero-clearance cases where both have 32/32, the more general induction incurs overhead.

## First-principles research decision

1. **Retain typed-relational AST induction as optional mechanism evidence**, never as a global Q3 PASS. Examples only permit synthesis within the provided grammar. No semantic opcode outside that grammar was discovered.
2. **Reject premature neural JEPA training**: the demonstrated correspondence/program cases are handled by cheaper classical transformations and rules. No causal PRH/JEPA → new executable solver capability has been shown.
3. **Preserve failure and repair separately**: P0.5 first FAIL is immutable. P0.5.1 used disjoint seeds plus reference geometry audit; its PASS scope is local synthetic only.
4. **Degraded mode**: require abstention on contradictory data, nonidentifiable roles, partial/disconnected/multicolor scenes, unsupported geometry, competing ASTs or checker uncertainty; only independently verified original-task solutions are acceptable.
5. **Next high-value gate**: preregister a genuinely new *typed semantic primitive induction* mechanism, not just program selection/parameter tuning. Use not-preinspected original task families, duplicate/leakage audit, a strong matched classical synthesizer and Direct, an independent original checker and full discovery/execution/verification/fallback cost. A sole opened benchmark success cannot promote global Q3–Q7.
6. **No automatic mainline integration or CI GPU run** from this Draft research PR. P1.12 actual, P2 and sealed Frontier Gap remain on their own research admission contract.

## Reproduce minimal GitHub module

```bash
python -m pytest -q tests/test_prh_relational_macro_p07.py
```

The full local evidence archive additionally contains standalone P0.4, P0.5, P0.5.1, P0.6 experiments, archived first receipts, and the expanded test corpus. `neumann1/prh_relational_macro_p07.py` is not a complete NEUMANN architecture; it is a reviewed, bounded, classical component.
