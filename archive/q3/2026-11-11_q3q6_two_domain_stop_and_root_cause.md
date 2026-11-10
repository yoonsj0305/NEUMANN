# Q3/Q6 STOP: verified negative two-original-author capability result

2026-11-11 KST | Retained original public corpora, model-output digests and workflow evidence. This file is an **archival scientific decision**, not a new experiment, new architecture, or Q3/Q6 PASS.

## Question and answer

**Can the same learned intelligence mechanism invent a new useful causal representation and transfer newly acquired ability to two unrelated, independently authored original problem classes?**

**Answer: NO for both completed experiments; Q3 and Q6 globally UNPROVEN.**

## Immutable study 1

- Original externally authored FOLIO 4 and BBH causal judgment 4 tasks, label-blind IDs and frozen model outputs.
- [First A/B/C run #42834364029](https://github.com/yoonsj0305/NEUMANN/actions/runs/42834364029): exact same pretrained base, B with prior, C with latent-world LoRA. All A/B/C original target tasks `ABSTAIN_ValueError`, C actual SGD updates **0/4**. Initial model emitted JSON-fenced `[{"hypotheses": ... "query_id":"predicted observed JSON value"}]` template rather than an evidence-grounded hypothesis. [SOURCE-only one-call diagnostic #42836583910](https://github.com/yoonsj0305/NEUMANN/actions/runs/42836583910) reproduces this *without accessing any original TARGET labels*.
- [Independent first scorer #42836007493](https://github.com/yoonsj0305/NEUMANN/actions/runs/42836007493) from the unchanged frozen artifact: FOLIO A/B/C=0/4, transparent SOURCE-nearest classical 1/4; BBH causal A/B/C=0/4, classical 2/4. No learned C-only wins.
- Scientific inference: formal-world-output prerequisite blocked all gradients; symbolic latent JSON emitter was not learned reliably. Not evidence that general intelligence is impossible.

## Immutable study 2, no reused original data or worlds

- Replaced dependent-on-valid-JSON hypothesis step with directly trained language-model option scoring via `neumann1/q3_predictive_state.py`. B received same prior SOURCE history as C; only C had SGD.
- A separate, label-blind SHA-frozen original cohort excluded **all** prior train, SOURCE and TARGET original IDs and premise-story groups, in both FOLIO logical entailment and BBH causal judgment.
- [Second causal neural run #42838378641](https://github.com/yoonsj0305/NEUMANN/actions/runs/42838378641) completed both neural and independent scorer successfully. Actual **4 real SOURCE gradients**, aggregate trainable parameter absolute L1 movement **81.64392104672879** in checkpoint weight units (not FLOPs, time or proof of generalization).
- FOLIO original targets: A 0/4, B 0/4, C 0/4, classical SOURCE-nearest 3/4.
- BBH original targets: A 0/4, B 0/4, C 0/4, classical SOURCE-nearest 2/4.
- **ALL 8 RAW ANSWERS IDENTICAL ACROSS A, B and C**, despite four real C updates; FOLIO always `Uncertain`, BBH `No,Yes,Yes,Yes`. Raw diagnostic accuracy for C: FOLIO 0/4, BBH 2/4, but B/A were IDENTICAL and NONE was SOURCE-certified. Zero submitted original answers.
- Independent cross-instance SOURCE checks: A 4/16, B 4/16, C **3/16**; C was not more predictive even on this inadequate check. Aggregate per-8-target inference wall time from frozen receipts: A 157.4974 s, B 299.7084 s, C 292.6445 s on workflow CPU; does not include C training, model loading, memory or scoring, and is NOT a matched-capability total-cost or 10x claim. RAM/VRAM/J energy UNKNOWN.

## Three causal/architecture errors, not an optimizer glitch

1. **Wrong learning objective**: `PredictiveStatePolicy.learn_source()` optimizes cross-entropy over the answer labels `Yes/No` or `True/False/Unknown`. `predict()` ranks their LM token log-likelihood. NO new explanatory variable, causal structure, transformation law or learned hypothesis-revision policy is created or used. Calling ordinary hidden Transformer activations a `learned latent representation` did not turn classification into autonomous invention.
2. **SOURCE is not an intervention on the TARGET's world**: `q3q6_two_author_freeze.py` picks FOUR label-blind but DIFFERENT original story/premise groups per task: demonstration, probe, sealed, target. They can provide generic supervised prior evidence, but correctly predicting two independent author-world labels **cannot certify a causal theory for a fourth**. `source_certified=correct_source==2` was a false causal certificate; improving that rate does not show method invention.
3. **No useful behavioral transfer**: exact same eight raw outputs A=B=C, even with four nonzero gradients. B/C have longer SOURCE contexts and more inference time, but no demonstrated new capability. Plain prior-output-label learning plus random tasks cannot identify what to revise in a candidate concept or when to intervene.

Additional experimental caveat: Official FOLIO TRAIN has `Unknown` label, official VALIDATION has `Uncertain` label; although the adapter preserves both verbatim, this vocabulary discrepancy further limits naive label-level transfer. Public pretrained data overlap remains unexcluded. Classical retrieval is a transparent local comparator, NOT strongest specialist.

## Root-cause corrective code, NO new experiment

- `q3q6_two_author_freeze.py`: preserve **label-blind per-world/premise SHA linkage metadata** and explicitly set `source_target_common_world_certificate=False` for disjoint original stories.
- `q3q6_predictive_state_original.py`: `source_can_certify_target()` fails closed unless all *independently supplied* world IDs are grounded and the same and the source-target link is explicitly certified. Never turn success on unrelated cases into a causal-source certificate. This does **not** change already frozen or scored original results.
- `q3_predictive_state.py`: declare `OBSERVED_LABEL_CROSS_ENTROPY` as the actual learning objective and explicitly mark `independent_concept_invention_demonstrated=False`. Do not rebrand it as learned concept discovery.
- Tests cover that four unrelated author worlds cannot certify a target even if the model predicts both SOURCE outputs correctly, while actual same-world evidence can in principle be admitted. Existing original TARGET predictions are not rerun.
- These are **measurement/contract repairs**, not an acquired intelligent capability.

## STOP decision and retained path

**STOP further work on the predictive-state answer-label classifier as the Q3/Q6 intelligence mechanism**. Do not merge draft PR #776 into main, do not change the original evaluation scores, do not add more training examples, retries, model size, prompt templates, solver families or benchmarks just to report a win. Existing #748/#775 research remains *conditional candidate infrastructure*, not proven Q3/Q6. Keep historical artifacts/branches, Q1-Q7 unchanged.

A third new experiment would only be decision-changing if its predeclared SOURCE observations and counterexamples share an actual hidden structural/causal rule and the SAME trainable mechanism changes a **reusable hypothesis construction/revision strategy**, not just label probabilities. It must freeze independent, previously unexposed original target families, strong relevant specialist B, full evidence/learning cost, and handle failure by ABSTAIN. No third study is authorized merely to raise CI/PR count.

**Question: NO for the current two studies. Global Q3/Q6: UNPROVEN.**

다음에 내가 결정할 것: #776의 실패한 분류형 학습 경로를 STOP하고, 단일 실제 개념 구성·반증·개정 메커니즘을 설계하여 남은 실험 1회에 사용할지.
