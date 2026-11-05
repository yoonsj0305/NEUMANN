# NEUMANN 1 | P1.7 good operator views: first empirical FAIL and model-admission decision

Date: 2026-11-05 KST. Authority: `docs/research/frozen_north_star.md`. All Q1–Q7 globally OPEN. Frozen local preregistration `docs/research/q3_operator_good_views_p17_PREREG_2026_11_05.md` was committed before the first model run.

## First empirical result: retained without post-result tuning

Two **identical 122,744-parameter CPU convolutional encoders**, initialized with the same weights and trained for 400 AdamW batches with the same 6 operator categories, learning rate 0.002 and contrastive objective; only the formation of positive training pairs differed. Neither model was a JEPA reproduction; both are small contrastive representation learners for a highly constrained synthetic task.

| Evaluator | All 384 held-out query examples top-1 | Seen operator classes (288) | Unseen rotations (96) |
|---|---:|---:|---:|
| Same-operator **independent-execution views** | **310/384 = 80.73%** | **279/288 = 96.88%** | **31/96 = 32.29%** |
| Same-execution **noisy duplicate views** | **87/384 = 22.66%** | 23.61% | 19.79% |
| Untrained encoder and independent prototypes | **68/384 = 17.71%** | 19.79% | 11.46% |
| Exact deterministic operator-matching classical Direct | **384/384 = 100%** | 100% | 100% |

- First local registration required overall good-view >=80%, margin over bad >=15 **percentage points**, and **unseen operation >=50%**. The first two conditions passed; unseen rotation **32.29% fails**. Final local gate **FAIL_OPERATOR_VIEW_ABLATION** and cannot be rescued by revising seed/threshold.
- Good model CPU training **1.794 s**, bad **1.710 s** measured region. Both had **122,744** trainable parameters and equal batches. Process max RSS **372,016 KiB** (Python and torch, not model-only peak).
- The evaluation's support/query encoder inference for good model **0.162 s**, while direct symbolic operator execution/checking on 384 queries took **0.0188 s**. The tasks are not matched in accuracy, and prototype inference includes support calculation; no iso-capability compute advantage may be asserted.
- Five code/contract unit tests **PASS**, first JSON receipt is immutable at `docs/experiments/results/q3_operator_good_views_p17_FIRST.json`; GitHub and container copies checked for identical size and content. No actual public ARC task scoring or independent original-task generalization in P1.7.

## Scientific caveats that must not be deleted

1. **Not identical original-sample exposure:** Good-view training uses two independent original scenes per operator per batch (400×6×2 = **4,800** underlying execution samples). Bad-view training uses only one original scene per operator per batch (400×6 = **2,400**) and two independent noisy copies. Thus even with matched optimizer steps and architecture, the contrast mixes positive-view definition **with 2× underlying distinct-scene exposure**. The 80.7% vs 22.7% effect cannot be attributed solely to better pairing. A matched-unique-scene control would be required for a clean causal estimate.
2. **Operator identity supervision:** Generating good positive pairs requires knowing the operator identity in the simulator. Although no identity label is passed as an input feature, it selects positive pairs at training time. This is **not oracle-free discovery of a new program**.
3. **Seen vs unseen gap:** Training on six transformations did not produce adequate transfer to withheld 90-degree rotations. A good representation alignment signal is not a semantic generalization guarantee.
4. **Strong symbolic counterexample to adoption:** For this exactly known 8-operator family a deterministic matcher correctly identifies the operation on **all 384** query pairs. Training a neural model is strictly unnecessary to achieve that capability, and its training costs cannot be ignored.
5. **No JEPA guarantee:** The 2026 Balestriero & LeCun arXiv `2610.39302` theorem pertains to paired observations of *one latent scene*, not paired executions of a shared action on *different* scenes. This experimental adaptation has no theorem-backed convergence guarantee. The published 42× figure concerns samples to alignment, not reasoning or complete cost.

## First-principles go/no-go

**NO-GO for neural training as a NEUMANN Q3 core component based on P1.7.** Stop multiplying toy transformation/metric experiments, preserve the failed first receipt and do not add a JEPA just because alignment improves.

More decisive next question: what aspects of the **task goal/required action** must a representation preserve so that a shared scene embedding can actually determine a useful executable operator? A latent of the scene alone can be perfectly aligned yet insufficient when the required transformation depends on an independent instruction. Prove the information-theoretic necessity and introduce a **task-sufficiency gate** before trying new training objectives. Only then run a newly preregistered real original-task gate against strong classical Direct and P1.6 exact semantic quotient at full costs.

Global Q1–Q7 **OPEN**. P1.5 1/32 FAIL and P1.6 3.62× bounded classical saving with 10× FAIL remain separate. No mainline or sealed benchmark modifications.
