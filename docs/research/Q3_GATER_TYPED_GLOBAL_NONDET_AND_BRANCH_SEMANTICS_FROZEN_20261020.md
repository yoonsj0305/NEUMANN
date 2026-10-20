# Q3 Gate R first meaningful semantic representation extension

2026-10-20, POSTHOC engineering on already OPENED original external benchmark sources; ZERO fresh-blind/G1/learned-invention claims.

Frozen originals: SyGuS-Org/benchmarks@13c8deb68a873635879c9a69bc78caebd340f646.
- xujie_code2inv/1.c.sl original git blob SHA1 859bae24a9f26044a40a3c97f1d2e5fc08504f06.
- andrew_lustre/DRAGON_1.lus.sl original git blob SHA1 8490b3e25ff7d462a7405e68e742be1abb35b8f8.

Only proposed representation improvements:
1. A typed original mixed Bool/Int interpreter must recognize ONLY source-declared `declare-var` global non-deterministic symbols (31 in DRAGON_1), without replacing or constraining them. No unbound variables permitted. `init/trans/prop` source argument signatures, all named-helper calls and sort parity must be preserved.
2. Separate independent native SMT-LIB parser against the original source's raw, byte-identical `define-fun` declarations, translating SyGuS `declare-var` syntax to SMT-LIB `declare-const` for environment compatibility, and instantiate original named Pre/Trans/Post with fresh state symbols; assert XOR with typed AST compiler expressions. Require Z3 UNSAT for all original meanings, and independent pinned cvc5 UNSAT when affordable. A failure / timeout is UNKNOWN, never PASS.
3. Non-deterministic multi-branch native original Trans, such as xujie, must retain the full OR of conjunctive branches including partial next-state freedom. Extract conditional branch guards and constraints, with exact Z3 and independent cvc5 UNSAT for `Trans XOR OR(branches)`; deliberately omit a branch as a negative control and require a SAT distinguishing witness. Do not turn unspecified physical next-state coordinates into deterministic equations.
4. Test source Pre SAT, NotPost SAT and actual Trans SAT; no original safety proof implied. A later candidate can be independently proved via existing 3VC without changing source.
5. Classical-only infrastructure. Previously frozen 42-weight polynomial model remains strict NO_GO for new operator within its grammar, GLOBAL Q3 OPEN. This is Gate R frontend SUBGATE, not complete Gate R generative structural invention, not Gate V.

Acceptance: first CI must retain actual per-source evidence, source original blobs, typed compile diagnostic, original/native XOR parity, independent cvc5 check, negative branch-ablation. Failing any parser or solver must be ABSTAIN. No source-specific gold invariant or artificial Post strengthening.