# Semantic diversity and true-oracle cost: frozen independent PROSE follow-up
2026-10-26. Existing NEUMANN discovery-policy research branch, NO NEW RC, NO NEW PR. Global Q1–Q7 remain OPEN.

## What is frozen BEFORE access to these original spec contents
Exact twelve public Microsoft PROSE original task identities, all previously uninspected within this continuing experiment: DateTime.000009, ShippingCode.000004, Phone.000007, Number.000008, Email.000011, City.000011, FilePath.000004, Name.000014, Column.000003, DateTime.000010, ShippingCode.000005, Phone.000008.

Only tasks with >=5 original examples and both first labels being supported strings are eligible; never replace excluded IDs. First two original IO demonstrations SOURCE. Third original input is an **available unlabeled potential verifier query**. The third ORIGINAL output is revealed ONLY for any program that has demonstrated a source-consistent *hypothesis disagreement on this exact third input*, and also for the separate expensive all-oracle C1/C2 baseline. The fourth/fifth ORIGINAL outputs are the independently scored FUTURE and cannot be used to tune the algorithm; freeze FIRST for every arm before viewing them.

Algorithms held fixed in local Python before looking at new originals:
- `diversity_aware_synthesis.py` SHA256 `a427fff0652a486eb2483f7614a131c162369a6c0729d12aa62c8117612e8753`
- `synthesis_import.py` SHA256 `092165e7b93d0f8229da47f7f8abed54547b4ecc3e34c3f1df3fc631e122ff47`
- tests SHA256 `3136f233867518ac44637951ca8dd7c5ec164e68cca41f514575babd2cdbee55`, pytest **4/4 pass**.

Main **DIVERSE-ON-DEMAND** arm: enumerate all 1,632 generic parameterized one-atom programs; preserve distinct semantics even when all agree on first TWO training examples. If proposed third-input outputs have >1 class (including undefined), request one independent third-output oracle; filter all source-consistent atoms accordingly, then predict fourth/fifth outputs only under a **single surviving output class**; otherwise HOLD. If no input disagreement, do not ask; never call neural. This costs one oracle only when classical structural alternatives disagree.

Controls:
- C0: same diverse atomic candidate set, **zero third feedback**; source-only one-class prediction or HOLD.
- C1: same diverse atomic candidate set but **ALWAYS request third output** and filter, report difference in task-verified ability and label-request costs.
- C2: stronger multi-atom classical Dijkstra/AST resynthesis on the same first 2 IO PLUS third authentic labeled feedback, with source-exact program-consensus, cap 1800 candidate state expansions/12 complete programs.
- Baseline of older cheapest atom dedup retained for diagnosing false apparent consensus, not a substitute for strong C2.
- PRIMARY: full-task exact vs wrong vs HOLD across all non-ineligible original tasks. SECONDARY: number of real oracle requests, correctly detected source ambiguities, false source consensus, actual process CPU, unchanged codes and their hashes.
- In a deployed tool the oracle is not free, and may not be available; its monetary cost unknown. Public PROSE text-only tasks, semantic families overlap earlier studies; NOT global novel model invention or frontier comparison. New original labels are unseen at preregistration, but the currently assisting GPT model could have public-data contamination. This specific engine has **no neural weights**.

This is a targeted experimental test of whether the previously cheap but lossy `create_atoms` source-behavior dedup was hiding source-equivalent alternatives necessary for discriminative verification. Any result, including negative, is preserved. No after-gold tuning may count as original first evidence.