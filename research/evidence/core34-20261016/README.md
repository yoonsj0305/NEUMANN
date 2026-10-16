# NEUMANN 1 | CORE-34: matched-space selective proof audit

**2026-10-16. DEVELOPMENT ONLY. Restricted classical result; Q1–Q7 OPEN.**

## The one question
CORE-32 reported a large reduction in proof cost but changed the hypothesis language.
Can identical candidate spaces be compared fairly, and does adding a learned component
buy anything once the strongest cheap classical solution is included?

## The executable, deliberately narrow test
This is a **synthetic** integer/list recursion, not an authentic external Horn benchmark.

Source: `F(z,nil)=z`, `F(z,cons(h,t))=h+F(z,t)`, and ordinary list concatenation.
An auxiliary lemma candidate is the full linear AST
`F(z,append(A,B)) = a*F(z,A)+b*F(0,B)+c*z+d`.

The candidate universe is **3,645** complete ASTs: `a,b,c` in `[-4,4]` and
`d` in `[-2,2]`. It is held **IDENTICAL** for exhaustive and selective search.
No neural model and no theorem-type learning are involved.

1. **Exhaustive:** attempt universal integer-polynomial induction proof for
   every candidate in the identical finite grammar.
2. **Selective:** evaluate all 3,645 candidates on the same four source-derived
   probes, then attempt independent universal induction proof only for survivors.
   Observation alone **never** authorizes a theorem.
3. **Strong direct classical baseline:** use precisely those same four probes
   to solve the four unknown coefficients with exact Fraction Gaussian elimination,
   then independently certify the result by the same induction proof.

The independent `proof` function checks symbolic base and inductive step
identities with SymPy polynomial normalization over unbounded integers.
A second closed-form coefficient check independently evaluates the result.
Mutation controls reject a previously valid lemma when the real nil base changes;
the revised problem has a separately provable new offset lemma.

## Actual local development result (single complete execution)
- 3,645 exhaustive proofs; **exactly one true auxiliary AST:** `(1,1,0,0)`.
- Four finite probes leave exactly one AST; one universal proof is still required.
- Original candidate is rejected on a poisoned nil base; a revised offset
  `(1,1,0,-1)` can be proved instead for nil offset = 1.
- `pytest` **5/5 PASS**; plus 120 deterministic finite randomized checks.

Measured on one local process, in milliseconds (not cold-start/end-to-end costs):

| Candidate policy | wall ms |
|---|---:|
| Exhaustive, same grammar | 1176.769 |
| Probe filter plus one universal proof | 1.999 |
| Exact direct classical solve plus one universal proof | 0.306 |

Five subsequent standalone runs showed medians of approximately
`1200.416/1.923/0.280 ms` respectively. These are **development timing
observations** subject to cache, machine and version effects, not universal speed
guarantees. Python initialization, solver installation, model training,
energy and real frontier compute were not included.

## Correct interpretation
**YES:** A paired, hypothesis-space-matched reduction in universal proof
count from 3,645 to 1 has been observed while preserving exact certification.
**NO:** This is not evidence of learned structure invention; the exact direct
classical method is even faster on the same task. The selective method must
NOT claim a learned advantage, frontier efficiency, external transfer,
nor closure of global Q3/Q4/Q6/Q7 or any of Q1–Q7.

This data supports the deletion principle: for this source family, **remove
the neural pathway**. The remaining hard science is not faster enumeration of
trivial linear lemmas.

## Run and independently inspect
```bash
cd research/evidence/core34-20261016
python -m pip install 'sympy==1.14.0' pytest
python -m pytest -q
python experiment.py --output receipt.json
```

## Strict next experiment (not yet demonstrated)
Freeze the whole source-and-goal input encoder, helper-language search interface,
model weights and admission verifier *before* opening an untouched authentic
external CHC **different family**. An admissible learned claim requires a new
unprovided typed helper signature plus base and recursive rules, independent
proof of the complete original source goal, and a strong exact classical
synthesizer with identical information and fully charged training/inference/
verification cost. If the classical solver already has the answer, run it first.
Fail closed on UNKNOWN and ABSTAIN when the grammar cannot express a sound lemma.

**Historical CORE-1–33 verdicts are unchanged.**
