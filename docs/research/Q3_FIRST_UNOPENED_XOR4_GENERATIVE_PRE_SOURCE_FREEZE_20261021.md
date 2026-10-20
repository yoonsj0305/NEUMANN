# Q3 Gate R: learned four-variable XOR composer FIRST source-unopened transfer
Date: 2026-10-21 KST. **PRE-SOURCE METADATA FREEZE**. Do not inspect target actual source bodies before this commit.

Upstream: SyGuS-Org/benchmarks@13c8deb68a873635879c9a69bc78caebd340f646; original source file identities from metadata only:
- lib/Inv_Track/andrew_lustre/FIREFLY_1.lus.sl Git blob e23218d41372a350467aba1386897cb0311247ff
- lib/Inv_Track/andrew_lustre/DRAGON_2.lus.sl Git blob 17f0cea250008e9e3575d38181f7e40804501dde
Both are **new unopened original file instances but same already studied andrew_lustre author-origin family**; NOT independent author-family G1.

### Hypothesis and frozen learned mechanism
From independent SYNTHETIC 4-variable Boolean samples, train a tiny CPU MLP 16 occupancy features -> 32 tanh -> 3 source-independent classes: NO_PARITY / XOR_4_EQUALS_0 / XOR_4_EQUALS_1. This produces a **four-variable typed XOR program AST** as a compositional relation, not a pairwise equality menu. Training 3600 synthetic examples, heldout 600 independent seed, exactly 220 gradient steps and deterministic RNG seed 20261021, model state parameters frozen BEFORE target source read. Permuted-label and exact nonlearned parity-count classifier control, all full-CPU training cost.

On pinned originals use prior exact source-native mixed Int/Bool and declared nondet parser from PR #319 and verify XOR parity 3/3 UNSAT in native Z3 + independent official cvc5 1.4.2. Without any target invariant or Post labels, collect at most 32 unique true original Pre source Bool states plus 32 from real Pre AND Trans successor states (2x source clock). Original Post allowed only to mask state variables directly used by source published safety goal (no gold invariant features). A Boolean variable eligible for candidate tuple must not be among Post support. Require >=4 eligible Bool state vars, otherwise UNSUPPORTED.

**Hard nontriviality**: First compute affine GF2 span of *all pairwise and singleton source-sample-consistent constraints* over exactly SAME source samples and eligible Bool variables, using exact XOR row elimination. Require each proposed four-variable parity candidate be **outside this span**. This is conservative: sample-consistent pairwise is an overapproximation of truly inductive pairwise, so independence from it implies true independence from all genuine pairwise constraints. This condition blocks transitive equality tautologies such as prior DRAGON_1 group 14,24,26,27.

Evaluate all 4-combinations and rank by FROZEN MLP confidence. At most 48 first proposed source ASTs go to actual original Pre⇒candidate and candidate+Trans⇒candidate' under BOTH Z3 and independent cvc5; preserve failures, stop at cap. No manual target labels or code-specific edits. Strong exact source-only classical comparator enumerates all 4-way XOR constraints, with sample consistency + independence screen and same original 2VC dual proof budget for up to 48 target candidates, plus use original cvc5 SyGuS as non-neural safety baseline if needed. If model 0 or classical dominates, preserve failure and do not tune on these opened targets.

Requires real original source 2VC proof for any limited POSITIVE, not source published safety Post (3VC) and not G1 new mathematical primitive beyond predeclared XOR4 grammar. Conditional scientific status `SCOPED_LEARNED_XOR4_FIRST_FILE_TRANSFER` only if original 2VC exists. GLOBAL Q3=OPEN, Gate R generative OPEN, Gate V source-author-disjoint OPEN, Q4–Q7 OPEN regardless of result.

One first workflow and original untouched receipts. Old first Bool pair rank18=0, full110=6 (one 4-variable equality cluster), and fixed42 exact-classical NO_GO are immutable. No GPU/paid API.