# NEUMANN 1 · P2.2 | Open executable program proposals from an external teacher
**2026-11-05 KST. Registration before viewing selected public evaluation task bodies.**

## Goal and basis
North Star: **Frontier-level problem solving with minimum necessary computation**. Q1–Q7 globally OPEN. P2.1/P2.1.1 found 0 additional correct original ARC tasks from adding fixed object-rewrite templates; STOP that family. P1.3 earlier demonstrated GPT-6 generated 4 executable programs on **public training**, but 4 source programs reused on novel tasks failed 0/24. P2.2 is an *independent public ARC-AGI-1 evaluation* replication of the program-proposal **interface** beyond a frozen DSL, not proof of an autonomous NEUMANN student.

## Source and irrevocable 8 original tasks
Official `fchollet/ARC-AGI` public **data/evaluation/** pinned git SHA `399030444e0ab0cc8b4e199870fb20b863846f34`. Exclude **all 96 task filenames** reserved in P2.1 and P2.1.1 (regardless of whether their source bodies were opened), leaving 304. Choose first **8** filenames sorted by unsigned FNV1a32(`neumann-q3-p22-20261105|`+basename), tie alphabetically. Commit manifest before ANY selected body fetch. This public set may be memorized by frontier pretraining and is NOT sealed unseen benchmark evidence.

## Teacher's exact information boundary
The ChatGPT GPT-6 teacher can see **only original `train:[{input,output}]` and `test:[{input}]`**. The connector fetch code MUST strip original test outputs **inside the tool call before tool text reaches the language model**. It must not print or return them in any interim tool message. Teacher is allowed to inspect training pairs and test *inputs*, and author **one pure JS program** `solve(grid)` per task or explicit ABSTAIN. Each program must be a generalized rule inferred from training pairs, NOT `if input===testInput return memorized output`, ID-based behavior, hardcoded single test grid, network calls, file reading, imported or executed arbitrary plugins, eval, execution sandbox escapes, or copy of a task's gold answer. Teacher can iterate reasoning *before* first proposal, not rerun after first score.

## Baselines, independent verification, first submission
- Freeze unchanged strong B=P1.1, Q=P1.6, P20=P2.0 and C211=P2.1.1 source blob identities before opening bodies.
- **First submitted source file** with all eight programs or explicit ABSTAIN must be committed before any original test gold is fetched into model-visible tool outputs or scored. Original test gold can only reach a separate scorer after this commit.
- For every proposed function, replay ALL original train examples first, independently check full output shapes/cells and errors; then evaluate ALL original test inputs and compare to upstream original test outputs. Invalid output/exception => FAIL or ABSTAIN, never PASS.
- Existing strong Direct baseline predicts via B/Q/P20 and optionally C211 on complete baseline abstention. Baseline wrong accepted original output counted separately; conflicts ABSTAIN.
- A teacher program solved original task only if every test output exact **and** all original training pairs exact. A teacher program returned as a prediction that is wrong on original test is a false accept, not silently deleted.
- Full run receipts: frozen task list, first source blob SHA, per-task exact outcomes including train/test grid counts, confidence/audit and nonmatching cases, full cost telemetry where measurable. Teacher **generation token/time/price/energy costs UNKNOWN** unless metered. JS execution milliseconds is NOT total discovery cost.
- Original task scoring MUST NOT use the task ID as a rule or return cached gold.

## Predeclared local decision
**LOCAL_TEACHER_PROGRAM_INTERFACE_PASS** only if first-submitted external teacher code solves >= **2** original public evaluation tasks that every strong baseline cannot solve, with **0 teacher false accepts**, **0 training inconsistencies for accepted programs**, full source identity and label-leakage audit. Exactly one additional => INCONCLUSIVE. Zero additional or any false accepted => FAIL. This local PASS proves only a useful **external teacher programming interface** on a small, public possibly contaminated sample, not NEUMANN's autonomous Q3 or a 10× cost advantage. All Q1–Q7 globally OPEN.
- Do not retune the same eight tasks after scoring. If any behavior changes, new experiment/version and new original task cohort.
- If teacher's generated functions cannot generalize to fresh task families when converted to a reusable policy, do not call them learned structure; store them as task-specific demonstrated programs only.

## Next stage only after source freeze
Extract **typed semantic ASTs and novelty vs frozen initial grammar**, then evaluate transport of patterns across new task families under matched classical Direct with full amortized costs. This is a separate, NOT RUN gate. Global status OPEN.
