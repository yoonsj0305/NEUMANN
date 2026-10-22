# NEUMANN 1 | Source-authentic automated structure discovery and full truth closure

**Date:** 2026-10-22 (KST)  
**Research verdict:** SCOPED POSTHOC CLASSICAL AUTONOMOUS STRUCTURAL DISCOVERY PASS.  
**Global Q1–Q7:** OPEN. **Learned-model-exclusive operator invention:** NOT PROVEN.

## I. What was actually proved and independently repeated

Pinned source: `SyGuS-Org/benchmarks@13c8deb68a873635879c9a69bc78caebd340f646`; corpus has 12 original SyGuS `.sl` files. The previous SHA registry accidentally had one incorrect SHA for `fib_11.sl`: first study retained its 12 denominator and the mismatch as `SOURCE_IDENTITY_FAILURE`; this proof-completion is explicitly **POSTHOC** with the corrected original Git blob, never relabelled first-blind. All twelve authentic byte identities in the current study checked.

**New experiment:** Without receiving a single human-written winning invariant in its algorithm input, a generic zero-neural exact-source algorithm finds a complete original inductive safety invariant for **11/11 genuinely SAFE** source programs. For the remaining **1/12** original (`fib_07.sl`), the independent original-source truth check certifies a *concretely reachable UNSAFE* trace. There is no false SAFE certification. This is full source-truth coverage **12/12** in this specific previously exposed posthoc evaluation cohort; the unsafe trace is checked independently and is not discovered by the safe invariant proposer. The separate UNSAFE witness is not labelled an automatic discovery in this trial.

Actual source-original dual SMT proof authority: **Z3 + independently installed checksum-pinned cvc5 1.4.2**. Eleven automatically generated source-specific inductive invariants passed **33/33 original three-VC proof obligations in EACH solver**, plus **22 intentionally unsound candidate controls SAT in EACH solver**; no manually supplied target invariant contributes to automated success. The independent checker reports `q_z3=55`, `q_cvc5=55`, `dual_safe_certified=11`, `original_checked=12` and one fail-closed no-proposal original, subsequently separately proved UNSAFE. A second separate source-truth pass verified 11 SAFE and one UNSAFE original; this pass *does* contain previously archived human candidates and is never used as the automatic generator's input.

**Official run (verified SUCCESS):** https://github.com/yoonsj0305/NEUMANN/actions/runs/39711864365  
**Head commit:** `c9c5aee7ec1d9023bf8eb9a01fbbdfbf5aeb2f63`  
**Evidence artifact #12397622481:** SHA-256 `f22ef25a060cb851be6c97e30a92fab53559667b162cf194d18f840c4403c54e`  
**PR #452, unmerged:** https://github.com/yoonsj0305/NEUMANN/pull/452  
Earlier working full proof run 39711474514 recovered 10/11 SAFE in new generator + 1 fallback; stronger symmetric generic signed bound grammar recovered the final 11th SAFE original automatically in the new generator, without source-specific fixups. Intermediate malformed-CI and accidental uploaded trailing duplicate-file syndromes are preserved as historical infrastructure errors, never treated as solver evaluations.

## II. Exact mathematical source structure generated without gold formulas

General source-only process:

1. Parse actual `Pre`, `Trans` branches, original `Post` AST and original Git source bytes.
2. Convert all universally true explicit **linear initial equalities** into rational matrix equation `M x = b`, no source filename or expected invariant lookup.
3. For each original affine transition branch, derive the exact symbolic coefficient matrix `C` of state differences (including unconstrained primed values where necessary). A conserved linear relation must satisfy `C w=0` with `w=Mᵀ α`. Solve `C Mᵀ α=0` by exact rational nullspace, normalize integral coefficients, form `wᵀ x = bᵀ α`. This equation is an original-Pre consequence that is algebraically conserved across the considered transition branches.
4. Split only by *actual original source branch guards* such as `t=0` vs `t≠0`; generate guarded implications, not hand-coded target formulas. Independently check all original branches and state-space conditions with complete original source SMT three-VC, so branch reachability and cross-guard transitions are not assumed safe without proof.
5. Generate bounded signed relational inequalities with coefficients ±1 and bound constants {-2,-1,0,1,2}, augmented by numbers actually found in original source. Use full exact Houdini fixed-point elimination to remove candidates not inductive with the whole conjunction. No trained model, no GPU, no paid API, no human invariant labels read.

Machine-generated, source-proven structures:

- **`ex23.sl`:** source Pre + Trans yield `z−36y−c=0`, with source-derived bounds. Old fixed {-1,0,1} affine feature grammar alone did not generate this conservation directly; new source-conditioned exact algebra did.
- **`fib_11.sl`:** source-derived `j−2i=0` plus bounds; the original preregistered SHA error makes this necessarily posthoc.
- **`fib_13.sl`:** source branch guard `t=0` implies `k=0`, and complementary guard `t≠0` implies `j−2k=2`. Conditional composition is generated automatically.
- **`fib_14.sl`:** full original safety requires positive and negative source-state relation bounds: adding the sign-symmetric small relational thresholds {-2,-1,0,1,2} fixed missing grammar headroom, without any source-specific invariant injection.

**Scoped exact structural impossibility for `fib_13.sl`:** original initial-state affine equalities span `j=2` and `k=0`, with t unconstrained. The two transition modes preserve t but make state increments `(Δj,Δk,Δt)=(4,0,0)` and `(2,1,0)`. A linear equality `a j + b k + c t = d` true on all initial states forces `c=0`; inductiveness across both modes forces `4a=0` and `2a+b=0`, hence `a=b=c=0`. There is **no nonconstant globally conserved affine equality** in this supplied representation class. But when the source guard is included, two nontrivial conditional conserved equalities exist and generate an original dual-checked invariant. This is NOT a theorem that *no* other kind of unconditional invariant works, and no novel general algebraic primitive is claimed.

## III. Historical comparator, actual costs and necessary caveats

| Route on the same authentic 12 originals | Exact source SAFE certificates | CPU proposer wall, single GitHub job |
|---|---:|---:|
| Prior finite exact Houdini (zero neural) | 8/12 (8/11 actual SAFE) | **1.678 s** |
| New exact source-conditioned affine/guard/relational Houdini (zero neural) | **11/12 (11/11 actual SAFE)** | **3.6694 s** |
| Safe-only proof union of these methods | 11/12 | sequential cost if always running both; no claimed 10x |
| Frozen actually trained source-cross-transfer proof ranker PR #450 | 7/12, with one original SHA mismatch in original first registered run | training and costs separately retained |
| Frozen no-learning random order on same PR #450 cohort | 7/12 | no learned-exclusive solved-task headroom |
| Separate authoritative original truth audit | **11 SAFE + 1 UNSAFE /12** | contains archived manual proofs; do not attribute to automatic discovery |

The new autonomous source-conditioned method correctly solves three original SAFE cases missed by the old finite Houdini grammar but uses ~2.19× longer proposer CPU wall than the old method on this one unrandomized CI run. This is **capability extension at higher cost, not 10× efficiency or learned invention**. Checker wall in the same final experiment was 1.151 s; no end-to-end matched frontiers or power/GPU/cost benefit established. Learned-model-exclusive novelty remains negative/unproven on this cohort; strong no-learning source algebra covers every actual SAFE case.

## IV. Scientific decision and next gate

Admit one narrow conclusion: *the fully automatic classical source-to-guarded-relational-structure engine can generate and independently certify useful original inductive invariants with no gold on all eleven SAFE sources within this exposed cohort.* The source-authenticated original safety truth of all twelve is independently closed (11 SAFE, 1 UNSAFE). This is a real **mechanism and scoped engineering/correctness result**, not a new neural architecture with proven learned unique structure, independent-author transfer, general-world safety, or frontier performance.

For actual NEUMANN learned-unique Q3, stop testing a learned coefficient optimizer or pretrained ranker against already fully solvable classical source families: there is zero possible extra verified solve coverage here. Next independent, preregistered unrelated-source evaluation must target strong-classical failures, freeze source identities and a learned grammar-expansion mechanism before seeing original text, and compare exact full independent original proofs, failed candidate counts, training amortization and cold total work. Preserve any FAIL or UNKNOWN rather than forcing PASS.