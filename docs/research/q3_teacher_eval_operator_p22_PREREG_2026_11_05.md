# NEUMANN P2.2 | Public-evaluation test of externally generated executable programs (PRE-REG)
Date 2026-11-05 KST. **Freeze before task bodies are fetched.** North Star frontier-level problem solving with minimum necessary computation; all Q1–Q7 globally OPEN.

## Hypothesis and strict category
P2.1.1 hand-coded object DSL found zero train-consistent candidates among 47 B/Q/P20-abstaining official public ARC-AGI-1 evaluation tasks. P2.2 separately tests an **external GPT-6 teacher's** ability to write *task-specific executable source* outside the fixed P1.9/P2.0 and P2.1 grammars. A pass establishes a limited externally assisted executable-discovery interface, **not autonomous learning by NEUMANN**, nor original computer-science opcode novelty, nor compute efficiency.

## Frozen public task source
Use official **public data/evaluation/** from `fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34`. Exclude all 48 P2.1 and all 48 P2.1.1 preregistered public evaluation task IDs, whether or not used at runtime. From the remaining 304 filenames sort by unsigned FNV1a32(`neumann-q3-p22-20261105|`+filename), tie by name, choose first **six**. Commit this frozen exact list *before opening task JSON*. These are new-to-this-development public evaluation tasks, not sealed or ARC-AGI-2 private tests.

## Genuine no-test-gold proposal protocol
A data-scrubbing fetcher may output to the external teacher only original `train:[{input,output}]` and `test:[{input}]`. It MUST delete all `test.output` inside the connector before emitting any model-visible tool response. All six original gold test arrays are reserved only for the later score operation. The user-visible teacher can view train outputs and test INPUTS, which is allowed. Public data may be present in GPT-6 pretraining, so this is *not* a provably unseen benchmark for that model.

Exactly **one first-submitted executable JS solve(inputGrid) program** or explicit ABSTAIN for each task, built from training evidence, with no task-ID branch, no input-array fingerprint lookup, no network, eval, external file, hidden test answers, or model calls in generated solve(). Programs must output rectangular 1..30 grids of integers 0..9. The first submitted six source functions must be committed to a single immutable GitHub file BEFORE the original scorer opens and compares any test gold. Subsequent edits cannot change this first-run score.

## Strong baseline and gating
On the identical six tasks, compute frozen B P1.1, Q P1.6, P20 and P2.1.1 deterministic outputs from the same original train and test INPUTS, with independent whole-task exact scoring only AFTER teacher first source commit. Count all original train pairs, each original test grid, program exceptions, wrong accepted output, and source sha.
- Local P2.2 teacher-interface PASS iff at least **two** original-task exact solutions *not* solved by any frozen classical baseline, source immutability, train exactness, independent cell-wise replay and gold mutation audit, **zero teacher program accepted wrong results**. Exactly one extra => INCONCLUSIVE; none or any wrong accepted => FAIL. ABSTAIN is valid and does not falsely increase score.
- The first 6-task result is immutable. Do not tune prompts, code, operator library or selectively redraw tasks on the scored cohort.
- No 10x or iso-capability inference. Full GPT-6 generation tokens, inference energy, price and latency UNKNOWN; compiled-program time is a small subcost. Report as teacher externally sourced and separate from NEUMANN.

## Degraded mode
If no general rule can be justified from training examples, submit ABSTAIN. If program fails any original train example or violates output schema, scorer marks wrong/ABSTAIN according to first source, never silently repair.

## Future admission
A teacher-PASS is only potential training signal for a smaller **internal** learned proposer; require task-disjoint semantic families, teacher-versus-student comparison, cumulative discovery cost, source code semantic dedup and independent proof before any global Q3/Q4 PASS.
