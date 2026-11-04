# NEUMANN 1 — P1.0 first complete opened ARC transfer audit and STOP decision

Date: 2026-11-05 (Asia/Seoul)
Authority: `docs/research/frozen_north_star.md`. **Frontier-level problem solving with minimum necessary computation.**

## Registered design and provenance

The selection policy was frozen before task bodies were opened in `docs/research/prh_opened_arc_blind_p10_prereg_2026_11_03.md` and `docs/experiments/prh_opened_arc_blind_p10_cohort.json`. Upstream source `fchollet/ARC-AGI` public **training** corpus pinned at commit `399030444e0ab0cc8b4e199870fb20b863846f34`. Filename-only FNV-1a ranking selected 32 IDs among 400, excluding four previously inspected opened development IDs. Both the ID list and fixed evaluation code `experiments/prh_arc_blind_eval_p10.mjs` were committed before scoring. The two recorded result shards include all 32 IDs in original order. The first complete aggregate is `docs/experiments/results/prh_opened_arc_blind_p10_FIRST_COMPLETE.json`.

This is a precommitted **opened public ARC-AGI-1 transfer audit**; it is **not** an independent private/official ARC-AGI-2 evaluation, frontier task set, unseen program-family proof, or broad random sample sufficient to establish general performance. The selected task outputs appear only in original-task scoring, not in candidate building or route choice.

## First complete result (immutable FAIL)

| Method | Tasks solved exactly | Additional tasks |
|---|---:|---:|
| Frozen P0.3 classical finite DSL | **0/32** | baseline |
| Cascade: P0.3 → P0.7 typed spatial relation → P0.9 local rule induction | **0/32** | **+0** |

- The evaluator attempted **384** P0.3 candidate checks (12 per task). Every task had **zero** candidates satisfying its full train examples.
- Every task returned no P0.7 spatial-program candidates and no fitted P0.9 row-wise local rule in the resulting route.
- **32/32** task results were explicit ABSTAIN; none was marked solved and none received a favorable post-result rerun.
- Under the retained evaluation protocol, **P1.0 verdict = FAIL_NO_TRANSFER_SIGNAL**. Failures from P0.5 remain separately immutable and are not modified here.
- The 32-task run did **not** instrument end-to-end CPU seconds, FLOPs, RAM, GPU memory, electricity, cold start, verification or monetary cost. Candidate checks are work units, **not** a substitute for measured FLOPs or a complete-system cost claim.

## Diagnosis

This failure indicates **representation/hypothesis-space coverage** rather than ranking or selection among available consistent programs: not one rule from the small fixed DSL fit the full examples; follow-up representations were structurally too narrow. P0.7 handles two distinct connected monochrome objects and a particular axis projection; P0.9 supports two-symbol radius≤2 rowwise binary rules. These restrictions exclude many ARC object/scene/composition transformations. The experiments do not establish that all ARC problems are inexpressible or that a larger DSL/learned hypothesis space would succeed. They also do not establish why every candidate failed on an instance-by-instance semantic level.

The P0.4/P0.5.1/P0.8/P0.9 synthetic/local pass results remain valid **only at their preregistered bounded scope**; none rescues P1.0.

## Frozen stop policy

1. **STOP** changing the P1.0 DSL, P0.7 spatial program or P0.9 rule templates to fit these already-opened 32 IDs. No favorable re-score or revised thresholds can be called an independent P1.0 result.
2. Do not train a JEPA or scale model size merely because P1.0 failed. A learned representation has to produce an executable generalizable structure that the strongest deterministic comparator could not already obtain, at smaller **complete** cost.
3. Keep the P0.2 metric matcher and P0.7 typed executor as optional audited utilities, not the central Q3 architecture.
4. The next admissible gate is a **genuinely different, open-ended or extensible executable structure induction** on a separately preregistered new source split. Candidate discovery must be oracle-free and independently checked on original tasks; strong, matched deterministic enumerative/program-synthesis Direct receives equal operators, examples, budget and verifier. A new DSL with solutions coded in advance does not qualify as spontaneous discovery.
5. Preserve degraded mode: ABSTAIN on unsupported/ambiguous cases, then standard original-task verified Direct only when permitted. Attribute any Direct fallback's correctness and cost to fallback, not to discovered novel structure.
6. Recheck full Capability × Compute × Memory × Latency × Energy × Cost before advancing from Q3/Q4 mechanisms to Q5/Q6/Q7. Global Q1–Q7 **OPEN**; P1.12 and the P2/Decision3 admission path remain independent and untouched.

## Concrete next contract (proposed, NOT RUN)

- Split *new* original tasks into preregistered opened development, locked validation and sealed frontier-gap only after existing gates allow it. Run a contamination/near-duplicate audit before scoring.
- Separate **perception** (objects, topology, relational predicates), **induction** (typed transformation grammar that can grow under evidence), **execution** (deterministic program), and **independent checker** (original task). Do not claim the independent checker can prove unseen correctness from finite examples alone.
- Test three matched arms at fixed compute budget and equal task access: A) optimized classical enumeration; B) abstraction+enumeration, no neural model; C) identical path augmented with learned good-view proposals. If B matches C, delete the neural proposal. If A matches B, delete the abstraction layer.
- Declare exact timeouts, max generated candidates, verifier calls, data read policy, memory sampling, and accounting. Use first-run immutable PASS/FAIL/NOT_EVALUATED and no post-hoc best-seed reporting.
- Progress to original Q3/Q4 only after new executable behavior, independent correctness and discovery costs meet separately frozen criteria; the final Frontier Gap goal requires strong actual frontier solved cases and full measured iso-capability cost.

**Outcome:** stop this narrow generalization path and conserve compute; shift to evidence-bearing executable structure discovery. Never confuse high local synthetic training accuracy with real novel-task capability.
