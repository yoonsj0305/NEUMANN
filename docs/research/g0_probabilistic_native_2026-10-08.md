# G0 A — opened native probabilistic diagnostic

**INCOMPLETE; NO REGISTERED FAMILY PASS; HOLD_LEARNING.** The first CPU execution
is complete as an attempted cohort, but failed/unsupported/timed-out routes
prevent a complete scientific cohort. No learned discovery, G1, G2 or Frontier
evaluation was performed. All historical verdicts and sealed data remain intact.

## Frozen question, sources and comparison rights

Can an exact free goal-preserving quotient leave tenfold discovery/execution
headroom against strong tested native methods, with equal reuse rights?
Before performance measurement, a cost-blind rule selected 13 public requests
from 9 QVBS families and 11 unique JANI files. Some source files are reused with
different parameters. Formats and repeats are not independent problems; these
are opened development requests, not 13 fresh independent evaluations.

Pinned [QVBS source](https://github.com/ahartmanns/qcomp/tree/c7324a311475ba1a3f40e36a324e32f91e766540/benchmarks/dtmc)
is commit `c7324a311475ba1a3f40e36a324e32f91e766540`, CC-BY4.0. Existing authors and
model metadata are preserved. Sparse exact/default and topological, rational
bisimulation, and symbolic DD-to-sparse paths were tested in Stormpy1.14.0.
Both original PRISM and JANI were allowed when supported; Coupon was JANI-only
because its original PGCL compiler was absent. This is a limitation, not an
equivalent full native coverage claim.

The free arm gets the quotient already built by Native, then actually solves
it. Native can reuse that SAME compiled quotient and also solves it again.
Neither arm reads an answer cache. Exact Fraction outputs are compared with
public parent-only exact references; the worker cannot read those references.
All initial values or the original maximum over them are retained. Trust is
the existing Storm implementation and exact checker, not a new independent
proof checker for arbitrary quotient programs.

Three conditions were frozen: first cold request, resident process with a newly
parsed/rebuilt request, and repeated solve of the same compiled quotient.
Each path has one cold and three fresh resident requests; compiled arms each
have one warmup and three measured solves. One worker, numerical thread1,
75s/job, 8GiB virtual address limit, free Kaggle CPU4, Python3.13.15/Linux.
The positive rule requires both fixed size bins and at least10x geometric
optimistic resident-new-request advantage. Singletons cannot pass a family.
No such flag would automatically admit learning.

## First execution and independent replay

125/125 jobs were attempted:101 FINISHED,9 PROCESS_FAILED,15 TIMEOUT.
375 request receipts were retained:361 exact original-goal PASS and14
NOT_VERIFIED; no returned wrong exact output was observed. 87 paths completed
all four verified requests. This is not a 361/375 capability score because
timeouts lack unfinished request receipts and paths share originals.

Parent elapsed time was1809.169s (30.15min). Independent reference audit took
0.089258s, reported separately from execution. Worker `perf_counter_ns` is
used for latency: parent `subprocess.wait` polling quantizes per-job elapsed
times. Peak process RSS is retained in raw receipts; energy, FLOPs, money and
full lifecycle investment were not measured. Missing stage times are UNKNOWN.

The local export ZIP is1,215,837bytes with1022entries. All1021 manifested files
passed byte/hash verification; replay calls no solver. ZIP SHA256:
`63e04646c8070b8df8fbe51ef7793a37f8dc873aae23e02488525e63be25bbc1`.

## Actual costs and explicit optimistic floors

Ratios below are Native / FREE QUOTIENT FLOOR. The floor retains original
parse/bind/hash and exact solve/restore, but omits quotient discovery, delivery,
and independent certificate acquisition. Cold floors charge measured startup.
These numbers are not learned NEUMANN or complete lifecycle speedups.

| Opened request | Native fresh resident seconds | Free fresh floor seconds | Cold ratio | Resident ratio | Same compiled quotient ratio |
|---|---:|---:|---:|---:|---:|
| BRP small | .027870 | .003819 | 1.197 | 7.297 | 1.033 |
| BRP large | .127392 | .048821 | 1.350 | 2.609 | .998 |
| Coupon | .049225 | .002183 | 1.335 | 22.550 | 1.067 |
| Crowds small | .039668 | .006864 | 1.227 | 5.779 | 1.050 |
| Crowds large | .098401 | .006071 | 1.566 | 16.210 | 1.079 |
| EGL | .758147 | .014281 | 4.741 | 53.089 | 1.094 |
| Haddad–Monmege | .019582 | .001963 | 1.174 | 9.973 | 1.046 |
| Herman7 | .017364 | .002102 | 1.189 | 8.260 | 1.091 |
| Herman15 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| Leader | .027266 | .004680 | 1.188 | 5.826 | 1.251 |
| NAND | .744755 | .138205 | 2.882 | 5.389 | .991 |
| Oscillators small | .447629 | .120930 | 1.920 | 3.702 | .996 |
| Oscillators large | 12.588702 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

Verified two-bin geometric means: BRP4.3636x, Crowds9.67849365x. Neither
reaches the frozen10x rule. Do not round Crowds to a PASS. Coupon/EGL are
singletons. Herman/large oscillators lack complete comparable quotient paths.
No cold request reaches10x. When both arms reuse the same native compilation,
their solve costs are approximately equal; reduction alone does not distinguish
a new discovery mechanism from existing compilation/reuse.

For example, EGL's native quotient removes2815.8x states, but the tested cold
floor is4.741x and equal-reuse execution1.094x. State counts are not cost ratios.
The possible new-request gap is acquisition-related and still omits proof cost.

## Failures and qualifications

- All9 process failures had returncode-11 (SIGSEGV) and empty stderr. Their
  root cause is UNKNOWN; an8GiB limit alone does not prove memory exhaustion.
- All14 NOT_VERIFIED receipts came from DD-to-sparse paths losing expression
  label binding, raising `InvalidPropertyException`. Missing strong symbolic
  paths qualify the portfolio comparison. First results were not repaired/rerun.
- Herman15 had no exact native result in this tested portfolio. A published
  exact analytic method already gives100/3, so this is not a strong-native
  capability gap. Oscillators large produced exact results in direct sparse
  paths but its quotient comparisons did not complete.
- Runtime transported the native manifest's rows rather than the pinned whole
  container. Their hashes differ. Independent replay confirmed exact equality
  of the registered container's row projection, every source hash and every
  exported file. The first contract and runtime files were not changed. The
  runtime did not assert the full-container hash; this limitation is retained.
  The initial failed analyzer is saved separately from corrected projection
  analysis, which is an audit correction and zero-solver execution.

Container hash `2f22f947737757931903ce23d6bf2b7b8c658b5f1ca7e5a3f226e86111a2d6f0`;
executed row-list hash `9d493a94fdc15b43055c6f864a779488bc4bad34bd80b46039a9a1b4079d50d4`.
This is a semantic projection match, not byte-identical contract enforcement.

## Stronger source-level controls and decision

Subsequent source-only review derived exact classical controls for Coupon,
EGL and both Crowds requests, and bound the published Herman15 maximum theorem
to its source. Five original exact outputs agree; transition/goal/property/
parameter mutations are refused.10 engineering tests passed. No analytic-control
performance measurement or machine-formal source proof was performed.
[Proof scope and engineering evidence](probabilistic_analytic_controls_2026-10-08.md).

These controls expose gaps in a Storm-only strongest-comparator claim. They do
not change the first screen's costs or verdict, nor establish a numerical global
no-headroom theorem. The large singleton warm floors and the large Crowds cell
do not supply learning admission while cheaper applicable goal-specific native
methods remain unmeasured and no independent structural transfer is tested.

**HOLD_LEARNING** for the tested acquisition/reuse setting. No G0 family PASS,
no GPU, learned generator, G1/G2 or sealed evaluation. The existing G0 B counting
cohort remains separately INCOMPLETE12/17 with its first timeouts preserved.
Other probabilistic abstraction families are not ruled out by this diagnostic.

Evidence: local `Continuation/G0_PROBABILISTIC_2026-10-08/` retains contract,
first source selection, runner,125 raw jobs, export, failed audit attempt,
independent analysis and session-stop screenshot. Portable derivatives are
`research/audit/G0_PROBABILISTIC_NATIVE_ANALYSIS.json/.csv`. Contract SHA256:
`9694bd5031d6a08e265d112922eeb67c3e3bd72ea51bf4c4beaf2082bea05a1c`;
runner SHA256:`102c647cb82b1b498dc667c8befb35375bb680cec36349b45873e6a83c3cb303`.
Kaggle CPU session was stopped after export. New work remains local; GitHub
CI belongs to the unchanged existing PR HEAD, not these local additions.
