# NEUMANN 1 | Invention core: structural bottlenecks, one mechanism to test next, edge-cost analysis
2026-11-11 | Static analysis and design ONLY, written while the frozen TARGET FIRST run is in progress | Global Q1–Q7 OPEN

Scope and integrity. Nothing here was executed against TARGET data. The frozen code
(`neumann1/invention_core.py`, `research/q3/invention_first.py`, `research/q3/sequence_specialist.py`),
the arm order, budgets, the frozen core and the result file are untouched. The only TARGET facts used are the two
log lines already printed by the running harness (rule A 25/125 in 70 s, rule A4 34/125 in 312 s) and the
observation that rule B has been running for > 45 min at the same 200 k budget. SOURCE facts come from
`docs/experiments/results/invention_core_frozen.json`. Nothing below is implemented; nothing below is a result.
The mechanism proposed in §2 is NOT new in the literature (see "prior art") and is NOT present in this repository
today (searched: no witness-function / sub-specification / failure-driven invention code exists).

## 1. Fundamental bottlenecks of the current invention core

### B1. Invention is closed: it can only re-encode what the system has already solved (most fundamental)

Code evidence:

* `train()` (l.1159–1163) admits a program into the learning corpus only if `x["fit"] and x["solved"]`. A failed
  task contributes **zero** bits to learning. Failures, partial fits and counterexamples are discarded.
* `propose()`/`_au()` (l.787–919) anti-unify **syntax trees of those solved programs**; `compress()` (l.922–968)
  adopts a pattern only if it occurs syntactically in ≥ 2 solved programs (`min_tasks=2`) and the rewrite is
  semantics-preserving (re-verified, l.949–957). Two tasks whose solutions are semantically related but
  syntactically different never produce an abstraction.
* Every invention is definitionally expandable into the substrate (`inline()` l.466, `expand()` l.430); the
  memory is even stored inlined (l.1185). So inventions never enlarge the hypothesis space H; they change only the
  **order** in which H is enumerated (shorter description ⇒ reached earlier under the candidate budget).

Consequence. The capability that C can add over A is bounded by "compositions of fragments of programs A-like
search already found on SOURCE". SOURCE wake found 33 → 43 → 45 of 312 usable tasks over three rounds
(frozen history), i.e. the learning signal saturates at the reach of the search itself. The development log in
the pre-registration already showed the symptom: from a fold-only substrate the core invented `map` but could
never bootstrap `filter` within 12 M candidates, because no solved program contained a filter-like pattern to
compress. This is the precise sense in which the current core is **re-encoding, not invention**: an abstraction
can only name a pattern that was already reached.

Two different things must not be conflated:

| | changes reachable set at a fixed budget | changes the expressible set in the limit |
|---|---|---|
| current inventions (syntactic compression) | yes, but only toward already-found patterns | **no** |
| failure-driven specification abstraction (§2) | yes, toward patterns NOT yet found | no |
| representation invention (new types / state) | yes | **yes** — not addressed by anything here |

Representation ceiling (also B1, code evidence): types are fixed to `{I, B, L}` (l.33, `_Ctx.done` l.512);
fold accumulators are a single I or L (l.346–358); binder depth `max_nb=2` (l.545); `LEN_CAP=40`. Programs that
need two pieces of state (e.g. running max *and* its index), nested lists, pairs, strings or grids are not
expressible at all; such tasks are registered as `unsupported` and fail in every arm. Memory primitives are only
built for unary tasks (`memory_prims` l.1050), so multi-input tasks get no memory benefit. No mechanism in the
core can create a type, a data structure or a recursion scheme; those are human given.

### B2. Hypothesis selection = "first minimum-cost program consistent with TRAIN"

Code evidence:

* `_keep()` (l.737–744) raises `Found` at the first top-level entry whose TRAIN vector equals the target; there
  is no second candidate, no held-out check, no counterexample loop.
* Observational equivalence merges programs by their **TRAIN** vectors only (`ctx.seen` l.738–741); among
  programs that agree on TRAIN but differ off-TRAIN, the cheapest is kept unconditionally, so the choice among
  generalizations is decided by the prior alone.
* The prior is a context-free per-type unigram rounded to integer bits (`learn_costs` l.986–1005). It cannot
  encode structural regularities ("filter bodies are comparisons with a bound variable"), so it is a weak
  selector exactly where selection matters.

Consequence. On ConceptARC the same failure class showed TRAIN-fit precision of 6 %. Here the harness records
`fit` and `solved` per arm, so precision is measurable when the run ends; nothing is claimed before then.

### B3. The budget unit (candidates) is blind to execution cost, and the memory arms pay for it

See §4 (this is the edge-cost bottleneck). Short form: a retrieved memory program is priced like a primitive
(`$mem = 3`, l.1097/1142) but executes an entire inlined program per call; at the same 200 k candidate budget A
took 70 s of wall time and B has taken > 45 min, a > 40× wall ratio.

## 2. The one mechanism worth testing next: failure-derived specification abstraction (FDSA)

Target bottleneck: B1 (and, as a side effect, B2).

Idea. Learn abstractions from **what failed tasks needed**, defined first by behaviour (an input/output
specification) and only afterwards given an implementation — instead of from the syntax of what succeeded.

1. **Sub-specification by inverse semantics (generic, derived from substrate semantics).** For a failed SOURCE
   task, push the output examples backwards through each substrate primitive whose inverse is finite on the
   observed values: `map f xs = ys` with `len xs = len ys` ⇒ element pairs `(x_i, y_i)` for `f`;
   `filter p xs = ys` ⇒ labelled examples for `p` when `ys` is a subsequence of `xs`; `cons h t = ys` ⇒
   `h = head ys`, `t = tail ys`; `foldr/foldl` with a list accumulator ⇒ per-step pairs when the output is a
   prefix-closed construction. The inverse rules are not hand-written per task; they are obtained mechanically
   by evaluating each primitive on finite observed domains (so the only human input remains the substrate
   semantics). The result is a set of **candidate sub-specifications** (typed partial functions).
2. **Cross-task concept formation.** Normalise each sub-specification to a behavioural table and merge tables
   from *different* failed tasks when they are type-compatible and agree on every shared input. A table supported
   by ≥ 2 tasks becomes a *pending concept*: a named function whose meaning is the union of its observations.
3. **Implementation by search on the pooled specification.** In sleep, synthesise the smallest program
   consistent with the pooled table (the existing `Search`, unchanged), with a held-out subset of the pooled
   observations as a counterexample check. A counterexample splits or rejects the concept (no silent adoption).
4. **Adoption by the existing MDL rule**, then wake again: the concept is a callable primitive, its cost
   re-estimated from use.

Why this is essentially different from the current core.

* The learning signal comes from failures; abstractions can target patterns that **no solved program contains**
  (the `filter`-from-`fold` case above is the canonical test).
* Decomposition changes search cost from roughly `b^(d1+d2)` for one program of depth `d1+d2` to
  `b^d1 + b^d2` for a concept and a caller — a structural saving, not more compute.
* Pooling observations across tasks gives each concept more examples than any single task has, which directly
  attacks B2 (fewer TRAIN-consistent but wrong generalisations).

Prior art (stated plainly): inverse semantics / witness functions (FlashMeta/PROSE, Polozov & Gulwani 2015;
λ², Feser et al. 2015), learning from failures in ILP (Popper, Cropper & Morel 2021), library learning
(DreamCoder, Stitch, LILO). The open question is not novelty but whether NEUMANN's single core turns failures
into transferable capability under a pre-registered, compute-matched test.

Failure modes and counterexamples (expected, to be measured not argued away):

* Non-invertible top structure: sums, products, sorting, folds with integer accumulators (`foldrI`) give
  infinite or exponential pre-images; FDSA produces no sub-specification. Many OEIS tasks are of this kind, so
  FDSA may help lists and do nothing for sequences.
* Ambiguous decompositions: one output admits many `(f, xs)` splits; the concept pool can explode. A hard cap on
  sub-specifications per task is a design choice that can bias results.
* False merges: two tasks agree on shared inputs but mean different functions; the counterexample check catches
  this only when held-out observations overlap the disagreement.
* Compute confound: FDSA spends extra sleep search. Without a control that gives the baseline the same total
  candidates, any gain may be compute, not mechanism.
* It does not touch the representation ceiling (B1, last row): a concept is still a program over `{I, B, L}`.
  If the TARGET failures are dominated by inexpressible tasks, FDSA must fail, and that failure would itself
  locate the next bottleneck (type / state invention).

## 3. Scope of the current BIG-bench / DreamCoder / OEIS evaluation (what it can and cannot show)

| Family | What a PASS shows | What it does NOT show |
|---|---|---|
| rule (BIG-bench c001–c250) | generalisation to unseen functions of the **same author and distribution** (SOURCE/TARGET are a hash split of one set) | transfer across sources or semantics |
| dc (DreamCoder list tasks) | **cross-source** transfer: different author, zero-shot, never used for learning | cross-semantic transfer — same list→list semantics, same substrate |
| oeis (A000 seqs) | that **one core** (one learned library + prior) also works on a second semantic family | zero-shot cross-semantic transfer: the core was trained on 250 OEIS SOURCE tasks (11 of the 45 learned programs are OEIS, frozen core); the per-signature prior `I>I` was learned from them |

Therefore "Q6b cross-semantic, one core" as registered is a **shared-core** test, not a **transfer** test. A
transfer test needs a core trained on one semantic family only and evaluated on another it never saw. All three
families also live inside one human-designed typed substrate, so none of them tests whether the core can discover
the right representation for a new domain (strings, grids, graphs, physical state).

## 4. Edge execution cost of memory calls in B and C (static analysis, no runs)

Why B and C cost more CPU per candidate than A:

1. **Price ≠ work.** `solve()` gives each of the k = 8 retrieved programs cost `$mem = 3` (l.1097), like a
   primitive, while its body is a whole inlined program (memory stored via `inline`, l.1185; SOURCE program sizes
   1–33 nodes, median 8, most containing folds/maps). The budget counter `self.n` (l.695) counts one unit per
   candidate regardless of work, so B and C fill the same budget with far more expensive candidates. 34/45
   memory programs are `L→L`, so they apply to every list-typed entry in every context.
2. **No reuse across candidates.** In value mode (l.710–723) every candidate re-runs `vp(args)` per example even
   when the same argument value was already processed by an earlier candidate. Observational equivalence dedups
   whole vectors, not individual values, so the same list (the input, its tail, its reverse, …) is fed to the same
   memory program thousands of times.
3. **Inside lambdas the cost multiplies.** In binder sub-contexts the envs are probe envs, `nprobe = 32 //
   len(examples)` (l.557) per example, i.e. ~32 envs; a memory call inside a `map`/`filter` body runs once per
   element per probe env.
4. **Higher-order path re-executes known children.** For fold/map/filter and higher-order inventions
   (l.724–732) `p.make([k.getfn() ...])` rebuilds closures and re-evaluates every child subtree on every env,
   including binder-free children (the list argument, the init value) whose value vector `k.vec` is already known.
5. **Allocation in the inner loop.** Templates allocate a fresh list of lambdas per call (l.303–305); every fold
   step builds `env + (x, acc)` and every hole application slices `env[:dcall] + ...` (l.284–293), so allocation
   grows with scope depth on every iteration. `Fail` exceptions are used for control flow per evaluation.
6. **Weaker pruning.** Memory outputs are diverse, so observational equivalence merges fewer entries; pools are
   larger and the budget is spent deeper in expensive compositions (this changes search order and is a design
   property, not removable waste).

Removable without changing any output (exact eliminations; same candidates in the same order, same `Found`):

| Elimination | Where | Why exact |
|---|---|---|
| per-primitive value memo `(prim, args) → result/Fail` | value mode l.711–723 (memory and first-order inventions) | all primitives are pure and deterministic; `Fail` is memoised too |
| binder-free children read from `k.vec[i]` (partial evaluation by env index) | higher-order path l.724–732 | the child's value at env i is already computed and env-independent of the binder |
| compile each abstraction / memory program once into a flat function (fixed-slot frames, or generated Python source via `compile()`), no per-call lambda lists, no tuple concatenation | l.271–305, l.158–212 | same semantics, different calling convention |
| hash-consed sub-expression cache keyed by (node identity, env index) inside binder contexts | l.724–732 | pure evaluation; an identical subtree on an identical env gives the identical value |

These must be validated exactly as `classical_grid_fast.fit_all` was: identical returned programs and
candidate counts on development tasks before adoption. Not exact (a design change, would need its own test):
charging execution work in the budget or raising `$mem` with program size — that changes search order and
therefore capability.

## 5. Minimal verification experiment after the current run ends (design, not run)

Question: does FDSA create abstractions that syntactic compression cannot, and do they produce TARGET capability
that the same core with the same total compute does not?

* SOURCE (learning only, already legitimately opened as SOURCE): the 125 rule SOURCE + 250 OEIS SOURCE tasks.
* TARGET (never opened): `oeis_reserved_unopened` — the 499 hash-ordered A000 sequences already registered by
  blob SHA-1 and not fetched. For lists no registered unopened pool remains after this run (rule TARGET and dc are
  opened by it, so they become development data); a new list source must be registered blobless only after a full
  commit **and** PR search proves it unused (the ConceptARC lesson).
* Arms, all from the same frozen code: **C** (current core, retrained identically), **C_FDSA** (C + FDSA in sleep),
  **C_matched** (C with its wake budget raised so its total SOURCE + TARGET candidates equal C_FDSA's), plus A and D
  (Berlekamp–Massey/differences) on sequences.
* Mechanism gate (decides whether FDSA did anything at all): ≥ 3 adopted concepts whose pattern occurs in **no**
  solved SOURCE program of C (provably unreachable by `compress`), each with a held-out-verified pooled spec.
* Capability gate: solved(C_FDSA) > solved(C_matched), exact McNemar p < 0.05, ≥ 5 C_FDSA-exclusive tasks of which
  ≥ 3 use a failure-derived concept; TRAIN-fit precision reported per arm.
* Pre-stated falsifiers: no failure-derived concept adopted ⇒ FDSA FAIL (B1 not addressed); concepts adopted but
  C_FDSA ≤ C_matched ⇒ the gain is compute; C_FDSA wins only on tasks D also solves ⇒ no gain over a classical
  specialist. Every outcome is kept.
* Wall-time precondition: implement the exact eliminations of §4 first and time every arm on a small development
  sample before freezing, so no arm's runtime is unknown at launch (the mistake made in the current run).

What the current run decides first. If C does not beat A and B on rule TARGET, B1 is confirmed as the binding
constraint and FDSA is the next step. If C does pass, FDSA is still the next step for Q3, because the current core
can only re-encode what it has reached. Either way the decision is taken only after the frozen verdict is written.
