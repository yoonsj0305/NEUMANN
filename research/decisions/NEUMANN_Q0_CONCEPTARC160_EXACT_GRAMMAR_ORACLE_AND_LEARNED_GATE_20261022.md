# NEUMANN 1 | Q0/Q3 Exact ConceptARC Oracle and Controller Stop Gate | 2026-10-22

## Decision: fixed-grammar neural reranking MUST NOT be next mainline

The research North Star remains **frontier-level problem solving with minimum necessary total computation**. The previously frozen typed source-only AST solved 6/160 actual independent-source ConceptARC tasks versus 1/160 for the prior symbolic baseline, but 0/120 on previously tested ARC-AGI-2 public evaluation. No neural learning was used. Paired item-level McNemar two-sided p=0.0625, and five new task wins are restricted to 2/16 concept categories.

A NEW fully independent, end-to-end original ConceptARC audit of the SAME SOURCE-FROZEN model has been executed at [GitHub Actions #39757419441](https://github.com/yoonsj0305/NEUMANN/actions/runs/39757419441) and linked [PR #469](https://github.com/yoonsj0305/NEUMANN/pull/469). Previous [PR #468](https://github.com/yoonsj0305/NEUMANN/pull/468) supplied the untouched-first-exposure original 160 study. This new audit is **POSTHOC** and does not claim a new blind cohort.

Original source IDs: `victorvikram/ConceptARC@0e67da6af879e4bad3d7cd3c196e8d551b445725`; original `corpus` Git tree `a9e933c021388297f21fa1cded180105479addc0`; 16 concept categories × 10 original tasks × 3 original test grids = 160 tasks / 480 grids. Exact same original previously registered grammar Git blob `a46dc5480f0819895effc48df1e0600a23640bdf`. Three isolated CI jobs: mask all original output labels; generate and freeze ALL demonstration-consistent AST predictions and their behavioral classes without labels; separately fetch originals and grade the entire finite candidate pool. Source SHA and first candidate artifact remain immutable.

### Observed full-cohort decomposition
- **143/160**: the frozen typed AST grammar has NO candidate fitting the source demonstrations.
- **17/160**: at least one AST exactly fits demonstrations, **415 raw ASTs** total across these source tasks.
- Of the 17, **2** have NO defined output on the original held-out test inputs even when the AST fits demonstrations: `Center__Center2`, `TopBottom2D__TopBottom2D5`. Source-runnable candidate count is 15.
- Only **5/160** have more than one distinct held-out prediction after collapsing all syntactic ASTs to behavioral equivalence classes. Lots of candidate programs alone do **not** mean that ranking is meaningful.
- **6/160** actual full-task exact from MDL source-only ranking, **7/160** exact FINITE-GRAMMAR oracle (all possible demo-consistent ASTs with oracle choosing the correct test prediction AFTER grading). Therefore within this unchanged grammar, **at most +1/160 extra can be achieved by any learned/rule-based reranker**.
- Sole oracle-selectable but current MDL missed: `TopBottom2D__TopBottom2D6`, 28 source-fitting ASTs partitioning into 14 distinct test prediction classes. This is hindsight **NOT** a discovered learned new solution.
- Existing source-only majority vote among behavioral classes obtains **5/160**, worse than MDL's 6/160. No guarantee that simple voting improves correctness.
- The six already-solved original IDs are `Copy__Copy1`, `ExtractObjects__ExtractObjects1`, `ExtractObjects__ExtractObjects9`, `TopBottom2D__TopBottom2D1`, `TopBottom2D__TopBottom2D2`, `TopBottom2D__TopBottom2D7`.
- **6 singleton-prediction cases** have one behavioral class but the UNIQUE candidate answer is wrong, illustrating that agreement/uniqueness within a narrow grammar does not imply truth.

### Mathematically exact result

Let `H(x)` be the frozen finite set of typed AST programs consistent with every source demonstration and defined on all tests. Any selector (a 5B learned language model, a trained smaller model, MDL, oracle, or a classical prior) restricted to outputting a member of `H(x)` is correct only if at least one program in `H(x)` emits the actual hidden test output. Postgrade exhaustive original source enumeration proves only 7/160 such tasks. Hence **conditional on the FIXED source program grammar and no bypassed test-output generator**, even a perfect neural ranker has `accuracy <= 7/160 = 4.375%` on these exact tasks. Existing 6/160 = 3.75%. Incremental accuracy ceiling for ANY reranking-only intervention **+0.625 percentage points**. This mathematical bound does NOT constrain a neural network or other method able to GENERATE previously inexpressible programs, direct-answer models, or other task sets.

### Engineering consequence

**Reject and save training compute** for reranking frozen ASTs as mainline work. Do NOT keep adding optimization rounds to unchanged finite grammar. Next high-information experiment must produce source-conditioned **new typed operators/program structures** absent from the current grammar, ideally using a learned proposer but maintaining fair stronger independent exact classical grammar-inventor controls, no-label genuine first-blind independent new task corpora and FULL train+inference+verification cost. To reach 50% exact on this *same posthoc cohort* even with perfect reranking, an expanded representation must cover at least **73** more tasks (80 target - 7 current finite oracle). This is a conditional coverage target, NOT projected expected gain.

**Scientific admission:** scoped source-only AST structural ability has new validated cases (5 over previous baseline), fixed-grammar representation insufficiency is demonstrated, Q0/Q3 unique learned operator generation is STILL OPEN, Q4 complete 10x and frontier-parity remain OPEN. We do not claim a new general theorem priority, zero global dataset contamination, training-driven intelligence, or a big-tech-beating model. Original PR #469 unmerged, historical unrelated repository CI red is not an authority on this dedicated 3-job SUCCESS.
