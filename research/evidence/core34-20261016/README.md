# NEUMANN CORE-34 | Authentic LIA cross-family classical invariant baseline
2026-10-16 · DEVELOPMENT ONLY. **Q1–Q7 remain OPEN.**

## Executed evidence
A source-driven classical enumerator reads the entire original Constrained Horn Clause (CHC) source, proposes a homogeneous affine equality interpretation with coefficient domain {-1,0,+1}, zero offset, and proves each original Horn clause (including the unsafe goal) by independently checking the negation with system libz3. All three actual sources from CHC-COMP'26 commit `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`:

| Source (extra-small-lia/) | Arity | Synthesized interpretation | Original clause proofs | Candidates / Z3 calls | 20-run median |
|---|---:|---|---:|---:|---:|
| bouncy_symmetry_000.smt2 | 2 | x-y=0 | 5/5 UNSAT | 3 / 9 | 42.192ms |
| bouncy_two_counters_equality_000.smt2 | 3 | x-y-z=0 | 5/5 UNSAT | 10 / 27 | 139.160ms |
| bouncy_three_counters_merged_000.smt2 | 4 | x-y+z-w=0 | 3/3 UNSAT | 35 / 71 | 143.572ms |

**13/13 actual original Horn clause negations UNSAT**; exact Git blob identities independently matched the source bytes. 11/11 tests passed, including actual SAT counterexample for replacing inferred predicates with `true` in all three originals, plus poisoned transition, poisoned goal, and alpha-renamed predicate controls. SHA-256 code+receipts archive in session: `1f62e377073211cada043397384c6dd0da0e9219ea0a078b967747ce2e7fdeb8`, 9,623 bytes; ZIP CRC and 9/9 payload SHA checks PASS. Third-party SMT source bytes excluded from archive; pinned fetch script included.

## Scientific boundary
**No neural model was trained or invoked.** This confirms only a restricted classical invariant synthesis capability on a new real LIA CHC family. It is *not* autonomous learned creation of a fresh auxiliary predicate/language; it interprets original predicate symbols using human-defined simple affine grammar, one same-form expression per relation, no conjunction or nonlinear grammar. The three examples were observed by the researcher before the experiment, so this is **NOT a preregistered blind generalization test**. There is **no valid 10x superiority comparison** to a capability-matched baseline or frontier model. Unknown/errors reject, unsupported arity abstains.

## Decision
Do not waste neural training on tiny affine CHCs that the cheapest exact solver already proves. Next sole neural gate: consume full authentic Horn source + visible goal, emit a new non-supplied typed predicate language, prove an unseen external hard-family original, and beat matching specialized classical synthesis on full lifecycle costs. Keep historical failures and Q1–Q7 OPEN.

Upstream source: https://github.com/chc-comp/chc-comp26-benchmarks/tree/b4fa7a708e5863bbcdb5de50d692ead3a67cbedc/extra-small-lia
