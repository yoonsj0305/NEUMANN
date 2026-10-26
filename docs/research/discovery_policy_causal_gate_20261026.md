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
