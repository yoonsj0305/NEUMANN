# NEUMANN 1 | P1.12 first actual semantic judge — immutable FAIL, independent audit

Date: 2026-11-05 KST. **STOP CURRENT P1.12 MS-MARCO JUDGE** on the current P0 hypothesis. Preserve the first negative result. No model refitting, no repricing, no favorable rerun or new threshold fitted to this set.

## Actual first model result

- GitHub Actions [first actual run #42013751594](https://github.com/yoonsj0305/NEUMANN/actions/runs/42013751594) **engineering SUCCESS**, scientific **P112_LOCAL_OPENED_FAIL**.
- Previously frozen model: `cross-encoder/ms-marco-MiniLM-L6-v2` at revision `ce0834f22110de6d9222af7a7a03628121708969` (22,713,601 parameters).
- **New author-constructed opened 12-question engineering-role selection corpus**. No P1.11/P1.11.1 task scores reused. 12 CPU model forwards, no training, no generative calls.
- Exact raw-top selection: **3/12**. Preregistered best zero-model lexical comparator: **3/12** (character n-gram TF-IDF 3, word TF-IDF 0, constant first 3). Gain: **0/12**.
- Preregistered gate required >=9/12 and +2 correct over best lexical. Both primary criteria FAILED. Do not retroactively relax.
- Measured on this GitHub runner: complete study 4,065.31 ms, cold model load 3,861.78 ms, input tokens 1,195, padded tokens 1,244. Power, money, accelerator VRAM and full integrated system economy UNKNOWN.
- Immutable first report SHA-256: `67644a9a29c7ff1a3c4c66cff07207208205e956191ad3333974cc20bbb8c16a`. Uploaded as `neumann-p112-first-fresh-real-model`.

## Independent offline reproduction

- [GitHub Actions #42014454394](https://github.com/yoonsj0305/NEUMANN/actions/runs/42014454394): **PASS**.
- Reused unchanged first-model score vector, independently recomputed each unique maximum, 12 correct/wrong labels, original source-bound semantic IR, all three predetermined lexical comparator predictions and aggregate gate.
- Zero additional neural/model calls. Deliberately tampered receipt bytes rejected.
- Independent first classification: `P112_LOCAL_OPENED_FAIL`. No Q1–Q7 closure.

## Critical preregistration/protocol limitation

The original registration v1 had an incorrect author label for s03 (expected index 3 for an electrical step-down circuit, but the physically correct candidate is **buck converter** at index 0). The mistake was discovered and preserved by a separate corrected-v2 immutable file **before any pretrained model inference**. Both v1 and v2 source blob identities are retained; model actual loaded only corrected v2. Never conceal the correction or treat it as model-based tuning.

Furthermore the final corrected task labels are **not position-balanced**: indices 0/1/2/3 occur 3/6/0/3 times. A constant index-1 baseline would obtain 6/12. That number is an **explicit post-hoc diagnostic**, not a preregistered comparator and not a replacement for the immutable primary test. This dataset is too small and biased to prove general inability or future transfer. A negative gate decision is justified for **this particular frozen candidate and evaluation**, not all cross-encoders.

## Scientific interpretation and next mainline

1. The P1.11.1 bi-encoder's raw-top 6/12 failure was on DIFFERENT opened tasks. Do not compare its 6/12 numerically to P1.12's 3/12 as a controlled architecture ablation.
2. The selected MS-MARCO model is trained for passage relevance, not independent discovery of program operators. P1.12 would have selected one of already-defined candidates even if ranking succeeded. Thus it cannot establish autonomous Q3 new executable semantics by construction.
3. **STOP** current P1.12 raw MS-MARCO candidate; no margin tuning, same-task prompt sweep, no P2/Decision3 admission. Keep source identity, first fail, offline scorer, and hash intact.
4. **NEXT condition**: a genuinely discriminating original source problem set where a strongest matched classical TOOL baseline cannot already succeed, and a NEUMANN proposer produces a new independently checked typed executable program/representation not available in the baseline's hypothesis class. Equal model, tools, verifier and complete-cost budgets; untouched new-family transfer only after opened success.
5. Remain clear about control/representation: semantic ranking != structure invention. No broad problem-solving 10x, neural learning effect, frontier parity or transfer proven.

**Official verdict:** `P112_LOCAL_OPENED_FAIL / INDEPENDENT_AUDIT_PASS / GLOBAL_Q1_Q7_OPEN`.
