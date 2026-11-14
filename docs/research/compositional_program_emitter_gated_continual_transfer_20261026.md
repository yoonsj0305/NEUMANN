# NEUMANN 1 — Compositional program-emitter learning and safe continual transfer (2026-10-26)

**SCOPE**: Actual CPU Torch neural learning, all tasks assistant-authored synthetic arithmetic programs. Strong classical dominates. Existing research branch only; NO new RC or PR, Q1–Q7 globally OPEN.

## Frozen FIRST learning study

Frozen first source `open_rewrite.py` SHA256 `f466ff88de62baffef1c9df0f09a2fd1deb6dcc537afcc2cc1bcfc795dee79c2`, prereg `PREREGISTRATION.md` SHA256 `cbad7806bea177545c5b9a22249f85254f177f99e8050b2f08ca7cf3f6f24f23`. FIRST results SHA256 `c8a8685a527c3a6fb48a66be75d0fee8526b62696b48817ba0a80335f42c7638`, full first predictions SHA256 `8419c6a12bf77a3c83eaf931e9d6874277ef535305fb609ab7fe3030ab8704e2`; actual model checkpoint SHA256 `dce60df8d91db74c5f11114d9cc4d5229f2cfbee0e38b953d1ce294fe43ba072`.

An autoregressive GRU predicts a **variable-length sequence of 1–3 executable unary operator tokens** (not a closed prewritten full-program class). Full semantics of TEN primitive unary operators `add1,sub1,add2,mul2,half,square,abs,relu,neg,cube` entirely HUMAN supplied. 9 source IO points and 9 future heldout numeric x's. Training: 321 source-function-unique canonical programs, testing 110 disjoint SOURCE-function signatures, each requiring 3 tokens. Three seeds 3,7,11, teacher-forced supervised training 450 Adam steps. B same init/steps/architecture with labels randomly permuted across 321 tasks; not RL reward-shuffled. A beam10 self-proposes token sequences; exact source execution verified, prediction disagreement HOLD. All first frozen results after source code freeze:

| Mode | Independent task exact /110 | Wrong | HOLD |
|--|--:|--:|--:|
| A ownweight trained composition emitter, seeds 3/7/11 | **75,76,79** | 0 | 35,34,31 |
| B shuffled-target neural emitter, seeds 3/7/11 | **0,0,0** | 0 | 110 |
| C exhaustive full same-rights CLASSICAL grammar synthesis | **110** | 0 | 0 |

Independent arithmetic implementation checked all **431** canonical source-function programs and all 75 first-model accepted predictions; original model checkpoint restored and reproduced **110/110 first statuses**. C compiled grammar 431 unique signatures in **~8ms CPU** and completed source lookups for 110 tasks median **~0.9ms** (21 repeats). A used **~1.4–1.5s CPU supervised training + ~208–228ms inference/110**, overwhelmingly inferior total runtime/solving to C. All output primitive semantics are provided; model only recombines them. No novel underlying operator, no strong-classical marginal gain, no cross-domain transfer or frontier 10x claims.

One first CLI **print-only bug**: after evidence files are created, original `open_rewrite.py` standalone launcher calls a baseline grade helper lacking `first_match` and raises a KeyError. This failure was preserved in first source and was corrected ONLY by standalone `verify_first.py` independent baseline evaluator; NEVER silently amend original code SHA. Original A/B first evidence and checkpoint remain intact. `reproduce_training.py` reran full three seeds and matched results after the fact, without overwriting first files.

## Post-FIRST exploration: using actual verified failures to learn

First 40 tasks of same already-scored 110 were allocated to new experience training. ONLY 13,15,13 originally HOLD tasks across seeds were paired with an exact SOURCE-fitted classical program (also verified on synthetic future examples). Each is an independent SOURCE-function signature but same synthetic generating algebra; 80 original training examples used for rehearsal. New teacher A receives these verified programs, B receives identical prior pretrained model/rehearsal with ONLY the NEW teacher labels permuted. 200 additional matched Adam steps. Test ONLY remaining 70 disjoint synthetic SOURCE functions.

**Naive policy replacement produces forgetting:**
| seed | before | trained A after | trained B sham after |
|--|--:|--:|--:|
| 3 | 48/70 | 45/70 | 25/70 |
| 7 | 51/70 | 43/70 | 28/70 |
| 11 | 52/70 | 44/70 | 32/70 |

A solves 8,10,9 *formerly held* transfer problems but loses more formerly solved ones. This IS NOT continual improvement under a naive replacement. Post-first recorded `CONTINUAL_POSTFIRST.json` SHA256 `5b183280c2e793eb8f99f5d3290985c466da033e3ffd59ec2af06419ab471197`.

**Classical source-gated dual-policy selective use**: old checkpoint always keeps its formerly accepted source-verifiable proposals; updated A/B is called ONLY on old HOLD problems (22,19,18 tasks per seed). Exact future first-test outcomes:
| Seed | Previous | Normal new feedback A with gate | Shuffled new feedback B with gate | new A gains | new B gains |
|--|--:|--:|--:|--:|--:|
| 3 | 48/70 | **56/70** | 49/70 | 8 | 1 |
| 7 | 51/70 | **61/70** | 55/70 | 10 | 4 |
| 11 | 52/70 | **61/70** | 58/70 | 9 | 6 |

Saved `DUAL_GATE_POSTFIRST.json` SHA256 `a98b5505ad8d03969c201cd72eb86b01e92cda15c3130ee8e93ca411c1b2db1f`. Updated A Stage2 CPU train **650–715ms**, selective failure-only inference **39–50ms** (plus the original pretrained checkpoint and normal first call). Classical C does **70/70 with lower CPU and no retraining**. New policy's base-model acceptance is only empirical source consistency, NOT a mathematical correctness proof beyond benchmark. The continual split is POST-FIRST selection of the previous original synthetic test cohort, **not independently sealed new data**; potential tuning optimism not ruled out.

## Precisely what counts as achievement

Locally supported: a trained neural model can learn to emit previously unseen complete 3-token expression sequences within supplied grammar, and genuine verified correction programs can change learned weights so that a safe old-policy gate gains new task competence on other synthetic equations. The direct complete-policy model forgets, so the gate is mechanistically relevant in this toy setting.

**NOT proven**: new base semantic primitive invention, natural-language/ARC/MS PROSE real transfer, full AI frontier, strong classical Pareto win, constant-time meta-learning, training data/energy/memory/teacher procurement costs, general long-term safety. The prime Q3/Q4/Q5 claims and global Q1–Q7 are OPEN. Model policy can be useful only if it beats STRONG classic C at quality or normalized all-in cost on new independently authored domains. Otherwise a cheap classical learner is preferable.

## Complete executable reproducibility
Current-conversation artifact `NEUMANN1_COMPOSITIONAL_EXPERIENCE_GATED_TRANSFER_20261026.zip`, SHA256 **`2d7649b9521f1fe4cb697d6d3a3806be8e3d32499999501f4f058ec68b6b34a8`**, 18 files, ZIP CRC PASS. Entire runnable Torch source, first and postfirst JSON, real Torch checkpoint, independent arithmetic reference and test suite, integrity manifest. Fresh clean extraction `bash REPRODUCE.sh`: **17/17 SHA256**, **7/7 pytest**, **431 independent source arithmetic checks**, **110 checkpoint first-score replays**. Additionally `python reproduce_training.py` reproduced all 3 paired A/B first full training outcomes. Full implementation is in ZIP; this GitHub research note does not pretend to contain it.

Decision: *Keep strong classical-first*. Restrict learned policy updates to previously source-HOLD slots to prevent overwriting existing work, and require independent future task, strongest same-rights C, sham B, data/oracle all-in compute, and primitive innovation before saying NEUMANN self-invents semantics.
