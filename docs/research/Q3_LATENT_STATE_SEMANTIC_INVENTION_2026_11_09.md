# NEUMANN 1 | Q3 Source-Discovered Latent State and Semantic Primitive Growth

Date: 2026-11-09. Stacked research PR #734 on Q3 active-method repair #733.
Priority: Q3 autonomous executable semantic discovery, not Q4 total costs.

## New capability

Instead of only combining pre-given integer, set and string operators,
NEUMANN now builds an **unobserved internal state ontology** from binary
membership observations on symbolic sequences. The SOURCE interface exposes
only a function word -> {0,1}. It supplies NO state identifiers, transition
rules, program text, or target-score feedback.

The learned operator contains:
- discovered minimum distinct residual state classes;
- an executable state transition table over the supplied input alphabet;
- learned acceptance state classes;
- an executable program AST, source-query audit and conditional proof.

The programmer DOES supply the hypothesis class (complete deterministic
finite-state language) and a trusted numerical upper bound N on state count.
The underlying mathematical construction is conventional Myhill--Nerode
residual equivalence, not an original theorem.

## Conditional all-length proof

For any DFA with at most N states, any reachable state has an input prefix
of length <N. Any distinct minimal states have a distinguishing suffix of
length <N. Define residual signature R(p) as the vector of observed
membership labels f(p+s) over EVERY suffix s of length <N.

- Every state is represented by one observed prefix p of length <N.
- Different true states have different signature vectors R(p).
- The transition on character a is the unique state with signature R(p+a).
- Acceptance is the empty-suffix component of R(p).
- Inductively the constructed DFA's state after every input prefix is the
  residual-equivalence class of the true state. It therefore has identical
  acceptance for arbitrary longer input sequences.

All discovery SOURCE oracle requests are of length <=2N-1. The theorem is
valid CONDITIONAL on a genuine <=N-state DFA. Membership data alone cannot
certify that the unrestricted black-box source function obeys this prior.

The implementation checks observed source-state congruence, rejects
invalid alphabet/outputs, enforces finite budgets and target-probe isolation,
and disallows independent SOURCE verifiers that overlap the discovery
experiment basis.

## First executed formal evidence

GitHub Actions 42548513386: 7 focused tests PASS, following correction of a
test's wording-only assertion. Exhaustively enumerated:
  3^(3*2) * 2^3 = 5,832 binary-input, three-state transition/acceptance
  parameterizations, with no hidden transitions supplied to the learner.
Learned candidates were checked on longer unseen input words.

Further controlled tests:
- 4-state symbolic two-symbol joint parity representation;
- 5-state binary modulo-five language from raw word membership labels,
  not from hard-coded modulo operations;
- 3-state symbolic protocol-pattern recognition;
- trusted classical-first path with zero source queries;
- forbidden target probes/invalid outputs;
- nonidentifiability counterexample: accept ONLY an exceptionally long word.
  A hypothesized three-state reject-all DFA matches every bounded SOURCE
  observation yet fails the exceptional target. This explicitly proves
  finite observations do NOT establish an unrestricted guarantee.

These are researcher-written unit/formal cases, NOT independently authored
frontier tasks and NOT a new general complexity or efficiency theorem.

## Actual language-capability extension

GrammarInventor now accepts one additional kind of generated primitive
from the independent-source-certified InventedStateOperator type.
It rejects arbitrary method names, lacking proof metadata, invalid
source verification, and verification words inside the discovery horizon.

The new operation is a first-class executable instruction in the production
program-grammar search; this is not a cached answer or a source-family
router. Tests require old DSL to fail on a binary modular predicate and
then demand that after learning/promoting the new state instruction, the
same real synthesizer solves its formerly inexpressible source behavior and
generalizes on longer heldout strings.

## Independent external original author gate

Pinned author repository: eendor/formal-languages
Pinned source commit: 9f43910c2d2facfcc3c8e1510dcfae7003caf638
Published original files: examples/dfa_even_zeros.json and
examples/dfa_div3.json.

Workflow q3_hidden_state_external_first.yml:
1. Download exactly the pinned original author JSON specs.
2. Hide their transitions in a separate line-oriented SOURCE oracle worker.
3. Present only word->binary labels to the NEUMANN discovery engine.
4. Freeze 2 * 2048 = 4096 novel long-target predictions to SHA-256.
5. Only after freeze, independently open author JSON original scoring semantics.
6. Archive programs, predictions, SHA, original score and failures.

These are genuine external authored formal tasks, but BOTH use regular
finite-state semantics. No unrelated-mathematics Q6 claim is appropriate.
The classical DFA identification literature (e.g., Angluin L*) already
contains stronger purpose-built learning algorithms; the advancement here
is the new capability relative to NEUMANN's previous fixed typed DSL.

Do not label this external experiment PASS before its actual CI report.

## Research decision

What can be proven: under the explicitly supplied DFA size/class prior,
the hidden-state constructor returns an executable exact-all-length program.
Proof is independent of test-set size.

What cannot be proven: that a novel unknown black-box law really belongs
to the DFA class, that arbitrary new semantic ontologies can be invented,
or that this meets frontier-level Q3 across independent unrelated
mathematics. Global Q3 and global Q6 remain OPEN. Full-cost Q4 is deferred
by the user's research priority.

Next bottleneck: learning when the DFA class is WRONG, then autonomously
constructing a *different* grammar class (e.g. unbounded stack/counter,
tree rewrite, nonregular algebra) with a source-only falsification interface.
Crucial safety: the system must ABSTAIN on unsupported extrapolations,
not relabel source-fit as unrestricted success.
