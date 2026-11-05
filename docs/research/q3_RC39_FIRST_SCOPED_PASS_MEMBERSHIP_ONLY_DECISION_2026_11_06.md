# NEUMANN 1 | Q3 RC39 ACTIVE STATE STRUCTURE · original first / source-only cost closure

Date 2026-11-06 · Research draft, not a global Q3 PASS. North Star: **frontier-level problem solving with minimum necessary computation.**

## The point of this experiment
RC38 learned 0-4 local relative reads, but its supplied source language can inspect only up to ±7 local positions. Two 41-character ABC words differing exclusively at the first symbol are identical at the central B's ±7 window, yet a target that changes that B based on the parity of all earlier A characters requires different outputs. A fixed local read instruction cannot represent this unbounded-prefix memory. This is a rigorous scoped representation ceiling, not proof that no other AI approach could solve it.

RC39 uses **active observation-table Mealy induction**, a known **classical** finite-state learning algorithm. A fixed finite-state metagrammar and input/output membership service are provided by humans. The learned state count, transition graph, and executable state tables are not given to the learner. Its output is an executable deterministic finite-state transducer, verified with a second implementation.

## Precommitted FIRST, perfect equivalence oracle available
- [Opened smoke #42130191896](https://github.com/yoonsj0305/NEUMANN/actions/runs/42130191896): 3/3 tests PASS.
- Learner source Git blob **`83bd15d98b8fa02f4427b26c27264d35c0ec261e`** and 24-case first preregistration were immutable before independent grader was authored.
- Six targeted state-structure classes × four deterministic seeds, **24/24** source-generated executable transducers independently certified to agree on **every finite input string** by exhaustive reachable product-state BFS. This is not extrapolation from finitely sampled test strings.
- `30` independent exact equivalence service calls, `1,082` unique internal source membership calls, `4,237` source characters; first original **total model process CPU ~6.014197ms** on the one GitHub Actions CPU runner. Financial, electrical and model development cost unknown.
- All-length proof does NOT apply to arbitrary Turing-complete programs. The oracle itself has access to the exact hidden reference states and can return a shortest counterexample.
- [FIRST #42130628242](https://github.com/yoonsj0305/NEUMANN/actions/runs/42130628242); raw FIRST SHA256 `829bab136751cc72f972d489d25ace9bde9cae0b29208a3c99a04d1fe66f1a05`.
- [Independent first read-only audit #42130960223](https://github.com/yoonsj0305/NEUMANN/actions/runs/42130960223): alternate AST interpreter, **24/24 all-length**, **24/24 mutated transition programs rejected**, forged first receipt rejected, no re-learning.

## The essential source-rights upgrade: NO perfect equivalence service
The next test reused the **same already opened 24 task families**. It is a source-rights ablation, NOT a clean heldout semantic-family test. Learner received only `membership(word) -> output` and a public bound `at most 5 hidden states`. An external conformance checker, without reading the target graph, enumerates all source input words of length at most `5 + candidate_states - 1` and returns a discrepancy, if found. Completeness follows by iterative state-equivalence refinement over the disjoint union of any two complete deterministic Mealy machines (if non-equivalent, some distinguishing string has length at most n+m-1). Independent hidden-state product proof runs **only AFTER** the learner emits a program.

- [FIRST reopened membership-only run #42131620991](https://github.com/yoonsj0305/NEUMANN/actions/runs/42131620991) scoped **24/24 PASS**, no wrong all-length certifications.
- **172,051** distinct source membership requests, **1,362,696** distinct query characters, **172,499** finite conformance word checks, **30** conformance callbacks, **676.103135ms** measured total process CPU; all original input calls, including the complete conformance checker, counted. No hidden exact-equivalence calls.
- First membership-only source receipt SHA256 `f89b488bee9dfe3f04ec2ac0566bab265385b08d32611ea637c4fa299e3d1f1f`.
- [Independent read-only audit #42131926384](https://github.com/yoonsj0305/NEUMANN/actions/runs/42131926384): 24/24 programs independently all-length proved, 24/24 mutated programs rejected, exact original query totals reconstructed, forgery rejected, no re-learning. Original source file hashes unchanged.
- This source-only interface required **~159×** the earlier ordinary learner's membership query count (172,051 / 1,082). CPU was also higher in separate runs, but the interfaces differ, so raw CPU ratios are NOT a same-rights performance comparison.
- Trust boundary: theorem assumes complete deterministic Mealy target with ≤5 states and truthful membership responses; absent such a bound, finite data alone cannot certify arbitrary all-length behavior.

## Fundamental identifiability boundary

It is impossible to promote finite source observations to an all-length theorem **without a trusted state/grammar bound or a sufficiently strong proof oracle**. Constructively, for any observed finite input set whose longest string has length L, two deterministic complete Mealy machines agree on every observed word: (i) one-state ALL_ZERO, and (ii) an (L+2)-state counter emitting 1 only at the (L+1)th observed A. Yet A repeated L+1 times separates them. Thus no learner observing only finitely many queried strings can rule out arbitrary larger machines. This is a counterexample to *unconditional* all-length certainty, not a failure of the legitimate bounded-state RC39 certificates.

[First mathematical negative-control CI #42132637162](https://github.com/yoonsj0305/NEUMANN/actions/runs/42132637162): 2/2 tests PASS; for source length L=0..6, all alphabet-ABC words up to L match and the length L+1 witness differs. The bound-5 premise is necessary and visible, not hidden in the verification procedure.

## Gate status and decision
| Question | Evidence | Status |
|---|---|---|
| Automatically construct a new finite-state transducer from IO evidence | Source-only 24/24, alternate finite-state all-length proof | **SCOPED PASS** |
| Avoid access to exact hidden-model equivalence oracle | Membership-only 24/24 using known ≤5-state bound | **SCOPED PASS, queries expensive** |
| Break RC38's fixed local-radius representational ceiling | Exact parity-prefix indistinguishability witness vs RC39 model | **SCOPED PASS** |
| Invent an entirely new base ISA or learn the discovery policy in neural weights | A known human-authored L* algorithm and finite-state executor were provided | **NOT PROVEN** |
| Transfer to truly independent, external semantic family (Q6) | All 24 tasks are in the human-provided Mealy substrate; membership-only reuses them | **OPEN** |
| Beat strongest equal-rights classical baseline by 10× total cost (Q4) | The RC39 discovery algorithm IS classical; true source-only probe cost is high | **NOT PROVEN** |
| Frontier-grade general problem solving (Q7) | 24 bounded finite-state automata, no ARC or SyGuS capability gain | **OPEN** |

**Decision:** Keep RC39 as a small, independently executable **state-structure discovery subsystem** and future conformance-test primitive, not as global NEUMANN 1 completion. Reuse prior RC29/RC38 genuine PyTorch learned-semantics work if exploring learned policies, but do not repeat local radius/grammar enumerations. Next admission must compare a learned discovery-policy improvement against best **equal-query and equal-source** classical active learners and a truly independent external-author family; use formal trust accounting and reserve the last 11 unregistered ARC-AGI-1 evaluation tasks. Preserve all original receipts; no further favorable regrading.
