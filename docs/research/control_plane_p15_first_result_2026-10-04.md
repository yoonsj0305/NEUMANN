# P1.5 first actual typed-sketch result — retained FAIL

Date: 2026-10-04

## Immutable evidence

- archive: `NEUMANN_P15_FIRST_EVIDENCE.zip`
- bytes: **39,438**
- SHA-256: `4e252ab6a67c0988d31fb148647ef7124b2543b5f52abfd84987b3a164ffea5d`
- ZIP members: **27**
- unsafe paths: none
- duplicate members: none
- symlinks: none
- ZIP CRC: valid
- every `archive_manifest.json` member byte count and SHA-256: valid
- no replacement attempt

Frozen identity:

- source head: `26e40447c23e9820197d03edeee52415fe00bee7`
- merged P1.5 main before result: `3886911214971f78ae134045abb9591640bc8c5a`
- bootstrap SHA-256: `441b8bc28a6f5522dcf79e143569cb1f15c79fc2c341051a3b977fc55e8820df`
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
`/NEUMANN 1/Evidence/NEUMANN_P15_FIRST_EVIDENCE.zip`.

## Frozen result

The first actual P1.5 study completed all eight registered obligations and the independent model-free replay passed.

```
study status = COMPLETE
observations = 8/8
P1.5 verdict = FAIL
reason = SEMANTIC_PATH_CAPABILITY_FAILURE

raw semantic accepted = 4/8
raw arithmetic accepted = 4/4
raw CSP accepted = 0/4

P2 registration admitted = false
P2 actual admitted = false
Decision 3 admitted = false
```

This is a clean capability FAIL, not an accounting, replay, identity or infrastructure failure.

## Task-level result

| task | domain | raw learned sketch | result | failure locus |
|---|---|---|---|---|
| p15d_01 | arithmetic | `START 30 /5 -2 *9` | ACCEPTED | none |
| p15d_02 | arithmetic | `START 17 +7 /3 -5/2` | ACCEPTED | none |
| p15d_03 | arithmetic | `START 19 -7 +1/4 /7` | ACCEPTED | none |
| p15d_04 | arithmetic | `START 6 *4 /8 -3/2` | ACCEPTED | none |
| p15d_05 | CSP | bare assignments + prefix relations | FAILED | strict sketch parser: unsupported CSP atom |
| p15d_06 | CSP | bare domains + infix word relations | FAILED | strict sketch parser: unsupported CSP atom |
| p15d_07 | CSP | brace domains + symbolic infix relations | FAILED | strict sketch parser: unsupported CSP atom |
| p15d_08 | CSP | brace domains + symbolic infix relations | FAILED | strict sketch parser: unsupported CSP atom |

All four arithmetic items compiled to exact nested Fraction expressions and passed the original verifier:

```
p15d_01 -> 36
p15d_02 -> 11/2
p15d_03 -> 7/4
p15d_04 -> 3/2
```

This directly removes the P1.4 failure modes that motivated P1.5 on the new opened arithmetic set: sequential operation scope is preserved, rational literals remain exact, and executable expression syntax is deterministic.

All four CSP items failed **before canonical compilation, specialist execution or original verification**. Their records have:

```
proposal = null
selected_route = null
tool_calls = 0
verifier_calls = 0
accounting_complete = true
semantic_budget_valid = true
error = ValueError: unsupported CSP atom
```

Therefore the frozen 0/4 CSP result does not show that the deterministic CSP compiler produced wrong IR. The strict P1.5 wire parser never admitted a CSP sketch.

## What Gemma actually emitted on CSP

The frozen prompt explicitly requested:

```
DOMAIN name values...
LT/LE/EQ/NE left right
```

but the model chose several alternate surface languages:

```
p15d_05
CSP
M 3
N 1
O 1
LT N M
EQ O N
END
```

```
p15d_06
CSP
I 0 1 2
J 2
K 0 1 2
L 0 1 2
I NE K
J EQ 2
K EQ L
I LT J
END
```

```
p15d_07
CSP
S {-2, -1, 0, 1}
T {-1}
S <= T
S != T
END
```

```
p15d_08
CSP
P {0,1,2,3}
Q {0,1,2,3}
R {0,1,2,3}
R = 2
P != 2
Q <= 2
P = Q
END
```

These outputs contain substantial useful CSP structure, but they violate the one frozen serialization accepted by `parse_sketch`.

The distinction matters:

1. **p15d_06–08** largely preserve the original constraint content under ordinary mathematical reading while changing notation and, in some cases, propagating fixed equalities into singleton domains/constants.
2. **p15d_05** goes further and narrows the CSP to one satisfying candidate assignment rather than preserving the full original solution set. That is not natural-language equivalence, but it may still be a useful compressed hypothesis if the original verifier later accepts the produced answer.
3. None of these observations can rescue P1.5. The registered contract required the exact P1.5 wire and all four records are immutable FAILs.

## Post-hoc semantic reading of the rejected CSP text

For diagnosis only, not admission, the four rejected CSP strings were read under the ordinary mathematical meanings of their alternate notation. A brute-force comparison against the private original obligations shows:

- `p15d_06`: equivalent original solution set after reading bare value lists as domains and infix `NE/EQ/LT` normally.
- `p15d_07`: equivalent original solution set after reading brace notation and symbolic `<=/!=`.
- `p15d_08`: equivalent original solution set after reading brace notation and equality propagation (`R=2` permits `P!=R -> P!=2`, `Q<=R -> Q<=2`).
- `p15d_05`: **not equivalent** to the full original CSP. It narrows the original two-solution set `{(3,1,1),(3,2,2)}` to the valid singleton candidate `(3,1,1)`.

Thus three rejected strings are surface variants of an equivalent CSP and the fourth is a valid solution-subset hypothesis. All four carry enough semantic content to support at least one original-valid answer under an appropriate prospectively frozen interpretation. This is useful architecture diagnosis only: P1.5's registered exact wire rejected all four, so the official result remains 0/4 CSP and FAIL.

## Scientific diagnosis

P1.5 split the previous P1.4 failure into two sharply different regimes.

### Arithmetic

```
natural language
  -> ordered semantic atoms
  -> deterministic exact compiler
  -> P1.3
  -> specialist
  -> original verifier
```

worked 4/4.

This supports the architectural move away from free-form executable IR. It does **not** yet establish fresh/general semantic capability or economic advantage.

### CSP

The new bottleneck is:

```
useful semantic content
  -> exact learned surface serialization
```

rather than canonical compiler correctness.

Requiring the neural model to reproduce a single textual wire appears to spend learned capacity on syntax that deterministic machinery can own.

The strongest first-principles interpretation is therefore:

```
semantic content != serialization
```

The model should be responsible for uncertain semantic choices. Deterministic code should own representational convention wherever possible.

A second observation is potentially more important for NEUMANN's structural-compression thesis: a useful intermediate representation need not preserve the entire original problem if the final answer is checked against the **original obligation** by an independent verifier. A narrowed candidate subproblem may be valid computational compression, but only if this is frozen prospectively and cannot become post-hoc answer repair.

## Candidate next architecture, not preregistered here

The next candidate should explicitly separate **semantic hypothesis** from **surface normalization**.

One possible P1.6 shape:

```
raw language
    ↓
bounded semantic hypothesis
    ↓
deterministic ambiguity-rejecting surface normalizer
    ↓
typed atoms
    ↓
canonical compiler
    ↓
P1.3 admission
    ↓
specialist
    ↓
original verifier
```

The normalizer may canonicalize predeclared equivalent notation classes, for example prefix/infix relation notation and brace/space domain notation. It must not infer omitted facts from the original query, repair a failed candidate, add relations, expand domains, reverse operands, or retry the model. Any semantic narrowing remains the model's charged hypothesis and is accepted only through the original verifier.

A stronger future option is constrained decoding or anchored/coded semantic choices so the model never spends probability mass on deterministic syntax at all. This should be evaluated against complete cost before adoption.

Because P1.5 outputs are now opened, they may be used only for diagnosis and architecture design, never as fresh confirmatory evidence.

## Complete measured work

- model calls: **8**
- input tokens: **1,979**
- output tokens: **261**
- summed generation time: **23,638.407 ms**
- tool calls: **4**
- verifier calls: **4**
- model startup: **97,824.440 ms**
- whole study: **419,011.278 ms**
- longest item: **33,921.563 ms**
- max accelerator allocated: **10,281,742,336 bytes**
- energy / FLOPs / money: UNKNOWN

The outer setup + runner wall was 466,826.986 ms and model-free replay completed successfully in 1,723.800 ms.

## Boundary

P1.5 first actual is permanently retained as FAIL. It is not rerun or replaced.

P2 registration remains BLOCKED.
P2 actual remains BLOCKED.
Decision 3 remains BLOCKED.
Q1-Q7 remain globally OPEN.
