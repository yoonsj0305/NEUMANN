# NEUMANN 1 · Q3 Source-Experimental Method Invention: Version Space and Proof Scope

2026-11-09 · experimental stacked PR #733 · base PR #732. **Scoped Q3 PASS; global Q3/Q6 OPEN. Q4 intentionally deferred.**

## A real failure in the inventor

The terminal-only inventor previously returned the first source-fitting typed fixedpoint AST. Positive-only integer endpoints admitted a process mapping negative inputs to zero. Initially the new source oracle found a negative counterexample but the AST synthesizer still could not repair it: the intermediate expressions were deduplicated only on the original training inputs, so potential repairs were pruned.

[Failed CI 42546266767](https://github.com/yoonsj0305/NEUMANN/actions/runs/42546266767): 1 failed / 11 passed. Repair: use ALL legitimately observed SOURCE inputs (including new counterexamples) in intermediate-expression signatures. [Fixed CI 42546441502](https://github.com/yoonsj0305/NEUMANN/actions/runs/42546441502): 12/12 passed.

## New algorithm: design the next SOURCE question

SOURCE endpoints → enumerate executable typed transition ASTs → attach previously learned higher-order fixedpoint controller → retain multiple source-verified and unlabeled-probe-distinct hypotheses → generate new typed SOURCE experiment input ASTs → select the input maximizing disagreements → request a SOURCE-only terminal label → eliminate inconsistent hypotheses → **resynthesize the transition AST after a counterexample** → verified result or ABSTAIN.

The disagreement score for n candidates with prediction group counts n_j is

    D(x) = (n^2 - sum_j n_j^2)/2.

It counts disagreeing unordered pairs. If D(x)>0 and a deterministic true oracle belongs to the finite version space, a SOURCE answer eliminates at least one candidate. This is a conditional contraction statement, not universal correctness or automatic discovery of the true hidden trajectory.

The source probe inputs are used as unlabeled representational distinctions. Their gold outputs are not known to the program synthesizer until the authorized source oracle is called. Forbidden target inputs cannot be probed; a missing oracle or exhausted budget forces ABSTAIN. Verified classical methods bypass invention.

[Latest hard positive test 42547326943](https://github.com/yoonsj0305/NEUMANN/actions/runs/42547326943): 12/12 PASS. Signed integers: 3 candidate hypotheses examined across rounds, 1 discriminating question, 1 falsifying SOURCE endpoint and a genuinely different newly synthesized AST. 53 total SOURCE oracle queries. These figures are not FLOP/time efficiency claims.

## Frozen synthetic unseen input evidence

[Source-frozen Actions 42547326845](https://github.com/yoonsj0305/NEUMANN/actions/runs/42547326845), SHA-256 26e12b70640b1e5ec8d41e34e5b57b30cb6f925b0901bf53d6ac5a179d10ec2b.

| Type | Before | After |
| --- | ---: | ---: |
| Signed integers | 200/400 | 400/400 |
| Finite sets | 200/200 | 200/200 |
| Binary strings | 200/200 | 200/200 |
| Total | 600/800 | 800/800 |

Outputs were SHA-frozen before separate target scoring; SOURCE oracle calls happened before targets were generated. These are 800 researcher-authored synthetic tasks, not independent-author originals, frontier evaluation, or an unrestricted Q3 success. There are ZERO target-domain successor labels. The primitive typed library and search policy remain human provided.

## Conditional semantic theorems for synthesized programs

1. **Signed integers.** The synthesized update is T(n)=n-max(0,min(n,1)). For n>0, T(n)=n-1. For n<=0, T(n)=n. Consequently repeated iteration until full-state equality returns min(n,0) for every mathematical integer if there is no resource budget. The implementation only guarantees this when the state bounds are satisfied and max_steps>=max(n,0)+1.

2. **Finite sets.** The synthesized update is T(S)=S minus {min(S)} for nonempty S; T(empty)=empty. Every nonempty step strictly decreases |S| by one, so a finite input set reaches empty after |S|+1 transition calls, provided size/step budgets are sufficient.

3. **Binary alphabet strings.** The synthesized update is replace("bb","b") repeatedly until a full-state fixed point. Any string containing "bb" shrinks in length; the order of non-b characters and each nonempty b-run's location are preserved. This yields exactly one b per maximal run. Termination follows within at most input_length+1 transition calls if resource bounds allow.

These are HUMAN-DERIVED proofs about machine-synthesized programs, not claims that the machine invented the mathematics or autonomously proved induction. The added semantic-invariant tests exhaustively check 513 signed integer states, 64 finite sets and 2047 short binary strings.

## Exact limits and next Q3 gap

- Endpoint observations cannot identify unique hidden successor dynamics. Even agreement on ALL terminal values may not determine the true internal transition.
- No evidence of arbitrary new primitive invention beyond the supplied instruction language.
- No independent-author new semantic family or frontier superiority demonstrated by this experiment.
- Finite source checks and probe sets cannot guarantee arbitrary unknown-function extrapolation.
- Do NOT claim 10x cost/compute; Q4 is intentionally deferred while Q3 is primary.
- Degraded mode: source uncertainty, missing oracle, unsupported type, process budget, unverified convergence, or absent grammar → ABSTAIN; retain any independently verified classical method.

**Verdict:** A source-experimental and source-reflective invention mechanism now actually reconstructs executable process ASTs, with reproducible cross-type bounded semantic transfer. Global unrestricted Q3 and Q6 remain OPEN, not PASS. Keep this research PR unmerged pending independent-author original semantic transfer and genuinely new primitive discovery.
