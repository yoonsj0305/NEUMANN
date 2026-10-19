# Q3 prospective cross-stem official SyGuS FIRST gate: FAIL (immutable)

**2026-10-19 KST. First scientific gate registered in [Issue #279](https://github.com/yoonsj0305/NEUMANN/issues/279) BEFORE ORIGINAL SOURCE BODIES were inspected. Original first result: FAIL. Do not overwrite with later opened-source fixes.**

## Immutable original provenance

Public upstream SyGuS-Org/benchmarks exact commit `13c8deb68a873635879c9a69bc78caebd340f646`. Three source files selected from public GitHub directory metadata (names + Git blob SHA only) before seeing source contents: 2017 `cegar1.sl` Git blob `5265f78e457228bfb7eef931aca690ee40f53a31`, 2018 `const_true-unreach-call1.sl` Git blob `604a6aa928198724679e1fc87c66f88d7acee627` and 2018 `fib_01.sl` Git blob `bb7ec75163dd94227ee4238f9674173181893faf`. Three distinct filename stems do **not** establish independent author or algorithmic original lineages, and no independent author verification was conducted.

Frozen source-original comparator is old full **classical** Q3 source prover: Post-only then octagonal Houdini then affine branch nullspace then Z3 SPACER safety. New tested source-original method is PR #278 unchanged Pre-derived signed sparse 2-variable Houdini plus actual original Z3/cvc5 bad-condition checks, no gold. It was selected/registered without seeing these exact three source bodies.

## FIRST actual execution

[GitHub Actions #39230552099](https://github.com/yoonsj0305/NEUMANN/actions/runs/39230552099) **FAILED the preregistered scientific gate**, after successfully running and archiving all three original cases before adjudication.

| First original | Old full frozen source portfolio | New relational source-only candidate | New distinct 3VC gain |
|---|---|---|---|
| `cegar1.sl` | **SOURCE_ONLY_SPACER_UNSAT** (no explicit inductive invariant) | Candidate inductive (`initial=UNSAT`, `consecution=UNSAT`) but safety **`post=SAT`** | 0 |
| `const_true-unreach-call1.sl` | **POST_ONLY original 3VC** | New source candidate inductive but safety **`post=SAT`** | 0 |
| `fib_01.sl` | **OCTAGON_HOUDINI original 3VC** | Native original **3VC UNSAT x3**, independently cvc5 UNSAT x3 | 0, already old solved |

Original files all passed native-vs-custom SyGuS parser parity and original Pre/NotPost nonvacuity. One real positive candidate `fib_01.sl` passed strict SHA-bound original SMT independent cvc5 and negative controls, but this was **already in old classical capability**. First `cegar1` missed necessary **source-tight negative bound** to prove original Post even though its generated candidate was itself inductive. No case was removed/replaced. Failure flags were precisely `one_original_nonpost_structural_gain_over_old_frozen_portfolio=false` and `some_surviving_true_relational_two_var_atom=false`; all other seven prereg conditions true. Therefore **FIRST GLOBAL SCIENCE VERDICT = FAIL, and Q3 global OPEN**.

## Actual first receipt identity

- Archived FIRST Actions artifact ID `12175609386`, downloaded ZIP SHA256 `0705bc6c972efa246b645f7f3d25102c967668d37d4b3800f19e080e761145a2`, ZIP CRC PASS.
- Raw first 3-case JSON SHA256 `fa3ac937f78a64e7f0079e8e684cf9f426ae02b7987c70688c2d819a946598d2` (17,583 bytes). All individual original hashes/first native/cvc5 statuses independently inspected.
- Original source SHA256: cegar `32b5b66c141e12a97e55de65fd2777495e8e9b6194b2be7c51f858554455f0c0`, const `46790eeed813fa578bb046a137a269fbfb9038a1525c8b252725eb016de6f1fe`, fib `9a70599bdf06dc855e273e66169759c4ef9a8040dea823f8bc17c553187f9ac6`.

## Follow-up scope

Upon inspecting `cegar1` only **AFTER FIRST FAILURE**, the public Pre was seen as `0<=x<=2 and 0<=y<=2` and original Trans was `x'=x+2, y'=y+2`. Old witness/[-1,0,1] cutpoint grammar did not derive tight **`y-x>=-2`** from initial states, leaving goal proof SAT. [Issue #281](https://github.com/yoonsj0305/NEUMANN/issues/281) explicitly registered a separate **posthoc development-only** change to compute exact finite linear form minima under public Pre. Any success on now-opened cegar1 is NOT a retrospective prospective three-source transfer PASS, and no independent authorship claim can be made. No hyperparameter change/rerun of this original FIRST outcome.

```text
Q3_THREE_STEM_FIRST_PROSPECTIVE_TRANSFER = FAIL_IMMUTABLE
Q3_NEW_EXPLICIT_ORIGINAL_GAIN_OVER_FROZEN_PORTFOLIO = 0_OF_3
Q2_SOURCE_BOUND_Z3_AND_EXTERNAL_CVC5_NEW_POSITIVE = 1_OF_3 (fib only; old also proves)
Q3_GENERALLY_DEPLOYABLE_SOURCE_DISCOVERY = OPEN
Q3_NEURAL_LEARNED_UNIQUE_STRUCTURE = NOT TESTED
Q4_Q5_COST_EFFICIENCY = NOT PROVEN
Q7_FRONTIER_GAP = NOT EVALUATED
GLOBAL_Q1_Q7 = ALL OPEN
```

[First evidence branch PR #280](https://github.com/yoonsj0305/NEUMANN/pull/280). Historical AM1 first model FAIL, separate learned fixed-Γ and learned-transfer failures and sealed D3 remain unchanged.