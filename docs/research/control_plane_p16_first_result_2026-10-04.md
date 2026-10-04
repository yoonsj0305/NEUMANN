# P1.6 first actual semantic-surface result — retained FAIL

Date: 2026-10-04

## Immutable evidence

- archive: `NEUMANN_P16_FIRST_EVIDENCE.zip`
- bytes: **39,521**
- SHA-256: `7a217717513ddac16aa54a00e28aec62397ff2d356dbd689fe42d4952b1862d4`
- ZIP members: **27**
- unsafe paths: none
- duplicate members: none
- symlinks: none
- ZIP CRC: valid
- every `archive_manifest.json` member byte count and SHA-256: valid
- every terminal receipt SHA-256: valid
- no replacement attempt

Frozen identity:

- source head: `82581ca94fdf8f5fd0b85fe7d654c4fc8fe460c2`
- merged P1.6 main before result: `1e7acde57bdb6bf256e9e77dc3959f836eaba265`
- bootstrap SHA-256: `00de9c30c5a35716a0563d7ca79f5a4a601be4f5ce25d9f8b3173fb675849688`
- model: `google/gemma-4-E2B-it`
- revision: `3e22461f65e89153144f8adb70e3b8c2cc9845a7`
- precision: BF16
- accelerator: Tesla T4
- frozen core audit unchanged: true
- replay exit code: 0
- new training: false
- frontier calls: 0
- sealed data opened: false
- historical score reuse: false

The first evidence is retained unchanged in Library:
`/NEUMANN 1/Evidence/NEUMANN_P16_FIRST_EVIDENCE.zip`.

## Frozen result

The first actual P1.6 study completed all eight registered obligations and the model-free replay passed.

```
study status = COMPLETE
observations = 8/8
P1.6 verdict = FAIL
reason = SEMANTIC_PATH_CAPABILITY_FAILURE

raw semantic accepted = 1/8
raw arithmetic accepted = 0/4
raw CSP accepted = 1/4

P2 registration admitted = false
P2 actual admitted = false
Decision 3 admitted = false
```

This is a clean capability FAIL. It is not an accounting, identity, timeout, replay, or packaging failure.

## Task-level result

| task | domain | status | accepted | immediate failure locus |
|---|---|---|---|---|
| p16d_01 | arithmetic | FAILED | false | generated comma-separated single-line hypothesis; exact header/END framing rejected |
| p16d_02 | arithmetic | FAILED | false | same framing failure; generated content also contains a wrong/ambiguous divisor |
| p16d_03 | arithmetic | FAILED | false | generated comma-separated single-line hypothesis; exact header/END framing rejected |
| p16d_04 | arithmetic | FAILED | false | same framing failure; generated content also contains an ambiguous/wrong divisor expression |
| p16d_05 | CSP | FAILED | false | generated comma-separated single-line hypothesis; exact header/END framing rejected |
| p16d_06 | CSP | FAILED | false | generated comma-separated single-line hypothesis; exact header/END framing rejected |
| p16d_07 | CSP | FAILED | false | first line is comma-packed and followed by a candidate-assignment suffix; framing rejected |
| p16d_08 | CSP | ACCEPTED | true | normalizer -> P1.5 compiler -> P1.3 -> solver -> original verifier all succeeded |

Seven of eight failures stop in `normalize_hypothesis` with:

```
ValueError: exact hypothesis header and END required
```

They therefore have `proposal=null`, `selected_route=null`, `tool_calls=0`, and `verifier_calls=0`.

The one admitted item, p16d_08, normalized:

```
CSP
D { -3, -2, -1, 0 }
E { -3, -2, -1, 0 }
D < E
E = -1
D != -2
END
```

to the canonical P1.5 wire and produced the original-valid answer `{"D":-3,"E":-1}`.

## Why P1.6 failed

P1.6 broadened *within-line* CSP notation but still made physical line boundaries part of the learned contract. Seven Gemma outputs serialized their hypothesis primarily as a comma-delimited inline sequence:

```
ARITHMETIC, START 44, DIV 4, ADD 3, MUL 2, END
```

or:

```
CSP, A {2}, B {0, 1}, C {0, 1}, A = 2, B < A, C = B END
```

The normalizer's prospective surface classes covered brace/space domains and prefix/infix relations, but not sequence punctuation replacing line boundaries. Consequently most outputs were rejected before the new semantic-surface machinery could exercise its intended role.

This exposes a design error:

```
semantic content != token spelling != record separator
```

A deterministic surface layer should own unambiguous record delimiters and punctuation too, rather than forcing the language model to reproduce newline placement.

## Post-hoc semantic-content diagnosis, not admission

The opened outputs were inspected only to localize the next bottleneck. None of these readings changes P1.6's official 1/8 result.

### Arithmetic

A conservative punctuation/synonym normalization would expose two clearly correct ordered hypotheses:

- p16d_01: `START 44, DIV 4, ADD 3, MUL 2` -> 28, matching the original obligation.
- p16d_03: `START 7, MUL 5, SUB 11, DIV 8` -> 3, matching the original obligation.

Two are not safely recoverable by surface normalization alone:

- p16d_02 generated `SUBTRACT 5, DIVIDE 18, ADD 2/3` although the original divisor is 6. Literal ordered execution gives `5/3`, not the required `11/3`.
- p16d_04 generated `ADD 7, DIVIDE 36/9, SUBTRACT 1/4`. Treating `36/9` as the divisor gives `35/4`, not the required `15/4`. Reading it as an intermediate-state expression would require a new semantic convention, not mere punctuation normalization.

Therefore widening surface syntax alone would still leave a genuine arithmetic semantic-content problem on this opened evidence. A conservative post-hoc lower bound is arithmetic **2/4**.

### CSP

The CSP content is much stronger:

- p16d_05 proposes A={2}, B={0,1}, C={0,1}, with A=2, B<A, C=B. This contains valid original solutions.
- p16d_06 preserves the original constraints while narrowing V to {1}. It contains valid original solutions.
- p16d_07 states the original domains/relations and then adds the complete candidate H=1,J=2,K=1,L=1, which satisfies every original constraint.
- p16d_08 is the actually admitted 1/4 item and passes the original verifier.

Under a prospectively frozen deterministic sequence parser plus a clearly defined candidate-assignment suffix, all four CSP outputs contain enough information for an original-valid answer. That is architecture diagnosis only; P1.6 remains 1/4 CSP officially.

## Scientific interpretation

P1.6 shows two distinct residual failure classes.

### 1. Deterministic serialization is still leaking into neural responsibility

Comma versus newline is not semantic reasoning. The normalizer should not demand one record separator if a bounded, ambiguity-rejecting tokenizer can deterministically recover the same atom sequence.

### 2. Free generative semantic operands still hallucinate or collapse state

Even after surface syntax is removed, p16d_02 and p16d_04 show that a model writing numeric operands can replace a requested operand with an intermediate value/expression.

The next architecture should therefore not be just “accept more punctuation.” That would fix the easiest failures but not the arithmetic domain floor.

A stronger first-principles candidate is to separate **evidence extraction** from **semantic choice**:

```
raw obligation
    ↓
deterministic literal/entity/operator candidate extraction
    ↓
bounded typed semantic choice over extracted candidates
    ↓
canonical compiler
    ↓
P1.3 admission
    ↓
specialist
    ↓
original verifier
```

Numbers and variable names already present in the obligation should be copied or referenced by deterministic span identity rather than regenerated from scratch. Neural computation should only resolve genuinely uncertain semantic choices. If the extracted structure admits a unique safe interpretation, a zero-neural fast path is preferable. Ambiguous cases should use a bounded coded/typed selector rather than free-form operand generation.

Any such P1.7 must use new opened development data and be preregistered before model scores. P1.6 outputs are now diagnostic-only.

## Complete measured work

- model calls: **8**
- input tokens: **2,375**
- output tokens: **314**
- summed generation time: **27,533.482 ms**
- tool calls: **1**
- verifier calls: **1**
- model startup: **94,641.527 ms**
- whole study: **399,712.332 ms**
- longest item: **33,442.420 ms**
- max accelerator allocated: **10,290,313,728 bytes**
- outer launcher/setup/runner wall: **450,195.023 ms**
- model-free replay: completed successfully, exit code 0
- energy / FLOPs / money: UNKNOWN

## Minor retained metadata defect

The frozen `decision.next` string says `RETAIN_FIRST_P15_FAILURE_AND_DIAGNOSE`. This is a stale label inherited from P1.5 code. It does not affect the verdict, thresholds, evidence, replay, admission flags, or task results. The immutable P1.6 evidence is not edited to correct the label.

## Boundary

P1.6 first actual is permanently retained as FAIL. It is not rerun or replaced.

P2 registration remains BLOCKED.
P2 actual remains BLOCKED.
Decision 3 remains BLOCKED.
Q1-Q7 remain globally OPEN.
