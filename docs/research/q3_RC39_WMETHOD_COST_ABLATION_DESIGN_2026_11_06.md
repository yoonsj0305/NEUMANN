# NEUMANN 1 | RC39 W-method conformance cost ablation

2026-11-06. **Research Draft / proposed gate, not an empirical PASS until CI.**

## Verified starting point

RC39 draft PR #651 reports independently checked all-length equivalence for 24/24 complete finite-state transducers with a public target bound of <=5 states. The original *membership-only* exhaustive conformance checker cost 172,051 distinct source-word calls, 1,362,696 input characters and 172,499 conformance word checks. Original primary results and learner source remain untouched.

## Single causal hypothesis

Can a **known classical W-method** reduce the cost of a source-membership-only completeness check by >=10x on those SAME 24 opened tasks, while both baselines still obtain 24/24 independent exact product proofs, zero false certificates, and equal access rights?

Both methods receive only membership(word), alphabet ABC/output 01, public upper bound N=5, the same query caps, the same frozen active learner and the same original reference families. The conformance checker is forbidden to read the reference transition graph. Hidden reference structure appears ONLY when constructing the black-box membership callback and when checking frozen output with a separate product algorithm.

## Method and proof boundary

Minimize the candidate transducer to reachable behaviorally distinct states (n). Construct its shortest state cover P and a state-characterization suffix set W. Enumerate and deduplicate the classical W-method finite complete suite:

    P · Sigma^(<= N-n+1) · W

This is *not* a newly invented technique and not a neural discovery. Its completeness holds only for complete deterministic Mealy machines, truthful resettable membership, fixed alphabets, and a TRUSTED bound N. A falsification test deliberately supplies an invalid bound and demonstrates false certification can follow. Budgets and inconsistent interfaces fail closed to UNKNOWN.

Reference: Kruger, Junges and Rot, "Small Test Suites for Active Automata Learning", TACAS 2024, Sec. 3, https://link.springer.com/chapter/10.1007/978-3-031-57249-4_6

## Precommitted acceptance and negative controls

Required gate: 24/24 exact independent product proofs for BOTH algorithms; baseline replays 172,051 source queries; challenger uses at most 17,205 unique queries (>=10x reduction); all caps enforced; no additional ARC evaluation items opened. Supporting regression: 780 exhaustive small-model comparisons, 500 three-state adversarial comparisons, candidate minimization, invalid state bound, query budget failures. Keep FIRST remote run and any failures immutable.

## Interpretation even if gate passes

A classical conformance-verification optimization may offer real measured source-query savings. It would **not** establish global Q3 autonomously invented operations or trained discovery policies, Q4 learned-versus-classical 10x TOTAL cost, Q6 outside-substrate semantic generalization, or Q7 frontier performance. The 11 globally unused public ARC-AGI-1 evaluation IDs remain reserved.

**Degraded mode:** UNKNOWN on budget exhaustion, broken interface or unverified state-bound contract. No silent PASS.
