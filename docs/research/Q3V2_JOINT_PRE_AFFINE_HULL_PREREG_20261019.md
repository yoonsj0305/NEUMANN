# Q3V2 · Exact Pre-affine-hull / all-branch nullspace intersection (2026-10-19)
**Pre-registration before Q3V2 source-check workflow.** Parent branch is Q3V, not main. Baseline first runs and their SHA are immutable; this is a new *development-only classical representation fix*, not unseen-family evidence, learned discovery, nor global Q3 closure.

## Prior observation and fixed hypothesis
Q3V checks each basis vector of the all-branch conservation/reset nullspaces separately for a source Pre-forced value. This is incomplete because a linear combination can be Pre-forced even when none of its basis vectors is.

Fixed constructed counterexample: original `Pre=(x+y=0 ∧ t=0)`; exact `Trans=(x'=x ∧ y'=y ∧ t'=t+x+y)`; `Post=(t=0)`. Q3V rejects standalone e_x and e_y, while the joint equation `x+y=0` is preserved and `I=Post ∧ (x+y=0)` satisfies the 3 unmodified VCs. Post alone is not inductive. Mutating t' by +1 must invalidate the old proof.

## Algorithm, costs, and negative gates
1. Compute exact affine hull of `Pre` using SMT models x0 and repeated counterexamples outside the currently spanned affine hull D. Each round either produces an independent new direction or returns UNSAT proving the full affine hull; at most n-dimensional progress with n<=8. SMT UNKNOWN or timeout => ABSTAIN, never an approximate hull.
2. For every bounded exact source transition branch (inherited Q3V parsing), jointly compute rational nullspace of `(Aj-I)^T c=0`, `bj^T c=0`, and `D^T c=0` for conservation. For reset intersect `Aj^T c=0` for all j, `(bj-b0)^T c=0`, `D^T c=0`, and `(x0-b0)^T c=0` directly. Derive k=c^T x0, normalize primitive integers. Avoid testing individual basis candidates prematurely.
3. Every proposed relation independently requires original `Pre⇒R` and `R∧Trans⇒R'` negations UNSAT. Combined unchanged-source `Post∧AND(R)` must satisfy all three original VCs for an original safety PASS. An unsupported branch, model UNKNOWN, source parser mismatch, or invalid proof cannot be counted.
4. Tests frozen ahead of first source workflow: single-branch constructed positive, two guarded branches, branch mutant, wrong transition mutant, true joint reset, exact rational algebra; source-only Post control. Reuse **exact same ten already opened Q3V source files** only as regression (NEVER blind performance or new scientific evidence). Preserve all ABSTAIN and failures.
5. No extra neural training, GPU or paid API. Equal-original-solved full cost vs SPACER has NOT been demonstrated. Avoid claiming any universal affine invariant completeness: the kernel is complete only for global common affine conservation/reset equations over fully characterized Pre hull; conditional, nonlinear and arbitrary inductive relations are not covered.
6. Stop after first CI and record exactly its status. No repeated calibration on FiB to inflate counts. All global Q1-Q7 remain OPEN. The Q3V first fixed Action #39175953888, independent repeat #39176159370, original success counts, and 9/10 vs 8/10 specialist variability remain immutable.

**Admission of narrow result:** exact algebraic joint relation present when old per-basis approach misses it; the same constructed original Z3 three VCs pass and mutated variants fail. Anything short of successful Z3 checks remains only algebraic validation, not original proof.
