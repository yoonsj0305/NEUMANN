# NEUMANN 1 · Q3O / Q3O-2 first independent external original SyGuS proof-backed Typed AST data

Date 2026-10-18 KST. **Bounded external authentic original-safety and invariant extraction positive**, **learned Q3/Q4/Q7 still OPEN**.

## Why this exists

The first Q3N Loopy 150-program typed-AST original proof audit [#39090412847](https://github.com/yoonsj0305/NEUMANN/actions/runs/39090412847) observed only **4 independently original-C proven typed positive learning examples across 3 source-origin TRAIN groups** (116 licensed original train files); six from 2 other original evaluation groups (34 licensed files). Creating more near-duplicate fragments from four source originals is not independent supervision. No model was trained.

A new **external mathematical input representation** can avoid the earlier C comment location and overly restricted original-C single-loop parser problem: exact typed SyGuS-INV pre/trans/post formulas. Chose pinned upstream `SaswatPadhi/LoopInvGen` at Git revision `6ac90265b11431c9477dfbd33e3e3380234c0499`; global repo MIT LICENSE.md Git blob `1e853cd500e1317b7c2ad0a2514b548c32c46f5e`. Individual copied competition benchmark provenance/license is a separate issue. No original benchmark or extracted invariant text is copied or redistributed.

## First two external source groups

Preregistered in `docs/research/Q3O_EXTERNAL_SYGUS_FIRST_TWO_PREREG_20261018.md`; [GitHub Actions #39091042277](https://github.com/yoonsj0305/NEUMANN/actions/runs/39091042277), **SUCCESS** as experiment execution, artifact **12122696670**:

- `benchmarks/LIA/2016.SyGuS-Comp/array.sl`, source Git blob `b1c26aaddfcbab90f2dd47b6e84faaae973be200`: original `Pre` SAT; classical SPACER reachability `BadExit UNSAT` in ~8.444ms; extracted **one** nontrivial typed invariant of 14 recorded AST nodes; original three VCs `Pre => I`, `I && Trans => I'`, `I => Post` all negations UNSAT after independent recheck. Candidate SHA256 `5261bf558d723e95add19dda2ffa74f20cb2a12ff97a75c5defb08795cf5e8fc`.
- `benchmarks/NIA/2018.CHI_InvGame/s10.desugared.sl`, source blob `f066be50786c6a41bdaf0b0e2df399c579469f3f`: solver canceled at ~5,000.499ms, no original theorem or proof-backed invariant accepted. This is a **timeout/error** not mathematical unsolvability.

## Frozen first 56-source original corpus survey

Protocol frozen before batch in `docs/research/Q3O2_EXTERNAL_SYGUS_56_PREREG_20261018.md` at commit `ba2b0622bc88f60b95551bc4d8d841ef1133b9b1`. Immutable exact upstream SHA, lexicographically FIRST **40** original LIA and FIRST **16** original NIA `.sl` problem files; no cherry-picking solved sources. Generic source-only Z3 SPACER per-benchmark BadExit timeout **2,000ms**; any successfully extracted cover must pass all **three original first-party VC refutations UNSAT**, with `Pre SAT` to exclude vacuous empty initial domains. No reference solution label or source-specific lemma supplied to solver. Both proof and source file hashes preserved. No paid models, neural forwards or benchmark sources from Q3F exposed.

[GitHub Actions first #39091298773](https://github.com/yoonsj0305/NEUMANN/actions/runs/39091298773) **SUCCESS**, immutable artifact **12122563691**:

| Original logic | Files checked | Direct source-safe SPACER UNSAT | Independently 3-VC-verified typed AST seed tasks |
|--|--:|--:|--:|
| LIA | 40 | 30 | **30** |
| NIA | 16 | 0 | **0** |
| TOTAL | **56** | **30** | **30** |

In the complete 56 first outcomes there were **30 BadExit UNSAT**, **2 BadExit SAT** original problems (not safe on mathematical SyGuS integer semantics), and **24** solver exceptions (23 `canceled`, one unsupported `div` encoding). No SAT/UNKNOWN/exception incorrectly counts as a proof. 30 accepted tasks produced **33** original-proof-backed cover variants with **29 unique formula SHA256s**, so duplicates exist and should not be inflated.

Thirty accepted original-proof cases span only **four source-family groups**, whose exact counted cases are:
- `benchmarks/LIA/2005.ICALP_PolyRank`: **2**
- `benchmarks/LIA/2013.OOPSLA_Hola`: **5**
- `benchmarks/LIA/2015.FMCAD_Acceleration`: **4**
- `benchmarks/LIA/2016.SyGuS-Comp`: **19**

There are **seven** selected original family groups in total, only four with positive verified covers; 30 source-file examples are not 30 independent groups or independent operator inventions. All sampled examples are publicly available and were actively studied in this test, hence NOT a future blind evaluation. Source-name and original pre/trans/post variable signature are verified exact by a strict typed parser, and direct solver-produced covers are independently rechecked as valid original invariants. The AST and source contents remain in external runner during proving; only receipt hashes, AST structural node count, and proof verdicts appear in GitHub artifacts.

## What this closes, and what remains

**Scientifically demonstrated:** A materially broader authentic independent-source proof-backed Typed AST data acquisition pipeline beyond Loopy C; **30 actual original SyGuS proof-carrying positive candidate tasks** from several origin groups, at CPU/no model cost, with strong classical direct SPACER baseline. This resolves the concern that every new source lacks independently verifiable structure.

**Still NOT established:** legal reuse of every competition-origin benchmark for learning, a trained model's ability to generate an AST from pre/trans/post or invent operators, cross-family blind proof generalization, superiority over the same capable SPACER, 10× complete economics, a frontier small-fail/frontier-pass. **Q1–Q7 ALL OPEN.**

**Decision:** Q3O2 first authentic source acquisition and independently checked AST proof seed mechanism is **BOUNDED POSITIVE**. Before any Q3 learned AST generalization claim, run rights/provenance and structural dedup screen; keep real original group-separated evaluation families out of training; freeze an actual learned checkpoint and typed generator; compare proof success and full cost to SPACER. Since SPACER already solves these 30 cheaply, they are supervision/controls, not evidence of learned incremental capability. Q3F two competition CHC original source texts remain unopened.

Keep PR #201 Draft until exact runner receipts are preserved and CI checked. Do not reopen these same originals to overfit after seeing their proofs.
