# Stage 1 / week 1 — length-generalisation baselines (harness)

Active question (CLAUDE.md): learning curves of strong Transformer baselines on length-generalisation tasks. No new
architecture.

* `tasks.py` — addition, multiplication, sorting, parity, graph reachability.
  * Numbers are written least significant digit first.
  * Train on n = 1..L. Evaluate at exactly n = L, 2L, 3L, 4L; arithmetic operands are exactly n digits at
    evaluation.
  * L = addition 10, multiplication 5, sorting 8 numbers, parity 16 bits, reachability 8 nodes (not fixed by the
    spec; a question for the design chat).
* `models.py` — the two baselines.
  * `abacus`: decoder-only, pre-LN, NoPE + Abacus digit-position embeddings with a random training offset of 0..100.
  * `looped`: one shared 2-layer block × 4 iterations with input injection, plus Abacus + NoPE. Evaluated with 4
    iterations and with iterations × (eval length / L).
  * Scales: about 0.86M / 10M / 48M parameters.
* `run.py` — one run: train, then evaluate (greedy exact match), recording accuracy per length, training and
  inference FLOPs, wall-clock and hardware.
  * FLOPs are analytic from the executed shapes and agree with `torch.utils.flop_counter` within 0.6 %.
  * Result files are never overwritten.
* `results/` — run records. `_harness_smoke/` holds harness tests only (not results).
