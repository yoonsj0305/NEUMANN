# NEUMANN 1 Q3 | generic source-only symbolic discrete antidifference for 3 already opened real originals

**2026-10-20, POST-PREFLIGHT developmental classical baseline**, not prospective blind and NOT neural Q3 invention.

## Frozen actual sources and strongest honest target
Three originals were source-SHA preregistered under PR #308 before first original bodies were inspected; first bounded source-violation BMC found UNSAT for depths 0..3, which NEVER proves unbounded safety.
Now original contents have been opened. This newly developed exact symbolic classical solver is expressly POSTHOC, without source-family blind eligibility.
Sources at SaswatPadhi/LoopInvGen@6ac90265b11431c9477dfbd33e3e3380234c0499:
- benchmarks/NIA/other/pottsumm3.sl Git blob e0734e4358956b3ca66d280c9d4f8282b18d29b4
- benchmarks/NIA/2018.CHI_InvGame/s9.desugared.sl Git blob 36234fd712b21a9111f834058e8371b10e3de191
- benchmarks/NIA/2018.CHI_InvGame/non-lin-ineq-3.desugared.sl Git blob 728ee7e03686db111e47b429e3d584ad3ed668db

**Algorithm has NO hardcoded result forms, no filename-based branches and never reads published Post until the generated full candidate is frozen.**

1. Exact original SHA, independent custom/native Pre/Trans/Post logical XOR and original Pre SAT, Not(Post) SAT.
2. Traverse native Z3 Trans *conjuncts* to identify deterministic successor equalities for each state coordinate, inline next-state dependencies to obtain entire transition expressed in old state. Verify original whole native Trans logically entails EVERY derived next-state equation (one source bound Z3 UNSAT check) and no transition ambiguity. Unsupported/UNKNOWN => ABSTAIN.
3. Convert each exact polynomial source state update to SymPy integer polynomial; identify mutable clock variables updated +1, source-static variables updated 0. For each (clock, accumulating state variable) where delta depends only on that clock and source-static parameters, derive exact antidifference P(clock)=SUM[t=0..clock−1] delta(t). Candidate invariant: acc−P(clock)=0, with correct integer clearing denominators. All candidates are checked against original Pre before joining; SMT postcondition NEVER enters synthesis. Compute symbolic finite-difference identity F(c+1)−F(c)==delta(c), independent of sampled behavior, as explicit certificate.
4. Add source-only Pre-proven positivity and loop-bound facets from literal original source Trans guards clock<bound, if start and direct branch preservation can be checked. Preserve all generated/rejected candidates. Rule for protected candidate dropping: no source-specific intervention based on final Post result.
5. Prove actual native original Pre⇒I, I∧Trans⇒I', I⇒Post original three negated VCs Z3 UNSAT and independently SHA pinned official cvc5 1.4.2 UNSAT. If nonlinear SMT returns UNKNOWN, preserve and use decomposed SymPy identities only as partial evidence, never claim full dual original pass. Source goal is NEVER weakened.
6. Exact same algorithm for all three real sources, no training, no GPU, no paid API, immutable first CI receipt. A success proves strong classical mechanism, so those sources are NOT eligible for showing learned-exclusive G1 even if earlier BMC had no short violations.

G0/learned-Q3 global remains OPEN. A solver fail/UNKNOWN is not evidence of inherent safety failure or neural headroom. Strong classical antidifference is included in future equal-information baseline contracts.

Expected structural family from human posthoc inspection: sums of squares, constant-coefficient clock accumulators, and cubic lower bounds. These **are not programmatically supplied answer labels** or source-specific templates. Do not silently insert golden equalities.