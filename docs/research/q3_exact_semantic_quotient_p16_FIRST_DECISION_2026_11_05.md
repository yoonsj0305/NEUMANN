# NEUMANN 1 · P1.6 exact semantic quotient: first result and theorem
Date: 2026-11-05 KST. Authority: `docs/research/frozen_north_star.md`.

## First original-task result, frozen before task-body fetch

Source `fchollet/ARC-AGI`, public ARC-AGI-1 training at pinned SHA `399030444e0ab0cc8b4e199870fb20b863846f34`; 24 new filename-hash selected tasks, excluding 144 previously studied public task IDs. Frozen engine `experiments/q3_exact_semantic_quotient_p16.mjs` and P1.1 primitive interpreter, all 24 original outputs scored only after both programs built predictions. Four first-result shards and first full receipt retained.

| Frozen arm | Original tasks solved | Actual `applyGrid` invocations | Study-region wall clock |
|---|---:|---:|---:|
| P: **strong syntactic-prefix-cached** breadth-first enumeration | 1/24 | 398,236 | 18,326 ms |
| Q: exact execution-behavior quotient, BFS of unique observed semantic states | 1/24 | 110,072 | 5,956 ms |

- **24/24** predictions or ABSTAIN status exactly identical between P/Q, **no** original task correctness loss and no falsely accepted output.
- **3.617959×** operator invocation reduction, **3.076897×** study-region elapsed-time reduction. Included exact signature generation overhead in Q. Median per-task operation ratio **3.657666×**. On two particular cases the individual operation ratios exceeded 10× but **the 24-task preregistered total did not**, so the **10× local gate is FAIL**.
- Q pruned **3,035** equivalent successor subtrees in the actual 24-case study.
- The sole original task solved by both was `74dd1130`. This is same limited 23-primitive length≤3 language; Q is strictly a **compute-elimination** improvement, *not* new original-task capability and *not* discovery of new executable semantics.
- Study timings use coarse JS `Date.now()` in one execution isolate, omit GitHub remote transfer and whole-system initialization; FLOPs, GPU use, energy, peak memory, dollars UNKNOWN.
- Unit contracts: five program-test suites PASS in an independently executed JS test harness (including 16-seed randomized parity loop, train-only-equivalence counterexample, invalid-input abstain and suffix equivalence). No neural JEPA or GPT-6 teacher calls.

## Soundness lemma (valid only on observed inputs)

Let `X={x_1,…,x_n}` comprise all original training **inputs** and *test inputs*, **never test outputs**. All primitive operators in the frozen DSL are deterministic partial maps `f:Grid → Grid∪{ABSTAIN}`, and ABSTAIN is absorbing. Define observational equivalence

`p ≡_X q iff for every x∈X, p(x)=q(x)`.

For any deterministic suffix `h` from the same typed DSL, `p ≡_X q ⇒ h∘p ≡_X h∘q`, because equal intermediate values passed to a deterministic function yield equal outputs. Induct on suffix length. Under bounded maximum depth D, BFS exploring only one representative of each equivalence class at its first occurrence (minimum depth) visits every *distinct* reachable output tuple for X of programs length≤D, because every skipped longer prefix has a shorter/equal equivalent representative whose remaining budget is at least as large. Thus P and Q have exactly the same set of possible training output matches and test-input predictions and preserve original task decision/ABSTAIN on X.

**Important limits:** This theorem does not assert equivalence for unobserved future inputs, learned world models, non-deterministic tools, hidden side effects or programs that may later recover from invalid values. The interpreter must enforce those premises. A representation that aligns two programs only approximately or on TRAIN inputs alone cannot be substituted into the quotient without potentially losing valid distinct TEST behavior.

## Critical applicability to the 2026 JEPA paper

Randall Balestriero and Yann LeCun, *Proving and Improving the Platonic Representation Hypothesis with JEPAs* (arXiv:2610.39302, October 2026), prove a conditional latent representation alignment theorem for *good paired views* of a shared scene. Their reported **42× fewer samples** to achieve a target alignment score refers **only** to that representation metric, not to executable program search, inference cost, or NEUMANN Q3. The quotient above is a task-specific exact behavioral equivalence baseline, not their neural JEPA theory.

NEUMANN should use pair-of-executions / multi-view operator semantics as an optional proposal-learning signal only **after** testing whether it recovers additional independently verified original tasks or beats **this exact quotient** at iso-capability including fitting, model calls, verification, caching and amortized training. A learned embedding must not be allowed to merge states that can lead to different original-task answers. If only alignment R@1 improves but original-task solution coverage/cost does not, discard the neural component.

## Decision
- **Q1 narrow mechanism: evidenced** (3.62× fewer operator invocations; 3.08× faster observed study region at identical decisions).
- **Preregistered P1.6 10× gate: FAIL**; no 10× complete system advantage.
- **Q2 narrow equality: evidenced** (24/24 observed task prediction parity, plus soundness argument under stated interpreter assumptions).
- **Global Q1–Q7: ALL OPEN**. No fresh-semantic-family generalization, frontier capability, learned discoverer or full-cost accounting.
- Keep this as an optional audited classical subroutine. Stop expanding a fixed DSL just to raise its local recall on already scored tasks. Next effort must be *new operator proposal learning* on fresh program families with strong exact classical baseline, original-task independent checker, and hard nonleakage constraints.
