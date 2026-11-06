# NEUMANN Q3: exact affine source influence, after a frozen semantic OOD FAIL

2026-11-06. Child branch of Draft PR #678. Global Q3/Q4/Q5/Q6/Q7 remain OPEN.

## Why this exists
A frozen previously trained 3-weight representation selector scored 2/6 on
semantic cancellation source-free adversaries; untrained scored 4/6; exact SMT
semantic classifier scored 6/6 in the original FIRST. DO NOT modify or
rescore that first result. Merely observing `select(S,...)` is not enough:
`S-S` and `0*S` are syntactically source-reading but semantically independent.

## Exact normalized linear integer domain
Allow constants, index variables b/i, source-array reads at source-independent
affine indices, addition, unary negation, and multiplication by an integer
literal. Normalize each expression into a sparse coefficient map over
constant/index atoms and source select atoms. Canonicalize commuted affine
indices and sum identical select coefficients. If every source coefficient is
exactly zero the update is source independent. If at least one coefficient is
nonzero, the update depends on some source value for a suitable index and
source-array assignment on this unrestricted integer-array domain.

**Conditions:** unbounded mathematical integers, unrestricted source arrays,
the listed affine grammar, no alias constraints, source-independent affine
indices, and same base/index metadata across the two representations.
Outside this grammar, return UNKNOWN; do not generalize to nonlinear,
bit-vector overflow, finite arrays, aliasing writes, or other semantics.

This is a **human-designed deterministic algebraic analysis**, not training,
novel grammar invention, independent problem solving, or a new formalism Q6.

## Before remote measurement
On the exact already-opened 8+6 source-free ASTs from #676 and #678:
- Compare 14 analytic verdicts with independent SMT existential collision
  proof over arbitrary source array values and indices, on the same runner.
- Strict threshold 14/14 agreement, any SAT/UNSAT unknown is FAIL.
- Measure total 14 analytic calls and 14 independent SMT reference calls,
  separate wall timings and memory as available. The analytic method must
  itself make 0 Z3 calls. Any speed ratio applies ONLY to this classification
  interface, not the whole Q4 computation.
- Check cancellation, commuted indices, unsupported nonlinear AST,
  malformed constants, UNKNOWN fallback.
- No new unopened original CHC, no reserved copy4–6 source access.
- Original 2/6 learned FAIL stays immutable and cannot be relabeled PASS.

**Decision:** If exact analysis matches 14/14, delete learned lexical
source-read selector for this supported grammar; use algebraic normal form
first, then an independent SMT oracle or UNKNOWN for unsupported semantics.
Redirect learned effort to construction of truly unavailable operators
on real independent originals. Otherwise preserve first failure.
