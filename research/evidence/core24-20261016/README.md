# NEUMANN CORE-24 · learned typed relationship-composition AST from goal graph

**2026-10-16 | Limited neural composition proven | No matched headroom | All Q1–Q7 OPEN**

## Actually executed

- A 65,571-parameter PyTorch transformer, trained on 4,400 **procedurally generated same-grammar typed goal-variable graphs**, independently selects two unary relations and one binary-composition relation, producing a complete **typed auxiliary theorem AST** `forall L. C(U_left(L),U_right(L)) = L`. It does NOT invent the theorem shape or semantic operator definitions.
- Training time 14.065s on CPU; best development exact 378/400. Frozen checkpoint SHA-256 `6f6aae1eb2c824295a08011fad5309cea6f3ba2f036c28adb06c8a0653b819f3`.
- Independent-seed synthetic graph holdout: **486/512** exact model structural ASTs (94.9%). On the SAME inputs and grammar, the exact symbolic graph unifier: **512/512**, faster.
- Source-conditioned evaluation on previously studied, DEVELOPMENT-only CHC-COMP `ADTRem/isaplanner/goal43_000.smt2`, pinned commit `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`, Git blob `125e17e95967b4af13f5a1de9031f0d1d533e330`, 4,286 bytes, SHA256 `07202db07e74154416379c8e0e548fd1a46f4c4553b1c56d07c76da306865449`.
- The model independently output the actual AST `forall L. append(takewhile(L),dropwhile(L))=L` from the source failure-goal join graph. A checker CONSUMED this emitted candidate, independently certified all **3 induction cases as UNSAT**, then instantiated the certified lemma under a **human-authored** total interpretation of all source relations and checked all **18 original Horn clauses as UNSAT** in negated form. Incorrect order and duplicate-take hypotheses were blocked by SAT induction counterexamples.
- A real goal-join input mutation `append(C,D,E)` -> `append(D,C,E)` changed the FROZEN neural emitted theorem into the reversed order, which the inductive solver rejected. Four relation alpha-renamings preserved structural prediction. **9/9 pytest** fresh-unzip replay PASS.

## Economics / classical matched baseline

Nine paired warm CPU trials, same 512 graphs; exact symbolic graph unification median **2.007ms** vs frozen neural inference **17.672ms** (includes checkpoint restore); approx 8.8x classical advantage on this specific proposal-only measurement. Neural training adds ~14.1s. This is NOT an all-in energy/capability estimate, but there is no neural efficiency headroom.

## Strict newer real-source preregistered support check

Before source inspection, frozen model + parser SHAs and target paths `ADTRem/isaplanner/goal45_000.smt2` and `goal46_000.smt2` were registered. GitHub connector original files: `goal45` Git blob `6137f0d14991388f33d0b04eee00c69a315c3aff` (4,726B) and `goal46` Git blob `9a0a1392f0cfb994a8d1501017c6ed6eb2f758ca` (1,701B). BOTH have THREE datatypes: pair, list-of-pairs, list-of-Int. Frozen adapter supports ONE datatype. **UNSUPPORTED_MULTIPLE_DATATYPES** on both. Important: this was a **GitHub original metadata/type-signature preflight**. Full source bytes were not transferred to the local model, so no neural inference or original-proof run occurred on those two heldouts. No evaluation-specific grammar extension was made.

## Correct scope and limits

Input to neural encoder: **only typed goal-clause signatures and variable joins**, not the full dependency-complete Horn program from CORE21. Source semantics, helper grammar and external proof-template remain **human/classical-authored**. Model is trained and evaluated within the same synthetic graph generator and on an already-seen development source; novelty of representation type, genuinely unseen-family generalization, frontier parity and total compute superiority remain UNPROVEN. Initial parser bugs (signature arity, Bool output, ff guard, thread setup) were repaired BEFORE certified development original run, WITHOUT updating trained weights. All first-run receipts retained.

## Reproducibility and artifact

`NEUMANN_CORE24_LEARNED_TYPED_JOIN_20261016.zip`: **270,078 bytes**, SHA-256 **`481f4195767c4c803fd6ebcaacca57b4128d02cc184ed465d973099bdb4684b3`**; archive CRC PASS; independently extracted replay 9/9 tests PASS; 16-file exact SHA256 manifest inside. Includes frozen.pt, training/benchmark/proof receipts, goal-graph neural composer, full AST certificate checker, negative controls and pinned external-source fetcher. **The original benchmark CHC source bytes are excluded from ZIP**; re-fetch pinned source to replay proof. **The ZIP binary is NOT uploaded to GitHub, only this report and SHA record**.

## One next decisive gate

Stop optimizing the fixed goal-join law. Freeze an architecture that consumes dependency-complete source clauses and emits a genuinely new typed helper *recursive definition* on type-diverse untouched originals, source-proofed with matched specialist classical synthesis and full cost. **Q1–Q7 remain OPEN.**