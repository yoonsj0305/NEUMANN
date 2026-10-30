# NEUMANN 1 | POST-CONTENT two distinct grammar-legal program solutions for original external SLIA examples · 2026-10-28

**Retrospective specific original opened AFTER pre-freezing the 16 new external source names.** We inspected original `SyGuS-Org/benchmarks` pinned `13c8deb68a873635879c9a69bc78caebd340f646`, file `lib/PBE_SLIA_Track/euphony/get-first-word.sl` to design this. Thus this is NOT a blind neural G1 result, no novel original operator, and no claim the benchmark's desired real-world behavior is unique. It is a formal *under-specification information-rights counterexample*, entirely different from source-16 fixed BYTE-DSL.

Original complete provided 3 ground example constraints:
- f("The quick brown fox.") = "The"
- f("quick brown fox.") = "quick"
- f("fox") = ""

Original grammar allowed `_arg_0`, `" "`, `0`, `str.substr`, `str.indexof`, `ite`, `str.suffixof`. Precommit two EXACT original-grammar candidate ASTs prior to running any SMT check:
- **Program P1:** `(str.substr _arg_0 0 (str.indexof _arg_0 " " 0))`.
- **Program P2:** `(ite (str.suffixof " " _arg_0) _arg_0 (str.substr _arg_0 0 (str.indexof _arg_0 " " 0)))`.

For all 3 original source examples, suffix test is false, and both candidates yield identical specified output. But on **new source input `"hello "`**, P1 returns `"hello"` whereas P2 returns `"hello "`. These are **two different programs semantically satisfying all authored constraints**; candidate A does not uniquely determine a human "first-word" ideal behavior for all strings. The original source only gives 3 labeled examples and no callable *true intended function oracle* at arbitrary new inputs. It is therefore inappropriate to transfer the synthetic 8-bit "ask oracle y" policy mechanically to this source. Proposed witness input was selected AFTER inspecting the original examples; do not treat as blinded external heldout test.

**Formal independent original-source check to run:** verify original source SHA against pinned upstream; parse/check that exactly three authored `constraint` and original `synth-fun f` grammar includes all claimed AST operations. For each P1 and P2, define precisely one original signature `f((_arg_0 String))→String`, replace `synth-fun` with this program, and ask native CVC5 1.4.2 and/or independent Z3 4.13.3 **UNSAT** for the negation of the conjunction of all three source constraints. Verify witness **SAT** for `(not (= (f_P1 "hello ") (f_P2 "hello ")))` plus exact output `"hello"` vs `"hello "`. If SMT returns UNKNOWN/parser error or grammar mismatch => HOLD; no fabricated source proof. Preserve full SMT scripts and proof status.

**Scientific boundary**: This will prove multiple semantically different programs satisfy the *finite given source specification* and a new input with ambiguous implied label, not that P2 implements a good real-world text parser nor that original synthesis task is unsatisfiable. It is a testable counterexample to an unjustified unrestricted target-output oracle. G1 HOLD Q1–Q7 OPEN; PR #616 DRAFT.
