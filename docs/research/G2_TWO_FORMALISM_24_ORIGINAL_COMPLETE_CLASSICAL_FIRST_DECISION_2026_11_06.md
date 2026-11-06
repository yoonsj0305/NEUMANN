# NEUMANN 1 | G2 complete original 24 native-headroom proof and classical-first decision

**2026-11-06. Scientific status: scoped proof closure; NO NEUMANN learned-structure / Q3 / Q4 / Q6 / Q7 success.**

## 1. Core question

The previous own-weight two-token string student made a measurable source-free generative AST composition (31.5625% exact never-trained synthetic pairs) but failed in independent public SyGuS STRING originals (1/5). Genuine cvc5 with full original grammar independently solved 8/8. Therefore repeating a neural selector or fixed AST expansion cannot prove learned-exclusive capability.

**G2 tests whether a genuinely different mathematical formalism and independently sampled original sources first reveal strong classical solver headroom.** Do not start neural training until source feasibility/unsafety and strong native solvers have been proved.

## 2. Source-blind registration before any selected original body

- Independently published SyGuS-Org 2018 source repository at `13c8deb68a873635879c9a69bc78caebd340f646`.
- [Original metadata prereg](../experiments/G2_NATIVE_RESIDUAL_24_SOURCE_METADATA_FIRST_PREREG_2026_11_06.json): **12** integer-transition inductive invariant originals (INV) + **12** 64-bit bit-vector PBE synthesis originals (BV). Actual task filenames and all 24 Git blob SHA1 source identities chosen from GitHub metadata only by a specified deterministic FNV32 filename ranking with group caps, before reading these 24 bodies.
- Two **different, not selected** pilot originals validated original source parsing. On pilot BV, real cvc5 fit 9/9 original TRAIN but a single withheld original output refuted its candidate. This was an actual PBE generalization negative, not a source parser error. A separate early verification issue using legacy `(BitVec 64)` (instead of SMT2 `(_ BitVec 64)`) was corrected before any 24-task original first. Pilot provenance and errors fixed in [source-only pilot erratum](../experiments/G2_PILOT_ONLY_BEFORE_FIRST_VERIFIER_ERRATUM_2026_11_06.json).

## 3. The immutable FIRST source-native screen

[First real two-formalism native CI #42167219443](https://github.com/yoonsj0305/NEUMANN/actions/runs/42167219443):

- Pinned original BV first JSON SHA256 `45bb7b75af101a334f1eff393483f03a3bfc017e0077405599c21cf1041c3d7b`: native cvc5 published grammar with last original PBE constraint withheld, **12/12 original TRAIN AND withheld LAST ground examples independently proven by UNSAT of a possible counterexample**. No added program or neural training.
- Pinned original INV first JSON SHA256 `df7486f738cc47aa59b3fc91569ca73ccebb53da0b06ad4892c8f74e16d96229`: cvc5 source synthesis with 12 sec/task, **7/12 universally inductive verified at original first**, **2/12 timeout**, **1/12 solver responded `infeasible`**, **2/12 first SMT verifier failed to parse old negative integer tokens `-2` / `-3`**.
- Both FIRST GitHub jobs were marked **CI failure solely due to an unbound shell logger variable AFTER both complete scientific JSON files had been written and artifacts archived**. Never rewrite or rerun these original FIRST receipts. Their SHA-pinned independent [read-only audit #42167502277](https://github.com/yoonsj0305/NEUMANN/actions/runs/42167502277) PASS.
- `unknown`, timeout, `infeasible`, and source parsing failure are distinguished from a proved valid program.

### Post-FIRST independent error correction, never student training

[Two original legacy integer literal reproofs #42167853857](https://github.com/yoonsj0305/NEUMANN/actions/runs/42167853857) PASS. The exact native first candidate SHA for `minor1.sl` and `minor2.sl` was preserved. A separate original Git-blob verifier changed only the legacy integer token representation from `-N` to standard SMT2 unary `(- N)` in original formula declarations, then proved initiation, inductiveness and safety **3/3 UNSAT for both**. Mutated always-false invariants were rejected. Native cvc5 source-original proofs therefore **9/12**; the two timeouts and one `infeasible` remained.

### The essential mathematical result: all three remaining originals resolved

[Fixed-before-proof analytic hypotheses](../experiments/G2_POSTFIRST_THREE_SOURCE_ANALYTIC_PROOFS_CONTRACT_2026_11_06.json) were **constructed by the assistant after inspecting the original source**, not by NEUMANN weights, and checked by real SMT cvc5:

1. `fib_19.sl`: for all source states with original preconditions `n≥0, m≥0, m<n`, propose `0≤x≤n` and `y = max(x,m)` encoded as `ite (x≤m) (y=m) (y=x)`. **Initiation, induction, safety each UNSAT of counterexample**. In particular at termination `x=n`, so `y=n`.
2. `gcnr_tacas08.sl`: `w=x`, `z=10w`, `x≥0`, and `x≤y≤100x`. The third transition branch requiring `y>10w` and `z≥100x` cannot fire under this invariant. The two remaining increment branches preserve the linear cone, giving original safety `x≥4→y>2`. **All three universal obligations UNSAT**.
3. `jmbl_matrix2.sl`: original initial `(m,a,j,k)=(0,0,0,0)` and next `(m!,a!,j!,k!)=(1,1,0,1)` satisfy **Pre ∧ Trans ∧ ¬Post**, as independently proved SAT. A deliberately altered next state was rejected by UNSAT. Therefore this exact source problem is **unsafe in one step** and cannot have a simultaneously inductive and safe invariant.

[Mathematical source proof #42168295110](https://github.com/yoonsj0305/NEUMANN/actions/runs/42168295110): **all 3/3 scoped math hypotheses PASS**, no synthesis rerun. The first cvc5 12-second timeouts are failures of that search configuration, NOT evidence of source unsolvability or first hand-authored models being more general.

## 4. The necessary stronger classical competitor: Z3 Spacer

A SECOND, independently implemented classical verification algorithm was then tested on all SAME opened original INV12, with exact original source SHA, at up to 15 sec/task. Source parser/toolchain errors from unsupported Z3 `:fixedpoint.engine` and then a Python syntax mistake were caught on *synthetic-only preflight*, before this alternate solver opened original 12. The final corrected version uses Z3's native Horn semantics:

[
\mathrm{Pre}(s)\Rightarrow I(s),\quad I(s)\land\mathrm{Trans}(s,s')\Rightarrow I(s'),\quad I(s)\land\neg\mathrm{Post}(s)\Rightarrow\mathrm{Bad}.
]

With query `Bad`, **UNSAT** certifies safe, **SAT** identifies a reachable safety failure. This does NOT require manually supplying an invariant or using NEUMANN weights.

[Actual successful native classical Z3 Spacer #42169011956](https://github.com/yoonsj0305/NEUMANN/actions/runs/42169011956) returned:

- **11/11 actual safe originals UNSAT**, and **1/1 provably unsafe original SAT**, agreeing with separate per-original explicit invariant/counterexample evidence. No UNKNOWN, timeout or unparseable source.
- Native Z3 observed process runtime `fib_19.sl` **39.887 ms** and `gcnr_tacas08.sl` **984.888 ms**, compared with real cvc5 12-second per-case timeout. These are **separate existing solvers**; model generation/solver setup/human reasoning not a common all-in cost. Never claim a new NEUMANN 10×.
- Original Z3 receipt SHA256 `b1a22013aae9e2effc04dff9581de7c3200e8829a09b3adcbfd9ff76e1180414`.

### Combined result

| Original formalism | Native specialist and independent original results | Ultimate source-level scientific conclusion |
|---|---|---|
| 12 BV synthesis PBE | cvc5 12/12 correct on TRAIN and withheld LAST original examples | **Native classical source prediction covers 12/12** |
| 12 LIA induction invariants | cvc5 first 7 universally proven + 2 independently rechecked =9; two other valid source invariants analytically proved; one one-step unsafe witness SAT | **11 safe source originals plus 1 truly unsafe** |
| 12 same LIA originals using Z3 Spacer | **11 safe UNSAT, 1 unsafe SAT**, all 12 independently matching explicit original-source evidence | **Stronger existing classical fully classifies 12/12** |

**Therefore: 24/24 original source problems classified (23 valid proofs/solutions and one mathematically unsafe). This is a native classical and source-verification result, NOT 24/24 NEUMANN neural ability.**

## 5. The recurring mistake was avoided

A researcher seeing cvc5 time out on `fib_19` and `gcnr_tacas08` could declare an exciting new learned neural headroom. That claim would be false: Z3 Spacer already resolves both using a more appropriate original mathematical representation. Likewise, retrying `jmbl_matrix2` endlessly seeks a safety invariant that **cannot exist**. This shows why the mandatory native specialist portfolio and SAT/UNSAT feasibility proof must precede model training.

**Delete all new NN or hand-grammar optimization on the 24 used originals as Q3 novelty gates.** Retain them solely as classical dispatch/source proof tests. Source-specific unmetered external LLM solutions, human-authored analytic formulas and existing native algorithms cannot be credited to the NEUMANN learned policy.

## 6. Smallest actually meaningful next original experiment

1. Freeze an **independently authored** problem family distinct from the now-opened SyGuS 2018 INV/BV and old SyGuS 2018 STRING source, with exact source blobs and *unopened validation*.
2. Execute the **strongest domain-native classical specialist portfolio first**, not one arbitrary weak search configuration. Require valid original source semantics, proof-checkable output and defensible timeout.
3. Exclude **UNSAFE/UNSAT** tasks when the target is "find a valid invariant". Count them as feasibility-classification results, not model proof failures.
4. On **confirmed bounded unsolved/expensive but feasible original residuals**, freeze the NEUMANN own-weight typed operator generator, strong same-rights GP/CEGIS, independent checker and full cost policy. Limit neural spend to this actual classical gap.
5. One immutable FIRST with no post-original retuning. Compare learned-only original witnesses over the **strongest classical baseline** with end-to-end amortized cost. If still no headroom or learned-exclusive result, STOP.

### Engineering stop states

`G1_TWO_TOKEN_STRING_AST=STOP_NATIVE_SATURATED`

`G2_BV2018_12_ORIGINALS=STOP_NATIVE_CVC5_COVERS_12OF12`

`G2_LIA_INV2018_12_ORIGINALS=STOP_NATIVE_Z3_SPACER_CLASSIFIES_12OF12`

`G2_INSOLUBLE_ORIGINAL_jmbl_matrix2=PROVEN_ONE_STEP_UNSAFE`

`G2_CLASSICAL_NATIVE_DISPATCH=KEEP_AS_BASELINE_NOT_NOVEL_AI`

`Q3/Q4/Q6/Q7=OPEN`.

No new ARC public evaluation IDs consumed; the global ledger continues to reserve the previously remaining untouched 11 IDs.

This was real multi-formalism research and strong scientific **negative filtering**. It is not a frontier learned-discovery quantum jump. The real step forward is avoiding an entire second cycle of wasting training on source problems already settled by stronger classical methods.
