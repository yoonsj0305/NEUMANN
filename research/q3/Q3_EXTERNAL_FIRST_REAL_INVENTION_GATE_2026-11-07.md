# NEUMANN 1 | Q3 external original scientific closure gate

Date: 2026-11-07. **Global Q3 OPEN. Q4 OPEN. Q6 OPEN.**

## Original-source evidence, unchanged after external test exposure

- Source: Anjiang Wei et al. CodeARC (COLM 2025). Dataset revision 119512573bf96148cbb95e99cf7cdd21c06153e4, SHA256 3f08820594d4825c78bbdcc3b8eb2e6c8c0285fb3de966e900463b53f1723962.
- [PR #709](https://github.com/yoonsj0305/NEUMANN/pull/709): first 84-source original cohort. One completed shard had 0/16 train-admissible inventions, other three were preempted/cancelled. NO valid 84-task score exists.
- [PR #710](https://github.com/yoonsj0305/NEUMANN/pull/710): already exposed old source TRAIN-only diagnosis, 77/84 supported, seven unsupported. No heldout used for development diagnosis.
- [PR #711](https://github.com/yoonsj0305/NEUMANN/pull/711): distinct hash bucket 1, 65 original tasks, 54 eligible, one full 3/3 original-test correct. BUT its generated AST was a constant six, not a new structure. **Novel Q3 result 0/54.** One source-perfect sequence filter on #148 failed all heldouts.
- [PR #712](https://github.com/yoonsj0305/NEUMANN/pull/712): frozen exact learner source Git blob 01862093cf68c0a3425002a01fa8f83967bbcd23 and original evaluator blob ca2c6c19119fa3fe724eb2471f95ad1439e0bec8 on ALL remaining original hash buckets 2..16. 8/8 shards and coverage auditor passed.
- PR #712 [full original Actions run](https://github.com/yoonsj0305/NEUMANN/actions/runs/42352247449); [immutable complete audit artifact](https://github.com/yoonsj0305/NEUMANN/actions/runs/42352247449/artifacts/13565774498).

## Whole independent original cohort exact counts

| Measured quantity | Observed |
|---|---:|
| Previously unexposed author-created original task IDs | 944 |
| Supported original I/O tasks | 749 |
| Unsupported input or presentation contract | 195 |
| Full 3/3 original heldout exact programs | 20/749 |
| Exact individual original test examples | 68/2247 |
| Full-exact results from restricted older core | 12/749 |
| Full-exact results from cold NEW generator without memory | 20/749 |
| Full-exact results from online grammar memory | 20/749 |
| Nonconstant nontrivial generated source operator AST, exact 3/3 | **7/749** |
| Numeric formula types learned from original examples | 4 |
| String symbol-predicate filter functions learned from original examples | 3 |
| Constant-polynomial false novelty classifications rejected | 2 |

## Seven real source-specific executable ASTs

- CodeARC #135: generated mean (a+b)/2, exact original test 3/3.
- #156: generated polynomial 2ab+a^2, original 3/3.
- #421: generated polynomial 1+2b-a, original 3/3.
- #895: a five-term rational polynomial fits 7 training and 3 heldout original cases. This is NOT proof of semantic equivalence to the underlying reference implementation.
- #832: generated a filter predicate removing digit symbols 0-9, original 3/3.
- #834: generated a filter predicate removing !, original 3/3.
- #841: generated a filter predicate removing whitespace space, original 3/3.

These are new EXECUTABLE operator instances derived from source I/O, relative to the limited old core. However the two general constructor ALGORITHMS (sparse-polynomial search and subsequence/symbol-filter extraction) were HUMAN-CODED. They are NOT a machine-invented new fundamental constructor family.

## Causal failure and fixed gates

1. Earlier 34,000-candidate untyped search could not discover any program on the first CodeARC supported original shard, with runner preemption elsewhere. Type-directed search reduces useless candidates but cannot guarantee broader task correctness.
2. An apparent first original new polynomial #446 was only a constant f(x)=6. A scientific audit removed this false positive. NEVER count a new AST tag or a previously unsupported literal as novel computation.
3. Online grammar memory and cold new-generator runs had IDENTICAL whole-cohort exact accuracy: 20 vs 20. No cross-problem learning advantage was demonstrated. Do NOT claim the system has learned a better discovery policy.
4. The no-new restricted baseline cannot express all observed constants and is weaker than a full competitive baseline. All reported improvements are RELATIVE TO THAT SPECIFIC BASELINE, not a universal computational-advantage claim.
5. External original tests were published, not sealed. A full independent author domain outside CodeARC and a new unseen benchmark are required for global generalization.

## Next minimum necessary Q3 redesign

Build a single universal safe interpreter plus an algorithm which GENERATES representation-constructor ALGORITHMS, not just parameters of two programmer-installed families. The discovered constructor should have its own AST, executable implementation, preconditions, independent proof, and source code/library hash.

Experiment protocol: freeze generator before an entirely different corpus; reject constants and shallow memorization; include full cold vs memory vs no-new-constructor vs stronger classical baselines under matched end-to-end budgets; record source-excluded failures. Unknown/unsafe type or exhausted budget -> ABSTAIN (degraded mode).

Proposed stringent gate: at least three machine-created new constructor algorithms outside the existing family set; two independent author domains; one representation constructor transferred successfully to a distinct source domain; independent heldout correctness and causal benefit from memory. These are ASPIRATIONAL PASS criteria, not demonstrated results.

## Fundamental limit

Finite input-output observations do not identify a unique arbitrary function: for any hypothesized h and finite observed set S, another function g can agree everywhere on S and differ on an unseen input. Consequently unrestricted guaranteed correct invention on every unseen problem is not possible to establish without additional assumptions. Research success needs preregistered distributions, justified priors and reproducible independent testing.

**Decision: scoped original source-derived operator synthesis PASS (7/749); GLOBAL SELF-GENERATING REPRESENTATION-CONSTRUCTOR Q3 OPEN; memory-policy learning Q3 OPEN; Q4/Q6 OPEN.**
