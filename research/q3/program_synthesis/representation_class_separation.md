# Q3 RC13.1 | exact finite-grammar representation separation

**2026-10-25 · scoped theorem in fully enumerated human-defined source grammar.**

- Integer low-multiplication width1..3 source: 84 input pairs, 228 output bits.
- Original RC12 grammar: index AST of at most one binary +/- node, memory NONE/LATEST/HISTORY for each operand, 3 loop modes, XOR/OR accumulators, **no persistent scalar**. Exhaustively assessed **23,814/23,814** possible programs; exact fit 0; BEST **224/228** source output bits.
- Expanded RC13 grammar: 214,326 programs = original index/memory/loop choices with XOR/OR/ADD and scalar read (off/on), scalar update (ZERO/SHIFT_RIGHT_1/LOW_BIT). Exhaustive independent evaluation **214,326/214,326**; EXACT **16** of them fit all 228 source bits.
- ALL 16 source-exact programs have BOTH HISTORY buffers, integer ADD, scalar read ON, scalar update SHIFT_RIGHT_1. Forbidding read or update cannot fit 228/228.
- This proves **a representation-class capacity gap within exactly these two fixed finite program languages**. Does not prove all algorithms require this register or new DSL self-invention. The 16 finite-source-perfect programs are not each unbounded certified; only the own-weight-selected (j,i-j), inclusive-loop program is separately inductively proven.
- RC13 model: 12/12 best sampled valid, **only 6/12 final greedy** outputs valid. Classical complete enumeration still faster.
- Full independent auditor `rc13/representation_gate.py`, all16 witness codes in `rc13/REPRESENTATION_GATE.json`, and clean replay are inside conversation archive `NEUMANN1_Q3_RC11_TO_RC13_PROGRAM_SYNTHESIS_20261025.zip` SHA256 **de8c43de754c33607df7e47e559117e4772863c6ae30038b2de699d578312573**.
- Research gate **RC13.1 scoped PASS**. Frozen global Q3 autonomous new language, Q4 complete10x, Q6 external generalization, Q7 frontier gap all **OPEN**.
