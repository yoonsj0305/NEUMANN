# NEUMANN 1: high-efficiency system research gates

Updated 2026-09-30. Goal: a system with substantially less **total** compute
at fixed independently verified capability, not victory in one solver subroutine.
"Model" means the complete inference system; a small learned component alone
does not constitute the desired model. No extrapolation from a synthetic
family to general reasoning capability is permitted.

## Q1 — Does learned structural discovery pay for itself?

**Decision on v0.0.33–0.0.36 exact affine-linear family: No.** v0.0.68
measures the entire existing frozen path; all 32/32 cases verify in each
method, but n=32 learned inference is ~95–104 ms versus ~3.2–3.4 ms for
exact direct, despite lower *final* solver arithmetic counts. The learned
scorer alone takes ~9 ms. Stop promoting this model on this family. This
does not establish impossibility on other tasks or larger dimensions.

## Q2 — Where is compression actually profitable?

**Open beyond the studied affine family.** v0.0.69 found no opportunity at
n≤32 after adding a fast numerical direct proposal with exact original
verification and exact fallback: n=32 direct took ~0.31–0.33 ms versus
~110–116 ms learned compression (4 new cases/cell, 5 repeats/case, all
verified). Define and measure a different family where direct verified computation is
costly enough that discovery, validation, reconstruction, and verification
can collectively fit beneath it. Select the family for principled structure
and genuine difficulty, not because one particular method won preliminary
timings. Require strongest cheap deterministic and optimized direct
baselines. Pre-register the minimum capability and costs before final data.

## Q3 — Is learned discovery needed beyond cheap tests?

**Open.** Construct a matched-observable case where cheap deterministic
features are insufficient and a model predicts a useful compressible
structure from admissible input; no hidden oracle labels at inference.
Compare to a strong deterministic search and equal-budget direct learner.
If learned discovery costs more than it saves, disable it.

## Q4 — Does NEUMANN itself beat a matched direct model?

**Open.** v0.0.31's 2×2 neural demonstration is a capability feasibility
result, not evidence of lower total compute. Hold fixed problem distribution,
training data budget, quality target, hardware, warm-up convention, and
verification contract. Report model inference, deterministic tooling, retries,
memory, and training amortization separately. At matched verified quality,
compare capability-versus-total-compute frontiers, not parameter counts.

## Q5 — Are scaling and cross-domain reuse real?

**Open.** Only after Q2–Q4 pass: test larger apparent sizes and independent
domains, randomized surface forms with held-out structural classes, cache
misses and invalidation, and separately report cold and warm traffic.
Estimate uncertainty in the log-compute slope; do not infer improved slope
from the reduced solver dimension alone.

## Stop / advance rules

Advance only on exact, independently checked success and end-to-end
iso-capability total compute. A result that improves a proxy but worsens
complete time is a failed compute gate, not a partial speed win. Retain
negative results and costs for all failed proposals. If a cheap deterministic
component saturates a family, do not train a model merely to have one.

Immediate next experiment: seek an identifiable input regime in which
full-path savings remain possible **after** strong direct computation,
reuse, batching, and exact verification. Freeze its capability criterion
and comparators before a final holdout. The v0.0.68 score-only lower bound
rules out a checker-only rescue for the existing n≤32 learned path.
