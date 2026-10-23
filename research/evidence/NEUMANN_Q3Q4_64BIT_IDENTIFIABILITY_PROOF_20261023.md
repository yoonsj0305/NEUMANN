# NEUMANN 1 · Q3/Q4 reversible-CA identifiability and minimum-computation certificate

**Scope:** finite, fully specified *bijective* binary Margolus block CA on an even torus, up to 64 cells, within exactly the stated observed transition horizon. This is a classical algorithmic certificate, **not** proof of learned novelty, general unknown rules, universal world modelling, or frontier parity.

## Theorem 1: exact inverse of a known reversible block transition

Let each time step partition all cells into non-overlapping (2\times2) blocks, shifting the partition with time parity. The rule (p:\{0,\ldots,15\}\to\{0,\ldots,15\}\) is a *given bijection*. Therefore each whole-board step (F_t) is itself a bijection because it is a Cartesian product of disjoint copies of (p). Its inverse is a Cartesian product of the inverse rule (p^{-1}) acting on the **same partition at step (t)**. The composition (F_{0:T}=F_{T-1}\circ\cdots\circ F_0) is also bijective, with inverse (F_0^{-1}\circ\cdots\circ F_{T-1}^{-1}).

**Test evidence:** 300 pseudorandom native-forward versus vector-backward one-step state/rule/parity cases (4×4, 6×6, 8×8) PASS. **Limits:** this theorem does not apply when the transition is lossy, the supplied permutation is not bijective, or the geometric partition differs.

## Theorem 2: exhaustive source-conditioned identifiability when terminal unknown count is small

There are (N=H\cdot W) cells and an observation at time (T) fixes (N-m) distinct terminal cell values. Enumerate **all** (2^m) assignments to the remaining (m) cells. For every candidate, reverse exactly (T) transitions as in Theorem 1 and reject it whenever any other time-indexed observed cell disagrees.

This enumerates **every** possible full forward history compatible with the observed terminal cells: any possible original state must evolve into exactly one enumerated terminal completion, and its unique inverse history will be evaluated. Filtering other observations only removes incompatible histories.

- **Zero survivors:** no compatible initial state exists, if all source observations are trusted and model correct.
- **One survivor:** unique initial state, and the independent native forward simulator replays every observation.
- **Two or more survivors:** select two different full initial states and replay both independently. Both explain all observations; no single initial-state answer is *identifiable* from this evidence. This is a constructive proof of **non-uniqueness**, not solver indecision.
- This implementation restricts enumeration to (m\le10\), (N\le64\) and uses exact Python-int bitfield generation before converting to `uint64` (a prior high-bit NumPy issue was actually found and corrected). This is (O(2^m\cdot T\cdot N)) rather than (O(2^N)) in this special observable-terminal regime. No claim that unobservable 64-bit worlds are cheaply enumerable.

## Theorem 3: two-witness certificates outside exhaustive enumeration

When (m>10), a deterministic bounded search of terminal completions may find two **distinct** initial configurations satisfying every observed source cell by independently verified whole-history forward simulation. That pair is sufficient to prove that unique identification is impossible even though the search is incomplete. Failure to find a pair **does not** prove uniqueness or no-solution and must fall back to a sound exact solver or UNKNOWN.

If every time-zero cell is directly observed and consistent with all later observations, the uniquely specified initial configuration is a complete no-search certificate. Original strong `propagation+SAT` remains the fallback for cases not admitted to these specialized exact source proofs; timeout is never renamed nonuniqueness.

## Original three-cohort evidence (do not pool as independent original external problems)

| Research run | 6×6/8×8 source tasks (self-generated, 160 per seed) | Exact initial-state solves | Concrete nonunique two-witness proofs | Incorrect predictions | Measured source CPU ratio to strong SAT |
| --- | ---: | ---: | ---: | ---: | ---: |
| [PR #516 / Actions 39876590152](https://github.com/yoonsj0305/NEUMANN/actions/runs/39876590152) | 160 | 138 | 20 status-level reports; no independently archived full witness-grid pairs in that earlier runner | 0 | 16.3208× |
| [PR #517 / Actions 39877074604](https://github.com/yoonsj0305/NEUMANN/actions/runs/39877074604), exact source blobs frozen, new seed | 160 | 136 | 20 status-level reports; no independently archived full witness-grid pairs in that earlier runner | 0 | 14.4577× |
| **[PR #518 / Actions 39878324609](https://github.com/yoonsj0305/NEUMANN/actions/runs/39878324609), NEW seed, full witness archive** | **160** | **135** | **25 individually replayed two-initial-state pairs (25/25 independent grader PASS)** | **0** | **16.0877×** |

**Caution:** first/second research run's generated source statuses were not audited by this third seed's independent two-witness receipt. Do not claim those earlier cohorts all closed by externally preserved witnesses. The third-seed only is **160/160 fully classified as exactly identified or independently shown nonidentifiable**. Third-seed source-only JSON SHA256 `293ce2188f9d377b25dca7b5a192a94fb1ec55b7c1f3798e3186c4a89a751d28`; independent graded receipt SHA256 `ecd400ba42391366433a8e91c02b36a3e1e66a7d5f0b8243681f5ccad21b38fe`. Originating true initial configurations were withheld in a physically separate CI artifact until the final job; witness pairs were recorded before that truth was read. All 160 generated examples admitted without post-hoc dropping failures. Source solver uses only the *given* published CA rule and partial observations.

Third seed proof stratification: exactly 20 intentionally severely underdetermined source problems (10 6×6 +10 8×8) yielded constructive nonunique pairs, plus **five naturally nonidentifiable** partially observed dense-terminal tasks (two 6×6 and three 8×8); every witness was independently native-forward verified. Among positive cases, dense 6×6 58/60, dense 8×8 57/60, direct fully known t0 20/20.

### External original 300 public benchmark repeated equivalence control

Previously first-scored independent-author AutomataBench public evaluation in [PR #514](https://github.com/yoonsj0305/NEUMANN/pull/514) was 300/300 exact and uniquely determined. This run **reuses that same published original evaluation**, not first-blind. Under identical whole-run 3× alternating CPU measurements, the third-seed code again yielded **300/300**, no extra errors, 17.923069427s strong SAT versus 0.6982327799999979s adaptive solver = **25.6692×** *source inference CPU*, not whole-system training+inference+verification energy. Source prior original evaluation data and verifier are pinned at `neelsomani/automata-bench@7d86373fdb63fe1bd3592ddf71d923ceebc5acd9`.

### Admission decision

- **Q3 scoped PASS:** complete identification vs observed non-identification on ONE new *programmatically generated* 160-case 6×6/8×8 cohort with 135 unique state reconstructions +25 concretely proven nonunique histories. Fails closed only when no source proof.
- **Q4 scoped PASS:** same cohort original strong SAT solution accuracy, **16.09×** CPU speedup repeated; two earlier seed experiments **16.32×/14.46×**. External author's published 4×4 original300 still **25.67×**.
- **Global Q3 OPEN:** neural-only novel hidden rule family discovery, unsupplied dynamics, outside manually designed grammar, cross-author generalization of *the algorithm without adaptation*.
- **Global Q4 OPEN:** minimum necessary compute over complete NEUMANN train/model/controller/verifier pipeline; 10× general unbounded problem families and GPU energy not measured.
- **Frontier benchmark parity OPEN:** no claim of ARC-AGI-2 scores beyond archived unrelated results.

Every numerical scientific claim above refers to actual source-only / independent grader GitHub Action logs; GitHub CI green on a scientific workflow means the *measurement process completed*, not an unbounded scientific achievement.
