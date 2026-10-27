# NEUMANN 1 | G0-SGI real SyGuS solver headroom preregistration | 2026-10-27

**Scope**: independent public benchmark, strong classical baseline BEFORE spending on ownweight model. No Q1-Q7 promotion, G1 HOLD.

## Frozen task source and selection
- Public Barnard-PL-Labs/sygus-sgi-1 repo commit e7ae840e5546e9243ff94afb1a29064fc050011c.
- Prior to this freeze only the repository README and the author's example filenames were visible; no selected source tasks had their full content fetched in this chat.
- Select EXACTLY 6 easy and 6 hard original SyGuS files. Eligible filenames are obtained by deterministic filename-only glob: data/benchmarks/easy/*/*.sl and data/benchmarks/hard/*/*.sl. Sort each bucket by SHA256("neumann1-semantic-gap-v1/" + repo-relative filename), tie break original path, retain first six. This deterministically freezes task identities by code before reading any selected file content. No substitution for missing/unsupported files. Always include all 12 in report.
- The repository authors describe easy cases as 8-bit, hard as PBE-BV 64-bit and warn cvc5 usually solves many. These are their claims, NOT new experiment results. Public source can be in LLM training sets and is not guaranteed unseen.

## Original goal and leakage-proof split
- Parse top-level SMT-LIB/SyGuS s-expressions with balanced strings/comments, not a naive multi-line regex.
- At least three top-level constraints; remove only the LAST exact constraint from a separate evaluation copy. Preserve all earlier constraints, synth-fun grammar, set-logic, and check-synth. The solver MUST NOT see the last original input-output constraint during synthesis. Unsupported syntax => HOLD, no adaptation without post-first label.
- Run domain-expert C = native cvc5 SyGuS command line with original source grammar, <=15 seconds/task wall and <=12s CPU, 800 MiB sampled RSS watcher, at most one attempt/task. Pin and record cvc5 version before running. No neural run at G0.
- A nonempty cvc5 define-fun response is only a CANDIDATE. Independent Z3 or a separately implemented bitvector evaluator MUST verify source and heldout original IO and whole original task obligation. If that validation is not runnable, use HOLD, not PASS.
- For 8-bit cases, check functional novelty via all 256 input values against exact finite libraries, not AST order or new words. For 64-bit, strong SMT proof or a concrete counterexample; no random sampling claim of global proof.
- Preserve exact source Git blob/bytes hashes, source-only transformed input SHA, C stdout/stderr SHA, CPU/wall and RSS lower-bound samples, counts and code SHA. Candidate outputs FIRST frozen BEFORE gold grading. If execution bug, do not alter first receipt; post-first repair receives a distinct run/artifact.

## Discriminating questions and stop
- Does a professional solver with the *original grammar and permitted information* correctly predict the removed original constraint? A full-source synthesis solution is NOT a source-only transfer success.
- If C solves eligible cases within allotted resource, this corpus supplies no neural-only headroom at that budget. If C HOLD, classify C-specific bounded failure; it does not imply impossibility for other strong classic algorithms.
- Train A/B ownweight only after verified residual semantic gap and a separate frozen multi-author discovery protocol. No training budget, no new primitive, no Q PASS at this stage. Full hardware/energy/system amortization remains unknown.
- Invalid/missing data => NOT RUN/HOLD; report exactly and stop instead of cherry-picking.

### Preregistered implementation order
1. Freeze this document on research PR #616.
2. Freeze runner code independently BEFORE opening selected original source.
3. First runner selects 6+6 and runs source-only C; uploads first proposals.
4. Only then run independent original-heldout verifier V, preserve first result.
5. Admit learning only if strong C falls short and a verified, nonduplicate semantic gap exists.
