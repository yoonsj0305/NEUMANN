# CORE29: Source-only finite Horn semantics and independently checked intermediate theorem

Date 2026-10-16. DEVELOPMENT-ONLY. **Q1–Q7 OPEN. Neural forwards=0.**

## Executed
Reads exact public CHC-COMP goal52_000.smt2 (Git blob `f27b6a56e752498b2a67cb59bd739aebbb7dd179`, 2,605 bytes, SHA-256 `3db92ef5e5f890bf6fc0a61aefddd45bfe364fcd9b39653c9f542c59bcd372f5`) and automatically builds finite least-fixed-point interpretations from the actual Horn rules by type-directed generic unification, fact joins and arithmetic constraints. Unlike CORE28's candidate generator, the finite evaluator has NO handwritten COUNT/APP/REV implementations.

- Generated finite source facts: count 258, append 121, reverse 43.
- 726 small bounded source-derived input signatures; only `+` of the researcher-specified four-operator grammar `+,-,min,max` matched all 726.
- Poisoning the original COUNT base 0->1 invalidates all four hypotheses on 726 finite observations (not treated as an original proven source).
- Consistent predicate alpha-renaming preserves the selected equation and 726 observations; removing the original unsafe goal clauses also preserves the selection.
- IMPORTANT: an initial TOO SMALL integer universe produced a spurious `max` for the poison, rejected as insufficient finite evidence; expanded bounded universe fixed the test. This is a central failure to preserve, not claim as a theorem.

## Independent certified proof (still HUMAN INTERPRETED)
Source-selected `+` is passed to an independent previously existing CORE27 source theorem verifier. The verifier uses HUMAN-written recursively defined mathematical meaning for count/append/reverse and manually specified induction obligations. Results: **2/2 auxiliary lemma induction UNSAT**, **2/2 reversal induction UNSAT**, **11/11 genuine original Horn clause negations UNSAT**, **6/6 mathematical and poisoned original negative controls SAT**. The source-derived finite interpreter did NOT automatically synthesize those total recursive proof definitions, so end-to-end source-to-proof is NOT fully automated.

## Reproduction
`NEUMANN_CORE29_SOURCE_FIRST_HORN_20261016.zip` SHA-256 `355835e1f28b9a3596cdb9e9d5e376a6dd48b2e6d8b8608aba0d1d52c45e7f70` (20,051 bytes; 13 ZIP entries, 12 payload SHA manifest); CRC PASS. Exact external SMT original excluded due to unknown redistribution license; source fetcher checks pinned Git bytes. Fresh independent unzip + exact original separately supplied: **9/9 pytest PASS, 12/12 payload hashes PASS**.

## Headroom and novelty
Finite extraction is CLASSICAL and a fixed four-operator candidate hypothesis class is human supplied. The source was previously read in CORE27/28, so not prospective blind transfer. Strong exact classical operator selection is already possible, and training-free system has no frontier or cross-family neural advantage. Global **Q1–Q7 remain OPEN**. NO basis for Q3 invention or Q4 10x efficiency claims.

## Next single gate
Stop training fixed candidate slots/operators. Produce typed recursive semantic definitions and helper relation LANGUAGE automatically from the full original source, then pass independent inductive/original-source certification on a frozen truly unseen distinct family and strong exact symbolic baseline with all costs. No human implementation of per-source recursive functions in either candidate generator or verifier.