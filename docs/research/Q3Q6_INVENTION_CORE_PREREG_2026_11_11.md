# NEUMANN 1 | Pre-registration: one invention core, experience → new capability (Q3) and transfer (Q6)
2026-11-11 | Written BEFORE any SOURCE or TARGET task file of the three families is opened | Global Q1–Q7 OPEN

Authority: [Frozen North Star](frozen_north_star.md), issue #745 (single learned discovery core, A/B/C contract),
and the owner's 2026-11-11 instruction to prioritise Q3 (autonomous invention) then Q6 (transfer).
This is study 3 of 3 of the #745 Q3/Q6 budget; the owner explicitly re-authorised it.

## 1. Which earlier failure cause this acts on

| Earlier failure (receipts) | Cause | What this mechanism does about it |
|---|---|---|
| P1.5/P2.5/P43–P45: fixed H, 399/400 tasks have no program | hypothesis space closed | open compositional substrate; the language itself GROWS by self-defined abstractions |
| #704/#715: 1 production from 3 programs, 16-candidate search, HumanEval 0/14 | invention too small, target mismatched | wake–sleep over hundreds of SOURCE tasks, 2×10^5–6×10^5 candidates/task, targets expressible in the same substrate |
| #670: Stitch macros 0/750 on other corpus | source/target DSL incompatible | one shared typed substrate for every family |
| #764–#776: LoRA weight updates, A=B=C | weight change ≠ new response policy | the learned state is explicit (abstractions + description-length prior) and provably changes which programs are reachable |
| ConceptARC 2026-11-11: TRAIN-fit precision 6 % | no principled choice among consistent hypotheses | minimum description length in the LEARNED language selects the hypothesis; precision is measured |
| lazy router: learning cost > savings | Q4 never amortised | invention + search cost is metered in one deterministic unit |

## 2. The core (frozen by SHA at the `train` step)

`neumann1/invention_core.py`, one mechanism, no family name or task-specific operator:

* **Substrate (human given, same for all arms):** ints, bools, int lists; `add sub mul mod div`, `eq lt not`,
  `nil cons head tail isnil range`, `if`, left/right `fold`, `map`, `filter`, constants 0–9 and generically
  detected data constants.
* **Wake:** cost-ordered bottom-up enumeration with observational equivalence; only TRAIN I/O is visible;
  budget = number of candidate programs evaluated (deterministic, machine independent).
* **Sleep (invention):** second-order anti-unification over the system's own verified programs proposes
  abstractions (holes may be functions of variables bound inside the abstraction); one is adopted only if it
  shortens programs of ≥ 2 tasks and every rewritten program still reproduces its examples.
* **Prior:** per-type symbol description lengths re-estimated from the rewritten programs (35 % uniform mix),
  per observable task signature when ≥ 8 programs exist.
* **Arms (#745):** A = substrate, untrained uniform prior. B = A + memory of all verified SOURCE programs
  (exact replay + 8 behaviourally retrieved programs as callable primitives). C = B + invented abstractions +
  learned prior. A4 = A with 4× the candidate budget (strong same-language classical baseline).
  D (integer sequences only) = classical specialist: finite differences + Berlekamp–Massey recurrences
  (`research/q3/sequence_specialist.py`).

Prior art, stated plainly: this is the DreamCoder / Stitch / Probe family of ideas. The claim under test is not
algorithmic novelty but whether NEUMANN's own core converts experience into new, transferable capability.

## 3. Development evidence (self-authored tasks only, NOT evidence)

80 list functions written by the developer (`research/q3/invention_dev_family.py`), 45 source / 35 target, used to
debug and to choose hyper-parameters. With fold-only substrate the core invented `map` from `fold`
(`foldr(cons(?f(x), acc), nil, ?xs)`) but could not bootstrap `filter` at ≤ 12 M candidates, so `map`/`filter` were
moved into the fixed substrate for all arms. Final dev run (200 k budget): A 15/35, B 26/35, C 32/35; self-invented
`sum`, `length` (= `sum(map 1 xs)`), `snoc`, `drop`, `filter >k`. These numbers are on the developer's own tasks.

## 4. Independent families, pins and splits (fixed by hash before opening)

| Family | Source (author) | Pin | Role |
|---|---|---|---|
| rule | `google/BIG-bench` `list_functions` c001–c250 (Rule, Piantadosi, Tenenbaum) | `092b196c…` | 125 SOURCE / 125 TARGET, SHA-256 order with salt `neumann-invention-first-v1` |
| dc | `ellisk42/ec` `data/list_tasks.json` (DreamCoder list tasks) | `cb0e63f5…` | all tasks TARGET only (different author, zero-shot) |
| oeis | `oeis/oeisdata` `seq/A000/*.seq` (OEIS contributors) | `2066359a…` | 250 SOURCE / 250 TARGET / 499 RESERVED-unopened, same hash order |

Registry with every git blob SHA-1: `docs/experiments/invention_first_registry.json` (built from blobless clones;
no task blob fetched). Examples: list families — search sees the first 8 examples (⌈2n/3⌉ if n < 12), the rest are
hidden tests; OEIS — index n from the %O offset, search sees the first 14 terms, the next 6 terms are hidden.
A task is **solved** only if the single returned program reproduces all TRAIN examples and all hidden tests.
Unsupported signatures (e.g. list-of-bool output) and sequences with < 20 terms stay in the denominator as failures
for every arm. SOURCE learning never reads a reference program; SOURCE hidden examples are used only to verify the
system's own programs before they enter the corpus.

Exposure disclosed: BIG-bench's README prints two example functions; earlier branches used a handful of OEIS
recurrences (#545–#557); the developer knows these public benchmarks from the literature. No PR in this repository
mentions the rule or dc task files. No language model is involved, so there is no pretraining-contamination channel.

## 5. Budgets

SOURCE: 3 wake–sleep rounds, 600 000 candidates per task per round. TARGET: 200 000 candidates per task per arm
(A4: 800 000). 4 worker processes; wall time is reported but never used for decisions.

## 6. Hypotheses and frozen decision rules (per TARGET family F)

`E_F` = tasks solved by C and by none of A, B, A4 (and D for oeis).

| ID | Rule |
|---|---|
| P1 invention | frozen core holds ≥ 5 self-invented abstractions AND ≥ 3 distinct ones occur in C-exclusive TARGET solutions |
| P2_F new capability | solved(C) > solved(A) and solved(C) > solved(B), exact two-sided McNemar p < 0.05 for C vs A and for C vs B, and E_F ≥ 5 |
| Q3 scoped | P1 and P2_rule |
| Q6a cross-author zero-shot | P2_dc (no dc task is ever used for learning) |
| Q6b cross-semantic, one core | P2_oeis with the SAME frozen core that passed on lists |
| #745 gate | Q3 scoped and Q6a and Q6b |
| P3 (reported, not gating) | solved(C) > solved(A4): classical search with 4× compute still below C |

Secondary, reported regardless: ablations on rule (C without inventions; C without learned prior); precision of
TRAIN-consistent programs per arm (Q2); search candidates on tasks both A and C solve (Q1); SOURCE investment vs
TARGET savings and break-even (Q4); tasks lost by C. Any FAIL is retained; no rerun, no retuning on opened targets.

## 7. What a PASS would and would not mean

PASS = first scoped, independent-author evidence in this project that experience is converted by NEUMANN's own
core into abstractions that (i) did not exist in the human-given substrate, (ii) solve unseen tasks that equal- and
4×-budget classical search and a memory baseline cannot, (iii) in two unrelated semantic families with one core.
It would NOT establish: invention of new substrate primitives or representations beyond typed list/integer
programs; open-ended natural-language, visual or physical domains; frontier capability (Q7 — no frontier model is
run here); complete resource accounting incl. memory/energy (Q5); global Q3/Q6. An external specialist exists only
for integer sequences; for list functions the classical comparator is same-language enumeration at 4× budget.
