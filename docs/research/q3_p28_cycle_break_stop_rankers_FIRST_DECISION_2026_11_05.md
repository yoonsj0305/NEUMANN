# NEUMANN 1 | P2.8 Q3 cycle-break decision: stop ranking, require language growth
2026-11-05 KST | Research decision, not a capability claim | North Star: **Frontier-level problem solving with minimum necessary computation**.
Global Q1–Q7 **OPEN**. No merge into main.

## 1. Exact problem redefinition
Generate, execute, independently verify, and **reuse previously unavailable executable problem-solving structures** across different unseen problem families at lower **complete** cost than strong classical or model-first alternatives. A faster searcher of preauthored semantics is NOT sufficient.

## 2. Five eliminable assumptions
- **Reject**: another ranking model on the same finite grammar may fix tasks with zero train-consistent candidates. It cannot, by definition.
- **Reject**: adding handwritten operators after inspecting public evaluation failures is autonomous invention. It is human design and post-hoc benchmark tuning.
- **Reject**: one synthetic mechanism PASS or in-domain transformation is independent semantic-family transfer.
- **Reject**: local failed-search 10.23× speed ratio is 10× *solving* efficiency; these failed branches output no solution.
- **Keep**: complete original TRAIN replay, typed and sandboxed executable semantics, independent score only after proposal, fail-closed ABSTAIN, strong classical Direct, all-in compute accounting.

## 3. First independently reproduced ceiling
P2.7 original immutable receipt SHA256:
`c472a96a4b1dc1cbe5e8292323a69455a1ac4deec2c38e27ac3c887a74346671`.
Original public ARC-AGI-1 evaluation upstream `399030444e0ab0cc8b4e199870fb20b863846f34`.
[First scoring](https://github.com/yoonsj0305/NEUMANN/actions/runs/42003978711), [independent first audit](https://github.com/yoonsj0305/NEUMANN/actions/runs/42004559375), [P2.8 independent full 157 × 32 TRAIN-only hypothesis enumerator](https://github.com/yoonsj0305/NEUMANN/actions/runs/42006335567) ALL source-pinned.

Among 32 FIRST public evaluation tasks:
- Classical B/P20/P24/P25 combined **2/32 exact**.
- NEW classical 157-AST exhaustive search **0/32 exact**, learner-prior 157-AST exhaustive search **0/32 exact**; neither added any exact answer; both ABSTAIN 32/32.
- Exhaustive independently recomputed fit sets: **31/32 empty**, 1/32 exactly one full TRAIN-fit candidate but unsupported at test. Full candidate enumeration **5,024** for each arm.
- Training prior: **9 meta-positive tasks among 400**, from **only 6 distinct macro AST keys**: identity 4, flipH 1, flipV 1, flipH+cropNZ 1, cropBG 1, scale2+cropNZ 1. These are NOT six invented primitive semantics.
- Thus the meta-policy trained on 400 tasks effectively observed just 9 verified successful transfers (2.25% of meta-training tasks), strongly limiting support. This is a dataset count, NOT a generalization confidence interval.
- No neural forward calls or new teacher calls; external GPT-6 teacher P2.2 successes belong to the external teacher, not NEUMANN learned capability.

### Mathematical STOP result
For fixed grammar H and original TRAIN D, H_D = {h ∈ H : h(x_i)=y_i for all (x_i,y_i) ∈ D}.
If H_D is empty, **any ranking, search policy or trained neural prior whose output must be in H has zero TRAIN-fitting solution**, regardless of compute. No weighted ordering or retries can enlarge H. This is true for **31/32** cases in the frozen P2.7 exact 157-program grammar. Even the remaining one was NOT a verified test solution.
Scope is a FINITE frozen hypothesis class, not an AGI or ARC impossibility theorem.

## 4. New architecture boundary (genuinely distinct, NOT RUN)
The next allowed family must change the **source of semantic rules**, not reweight a known hypothesis inventory:

1. **Open-ended proposal with an explicit execution contract.** A generative proposer creates *new typed program ASTs* and/or new library definitions not prelisted as whole operators. Use a generic executable substrate with strict bounds and sandboxing. The proposed *programs* may be informed by pretrained open-source LLMs or external teachers, but attribute their capability and compute correctly.
2. **Verifier/CEGIS from original TRAIN.** Reject nonterminating, ill-typed, ambiguous, unsupported and wrong programs; extract counterexamples from TRAIN, repair or abstain. Never route original TEST gold back to generation.
3. **Library invention + independent reuse.** Abstract common executable substructures (e.g. anti-unification / e-graphs / MDL) across verified successes into new reusable functions. Require separate proof that a new library entry shortens heldout program descriptions or reduces computation AND improves independently verified new-family capability compared to a matched classical composer. A renamed hardcoded operator is not an invention.
4. **Train the discovery policy itself.** Use positive/negative verified code traces, not 9 successes or task-ID caches; maintain an untrained generative baseline and a strong classical baseline granted the same low-level code execution/verification rights.
5. **Transfer BEFORE scaling.** Evaluate unseen **semantic families**, not rotations of the same seed or heldout cells. Do not consume additional official evaluation tasks unless the development-only transfer-first gate below passes.

This architecture is compatible with lessons from DreamCoder's automatically grown libraries and SOAR's hindsight refinement, but following those papers is not itself novel research.

## 5. Development-only preflight (new admission gate; proposals)
Use a NEW, frozen split of public-development tasks and independently created different-semantic-family tasks. Do **not** reuse the 32 consumed P2.7 evaluation samples to tune the proposer. Possible thresholds [ASSUMPTIONS, not results]:
- At least **32 task-independent verified correct program traces** across ≥ **8 reusable extracted substructure families** before training the ranker. Count tasks, not cells/variants. The number may be revised *before* the freeze based on measured learning curves.
- A successful functional program that cannot be reduced to the old 157-AST P2.7 grammar on a registered **separating witness set**; a finite witness can demonstrate *behavioral difference* but cannot generally certify global non-equivalence.
- ≥ **2 new correct** in 32 never-opened original tasks above a matched classical proposer **using the same expanded semantics**, no newly false accepted outputs; and at least **1 independently held-out different-semantic-family success**. Exact 32-task threshold can only become official if declared BEFORE opening any future cohort.
- A **positive out-of-family advantage** after amortizing training, proposal, code execution, independent replay, retry and fallback costs. If no positive transfer, STOP regardless of in-domain accuracy.
- Hold a fixed max proposer budget and total inference budget per arm, with a classical/teacher/learning ablation. No manual grammar patch prompted by test gold.

## 6. All-in cost and safety
C_NEUMANN = amortized C_teacher + amortized C_training + C_propose + C_compile + C_repair + C_verify + C_fallback.
Use matched same-capability Direct and hard cost metrics. Unknown components remain UNKNOWN, not zero.
- Never execute arbitrary untrusted generated code on an unsandboxed CI host. Use a restricted interpreter, time/memory quotas, permissions with no network access and syntax validation.
- Degraded mode: ambiguity, code safety rejection, insufficient data, OOD uncertainty or resource cap => ABSTAIN or verified Direct fallback, and charge fallback.
- File/name hashes, open-source model pretraining exposure, selection on public evaluation, correlated variants, and opaque teacher solutions can all create leakage/illusory gains.

## 7. WBS and stop rules [ESTIMATES, engineering plan only]
A. 0.5–1 engineering day: define typed proposal/execution/sandbox and freeze baseline/metadata (plus 30% integration buffer).
B. 1–2 engineering days: reuse existing verified teacher source or safely run pretrained local proposer; collect signed TRAIN replay and failure traces, no heldout evaluation.
C. 2–4 engineering days: automatic abstraction extraction and decontaminated meta-policy, compare with identical-budget classical + pretrained-only controls.
D. 1–2 engineering days: preregistered internal cross-semantic transfer and all-in cost accounting; STOP if no incremental verified transfer.
No GPU allocation to an expanded ranker unless the novel executable grammar has shown a measurable training-only or dev-heldout ability.

## 8. Research decision
P2.8 is a **STOP/REDEFINE** proof, not one more ARC solver release.
- STOP: bigger finite beams, P2.7 prior retraining on 9 positives, task-local handcrafted Boolean expansions and fresh public-eval scoring of the SAME candidate grammar.
- KEEP: P2.6 exact language collision certificates, P2.7 FIRST receipt, strong classical Direct, independent compiler verification, and fallback.
- NEXT eligible work: **open-program generation → checked training solutions → automatic reusable abstractions → trained discovery policy → genuinely independent family transfer**, each with a failure-first gate.

**Do not call this quantum jump in capability**. The decisive achievement so far is proving what cannot work under the frozen representation and preventing more invalid capability claims. Q3 autonomous invention, Q4 transfer, Q5 all-in efficiency and Q1–Q7 globally remain **OPEN**.
