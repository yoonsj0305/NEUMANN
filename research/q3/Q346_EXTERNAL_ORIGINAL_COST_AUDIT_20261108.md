# NEUMANN 1 Q3/Q4/Q6 | External original result and cost gate

Date: 2026-11-08. Source: GitHub Actions `42474777128`, artifact `q3-fifth-disjoint-original-bulk-program-frozen`, original ARC-AGI-2 **training** tasks at pinned upstream `f3283f727488ad98fe575ea6a5ac981e4a188e49`. This is not the official ARC evaluation.

## Frozen external-author experiment

- Fifth disjoint cohort: 128 original training tasks, excluding 608 earlier selected originals.
- 102 evaluated, 26 skipped due to source-example prerequisites.
- Classical correct: 2; previous 2-attempt composed baseline correct: 2.
- New invented parallel-object program correct: 1; combined 2-attempt correct: 3.
- New residual originals: **1**, ID `12eac192`; existing correct answers lost: 0.
- Source-fitted invented bulk programs: 2; one generalizes to its original hidden target.
- Frozen predictions SHA256: `45d4ef777ba60e9e0e27a9620cc95e219eea8ab05f3cd327ac61a9fa0658ddd8`.
- Blind process: source task training examples only to proposer; test gold accessed by separate scorer after SHA freeze.

## Q4 measured runtime and outcome

The same 102 evaluated originals are used for baseline and treatment. Summed benchmark times from frozen original artifact (seconds):

| Component | Time |
| --- | ---: |
| Classical | 8.22749 s |
| Previous composed inventor | 8.74047 s |
| Previous object inventor | 1.80581 s |
| **Previous path subtotal** | **18.77377 s** |
| New bulk invention | **0.23707 s** |
| **Previous + new bulk subtotal** | **19.01084 s** |

On this narrow cohort, +1 correct answer costs 0.23707 s additional cumulative source-invention time. The new component adds **1.263%** to the measured subtotal. Correct original tasks per measured component-second changes from 2/18.77377 = **0.10653** to 3/19.01084 = **0.15780**, a **1.481x** ratio. These are conditional *component-level throughput proxies*, not independently measured complete system wall clock or frontier model comparisons. The 2/102 and 3/102 samples are small and highly cohort dependent. **Q4 global 10x NOT PASS**.

## Q3 and Q6 epistemic boundary

Q3 has **one positive independently authored original training-task residual** with an executable source-invented program. Its predicate vocabulary, component extraction and color operations remain human supplied. **Global autonomous invention NOT PROVEN**.

Q6's typed representation adapter evaluates the *same executable Boolean AST* on graphs and tables through a declared feature map, without relearning. A passing test establishes cross-encoding invariance on a shared feature ontology, not autonomous discovery of an unrelated ontology or new mathematical domain. **Global Q6 NOT PROVEN**.

## Failure cause and next decisive test

- Earlier pairwise mover/anchor invention: 0/116 correct, 0 source fits on fourth independent cohort; representational mismatch.
- Bulk object-set invention: 1/102 residual on fifth cohort; weak coverage and selection prior.
- Most promising bottleneck is **unbounded representation discovery**: source-difference-derived object partitioning and relations beyond hand-coded typed grammar. Expand *only* if measured heldout residuals improve over a classical matched search under the same budget.
- Require separate evaluation cohort, stronger classical synthesis baseline, total end-to-end time/energy, and genuinely different semantic problem family before Q3/Q4/Q6 global PASS.
