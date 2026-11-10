# Q3 STOP register and architecture alignment | 2026-11-10

**Question: Has NEUMANN demonstrated self-improving, task-agnostic program invention on independent authored problems? Answer: NO (not yet).**

This archive is a **decision record changing the active PR set**, not a new algorithm, dataset, experiment, or claim of progress. It preserves the exact research branches, PRs and immutable original receipts rather than deleting history.

## Frozen authority and current mainline mismatch

- `docs/research/frozen_north_star.md`: frontier-level useful capability with minimum necessary complete compute; Q1-Q7 fixed, current Q3/Q6 still OPEN.
- [Issue #745](https://github.com/yoonsj0305/NEUMANN/issues/745): ONE learned discovery policy, source-observed latent structure -> new executable program -> independent counterexample -> update the same policy. No per-task/family answer-bearing solver contributions.
- The live `main` SHA reviewed: `5ce4a9d2083121d0a0ad5ab2e440dc0ff3f080ad`, still carrying legacy task-category routing; clean single-core [#748](https://github.com/yoonsj0305/NEUMANN/pull/748) is NOT MERGED.
- **Unresolved planning conflict:** `docs/research/core_question_gates.md` and `architecture_multiplier_gate.md` prohibit new training before the opened Gemma-E2B Architecture Multiplier, while newer #745 commissions exactly one single-core Q3 causal study. An authority decision is required before merging new Q3 training into main; an experimental side branch does not settle it.

## Actual negative evidence, never relabel as Q3 PASS

| Action | Observation | Scientific verdict |
|---|---|---|
| Run [#42766002744](https://github.com/yoonsj0305/NEUMANN/actions/runs/42766002744) | pretrained 0.5B 0/6 vs 2-step repair LoRA 0/6 real original AUTHOR SOURCE | no C-exclusive |
| Run [#42770959343](https://github.com/yoonsj0305/NEUMANN/actions/runs/42770959343), PR #768 | 4 genuine error/certified-correction pairs, 8 preference weight updates, 0/6 vs 0/6 | no observed transfer |
| Run [#42771878295](https://github.com/yoonsj0305/NEUMANN/actions/runs/42771878295), PR #769 | 0.5B 0/6 vs 1.5B 0/6, identical SOURCE/attempt cap | scaling alone ineffective at this budget |
| Run [#42773428267](https://github.com/yoonsj0305/NEUMANN/actions/runs/42773428267), PR #770 | 36 model-sampled proposals over 12 dev SOURCE originals, 0 useful partial preference pairs | no positive gradient signal |
| Run [#42789919942](https://github.com/yoonsj0305/NEUMANN/actions/runs/42789919942), PR #771 | universal lossless JSON causal observation vs RAW on six dev SOURCE originals, both 0/6 | observation reformat does not fix generation |
| Run [#42790569695](https://github.com/yoonsj0305/NEUMANN/actions/runs/42790569695), PR #772 | one free-text neural latent hypothesis + executable code vs two direct code calls, both 0/6 | verbal intermediate hypothesis != demonstrated useful method |

All six original tasks have been reused across development branches; even a later gain here is **post-exposure development**. The proper independent-author/independent-semantics A/B/C gate is not complete. CI SUCCESS, reduced LoRA loss, exact re-execution on synthetic tasks, or handwritten operator wins are not evidence of a learned invention-policy capability multiplier.

## STOP branches (not deleted; do not merge into main)

- Research PRs #768, #769, #770, #771, #772: tested mechanism alternatives with zero extra original AUTHOR SOURCE task wins. All original receipts and branches must remain accessible.
- Human-specified ARC object/coordinate/reducer research PRs #753 and #755-#764: retain as scoped comparators and historical examples only. This entire line does not satisfy #745 as mainline invention intelligence.
- Self-play PR #773 is **pending last already-launched experiment**. It generates its own synthetic code-worlds, which is not identical to discovering the causal solution of a new externally authored task. It may support curriculum research but is **not** Q3 PASS. Do not increase its 48 proposed worlds, 24 gradient steps or add other experiments after the current receipt. If C-exclusive on original SOURCE remains 0, archive/close; if positive, require independent author/original TEST confirmation *before* promoting capability.

## Minimal retained path

1. [PR #748](https://github.com/yoonsj0305/NEUMANN/pull/748): smallest common model-authored executable discovery / independent-source contract, without new domain solver.
2. [PR #766](https://github.com/yoonsj0305/NEUMANN/pull/766) and [#767](https://github.com/yoonsj0305/NEUMANN/pull/767): conditional **evidence and interface correctness** changes (real independent SOURCE splits, sealed checker, correct code-in-feedback, bounded context, lossless JSON), **not a Q3 capability claim**. Review/test this stack separately from research branches.
3. For unsupported original problems, trusted existing classical solver if verified; else **ABSTAIN**. No fabricated labels, no original TARGET gold, and no command to an actuator without adequate verification.

**Question budget:** More than three materially related Q3 experiments were already attempted within this research cycle. STOP additional experimental variants until the owner explicitly chooses whether to end Q3 now, or authorizes one **new, decision-changing, pre-registered** independent causal study; do not repeat the same six development originals.

**Next owner decision:** reconcile #745 Q3-first experimental authority with the older opened Architecture Multiplier mainline gate, and choose whether to STOP or reauthorize Q3 under a fixed experiment budget.


## 2026-11-10 frozen model-authored self-play causal outcome (second actual completed run)

- [Workflow #42793604422](https://github.com/yoonsj0305/NEUMANN/actions/runs/42793604422) SUCCESS as a **completed experiment**, NOT a Q3/Q6 PASS; source program-generation SHA and raw evidence retained as its Actions artifacts.
- Actual code-world creation budget: **48 pretrained-model proposal attempts**, **7** independently executed nontrivial code-text programs; frozen split **5 training** programs and **2 program-hash-disjoint synthetic heldout** programs.
- Actual LoRA weight learning ran: **24** optimizer steps, training loss **0.4912452697753906 → 0.4203656017780304**. This is gradient fit, not generalization.
- **Synthetic heldout A=0/2, C=0/2, C-only=0.** Original ARC-AGI-2 real AUTHOR SOURCE previous-development six A=0/6, C=0/6, C-only=0; original AUTHOR TARGET gold never read.
- Independent forensic review of 48-proposal artifacts: **0/12 accepted model-generated programs on nested-array inputs** in first frozen run [#42791954426](https://github.com/yoonsj0305/NEUMANN/actions/runs/42791954426), whereas the original ARC tasks require grid-shaped inputs/outputs. Common accepted programs were stringification, sort, dict->list and uppercase-key conversion. Two code-hash-distinct `sorted(x)` implementations in that first run describe an identical behavior, invalidating any inference from `8` code hashes to `8` discovered semantic operators. Model-authored synthetic tasks are **not independently authored unfamiliar task families**. The separate observational collision audit [#42794443250](https://github.com/yoonsj0305/NEUMANN/actions/runs/42794443250) found zero **train-vs-heldout** collisions on finite probes, but this DOES NOT eliminate training-vs-training semantic duplicates.
- A first older frozen run #42791954426 was still in progress at this archived note's creation, and its result is NOT invented or merged with the completed run. Any later result must be reported as its own cohort with its own SHA.

**Decision:** the self-generated inversion-training mechanism **did not produce a Q3/Q6 multiplier on the completed original SOURCE and synthetic heldout gates**, even though it autonomously generated runnable code. This is an actual negative evidence-based STOP on promoting the #773 branch. Do not expand self-play samples, add per-task answer operators, rerun this development six, or reinterpret syntax output as a learned novel discovery policy. The next different experimental study exceeds the Q3 budget; owner must explicitly approve a single frozen two-independently-authored-semantics gate and settle its authority against the older Architecture Multiplier block.


## 2026-11-11 Q3/Q6 independent two-domain causal study: STOP classification-only mechanism

**Question answer for actual original tests: NO. Q3/Q6 global: UNPROVEN.** This is the scientific decision from previously registered studies, not a newly repeated experiment.

### Original test 1: symbolic-latent JSON as prerequisite to learning

- [Frozen original A/B/C run #42834364029](https://github.com/yoonsj0305/NEUMANN/actions/runs/42834364029); [separate immutable original scorer #42836007493](https://github.com/yoonsj0305/NEUMANN/actions/runs/42836007493).
- Yale-LILY FOLIO original independent validation: A=0/4, B=0/4, C=0/4; transparent nearest-SOURCE comparator=1/4.
- BIG-Bench Hard causal judgment original: A=0/4, B=0/4, C=0/4; nearest-SOURCE comparator=2/4.
- C original four SOURCE learning episodes yielded **zero neural updates**. A/B/C no model-authored query hypotheses passed `start()` and all original attempts ABSTAIN.
- One SOURCE-only identical frozen checkpoint diagnostic [#42836583910](https://github.com/yoonsj0305/NEUMANN/actions/runs/42836583910) showed base 0.5B copied a literal JSON template in a top-level LIST, including the placeholder `query_id` and value `predicted observed JSON value`. `ValueError('latent hypotheses must be JSON object')` occurred BEFORE the first refutation. Mere permissive JSON parsing cannot generate missing falsifiable hypotheses. **Decision: do not use correctly formatted symbolic text as an indispensable prerequisite for learning from observations.**

### Original test 2: direct SOURCE label prediction with actual learned weights

- [SHA-frozen two-author study #42838378641](https://github.com/yoonsj0305/NEUMANN/actions/runs/42838378641) completed all three jobs SUCCESS, including independent original TARGET scoring performed after prediction freeze. New SHA-salt cohort excludes *all* original question IDs and same-story/premise groups exposed in test 1.
- Same model and architecture A/B/C, identical seed/init: C ran **4 true LoRA SOURCE gradients**, measured summed trainable L1 parameter change **81.64392104672879**; this is an absolute parameter sum, NOT a normalized ability or calibrated skill measure.
- FOLIO original unseen 4: A=0/4, B=0/4, C=0/4; nearest-SOURCE comparator=**3/4**.
- Causal original unseen 4: A=0/4, B=0/4, C=0/4; nearest-SOURCE comparator=**2/4**.
- Frozen raw (not admitted) original predictions were **IDENTICAL across A/B/C for ALL 8**:
  - FOLIO rows validation-159, -177, -106, -28: A=B=C `Uncertain` on all four, all wrong.
  - BBH IDs 185, 6, 73, 136: A=B=C `No, Yes, Yes, Yes` respectively; raw correct on 6 and 136 for all arms, no C-only gain.
- Held-out SOURCE source-check counts: FOLIO **0/2** for every A/B/C task; BBH A/B **1/2** each task; C **0/2** for ID 185, **1/2** others. The learned C made one SOURCE check **worse**.
- Therefore zero new method/representation solving ability from the measured four SGD updates; even raw unverified TARGET predictions offered zero C-exclusive gains.

### Root cause: invalid causal episode definition plus wrong optimization target

1. **Learning objective was category prediction, not new concept/discovery policy.** `neumann1/q3_predictive_state.py::_choice_loglik` compares autoregressive next-label scores, `learn_source()` optimizes generic outcome cross-entropy. Four nonzero gradients prove updating weights, not identifying a new causal representation or improving hypothesis-construction policy.
2. **No coherent hidden world/causal episode.** `research/q3/q3q6_two_author_freeze.py` intentionally selects SOURCE demonstration, probe and sealed check from DIFFERENT original stories/premise groups, and TARGET from ANOTHER unrelated group. This is a useful domain-distribution test, but not a within-world intervention/counterexample chain. The 2/2 SOURCE check lacks causal bearing on each individual TARGET. Treat it as a conservative unrelated-data abstention filter, NOT certification of a discovered target mechanism. In FOLIO random three-label tasks, meeting two unrelated exact checks has a ~1/9 *Assumption* probability under an iid-uniform guess, and in binary BBH ~1/4; these are illustrative probabilities, not measured distributions.
3. **No independent concept verification or mechanism reuse.** The model's internal states were not materialized as separate falsifiable, reusable hypotheses. Label ranking by the frozen model, even if it changed, would not by itself prove Q3 invention.
4. **Surface mismatch**: official FOLIO TRAIN uses `Unknown`, official validation `Uncertain`. Source/target label surface thus differs, a domain adaptation confound. This was preserved as published and NOT retroactively changed to improve results.
5. **Total cost not established**: neural inference/training wall-time and RAM/VRAM not fully metered per term; the measured L1 sum is not a compute saving.

### STOP and preserve

- **STOP PR #776 predictive-state classification branch as a Q3/Q6 mechanism; do not merge.** Keep branch commit and all first-run receipts, old TARGET outputs, hashes and independent scorer logs immutable. Move its active decision to `archive/q3/`.
- PR #775 remains a **draft learning-interface mechanism**, not demonstrated useful autonomous invention, and remains unmerged.
- **Do not create a third experiment from prompting tweaks, increased context size, teacher count, unrelated SOURCE checks or reusing the now-opened eight original TARGETs.** Q3/Q6 experiment count in this bounded cycle is **2/3**. If a third is authorized, its decisive change must be a *within-instance/world-bound* intervention+counterexample, learned reusable structural representation, and truly new original AUTHOR TARGETs in two unrelated mathematical/causal semantic domains. The same tool budgets and properly matched baseline must remain. Positive in both domains decides whether to retain the mechanism for reproduction; zero C-exclusive in either decides STOP. No ability guarantee.
- Do not claim frontier-level intelligence or Q3/Q6 PASS from 39 regression tests, four gradients, or author-domain labels alone. Q1-Q7 global all remain UNPROVEN.

**Next owner decision:** retain PR #775 as only an experimental interface while STOPping current predictive-state classification direction; approve a single coherent-world, representation-learning third and final bounded study ONLY once there is a falsifiable common causal episode and novel-structure acquisition objective.
