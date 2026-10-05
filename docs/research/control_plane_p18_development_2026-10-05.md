# P1.8 opened development — feasibility reduction plus residual semantic selection

Date: 2026-10-05

P1.7 remains immutable **FAIL / TASK_WALL_CAP**. P1.8 P0 already established, synthetically only, that deterministic finite-CSP feasibility can soundly eliminate impossible source-bound candidates before any neural selector. This registration turns that mechanism into an opened-development experiment with two prospectively separated strata.

## Research question

P1.8 asks two different questions and must not collapse them into one score.

**A. Can public deterministic feasibility eliminate neural work when only one source-bound interpretation remains feasible?**

**B. When two or more source-bound interpretations remain feasible, can the frozen non-generative semantic selector choose the interpretation supported by explicit public linguistic evidence?**

This distinction matters because a benchmark containing only A would encode the answer into satisfiability and could not support a learned semantic-capability claim.

## Frozen opened-development set

Eight newly authored CSP obligations are registered before any P1.8 Gemma score.

### Stratum A — feasibility-reducible ambiguity

Four tasks have 2/3/4/3 source-bound pronoun candidates. Public finite constraints make exactly one candidate satisfiable. The public instruction explicitly states that the pronoun must be resolved to the jointly satisfiable interpretation.

Expected architecture:

```
raw query
-> source-bound candidate enumeration
-> deterministic bounded feasibility
-> exactly one SAT candidate
-> zero neural selection
-> exact compiler
-> cached feasibility witness
-> independent original verifier
```

All four A tasks must use zero model calls and zero neural forwards.

### Stratum B — multi-feasible public semantic cue

Four tasks again have 2/3/4/3 source-bound candidates, but deterministic feasibility leaves multiple candidates alive. Their public instructions supply lexical-semantic grounding:

- primary/spare vs backup channel
- input/buffer/output vs intermediate storage
- intake/processing/holding/output vs temporary storage
- leader/deputy/observer vs second-in-command

Candidate CSPs are authored to remain satisfiable while being mutually disjoint at the ambiguous literal, so a wrong binding cannot accidentally satisfy the independent original obligation.

The B selector sees only the original public instruction/query, deterministic source evidence and the candidate legend. It never receives the private expected candidate, semantic-grounding note, witness or original checker state.

## Query parser boundary

P1.7 query candidate construction remains unchanged. For the four prospectively registered B instructions only, P1.8 creates an instruction-normalized parser view with the **identical query string**. Numeric/entity/operator evidence and candidate IR are therefore still copied from the original query spans. The original semantic instruction is restored in the selector prompt and the original verifier remains final authority.

This is an instruction extension, not free-form query parsing.

## Residual selector

The B path uses the same frozen Gemma identity, audited one-token A/B/C/D codes, all 24 code mappings and all three batch/order modes. It remains teacher-forced and non-generative.

Because P1.7 showed that a 120 s residual-selector cap could expire after complete full-S4 work, P1.8 prospectively gives the residual selector **180 s** while retaining every forward/token/timing charge. This is not an efficiency claim. It is a development diagnostic intended to distinguish semantic selection from a known overly tight timing cutoff.

Frozen-core startup occurs once before the B stratum and is charged to whole-study time, not hidden inside the first B item wall. The full study still carries that startup cost.

## Frozen gates

The first P1.8 opened-development result is PASS only if all integrity/accounting/timing gates pass and:

- observations = exactly 8
- A tasks = exactly 4
- B tasks = exactly 4
- total accepted >= 7/8
- A accepted = exactly 4/4
- B accepted >= 3/4
- A model calls = 0
- A neural forwards = 0
- B model calls = exactly 4
- B neural forwards = exactly 144
- generated calls = 0
- deterministic feasibility calls = exactly 24
- tool calls = exactly 8
- original-verifier calls = exactly 8
- selector wall <= 180 s
- item wall <= 240 s
- whole study wall <= 1800 s
- complete known-work accounting
- frozen model identity unchanged
- model-free receipt replay reproduces the frozen verdict

A PASS is only **OPENED_P18_A_B_DIAGNOSTIC_ONLY**. It does not register or execute P2, admit Decision 3, or close any Q1-Q7 question.

## Construction controls

Before any model score:

- public/private task order and hashes are frozen
- raw-query text is deduplicated against P1.6 and P1.7 opened obligations
- each A item is proven to have exactly one SAT candidate
- each B item is proven to retain at least two SAT candidates
- exhaustive finite enumeration verifies that the expected B candidate has original-valid assignments while every wrong B candidate is disjoint from the authored original obligation
- positive/negative independent-checker controls pass
- four malformed/out-of-grammar controls stop model-free

The semantic target in B remains a human-authored lexical-semantic label grounded by the public instruction. These four development items are not a claim of irreducible language ambiguity, a lower bound on neural computation, or a general NLP benchmark. Future baselines must receive the same deterministic extraction/compiler/pruner/tools/checker access.

## First-result discipline

The first actual result is immutable whether PASS, FAIL or INCOMPLETE. No favorable rerun or replacement archive is permitted.

Completed partial neural work remains charged. Unknown work remains UNKNOWN rather than zero. The runner retains task receipts, source/runtime identity, feasibility proofs, selector receipts, original-verifier decisions, complete cost ledgers, core audit and terminal SHA pins. The separate model-free replay reconstructs semantic decisions while treating locally re-measured timing as accounting evidence rather than semantic identity.

Actual P1.8 Gemma development result at freeze: **NOT RUN**.

P1.7 is not rerun. P2 registration=false. P2 actual=false. Decision3=false. Q1-Q7 remain globally OPEN.
