# NEUMANN 1 | G3 independent hard residual and structural-learning root-cause decision

**2026-11-06. Status: original external challenge found; NEUMANN learned Q3 still OPEN.** 

The North Star remains **Frontier-level problem solving with minimum necessary computation**. The original scientific question is NOT whether a tiny NN can reproduce an easy SMT answer. It is whether a learned proposer can discover a **new executable, independently proved structure** on an unseen family, and reduce total compute against real strong classical native algorithms.

## 1. Last three research cycles and what actually failed

| Cycle | Exact first/reproof observation | Actual proven failure mode |
| --- | --- | --- |
| G1 own-weight two-token string AST | Synthetic reserved pair composition 31.5625%, external original source 1/5, full 225 human-coded classical 1/5; cvc5 published original grammar **8/8**, independently source-proved | **Expressivity/interface**, not neural ranking. Four of five supported originals had zero source-compatible programs in all 225; three other originals required two input strings rather than frozen unary interface. Native frontier headroom on eight opened originals ZERO. |
| G2 original SyGuS BV + integer inductive safety | Original BV 12/12 native cvc5; original INV first 7/12, after old negative numeral SMT verifier correction 9/12. Human analyst wrote two valid source invariants and one concrete unsafe transition. **Z3 Spacer** autonomously classifies all **11/11 safe** + **1/1 unsafe** from original source. | Wrong benchmark family and **choice of classical algorithm**. The apparent novel-lemma headroom was zero once domain-native CHC methods and unsafe counterexamples were included. |
| G3 independent CHC-COMP 2025 original three theory families | The *pre-open* published source filenames and git blobs were frozen before first: 8 LIA-Lin, 8 LIA-Lin-Arrays, 8 ADT-LIA. Original first Z3 returns **9/24** claims in 15 s, **15/24** no grounded result. All 9 match competition author-declared expected verdict, independently corroborated without original rerun; original 24-byte first frozen. | Now real **resource-bounded classical solver residual** exists. But LIA 7/8 failures were already solved by competition engines and by modern Eldarica/Golem in 3/7 additional cases. ADT 8/8 are ordinary solver-covered. **All eight array originals** genuinely belonged to the 2025 competition's LIA-Lin-Arrays .set with absent expected_verdict; source README says this means no tool returned a successful answer in 2025. **Not** a proof of unprovability and labels are not proof objects. |

### G3 immutable source and native evidence

- The 24 source identities are in `docs/experiments/G3_2025_CHCCOMP_24_FIRST_METADATA_PREREG_2026_11_06.json`. The original manifest contains ONE 38/40-hex Git blob transcription typo; the source-free prereg check correctly FAILed and the exact single correction is retained in `docs/experiments/G3_SOURCEFREE_PREOPEN_ONE_GIT_BLOB_ERRATUM_2026_11_06.json`. **No original source was read before freezing/correcting metadata.** Original source ids/denominator unchanged.
- [Native original FIRST GitHub CI #42174775254](https://github.com/yoonsj0305/NEUMANN/actions/runs/42174775254). Raw result SHA256: `LIA c4529472973dc7e102e3b755ff866ccac5f285a9d7206488d65dd054f5b41535`; `Arrays 47d2776afe699cccab8dc6d6e4b4f06707522f61e8d3d079c478c5614ed5f8c8`; `ADT 84e35263eb08153776ccb1fb6ae97a1a76b82b8ca8959fd8b6502987474c6376`.
- [Independent 2025 official metadata/source audit #42175491787](https://github.com/yoonsj0305/NEUMANN/actions/runs/42175491787) PASS: all **24** original Git blob hashes verified against source; all 24 in official competition .set; 16 published labels (10 SAT, 6 UNSAT); Z3 first agrees with the label in **all nine** cases where Z3 reported verdict; all eight array original labels absent. Published README: https://github.com/chc-comp/chc-comp25-benchmarks.
- The competing 2025 event included Eldarica 2.2, Golem 0.7.1 and other real CHC tools. The absence of an official verdict is **historical "not solved in that contest"**, not all-algorithms impossibility.
- [Current Eldarica 2.3 SHA pinned / Golem 0.9.0 sourcefree gate #42176098022](https://github.com/yoonsj0305/NEUMANN/actions/runs/42176098022): both independently SAT on safe and UNSAT on unsafe Horn controls. Eldarica asset SHA256 `6815742c34e92d26b379006029eeeb1877757947206b5af9c2f7ff61a5e9440d`; Golem asset SHA256 `8209e804c6d4870e52d8d53b605a19145309445bffbd7e89f3ab4db31afdc490`.
- [Post-first current specialist actual original #42176459753](https://github.com/yoonsj0305/NEUMANN/actions/runs/42176459753): Eldarica 2.3 default on exact **eight arrays returns eight TIMEOUT**, 0 grounded verdict (process elapsed ~22 s each, budget declared 20 s with timeout wrapper +2 s). On seven known-label LIA unresolved by original Z3, Eldarica or Golem now reports SAT on **three**, while four remain unknown/timeouts under this cap. Each printed SAT is a native solver **claim** corroborated by official historic labels; no learned model.
- [Additional new-Z3 source run #42176390173](https://github.com/yoonsj0305/NEUMANN/actions/runs/42176390173) on the same eight arrays returned **eight UNKNOWN** under 15s wall cap; not a learned solution or a universal failure of Z3.

## 2. One controlled quantified array hypothesis was falsified *before* original access

Array property verification is qualitatively different from scalar LIA: to maintain a frame/copy relationship for a dynamically indexed array, a potential invariant may require statements such as

[
\forall i,\quad (0\le i< n)\Rightarrow \operatorname{select}(A,i)=\operatorname{select}(B,i).
]

This is an **example of a possible relational invariant family**, not a certificate for the 2025 original sources or an invented neural lemma. A static integer ranker cannot express it if the typed grammar lacks array sorts, quantified index binders, and relation predicates.

Before touching any selected original, we froze one algorithm-level hypothesis for Eldarica 2.3 `-arrayQuans:1 -verifySolutions` across the entire set of eight. [CI #42177295285](https://github.com/yoonsj0305/NEUMANN/actions/runs/42177295285) FAILED the mandatory source-free two-sided control: a clearly safe synthetic array CHC returned `sat`, but a deliberately unsafe counterpart returned **`unknown`** (exit 0), not the required `unsat`. All eight selected original source scores in this experiment **NOT RUN**. The original G3 8/8 default timeouts are unchanged. This flags incomplete treatment of negative cases by this fixed tactic and prevents misleading "one switch fixes all array CHCs" rhetoric. Do not flag-sweep this now-closed hypothesis until a distinct precommitted mechanism exists.

## 3. A different architecture is necessary to make genuine learned Q3 possible

**Problem redescription:** Given CHC source S with arrays and an unbounded index domain, synthesize a finite, executable, checkable relational invariant `I` or a concrete unsafe counterexample `T` such that a source-independent verification engine discharges all original proof obligations. Count total CPU/GPU time and the cost of unsuccessful candidate proofs.

**Interface-first proposal:** `S (source+declared types) -> learned typed graph generator -> candidate I=(∀i. guard(i,state) ⇒ relation(select(A,i),select(B,i),...)) -> independent SMT proof (init, transition preservation, error exclusion) -> accepted certificate or EXPLICIT UNKNOWN`. The generator can also abstain; default route is a known suitable CHC solver, with trustworthy error boundaries and no fabricated claims.

Every proposed invariant must get **three UNSAT counterexample proofs** over the original source, not just a model's confidence. Unsafe cases need **an actual source-reachable state/transition witness**. A proposed invariant with vacuous guards, malformed sorts, false implication, untrusted source token manipulation, or false mutation must not pass. Learned weights and code must be frozen before originally unopened tasks, with disjoint synthetic pretraining from published array tasks.

**Musk five-step applied:** challenge "must always run a model", DELETE model path for source-native solved tasks, simplify to a single verified typed interface, accelerate by only invoking costly proposal on proof-residual cases, automate scheduling and logging **last**.

**Degraded Mode:** native source solver success immediately returns native result and its solver provenance; native UNKNOWN + rejected generated invariant returns UNKNOWN and resource-use receipt, never "PASS". If a source model's proof checker errors, fail closed rather than switching to optimistic numeric scoring.

## 4. Crucial next untouched transfer set (already frozen but *not* opened)

`docs/experiments/G3_ARRAY_STRUCTURAL_TRANSFER_8_UNTOUCHED_RESERVED_2026_11_06.json` now lists **another eight deterministic-ranked, previously unopened** original array CHC files with Git blobs, after the first opened eight. No bodies, metadata gold or native first scores were read for those eight. They remain `NOT_RUN` by design.

**Passing this new gate would require:** frozen own-weight trained model and typed proof generator, a source-independent model-proof checker, same-language / same-rights strong classical CEGIS + native specialist comparison, untrained-weight ablation, and all-in compute. One FIRST on all eight reserved sources. No repeated tuning on the 2025 opened hard-8 as if still unseen. For genuine Q6, the same learned generator must also independently transfer to a *different mathematical FORMALISM*, not only another array problem from the same repository.

## 5. Gates, root costs and explicit scope

- **G3_BASELINE_FIRST_24_EXACT_SOURCE_PINNING = PASS**.
- **G3_Z3_FIRST_24 = 9/24 raw native claims, 15/24 resource-unknown**.
- **G3_OFFICIAL_2025_COMPETITION_LABEL_CROSSCHECK = PASS, 24/24 source member, all 9 reported claims consistent**.
- **G3_ARRAY_2025_ARCHIVE_NO_SOLVER_SUCCESS = 8/8 historic unlabeled**, not a proof of hard unsolvability.
- **G3_ELDARICA_2.3_ARRAY_8_DEFAULT = 0/8 grounded within ~22s process timeout**.
- **G3_ONE_INDEX_QUANTIFIER_SOURCEFREE = FAIL (unsafe UNKNOWN); selected original tests 0**.
- **G3_OWN_WEIGHT_ARRAY_LEARNED_STRUCTURE = NOT RUN**, next model architecture still needs implementation and verification.
- **Q3/Q4/Q6/Q7 remain OPEN.**

There is no meaningful manufacturing `Idiot Index = finished product cost / raw materials cost` for software-only theorem proving. An analogous but **not interchangeable** compute efficiency signal is `(total amortized trained-system cost) / (total specialized native solver cost)`, which remains **NOT METERED** for a valid learned G3 comparison. Raw solver process wall time cannot prove the all-in 10× North Star by itself.

**Stop list:** No more P44/P45 one-seed fixed-H rankers, no G1 two-token string AST sweeps, no G2 opened 24 as learned-only capability test, no treating Z3-only timeouts as frontier proof, no single native flag sweeps after failed source-free controls. Invest next ONLY in a *trained executable relational structure proposal* plus *independent original certificate* and *frozen unseen different-author/formalism transfer*.
