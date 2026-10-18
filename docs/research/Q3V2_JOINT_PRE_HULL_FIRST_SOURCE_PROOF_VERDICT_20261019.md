# NEUMANN 1 · Q3V2 first original-proof closure and retained limits (2026-10-19)

**Official bounded verdict: `Q3V2_EXACT_JOINT_HULL_DEFECT_REPAIRED_AND_ORIGINAL_VC_CHECKED / GLOBAL_Q1_Q7_OPEN`.**

## Immutable first provenance
- Preregistration committed FIRST: `77dbee83dd2a9f7a5981a95b184b90d507058e4f` before implementation and this CI.
- Implementation: `1ee4b38abc8b1c00a0c127a15b6c35ec356ebd9f`.
- Tested exact GitHub branch HEAD: `3c2d20f96fb0fca7fd615e6ff829a001d9b30969`.
- [Actual first GitHub Actions #39177625567](https://github.com/yoonsj0305/NEUMANN/actions/runs/39177625567): **SUCCESS**. Source Z3 step completed successfully; separate pinned Python 3.11 / SymPy 1.13.3 / Z3 4.13.3.0 environment.
- Uploaded first full JSON artifact **12155510004**, name `q3v2-joint-first-source-result`; raw JSON SHA256 `575ce84dd22380990d1487a29a3f0c915755f6a566feb69ce92cede3a0a171ec` (this hashes the uncompressed JSON, not the ZIP artifact digest).
- [Historical Q3V original first](https://github.com/yoonsj0305/NEUMANN/actions/runs/39175953888) and [repeat](https://github.com/yoonsj0305/NEUMANN/actions/runs/39176159370) unchanged. Upstream LoopInvGen pinned `6ac90265b11431c9477dfbd33e3e3380234c0499`.

## Actual first checks
- **Exact algebra PASS:** prior global conservation kernel basis = `(1,0,0)`, `(0,1,0)`, each unfixed by Pre, while the joint intersection obtains primitive `(1,1,0)` for `x+y=0`. Tested single affine branch, multiple affine branches, mutant-branch corruption, and reset joint intersection.
- **Actual constructed original Z3 safety PASS:** source `Pre: x+y=0 ∧ t=0`; `Trans: x'=x, y'=y, t'=t+x+y`; `Post: t=0`. Original **three VCs** `I=Post∧(x+y=0)` certified; Post alone lacks induction. Original old `common_kernels` yields **0 candidates**; corrected algorithm returns exact source-certified `(1,1,0)`.
- **Guarded two-branch original Z3 PASS**, with the new joint relation; original Post alone still fails. Two mutants (changed update, changed single branch) explicitly fail full original 3VC.
- **Pre hull proof policy:** queried SMT for states outside current affine hull until UNSAT, then intersected the *whole* Pre-hull normal space with *all* source-branch conservation/reset constraints **before** taking nullspace basis. Arbitrary SMT UNKNOWN, noninteger model or source parity mismatch is not accepted as a proof.

## Existing previously opened source regression, NOT new scientific generalization
- Exactly the same ten original upstream SyGuS files, three family directories, and independent source parser parity as Q3V.
- **7/10** full explicit affine branch extraction; **3/10** unsupported/ABSTAIN; **5/10** full original safety 3VC certificates; **3/10** where relation needed beyond Post alone, namely existing `fib_01.sl`, `fib_07.sl`, `fib_11.sl`.
- **Incremental external authentic program gain over Q3V = 0**. New evidence is repair of a real representation incompleteness and new constructed original-Z3 controls. It is not a new source family and may not be promoted to learned Q3 transfer evidence.
- Specialist SPACER direct not rerun by Q3V2; historical Q3V first specialist 9/10 and independent repeat 8/10. Comparable end-to-end cost advantage **NOT VERIFIED**. Per-file wall measures here exclude offline training and cannot support Q4 economics.

## Scope theorem, honest boundaries, decision
Let `x0` be a genuine original Pre state and `D` span the EXACT affine hull of all Pre states. Given all represented branches `x'=Aj x+bj`, conservation equations `c^T(Aj-I)=0, c^T bj=0, c^T D=0` describe **all** linear coefficients whose constant-affine invariant `c^T x=c^T x0` is globally conserved by every branch and holds in every initial state. This follows directly from linear algebra, and Q3V2 computes their whole vector subspace before selecting a basis. Reset normals additionally satisfy `c^T Aj=0, c^T(bj-b0)=0, c^T(x0-b0)=0, c^T D=0`. These are sufficient and complete only for their stated *global conservation/reset classes*, not arbitrary guarded/conditional or nonlinear inductive invariants. Exact original Z3 VCs still independently gate safety.

**CLOSE/PASS (bounded):** missing Pre-compatible combinations of affine conservation/reset basis; constructed original Z3 three-VC positive and mutation negatives. **OPEN:** learned self-invented relations on genuinely unseen source families, stronger classical baseline headroom, complete cost/Q4, unseen transfer/Q6, frontier gap/Q7, and all global Q1–Q7. **Stop** repeated already-opened FiB tuning and unnecessary neural training; preserve initial immutable evidence. PR stays DRAFT.
