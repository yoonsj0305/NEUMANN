# NEUMANN 1 | RC40 bounded-source conformance: 28.13x fewer queries, 24/24 exact

**Date:** 2026-11-06 · **Scope:** classical finite-state source-only verification on the **same reopened** 24 RC39 tasks. NOT global Q3/Q4/Q6/Q7 completion.

## Real first execution and independent audit

- [Immutable FIRST RC40 run #42136993787](https://github.com/yoonsj0305/NEUMANN/actions/runs/42136993787), **SUCCESS**. Source receipt SHA256 `9174cbaf28715a36bae57731b0295e39c8a0b5c63e4436541692a1f09fc446e2`.
- [Separate readonly audit #42137380049](https://github.com/yoonsj0305/NEUMANN/actions/runs/42137380049), **SUCCESS**. Uses alternate product-state checker and source receipt SHA pin; 24/24 states exact, 24/24 modified programs rejected, first score forgery rejected; re-learning **0**.
- Original learner Git blob **unchanged**: `83bd15d98b8fa02f4427b26c27264d35c0ec261e`. Same 24 hidden references, original membership-only rights, advertised true-state bound N=5. The baseline in this experiment is a **same-runner replay** of the old exhaustive conformance, not a rewrite of original FIRST evidence.

| Metric, same runner | Exhaustive all-words | RC40 classical W-method |
|---|---:|---:|
| Unique source membership queries | 172,051 | **6,117** |
| Unique source input symbols | 1,362,696 | **28,354** |
| Conformance words enumerated | 172,499 | **6,065** |
| Learning and conformance process CPU (single runner) | 546.066374 ms | **19.845976 ms** |
| Independent all-finite-word equivalence | 24/24 | **24/24** |
| False all-length certificates | 0 | **0** |
| Deliberately altered state programs rejected | 24 (independent audit of W) | **24** |

**Query reduction:** 172051/6117 = **28.126696x**. **Source-symbol reduction:** 1362696/28354 = **48.0601x**. CPU values are single-run empirical process-time observations, not hardware-independent performance or financial/energy cost. Direct real-world API latency was not measured.

Test suite: [3000 synthetic Mealy source/hypothesis pairs](https://github.com/yoonsj0305/NEUMANN/actions/runs/42136993787) independently checked against exact reachable-product equivalence. Reachability/nonminimality violations are UNKNOWN. Negative controls include an output discrepancy delayed until a fifth A.

## Why the improvement is **general** within its mathematical scope

The hypothesis is a **reachable, state-minimal deterministic complete Mealy machine** with `m` states over input alphabet Sigma (`s` symbols). We assume, from a **trusted external contract**, that the unknown target is a deterministic complete Mealy machine with at most `N` states and the same alphabet, and that membership(word) returns truthful, resettable output traces.

Compute a state cover `P`, a transition cover `P ∪ P·Sigma`, and a candidate characterization set `W` that distinguishes each pair of candidate states. Use the established classical **W-method** suite

`T = (P ∪ P·Sigma) · Sigma^[0 .. N-m] · W`.

The suite is a conformance-complete fault-domain test if its prerequisites hold. The complete scope is a theorem of finite-state conformance testing, *not* evidence that a new neural representation was autonomously invented. It applies to different task names, application stories, state-transition topologies, and all finite input lengths **within this formal class**. W-method reference: F. Howar et al., *Small Test Suites for Active Automata Learning*, Springer, 2024, DOI 10.1007/978-3-031-57249-4_6.

For `m <= N` and `s >= 2`, a conservative upper bound for enumerated tests **per callback before deduplication** is

`m(1+s) · [1+m(m-1)/2] · sum_{k=0}^{N-m} s^k`.

With `N=5` and `s=3`, this bound is at most **640 tests per callback** across `m=1..5`, versus exponentially longer blind enumerations using the prior all-word upper cutoff `N+m-1`. The actual unique query count also includes the active learner's own membership calls and cross-callback cache effects.

**No unconditional generalized proof** exists without a trusted state/grammar bound or stronger oracle: a finite query sample cannot distinguish a simple machine from a sufficiently large delayed-output machine. Original RC39 proved this boundary; RC40 does not repeal it. Fail-closed UNKNOWN is the correct degraded mode when the premises do not hold.

## Scientific gate, no favorable grade inflation

| Capability | Decision |
|---|---|
| Source-only, bounded-state all-length certificate | **24/24 SCOPED PASS** |
| >10x fewer unique source membership queries than identical exhaustive source rights | **28.13x SCOPED PASS** |
| Independent read-only proof and first-result tamper detection | **PASS** |
| New/neural structure or new primitive invented by learner (Q3 global) | **OPEN** |
| Independent external semantic-family transfer (Q6) | **OPEN** |
| Equal-rights strongest classical vs neural end-to-end efficiency, total lifecycle 10x (Q4) | **OPEN** |
| Frontier general problem solving (Q7) | **OPEN** |

The 3,000 randomly generated machine pairs check **software conformance logic**, not trained cross-domain generalization. The 24 original tasks were already opened before RC40. No original ARC-AGI-1 evaluation identifiers were consumed.

## Strategy and integration

**Keep** W-method as a drop-in verification interface for the known bounded-resettable finite-state subdomain, not as a top-level intelligence breakthrough. Output certificate must include `N`, alphabet, candidate state count, receipt SHA, source-call count, and verified W-suite completion. If N is unknown or source behavior non-resettable/noisy, return UNKNOWN and revert to trusted exact classical solution paths; never issue unconditional all-length proof.

**Do not** spend the remaining 11/400 unused public ARC-AGI-1 original evaluation IDs on further variants of a known classical finite-state grammar. The next candidate Q3/Q6 gain needs external-author fresh semantic-family tasks, a policy learned rather than a handcrafted search operator, and matched source rights + strongest classical baselines. The critical path is *novel policy and transfer*, not squeezing another few percent from 6,117 queries.

## Repository provenance

- PR #650: global original ARC evaluation ledger, 389/400 used (draft).
- PR #651: RC39 first 24 and membership-only scoped proofs (draft; stacked on #650).
- PR #654: RC40 W-method implementation, preregistration, 3000-case controls, first receipts, independent pinned audit (draft; stacked on #651).

Do not silently merge stacked drafts out of order. Keep all FIRST receipts immutable. All status decisions above are explicitly limited to inspected GitHub evidence.
