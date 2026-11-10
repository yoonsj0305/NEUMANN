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
