# NEUMANN 1 | G3 array-fill parametric inductive proof: first-unseen and all-stage conditional generalization

**2026-11-06 | One human-designed generic proof structure generated original CHC invariants for 6 externally authored original tasks, including three source-unopened originals FIRST 3/3. A separate symbolic theorem proves the stage pattern under explicit premises. Q3/Q4/Q6/Q7 OPEN.**

## 1. The substantive change

Prior G1 string generation: the human-fixed 225 AST language did not even contain a TRAIN-fitting candidate for four of five supported original tasks, while full-source cvc5 solved all 8 of the official cohort. G2 two independent mathematical theories were completely discharged by existing strong native classical engines. Those benchmarks had **zero exclusive learned capability headroom**. G3 pre-registered 24 CHC-COMP 2025 original sources; original array CHC eight included three previously opened `standard_init4/6/7` source programs and returned **no Z3/cvc5 verdict in the 15s first**. Later published newer Z3 5.0 and third-party Eldarica 2.3 likewise timed out on those eight. [First original 24](https://github.com/yoonsj0305/NEUMANN/actions/runs/42174775254), [pinned Eldarica expert follow-up](https://github.com/yoonsj0305/NEUMANN/actions/runs/42176459753), [new Z3 follow-up](https://github.com/yoonsj0305/NEUMANN/actions/runs/42176390173).

We stopped adding more native solver variants and instead built **one generative conditional invariant construction rule**. This algorithm inspects the typed signature of CHC array loop predicates and original integer `store` writes to deduce a stage sequence of arbitrary finite length. It emits a universally quantified array relation per stage, then **independently proves every unchanged original Horn clause** by Z3 UNSAT of the clause's negation.

### Exact mathematics

For offset `n`, loop cursor `i`, length `L`, source array `A`, and consecutive store values `v_{k-1}`, `v_k`:

```text
INVARIANT(k, i, A) =
    0 <= i <= L
    ∧ ∀ j∈[0,i):   A[n+j] = v_k
    ∧ ∀ j∈[i,L):   A[n+j] = v_{k-1}

STATE UPDATE: A' = store(A, n+i, v_k), i' = i+1, guarded i<L.
HANDOFF:     i=L  =>  ∀j∈[0,L): A[n+j] = v_k.
NEXT STAGE:  i'=0 with old value v_k; the new prefix is empty.
FINAL READ:  the entire finished range equals the last written value.
```

Stage0 uses only the prefix property (initial array is unconstrained), intermediate stages use both prefix and suffix, final scan uses full-range uniformity. The typed constructor explicitly rejects unrecognized predicate interfaces, nonconsecutive store constants, unknown relations and source-language changes. This is an interface **contract**, not a generic interpreter for arbitrary programs. Crucially, no original source clause is weakened, removed or silently reclassified: all 108 original unchanged clauses were negated one by one and proved UNSAT.

## 2. Opened development vs truly uninspected source FIRST

| Original external `quic3/data` program | Research status | Stages | Direct original CHC implication UNSAT proofs | Outcome |
| --- | --- | ---: | ---: | --- |
| `standard_init4_true-unreach-call_ground_000.smt2` | OPENED development | 4 | **13/13** | PROVED |
| `standard_init6_true-unreach-call_ground_000.smt2` | OPENED development | 6 | **17/17** | PROVED |
| `standard_init7_true-unreach-call_ground_000.smt2` | OPENED development | 7 | **19/19** | PROVED |
| `standard_init5_true-unreach-call_ground_000.smt2` | **UNINSPECTED BEFORE FIRST** | 5 | **15/15** | PROVED |
| `standard_init8_true-unreach-call_ground_000.smt2` | **UNINSPECTED BEFORE FIRST** | 8 | **21/21** | PROVED |
| `standard_init9_true-unreach-call_ground_000.smt2` | **UNINSPECTED BEFORE FIRST** | 9 | **23/23** | PROVED |

- **Before original source transfer:** exact three filenames and original Git blob SHA fixed in `docs/experiments/G3_ARRAY_FILL_ONE_RULE_UNSEEN_N5_N8_N9_FIRST_PREREG_2026_11_06.json`. No test-file body was opened in planning.
- Generator source pinned **Git blob `8043d84210822f9a47d78568c25ea97cb0c175dd`**, not modified after the 3/3 opened-development proof.
- [Original developer first #42177964703](https://github.com/yoonsj0305/NEUMANN/actions/runs/42177964703): 3/3, **49/49** exact first original clauses proved. First output SHA256 `7cbf1eade93e987391205115c916f0efe1bf63cf2a19708f90595272feb9ab1b`.
- [Original malicious stage mutant #42178278127](https://github.com/yoonsj0305/NEUMANN/actions/runs/42178278127): altering stage 1's new array cell value by +17 causes **actual SAT counterexample to clause index 4**. The checker demonstrably rejects an invalid invariant; not vacuously accepting arbitrary code.
- [**Truly source-uninspected transfer FIRST #42178462607**](https://github.com/yoonsj0305/NEUMANN/actions/runs/42178462607): fixed generator unchanged, exact original Git blob source checks, first N5 15/15, N8 21/21, N9 23/23, thus **3/3 independently proved, 59/59 unchanged original Horn clauses**. Immutable first output SHA256 `86cc31057e2fe96c412d39b5ff395ecde03aef9990df0df30ec63be6091c883a`.
- **6 original sources, 108/108 first original Horn clauses proved**. The three unseen originals and the old three all were included in the official 2025 `LIA-Lin-Arrays.set`; the three first unseen ones have official YAML with **no `expected_verdict`**. Under competition publication semantics, no CHC-COMP 2025 solver was recorded as solving those selected tasks, **not** a proof of algorithmic impossibility.

## 3. Mathematical generality beyond fixed stage counts

Conditional generic proof in [#42179034835](https://github.com/yoonsj0305/NEUMANN/actions/runs/42179034835) has **zero benchmark source-file inputs**; integers `n,L,i,v,w` and the entire `Int→Int` array `A` remain symbolic:

- Stage0 unconstrained original array has vacuous empty-prefix property: UNSAT of negation.
- Finished old stage implies the next stage's initial suffix predicate: UNSAT.
- Atomic `store(A,n+i,v)`, `i'=i+1` preserves prefix and suffix for **arbitrary array state and symbolic integers**: UNSAT.
- On stage completion `i=L`, full interval equals the newly written value: UNSAT.
- Final read inside the finished interval returns the last written value: UNSAT.
- Nonempty valid invariant instance exists: SAT.
- Deliberately wrong store value `v+1` has a real counterexample: SAT.

**5/5 general lemmas UNSAT and 2/2 witness controls SAT.** All 7 generated SMT2 proof scripts were archived with SHA; theorem output SHA256 `9943b9447993ade35a823bfdfd7e9b2febac382ec8ffae361674cfa9ca4388ed`. Conditional induction over stage count is valid for any **finite number of successive stages with the required shape**, not every array problem or every CHC system.

## 4. Scientific qualification, including 10× economics

**What is actually established:** a single deterministic typed structural construction transfers from previously inspected stages to **three previously unopened external problem instances**, and a general symbolic all-stage proof establishes *why*. Existing Z3 4.8, Z3 5.0 and Eldarica 2.3 timed out on related already-opened CHC 2025 arrays with raw, uninterpreted original source. The source-blind three were **not** tuned after first evaluation.

**What is NOT established:** neural autonomous program structure discovery. Human analysts devised this conditional prefix/suffix invariant pattern after inspecting the original `standard_init4` source; there are no trained weights, meta-learning dynamics, independent novel mathematical formalism transfer or all-in training/inference amortization. The 2025 competition missing labels do not prove every future algorithm must fail. The result **does not** establish generic frontier-level Q7 or 10× **total** compute efficiency. Operational fallback should remain native classical for problem types the native solver handles.

**Next strict scientific requirement:** independent checker reproducibility and matched per-instance native 15s/20s strong solver comparison on exact three frozen unseen tasks, with source rights and wall time measured but developer rule invention cost explicitly NOT METERED. If a native solver returns a correct original verdict, record it and do not claim exclusive ability. To turn this into Q3, a separately trained policy would need to autonomously infer the schema from source and transfer it to *new independent formalism* before the evaluator opens test sources; compare equal-rights strong classical program synthesis.

Status: `G3_CLASSICAL_ONE_RULE_CHC_SOURCE_TRANSFER=PASS_SCOPED_3/3`; `G3_ARRAY_ALL_FINITE_N_CONDITIONAL_INDUCTION=PASS_SCOPED`; `G3_MUTANT_REFUTATION=PASS`; `Q3/Q4/Q6/Q7=OPEN`.
