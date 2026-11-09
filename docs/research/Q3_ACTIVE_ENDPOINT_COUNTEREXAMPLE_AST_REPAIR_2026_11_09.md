# NEUMANN 1 | Q3 Counterexample-Driven Process AST Revision

2026-11-09 · PR #733 stacked on PR #732 · Q3 invention priority; Q4 cost deferred.

## Root cause: unsafe representation compression

Before the fix, the TerminalOnlyProcessInventor grouped candidate transition
expression ASTs by their output vectors on the original TRAINING source inputs
and retained only three ASTs per identical vector. Source validation on new
inputs happened AFTER this compression, so a genuinely repair-capable AST
could be deleted before encountering the counterexample that distinguished
it from a shorter but false candidate. This is a *representational* failure,
not merely search ranking.

Define e1 ~S e2 iff e1(x)=e2(x) on all original source training inputs S.
This does not imply equivalence on S union V for newly observed independent
SOURCE counterexamples V. The correction constructs candidate signatures
on ALL legally observed SOURCE inputs, including V. Training and independent
validation are still separated for task scoring and the hidden target
test remains excluded.

## New production invention procedure

- Synthesize a first source endpoint-compatible latent process under a
  previously source-learned higher-order control AST.
- Generate *new source experiment input constructors* by composing typed
  primitive ASTs, not a hand-authored list of numeric counterexamples.
- Execute these constructors on SOURCE states, exclude observed/forbidden
  target inputs, resource-bound outputs, and query only a permitted SOURCE
  terminal oracle.
- If the candidate's endpoint prediction disagrees with SOURCE feedback,
  add the counterexample as an independent source verifier, refine the
  representation signatures, and **synthesize a structurally new process
  transition AST**. Record the old and revised AST.
- If no valid repair exists, or source feedback budget is exhausted, ABSTAIN
  rather than return the known-false executable process.
- Source-verified trusted classical methods still preempt invention, with
  zero new oracle queries.

Production code: neumann1/active_terminal_process_inventor.py,
neumann1/terminal_only_process_inventor.py; both NeumannEngine and
RegistryEngine have meta_invent_active_terminal_process interfaces.

## Evidence / falsification trace

Initial independent CI 42546266767: 11 tests PASSED, 1 FAILED.
New signed-domain source challenge returned ABSTAIN_GRAMMAR_GAP. The flaw
was traced to training-only signature compression.

Following the fix, workflow 42546441502: **12/12 PASS** including old
terminal-only tests and new real source-generated experiment/revision tests.

Original SOURCE signed-integer examples contain only nonnegative integers
ending at zero; a program fitted to them incorrectly sends negative inputs
to zero. Newly synthesized experiment input constructors discover negative
SOURCE probes, obtain the permitted endpoint counterexample, and reconstruct
a different AST with source-consistent signed termination. The focused test
then verifies 24 previously unqueried negative and 100 nonnegative inputs,
plus classical bypass, forbidden target-input and fail-closed semantics.

Workflow q3_active_endpoint_frozen.yml is a subsequent SHA-frozen first
proposal before synthetic scorer opens 800 fresh integer/set/string targets;
its scientific status depends on actual CI result and archived artifact.

## Proof scope

The corrected dedup rule preserves source-observably distinct candidates
on all recorded source counterexamples. It does not provide unrestricted
identification from finite observations.

Fixed-point execution certifies a fixed point of the INVENTED transition,
not the unique hidden physical transition. Two different transitions with
the same terminal-map on every input are indistinguishable to ANY terminal
oracle, no matter how many queries are made.

SOURCE-PROBE-CONSISTENT is scoped empirical evidence; it is NOT an
independent-author original, mathematical universal generalization, or
frontier-level autonomous invention claim. Typed atoms, search bounds and
source oracle availability are supplied by the researcher.

Status: **SCOPED AST REPAIR PASS; GLOBAL Q3/Q6 OPEN; Q4 DEFERRED**.


## Frozen 800 evidence after source-only repair

GitHub Actions 42546939669 completed SUCCESS. The proposer SHA locked all
800 target predictions BEFORE the scorer opened their synthetic expected
terminal outputs. The SHA-256 was
26e12b70640b1e5ec8d41e34e5b57b30cb6f925b0901bf53d6ac5a179d10ec2b.

Matched first-proposal exact scores:
- Integer signed-domain: old 200/400, revised 400/400.
- Finite set: old 200/200, revised 200/200.
- String: old 200/200, revised 200/200.
- TOTAL: **600/800 -> 800/800**. The 200 newly corrected answers are in
  ONE signed-integer family; neither other family improved its accuracy.

The source-only falsifier found input -17; the prior program predicted 0
when the permitted SOURCE oracle returned -17. The invented transition AST
changed from a decrement-to-zero update to the sign-preserving update
T(x) = x - max(0, min(x,1)). A source-verified full-state fixedpoint loop
then produces the correct terminal map for the frozen extended-range
signed-integer target inputs.

Source-query counts on this run: integer 53, sets 5, strings 296. These
are additional permitted SOURCE observations, so the result demonstrates
ability correction, **not** an inference-efficiency win. The source oracle
and target input families are researcher-authored. Independent-author
frontier generalization is still OPEN.

Workflow and archived predictions:
https://github.com/yoonsj0305/NEUMANN/actions/runs/42546939669


## Higher-order experiment invention (source-only hypothesis disagreement)

Additional production improvements on this branch preserve multiple executable
source-fitting process hypotheses that differ on **unlabeled, generated SOURCE
experiments**. They then synthesize a question maximizing pairwise
terminal-prediction disagreement among the surviving hypotheses. The
question generator does not access target labels or successor trajectories.
Every SOURCE answer filters the executable hypothesis version space, and an
answer falsifying the chosen process invokes a NEW AST synthesis.

GitHub Actions 42547326943 proved this path was exercised:
- 3 executable version hypotheses examined in the signed-integer study.
- 1 source-oracle question with positive hypothesis disagreement.
- 1 counterexample-driven transition AST revision.
- 53 SOURCE terminal-oracle queries including ordinary verification.
- All 12 targeted production/regression tests PASSED.

This is a verified **bounded source-question-generation plus program revision**
result. It does NOT imply the learner autonomously discovered its own primitive
instruction semantics, uniquely recovered hidden state trajectories, or
generalized to unseen independent-author mathematics.

Evidence: https://github.com/yoonsj0305/NEUMANN/actions/runs/42547326943
