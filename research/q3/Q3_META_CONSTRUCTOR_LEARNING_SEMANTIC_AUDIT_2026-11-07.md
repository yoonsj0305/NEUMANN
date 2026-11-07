# NEUMANN 1 | Q3 meta-constructor discovery, source-excluded transfer and independent semantics

2026-11-07. Original source results preserved immutable. **Global Q3 OPEN.** Q4 OPEN. Q6 OPEN.

## Problem redefined

Instead of calling a new literal an invention, test whether a generated **program-generating constructor AST** can be learned from prior verified executable programs, then produce *new typed predicate operators* that extrapolate beyond observed values and survive independent semantic checks.

## A. Source-only learned higher-order constructor, #713

- Original CodeARC verified source programs #834 remove '!' and #841 remove spaces, seven SOURCE TRAIN I/O observations each. Only the old generated ASTs and input/output examples are used as source experiences.
- Human-supplied safe fold interpreter and generic AST anti-unifier. AST generalizer creates one literal-hole parameterized fold template, then automatically learns the meta-binder `minus(tokens(input), tokens(output))` from the source I/O cases.
- The system emitted executable `DefineRepresentationConstructor` AST, symbol `invented_constructor_0e7ead4b089f0de3`, SHA256 **2cd85f1712ef91dbcab4a3bc85c583dfd235dd9ef451ae13282c25aef1cfa332** and froze the program before MBPP original data retrieval.
- [Immutable FIRST #713](https://github.com/yoonsj0305/NEUMANN/actions/runs/42353573666), [artifact #13566586965](https://github.com/yoonsj0305/NEUMANN/actions/runs/42353573666/artifacts/13566586965).
- Google independently authored MBPP sanitized official test IDs 11..510: 257 originals, 21 eligible strict one-argument same-container parser, 236 unsupported; 6 source TRAIN-consistent operators, 3/21 original final-assertion exact. Strong previous human filter also 3/21: 0 accuracy advantage.
- POST-FIRST additional out-of-support probes falsified all three original-test hits: #412 only learned to remove 1/3 and missed unseen 9; #426 memorized observed even values and missed 12/14; #451 removed only ASCII space, missed tab/newline. They are **not general semantic discoveries**.

## B. Generic typed predicate AST invention with unchanged source memory, #714

- New human-coded hypothesis vocabulary for `item`: numeric modulo, numeric comparisons, `str.isspace`, `str.isdigit`, Unicode character classes and literal-set fallback. This is a fixed expressivity family; the machine searches and **chooses** the Boolean expression from source I/O, not from task identifier, prompt or reference code.
- It compiles the expression into the previously source-learned fold AST, resulting in actual executable new operator functions. Unknown/noncausal/contradictory input-to-output sequences ABSTAIN.
- New MBPP original task IDs 511..974 (previous MBPP first was IDs 11..510 only): 163 original tasks, 21 eligible, 142 unsupported. For each, first N-1 published tests used as TRAIN; last public assertion used only after program generation.
- [Actual first #714](https://github.com/yoonsj0305/NEUMANN/actions/runs/42354198810), [immutable full artifact #13567052253](https://github.com/yoonsj0305/NEUMANN/actions/runs/42354198810/artifacts/13567052253): generated first-source-TRAIN programs 4/21; original heldout exact 4/21; strong prior filter 2/21; original literal-only source constructor 2/21. +2 heldout exact from induced nonliteral modulo expressions.
- #554 (Google independently authored) generated `remove if x%2 == 0`, reference `keep if x%2 != 0`. Z3 proved the two predicates are equivalent for ALL integers. This means exact equality on arbitrary-length integer lists by per-element induction.
- #629 generated `remove if x%2 == 1`, reference `keep if x%2 == 0`. Z3 proved equivalence for ALL integers (modulo 2 in {0,1}), hence arbitrary-length integer list equality.
- #800 generated `remove if str.isspace(c)`, reference `re.sub(r'\s+', '',text)`. Python `str.isspace()` and `re.fullmatch(r'\s',char)` were evaluated on all **1,114,112 Unicode codepoints**, 29 whitespace codepoints, 0 disagreements; deleting each whitespace character is equivalent to replacing every nonempty whitespace run by empty string. This is implementation/Unicode-version dependent but exhaustive under the tested Python runtime.
- #593 generated `remove if c == '0'`, passed one original test but is **NOT correct** for the reference `re.sub(r'\.[0]*','.',ip)`: on `10.01`, generated `1.1`, reference `10.1`. This is a false positive and is preserved as FAIL.
- [Independent POST-FIRST proof #42354597895](https://github.com/yoonsj0305/NEUMANN/actions/runs/42354597895) [proof artifact #13566977208](https://github.com/yoonsj0305/NEUMANN/actions/runs/42354597895/artifacts/13566977208): exact original generated ASTs loaded from frozen #714 action artifact, Z3 integer equivalence both UNSAT for counterexample, full Unicode category exhaustive check 0 mismatches, expected #593 counterexample confirmed.

## C. Exact matched memory causality, separate post-FIRST run

- [Actual matching vocabulary ablation #42354886619](https://github.com/yoonsj0305/NEUMANN/actions/runs/42354886619), [full artifact #13567365743](https://github.com/yoonsj0305/NEUMANN/actions/runs/42354886619/artifacts/13567365743). This is explicitly POST-FIRST on exposed original tasks, not a new independent external test.
- The cold arm receives the **EXACT same human-coded typed predicate search grammar and primitive generic fold**, but no previously source-learned constructor AST or source-memory entry. All other I/O, source-training split, predicate candidate rank and original heldout are identical.
- Official MBPP task IDs 511..974: 163 source original IDs, 21 supported. With memory **4/21 exact**; same grammar without memory **4/21 exact**; **memory-specific accuracy lift 0/21**. Exactly **21/21 generated predicate expressions identical** in both arms. Cold feature search used 27 candidate checks and its evaluation recorded 3.2585 ms for the 163 source tasks, excluding dataset download and integration overhead. No 10x end-to-end cost claim.
- Therefore +2 successes versus the older literal-only strong filter are **causally attributable to access to a human-programmed wider feature grammar**, not to an experimentally proven autonomous improvement of the generator's discovery policy. A real Q3 learning-to-learn PASS must survive this stronger matched ablation. This is currently **FAIL/NOT DEMONSTRATED**.

---
## Scientific causal attribution and limits

1. Source-learned constructor AST generation: **SCOPED PASS**. New executable meta-program actually created automatically from two prior verified programs. But its human-coded source adapter, fold core, anti-unifier and set-expression binder grammar are preinstalled. The source examples are from a known human-coded filter hypothesis family.
2. External semantic operator inference under fixed typed feature vocabulary: **SCOPED PASS**. Two independently authored MBPP numeric filter tasks (#554,#629) were correctly generalized by a data-derived modulo condition and strongly outperformed a prior **literal-only / HUMAN-filter** baseline on the published original last assertion; post-first Z3 justified full integer semantics. One Unicode filter (#800) is also reference-equivalent under tested Python Unicode semantics.
3. **No causal proof that source memory itself added the +2 correct tasks**: the improved predictor was given a NEW human-coded modulo/Unicode feature grammar that the strong old baseline lacks. A properly compute-matched cold predictor using exactly the same feature grammar and an ordinary fold can also discover those tasks. Treat the observed +2 as effect of a *new fixed hypothesis language plus automated parameter/program induction*, not as proven learning-to-learn policy improvement.
4. Public original tests are weak: only ONE published heldout assertion per eligible task; semantic audit after original first is essential. New original IDs 511..974 come from the SAME Google benchmark author; this does not prove transfer across many independently authored domains.
5. Strict parser coverage remains **21/163**, excluding most real programming problems. True generality to graphs, trees, stack machines, variable-shaped outputs and arbitrary new representation constructors remains OPEN.
6. Q3 global self-invention of a NEW representation CONSTRUCTOR GENERATION ALGORITHM NOT IN THE HUMAN-CODED META/HYPOTHESIS SET: **OPEN**. Q4 discovery efficiency benefit or 10x cost win: OPEN. Q6 cross-representation robust causal transfer: OPEN.

## Degraded mode and next decisive experiment

- Reject malformed/unhashable/partial transformations; abstain rather than confidently predict.
- Freeze ALL meta-level primitives, then evaluate on a DIFFERENT author benchmark whose target families require an entirely absent representation constructor. The system must *generate and independently verify* the missing constructor code, not add a new branch in human-written interpreter.
- Include a **proper matched ablation**: cold universal fold with EXACT same modulo/Unicode primitives as the memory-enabled learner; memory without grammar extension; grammar extension without memory; and a competitive classical direct solver. Count *total discovery + proof + memory + execution* costs and final correctness.
- Require multiple independent new constructor-generating algorithms with proof-carrying transfer across structurally distinct domains before global Q3 PASS. Never promote passing one original public assertion or a new AST name to a universal intelligence claim.

**Result: source-program-to-program-generator synthesis confirmed; typed predicate generalization independently shown for two integer filter tasks; full unrestricted Q3 remains OPEN.**
