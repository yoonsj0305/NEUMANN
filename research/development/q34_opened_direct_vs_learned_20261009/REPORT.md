# NEUMANN 1 — Q34 Opened Historical Frozen vs Deterministic 4m

**Date:** 2026-10-09 (KST)  
**Status:** `COMPLETE_OPENED_RETROSPECTIVE` (not fresh, not global gate)  
**Frozen research base:** `c182fd3f8d8b5c711415a214e899bfefe7511a0a`  
**First technical failure:** [GitHub Actions 37885771474](https://github.com/yoonsj0305/NEUMANN/actions/runs/37885771474)  
**Successful corrected first measurements:** [GitHub Actions 37885937198](https://github.com/yoonsj0305/NEUMANN/actions/runs/37885937198)  
**Raw receipts artifact:** [artifact 11596308324](https://github.com/yoonsj0305/NEUMANN/actions/runs/37885937198/artifacts/11596308324) (subject to GitHub artifact retention)  
**Runner:** [experiments/q34_opened_direct_vs_learned_20261009.py](../../experiments/q34_opened_direct_vs_learned_20261009.py)

## Why this experiment exists

The original v102 learned ranking recovered the positive optimal basis at 2m for 40/48 views, versus 18/48 for the existing deterministic residual rule. Both cover 48/48 at 4m. That prior posthoc analysis did not compare full verified deterministic 4m execution against frozen learned 2m/conditional4m on identical original sources. This newly opened retrospective comparison addresses only that missing engineering contrast.

The first new run 37885771474 aborted with `KeyError: 'scikit_learn'` before model restoration, solver execution or recorded science observations. Its run and failure artifact were preserved. Only the runtime-key spelling was corrected for run 37885937198.

## Frozen authority and matched evaluation

- Original 24 constructed LPs, two equivalent base/surface views each, 48 historical opened views, NOT 48 independent originals.
- Original v102 source gzip SHA256: `9420b10a44ca3101374a79d638cc209f1301d2b867cec8de3ebecb0f270c4202`.
- Original v102 first-evaluation gzip SHA256: `a73c21e149852013b7db19c0380ddaa36d5c2d6582051008a22942e7309cf47a`.
- Both pretrained frozen pointwise checkpoints were restored from the original authority path. All newly calculated learned rankings were required to be identical to the retained first-timed v102 rankings.
- Same runner, one-thread CPU, Python 3.12, pinned v102 NumPy/SciPy/torch/sklearn/highspy, identical 5-second deadline, original independent LP primal/dual certificate.
- `DIRECT_NATIVE`, `RESIDUAL_FIXED4M`, `EXPAND4_s100001`, `EXPAND4_s100002`. 1 warmup and 3 timed repeats in shuffled matched order per view/route: 768 recorded attempts.
- Learned amortized development training charge uses historical 10,000-query protocol; deterministic rule has no learned investment. Initial model restoration (both checkpoints) cost 1164.271192 ms and is separately disclosed, NOT charged to the table; full lifecycle/training deployment economics are unproved.
- No new model, fit, source generation, hidden-label inference, official result replacement or new global Q closure.

## Actual CPU results

| Route | Verified views | Sum of per-view median + historical amortized investment | Direct-native speedup |
| --- | ---: | ---: | ---: |
| DIRECT_NATIVE | 48/48 | 12,103.153 ms | 1.000× |
| RESIDUAL_FIXED4M | 48/48 | 4,717.802 ms | 2.565× |
| EXPAND4_s100001 | 48/48 | 2,891.449 ms | 4.186× |
| EXPAND4_s100002 | 48/48 | 2,882.594 ms | 4.199× |

Against deterministic FIXED4M, learned 100001 is 1.632× and learned 100002 is 1.637× faster in this matched cohort (ratio of summed per-view costs).

- For m64 (24 equivalent views), learned 100001/100002 adds 2.098×/2.097× over deterministic FIXED4M; all 24 views favor learned.
- For m128 (24 equivalent views), learned 100001/100002 adds 1.582×/1.587×; 16 of 24 views favor learned.
- For each checkpoint, 40/48 views, corresponding to 20/24 independent original pairs after combining the equivalent views, have lower learned cost than deterministic FIXED4M.
- Every timed route returned an accepted full original primal/dual certificate; no fallback was used.

## Interpretation and limitations

**Supported conclusion:** In the historical constructed-LP distribution, the learned shortlist ranking has a positive, measured and nontrivial marginal economic contribution against the particular v097 deterministic residual FIXED4M comparator. This strengthens local learning attribution beyond basis coverage alone. The same family also allows strong deterministic 4m savings, so learning is **not** the sole source of the earlier 4.2× result.

**NOT supported:** universal superiority to the strongest possible deterministic heuristic, general learned perspective invention, independent external validation, novel cross-domain intelligence, 10× gain, measured energy, production amortization or any Q1–Q7 global closure. The original v102 first PASS and later basis-pursuit transfer FAIL remain unchanged. These v102 originals have already been exposed to researchers; the new measurements are retrospective.

**Policy:** `HOLD_LEARNING` remains for new training in the current BP/LP adapter. Retain both frozen checkpoints and deterministic comparator as bounded mechanism evidence. For future LPS research, add the strong cheap classical FIXED4M/conditional-depth options to the native envelope before allocating training. Prioritize new goal-and-certificate-sufficient representations and unobserved problems.

## Reproducibility

Download the raw GitHub Actions artifact (`receipts.json` and `summary.json`). Validate that:

1. status is `COMPLETE_OPENED_RETROSPECTIVE` and original/archive hashes match;
2. 24 pairs, 48 equivalent views, all 4 routes and all 4 repeats yield exactly 768 unique records;
3. 48/48 per route have 3/3 accepted original certificates with no fallback;
4. per-case median plus amortized investment reproduces the published total;
5. failures and technical first-run record are not erased.

No further retuning or favorable re-run of these 48 opened views should be treated as fresh scientific evidence.
