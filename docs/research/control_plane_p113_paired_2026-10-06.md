# P1.13 — paired functional-role development

P1.12's retained first study failed original verification on five of twelve
tasks. Its small compute footprint did not meet the capability requirement.
P1.13 tests whether a different learned objective plus more capacity improves
the residual functional-role decision. No previous first result is replaced.

The incumbent is the exact P1.12 MS MARCO MiniLM cross-encoder (22,713,601
parameters). The candidate is frozen `cross-encoder/nli-deberta-v3-base`, revision
`6c749ce3425cd33b46d187e45b92bbf96ee12ec7`, expected 184,424,451 parameters.
The [incumbent model card](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2)
identifies passage ranking as its training task. The
[candidate model card](https://huggingface.co/cross-encoder/nli-deberta-v3-base)
identifies SNLI/MultiNLI training and contradiction, entailment, neutral labels.
These facts motivate the hypothesis; they do not prove competence here.

Both arms share twelve newly authored role/function tasks and the same
deterministic extraction, candidate feasibility probes, source-bound witness
execution and original verifier. All 36 candidates per arm remain SAT. None of
the candidate role strings occurs in P1.11/P1.12 and all target-role exact-token
overlaps are zero. New role strings are **not** evidence of independent external
validation, unseen computational families or a Frontier Gap.

The NLI input is only the residual function and candidate role. The premise is
`The component performs this function: <target>.`; the hypothesis is
`This component is a <role>.`. Every candidate pair is processed in one batch
per task. Rank by entailment minus contradiction logit, equivalently the order
of binary entailment/contradiction softmax before floating-point saturation.
An exact top tie abstains. Scores are not calibrated confidence or a proof.
No hidden answer, CSP query, numbers, entity labels or witnesses enter the model.

The fixed diagnostic gate requires at least 9/12 original-verifier acceptances
and strictly more acceptances than the incumbent on these same tasks, with
one forward per item, no generation, selector <=10 seconds, item <=15 seconds,
and each arm including model startup <=240 seconds. Baseline runs first, then
NLI, without warmup or retries. This fixed order limits timing interpretation.

Size, pretraining and supervised objective change together, so even a paired
gain cannot causally identify the training objective alone. Each arm includes
its model startup, deterministic work, inference and verification. Setup,
artifact acquisition, subprocess and replay times are recorded separately;
packaging, GPU session allocation/idle and original training investment are
outside the measured study. Process RSS is a cumulative high-water mark.
Energy, FLOPs and money remain UNKNOWN.

The full source overlay, per-file model checksums, labels, task/reference hashes,
gates and local notebook are frozen in `Continuation/P113_PREPARATION_V1` before
the first GPU score. `P113_PREPARATION` was rejected by a model-free construction
gate because one distractor role had appeared before; it produced no model
scores and is retained as a preparation record.

Before a resource-advantage claim, a stronger direct solver and the best existing
specialist must be measured at matched capability on independent, growing
problems. This experiment is an opened development diagnostic only. P2,
Decision3 and global Q1–Q7 remain open regardless of its outcome.

## Retained first outcome

The first Tesla T4 study completed: **FAIL**, incumbent 3/12, NLI 5/12;
four paired wins and two paired losses. NLI's 184,424,451 parameters and
771,782,144 peak allocated GPU bytes were measured, versus 22,713,601 and
101,991,424 for the incumbent. The capability floor was not met, so the
candidate is not admitted. Study wall time was 30.636 seconds; measured
launcher/setup/acquisition/subprocess/replay wall time was 104.998 seconds.
The first arm paid shared library initialization, invalidating any simple
cold-start speed comparison from the per-arm totals.

First archive SHA-256:
`265c4bc939ce0cade72b97a29f79f40b9f8afef3b56cd49a440aa873d88c4f2a`.
Kaggle and local model-free replay reconstructed all 24 records and the same
FAIL. The source overlay was not changed after scoring. A separate post-run
audit wrapper turns malformed receipt type errors into NOT_EVALUATED.
Related local checks: 45 passed.

See the local workspace `Continuation/P113_FIRST/POSTMORTEM.md` for diagnosis
and the preserved evidence. Private Kaggle version 1 keeps the first outcome;
version 2 adds a read-only summary of that outcome, without another model run.
The GPU session is stopped. The next design should address functional knowledge
grounding and a demonstrably capable Direct baseline before further size scaling.
