# NEUMANN 1 | P1.6 exact semantic quotient versus strong syntactic-prefix caching

**PRE-REGISTRATION, 2026-11-05 KST, before source task fetch and first scoring.** Frozen North Star: **Frontier-level problem solving with minimum necessary computation**. Global Q1–Q7 **OPEN**, P1.5 first failure immutable.

## Hypothesis: delete redundant computation, not discover a weak ranking proxy

The LeCun/Balestriero preprint (arXiv:2610.39302) proves a conditional representation-alignment theorem for good views of the same scene. Alignment scores and its reported 42× sample ratio are **not** executable program discovery or total inference cost. Before a learned JEPA is introduced, establish an *exact* classical semantic-equivalence baseline.

Let X be the union of **original ARC training INPUTS and test INPUTS only**. Two executable prefix programs p, q are observationally equivalent on X iff `p(x) = q(x)` as exact same-shaped, same-colored grids for every x∈X. Here p,q are deterministic grid-to-grid programs from a frozen common typed DSL (P1.1 `GRIDOPS`, 23 operators, length≤3). If `p∼_X q`, then for every deterministic well-typed suffix h, `h∘p∼_X h∘q`. Thus a representative per semantic class suffices to enumerate **all possible original-task training/test input behaviors** in this bounded grammar. A formal induction is included in the decision document.

Crucial: *test inputs are permitted*, **test outputs are not**. Grouping only on training inputs risks changing test predictions and could falsely inflate performance. Grouping across test inputs is **not** a proof of generality on future unknown inputs.

## Frozen arms and fairness

- **P (strong cached prefix enumeration)**: deterministic BFS of all valid programs length 1..3, starting from identity, reusing each syntactic prefix once and never recomputing a prefix from scratch. Prune only obviously invalid/nonrecoverable intermediate grids. No neural encoder. This is a stronger comparator than naive rerunning every full program.
- **Q (exact observational semantic quotient)**: same BFS, exactly same operators and maximum depth and original inputs, but memoize one representative for each state signature `[p(x) for x∈X]` with full exact JSON (not lossy hash), across all depths. Skip generating suffixes for previously seen equivalent prefixes. Also prune nonrecoverable invalid intermediate grids. Include signature, mapping/overhead costs in wall time.
- For both arms, fit programs using *all* original training input/output pairs exactly, including output grid dimensions. For each candidate, record every distinct test-prediction tuple from fitting programs. Return **ABSTAIN** when zero fit or contradictory test predictions. A program error is ABSTAIN/invalid, not output.
- Score all original test grids only after both arms propose complete predictions. On the **same task**, P and Q must return identical prediction or both ABSTAIN: any disagreement is a **correctness failure**, even if the original output happens to match one.

## Cohort / first-time source boundary

Pinned `fchollet/ARC-AGI` public ARC-AGI-1 **training** directory at commit `399030444e0ab0cc8b4e199870fb20b863846f34`. Exclude earlier cohorts P1.0 32, P1.1 24, P1.2 24, P1.3 4, P1.4 24, P1.5 32 and the four explicitly inspected P0.3 development IDs: **144 distinct** (verify no overlap). Choose 24 new filenames by unsigned FNV1a32 of `neumann-q3-p16-20261105|` + basename, ascending tie filename. Freeze exact ID list, P1.1 operation blob and the P1.6 engine blob SHA **before task-body fetch**. No revising after results.

## First-run gates

1. **Semantic-preservation gate**: P and Q predictions exactly identical (including reason ABSTAIN vs proposed grid) for **24/24** original tasks. Zero original test correctness losses. Any divergence FAIL and stop.
2. **Cost mechanism gate**: at least **10× fewer actual `applyGrid` evaluations** in Q versus strong P over the 24 tasks, and aggregate *in-tool study-region wall clock* Q strictly less than P (including overhead). Otherwise not a 10× signal, even when equivalence holds.
3. Report per-task wall-ms using `Date.now()` (coarse), operator evaluations, number of unique semantic classes, explored syntactic prefix count, train-fit count, original-task correct task count, abstentions, and any possible false positives. Report median and total ratios. No favorable task exclusion or post-hoc threshold retuning.

## Degraded mode, limitations, relationship to JEPA

No learned model, no JEPA training, no learned new operator, no new Q3 autonomy. Exact quotient may save substantial deterministic search by deleting behaviorally duplicate subtrees. If effective, it becomes the **required strong non-neural baseline**: a trained view encoder is only justified if it increases verified original-task capability or wins full-system compute/memory/latency/energy/cost at equal accuracy, even after accounting for embedding training, lookup and verification. Any approximate embedding may only *rank* candidate states, never silently merge inequivalent operators without proof.

Measure total program-node execution region, not electricity, GPU utilization or dollar costs. FLOPs/energy/peak RSS/model inference cost **UNKNOWN** if not directly measured. The 10× operation count is not a 10× full-system or frontier claim. P1.6 first result remains OPEN or PASS/FAIL strictly based on evidence, while global Q1–Q7 remain OPEN.
