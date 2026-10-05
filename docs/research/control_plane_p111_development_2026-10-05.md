# P1.11 fresh opened-development preregistration

Date: 2026-10-05

P1.10 remains immutable INCOMPLETE / KeyboardInterrupt. No P1.10 score is reused.

P1.11 moves the residual semantic ambiguity from a 5.1B generative next-token controller to a frozen 22,713,728-parameter sentence-semantic micro-executor. This document freezes the first actual development protocol before any P1.11 pretrained-model score is observed.

## Fresh development set

Twelve newly authored CSP obligations are registered. Candidate counts are:

`2 / 3 / 4 / 2 / 3 / 4 / 3 / 2 / 3 / 4 / 3 / 2`.

Every candidate must remain SAT after deterministic feasibility, so the solver cannot reveal the intended semantic binding.

The public semantic instructions span replication, compilers, refrigeration, cryptographic verification, scheduling, sensor fusion, power systems, networking, fluid control, linking, robot localization and braking.

The target semantic phrase has zero exact content-token overlap with every candidate role description in all 12 tasks under the frozen lexical anti-triviality tokenizer. Therefore a raw exact-token overlap matcher must abstain on all 12. This is a construction control, not a strong semantic baseline.

## Frozen learned path

For every ambiguous item:

1. deterministic source extraction,
2. deterministic feasibility pruning,
3. derive Semantic Role IR containing only target role + eligible source-bound role descriptions,
4. one batched forward through frozen `sentence-transformers/all-MiniLM-L6-v2`,
5. attention-mask mean pooling,
6. L2 normalization,
7. cosine score against each candidate,
8. require top cosine >= 0 and top-vs-second margin > 0.05,
9. reattach selected source entity deterministically,
10. exact compiler + cached specialist witness + independent original verifier.

No generation, retry, training, hidden answer, full query, numeric literal, domain, CSP relation, candidate atom or solver witness enters the encoder.

## Runtime identity and complete cost

Actual runtime is the Tesla T4 environment to keep hardware class comparable to the retained Gemma control-plane experiments. The model runs in float32. The exact Hugging Face revision is frozen before scoring. Bootstrap acquires only the registered model/tokenizer files, records bytes and SHA-256 for every acquired artifact, then the timed study loads from that local snapshot with network disabled for model loading.

The timed study charges local model startup, tokenization, attempted forward, pooling, cosine selection, deterministic compilation, execution and verification. Bootstrap clone/dependency install/model download/archive packaging/replay remain separately timed setup/evidence operations and are not hidden inside the study wall.

Energy, FLOPs and money remain UNKNOWN unless actually measured. Parameter count is not substituted for any of them.

## Gate

PASS requires exactly 12 observations, >=9 independently accepted outputs, exactly 12 model calls, exactly 12 neural forwards, zero generation, exactly 35 feasibility probes, 12/12 complete selector receipts, lexical anti-triviality unique selections=0, selector <=10 s/item, complete item <=15 s and whole study <=240 s.

A PASS is only `OPENED_P111_MICROEXECUTOR_DIAGNOSTIC_ONLY`. It does not register fresh validation, admit P2 or Decision3, close Q1-Q7, or establish overwhelming/category-changing advantage.
