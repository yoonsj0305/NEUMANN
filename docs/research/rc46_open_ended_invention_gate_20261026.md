# RC46 / OEIT: Open-Ended Invention Test

**2026-10-26 research-only draft. Do not merge as Q3/Q4/Q5/Q6/Q7 PASS.**

## Architecture pivot
Frozen NEUMANN North Star: `Frontier-level problem solving with minimum necessary computation`.

Stop treating scaling within human-crafted grammar as evidence of general intelligence. Primary object of learning must be **how to invent problem representations and reusable methods**, not merely how to predict source tasks' code or operators.

Minimal contract:

`Original problem -> Cheapest known classical path -> Bounded learned perspective search -> independently verify -> retain new abstraction with provenance/cost -> transfer to independently authored, DIFFERENT problem family`

Degraded mode: UNKNOWN / ABSTAIN and verified fallback. No unverified candidate may become an authority. Discovery, source constraints, all failed trials, verification, executor and future reuse all have accounting receipts. Default is no neural invocation when proven classical solution exists. New methods are judged at **original-task iso-capability**.

## Creation gates (all still OPEN)
- **A: new program**. A function/program not directly supplied, discovered from original I/O, independently correct.
- **B: new useful abstraction**. Learner autonomously constructs the representation and interface (not just parameter values inside a task-specific interpreter) and proves it useful/reusable against unchanged strong controls. Must not be a human-authored target template.
- **C: discovery-policy transfer**. Without modifying learner, it discovers NEW abstractions on separately authored heldout problem families. Simply replaying a saved macro on the same semantic task with a different input type is NOT C.
- **Q4/Q5**. Discovery costs, search failures, model/API inference, verify and memory costs are included; Q5 compares the complete system with strong Direct. A 10x primitive-iteration reduction is NOT a 10x system result.
- **Q6/Q7**. Prospective external families, independent correctness, actual frozen frontier-gap observations, model contamination audit and resource costs all required.

## RC46 ACTUAL synthetic mechanism smoke
An executable Python prototype is archived in the 2026-10-26 ChatGPT attachment `NEUMANN1_RC46_OEIT_MECHANISM_SMOKE_20261026.zip`, archive SHA256:
`c7b5a8614bd96a355d480e21420d6e5b9a6d93fe2cefecda8143958833104884`.

Implements generic bounded composition search over original IO, MDL-proxy extraction of unseen composite macro from successful traces across distinct source data types, append-only explicit macro code, then no-memory vs memory search on synthetic tuple inputs. This is a **classical program discovery and reuse algorithm, not a trained NEUMANN learned core**.

The original v0 used weak examples. The baseline found an accidental early shortcut on source data in **6 candidate calls**. Historical v0 preserved as falsification; never relabel it as generalization.

The revised v1 strengthened source examples exhaustively for target alphabet/length:
- Independently scored two new but **same underlying target family** tuple tasks. Both arms 2/2 exact; no model trained.
- Candidate evaluations: strong original bounded enumerator 393+393, learned-library-first 1+1.
- Original single-run elapsed ns, excluding module bootstrapping: no library 12,896,619 ns; with library including source-task discovery 15,362,468 ns. Thus with-library is **1.19x slower** end-to-end in the measured tiny fixture; no 10x claim.
- Original FIRST source-only prediction receipt sha256 `322eea6d40266301773682ee7218c4903dfbaa69a058a09e7da08d28e585d6a3`.
- The clean extracted ZIP hash manifest passed, `pytest` 4/4 passed; full clean replay confirmed stable prediction/candidate counts but timing differed.

**Absolute evidence boundary:** tasks intentionally authored by implementer; two unseen *data types* share one target transformation; no true blind independent generalization, own-weight model creativity, energy, original frontier gap or all-in Pareto result. This is only an architecture harness smoke. Keep global Q1–Q7 OPEN.

## NEXT external OEIT preregistration: NOT RUN
Before inspecting holdouts, pick original independently authored tasks from three genuinely different semantic domains, e.g. symbolic/program transformations, ARC-style grid reasoning and formal constraints/graphs. Pin exact upstream revisions, task identities and graders. Source train two domains; third author/domain is never revealed until model and full discovery policy are frozen. Ensure underlying target semantically differs; do not leak a predefined target macro or gold source code into the learner.

Compare: (a) learned system with persistent verified abstractions, (b) identical system with library reset/no learning, (c) strong same-rights classical search/program synthesis/SMT, (d) foundation/direct+tools where accessible, (e) shuffled or false-macro control. Keep input data access, total compute budget, tool rights and source examples matched; count failed trials. All first model proposals/weights/code/results hash-frozen BEFORE gold.

Acceptance targets proposed before selection (not yet registered with dataset identities): >=20 third-family tasks; >=3 independently verified nontrivial B-level new concepts, >=2 useful transfers to novel target semantics; paired 95% confidence interval lower bound above zero for incremental third-family correct count; ZERO admitted verifier errors. Separate North Star Q5/Q7 demands >=10x *measured* full cost at matched actual frontier-gap capability on multiple families; cannot be inferred from this smoke. All numerical thresholds must be frozen with exact benchmark selection and cost conventions.

## Decision gate and cost
Candidate abstraction is admissible only when code is constrained to a safe interpreter, independent test confirms original task, and full benefit including future reuse exceeds discovery+verification+storage/fallback charge. Failed, ambiguous, or underconstrained -> UNKNOWN.

Physical resources measured by CPU-ns, joules, peak memory and $$$ as separately specified. The manufacturing `Idiot Index = finished-product cost / raw material cost` is UNKNOWN / not meaningfully measured for this software-only diagnostic. Never invent a numeric value.

WBS estimate, effort units (not schedule promises): lock provenance+grader 3; implement true own-weight general proposer 5; sealed freeze+third-domain run 5; matched ablation and cost 5; contamination+independent reproducibility audit 2; add 25% measured effort buffer. Stop early on independent validation failure and keep immutable negative results.

## Research positioning
RC38 had bounded learned READ_REL opcode growth but human-defined CREATE compiler. RC41 solved original opened 12/12 with posthoc classical code, not frontier evidence. RC44 ChatGPT GPT-6 wrote a valid scoped ARC operator, NOT NEUMANN own-weight invention. RC45 GPT-6-specific authored operators solved 9/12 new public ARC training problems with 3 abstentions, but their source-checked unchanged transfer to another 12 tasks was 0/12 admissions (no hidden wrong submissions). These motivate open-ended discovery-policy research, not a declaration of B/C PASS.

References: `docs/research/frozen_north_star.md`; drafts #604 (RC38), #606 (RC41), #609 (RC44); separately frozen RC45 candidate branch.
