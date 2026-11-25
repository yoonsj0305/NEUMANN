# Stage 1 — Phase A: do the three baselines learn the in-distribution task at 1M?

The active question and pass criteria are in CLAUDE.md (branch `claude/add-claude-md`). No new architecture.

## Tasks (`tasks.py`)

| task | training | in-distribution bin | out-of-distribution bins |
|---|---|---|---|
| addition | each operand's length independent uniform 1–10 | the training distribution (binned by the longer operand, 1–10) | longer operand 11–20 / 21–30 / 31–40 |
| parity | n uniform 1–16 | 1–16 | 17–32 / 33–48 / 49–64 |
| reachability | nodes uniform 4–8 | 4–8 | 9–16 / 17–24 / 25–32 |

Details:
* Numbers are written least significant digit first.
* In an out-of-distribution addition bin, the longer operand's length is uniform in the bin and the other operand is
  uniform in 1..longer.
* Reachability uses round(1.5 n) edges, node names from a pool of 100, and balanced Y/N answers.
* The training set is N i.i.d. draws (duplicates allowed).
* Evaluation sets have fixed seeds: 1 000 in-distribution examples and 500 per out-of-distribution bin.

## Baselines (`models.py`, ~0.84–0.86M parameters, within 2.5 % of each other)

| baseline | design | parameters |
|---|---|---|
| `abacus` | decoder-only, pre-LN, NoPE + Abacus digit-position embeddings, random training offset 0..100; 4 layers, d = 128 | 856 960 |
| `looped` | shared 2-layer block (d = 176) × 4 iterations, **input injection** (embedding added before every iteration), Abacus + NoPE | 835 824 |
| `gru` | 2-layer GRU, d = 256, embedding + LayerNorm + head | 851 456 |

**Looped evaluation (declared before any run):**
* **primary result:** iterations = 4 × ceil(bin upper / training upper), i.e. 4 / 8 / 12 / 16;
* **secondary:** fixed 4 iterations, recorded as `acc_fixed4`.

## Protocol (`run.py`)

* **Training:**
  * N = 100 000, batch 64, at most 20 000 steps.
  * AdamW: lr 1e-3, betas (0.9, 0.98), weight decay 0.1, grad clip 1.0.
  * Warmup 1 000 steps, then cosine decay to 10 %.
* **Early stop:** in-distribution accuracy ≥ 99 % at two consecutive evaluations.
* **Every 1 000 steps:** exact-match accuracy per bin, cumulative training FLOPs, mean training loss and wall-clock,
  written to `results/phaseA/<run>/log.jsonl`. Each run ends with `final.json`.
* **Exact match:** one teacher-forced pass. For a causal model it is identical to greedy-decoding exact match; this
  was checked against greedy decoding.
* **FLOPs:** analytic from the executed shapes; training = 3 × forward. They agree with `torch.utils.flop_counter`
  within 0.8 % for all three baselines.
* **Interruptions:** a run cut by the session's background time limit resumes from its last checkpoint (written
  atomically every 1 000 steps). The resume is recorded in the run's log and in `results/phaseA/QUEUE_LOG.txt`.
  Finished runs are never overwritten.

## Results directories

* `results/phaseA/` — the 9 Phase A runs.
* `results/phaseA_checks/` — the 200-step pre-run checks.
* `results/pilot_0d1430e/` — the earlier pilot under the old protocol (kept, not used).
