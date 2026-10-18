# Q3U FIRST original source exact transition nullspace mathematical result (2026-10-18)

**Final scientific verdict:** `PROVEN_SOURCE_TRANSITION_DERIVED_CLASSICAL_RELATIONAL_INVARIANT_ON_ONE_AUTHENTIC_ORIGINAL`; `LEARNED_OPERATOR_Q3_GLOBAL_OPEN`; `Q4_MATCHED_10X_OPEN`; `FRONTIER_Q7_OPEN`. All global Q1–Q7 OPEN.

## Frozen protocol and first receipt

The protocol was recorded in `docs/research/Q3U_EXACT_TRANSITION_NULLSPACE_PREREG_20261018.md`, commit **c9ac36be5ddb79cf92596281808711d253c0d988**, BEFORE the Q3U first real run. Input pinned upstream `SaswatPadhi/LoopInvGen` revision `6ac90265b11431c9477dfbd33e3e3380234c0499`. Cohort frozen: first 8 file paths lexicographically in `benchmarks/LIA/2017.ASE_FiB/`, plus prior-known `benchmarks/LIA/2016.SyGuS-Comp/array.sl` and `benchmarks/LIA/others/inria-00615623_4.sl`, exactly 10 original source SHA identities across 3 families. These are **previously opened development originals**, NOT fresh unseen source groups.

**FIRST actual independent [GitHub Actions #39100608497](https://github.com/yoonsj0305/NEUMANN/actions/runs/39100608497) SUCCESS**, original GitHub Actions evidence artifact **12126322933**. [PR #211](https://github.com/yoonsj0305/NEUMANN/pull/211) intentionally Draft. North Star contract CI SUCCESS. Full repository CI was IN PROGRESS on last check.

## Actual source-based coefficient derivation

Take the unchanged authentic original `benchmarks/LIA/2017.ASE_FiB/fib_01.sl`, *source Pre* `x=1,y=1`, *source Trans* `x'=x+y,y'=x+y`, *source Post* `y>=1`:

\[
\begin{bmatrix}x'\\y'\end{bmatrix}
=
\underbrace{\begin{bmatrix}1&1\\1&1\end{bmatrix}}_{A}
\begin{bmatrix}x\\y\end{bmatrix}.
\]

No target-specific coefficient was supplied to the algorithm. Exact rational `sympy.Matrix(A.T).nullspace()` yielded primitive normalized **`c=(1,-1)`** and original transition offset `b=0`. Thus mechanically construct the source-state typed relation
\[
R(x,y):\quad c^{T}(x,y)=0\quad\Longleftrightarrow\quad x-y=0.
\]

Original source proof admitted this relation ONLY after independent negated original VCs `Pre∧¬R=UNSAT` and `R∧Trans∧¬R'=UNSAT`. The original `Post` ALONE is **NOT** inductive: first original 3VC `NO_THREE_VC_CERTIFICATE`; using `I=Post∧R`, source-original `Pre=>I`, `I∧Trans=>I'`, and `I=>Post` all **UNSAT**. Original Pre SAT and original not-Post SAT (nonvacuity). Both handwritten Q3T original source parser and native Z3 SMT-LIB source parser produce exact same original Pre,Trans,Post (three XOR queries all UNSAT) before any theorem accepted. Direct unchanged original specialist SPACER also says BadExit **UNSAT** on this source. This is a **bounded classical structural automatic coefficient discovery** on a genuine, actual original problem, not a supervised/learned neural mathematical operator invention.

Elementary symbolic explanation (additional inspection, not the SMT receipt): base `x=y=1` has `R` and `Post`. Induction: if `x=y\ge1`, the exact original transition sets `x'=y'=x+y=2y\ge2`, hence both retained. No finite search/sampling or hidden benchmark solution was needed.

## All first ten results, no cherry-picking

| Frozen family | Authentic original files | Exact source explicit Int-affine transition matrix extracted | New primitive coefficient relation originally certified | Full authentic source safety 3VC via Post + learned? | Direct untouched classical SPACER BadExit UNSAT |
|---|---:|---:|---:|---:|---:|
| 2017 ASE FiB (lexicographic first 8) | **8** | **1** | **1** | **1** | **6** |
| 2016 SyGuS-Comp (preselected array.sl) | 1 | 0 | 0 | 0 | 1 |
| others (preselected inria-00615623_4.sl) | 1 | 0 | 0 | 0 | 1 |
| **TOTAL** | **10** | **1** | **1** | **1** | **8** |

The nine NOT certified by the new coefficient engine **ABSTAIN** because their unchanged original transition is not completely, syntactically explicit `x'=Ax+b` in its narrow first grammar. This first prototype rejects original branching/disjunction, next-state-to-next-state equations and missing next-state updates rather than guessing; it does NOT establish that these nine original programs are unsafe or mathematically unsolvable.

Specific statuses of eight other FiB variants: `fib_04`, `fib_07`, `fib_08`, `fib_09s`, `fib_10`, `fib_11` have incomplete syntactically explicit affine next state assignments; `fib_05_x` uses a next-state var RHS and is correctly rejected. Both other-controls also have nontrivial disjunctive/conditional transitions. Direct source-only SPACER proves 8/10 total, including the one new coefficient solver proves; **NO differential classical specialist solving advantage**.

## Real negative/positive controls in first CI

An independently created **synthetic** mixed-source guard (never counted in 10 authentic originals) automatically extracts normalized primitive **`(1,-1)`** from `x'=x+y,y'=x+y`. With Pre `x=y=1` and Post `y>=1`, original Post alone fails original 3VC; `Post∧R` passes. Deliberately false relation `x-y=1` fails; deliberately mutated actual step `x'=x+y, y'=y` destroys the previous certificate. All control checks correct. Classic conserved candidates are separately considered only if source Pre uniquely determines `k` and original proof accepts them.

## SCIENTIFIC ADMISSION / STOP

**PROVEN**: exact source-original transition relation coefficient retrieval from linear-algebraic left nullspace, without manually inserting the specific coefficient vector, yielding a source-bound new AST equation not equal to original `Post` and a full authentic original source 3VC safety certificate, with native source parsing equivalence. This answers a *scoped*, real structural inference/verification subquestion.

**NOT PROVEN**: model-learned discovery of an unanticipated operator, proof improvement over equal-information strong classical solver, **10× Q4 equal solved/full cost**, Q7 frontier parity, or source-family generalization. ZERO neural forwards/learned weights in Q3U; do not promote this to a NEUMANN global Q3 PASS. The 10 programs are NOT untouched tests and mostly outside narrow grammar.

**STOP** expanding FiB original performance numbers by post-hoc adding original source-specific clauses and calling them blind results. A valuable next preregistered research design could compose this deterministic exact coefficient-inference tool behind a neural/tool-choice controller on **a different never opened source-family** with strong specialized original source classical method/learning ablation and full cost. The Q3F sealed competition originals remain unopened. Individual competition benchmark redistribution rights not independently established; no third-party original source/formula text bundled in experiment artifact.

All Q1–Q7 OPEN; PR stays Draft. This historical first positive is limited but fully mathematical and independently auditable.
