# NEUMANN 1: PRH/JEPA adoption decision after P0, P0.1, P0.2, P0.3

Date: 2026-11-03 (Asia/Seoul). Scope: opened development, not a sealed general evaluation. Governing authority: `docs/research/frozen_north_star.md` and its Q1-Q7. First P0, P0.1, P0.2 and P0.3 results remain separately retained and unchanged. P1.11.1 FAIL and P1.12 actual NOT RUN remain intact.

## Executed evidence and interpretation

| Pilot | Method | Local evidence | Decision boundary |
|---|---|---|---|
| P0 | Linear orthogonal Procrustes, paired independent synthetic sensor readings | IID 128/128; sparse shift 118/128; entirely new sensor 1/128. Unit tests 5/5. | Good views can align under a frozen sensor; no JEPA. |
| P0.1 | Pair-free full-scene sorted distance fingerprints + Hungarian matching | New-sensor IID 128/128, sparse 118/128; unrelated worlds produce high geometry mismatch. Tests 8/8 cumulative. | Shared full-scene metric geometry is identifying context, not a general latent world model. |
| P0.2 | 4 fresh seeds x 5 adversity cases, guarded classical matching | Rigid new sensor 4/4 scenes accepted with 128/128 correct each. Nonlinear warped views 6,17,11,8 / 128; partial scenes 4/4 ABSTAIN; perfect symmetry 4/4 ABSTAIN; unrelated worlds 4/4 ABSTAIN. Local protection gate passes, full-transfer hypothesis fails. | Restrict geometric tool to metric-preserving complete scenes; threshold 0.08 is exploratory from earlier diagnostics. |
| P0.3 | Human-specified fixed mini-DSL synthesis on four **opened public ARC-AGI-1 tasks** | Test exact 3/4, task IDs 007bbfb7, 08ed6ac7, 0d3d703e solved; 05f2a901 ABSTAIN. 12-13 candidates, 12-20 candidate executions per task. Source fixture canonical hashes independently confirmed identical to upstream. Combined tests 16/16. | Executable validation interface works on these **pre-inspected, task-informed** examples; **zero self-invented operators** and no use of P0.1 matcher in this solver. |

**Attribution guard:** These four ARC files were copied exactly from `fchollet/ARC-AGI` (`data/training`) and are Apache-2.0-licensed. They were selected after the researcher had already viewed training AND public test examples. A per-task result of 3/4 is only an opened-development demonstration, NOT a benchmark accuracy estimate or fresh generalization. Test answers were withheld from the synthesizer function, but the program grammar and task selection were affected by pre-inspection. Both limitations are retained.

## Main scientific finding

P0.1 shows that shared relational invariants can eliminate coordinate alignment under strong geometric assumptions. P0.2 demonstrates those assumptions are essential. P0.3 establishes an executable candidate/verifier interface but has **no causal connection to good-view alignment**: using a hand-coded grammar, classical search alone solves 3 pre-inspected tasks and fails one. Thus the value of neural JEPA for Q3/Q4 remains **not demonstrated**. Spending GPU computation to train JEPA from these four results is rejected. The failure is an information problem (no candidate program) rather than a shortage of embedding similarity scores.

## First-principles deletion / go-no-go

1. Delete unconditional general geometric alignment. Reuse P0.2 only for fully observed rigid scenes with no duplicate fingerprints, with abstention on uncertain views and direct fallback.
2. Delete premature JEPA training. Re-activate only after a **frozen strong classical baseline** fails on original executable tasks, and a meaningfully different learned signal has a falsifiable chance to recover capability.
3. Keep Q3 as **oracle-free program/opcode discovery** rather than choosing an operator from a known list. Changing representation without inventing executable structure does not pass.
4. Do not run new sealed benchmarks or bypass P1.12's separate actual experiment. The current P1.12 joint cross-encoder is an independent mainline attempt; PRH is an optional research branch.
5. Preserve all cost fields as UNKNOWN when not measured. There is no valid software Idiot Index using raw material prices; report measured executed CPU/GPU work, training amortization, verification and fallback instead.

## Next falsifiable Q3 experimental gate (NOT RUN)

- Inputs: fresh task families with independent train/test source and no data pre-inspection, near-duplicate group and generator leakage audit. Baselines: strongest matched deterministic program synthesis using the exact same primitive set, P1.12 where semantically eligible, and resource-matched direct model/tool route if available.
- Intervention: an operator-induction mechanism that can emit **typed executable program ASTs/grammar rules not present as a fixed task-specific candidate**, together with a verifier-checkable behavioral specification; good-view relational features are only one optional source of hypotheses.
- Local admission: at least one additional independently verified original-task solution over the strongest matched Direct and no reference/label access during discovery. Report first failures, stochastic seeds, total cost including fitting, hypothesis search, execution, verification and all failed routes. A sole developer task win does not close global Q3.
- Joint Q3/Q4 only after meeting the existing retained 0.80 utility-recovery policy, a separately frozen discovery-cost-vs-savings coefficient and complete original-task correctness. Q5/Q6/Q7 still require strong Direct, new-family/fresh and real Frontier Gap matched evaluation. No threshold retuning after results.
- Degraded mode: output ABSTAIN + verified Direct on unknown operator / conflicting programs / unsupported sensor. Do not silently treat a fallback solution as a novel discovery.

## Original project aim still frozen

**Frontier-level problem solving with minimum necessary computation.** A genuine outcome requires new capability at iso-capability end-to-end cost advantage, independent original-task correctness, new-family transfer and eventual verified Frontier Gap recovery. **Global Q1-Q7 are all OPEN.**
