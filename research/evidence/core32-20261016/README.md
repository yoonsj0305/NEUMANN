# NEUMANN CORE-32 | Minimum necessary computation via typed structural admission

**2026-10-16, development-only. Scientific verdict: RESTRICTED_CLASSICAL_STRUCTURE_FILTER_VERIFIED, LEARNED_INDEPENDENT_ABSTRACTION_NOT_PROVEN. Global Q1–Q7 OPEN.**

## Actual algorithm and exact original
CHC-COMP 2026 external authentic source `ADTRem/isaplanner/goal52_000.smt2` at upstream commit `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`, Git blob `f27b6a56e752498b2a67cb59bd739aebbb7dd179`, **2,605 bytes**, SHA256 `3db92ef5e5f890bf6fc0a61aefddd45bfe364fcd9b39653c9f542c59bcd372f5`.

Algorithm masks three unsafe goal clauses, uses the existing source-derived generic Horn recursion compiler to construct three executable total recursive functions, and discovers typed roles of an `Int×List→Int` accumulating fold and `List×List→List` constructor-preserving composition. **Human-chosen fold/concatenation homomorphism theorem family** offers only four operator ASTs `+,-,max,min`. Five bounded source-executed observations reject three; the remaining full auxiliary AST undergoes independent universal induction proof.

### Executed proof
- **Four typed candidates, ONE sent to Z3 induction** (`+`); base and step **2/2 UNSAT**.
- Certified auxiliary used in a researcher-coded reverse-count theorem bridge; reverse induction base and step **2/2 UNSAT**.
- Original Horn clauses independently checked with compiler-generated source functions: all **11/11 negated clauses UNSAT**.
- Invalid COUNT base 0→1 produces no admitted operator; alpha-renaming of source relation identifiers preserves exact full-source proof; goal mutation does not change the proposed theorem.
- Wrong `max` theorem not admitted. On the first run the universal negative-control SMT query returned **UNKNOWN** instead of a required SAT, causing **one initially failed test**. Correct fail-closed check rejects UNKNOWN and a separate concrete wrong-value witness returned **SAT**. Historical failure retained.
- Other-family tree goal47 and multiple-datatype goal46 correctly **ABSTAIN_UNSUPPORTED**, no source-family transfer claim.
- Final automated test suite **9/9 PASS**, including exact benchmark identity, poisoned-source blocking and semantic renaming. Independent ZIP extraction: **13/13 payload SHA256 match**, **9/9 pytest PASS**, original 11/11 and base/step replay PASS.

## Measured economy and strict comparability boundary
CORE-31 broader source-compiled bounded AST enumeration examined **62** full theorem candidate ASTs with observed **~30.218s** internal CPU wall. CORE-32 **narrower hand-selected algebraic theorem family** has 4 candidates, 1 verified theorem, observed **~0.291–0.310s** internal wall (separate independent extraction replay **0.5456s**). This is a large empirical reduction of unnecessary candidate/proof work in one already-studied original, **NOT a matched-hypothesis-space nor frontier 100x result**, because CORE-32 is given strong researcher-specified fold/concat family information that CORE-31 does not receive.

The global mission is *frontier-level problem solving with minimum necessary computation*. This supports a hybrid runtime principle: prefer cheapest source-derived exact structural synthesis and selective SMT verification before invoking a learned system. It **does not prove a learned neural model is needed** for the current benchmark: neural forwards **ZERO**, training **ZERO**, other-family blind Q3/Q6 transfer **NONE**.

## Code, integrity, and public archival boundary
Local release `NEUMANN_CORE32_MINIMAL_COMPUTE_GATE_20261016.zip`, **22,510 bytes**, SHA256 **`260416d931aab498e284860cd951f8a6d4ba8caa569f2b2dd5737fbdf36a2c63`**; ZIP CRC PASS, 14 entries including 13 manifest-hashed source/receipt payloads. Original CHC SMT bytes are not redistributed; source fetcher downloads only the pinned exact version and checks original identity. This PR contains written report and checksum record; **ZIP byte contents are not yet present in GitHub**.

## Hard research stop / NEXT singular decisive task
Stop training fixed same-family theorem or operator slots. Freeze full-source learned generator of NEW helper predicate *signature, base and recursive rules* BEFORE inspecting a genuinely unseen other-family program. Demand independent all-original CHC proof and strong iso-information classical synthesis baseline with complete costs, else keep Q1–Q7 OPEN.