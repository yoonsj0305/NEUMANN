# NEUMANN 1 · G0 EXACT ORIGINAL SOURCE CONGRUENCE CERTIFICATES (2026-10-18)

## Immutable scientific result

**THREE exact, unchanged 2023 Ultimate Automizer SMT-LIB `QF_NIA` original problems have been mathematically certified UNSAT**, despite the official 2026 SMT-COMP reference statuses each being `UNKNOWN` and **all 17 participating 2026 classical solver result sets returning no SAT/UNSAT** on these three original keys.

- `ps5-ll.c_2.smt2`: original SHA256 `d1864366ae233ed613c0517ee11038150c7f972dc21a0e8ab35431df1976bc64`; `UNSAT` via universal 30-divisibility of `29y + 10y³ + 15y⁴ + 6y⁵`.
- `ps6.c_0.smt2`: original SHA256 `68528978bd85ad6b830131732462ea66b146c37341f9e883968a3e8e7183e152`; `UNSAT` via universal 12-divisibility of `y² + 7y⁴ + 6y⁵ + 10y⁶`.
- `ps6.c_12.smt2`: original SHA256 `60ba7df9e5d75c557c4f6f7138399127cb846c018fb6f4d0a9d361f9bedddafa`; same second divisibility theorem, original `UNSAT`.

**Important: there are just TWO algebraically distinct polynomial cores across three original cases, ONE generated source family, and these cases are ALREADY OPENED DEVELOPMENT. They are not unseen-origin Q6 transfer or neural invention.**

## Fully explicit source-derived mathematical proof (not heuristic SAT claims)

Source parser reads original `(assert ...)` expressions directly, identifies a *required top-level conjunct* `not (= (mod P(y) m) 0)` from each original, and independently extracts exact integer polynomial coefficients. It does **not** omit or mutate any original constraint. The other original conjuncts may only restrict possible assignments, never restore satisfiability once this conjunct is false for every integer y.

For any integer polynomial P and positive integer m,

`P(y)≡P(r) (mod m)` whenever `y≡r (mod m)`.

This holds for all integers (including negative y) because integer addition and multiplication preserve congruence. Consequently inspecting **every r=0,...,m-1** is a finite, complete certificate of the universal divisibility statement `m | P(y)`.

### Core 1: mod 30
`P30(y) = 29y + 10y³ + 15y⁴ + 6y⁵`.
- Modulo 2: `P30(y)≡y+y⁴≡0`, since `y⁴≡y (mod 2)`.
- Modulo 3: `P30(y)≡2y+y³≡0`, since `y³≡y (mod 3)`.
- Modulo 5: `P30(y)≡4y+y⁵≡0`, since `y⁵≡y (mod 5)`.
Since 2,3,5 are pairwise coprime, `30 | P30(y)` for all integer y. Original source asserts `P30(y) mod 30 ≠ 0`, contradiction, original UNSAT.

### Core 2: mod 12
`P12(y)=y²+7y⁴+6y⁵+10y⁶`.
- Modulo 3, `P12(y)≡y²+y⁴+y⁶≡0`: for y≡0 it is zero, for y≡±1 each power is one and the sum is 3≡0.
- Modulo 4, when y is even all monomials vanish; when y is odd, y²≡y⁴≡y⁶≡1 and y⁵≡y, so `P12(y)≡1+7+6y+10=2(y+1)≡0` because y+1 is even.
As 3 and 4 are coprime, `12|P12(y)` for every integer y. Both exact original ps6 sources require `P12(y) mod 12 ≠ 0`, contradiction; both original UNSAT.

**Independent executable certifying checks:** For each original, (a) separately tokenize and parse the complete original required conjunct; (b) compute extracted polynomial coefficient vector *from source* and evaluate all 30/12 residues both by direct parsed-AST integer arithmetic and by independent polynomial-map arithmetic; (c) all residues zero, no exception; (d) parse ALL original assertions with unmodified Z3 SMT-LIB parser and add only the **already mathematically proven** congruence as a lemma; all 3 original+lemma negated proofs `UNSAT`. This is not asking Z3 to discover the unknown lemma. The separate algebraic proof establishes the soundness of added lemma.

## First immutable executed evidence
- BEFORE proof execution, explicit formula/mechanism registered in [Issue #220 comment 6248280801](https://github.com/yoonsj0305/NEUMANN/issues/220). The source/solver outputs had already been viewed, so this is NOT a blind test.
- [GitHub Actions SUCCESS #39115949617](https://github.com/yoonsj0305/NEUMANN/actions/runs/39115949617) executed pinned real source parser proof.
- [First proof artifact #12132885246](https://github.com/yoonsj0305/NEUMANN/actions/runs/39115949617/artifacts/12132885246), ZIP SHA256 **`b513694712106ebf09a35c457dabd952c03d767312d5db31c0f444cf9e648b55`** independently verified after artifact download. JSON gives original per-file SHA256, literal polynomial coefficient maps, every residue remainder, individual original assertion counts, original+lemma independent Z3 result, source parse/mathematical proof wall times.
- Proof and original-check CPU wall, **excluding network source downloads, interpreter/setup/CI overhead**, 0.005634s, 0.001855s, 0.001759s respectively on CI Ubuntu runner. **Do not compare these times directly as a speedup ratio to a failing general solver with a 15s cap**. It is better to state a verified-answer-within-cap versus no-answer-within-cap distinction.
- Original baseline on same 3 [GitHub Actions SUCCESS #39115288928](https://github.com/yoonsj0305/NEUMANN/actions/runs/39115288928), artifact #12131553399 ZIP SHA256 `f227e953f21b329feda50dc4a677133b9478d27f9fe41d5e2a995d5267ed88ef`: Z3 4.15.4.0 0/3 original verified outcomes and cvc5 1.1.2 0/3 verified outcomes under ~14sec effective per original, all three official UNKNOWN. The cvc5 process return 134 with no SAT/UNSAT is classified as no-answer/timeout, **not a malformed program claim**.

## FAST-CLOSE gate precision and stop
- `G0_SOURCE_ORIGINAL_UNSAT_SOURCE_CERTIFICATE` **CLOSE/PASS for all three original opened source cases**, with TWO independent polynomial cores and one provenance family.
- `G0_CLASSICAL_STRUCTURAL_VALUE_EXISTS_IN_OPENED_DEV` **YES**: elementary classical modular theorem resolves exact source programs where the recorded time-capped Z3/cvc5 controls did not. It demonstrates a real **mechanism-level value**, not commercial neural headroom.
- `G0_FULL_MODERN_CLASSICAL_OPTIMIZED_COMPARISON`: **OPEN**. Mathematical source proofs alone do not establish improved *total cost against every strongest specialist*, comparable across different runtime settings. A suitable specialist modulo-polynomial tactic would also solve these cheaply and is a strong classical comparator.
- `G0_POSITIVE_FREE_ORACLE_NET_SAVINGS`: **UNKNOWN / NOT ADMITTED**; our proof is a classical targeted algorithm discovered POSTHOC, NOT free-oracle prospective matched original task solve on two independent previously unseen source families.
- `G1_NEURAL_UNKNOWN_STRUCTURAL_DISCOVERY`: **HOLD, untested**. No learned relationship discovery, no blind transfer, neural forwards 0.
- `G2_FRONTIER`: BLOCKED; Q1–Q7 all global OPEN. No claim of 10x normal throughput, frontier parity, autonomy or novel mathematics.
- **STOP this single-family DEV branch after this decisive proof.** Do not mutate targets, escalate solution claims, repeat prompts, expand original source sibling experiments or buy GPU. A future G1 is only scientifically justified once previously untouched independent original lineages and the strong specialist all-in cost gap are preregistered.

Code: `research/evidence/g0-ultimate2023-20261018/exact_original_modular_unsat.py`. Data anchored to original repo `SMT-LIB/benchmark-submission-2023` commit `7f993a017850ba547c6ea19a1bf3b54adf54a449`.
