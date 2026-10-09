# NEUMANN 1 — Nonlinear Goal-Sufficient Telescoping G0 (Opened, 2026-10-09)

**Research state:** `ENGINEERING_PASS / CONSTRUCTED_HEADROOM_VS_WEAK_ITERATION / STRONG_CLASSICAL_NATIVE_MATCH / HOLD_LEARNING`  
**Parent research SHA:** `c182fd3f8d8b5c711415a214e899bfefe7511a0a` (PR #176 draft, not main)  
**Original NEUMANN verifier SHA-256:** `2b1bff0563c9e0b216fcbb840f3220499d2d0f59d494f73762560f447a42159a`

## Exactly what was done
- Built eight opened synthetic polynomial recurrences `t'=t+1`, `x'=x+q(t)`, with degrees 2/4/6/8 × 2 random seeds. This is **ONE structural motif**, not eight independent families.
- Candidate discovers `Q` only from public `q` by ordinary classical Newton finite differences. It constructs an exact checked equation `D*(Q(t+1)-Q(t))=D*q(t)` with denominator clearing, using the repository's exact-integer polynomial verifier.
- Original goal `x_n=x_0+Q(t_0+n)-Q(t_0)` is established by induction/telescoping, not only sample matching. Original full iteration cross-checks concrete goals. Modified recurrence/incorrect closed forms are rejected.
- A separate, strong **SymPy 1.14 exact symbolic-summation control also discovered the same Q in 8/8 cases**. No language model or trained policy was used.
- First CPU development measurements retained once in ChatGPT artifact `NEUMANN1_Nonlinear_Goal_Sufficient_G0_2026-10-09.zip` (ZIP SHA256 `29810c8b392baec78987f9adfbaf3f152c38919526ac56438becc55844768fbf`), which contains `contract.json`, `experiment.py`, original-source snapshot, 8 first receipts, independent analysis, tests, Korean report and SHA manifest. **Those raw artifact bytes are NOT copied into GitHub by this note.**
- Tests: 7/7 PASS, ZIP CRC and archive SHA-256 per-file checks PASS.

## Actual measured observations and limitations
- Original sequential loop over closed-form **execution alone**: horizon 128 median 23.61x (range 19.21–29.02); horizon 2048 median 396.50x (range 323.86–458.84). This is deliberately a **weak iterative comparator**, NOT the strongest available native symbolic algorithm.
- One-time discovery+exact proof paid, then stationary repeated requests N projected from timed median single-query costs:
  - horizon 128, 256 requests: classical Newton vs loop 1.981x geo; horizon 128, 4096: 13.401x geo (six/eight reach 10x).
  - horizon 2048, 1 request: 0.155x geo; 16 requests: 2.467x; 256 requests: 35.287x (8/8 reach 10x); 4096 requests: 229.65x.
  - alternative SymPy discovery + same fast runtime: horizon 2048, 256 requests ~4.994x.
- These N-request values are **extrapolations, not timed N-request batches**. Startup/deployment memory and energy, full model lifecycle costs UNKNOWN.
- Since Newton itself is an existing classical method that achieves the identical fast representation, **strong classical vs candidate marginal headroom is NOT demonstrated**. No learned-generation ability, open-set generalization, frontier improvement or global Q1–Q7 closure.
- No past Q34, Q5, M106, Decision2, P1/G0 decisions modified.

## Decision
**KEEP** the exact proof contract, goal-to-formula mapping and per-query amortization accounting as `classical_native` Structural Experience; **HOLD** neural training or global G1/G2 admission for this family.

Before new learned-perspective research, identify a different structural family where (1) a free correct perspective gives large measured headroom against **strongest available native**, (2) strong symbolic generation cannot find that perspective economically, and (3) original-goal certification remains affordable.

## Prior art and grounding
- Sankaranarayanan et al. (2004), nonlinear invariant generation by Gröbner bases.
- Rodríguez-Carbonell & Kapur (2007), polynomial invariants of simple loops.
- Bayarmagnai et al. (2026), algebraic algorithms for polynomial loop invariants.

The present Newton finite-difference construction is classical mathematics, not a novel invention of NEUMANN.
