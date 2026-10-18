# Q3M · Original C annotation-site soundness repaired; 13/13 historical source proofs re-certified

**Date:** 2026-10-18 KST. **Verdict:** `Q3M_SOURCE_ASSERTION_SITE_SOUNDNESS_GATE_VERIFIED / HISTORICAL_13_OF_13_SCOPED_ORIGINAL_PROOFS_REPROVEN / GLOBAL_Q1_Q7_OPEN`.

## Critical vulnerability discovered

Earlier Q3H `static_assertions` found one `//@ assert(...);` ANYWHERE in the original C program, removed that source comment, and the proof builder reinterpreted the expression as the post-loop original safety goal. **There was no check that the asserted source point was physically after the loop.** This has a potential unsound false-certification path: a false assertion before a loop whose final state makes it true is different from an exit assertion. Such a source may appear provable by a verifier that silently moves the assertion to termination. This applies to the source-to-specification mapping, not the Z3 SMT engine.

Pre-registered hardening in `docs/research/Q3M_ASSERTION_SITE_SOUNDNESS_PREREG_20261018.md` before the first independent Q3M execution. The patch adds `original_assert_site.py` to EVERY call of `model_original` using a **parser-only copy**: replace exactly the original standalone `//@ assert` line with an inert AST marker, parse all original C statements via the existing frontend, and verify the marker is physically at the unique modeled `main` loop's immediate exit site. An otherwise EMPTY nested C compound statement surrounding the marker is acceptable: it is an unconditional, side-effect-free post-loop execution point. Conditional wrappers, effectful branches, before-loop, inside-loop and after-return are rejected. The actual original executable C is **never modified** when building proof obligations.

### Important original-first failure and correction history

1. Initial strict annotation gate [Q3M Actions #39089241234](https://github.com/yoonsj0305/NEUMANN/actions/runs/39089241234) was technically SUCCESS but admitted **0/13** historical originals. This was an **overstrict checker result**, not evidence all original programs were unsafe.
2. Diagnostic-only gate [Q3M Actions #39089481477](https://github.com/yoonsj0305/NEUMANN/actions/runs/39089481477) found all thirteen original annotations located **inside nested C blocks AFTER their modeled loop**, not before/inside. The scope requires matching this real original syntax rather than incorrectly rejecting benign nested source statements.
3. Corrected inert-compound guard re-ran original proofs [Q3M Actions #39089580709](https://github.com/yoonsj0305/NEUMANN/actions/runs/39089580709), and re-certified **13/13**. No failed original was silently omitted.
4. Additional negative/positive nested control hardening was then added and [final Q3M Actions #39089707181](https://github.com/yoonsj0305/NEUMANN/actions/runs/39089707181) **SUCCESS**, artifact **12122128097**. Final source gates accepted **13/13**, full original mathematical proof re-ran **13/13**:
   - Q3I nine original C sources: 9/9 genuine source-only classical Houdini induction and safety certificates.
   - Q3K-2 `sum04`: 1/1 original classical polynomial+CHC composed certificate, all composition obligations satisfied.
   - Q3L previously Q3I-failed source files: 3/3 original source-only SPACER BadExit and signed-overflow UNSAT.
   - Original exact source SHA256s were rechecked against immutable FIRST GitHub receipts and the pinned Microsoft Loopy source archive. Exact count is 13 unique original C **source files**, not 13 independent mathematical source families.

### Adversarial controls, final 7/7

| Position/side effect of original `//@ assert` | Gate |
| :-- | :-- |
| **False BEFORE loop** (expression becomes true only at exit) | REJECT |
| Correct immediate AFTER loop | ADMIT + full original proof |
| INSIDE loop | REJECT |
| AFTER RETURN | REJECT |
| Correct AFTER loop in unconditional inert `{; //@ assert...;}` compound | ADMIT + full original proof |
| AFTER loop but same block contains **a side-effecting update** | REJECT |
| AFTER loop but wrapped in **conditional `if`** | REJECT |

All seven source-location controls returned expected outcomes; the two admitted positives were also actually rechecked by original C induction and mutation gates. No arbitrary source text or target answer label was supplied to learn a neural model.

### What is and is not established

**Established**: a material source-to-formal-specification soundness hole was closed with fail-closed original AST location checks and 7 control cases, and the 13 previously asserted authentic source-file certificates survived full mathematical replay under the strengthened gate. This was scientifically more urgent than adding neural training to an untrusted verifier.

**Not established**: the model learned any new AST operator. The proving mechanisms remain classical and source-subset specific, with the same underlying Z3 and original Q3H finite single-loop C semantics. This patch is not an unrestricted full ISO C verifier and is not a new unseen source-family evaluation. **Global Q1–Q7 all remain OPEN**, notably learned Q3, equal-success >10× whole-cost Q4 and frontier Q7. The two pre-registered Q3F CHC challenge originals remain SHA-sealed and unread. Do not convert these safety receipts into frontier-level neural discovery claims.

**Next minimal high-value task**: Only after this proof source-site hardening, build and train a genuinely typed, variable-depth, source-conditioned AST operator proposer. Test against the now trusted original proof verifier and equal-information specialist classical baseline on source-group-disjoint problems. No more opened original cherry-picking.
