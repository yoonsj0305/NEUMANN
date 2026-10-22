# NEUMANN 1 | Q3 first12, stronger baseline and structural ablation | 2026-10-22

## Scientific outcome

**SCOPED SOURCE-UNOPENED-WITHIN-THIS-CAMPAIGN STRUCTURAL CLASSICAL TRANSFER = PASS.** A frozen, zero-training, source-only affine/guarded Houdini proposer generated certified inductive invariants for all **12/12 authentic SyGuS originals** from metadata/SHA-registered files before this campaign read their bodies. Independently reconstructed **36/36 original Init/Consecution/Goal formulas are UNSAT in both Z3 and pinned cvc5 1.4.2**, and 24 invalid-candidate controls were SAT in both. The original first CI archive is preserved.

**Scientific boundary:** the 12 are from two public anthology folders, not proven independent authors or absence from all historical exposure; the grammar and engine were developed on eight already-opened originals. These are classical, no neural learning, no learned-exclusive proof, no frontier level or global Q3/Q4/Q6 close.

### Summary, exactly as executed

| Experiment | Safe original 3VC | Notes |
|---|---:|---|
| Prior already-opened dev8, frozen source-only classical | 8/8 | Independent Z3+cvc5 24 original VCs |
| New preregistered source12 | **12/12** | Independent Z3+cvc5 36 original VCs |
| Post-only inductive candidate | 6/12 | Six need strengthening |
| Univariate generated relations + original Post, no guard features | 10/12 | Two failures retained |
| Pairwise signed affine relations + original Post, no guard features | **12/12** | Same source, same independent original proof authority |
| Triple-/four-way signed affine, no guard features | 12/12 | No additional coverage |
| Full original guarded grammar | 12/12 | No additional coverage |
| Strong raw Z3 SPACER 4.13.3, 5s original/task | 9/12 | 3 UNKNOWN (not UNSAFE) |

### Exact per-original ledger

| SHA-pinned official source basename | Post-only | Unary pool + Post | Pairwise pool + Post | Full grammar + Z3/cvc5 | SPACER at 5s |
|---|---|---|---|---|---|
| `anfp.sl` | FAIL | PASS | PASS | PASS | UNKNOWN |
| `sum4.sl` | FAIL | FAIL | PASS | PASS | UNSAT |
| `ex11.sl` | PASS | PASS | PASS | PASS | UNSAT |
| `ex14.sl` | PASS | PASS | PASS | PASS | UNSAT |
| `w1.sl` | PASS | PASS | PASS | PASS | UNSAT |
| `cegar1.sl` | FAIL | PASS | PASS | PASS | UNSAT |
| `gsv2008_true-unreach-call_true-termination.sl` | PASS | PASS | PASS | PASS | UNSAT |
| `inria-00615623_4.sl` | PASS | PASS | PASS | PASS | UNSAT |
| `gj2007b_true-unreach-call_true-termination.sl` | FAIL | PASS | PASS | PASS | UNSAT |
| `fib_30_x.sl` | FAIL | PASS | PASS | PASS | UNKNOWN |
| `minor3.sl` | PASS | PASS | PASS | PASS | UNSAT |
| `fib_28.sl` | FAIL | FAIL | PASS | PASS | UNKNOWN |

No sources were dropped, and no late-added successes are included. In the ablation, `sum4.sl` and `fib_28.sl` fail with unary-generated candidates but succeed with pairwise-generated candidates using independently checked original 3VC. This proves **necessity relative to the fixed source-to-candidate algorithm and grammar in this test**, not a universal invariant lower bound.

### Measured work and deletion

- First 12 proposer wall: 1.784 s; independent two-backend checker wall: 0.886 s, separate phases, not a single paired performance comparison.
- Ablation posthoc support1 / support2 / support3 / support4 / full proposer wall: 1.783 / 0.552 / 0.685 / 0.679 / 0.8 s on one CI job, fixed order (not replicated random order).
- Sum of generated initial candidate pools, support1 / pairwise support2 / full grammar: 231 / 591 / 791. So pairwise-only drops **200/791 = 25.3%** initial candidates while retaining 12/12 on this cohort.
- Source-only SPACER correct 12 run produced 9 UNSAT, 0 SAT, 3 UNKNOWN and total wall 15.227 s. This is a *different GH Actions process*, not sufficient for a precise paired end-to-end speedup ratio. SPACER UNKNOWN is not a proof that classical solvers generally cannot solve a task.
- Earlier SPACER test erroneously recorded 12 unsupported parser errors due an older system libz3. This infrastructure failure is preserved as `first_spacer_protocol_error.zip`, **not** a scientific 0/12 outcome. A pinned wheel backend was used for the successful baseline run.

## Highest value first-principles decision

1. Delete automatic neural fitting from this corpus; an untrained classical engine already certifies all 12. Additional *unique verified solved* cases from a neural model on this exact cohort are mathematically zero by set coverage.
2. Use exact original Post-only when inductive; then exact pairwise source relations with Houdini; only enable richer predicates if needed. This deletes larger feature enumeration where pairwise suffices. Keep independent original authority.
3. SPACER remains a strong source-only baseline and degraded mode; 5s UNKNOWN is UNKNOWN. Do not claim a new mathematical primitive or frontier model comparison.
4. Reaching global learned Q3/Q4/Q6 requires **new and truly independent source groups** with a preregistered learned proposer beating a strong same-source, same-budget nonlearned portfolio on verified solves *or* total work while retaining accuracy. The current 12 are a classical baseline capability proof, not a neural breakthrough.
5. Degraded mode: any source SHA mismatch, parser incompatibility, solver disagreement, certificate UNKNOWN, or unsupported state -> ABSTAIN, never SAFE.

## Original external links

- [Source repository at pinned revision](https://github.com/SyGuS-Org/benchmarks/tree/13c8deb68a873635879c9a69bc78caebd340f646)
- [Original frozen PR #447](https://github.com/yoonsj0305/NEUMANN/pull/447)
- [First completed official original12 run #39700991534](https://github.com/yoonsj0305/NEUMANN/actions/runs/39700991534); artifact #12391924371.
- [Strong source-only SPACER corrected run #39701925528](https://github.com/yoonsj0305/NEUMANN/actions/runs/39701925528); artifact #12393111452.
- [Support-size controlled ablation #39702267051](https://github.com/yoonsj0305/NEUMANN/actions/runs/39702267051); artifact #12393426223.

## Reproducibility

This archive contains the complete original first12/earlier-dev8 JSON receipts, the first malformed SPACER baseline (retained), the corrected source-only baseline, the five-arm controlled grammar ablation including all independent Z3+cvc5 query receipts, plus frozen git blob registry, proposer, independent checker and strong-baseline executable. Original SyGuS source file bytes are obtained by the pinned Git commit / original SHA registry rather than redistributed here. Full GitHub archived ZIP digests are preserved by the repository and in `MANIFEST_SHA256.json`. Not yet merged to main. Global Q1–Q7 remain OPEN.