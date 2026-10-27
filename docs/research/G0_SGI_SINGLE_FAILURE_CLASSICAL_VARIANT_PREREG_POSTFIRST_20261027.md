# NEUMANN 1 | G0 SGI classical residual adjudication · post-first pre-config freeze · 2026-10-27

## Scientific status

Only one **already opened** source-only original SyGuS-SGI task remained false for CVC5 1.1.2: hard/PRE_76_10/PRE_76_10.sl from the immutable first benchmark (the first 12 source-only candidate raw SHA and Z3 11/12 original grade remain untouched). **This is strictly POST-FIRST, not a new blind success or Q1–Q7 promotion.** Goal: determine whether its single-model wrong extrapolation is a brittle solver-policy tie rather than a substantial search/representation barrier.

### Immutable input
- Upstream Barnard-PL-Labs/sygus-sgi-1 @ `e7ae840e5546e9243ff94afb1a29064fc050011c`.
- Exact file `data/benchmarks/hard/PRE_76_10/PRE_76_10.sl`, no new or substituted benchmark.
- Remove the **last ground constraint** from the *solver* input with the previously checked balanced-parser method, retaining all other 9 source constraints and exact original grammar and helper definitions. NEVER reveal the heldout tenth ground pair to cvc5.
- Record full solver input SHA, original git blob SHA, the source-only SHA from frozen first, the exact first cvc5 stdout SHA for identity.
- Never use heldout output to generate, select, tune or choose among cvc5 variants. Generate **all 8 exact arms below** and freeze stdout and all metrics before running a separate verifier on heldout original.

### Eight pre-fixed classical C arms

All use native Linux cvc5 1.1.2 with `--lang=sygus2`, at most 15s wall and 12s CPU per attempt, same original 9 input/output constraints, max sampled RSS 800MiB; exactly one attempt/arm:
0. `--seed=0` (original default replay sanity)
1. `--seed=1`
2. `--seed=7`
3. `--seed=17`
4. `--sygus-enum=smart`
5. `--sygus-enum=fast`
6. `--sygus-enum=random --seed=1`
7. `--sygus-unif-pi=cond-enum-igain`

If CLI rejects any arm, report that arm `HOLD_UNSUPPORTED` and preserve stderr. No silent configuration substitution after watching results.

### Source-only candidate acceptance
Each arm's output must include one valid `define-fun f` (candidate) with zero errors, SHA recorded. Candidate can still be WRONG on future. Record source inputs and candidate hashes. At POST-FIRST independent grading, verify each arm's original 9 source constraints and original 10th heldout with **separate Z3 4.13.3** in fresh processes as before; report **all eight**, no winner chosen in hindsight as prospective first. If >=1 passes, label `CLASSICAL_POSTFIRST_RECOVERY` ONLY; original frozen first remains 11/12. If all fail, classify `EIGHT_CLASSICAL_VARIANTS_FALSIFIED_OR_HOLD`, not impossible for all classical methods.

### Fairness and decision
This is a **diagnostic of classical search robustness**, not Q1/Q3 scientific proof and not ownweight policy learning. Source benchmark already read; do not treat as new frontier parity. Summed CPU/wall and source budget per 8-arm portfolio charged; selecting best arm after graded gold **is oracle leakage** and must not be presented as a deployable automatic policy. To deploy, pre-fix source-only consensus or request an authorized, separately priced additional real source label, then conduct a *new blind cohort*. No neural G1 money until strong matched-rights residual semantic opportunity survives.
