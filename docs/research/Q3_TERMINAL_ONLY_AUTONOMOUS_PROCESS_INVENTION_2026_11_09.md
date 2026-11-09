# NEUMANN 1 | Q3 Latent Multi-Step Program Invention from TERMINAL OBSERVATIONS ONLY

2026-11-09 · PR #732 · **new scoped Q3 evidence PASS** · unrestricted universal Q3 still OPEN

## A distinct failure mode was removed

The prior Q3 end-to-end experiment learned **both** a typed state transition and a reusable fixedpoint controller, but it required direct one-step input→successor labels to fit the transition AST. These intermediate observations are often unavailable for a true discovery task. A claim of autonomous process invention based only on final goals would have overstated that evidence.

This experiment removes **all** target-domain successor labels from the research interface. Only initial→terminal SOURCE examples and independent initial→terminal SOURCE checks are provided. The control method is separately learned and revised from earlier, unrelated source control tasks; it is compiled with each newly synthesized transition candidate.

The new \`TerminalOnlyProcessInventor\` enumerates typed expressions from the SAME generic previously existing instruction set, executes each candidate under the SOURCE-invented higher-order loop, and admits it only when:
- all training initial→final endpoints match;
- all independent source endpoint verifiers match;
- the loop terminates with a **full-state fixedpoint certificate**, not a loose predicate;
- a source execution demonstrates at least 3 transition calls (one-step constant/projection cheat rejected by the deliberately stated multi-step research gate);
- state growth remains within explicit finite safety/resource bounds;
- a known classical candidate source-verifies first, if provided.

Every admitted \`InventedLatentProcess\` is an executable composition of a newly constructed transition AST and an earlier independently source-discovered loop AST. It is **a source-compatible multi-step process**, not proof that the hidden physical/causal transition is uniquely identifiable.

## Production code and source-first independent scoring

- \`neumann1/terminal_only_process_inventor.py\`: entirely new *goal-to-process* synthesizer, accepts **zero source successor pairs**.
- \`NeumannEngine.meta_invent_terminal_only_process\` and \`RegistryEngine.meta_invent_terminal_only_process\`: live engine APIs.
- \`tests/test_terminal_only_process_inventor.py\`: integer/set/string, unseen input tests, two-engine integration, known-classical bypass, fail-closed independent source checks, indistinguishability counterexample.
- \`research/q3/q3_terminal_only_blind_first.py\`: first freeze final target predictions; only then in a separate invocation score the reference outcomes.
- \`.github/workflows/q3_terminal_only_process.yml\` and \`.github/workflows/q3_terminal_only_blind.yml\`.

At GitHub run **[42544725395](https://github.com/yoonsj0305/NEUMANN/actions/runs/42544725395)** the EXACT production module's test suite passed **7/7**.

At GitHub run **[42544725318](https://github.com/yoonsj0305/NEUMANN/actions/runs/42544725318)**, **300/300 fresh synthetic target states** were correctly predicted and independently scored after SHA lock. The scoring summary is stored in Actions artifact \`q3-terminal-only-300-source-frozen-programs\`, artifact ID \`13643166344\`.

Frozen prediction SHA-256: \`a4de5617d8cff973507ceab806ceb47b5f27dc4be2495d3ef6f2f92c245359e1\`.

| Source test type | Domain-target successor samples supplied | Newly generated process | Independently frozen terminal tests |
|---|---:|---|---:|
| Nonnegative integers | **0** | Source-induced iterative decrement to terminal zero | **100/100** |
| Finite sets of integers | **0** | Source-induced iterative smallest-element removal until empty | **100/100** |
| Strings over a/b | **0** | Source-induced repeated 'bb'→'b' rewrite until no change | **100/100** |
| **Total** | **0** | **3 executable processes** | **300/300** |

Test inputs extend far beyond source endpoint sizes. The method controller was independently synthesized through two source-driven revisions before any final-task processes were fit. No target scorer was used during program search. This is **not** an independently authored frontier problem benchmark: every source and target problem is researcher-authored synthetic data. One-step state transitions were supplied for earlier CONTROL learning, but **not** for the 3 target process families.

## What is proved and what is NOT

**Executable evidence:** Under the fixed typed instruction language, the meta system finds and independently checks three different source-compatible multi-step algorithms without observing target-domain step transitions. The same synthesizer implements all three and is integrated into both NEUMANN engines.

**Conditional mathematical correctness:** For a deterministic pure candidate update \`T\`, if the compiled loop observes \`T(s)=s\` before its max transition budget, the returned state is indeed a fixed point of the **candidate T**. The SOURCE endpoint checks certify the observed input/output pairs and reject misleading candidate programs on those samples.

**Unidentifiability theorem:** Terminal-only data cannot determine a unique hidden successor law. \`T1(n)=max(n-1,0)\` and \`T2(n)=max(n-2,0)\` yield terminal zero for every nonnegative integer, but differ at intermediate states. Thus no unrestricted method can establish the genuine hidden trajectory based only on these terminal observations. The tests explicitly preserve this counterexample.

**Still OPEN:** Strong independent-author frontier task wins, arbitrary new primitive invention, correct identification of unknown hidden state trajectories, unrestricted generalization outside the stated typed language, and full Q4 strongest-classical 10× cost. Q4 economics deliberately deferred as requested.

## Evidence and next decisive Q3 test

The primary new gap is not a faster search loop. It is recovering a **new useful representation or causal operation** where neither terminal observations nor a programmer-provided typed instruction set is rich enough to express the solution. The next strong falsifiable test is a SOURCE-frozen, independently authored target set in which:
1. no successor labels or task-specific solution templates are supplied;
2. the system must invent a new representation/constructor absent from its previous fixed DSL;
3. at least one original target is correct where strong classical/unchanged-grammar baseline fails;
4. the same learned constructor solves another unrelated semantic family WITHOUT per-family source adaptation.

Do NOT promote endpoint-only 300/300 synthetic success into an unrestricted universal Q3 proof.
