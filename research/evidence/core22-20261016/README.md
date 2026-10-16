# NEUMANN 1 | CORE-22 learned recursive ghost-state parameters (2026-10-16)

**Verdict: NARROW_LEARNED_TYPED_HELPER_PARAMETER_PROPOSAL / OUT_OF_DOMAIN_FAIL / CLASSICAL_EXACT_STRONGER / ALL_Q_OPEN.** CPU-only, development-only. No historical Q1–Q7 gate or prior failed receipt is changed.

## Actually implemented

A source-checked, human-restricted synthetic typed list algebra program defines fold `S` and map `M`. The frozen **13,026 parameter** PyTorch MLP generates TWO integer parameters `g0,k` of a **new auxiliary function absent from source**:

```
S([])=z
S(h::t)=a*h+c+b*S(t)
M([])=[]
M(h::t)=(p*h+q)::M(t)

G([])=g0
G(h::t)=k+b*G(t)
lemma: S(M(L))=p*S(L)+G(L)
```

The full auxiliary **grammar** and variable locations remain human designed and the multiplier `b` is copied by a classical parser. This is not an unrestricted typed AST invention, and is not the general CORE-21 whole-Horn AST encoder. The correct numeric coefficients, known to the **training-label creator** and exact symbolic baseline, are `g0=z*(1-p)` and `k=a*q+c*(1-p)`.

## Independently executed

- Training: 5,200 synthetic original-program texts, 160 epochs, CPU wall **3.655 s**, no GPU/API.
- Mathematically identical `(a,c,p,q,z)` evaluation signatures excluded from **every training b**. Entire evaluation `b=3` class withheld.
- Frozen model emitted coefficient literals sufficient for **11/12** held-out induction proofs (two isolated Z3 UNSAT certificates required). Exact algebra baseline **12/12**.
- Further `p,q` outside the training range: frozen model **4/8**, exact algebra **8/8**. Four wrong candidates rejected by SAT induction counterexamples, not silently treated as proved.
- Candidate median warm CPU: neural **0.2723 ms**, classical exact algebra **0.00449 ms**. Separate end-to-end 12-case wall including parsing + Z3: neural 0.497 s / 11 proved, exact classical 0.515 s / 12 proved. This small wall difference is not a speed advantage; training is excluded and verifier subprocess variance dominates. Classical is superior on capability and candidate compute.
- Source-syntax mutations with poisoned map nil or extra relation assertions trigger classical ABSTAIN; false mathematical base or inductive step triggers SAT. Those defenses are **not learned**.
- `pytest` 9/9 pass and independent zip extraction replay 9/9 pass.
- An initial insufficient holdout split is retained separately as historical first-pass evidence; official run excludes the mathematical signatures.

## External original and negative transfer

Pre-registered source identity before inspecting full content: CHC-COMP 2026 `ADTRem/isaplanner/goal43_000.smt2`, commit `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`, Git blob `125e17e95967b4af13f5a1de9031f0d1d533e330`. Actual GitHub source uses `HORN` rules with `takewhile`, `dropwhile`, `append`, and other relations. Frozen CORE-22 only parses two `define-fun-rec` declarations in `ALL` logic, hence **ABSTAIN_UNSUPPORTED_INPUT_DSL**. This is a GitHub-connector structural preflight, **NOT a local full-source replay or original proof**. No target-specific patch.

## Artifact and preservation

Local SHA256 verified package `NEUMANN_CORE22_LEARNED_GHOST_20261016.zip`:
`0d6cf5a6fdc9b32103a59d04bd32808521470876c6a2fd20e793b06a48d69732`.
Its 16 payload files include frozen checkpoint, source generator/parser, isolated Z3 proof checker, 12-case and 8-case receipts, 9 tests, bad-split historical evidence and full SHA256 manifest. **The GitHub repository contains this report and SHA, not the binary ZIP/model weights**; binary upload still pending separate authenticated transfer.

**Decision:** stop optimizing neural algebraic coefficients because exact algebra already solves this class cheaply. The **sole next decisive research gate** is full original-source learned typed helper-definition synthesis with unseen external family proof and matched classical, all-in cost comparison. **Q1–Q7 remain OPEN.**
