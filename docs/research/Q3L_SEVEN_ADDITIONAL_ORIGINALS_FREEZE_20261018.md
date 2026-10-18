# Q3L Preregistered 7-source **classical specialist and composed proof** survey, before any Q3L execution
Date 2026-10-18 KST. **No model learning or Q3/Q4/Q7 promotion.**

## Scope freeze
Fixed source corpus Microsoft Loopy commit `91fe89245a0894ec8ad3741d85ae91ce3b552b2e`, dataset Git blob `17cac0f6734a39f0fe73558199cc2ad8d5c1a810`. Select exactly the seven ORIGINAL C source programs classified `SOURCE_ONLY_AUTO_INVARIANT_NOT_PROVEN` in the first 150-source Q3I receipt **excluding `sum04`**, which was already classically certified via Q3J+Q3K2. The seven exact path/hash identities are frozen by `first_seven_untested.py`; require 7/7 SHA match and a reconstructed Q3I summary matching that path set. The source bodies are already opened during Q3I development, so this is **not blind test data** and cannot establish Q3 autonomous learned generalization.

## Algorithms and gates fixed before execution
1. Same original Q3H subset C AST and unchanged annotated postcondition and signed 32-bit original semantics. Never load or use the published Loopy invariant *answer* strings; **no source rewrite**. Any unsupported or unknown result is NOT PROVEN.
2. For each original, run Z3 4.13.3.0 SPACER with exact original C initialization, a generic variable-arity Reach Horn relation, unreachable `BadExit` check, and an independent signed-step `BadOverflow` check; **3500 ms maximum per query**, fixed across all seven.
3. Run the already registered and unchanged Q3H2 **source-only classical Houdini** for the same exact C source to obtain independent original base, induction and overflow. This is not an upgrade of candidate grammar.
4. A complete ORIGINAL C theorem is admitted **only** if: original source/init prelude arithmetic UNSAT, SPACER original BadExit UNSAT, plus **either** SPACER BadOverflow UNSAT **or** Houdini's independently rechecked original init, induction and signed-step-overflow all UNSAT; three original-independent safe/unsafe/overflow controls PASS. The same original C semantics and original state signature must match.
5. Record a 0..32-step exact bounded **reachable exit witness** (if found) for non-vacuity analysis; no finite BMC result is a global safety theorem. If exit witness not found, classify `NONTERMINATION_OR_EXIT_REACHABILITY_UNESTABLISHED`; any proof of unreachable BadExit is still safety but **do not call it a nonvacuous task win**. No evidence of exit is not evidence of nontermination.
6. Every original case, source identity, solver status, reason unknown, query wall, and all passed/failed contracts is logged. Fail closed. **No threshold adjustment, helper relation source-specific patches, reruns with larger budget, selection of only successful cases.**
7. Q3F's two external competition-grade CHC holdouts are still cryptographically sealed; no source text accessed. All Q1–Q7 OPEN. Any result is restricted to 7 already-opened **classical** source-original safety problems.

## Stop-loss
If this approach achieves additional full original proofs, it expands **classical** structure/proof decomposition capability, not AI learned invention. Stop rerunning similar case families. If none, record the failure; do not retrofit grammar from source labels. Train a typed learnable operator constructor only if separately justified by proof-carrying and disjoint-source data and strong-classical gaps.
