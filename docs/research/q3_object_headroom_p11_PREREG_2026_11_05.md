# NEUMANN 1 · P1.1 object-structure headroom audit · preregistration
Date: 2026-11-05 KST. **Frozen before new task bodies are read or scored.**

Authority is the established frozen North Star: **Frontier-level problem solving with minimum necessary computation**; Q1–Q7 OPEN. P1.0 0/32 failure stays immutable.

## Hypothesis / controls
A: bounded, typed **classical grid program synthesizer**, including geometric operations, recoloring learned from train pairs, cropping, scaling, tiling and depth-two compositions. This is a materially stronger baseline than P0.3.

B: **A with an explicit object-structure vocabulary** (connected same-color components, areas, bounding boxes, position order; selective extraction, mask, erase, rectangle rendering, bounded compositions). The A part of B uses the same order, train examples, checker, candidate budget and execution interpreter. Both A and B are entirely classical. No JEPA or neural training. Any B advantage tests *representational headroom*, **not learning to invent new primitives** or neural intelligence.

Rule selection: exact original-task train consistency required across all examples. Program must predict all original test inputs. If zero programs agree on train, a program throws, or fitting programs disagree on predictions, **ABSTAIN**. Forbid access to test output from enumerator, including candidate order, termination or fitting. Score only after all proposals. Exact means full grid, all cells, dimensions, all test cases. Entire dataset must be scored, no best-subset scoring.

Candidate budget: maximum 500 attempted program ASTs per arm per task (A may have fewer if its fixed inventory exhausts); all attempts including invalid grid shape and runtime exceptions counted. Per-task CPU measured study region; cumulative CPU monotonic wall-clock time, peak RSS/energy not measured if unavailable. No cost reduction claim unless same original-task capability and all costs accounted. B's extra operations may consume more time; report this openly. If A's number of candidates is less than B, do **not** call it an equal-search-space experiment, only equal upper ceiling. Include a raw A-in-B ablation consistency check.

## New public cohort and contamination boundary
Choose *from filenames only* in the official `fchollet/ARC-AGI` public **training** directory at fixed upstream commit `399030444e0ab0cc8b4e199870fb20b863846f34`. Exclude exactly 32 prior P1.0 selected IDs and four pre-inspected P0.3/P0.4 IDs. Rank remaining by unsigned FNV-1a32 of `neumann-q3-p11-20261105|` + filename, ascending tie by basename. Select first **24** IDs. Commit the exact cohort before opening their bodies. Source examples and any public test outputs remain unseen to solver developers before code freeze.

No post-outcome changes to DSL, thresholds, ASTs, examples, seed, candidate ordering, or cohort can retroactively turn this first run into independent evidence. Any later revised experiment must get a new ID and new untouched corpus.

## Frozen decision
1. B additional exact successes >= 2 original tasks with independent scorer and no A lost tasks is a **local object-abstraction headroom signal**; weaker result is local FAIL/INCONCLUSIVE. It never closes Q3/Q4/Q5/Q6/Q7.
2. If B gains zero, STOP increasing an object heuristic library on this cohort. The bottleneck is more likely deeper representations/induction or object perception, and next work requires new source/family.
3. Whether B gains or not, calculate cost and verification call counts. This does not establish 10x complete computation or headroom over state-of-the-art Direct.
4. C (learned good views) is **NOT RUN**; only admit after verified B structural headroom and a separately preregistered study against strong Direct at iso-capability. If a deterministic abstraction explains all the gain, do not add a neural system merely for novelty.
5. Support degraded mode ABSTAIN and only independent authorized Direct fallback, logged separately. Do not call fallback successes B successes.

## Threats and provenance
Public ARC task bodies are accessible online and potentially present in pretrained model data. This is an **opened public, fresh-to-this-solver-development cohort** only, not truly private unseen problem-family transfer. A/B do not call external LLMs. Explicit architecture primitives remain human-coded: even B wins do not demonstrate autonomous opcode invention. P1.12, P2, sealed Decision 3 remain untouched.
