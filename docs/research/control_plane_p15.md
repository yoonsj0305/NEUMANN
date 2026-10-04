# P1.5 — Semantic sketch / typed atoms and a deterministic canonical compiler

P1.4 first actual study completed all twelve items. Its frozen verdict remains
FAIL / RAW_ACCOUNTING_INCOMPLETE, and the separately recomputed raw capability
also failed: 5/8 overall, arithmetic 2/4, CSP 3/4. Mixed typed fallback passed
4/4. PR143 retains that result and repairs only model-free replay of rejected
parsed proposals. It never repairs a generated answer or rescues P1.4.

The user-reported original first ZIP is `NEUMANN_P14_FIRST_EVIDENCE.zip`,
61736 bytes, SHA256
`7f819cd1dd26dc94ca690b4be3e2e365b7f65882900caff78e30e3e1c647af52`.
Parent main is `7b30f64efee7e4920b2752d0393bb92856d28ce8`.

## Architecture

The same frozen Gemma makes one bounded, thinking-disabled call to identify
semantic atoms. It does not generate executable expressions, domain JSON,
constraint tuples, or control-plane actions. The deterministic compiler alone
builds specialist IR and re-enters unchanged P1.3 admission before execution.

Arithmetic wire:

```text
ARITHMETIC
START 21
DIV 7
ADD 5
MUL 4
END
```

Each operation applies to the entire current accumulator. The compiler emits
`(((21/7)+5)*4)`. Bounded integer, rational and decimal **text atoms** are parsed
as exact Fraction values; `0.5` becomes `(1/2)` without passing through a binary
float. This is not permission to repair P1.4's already-rejected expression.
`0.333333` remains exactly 333333/1000000, not a guessed 1/3.

CSP wire declares finite integer domains first, then `LT/LE/EQ/NE left right`
atoms. The compiler emits canonical list relations, checks declared variables,
and enforces the existing grammar/resource limits. Unsupported text, duplicate
declarations, undeclared names and invalid domains are rejected. `ABSTAIN` is
safe but counts as unsolved. No candidate repair or model retry is permitted.

Compilation certifies syntax, exact literals and the order of the supplied
atoms. **It does not prove natural-language equivalence.** Wrong operation
order, missing facts, reversed relations and incomplete domains remain learned
semantic errors. The original obligation's independent verifier controls all
acceptance; it receives the raw original view and a separate private reference,
never a reference manufactured from the sketch.

## First opened-development registration

Eight new authored raw tasks: four sequential arithmetic and four finite CSP.
Public views contain only instruction/query; private original references and
construction witnesses never enter model, admission or executor inputs.
Normalized raw-text dedup checks the P1.4 raw catalog. This is a bounded authored
development diagnostic, not semantic novelty, external benchmark evidence,
general reasoning, fresh confirmatory validation or frontier capability.

The P1.4 mixed full-S4 mechanism and all earlier code/evidence remain unchanged.
P1.5 does not rerun it: this study isolates the newly changed raw compiler and
charges eight semantic calls, rather than repaying the prior 144 score forwards.

Model/revision/artifact/tokenizer/BF16 and original Tesla T4 runtime are fixed.
192 output tokens, 4096 context tokens, one call per item, no retries, 120s
semantic call, 180s item and 1800s complete study cap. Sources, architecture,
data hashes, ordered IDs and gates are frozen before any actual P1.5 scoring.
No model weights or actual P1.5 inference are loaded by registration/CI/replay.

The raw capability floors are unchanged: overall >=6/8 and >=3/4 in each
domain. Exact coverage/identity, complete telemetry, one call per item and
all resource caps also must pass. A completed but invalid sketch stays FAILED
with its input/output tokens and latency charged. A partial backend failure
retains an attempted call and UNKNOWN tokens; it cannot claim zero work or PASS.

## Evidence and cost

The exclusive directory retains each started marker, raw generated text/hash,
parsed atoms, compiler certificate, canonical IR, execution answer, independent
checker outcome, input/output tokens, call counts, VRAM, semantic/compile/route/
executor/verifier/item time and startup/study timing. Bootstrap setup, dependency
installation, replay and packaging are recorded separately. Python import time
and final report/terminal serialization are outside the measured study clock;
the launcher/outer stages include them. Energy/FLOPs/money remain UNKNOWN. There
is no Direct comparison or end-to-end economic/iso-capability claim here.

Model-free replay reconstructs atoms and IR from raw text, reruns unchanged
admission/specialists/original checkers and independently recomputes the gate.
Cached IR, token totals, decisions and admission flags cannot replace raw
evidence. Invalid compilation is a retained nonpass with charged completed
work, not replay corruption. Backend/telemetry failure remains nonpass.

```bash
python -m experiments.control_plane_p15_registration
python -m experiments.control_plane_p15_dev --directory NEW_EXCLUSIVE_DIRECTORY --frozen-head EXACT_TESTED_HEAD
python -m experiments.control_plane_p15_replay --directory NEW_EXCLUSIVE_DIRECTORY
```

`scripts/control_plane_p15_kaggle.py` is an import-inert first-attempt bootstrap;
the published launch cell pins its exact tested source head and SHA256. It
preserves and packages the first attempt even FAIL/INCOMPLETE, rejects output
replacement, kills/reaps an interrupted child process group, and permits
evidence-only recovery only after no child exists. Do not rerun historical
P1/P1.1/P1.2/P1.4 experiments or replace a first P1.5 attempt.

## Boundary

Actual P1.5 Gemma development run: **NOT RUN** at publication. A future PASS is
only OPENED_SKETCH_DIAGNOSTIC_ONLY. Freeze architecture and preregister another
fresh semantic validation before considering P2 registration. P2 registration,
P2 actual and Decision3 remain false; Q1-Q7 globally OPEN. Training, frontier API
and sealed data are forbidden. This compiler removes surface representation
hazards, not the learned intelligence or the need to verify semantic correctness.
