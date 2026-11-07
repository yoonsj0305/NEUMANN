# NEUMANN 1 | Compositional proof for copy invariant transfer across arrays and strings

Date: 2026-11-07. **Global Q3/Q4/Q5/Q6/Q7 remain OPEN.**

## Research question
Can the proved array-copy prefix invariant be reused for the *different SMT String theory* through a machine-checked observation map, rather than re-solving a heavy String substring induction end-to-end?

The map is **human-specified**, not a self-invented learned abstraction:

- For a finite string x of length n, alpha(x)[j] := str.at(x,j) for 0 <= j < n, an array-valued observation of one-character strings.
- A copy-write at cursor i in String uses substring/concatenation replacement.
- The abstract Array update writes source character to destination at i with store.
- Pointwise commuting diagram: alpha(T_string(src,dst,i))[j] = T_array(alpha(src),alpha(dst),i)[j], for all j in [0,n), assuming equal source/destination length n and 0 <= i < n.

## Frozen original FIRST and subsequent failure
Original [PR #683 FIRST run #42322134104](https://github.com/yoonsj0305/NEUMANN/actions/runs/42322134104): **7/9 checks passed, FAIL.** Direct String substring induction was TIMEOUT under 8 seconds. Separate Array finish check was inconclusive, not UNSAT. Important genuine positives: pointwise string/array commuting proof UNSAT (3.16 s), string completion UNSAT, wrong-write SAT.

Compositional [PR #684 first run #42322416607](https://github.com/yoonsj0305/NEUMANN/actions/runs/42322416607): **3/6 checks passed, FAIL.** All abstract obligations were UNKNOWN/CHECKER_ERROR because the script mixed an (Array Int String) sort with restricted AUFLIA logic. This is a solver-input contract bug; it is not evidence of a mathematical counterexample. Both failure receipts retained as independent runs.

## Corrected logic and actually executed result
[PR #685, run #42322545662](https://github.com/yoonsj0305/NEUMANN/actions/runs/42322545662) changes ONLY the abstract-layer logic declaration to ALL, preserving every proof formula and counterexample requirement.

Six Z3 checks are now independently returned with the expected answers:

1. ABSTRACT_INIT: UNSAT.
2. ABSTRACT_STEP_COMPOSED_FROM_POINTWISE_STORE: UNSAT.
3. ABSTRACT_FINISH_WITH_GROUND_INDEX: UNSAT.
4. STRING_TO_ARRAY_STORE_COMMUTES: UNSAT. This script is reused byte-for-byte from the original FIRST's core commuting obligation.
5. STRING_SAME_LENGTH_EQUAL_PREFIX_FINISH: UNSAT.
6. CORRUPTED_REAL_STRING_UPDATE_WITNESS: SAT.

Observed solver subprocess wall sum 3106.347 ms; whole Python process 3.14 seconds; max RSS 47,092 kB. This is not whole-system performance compared against an equally provisioned optimized direct string prover; the direct 8-second cap is censored.

## Conditional proof argument and explicit remaining gap
Array induction gives prefix equality of abstract per-position observations after every correct abstract write. The independently checked commuting equation shows each concrete String replacement has exactly the same in-range character observations. Therefore by induction the concrete string loop preserves *pointwise character equality* on the copied prefix at every step.

To replace this with an entirely machine-certified end-to-end string theorem, a proof assistant or an additional independently checked bridge lemma must establish that equal-length strings have equal prefixes iff their character observations at every index below the prefix length agree. The present scripts do not certify that general bridge lemma as a standalone machine proof. The proof here is therefore a rigorous **conditional mathematical composition with individually SMT-checked obligations**, NOT a Lean theorem proving the original source code end-to-end.

No external independently authored program was run. All test cases and alpha were human-authored. There is no neural training, learned operator invention, genuinely frozen cross-author holdout or full Q6 original-problem PASS.

## What this changes in NEUMANN's architecture
1. Stop retraining learned selectors for direct algebraic or semantic entailments.
2. Store reusable proof objects indexed by formal assumption and observation map, not textual problem similarities.
3. A proposed transfer must generate a typed alpha, a commuting condition alpha(T(x))=T'(alpha(x)) and a bridge obligation.
4. Proof backend verifies those obligations before using any transferred result. Unknown/timeout means ABSTAIN and classical fallback.
5. Learning is reserved for finding new alpha or new typed operators that were absent from the frozen grammar, then verified against strong equal-rights classical synthesis and independent authored benchmarks.

Recent related approaches: LimICE (arXiv:2607.27606) performs lemma-wise ICE learning with sound verification; Whiel (arXiv:2611.05612) uses leveled invariant checking, feedback and Lean certification; Quokka (github.com/Anjiang-Wei/Quokka) couples model proposals with independent correctness checks. We must not claim this architecture as a new general invention without a rigorous novelty comparison.

## Decision
**PASS_SCOPED** for the six source-free Z3 proof obligations of array/store-to-string observational simulation. **FAIL/OPEN** for learned cross-formalism Q6, model-driven novel Q3 operator and total amortized Q4 improvement.

Do NOT consume reserved CHC COPY4/5/6 originals or claim Frontier-level intelligence from a human-defined transfer. The next Q6 gate is a frozen learned proposer inventing alpha on a truly independent formalism with machine-checked commuting and bridge proofs, and costs compared with direct strong classical synthesis.
