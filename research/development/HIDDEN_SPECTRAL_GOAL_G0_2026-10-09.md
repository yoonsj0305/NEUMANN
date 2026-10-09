# Hidden quadratic goal-sufficient spectral G0 — 2026-10-09

**Verdict:** `ENGINEERING_PASS / EXACT_CLASSICAL_STRUCTURE_DISCOVERY / NO_LEARNED_GAP / HOLD_LEARNING`  
**Scope:** opened synthetic algebraic family, not fresh evaluation; no global Q1–Q7 closure.  
**Research base:** `c182fd3f8d8b5c711415a214e899bfefe7511a0a` (stacked PR #176).  

## Original mathematical discovery and proof

Take a nonlinear map presented as public expanded polynomials, with hidden planted integer unimodular mixing `L` used **only in fixture generation, never in discovery**:

`F(x)=L^-1 ((Lx) elementwise squared)`.

The classical discoverer constructs the exact symbolic Jacobian, finds left eigenvectors at a generic public evaluation point, extracts the latent linear forms `phi_i` needed by the public goal `G`, and verifies from **original public polynomial equations**:

`phi_i(F(x)) = r_i * phi_i(x)^2` and `G(x) = sum_i w_i * phi_i(x)`.

Independent polynomial equality checker: original repository `neumann1/representation_program.py::verify_original`, source SHA256 `2b1bff0563c9e0b216fcbb840f3220499d2d0f59d494f73762560f447a42159a`. The claims hold exactly for all integer states. Runtime testing modulo 65521 is descriptive, not proof authority.

A strong **goal-specialized classical native** can run exactly this same Jacobian method and retain only the necessary latent coordinates. Therefore hidden algebraic coordinates *alone* are not an opening for training NEUMANN.

## First CPU study (opened development)

First contract premeasurement, engineering smoke tests and first 12 timed goal-views retained in separate archive. Two seeds for each of n=4,8,12 -> **six base matrices**, two dependent goal-views each. Output requires one or two hidden latent forms. 12/12 exact perspective/goal certificates accepted. Two negative controls rejected.

| n | discovery median | exact proof median | sequential-loop/query ratio, geomean | full spectral / goal spectral query ratio | weak sequential / paid goal, 16 queries |
|---|---:|---:|---:|---:|---:|
| 4 | 14.47 ms | 1.99 ms | 53.62x | 2.36x | 0.104x |
| 8 | 32.41 ms | 3.02 ms | 146.24x | 4.03x | 0.139x |
| 12 | 118.26 ms | 3.61 ms | 292.13x | 5.95x | 0.094x |

- Huge loop speedups use a **deliberately weak plain 128-step modular iteration baseline**.
- Full-spectral native (compute all n latent coordinates) can be outperformed by goal-specific k-coordinate evaluation, but **the strongest goal-aware classical method is identical to the proposed discoverer**.
- All 12 are **slower at 16-query whole discovery + proof + compile** than even weak plain iteration.
- Query timing is microseconds; performance noisy, 16-query values projected from median single-query measurements, no operating-system service/energy/memory claims.
- Geometric group averages count goal views sharing source, not independent benchmark populations.

## Separate opened posthoc gate development

A necessary, **not sufficient**, test for this exact family is commuting evaluated Jacobians:
`[J_F(a), J_F(b)] = 0`.

6/6 positives passed; 6/6 registered noncommuting perturbations rejected; 6/6 homogeneous-squaring lookalike decoys that include linear terms also passed the necessary test and thus still require full certification. Median gate costs: positives 52.47 ms, negative noncommuting 12.38 ms, commuting decoys 7.33 ms. The gate can ADD costly overhead on positive candidates. Do **not** run unconditionally until prevalence/cost-benefit is measured.

## Artifacts and immutable boundaries

Code, first research receipts, posthoc gate receipts, source copy, all ten tests, read-only analyzer and file hashes are in separate attached ChatGPT archive:

`NEUMANN1_Hidden_Spectral_Quotient_G0_2026-10-09.zip`  
Archive SHA256: `c25bb51227c2873fe3b98a8c25cbad2269d21c7815d0be803b454c07c532bb47`  
First science record SHA256: `5bd99feefe818589559193e096bc4e850401bab23c0ea4ddac3f7375037b8772`  
Followup gate record SHA256: `3d8a60167eedc045467dde823044aa789f2b28d7d4440e73226e102fb928d568`.

**Only this summary is committed to GitHub; actual source and receipts remain in the separate research archive and are not accessible through this Markdown file.** Historical v102/Q34 PASS, Q5/M106/P1/Decision2 FAIL and global Q1–Q7 OPEN unchanged; new learning G1/G2 NOT admitted.

## Resulting research policy

- KEEP exact goal-sufficiency semantics, original verifier, strong native baseline and possible conditional cheap algebraic rejection test.
- HOLD neural refit/training on planted quadratic-conjugacy family.
- STOP generating variations of the same synthetic latent-squaring task as supposed independent evidence.
- For next external screening: SV-COMP 2026 official loop-verification category and SyGuS-Comp independently sourced public tasks. Ensure original task/split lineage, strong cvc5/SMT/CAS or competition solver baseline, independent full-goal verifier, paid representation discovery, and pre-registered economic headroom before training.
