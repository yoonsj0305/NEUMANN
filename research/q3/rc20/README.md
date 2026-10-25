# Q3 RC20 | OWN weight proposed integer register memory, not a prebuilt stack

**RESEARCH-ONLY DRAFT. DO NOT MERGE without independent review.**

This research explicitly removes RC19's STACK/QUEUE/LAST/NONE datatype menu. It
instead trains a PyTorch categorical policy over a HUMAN-authored generic
36,864-program scalar-integer microinstruction grammar. Source: the SAME
340 RC19 original I/O examples, 1,252 bits, k2 n1..4. Two opening instructions
and closing read/update/control are learned as a sampled 9-field program. Generic
CPU integer register and arithmetic semantics remain PROVIDED, so this is not
neural invention of a new fundamental machine language.

**Original weights and controls:** 16 source-only initializations, best
sampled12/16 source perfect; **final greedy4/16**. No holdout-assisted tuning.
The FIRST selected frozen code is (1,1,0,1,0,0,0,0,0), with complete actual
PyTorch logits and first-execution SHA in the SEPARATE reproducible ZIP.
8 FRESH disjoint postfreeze seeds (no retuning): best5/8, greedy1/8.
Selected macro represents unmatched typed openings as a scalar integer
S <- (k+1)S+(kind+1); on close compares S%(k+1) and reduces S//(k+1).
This is a **MODEL-PROPOSED NEW MEMORY REPRESENTATION** inside provided
arithmetic bytecode, not an independently invented base ISA or parser.

FIRST untouched independent k3 widths5..7 predictions **2,278,368/2,278,368**
bits, 334,368 streams, including 33,453 positive output bits. Other NEW
k4/k5/k6 exhaustive 429,744/429,744 streams, 2,376,032 bits; balanced
postfirst1,200 valid +1,200 near-invalid correct; depth to512, k16.
Human-planned task change: same learned radix program reused to reverse
1,200 novel typed sequences, 1,200/1,200 correct. Does NOT establish neural
zero-shot task planning or independently authored Q6.

Exact mathematical invariant over an arbitrary-depth pending-kind list,
written as ONE scalar radix-(k+1) integer, proves all finite lengths and
ALL k>=2 under arbitrary-precision integer assumption. Pairwise distinct
typed histories require >=ceil(d log2 k) information bits. Proposed code's
worst integer payload needs <=ceil(d log2(k+1)) bits, k16,d512:
2048 lower vs2093 upper. Code, allocator, parameter, transport, verified
fallback, energy and integer-operation time are not counted in these bit bounds.

**Equal-rights rigorous classical comparator:** 36,864/36,864 grammar codes
explored and pruned against identical source traces; exactly6 source-perfect,
all6 universally radix-proven; ~0.0929 CPU seconds. Neural 16 initial train
runs ~13.0407 CPU seconds, about **140× slower**. No neural-exclusive
advantage or global Q4/Q5. Exact timing is machine/process-specific.

Full original 22-file clean ZIP:
`NEUMANN1_Q3_RC20_ARITHMETIC_MEMORY_INVENTION_20261025.zip`
SHA256 `7797d1a88b544546973cb5168ad4b47a5c6a048883847e507176d3d8a2edd2a9`.
Contains original .pt tensor, all24 model receipts, raw first binary, SHA
manifest, source-only trainer, independent grader and classical enumerator.
Both REPRODUCE.sh and full 24-seed RETRAIN.sh separately PASSED from a fresh
ZIP extraction. This PR version controls only an extracted compact runtime,
a sound sufficient proof gate and quick tests; it does NOT contain raw .pt.

**PASS (bounded):** model-weight sourced arithmetically encoded dynamic memory,
formal exact behavior, new k, deep nesting, fresh restarts, reusable macro,
independent reference and fail-closed gate. **OPEN:** self-invention of
fundamental language/ISA, new external-independent authors, global Q3,
Q4 all-in 10×, Q6 new-family, Q7 frontier capability. Frozen North Star
remains unchanged. The research question is whether the learned model can
propose grammar mutations with a strong all-in cost/capability advantage,
not repeat this toy source indefinitely.
