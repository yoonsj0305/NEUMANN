# Q3X first CI erratum, frozen before any fresh NIA source bodies were read

First Q3X CI [#39103213463](https://github.com/yoonsj0305/NEUMANN/actions/runs/39103213463) FAILED on synthetic control B **BEFORE** evaluating any original source file. The original prereg's negative guard `x<=0 -> (x,y)` accidentally preserved `Post:y>=1` even when no relation was known, so the intended `Post-alone FAIL` negative comparator was mathematically invalid. This is not a CEGIS mechanism counterexample, not a NIA result, and must not be erased.

**Minimal correction to synthetic B, and NOTHING ELSE:** retain non-singleton original Pre (x=y=1 or 2), positive guarded branch `x>0 -> (x+y,x+y)`, all Q3W algorithm code, all Q3X original file path selection, caps, original source native parity and proof admissions unchanged. Change ONLY the otherwise idle impossible-for-reachable-state negative branch from `x<=0 -> (x,y)` to `x<=0 -> (x,y-5)`. This introduces an unreachable-in-the-sound-invariant-region step that makes Post-alone induction fail; `I:x=y AND Post:y>=1` blocks that guard and remains inductive.

No NIA or historical source bodies were opened by failed first run before the assertion. Retain both first and replay CI statuses, and maintain no global Q3 pass. This is an openly documented engineering-correction replay, **not** an untouched first synthetic evaluation.
