# NEUMANN 1 · P2.2 external executable-program teacher | first scientific decision
Date: 2026-11-05 KST. North Star: **Frontier-level problem solving with minimum necessary computation**. **All global Q1–Q7 remain OPEN.**

## First-source protocol and independent data
Official `fchollet/ARC-AGI` public `data/evaluation` files pinned to `399030444e0ab0cc8b4e199870fb20b863846f34`. The eight original task IDs were chosen by filename hash (excluding all 96 P2.1/P2.1.1 reserved evaluation files) **before opening their task bodies**. Model-visible tool responses contained all original TRAIN input/output grids and TEST **inputs only**, with TEST outputs stripped inside each connector call. The seven original pure-JS teacher programs and one explicit ABSTAIN were committed **BEFORE first original test gold scoring** at `experiments/q3_open_program_teacher_p22_FIRST_PROPOSAL.mjs` (blob `d82f09406b4b3ee4e9651c261013c8ce8aa850c7`). No post-score edits or retries.

## First original-task performance
- External GPT-6 teacher: **seven submitted pure executable programs**, all **24/24** corresponding training pairs exact; **7/8** whole public evaluation tasks exact (7/7 test grids for submitted programs); **one explicit ABSTAIN**, **zero submitted wrong outputs**. The abstained task contributed two more train examples, so total available train pairs =26, 24 matched by the 7 submitted programs.
- Frozen strong baselines on **the same eight cases**, **B=P1.1 0/8, Q=P1.6 0/8, P20=P2.0 0/8, C211=P2.1.1 0/8**; combined 0/8. Teacher yields **+7 original-task successes** over these evaluated programs. Local preregistered **external-teacher proposal interface PASS** (>=2 extra and zero false accepted).
- The **independent cell-by-cell audit** checked every original train and test output, original first source/blob identity, and that mutating gold test answers invalidates scores while leaving submitted program execution unchanged. Audit PASS. Original first result `docs/experiments/results/q3_open_program_teacher_p22_FIRST_SCORE.json`; audit `docs/experiments/results/q3_open_program_teacher_p22_INDEPENDENT_AUDIT.json`.

## Bounded relative expressivity: the most important causal diagnosis
All frozen Direct variants were run on original TRAIN examples and returned train-fit program counts. Six original public evaluation tasks solved by the external teacher had **zero exact training-consistent candidate programs** in each of B's bounded 500-program library, Q's depth≤3 grid composition search, P20's 1,598 typed affine/panel AST candidates, and C211's object-rewrite candidates. IDs: `bd14c3bf`, `19bb5feb`, `9a4bb226`, `e872b94a`, `aa18de87`, `66f2d22f`.

A seventh teacher-solved task `32e9702f` had **two training-consistent** P20 ASTs, but their distinct original TEST-input predictions caused mandated `AMBIGUOUS_PREDICTIONS_OR_UNSUPPORTED_INPUT` abstention; this task is a **disambiguation deficit**, not a zero-candidate deficit. The eighth task `759f3fd3` remained unsolved by both teacher and Direct.

Across these 8 tasks the Direct engines attempted B **4,000** candidates, P20 **12,784** ASTs, C211 **5,039** object ASTs; Q executed **46,898** individual grid operators. These are not matched to GPT-6 generation compute.

**Conditional proof:** For a fixed evaluated candidate set H and original TRAIN D, if `H_D={h in H : ∀(x,y)∈D, h(x)=y}` is empty, any selector/reranker confined to H is unable to produce a training-consistent executable program. Thus representation alignment, a better ranking network, or more compute devoted solely to choosing a member of that same H cannot close these six deficits. Need a candidate generator that **expands the reachable executable program space**, or a different correct problem representation/program language. This is a finite-candidate impossibility result, **not** an AGI theorem or a claim that all classical search cannot solve them. No claim of novel operators never previously known to computer science.

## Interpretability of proposed programs
The teacher programs use independent row/fill/shift rules, 2×2 quadrant abstraction, connected-component topological signatures, unique multicolor component selection, joined-zero panel logic, and counting of connected snakes. All are executable pure-JS functions operating on original grids; the program *registry* maps source IDs to functions for the harness, but the functions themselves never check a task ID or exact test-input fingerprint. This is **external teacher-written code**, not a trained NEUMANN model.

## Scientific limitations and real cost
- **Public evaluation set** may already have been in GPT-6 pretraining: program-code generation from train pairs and held-out target separation does NOT establish uncontaminated generalization.
- Small **n=8**, selected by deterministic filename hash rather than stratified family difficulty; 7/8 cannot be extrapolated to frontier-level reasoning accuracy or ARC-AGI-2.
- Teacher generation tokens, elapsed end-to-end thinking, memory/energy and monetary cost were **NOT metered**. P2.2 therefore **does not prove minimum necessary computation, iso-capability Pareto dominance, or any 10× advantage**. On comparable hardware the classical programs were cheap but had insufficient original-task coverage.
- The typed executable runtime is not a secure sandbox merely because a manually authored pure JS source passed audits. Never execute arbitrary future generated source in production without sandboxing and typed verification.
- The teacher programs have **not** been converted to a transferable student proposal policy. Previous P1.4 naive cache of four programs transferred **0/24** on novel original tasks. Do not call this self-learning or learned abstraction.

## Strict research decision and next contract
**GO**: preserve a teacher-to-typed-program proposal interface, original independent verifier, immutable candidate/code provenance, strong classical B/Q/P20 baseline, exact semantic quotient and sound shape pruning.

**STOP**: adding another 20 manual object/ARC-specific pattern templates to a fixed library, pretending that a learned ranking/JEPA alignment metric alone creates unreachable new executable operators, treating external teacher capability as NEUMANN Q3 PASS.

**NEXT ONLY IF INDEPENDENTLY VERIFIED (NOT RUN):** (1) distill the structural code/AST transformations and their goal-conditioned applicability into a learned program proposal policy which can generate **an operator schema absent from its frozen training library**; (2) evaluate on wholly new task/distribution/family with source sealed before generation and no teacher in the inference path; (3) require more correct original tasks than the strong exact classical Direct and complete teacher/train/inference/compile/verification/fallback cost below a justified amortization bound. If no additional verified original-task capability or full-cost improvement, delete that student component and retain classical Direct in degraded mode.

WBS **Estimate**, not deadline: typed safe proposal/verification interface 6 engineering hours; provenance and code-independent semantic AST verification 6h; teacher-to-student dataset/learning prototype 10h; new-family independent test 8h; total resource-metering 5h; risk/failure audit 3h; buffer 10h = **48 engineer-hours estimated**. Never reinterpret 48h as a guarantee of success.

All global Q1–Q7 OPEN. Draft research only. No sealed Frontier Gap or P1.12/P2/Decision3 gate altered.
