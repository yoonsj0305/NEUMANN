# NEUMANN 1 | Q3H: independent authentic original proofs and **LABEL-FREE classical invariant synthesis**

Date: 2026-10-18 KST. Research status **BOUNDED CLASSICAL SOURCE-CONDITIONED STRUCTURE DISCOVERY VERIFIED / GLOBAL Q1–Q7 OPEN**.

## Fixed genuine corpus and proof boundary

- Original public C program corpus Microsoft `loop-invariant-gen-experiments` at revision `91fe89245a0894ec8ad3741d85ae91ce3b552b2e`; exact ZIP and workbook Git blobs were pinned in Q3G.
- The Q3G first real neural program-to-invariant character generator was actually trained on 105 examples and tested on 32 source-group-separated cases: **0/32 exact**. Char similarity neural 0.188 vs equal-source-information retrieval 0.545. This remains a *different evaluation* and cannot be directly benchmarked against the 3 original C programs below.
- Q3H original proof auditor supports precisely scoped original C programs with one simple integer loop, original source annotations, assignments and guarded updates. It refuses unsupported effects, pointer/alias semantics or unknown expression forms; checks concrete initial validity, inductive consecution, exit safety, C signed 32-bit arithmetic range, and deliberately falsified goals. All SAT/UNKNOWN or unsupported cases are **NOT proofs**. It does not claim full unrestricted ISO C semantics, arbitrary nested loops, or an independent Frama-C implementation.

## First re-verification of *PUBLISHED* invariant annotations

[GitHub Actions #39083306080](https://github.com/yoonsj0305/NEUMANN/actions/runs/39083306080) **SUCCESS**. Three authentic programs with published labels, each original C source with its published invariant independently processed; **3/3** original init/consecution/exit and signed overflow UNSAT, deliberate false-post/empty-invariant controls each SAT. This proves correctness for these cases under the admitted C semantic subset, **not neural generation**.

Next, [GitHub Actions #39083471496](https://github.com/yoonsj0305/NEUMANN/actions/runs/39083471496) **SUCCESS** over all **150 permissively licensed** Q3G Loopy original program+invariant pairs:
- **10** full original C program proofs across **5** source groups, every 5 intended original proof conditions UNSAT, 2 mutation controls SAT.
- **135** unsupported/parser/other failures and **5** cases whose proof/control contracts were not met; neither category means the original program or published invariant is mathematically false.
- Actual proofs include loop examples from VeriMAP, InvGen, Sharma Splitter, Loops, and SV-Benchmarks. Original source and published annotation bytes were authenticated by SHA256 against pinned corpus. No Q3F CHC-COMP escrow targets opened.
- The source corpus remains public and many cases may be semantically similar; **10 passed rows != 10 independent mathematical tasks** until semantic duplicate detection. The five origin groups are not proof of cross-family neural transfer.

## More important Q3H-2: discover relations automatically *WITHOUT* seeing published invariants

Study predeclared at `research/evidence/q3h-real-source-proof-20261018/Q3H2_FREEZE_LABEL_FREE_HOUDINI.md` (commit `6723804f2b44a19404433458302eafe898c18f2a`) before the classical no-label search execution. Source files were already **opened development** cases (not blind). Source-only inputs: original C AST, original safety goal, variables, source constants, and if guards. Public Loopy label workbook **is NOT read or used by the synthesizer**.

A bounded Houdini classical source-conditioned generator proposes unary integer comparisons, pairwise variable comparisons, and guard-conditional constraints, then removes noninductive candidates. Every final proposed conjunction is independently rechecked on initial states, the unchanged original body, original exit safety and signed arithmetic; intentionally false safety goal and empty invariant return SAT.

[Actual GitHub Actions #39083882788](https://github.com/yoonsj0305/NEUMANN/actions/runs/39083882788) **SUCCESS**, artifact **12119881983**:
| Actual C program | Generated candidate formulas | Initial survivors | Final inductive conjuncts | Solver candidate checks | Candidate and proof wall |
| --- | ---: | ---: | ---: | ---: | ---: |
| `TRACER-testabs7_VeriMAP_true.c` | 27 | 13 | 10 | 61 | **58.952 ms** |
| `invgen/simple.c` | 21 | 9 | 6 | 43 | **60.886 ms** |
| `sharma_splitter/popl.c` | 98 | 62 | 34 | 308 | **330.343 ms** |

**3/3 source-only full original proofs**; every base/consecution/exit/overflow solver check UNSAT, false goal + empty invariant counterchecks SAT. Found source-specific relations include `i<=n`, `n==10`, and guards combining `y==x` with `x>50`, **without those relations being provided by published labels**. These operations are still from a fixed *generic* classical candidate grammar, not a model inventing new mathematical operators.

**Strict scientific boundary:** This result demonstrates authentic original C **source-and-goal-conditioned classical automatic invariant selection**. It does not independently establish learned model contribution, source-group-blind generalization, >10× whole-path economics, frontier-level capability, or closure of global Q3/Q4/Q7. No neural training or forward passes were used.

## Decision and next minimal work

**`Q3H_SOURCE_ONLY_CLASSICAL_INITIALIZE_INVARIANT_MECHANISM = BOUNDED_POSITIVE`.**

This is now a **nontrivial equal-information classical baseline** that any future neural structure engine must beat on comparable original programs. Stop another source-only hand-selected proof case; next scarce compute should target a learned AST mechanism that recovers structures not cheaply proposed by this classical Houdini and domain specialist, with frozen independent source groups and full proof+cost audit.

Keep PR Draft and Q1–Q7 globally OPEN. Preserve receipts and hash pinned C original sources, exclude Q3F benchmark groups from all learning.
