# Q3 structure-learning mechanism: affine expressivity theorem

**Scope:** Exact observed integers, 24 source-body-blind historical programs opened in PR403/404, trained PCA procedure fixed in PR399/400. Mathematical statement is elementary linear algebra, **not a newly discovered theorem**.

Let the original native Pre/Trans trajectory samples of a program be \(x_0,\ldots,x_m\in\mathbb{Z}^d\). Define \(D\in\mathbb{Z}^{m\times d}\) with rows \(x_i-x_0\).

For every affine candidate \(a^\top x=b\), \(a\in\mathbb{Q}^d,\ b\in\mathbb{Q}\), matching **all** observed samples:

\[
a^\top x_i = b \quad \forall i \iff D a=0,\quad b=a^\top x_0.
\]

Thus **every sample-consistent rationalized PCA candidate coefficient vector lies in \(\ker_\mathbb{Q}(D)\)**, computable by exact rational Gaussian elimination. No model fit is needed to represent this family. The PCA model may still choose a useful basis faster or help with bounded Houdini, but cannot have an exclusive affine *representational* advantage when the classical baseline has the same exact observations and can select linear combinations of its basis.

The GitHub Actions experiment checks this machine-verifiably on the original programs' actual Z3-sampled native states and on every concrete PCA-fitted candidate. It does NOT assert all sampled candidates are globally inductive: universal original Pre/Trans proof requires independent source-native Z3 and cvc5, as in PR400/401, while complete final safety additionally requires original Post (PR403/404). **24 originals with 19 learned complete proofs versus 20 exact-classical complete proofs** are compatible with this theorem, not a contradiction.

## Falsification target and architectural consequence

If any rational affine candidate fits all the exact observed integer samples but is not in the exact rational nullspace, this statement or the implementation is wrong. The test must fail rather than silently skip such a case.

First-principles R&D priority: stop scaling more PCA models within this exact affine search family merely to chase an exclusive Q3 discovery claim. Improve either **computation cost** (compare energy/wall of equivalent original source proofs with a strong exact baseline) or **genuinely new structural classes** (guards, disjunction, nonlinear/multiphase invariants), and run a new source-body-blind benchmark with all solver rights equal. Do not close global Q3/Q4 without that evidence.

Failure mode/degraded path: when learned hypotheses are absent, unsupported or fail independent native inductive proof, abstain or invoke an exact classical solver, never output unverified SAFE.
