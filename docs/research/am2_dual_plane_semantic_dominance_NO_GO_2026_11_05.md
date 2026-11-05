# NEUMANN 1 | AM2 Dual-Plane Semantic Dominance NO-GO
2026-11-05 KST | Source-level result + original opened controls | NOT actual frozen model evaluation

## Critical question
Can the newly introduced AM2 dual-plane runtime itself deliver a capability multiplier over a matched TOOL system with exactly the same frozen deterministic model and eligible tools?

**Conclusion: NO, not on the existing opened AM1 task schema.** The new runtime fixes a real control failure (no thought-channel final-JSON dependency), but its NEUMANN arm does not supply any additional executable semantics. Under a stable deterministic frozen core it produces the same final candidate as TOOL for each opened task, or rejects earlier due to extra checks.

## Conditional source-level proof
Let v be the canonical original model-visible view, t the unchanged authoritative task, E the same pure deterministic executor, and M the same deterministic model. Both arms are given v, the same M and original verifier, and identical eligible tool rights.

1. Math: visible_family(v) returns math_logic. TOOL sends expression and all bindings to the exact arithmetic tool. NEUMANN uses reduce_original to preserve the identical expression and exactly its referenced variables. Unused bindings cannot affect AST evaluation. Candidate values coincide.
2. CSP: visible_family(v) returns constraint_planning. The certified representation preserves every domain and every original constraint without transformation. Both arms run the same deterministic MRV CSP solver. Candidate assignments coincide.
3. Coding: visible_family(v) returns coding. In the current implementation, BOTH arms invoke model_generate(coding_prompt(v)) with the same output cap and thinking disabled. Hence M receives identical tokens and generates the same source. The same original Python subset worker, public examples, and original checker accept or reject it identically.
4. NEUMANN alone has extra certification failure points. If certificate fails the NEUMANN answer can only be absent, not a new correct candidate.

Subject to deterministic evaluation and unchanged model/task identity, the set of original-task successful NEUMANN outputs is a subset of the TOOL success set. Thus a +2/12 **capability** gain attributable to AM2 representation is unattainable for this implementation, not merely improbable. A different semantic proposer or executor must change the candidate before a paid/GPU matched capability run is scientifically warranted. The theorem does not assert identical wall times in nondeterministic operating environments or deny potential unrelated operational benefits.

## Constructive tests and first evidence
- [AM2 CI #42008933021](https://github.com/yoonsj0305/NEUMANN/actions/runs/42008933021) PASS: existing 5 model-free baseline tests, 10 original-checker/transport fixture tests, and 4 matched parity/authority tests.
- Fixture core tests are NOT actual Gemma 4 execution, not independent learned structural discovery and not Q5/Q6/Q7 evidence.
- Original opened-task control TOOL=8/12 and NEUMANN=8/12 with zero model calls already established. Coding model responses in the fixture were fabricated on purpose to test the interface, NEVER counted as model capability.
- Verified model-visible source binding: mutated public inputs cause ABSTAIN before tool/model and cannot be silently corrected from a different authoritative task.

## Decision
1. Keep the interface integrity tests and separate low-entropy control from open-ended source generation as an engineering prerequisite.
2. STOP GPU execution on this exact dual-plane AM2 candidate as a claimed architecture-multiplier capability test. The learned semantic path is not differentiated from TOOL.
3. Never lower TOOL privileges or omit its deterministic reductions just to engineer a positive result.
4. A truly new candidate must autonomously propose a meaningfully different executable representation or program, with exactly the same original verifier and identical model/tool authority for TOOL, then show successful original tasks beyond TOOL on opened data before any sealed evaluation.
5. Only the new candidate may get an independently preregistered opened capability/cost experiment. The original failed AM1 frozen record and Q1–Q7 OPEN are immutable.

## Evidence status
AM1 first accelerator verdict: FAIL and retained. AM2 no-model control: PASS. AM2 semantic-parity fixture: PASS. AM2 new accelerator multipler: NOT RUN. Q3 autonomous new semantics: NOT PROVEN. Q5 full efficiency: NOT PROVEN. Q6 unseen family transfer: NOT PROVEN. Q7 real frontier gap recovery: NOT PROVEN.