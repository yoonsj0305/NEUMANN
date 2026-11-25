# NEUMANN 1 | Q3 Self-Revision of the Discovery METHOD (not a task answer)
2026-11-09 | PR #732 | scoped mathematical meta-algorithm experiment | global Q3/Q4/Q6 OPEN

## First principles and design deletion

The user-required target is not "another specialized generator" or faster finite beam search. It is **a single method-learning core** that learns which steps to take when the *current search procedure* fails.

The interface is:

1. A classical domain backend receives \`attempt(complexity, source_checks)\` and returns a typed \`VERIFIED\`, \`REFUTED\` or \`UNIDENTIFIABLE\` observation plus any executable program.
2. A separate, domain-name-agnostic meta-interpreter executes an invented conditional procedure AST and may recursively increase search complexity on a genuine source counterexample.
3. A source-task meta-learner generates competing ASTs from its finite metalanguage, grades them on development tasks with known meta labels, prioritizes accuracy first, then measured source query acquisition and a transparent model-work proxy. It freezes the winning AST.
4. If the first learned method is falsified by a new meta-development task, the learner synthesizes a **different procedure**. It is not allowed to change the finished policy after opening test-target answers.
5. Classical specialist candidates have a first-class source-verified bypass, and all modelers abstain when source evidence is absent or a target query is attempted.

**Crucial scope:** Existing GF(2) polynomial elimination and symbolic-periodicity calculations remain classical. These are supplied as test adapters under \`research/q3/\`, not new production generators. The invented output is a **control program** describing how to call, challenge and extend those existing tools. The metalanguage (loop, branch, increment, multiply, source oracle) is supplied by the researcher.

## Feedback-driven substantive rewrite

The development corpus comprises 24 independently seeded tasks: 12 degree-3 Boolean polynomials and 12 period-3 symbolic processes. Using the same source-only meta-learning procedure, the system selects the AST with:

- Complexity update: \`k ← k+2\`
- Independent source challenges per attempt: \`16\`
- Continue after source refutation; abstain on absent evidence.

The distinct 15-task feedback corpus comprises Boolean degree-4 or degree-5 problems. The frozen initial policy is demonstrably falsified there. Including this *meta-development evidence* and re-running the general program search selects:

- Complexity update: \`k ← k+1\`
- Independent source challenges per attempt: \`64\`
- Same general verification and fail-closed semantics.

**This changes both a method's search trajectory and its challenge policy**, not a memorized target solution or an ARC task-specific primitive.

The procedure is recursive and can continue to complexity 9, beyond the maximum examples in the initial source-development corpus. All source probes are logged and cached, and target evaluation inputs are excluded from source oracle access.

## Local source-disjoint development evaluation (NOT final blind verification)

Training/feedback IDs are disjoint from 100 post-revision test IDs. New tests: 40 Boolean functions with degrees 4/5 and 10 bits; 20 functions with 11/12 bits, same degrees; 40 binary periodic processes with periods 7/9.

| Method | Correct new tasks |
| --- | ---: |
| Initial learned meta AST (\`+2, 16 checks\`) | **84/100** |
| Revised learned meta AST (\`+1, 64 checks\`) | **100/100** |
| Fixed depth-3 comparator (\`+1, 64 checks\`) | **0/100** |
| Strong class-specific classical methods | **100/100** |

After the learned method is frozen, the scorer also verifies **all 102,400** finite Boolean input cases and **108,000** more distant symbolic-process indices. These match the reference functions, but are researcher-defined synthetic problems. Exact scores will be independently rerun by GitHub Actions.

**Honest Q4 result on the local development cohort (measured, no hardware-normalized power accounting):**

- Current 100-task source discovery: **49,411** unique source queries under revised meta policy, versus **58,740** queries for strong class-specific classical reference. This apparent inference-level saving does not establish full economy.
- The conservative, gross **initial meta-learning + feedback diagnosis + retraining + feedback re-check + 100-task inference** charge is **97,440** source and meta-training grade queries. This is **more**, not less, than strong classical's **58,740** test-task source queries. Earlier speculative research costs are additional.
- On a local Python CPU measurement, the end-to-end revised meta development+test path was about **8.6 seconds** and the strong classical reference's 100-task inference was about **2.5 seconds** (Estimate from one local run; no confidence interval). Therefore **full Q4 FAIL**.

The fixed-depth-3 comparator is a weak capacity baseline for out-of-class tasks; it must NEVER be the sole baseline. The source oracle has strictly enforced target-query exclusion; meta-training labels are exposed during meta training but all their acquisitions are separately charged.

## Independent second first-cohort audit

A separate SHA-frozen \`research/q3/q3_recursive_method_second_first.py\` experiment reserves another **150 NEW** researcher-created tasks, selected by fixed non-overlapping seed schedules and input widths. It first serializes learned-program predictions for all finite Boolean inputs and distant symbolic time indices, commits their SHA-256, and **only then** executes an independent scorer which opens target-reference functions.

The definitive second-cohort result comes from the corresponding GitHub Actions workflow artifacts, not predictions about what the score should be. If it fails, retain the FAIL and analyze it; do not quietly alter the selected policy or scoring tasks.

## Research question status

- **Q3, method-level invention:** Bounded proof of autonomous procedure AST search and failure-based procedural revision (new *procedure*, not merely a target program). Stronger than only selecting one task-specific prewritten solver. **Scoped PASS** only after re-running CI.
- **Q6, cross-semantic transfer:** Same frozen meta control program across Boolean polynomial structures and periodic symbolic processes with different classical backends. Larger degree, period and input widths absent from initial training. **Scoped PASS** on verified cohorts, not universal ontology-independent learning.
- **Q4:** Efficient source queries may be visible at inference level, but learning+validation+execution gross CPU and query cost remains worse than strong classical reference. **FAIL against strong-classical total-cost target**.

No finite-data solver can promise the correct arbitrary unseen function: one unseen exception can agree with all observed source facts. Even exact GF(2) rank identification proves a unique law only within the assumed bounded degree class. A policy learned from finite trajectories cannot guarantee universal procedural invention.

## Real implementation

- \`neumann1/recursive_method_discovery.py\`: one bounded typed domain-agnostic meta-program compiler/interpreter/learner
- \`neumann1/engine.py\` and \`neumann1/registry_engine.py\`: production meta method learn, revise and classical-first execute APIs
- \`research/q3/meta_domain_adapters.py\`: two pre-existing mathematical backends used ONLY to test the same interpreter
- \`research/q3/q3_recursive_method_meta_first.py\`: first source-development corpus and full Q4 cost audit
- \`research/q3/q3_recursive_method_second_first.py\`: cryptographically frozen independent second-cohort predictions then separate scoring
- \`tests/test_recursive_method_discovery.py\`: fail-closed, source-only, cross-semantic and live engine evidence
- \`.github/workflows/q3_recursive_meta_cross_domain.yml\`
- \`.github/workflows/q3_recursive_meta_second_first.yml\`

Most important remaining frontier: **inventing general-purpose new discovery primitives and search representations, not merely re-synthesizing control flow over known classical algorithms**, with strong new-author tasks, independent source-only verification and complete cost accounting.
