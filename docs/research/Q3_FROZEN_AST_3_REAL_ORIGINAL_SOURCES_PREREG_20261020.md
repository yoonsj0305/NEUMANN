# NEUMANN 1 | G1 uninspected third-party source: frozen AST transfer gate (2026-10-20 KST)

**FROZEN BEFORE OPENING ANY OF THE THREE SOURCE BODIES IN THIS NEW STUDY**. The checkpointed AST was already learned in PR #300 from a five-modulus synthetic family and validated in PR #300 official first CI. That means learning is NOT source-family independent and the AST is not originally discovered without the full classical grammar (25,920 candidates). We must not reframe posthoc as new learned invention.

## Frozen model, no test-source training or model changes

- Frozen learned compound AST from [PR #300](https://github.com/yoonsj0305/NEUMANN/pull/300), real executed [CI #39402836605](https://github.com/yoonsj0305/NEUMANN/actions/runs/39402836605):
  `(- a (* (div a b) b))`, with exact training-source/model weights SHA-256 `c67457981ed9f8faea5b1b38061ceebb998340274554e003b67bf47822280f10`, 125-parameter shape-conditioned reward-learned AST model. Its source training uses 25,920 exhaustive behavioral evaluations to make the reward posterior. It is not an unassisted neural-first mathematical primitive and does not beat exact classical enumeration.
- For inference, **no training weights or method may update on heldout source bytes**. Reproduce frozen model only from original five synthetic training moduli 2,3,4,5,6 (48 source observations each), via unchanged `research/evidence/q3_behavioral_conditional_ast_20261020/first_cpu_original.py`. Assert greedy token AST and exact recorded weights SHA before inspecting each original benchmark. Do not silently load macro independently without a weight-identity gate.
- **Universal semantic identity claim**, to be evaluated before any original body can influence approach: over arbitrary integers a,b with b>0 (including a negative), Python/Z3 SMT Euclidean integer div semantics, `a mod b = a - b*(a div b)`. Z3 independent cvc5 v1.4.2 must both report UNSAT for the negation, under 15s time cap. If either unknown, leave unproven; never silently substitute Python float-floor semantics. Strong same-information classical arithmetic remainder identity solver also knows this, so zero learned-unique capability.
- A learned AST is structurally a `div` and multiplication composition; it is not novel relative to the 25,920 finite grammar.

## Three actual SOURCE identities pinned BEFORE reading original contents

Public upstream `SaswatPadhi/LoopInvGen@6ac90265b11431c9477dfbd33e3e3380234c0499`:
1. `benchmarks/NIA/other/div.sl`, upstream Git blob SHA1 `78ebf3875665cb257631beb87445abaf3c41f4a1`.
2. `benchmarks/NIA/other/lcm.sl`, upstream Git blob SHA1 `6c0cbaafc0c8b960d6047014dc5670554aacbc85`.
3. `benchmarks/NIA/2018.CHI_InvGame/sqrt-more-rows-swap-columns.sl`, upstream Git blob SHA1 `66d45fac379b9114a38bed6dc25599e0c0f5caa1`.

These are two independent public benchmark subdirectories/origin groups. We do NOT assert the source never appeared anywhere in past NEUMANN research, merely that **no source body was opened by this new study until this frozen identity contract was written**. All 3 rows must be included, including unsupported source and out-of-scope.

## Source interface/proof contract frozen before content

- Read source raw bytes, enforce pinned Git blob, parse typed custom and native SMT-LIB original `Pre/Trans/Post`, demand semantic XOR parity UNSAT three ways, real Pre SAT and nonvacuous not(Post) SAT. Unsupported must ABSTAIN not be counted as safe.
- **Expression eligibility**: traverse the native published `Post` formula and collect every occurrence of SMT `(mod A B)` with integer-typed syntactic operands (only formal SMT-LIB `mod`, not a filename heuristic). For each occurrence, rewrite it to the frozen model `A-B*div(A,B)` exactly, and check **original-source-derived** `Post ↔ rewritten Post` under source-available denominator positivity or a **global arithmetic theorem**. If no original Post mod term, mark `OUT_OF_SCOPE_NO_MOD_TERM` and do not silently generate a source-specific invariant from its intended answer. Never train, adjust source mapping, or select target outcome after inspection.
- Post-rewrite semantic equivalence is only a **macro interface certification**, not source invariant discovery. To claim full source transfer `SOURCE_INV_3VC`, the rewritten Post used unchanged as candidate must prove genuine original `Pre⇒I`, `I∧Trans⇒I'`, `I⇒Post` in native original Z3 and independent cvc5 original 3VC. **Explicit control:** original unrewritten Post alone must FAIL induction, or a new useful invariant must be clearly nontrivial. A tautological rewrite of the published Post is not Q3 semantic structure invention.
- Same-information classical rewrite of SMT mod via Euclidean algebra baseline is mandatory and should be at least equally capable.
- No fresh learned model training on any of the 3 target source file contents, no GPU or API spend, immutable first CI run even on FAIL/ABSTAIN, global Q3 stays OPEN. The macro arithmetic lemma is a mathematical tautology and already known in SMT theory; a universal identity verification alone cannot establish nontrivial AI generalization. This study is designed to distinguish correct mathematics from useful structure.

## Outcome

PASS of universal lemma is **SCOPED MATH CERT** only; all external 3 sources remain a genuine blind source-interface audit even if 0 eligible. Full G1 Q3 PASS requires a truly new neural-first invariant with strong same-information classical headroom, and is out of scope of this frozen macro reuse. Do not relax criteria based on targets.