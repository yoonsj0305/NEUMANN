# Q3 RC14 | Own-weight proposed NEW NAMED composite memory macro

**2026-10-25. DRAFT RESEARCH ONLY; DO NOT MERGE WITHOUT REVIEW.**

The previously frozen RC13 experiment provided **an entire SHIFT_RIGHT_1 opcode**. RC14 instead provides a general human-defined arithmetic-expression substrate with ADD/XOR/OR/MAX/SUB/MUL, register+digit+0+1 leaves, output projection, generic division/modulo/update and an allocatable scalar slot. Its *28 learned PyTorch policy logits* (elite sampling + Adam) emit compositional code from 84 n1..3 end-to-end integer multiplication I/O pairs (228 output bits), with no carry labels. **The original learned weights and all first outputs are in the complete SHA-audited study ZIP**, not in this lean GitHub branch.

Model source-best proposals: **9/12** independent seeds achieve228/228; **0/12 final greedy** succeed, so all success is retained best-of-sampled source search, not pure zero-search greedy model. Complete human-defined 6,144 candidate grammar includes exactly five source-perfect programs; three (XOR, SUB) are wrong on n4. Original sealed, correctly selected first program (seed2026102506) is ADD with register. A candidate-partition-selected membership query (n4,a3,b3) opens ONE extra label **after first predictions were SHA-frozen**, reduces five to two commuting ADD implementations. Both had already been proposed by own trained policy. No training after this query. Independent first-grader n4..8: 87,296/87,296, **87,295/87,295 truly untouched** (one n4 case was opened). Generic digit normalization theorem proves ALL finite widths.

Reusable new symbol `AUTO_RADIX2_DIGIT_NORMALIZER`, emitted **from frozen policy-selected code** into proof-gated MacroRegistry, passed frozen independent:
1,100 arbitrary positive digit streams length up to2048, 37,448 three-integer addition examples, 37,448 three-factor multiplication/convolution examples, **75,996/75,996**. Exact induction `sum_{i<t}d_i2^i=sum_{i<t}y_i2^i+2^tc_t`, where `t_i=c_i+d_i, y_i=t_i%2, c_(i+1)=floor(t_i/2)`. Guarded proof failure returns UNKNOWN and reference fallback remains available. `0<=d_i<=M` bounds carry storage by ceil(log2(M+1)) bits; operand histories/additional program state not included.

**Strong same-rights classical** exhaustive 6,144 programs, all five source-perfect, local process CPU **0.546s** versus model 12-seed training **2.961s** and 18,798 distinct candidate evaluations; **no neural-exclusive efficiency or global Q4 pass**.

### Full original data

`NEUMANN1_Q3_RC14_LEARNED_NAMED_MEMORY_MACRO_20261025.zip` SHA256 `f1aefc27eaf6fd36080cfe5b3709fb74464648b070f8b2d8be748b107cca6c1f` (conversation artifact). Contains real weights `.pt`, source-only trainer, full 12-seed receipts, 5 candidate first predictions, SHA manifest, active query receipt, independent all-width grader and 75,996 task probes. Full **clean-extract REPRODUCE.sh + fresh RETRAIN.sh PASS**. This PR intentionally only version-controls compact compiled code and quick tests.

**Bounded gate:** scoped new *named program symbol* self-registered from own trained policy = PASS, *autonomous invention of new base programming language/ISA* = OPEN, global Q3/Q4/Q6/Q7=OPEN. Human supplied the DSL, program interpreter, digit extractor, state slot substrate and symbolic proof rule. No true unseen external author or frontier breakthrough.
