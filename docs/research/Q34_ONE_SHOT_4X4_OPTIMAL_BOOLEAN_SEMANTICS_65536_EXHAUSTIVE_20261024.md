# NEUMANN 1 Q34 | Minimal-information one-shot operator discovery, exact exhaustive test

**First verified locally 2026-10-24.** This is a rigorously **BOUNDED** discovery mechanism for a known 2×2 binary toroidal local-rule class, **not** a claim of neural semantic invention, frontier AGI parity, or a new theorem.

## Formal source-only problem

A synchronous binary toroidal 4×4 grid has an **unknown** shared local Boolean rule \(f:\{0,1\}^4\to\{0,1\}\). At each cell a 2×2 southeastern patch, including wraparound, determines its next-state bit. The learner knows the four input locations, that a deterministic stationary shared rule exists, and that it can select one initial state and observe the complete resulting grid. It receives no candidate list of the 65,536 possible complete functions.

A full 4×4 exhaustive input enumeration discovers 32 grids whose **16 toroidal 2×2 patches enumerate all 16 binary 4-bit inputs exactly once**. The lexicographically first mask is \`0x12b7\`, grid:

\`\`\`
1110
1101
0100
1000
\`\`\`

The 16 local input words in row-major output positions are:

\`[15,7,9,14,11,5,2,3,6,1,0,8,13,12,4,10]\`.

Thus in **one** simultaneous 4×4 query, the observed 16 output bits disclose the entire unknown operator truth table. Reorder observed results into a 16-bit table; the GF(2) Möbius transform compiles it into a unique executable algebraic normal form (ANF), with AND monomials and XOR sums. There is no lookup library of the full operators.

The pure-Python algorithm \`research/q34/one_shot_boolean_operator.py\` enumerated **all 65,536 distinct unknown operators**, reconstructed **65,536/65,536** exactly from one observation each, synthesized the unique ANF for each, and checked every one of its 16 possible 4-input cases. Zero errors. Exactly **32,768** have ANF algebraic degree four. Essential input counts (k=0..4) were \`2, 8, 60, 872, 64594\`, independently matched to inclusion-exclusion \`binom(4,k)*sum_j (-1)^(k-j)binom(k,j)*2^(2^j)\`.

A separate independently implemented Shannon decomposition in \`research/q34/independent_shannon_audit.py\` constructs canonical reduced ordered binary decision diagrams from the observed truth semantics with **65,536/65,536** all-16-input exact validation, maximum **nine BDD internal nodes**, zero errors. It does NOT call the ANF transform, so supplies a genuinely different compilation path for identical observable semantics.

## Tight bound and comparison

A completely unrestricted 4-input Boolean operator has **16 independent output bits**, so \(2^{16}\) possible operators. Any noiseless binary measurement transcript distinguishing all 65,536 possibilities needs at least **16 observed output bits**. The universal 4×4 source produces exactly 16, meeting the information lower bound. A nonempty query is logically necessary and this achieves **one round**, so the round lower bound is met too.

Compared with a previous **four 4×4-probe** evaluation using 64 observed bits, this construction cuts queries and observations **4×**. Compared with the earlier **single 8×8** universal probe (64 bits), rounds are the same but input and output **volume** are **4× lower**. These are comparisons to specific previous procedures, NOT 10× end-to-end hardware efficiency, absolute time, or strong general-purpose methods.

A counterexample proves 15 input patterns cannot distinguish operators differing only on the omitted input. With an ordinary NON-toroidal 4×4 source, there are only nine non-wrapping 2×2 windows, and this theorem does NOT apply.

For bounded noise handling, a single **8×8 periodic repetition** of the optimal grid provides four copies of each 2×2 input word. Strict-majority decoding corrects at most one corrupted copy per input word. The local first run tested **16,000** 8×8 whole-state **single-bit corruptions** across 250 sampled unknown rules with **16,000 recovered**; multi-bit patterns weren't all enumerated. The noise-tolerant design now observes 64 output bits, not the 16-bit noiseless bound.

## Example unknown operator

Actual test input operator truth table \`0xBEEF\` resulted in observed 4×4 state \`0xB7F7\`; the learner recovered \`0xBEEF\` and automatically generated GF(2) ANF coefficients \`0xCFF1\`, including the degree-four term \`x0*x1*x2*x3\`. This is just a representative of the exhaustive 65,536.

## Scientific limits and gates

**Pass:** in this precisely stated problem class, unknown nonparametric operator semantics recovered from one source observation, executable ANF and BDD definitions independently proved over their ENTIRE possible input domains, exact minimum queries/observations proven.

**Unproven:** algorithmic primitives invented by a learned neural model (our algorithms are CLASSICAL), unspecified neighborhood size/geometry, passively observed or stochastic external systems, novel mathematics priority, independent author unseen benchmark distribution, frontier solving parity, and total computation/energy 10×.

\`Q34_LOCAL_OPERATOR_DISCOVERY=BOUNDED_PASS\`; \`Q3_GLOBAL=OPEN\`; \`G1=HOLD\`; \`Q4_GLOBAL_10X=OPEN\`; \`Q6,Q7=OPEN\`.

### Code/verification

\`\`\`sh
python research/q34/one_shot_boolean_operator.py
PYTHONPATH=research/q34 python research/q34/independent_shannon_audit.py
\`\`\`

No dependencies beyond the Python 3 standard library. The exact original local research archive \`NEUMANN_Q34_ONE_SHOT_OPERATOR_DISCOVERY_VERIFIED_20261024.zip\` additionally includes a separate longer noise-injection harness, explicit negative controls, independently computed receipts, and SHA manifest; available as the linked conversation attachment, not automatically uploaded by this repository PR.

Known prior art: de Bruijn-style covering tori, GF(2) algebraic normal form and Boolean Möbius inversion, Shannon binary decision graphs, classical information-theoretic counting.
