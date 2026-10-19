# NEUMANN 1 Q3 | First gradient-trained composite AST macro reuse and original safety evidence

**2026-10-19 KST. Scientifically exact result: `Q3_TRAINED_SELF_DISTILLED_COMPOSITE_AST_REUSE=SCOPED_PASS`; `Q3_NEURAL_INVENTED_INITIAL_MACRO=NO`; `Q3_NEURAL_INVENTED_NEW_MATHEMATICAL_PRIMITIVE=NO`; `Q3_GLOBAL=OPEN`.**

The original structural learning goal of NEUMANN 1 is to find *useful hidden structure with minimum necessary computation*. Previous PRs #294/#297 learned scalar coefficients on predeclared degree-2 monomial basis that same-information classical least-squares solved cheaper; PR #298 proved a universal degree-only polynomial grammar limitation versus modulo. This PR is the first concrete **trainable *variable-depth typed AST macro* library reuse** rather than learning only scalar coefficients or selecting a provided `mod` operator. But it MUST NOT be promoted to a pure neural discovery: the actual composition was first found via classical stochastic search, then self-distilled into learned categorical weights.

## Reproducible first GitHub source-bound action

- [Draft PR #299](https://github.com/yoonsj0305/NEUMANN/pull/299), first attempted true original CI [#39272890880](https://github.com/yoonsj0305/NEUMANN/actions/runs/39272890880) **FAIL** due to harness comparing `{pre,trans,post}` input parity keys to `{initial,consecution,post}` proof VC keys. Preserve failed first execution as received. Exact source/candidate/decoder/loss were NOT changed. Harness-only commit `7dd6b709cfc1657dc906fd4ce49564a907ca4c12` corrected three-key comparison before re-run.
- [First fully verified CI #39273131950](https://github.com/yoonsj0305/NEUMANN/actions/runs/39273131950) SUCCESS, [original Actions artifact #12197230094](https://github.com/yoonsj0305/NEUMANN/actions/runs/39273131950/artifacts/12197230094). Immutable first complete JSON SHA256 `43b7ae124c5f10c47329afdf09d92ce8cadf02726a1ef945569d274cc63f6fee`; downloaded artifact ZIP SHA256 `5bac7ea9fd0efcd09a320d594a04516f943cbea50bae37227e6c7e089b595b6b`, 2,515 bytes, CRC PASS.
- Frozen file `docs/research/Q3_TRAINED_COMPOSITIONAL_AST_MACRO_FIRST_CI_FREEZE_20261019.md` committed before CI BUT after local dev already discovered candidate. This study is **posthoc development**, not new blind G1.

## Training-only synthetic recurrence data and actual learned structure

- Author-created training source: `i=0,r=0`; `i'=i+1,r' = 0 if r=k-1 else r+1`; train k=2..6, 48 source states each, total 240 state-output pairs. Original program's hidden `mod` formula is NEVER supplied to model as an operator, training target AST or optimization gradient. Only source-available state output `r` is supplied as behavioral feedback.
- DSL starts with **4 typed binary operators** `+, -, *, div`, **3 typed leaves** `a,b,1`, **five possible binary-tree shapes of exactly 3 nodes**. `mod` is absent from initial grammar. Complete finite closure size `5×4³×3⁴=25,920` candidate programs. Thus a correct compound AST is **expressible within predeclared complete grammar** and automatically searchable by a strong exact classical enumerator. No fundamentally new elementary arithmetic operator or grammar extension was learned.
- **First discovery from UNTRAINED randomized classical enumeration** (seed 20261019) at AST behavioral attempt **12,806 / 25,920**, **526.711ms component**. The compound function discovered without gold target program:
  ```lisp
  (- a (* b (div a b)))```
  equivalent for b>0 to `a - b*floor_div(a,b)`, exactly nonnegative remainder.
- Trainable **29-parameter categorical policy** (shape 5, operators 3×4, leaves 4×3), initialized to all zeros; **100 real CPU Adam gradient updates using analytically computed softmax gradients** that maximize the probability of the **self-discovered** (stochastic-search) program. No original fixed target AST was provided; however **the search-generated AST IS its pseudo-label**. Actual cross-entropy loss **10.16277015→0.013738575**. Gradient fitting component **11.321ms**. Learned weight SHA256 `492cd1b7ce4ef9272a6da06cb465d6c321d810cab4d989bb349671cf86abb6b3`. Frozen decoder greedily emits the exactly found three-binary-node AST; the same untrained zero-logit decoder fails the source behavioral task. This is demonstrable weight-dependent **learned AST *reuse***, not proof weights discovered macro without search.
- Strong baseline deterministic lexicographic COMPLETE enumeration over IDENTICAL 25,920 programs and same 240 source output examples finds semantically equivalent `(- a (* (div a b) b))` at candidate **17,744**, **698.599ms component** on same CPU. Both search costs are first single seeded runs; 12,806 random probes vs 17,744 lexicographic probes is **not statistically established advantage** (or 10× all-in), and a cached classical macro can reuse one expression at the same marginal cost as the neural policy.

## Original counter program heldout formal proofs

- Model's weights frozen before heldout evaluation k=7,8,9,11. These are **four new synthetic instances within the SAME author-created recurrence family**, NOT independent real external source family blind G1.
- For each heldout program, compile frozen model AST *symbolically* into `r = i - k*div(i,k)` and add source-only `i>=0,0<=r<k`; use complete **unmodified synthetic** Pre, Trans, Post `r=i mod k`. Each of the four programs passed **Z3 original bad initial, consecution, safety UNSAT 3/3 AND fully separate official cvc5 1.4.2 3/3 UNSAT**, **12/12 VCs in each backend**. Exactly 100 independently heldout source states for each k also match. Helper-only safety counterexample SAT. Classical 17,744 search candidate passes the same heldout exact checks and implies source Post.
- The solver's cvc5 1.4.2 independent binary provenance remains pinned in CI via official SHA256 `7eb18f8c814c36a46c5a7d003983e9cfbc4b0a9828d6dd596239291bd4cc61d8`. No false UNKNOWN treated as PASS.

## Additional real PUBLIC original transfer, with honest remaining blocker

- Original external source (ALREADY OPENED earlier; **not fresh blind**): `SaswatPadhi/LoopInvGen@6ac90265b11431c9477dfbd33e3e3380234c0499`, `benchmarks/NIA/2016.ATVA_PILAT/mannadiv.sl`, upstream Git blob `8530c3a189403f14db1f505820a65e92ba876193`, original SHA256 `1bab97a325d0d0a9cfc664f480f2a6e09df0dbcef6a03dd185476414432f81fa`. Verify full source-native original Pre/Trans/Post semantic XOR UNSAT 3/3.
- Existing classically available bilinear source invariant `x1=x2*y1+y2+y3, x2>0, y3>=0,0<=y2<x2` proves original source complete Z3 3/3. **After freezing trained macro**, substitute `a=x1-y3,b=x2`, generating the new derived identity `y2=R(x1-y3,x2)`.
- Z3 universally checks `base → derived neural macro equality`: **UNSAT**; the complete strengthened invariant `base AND derived macro` passes actual original Z3 initiation/consecution/Post **UNSAT 3/3**. This is a meaningful original-source *semantic transfer* of a composite function trained only on synthetic sources, but mathematically redundant with the stronger old source invariant and matched exact classical macro. **Independent cvc5 on this extra derived original lemma: UNKNOWN at 15s under internal decision** for BOTH neural and classical programs. Independent cvc5 on strengthened original 3VC: initial UNSAT, consecution UNKNOWN, Post UNSAT at 3s, so **DO NOT mark external augmented original as cvc5 certified**. The older base proof separately passed independent cvc5 original 3VC under 15s on PR #295, unaffected.
- No source original goal weakened, no new external original-family blind test. This is a first *opened-source* semantic transfer test with explicit independent solver boundary.

## Scientific disposition and next mainline decision

`Q3_SYNTHETIC_TYPED_AST_LIBRARY_REUSE=SCOPED_PASS` with demonstrably trained parameter impact and dual independent Z3/cvc5 heldout proof.

`Q3_REAL_SOURCE_TYPED_AST_TRANSFER_Z3=SCOPED_POSTHOC_PASS`, `Q3_REAL_SOURCE_TYPED_AST_TRANSFER_INDEPENDENT_CVC5=UNKNOWN`.

`Q3_LEARNED_INITIAL_MACRO_DISCOVERY_UNASSISTED=FALSE`, `Q3_GENERATED_PRIMITIVE_OUTSIDE_PREDECLARED_GRAMMAR=FALSE`, `Q3_SAME_INFORMATION_CLASSICAL_UNSOLVABLE=FALSE`, `Q3_10X_FULL_COST=OPEN`, `Q3_FRESH_AUTHOR_BLIND=NOT_ADMITTED`, `GLOBAL_Q1–Q7=OPEN`, `Q7_FRONTIER=BLOCKED`.

**STOP and advance mechanism, don't enlarge this exact DSL or tune k:** this is random search + learning a cache. The actual next unknown is **a gradient-trained policy which proposes the *initial new macro without a classical search pseudo-label***, verified on newly frozen independently authored original source families, with exact classical grammar enumerator and overall compute costs. If not demonstrated, mathematical novelty from mere reuse is not substantiated. 

Code: `research/evidence/q3_learned_typed_ast_macro_20261019/train_self_discovered_composition.py`. Original third-party SMT task bytes are not redistributed.