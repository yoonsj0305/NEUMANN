# NEUMANN 1 — Discovery-Policy Causal Gate (NOT A NEW RC)

Status: PRE-EXPERIMENT PROTOCOL / no fresh model results. 2026-10-26.
Authority: user-frozen `docs/research/frozen_north_star.md`. Global Q1–Q7 remain OPEN.

## Main falsifiable claim

When original program, solution library, retrieval, exact known macros and prior search traces are removed, does an *updated learner policy* discover and verify useful NEW problem-solving methods in independently authored task families more successfully than the same learner without meaningful meta-learning, given identical compute budgets and tool rights?

This separates *experience improving the discoverer* from *caching and retrieving discovered answers*.
An NN can encode memorized macros in its weights, so we additionally test novelty of semantics, token/operation renaming, family holdout, provenance, and no-exact-program overlap.

## Why this is the single missing experiment

- RC47: bounded classical trace anti-unification learns a shared SLOT macro; no trained discovery policy. Its 30-repeat CPU advantage is only scoped 1.405x with discovery charged.
- RC48: a neural net receives equality-location features and rewards computed from those same observable relations. Classical anti-unification can do the work. Strong direct CPU 4.313ms vs ownweight + training 579.767ms; no unique neural advantage. On that same synthetic fixture 13/30 untrained initializations passed both narrow conditions; 8/8 additional training seeds passed, but there is no independently authored unknown-family causal demonstration.
- RC50: external public ARC training cohort 11/12 using strong classical + a separate ChatGPT GPT-6 proposer, not NEUMANN own weights; operators unchanged did not source-admit 0/12 next problems. Thus no B/C from NEUMANN learned core.

DiscoRL (Nature 2025 DOI:10.1038/s41586-025-09761-x) provides a concrete precedent for meta-learning a rule across many complex environments with transfer; not evidence for low-resource NEUMANN. DreamCoder (2021/2023) combines neural search priors and learned symbolic library; mere library growth is prior art.

## Pre-registered causal intervention (no labels opened until registered)

**A. Policy-updated, MEMORY EMPTY:** ownweight model meta-trained on author/source families A/B; freeze weights and optimizer state; delete exact macro library, retrieval indexes, program caches, candidate traces and saved solutions; allow only frozen model to propose novel concepts via identical general execution interface. Any learned weighting/internal representation remains as intended policy.

**B. Sham-updated, MEMORY EMPTY:** exactly the same initial architecture and matched train compute, but discovery-value signal permuted within preregistered provenance-safe task strata. Otherwise equivalent rights, budgets and optimizers. Controls optimization effects and information leakage.

**C. Classical strong baseline, MEMORY EMPTY:** general-purpose synth/SMT/e-graphs/search with same interface and total verifier/cost charges; not a deliberately crippled fixed-SLOT grammar.

**D. Updated + memory intact** (diagnostic only): quantifies exact stored-macro reuse boost. Cannot by itself establish discovery policy learning.

All arms use the same genuinely independent original tasks, trusted execution sandbox, verifier, refusal policy, original task identities and deadlines. A must beat B to show *reward-caused improvement*, and beat or complement C on the **same original task** to earn a role. D>A alone is only a library effect.

Holdout must have **novel underlying semantics**, not merely unseen strings/grid shapes or a changed operator name. Separate independent human authors grade train A/B vs final C/D tasks. Never choose convenient task IDs or success thresholds after opening gold. Do not substitute generated favorable synthetic tasks.

## Outcome and resource contract

PRIMARY (original-task utility): paired independent-verified solution success under the same capped wall/compute/tool budget on all assigned holdout tasks; count all failures and HOLD as failures for full coverage, with abstention separately reported. Quantify `Delta_Q = Q(A) - Q(B)`; report paired cluster-by-domain uncertainty and exact test outcome, not just training accuracy. Must beat sham policy across multiple truly disjoint families. Report A vs C separately.

SECONDARY (actual complete efficiency): only among **matched-accuracy** policies and task sets compare full costs: training, all discovery attempts, inference, tool/transport, verification, retries, logging/storage, cache rebuilding, fallbacks and amortized training over preregistered number of future uses. Record CPU/GPU work in appropriate units, joules, RAM/VRAM peak, latency, USD as separate dimensions; UNKNOWN never becomes 0.

For one discovered method a reused N times (if both paths meet same correctness target):
`NetValue_N(a)=SUM_i(C_baseline(T_i)-C_after_a(T_i)) - C_invent(a) - C_verify_store(a)`.
`N` and evaluation distribution fixed before study. This is a value/accounting criterion, NOT automatically a differentiable learning rule. Learning signal should be improvement in **future independently verified discovery**, not novelty-by-text or mere source fit.

B/C "PASS" require: (1) FIRST weights/method proposals SHA-frozen before task gold; (2) independent new reusable abstraction not a hardcoded answer template; (3) measurable positive A–B gap on predeclared heldout ORIGINAL tasks; (4) stress tests for exact-program and code/word leakage; (5) comparison with strong classical C; (6) failures + full costs retained. A correct first program in one external example does NOT close these.

GLOBAL Q5 / Q7 further demand actual frontier-gap membership and complete iso-capability cost advantage under the Frozen North Star. They stay OPEN even if discovery-policy mechanism passes.

## Minimal staged decision with stop conditions

Stage 0: audit the unmodified RC48 evidence and new-source provenance; no model training. If only hardcoded compression predicate is available, **STOP / FAIL TO ENTER**, do not optimize it.
Stage 1: freeze independently authored tasks, verifier, four arms, capabilities, target success and all costs. Explicit evaluation identities are sealed from model tuner. No code or threshold changes after this stage.
Stage 2: one small pilot meta-training on source families A/B, then memory-reset exact same model weights vs B/C/D on heldout C. If A does not have any nontrivial new verified method or A and B perform alike, **STOP, record FAIL/OPEN**.
Stage 3: only if stage 2 is promising, independent fresh author-domain D replication plus full resource accounting, with no retraining/tuning on C/D.
No implied time or performance forecasts; exact task counts, budgets and statistical thresholds require preregistration with the selected external datasets and allowed compute before the final study.

Degraded mode: return HOLD_UNKNOWN with explicit disputed assumptions; no downstream authority on source-only fit; rollback meta-updates if they degrade verification, capability or resource costs. All original receipts immutable.

## Historical evidence verdict

RC48 checks that actual Torch weights exist and narrow in-grammar structure can be proposed. It does **NOT** check A>B with libraries reset on independently authored novel tasks. No existing retained RC experiment establishes the core causal claim. Therefore CREATIVE DISCOVERY POLICY LEARNING remains OPEN, not PASS.


## 2026-10-26 — New evidence absorption (NO new RC, NO global promotions)

**Research center unchanged**: learn to invent genuinely new verified problem representations and transfer that *discovery capability* after clearing stored solutions. We adopt minimal prior-work mechanisms as controls or audit gates, NOT a 10-model stack.

| Paper / original source | Reduce to one accountable mechanism | Admission |
|---|---|---|
| DreamCoder (PLDI 2021 / 2023; DOI 10.1145/3453483.3454080) | Symbolic library growth separate from learnable discovery/search policy; memory-on vs memory-off ablation | Experimental baseline after G0 |
| Discovering state-of-the-art reinforcement learning algorithms, DiscoRL (Nature 2025; DOI 10.1038/s41586-025-09761-x) | Meta-reward on future discovery across **diverse** environments; do NOT reproduce 1024/2048 TPUv3 training | Long-term learner design |
| SkillGen: Verified Inference-Time Agent Skill Synthesis (Microsoft Research, May 2026) | Contrast successes and failures; paired repairs, regressions, still-fails on same original tasks | **Adopt now** as outcome accounting |
| Scaling Agentic Verifier for Competitive Coding (ICML 2026) | Select discriminative counterexamples, with independent oracle; candidate disagreement != correctness | **Adopt now** conditional on source-consistent multiple candidates |
| Budget-Aware Tool Use Enables Effective Agent Scaling / CATS (COLM 2026) | Count model tokens and **tool calls**, optimize allocation under preregistered cap | **Adopt now** as spending measurement, not new large controller |
| GEPA (ICLR 2026) | Reflections grounded in execution failures, record exact specificity and heldout net effect | Optional proposer; failure trajectories may be untrusted |
| AlphaEvolve (Google DeepMind 2025/26) and CodeEvolve (Findings EMNLP 2026) | Executable program proposals, diversity and fitness verified by independent evaluator | Strong baseline / expensive large evolution DEFER |
| Absolute Zero (NeurIPS 2025) | Generator creates verifiable training challenges **only within train fold**; reward-hacking audited | Conditional after G0 |
| Do Self-Evolving Skills Generalize to Held-Out Tasks? (arXiv:2609.39148; Sep 30, 2026) | Test against unseen cases, demand regression/overfitting accounting; 5/21 retained ALL train improvement | **Hard transfer guard** |
| Does Failure Feedback Direct Agent Self-Modification? (arXiv:2610.14662; Oct 10, 2026) | Separate target repair, same-mechanism transfer and independently heldout net changes | **Hard causal guard** |
| Are Self-Evolving Agents Continual Learners? (arXiv:2610.25858; Oct 19, 2026) | Retest old successes after each update, forbid cross-domain retrieval collisions and forgetting | **Regression and memory compatibility guard** |

### Executed historical external outcome audit, not a NEW model result

We fetched and cross-checked the original frozen first receipts for 12 ARC-AGI-2 **PUBLIC TRAINING** tasks, original corpus pin `f3283f727488ad98fe575ea6a5ac981e4a188e49`:
- 8/12 first-frozen original tasks correct under combined **classical** program portfolio;
- 11/12 with three extra proposals from **ChatGPT GPT-6**, NOT NEUMANN ownweight;
- Pairwise skill intervention, same original 12 tasks: **REPAIR 3, REGRESSION 0, RETAINED 8, STILL UNSOLVED 1**. These figures are retrospective and are NOT independent sealed generalization.
- On next 12 external public-training tasks, original frozen new-operator candidates **SOURCE FIT 0/12**, hold 12/12. This is not evidence of test-gold failure nor general classical impossibility. It demonstrates that exact candidate reuse did not cover this sequence.
- Model-discovery-policy learning A>B, A>C on new authored families remains **NOT RUN**. GPT-6 API inference/training/joules/storage total-cost UNKNOWN. No Q1–Q7 PASS.

**Executable local audit**: `NEUMANN1_DISCOVERY_POLICY_VALUE_GATE_20261026.zip`, SHA-256 `e4f566e7eff092ef180946d2f46ed9a7364bbed25a82623a97e9ee48034cb7d1`, distributed as conversation attachment. New isolated extraction: manifest 5 files PASS, historical audit deterministic replay PASS, pytest **9/9 PASS** (engineering tests, no new tasks). The GitHub document records method decisions; the full standalone code is attached in the conversation, not falsely claimed committed to repository.

**Single G0 decision**: ownweight generator that can synthesize useful **semantic hypotheses not reducible to input-provided feature predicate** is currently NOT demonstrated; do not spend on new meta-training until an independent verifier, strong classical gap, discovery-policy A/B/C/D and matched rights/cost source are assembled. RC48 neural SLOT controller is specifically **out**. Return HOLD on G0; retain frozen evidence. Avoid new RC and PR proliferation.

Full original references:
https://www.nature.com/articles/s41586-025-09761-x
https://www.microsoft.com/en-us/research/publication/skillgen-verified-inference-time-agent-skill-synthesis/
https://proceedings.mlr.press/v306/ma26av.html
https://research.google/pubs/cost-effective-agent-test-time-scaling/
https://arxiv.org/abs/2609.39148
https://arxiv.org/abs/2610.14662
https://arxiv.org/abs/2610.25858
