# CPU R0 release candidate — local integration result

Decision: **LOCAL_CPU_R0_RC_PASS_PENDING_REMOTE_CI**. Six of the seven requested
release checks have local evidence. Final remote CI is NOT RUN and public release
is not admitted. No upload, merge, model call, training, GPU, paid service or sealed
access occurred. This closes a bounded CPU packaging task, not NEUMANN's research.

## Frozen build and installation

- Starting local commit: `83e9abf09bafdd161c09ba40a4723b8eb8bc0855`.
- Fixed implementation source: `1e0524d5aae4f1b4f2afd215b065a47cba460904`.
- Wheel: `neumann1-0.0.106-py3-none-any.whl`, 510,027 bytes.
- Wheel SHA-256: `241ab25d1aa63a186e06d31abbaddd2de985e64dee9011a6c3fb04ec007a3bf0`.
- Exact committed pyproject/package files were exported by git archive to a
  separate snapshot; build did not consume the development checkout or editable
  installation. Snapshot SHA-256:
  `f7ed70ec762096cab25c44013a67d055f84b67ed30f35e03991177745281b25b`.
- Separate builder venv: build 1.3.0, setuptools 80.9.0, wheel 0.45.1; build 5.208 s.
- New runtime venv, system site packages disabled; non-editable wheel installation
  2.185 s; pip check PASS. Dependency versions and full logs are preserved.
- First post-install module import/identity process: **22.570 s**, preserved as
  initialization evidence. Later fresh-process requests reused OS file caches;
  their smaller launch times are not a virgin-machine startup measurement.
- Windows 11 x86_64, CPython 3.12.14; Intel i5-10400F, 6 cores / 12 logical CPUs.
  Thread controls OMP/OpenBLAS/MKL = 1. This is the tested platform only.
- cvc5 **CLI** 1.4.1, actual executable version output and archive/executable hashes
  recorded. Z3 4.15.4.0 independently checks original SyGuS obligations. Python
  cvc5 bindings are not used as a substitute for the executable.

[Installation contract](R0_CPU_INSTALL.md) and
[Windows dependency constraints](r0_cpu_windows_constraints.txt) describe the
retained module/JSONL entrypoint. No new loader, verifier or general runner was
implemented. The extra adds existing HiGHS/Z3 dependencies; SyGuS additionally
requires the external CLI. No native binaries, Q34 weights or evidence archives
are inside the wheel. Native COPYING/license notices and hashes are retained
privately. Wheel metadata currently declares no project license; a public
distribution license decision remains outside this local-install result.

## Seven-check release ledger

| Check | Result | Actual evidence |
|---|---|---|
| Fixed source wheel | PASS | source commit/archive, build log, wheel file list |
| Wheel identity and dependencies | PASS | SHA-256, METADATA, version locks, cvc5 --version |
| Clean independent installation | PASS | new venv, pip check, asserted site-packages import outside checkout |
| LP / Exact Linear / SyGuS original execution | PASS | 9 cold + 9 persistent receipts; 12 original certifications |
| Error / UNKNOWN / original verification | PASS | 6 invalid/singular receipts; missing CLI and missing weights checks; verifier fault tests |
| Results, time, memory, installation logs | PASS with stated limits | complete outer wall/stages; sampled process-tree RSS; unmeasured axes UNKNOWN |
| Final integrated remote CI and release scope | PENDING | local checks passed; remote CI NOT RUN; no public upload/release |

## Executed integration and test scope

Reused `experiments/hybrid_r0_release_gate_20261009.py` unchanged: task_suite,
sampled_process_tree_call and check_receipt. Only a private one-off packaging
orchestration supplies the installed Python and an outside-checkout working
directory. Historical first receipts were not rerun or overwritten. These are
new **engineering installation observations of opened fixtures**, not fresh F0,
G0, R1 or independent learned capability evidence.

Source: SyGuS-Org/benchmarks at
`13c8deb68a873635879c9a69bc78caebd340f646`,
`comp/2019/Inv_Track/From2018/ex1.sl`; exact reused bytes SHA-256
`930b37d15f14baf615c7e7741ef5d607db717390bb8465ad8255a0d12764125c`.
The other tasks reuse the previous gate's synthetic LP and exact-system fixtures.
9 requests are not 9 independent real-world originals; cold/warm observations
are repeats of the same tasks.

- Cold and JSONL: each 3 LP + 2 exact + 1 SyGuS VERIFIED; singular exact UNKNOWN;
  unsupported domain and malformed SyGuS ERROR. No unverified answer escaped.
- LP misleading external ranking exercised actual charged native fallback and
  original primal/dual verification; proposal acquisition cost remains UNKNOWN.
- SyGuS: all initiation/consecution/safety negations UNSAT in independent Z3.
  Mathematical Int/Bool semantics of the supported original grammar are the
  certified scope, not unrestricted program correctness or intent interpretation.
- No CLI: explicit DEPENDENCY_MISSING / UNKNOWN. No authorized Q34 assets in
  wheel: ERROR/UNKNOWN and no answer, zero model calls, no automatic download.
- Source tests: **59 passed, 58 subtests passed**, zero skips (runtime, SyGuS,
  F0 original bridge). Separate frozen North Star / Frontier contract / capture
  tests: **33 passed**, zero skips. Total 92 distinct selected tests.
- Installed wheel: the same 59 tests / 58 subtests passed, zero skips, with
  site-packages identity asserted before pytest and cwd outside checkout. This
  repeats regression coverage, not 59 additional scientific problems.
- An initial copied-test invocation used checkout cwd; its log is retained
  privately but excluded from independent wheel proof. The subsequent outside
  invocation removes that ambiguity. No failed integration receipt was discarded.

The minimal runtime change distinguishes actual SAT counterexamples (REJECTED)
from solver UNKNOWN/checker errors (UNKNOWN), preserves accepted=false for both,
and never authorizes execution without all three original proofs. Existing F0
verification behavior, certificate identifiers and original goal semantics remain.

## Cost and limits

| Observation | Outer process wall | Runtime request wall |
|---|---:|---:|
| First installed module import / identity | 22569.703 ms | not a problem-solving request |
| Cold LP native | 2744.639 ms | 1022.201 ms |
| Cold exact fractional | 1604.890 ms | 1.582 ms |
| Cold original SyGuS | 1915.207 ms | 300.357 ms |
| Single persistent process, all 9 requests | 1795.778 ms total | per-request stages preserved |

Persistent request walls: LP native 13.248 ms, exact fractional 1.575 ms, SyGuS
73.672 ms. These are one observed engineering batch, not a statistical speedup
comparison. Outer process time includes import/startup, IPC and shutdown; subtracting
runtime does not identify pure startup time. Startup is included in outer wall,
but its isolated attribution remains UNKNOWN.

Maximum 4 ms sampled process-tree RSS: **155,394,048 bytes (148.195 MiB)**. This is
a sampled lower bound, not an exact peak guarantee. Runtime's unsupported Windows
peak-memory field remains UNKNOWN; the external sampler supplies separate evidence.
Energy, FLOPs, monetary CPU cost, initial venv/dependency installation durations
and strict all-time peak are UNKNOWN. Paid calls and model/frontier calls are 0.
No claim of 10x economics, Frontier Gap recovery or Edge deployment is made.

## Preservation and next action

[Receipt manifest](../../research/development/r0-cpu-rc-2026-10-11/manifest.json)
links private originals to filesystem-path-redacted local copies; payloads, output,
cost values and certificate results are unmodified. Full private originals plus
the wheel/snapshot are in `R0_CPU_RC_2026-10-10/r0_cpu_rc_private_originals.zip`,
SHA-256 `ddb23a0c2335a95b6952850d510997a4813a9dfa51602acd952887c2d1b43c3e`.
No account subscription/quota metadata is exported. Historical research,
experiment code, original results and frozen contracts have no changed tracked
files relative to 83e9abf in the implementation commit.
All 43 exported copies match their manifest hashes. All 195 packaged Python
files match the committed snapshot bytes, and the private archive CRC check
passes. The final report commit changes no implementation or test bytes from
the wheel's fixed source commit.

Next single completion action: **when the user authorizes upload**, run CI against
this exact implementation and installation contract before public release. Until
then retain local RC status. Candidate recovery stays PARTIAL/closed, learning
HOLD, frozen Gemma BLOCKED_SMALL_MODEL_RUNTIME and Frontier Gap NOT_MEASURED.
Further R0 feature/solver expansion is not justified by this result.

## Final integrity and integration review (2026-10-11)

Current decision: **R0 LOCAL RC VERIFIED**, **NOT RELEASED**. The final remote CI
gate remains pending explicit upload authorization.

`1e0524d → e7bb00f` changes only documentation, agent/README guidance,
byte-preservation attributes and stored engineering evidence. Package Python,
pyproject/build dependencies, dependency constraints and tests are unchanged.
This follow-up adds CI wiring and derived audit records only. Keep the existing
wheel and its exact **build SHA 1e0524d**, not e7bb00f or the later report HEAD.
All 195 wheel Python files equal the current files; all 198 hashed RECORD entries
verify. The 43 retained public-copy hashes, matching private originals and private
archive hash verify. Previous test logs remain 92 selected source tests and 59
repeated installed-wheel tests, with no skips; no solver/model study was rerun.

### All eighteen requests

The [18-row classification CSV](../../research/development/r0-cpu-rc-2026-10-11/final-integration/request_classification.csv)
records mode, original/request hashes, expected and actual status, certificate
scope and unchanged timing. This table displays both modes separately by column.

| Retained task | Expected in each mode | Cold actual | Persistent actual | Verification |
|---|---|---|---|---|
| lp_native | VERIFIED | VERIFIED | VERIFIED | Original primal/dual certified |
| lp_residual | VERIFIED | VERIFIED | VERIFIED | Original primal/dual certified |
| lp_external_reject_fallback | VERIFIED | VERIFIED | VERIFIED | Rejected restricted path, actual fallback, original primal/dual certified |
| exact_fraction | VERIFIED | VERIFIED | VERIFIED | Exact original equations certified |
| exact_integer | VERIFIED | VERIFIED | VERIFIED | Exact original equations certified |
| sygus_original | VERIFIED | VERIFIED | VERIFIED | Original init/inductive/safe all UNSAT |
| exact_singular | UNKNOWN | UNKNOWN | UNKNOWN | no_unique_solution; no output/certificate, not an UNSAT claim |
| invalid_domain | ERROR | ERROR | ERROR | Unsupported input rejected before solver; no original proof |
| sygus_bad_source | ERROR | ERROR | ERROR | Unsupported source command rejected before solver; no original proof |

Thus **12 original-certified observations + 2 expected UNKNOWN + 4 expected ERROR**.
The six non-certified cases have no answer; they are expected safe outcomes rather
than six certified answers or six incorrectly labelled model failures. Repeated
modes and LP policies are not additional independent mathematical problems.

### External cvc5 identity

The actual local executable is
`<PRIVATE_RUN_ROOT>/native/cvc5-Win64-x86_64-static/bin/cvc5.exe`;
PRIVATE_RUN_ROOT is the private `Continuation/R0_CPU_RC_2026-10-10` folder, not
site-packages or the wheel. Actual version:
`cvc5 1.4.1 [git 2b2e844 on branch HEAD]`.
Executable SHA-256 remains
`04ee0af071fc18796ce9bf809fceac36e23893f8c2e42c829c4461bc9f0bec91`;
download ZIP SHA-256 remains
`1aaafe93484b5ed2cc8a74c2079242e85f160044afea647fadd3e794f7f7e50d`.
Both were rehashed and version output matched the retained log. Install the
external CLI on process PATH as described in R0_CPU_INSTALL.md; Python bindings
are not its replacement. No executable is bundled in the wheel.

### Verified PR ancestry and prepared CI

Read-only GitHub metadata, exact-head pull-request CI records and git ls-remote
agree with local Git objects. Main is still `55178a2`; all six PRs are OPEN and
unmerged. #174 is non-Draft; #175–#179 are Draft.

| PR | Current HEAD | Actual base | Queried HEAD CI |
|---|---|---|---|
| #174 | a011918 | main | SUCCESS |
| #175 | fb23dca | main; contains #174 ancestry | SUCCESS |
| #176 | c182fd3 | #175 branch | SUCCESS |
| #177 | 5cbda9d | #176 branch | SUCCESS |
| #178 | 986d774 | #177 branch | SUCCESS |
| #179 | a8ad955 | #178 branch | SUCCESS |

Each preceding HEAD is an ancestor of the next and of e7bb00f. At that reviewed
local HEAD, #179 is 13 commits behind and has zero commits absent locally. After
authorization and another remote check, publish the existing local history by
fast-forward to `research/f0-opened-original-comparison-20261009` (#179). Do not
squash, rebase, force-push, merge into main or merge storage-only evidence branches.
The earlier successful CI runs do not validate the unpublished local HEAD.

The existing wheel workflow previously matched only a historical push branch and
workflow-file path. Its minimal integration update enables scoped PR/manual
triggers, explicitly checks out the PR HEAD, uses the already tested dependency
lock, pins official Linux cvc5 CLI 1.4.1 with archive SHA-256, preserves build/source
and native identities, and reuses the unchanged 18-request gate plus installed
regression tests. It is **prepared, not executed**. YAML and all three embedded
Python blocks parse locally; Linux download/install and remote job success remain
unverified until approved upload. No package runtime or dependency change requires
a replacement local wheel.

[Final integrity receipt](../../research/development/r0-cpu-rc-2026-10-11/final-integration/integrity_summary.json)
and [read-only PR/CI snapshot](../../research/development/r0-cpu-rc-2026-10-11/final-integration/remote_pr_snapshot.json)
bind this review. Scope stays Classical-Hybrid CPU LP, exact linear and restricted
SyGuS only. No new learning, Gemma contract change, GPU, paid call, sealed access
or Frontier Gap evidence is admitted.
