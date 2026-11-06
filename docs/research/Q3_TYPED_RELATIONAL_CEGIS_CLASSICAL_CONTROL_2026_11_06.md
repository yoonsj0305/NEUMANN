# NEUMANN 1 | Typed relational invention: strong classical control BEFORE any neural claim

Date: 2026-11-06. Stacked on Draft PR #672. All global Q3/Q4/Q6/Q7 gates remain **OPEN**.

## Research question
Can the claimed missing H0-to-H1 interface already be traversed by a conventional
typed synthesis algorithm when it gets exactly the same observable traces and
a proof oracle? If so, simply generating COPY_PREFIX is **not** exclusive
evidence for a learned model's self-invention.

## Scope, contract and strict nonclaims
- Source-free, human-authored synthetic programs only. No new external original
  CHC bodies, no copy4/copy5/copy6 access, no ARC EVAL.
- Generator receives only four prefix traces, H0 collision signal, and a
  verifier callback. It does not receive the true source symbol, coefficient,
  bias, or an existing COPY_PREFIX program template.
- Both source arrays are typed `Array Int Int`; a third is destination.
  Fixed and **human-designed** grammar: select one of `left/right`, use
  coefficient in {-1,1,2}, offset in {-1,0,1}; 18 candidates total.
  Selection by finite trace consistency, then Z3 induction on arbitrary
  arrays / arbitrary nonnegative cursors.
- Proof queries check rejection of an inductiveness counterexample (UNSAT)
  plus acceptance of deliberate corrupted store (SAT), no fallback to
  optimistic PASS on timeout/unknown.
- Three synthetic updates differ: identity, +1, 2x, with an unrelated second
  array so source symbol must be inferred from traces.
- This is deliberately a **classical, untrained strong baseline**. There is
  no own-weight learning, no open-ended AST invention outside its grammar,
  no unseen external-author benchmark, no Q6 cross-formalism transfer, and
  no total-cost Q4 advantage claim.

## Pre-registered finite test before remote Z3 evaluation
1. Each task must have H0 destination-only indistinguishability collision.
2. True operator must be proposed without task-name or update-expression
   input to the proposer.
3. Every accepted candidate's quantified induction query must be UNSAT.
4. Every accepted candidate's corrupted transition must have SAT witness.
5. Any missing/unknown/timeout checker, absent collision, or missing candidate
   must ABSTAIN, never PASS.
6. Full Python and Z3 process wall for each case must be recorded.
7. If 3/3 PASS, the result is **scoped classical sufficiency** only, and
   the future neural method must outperform it on an identical language and
   proof budget. If FAIL, preserve the first failure rather than rescore it
   as success.

## Economic contract
End-to-end comparison, when an actual neural candidate exists:

C_total = C_train + C_discover + C_verify + C_adapt + C_inference + C_failed_attempts

C_amortized_per_task = (C_train + C_discover + C_adapt)/N +
                        C_inference + C_verify + C_failed_attempts/N

Count external source retrieval and human authored label generation where
material. Do not use proof-only milliseconds as evidence for 10x.

## Post-experiment interpretation guardrail
If the classical generator can construct a typed relation, the human-designed
typed grammar and verifier still deserve causal credit. To pass global Q3,
a frozen learned proposer must produce a semantically new admissible operator
not simply enumerated by this same baseline, on untouched independent source
tasks, while beating equal-rights classical/strong-native comparisons.
Q6 additionally requires proof-preserving transfer across formalisms, not
merely a different array expression. Use classical fallback or ABSTAIN by
default.
