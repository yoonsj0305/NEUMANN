# G1 | Postfirst classical comma name-swap specialist for the last string original, two independent verifiers · 2026-10-28

**This is POST-FIRST after original source was opened and after compatibility-normalized cvc5 1.4.2 reached 12s CPU timeout on `lib/PBE_SLIA_Track/euphony/get-last-name-from-name-with-comma.sl`. It is NOT a new learned NEUMANN discovery, not a blind score and not a fair same-task synthesis-runtime speedup.** Original official `SyGuS-Org/benchmarks` pinned `13c8deb68a873635879c9a69bc78caebd340f646`; original 16 FIRST SHA `7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c`; postfirst actual 4-grammar translation report SHA `0f0733023cc3528040640b93b7b91ef536f95eebdd5c989ac1b3d258b23c2d8f` (3/4 native all-original PBE examples verified, this one actual timeout). Here the task is a standard reversing two comma-separated name fragments, and this specialist program was selected after reading the source examples.

**Frozen explicit permitted original-grammar AST before formal checking:**
```
(define-fun f ((_arg_0 String)) String
 (str.++
  (str.substr _arg_0 (+ (str.indexof _arg_0 "," 0) 1) (str.len _arg_0))
  (str.++ "," (str.substr _arg_0 0 (str.indexof _arg_0 "," 0)))))
```
Original synthesis grammar permits exactly `str.++ ntString ntString`, `str.substr ntString ntInt ntInt`, `str.indexof ntString ntString ntInt`, `str.len ntString`, `+ ntInt ntInt`, input variable _arg_0, literal "," and 0/1. No novel grammar production and no hidden target labels. The original source f output grammar and same typed binder must match; all original original authored `constraint` expressions must be kept verbatim.

**Predeclared independent verification**: count original source constraints and check EVERY original source example with both Z3 4.13.3 and official native cvc5 1.4.2 on the same full original source clauses in a generated SMT-LIB2 script where only original synth-fun is replaced by this typed executable program. Assert negative conjunction: `(assert (not (and ORIGINAL_SOURCE_CLAUSES...)))`; require both solvers `unsat`. Independently check AST derivability from the original actual source grammar, not just occurrence of symbols (bottom-up old depth-less source PBE CFG). Independently also compute native concrete candidate evaluations on all source examples to guard against accidental parser mis-binding. Any parser/solver disagreement => HOLD; all candidates are produced AFTER original source opened and only prove PBE examples, not unseen ideal function. Record actual two-solver CPU and evidence SHAs.

**Research decision**: if this specialist proves all source PBE constraints, last parser→timeout issue has a verified classical postfirst solution; does not change original initial 16 cohort native cvc5 rates. Further neural training on this opened 4 task PBE set would not count independent OOD. Q1–Q7 OPEN, G1 HOLD, G2 NOT RUN, PR #616 DRAFT/main unmerged.
