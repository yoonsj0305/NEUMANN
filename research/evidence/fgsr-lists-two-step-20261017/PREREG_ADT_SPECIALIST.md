# ADT specialist classical validity screen: freeze before running

Date 2026-10-17. **Already OPENED real source** (not learned/validation holdout). The existing original Lists-4 was decided by a post-inspection HUMAN-supplied invariant, independently checked 12/12, while initial generic Z3/Eldarica fixed budgets timed out. This screen tests the strongest **relevant specialized classical** solver, to avoid attributing a real-source result to structural AI where an existing domain solver suffices.

## Frozen input and single treatment
- RustHorn origin `chc-comp/rust-horn`, immutable commit `e5a86a1ad252fe1df75e06814769ec1d14540032` and original file `lists-4-inc-some2-safe.smt2` SHA256 `a73dd31be612a9d01efee2c9d1aad59ae7c3ec9a84ba51d5d450ca4100a5b6db`, Git blob `5386fa67ac0248f9e8a3c4eb15465e1cac61d0b9`. No source rewriting, theorem hints, type repairs, or hand-authored invariants fed to Catalia.
- Catalia (HoIce ADT specialist) official `hopv/catalia` pinned commit `5ee6493e996863c8ec22c42d786822d6af39c7f6` (2026-10-06). Build using `cargo install --git … --rev … --locked`, max build job time 8min. Record exact build success/error; compiler artifacts do not count as proof.
- Call binary `hoice` on the original SMT2 with Z3 CLI installed from runner, one process, 30-second OS-enforced timeout, no fallback/multiple solver versions after seeing outcome. Record Z3 --version, full command, exit code, stderr diagnostics, solver status, wall time, original source identities, Catalia commit.
- Classify `SAT`/ `UNSAT` only if **one exact standalone status token** and process exit=0; `UNKNOWN`, `TIMEOUT`, unsupported/parser error or install failure distinct. SAT for CHC source usually means a safe invariant model exists; **solver report is not independently verified model proof**, unlike our original posthoc certificate.
- Explicit **stop condition:** if Catalia decides within 30s, further model-finetuning on this opened family cannot claim a discovered algorithmic gap. If Catalia fails/unsupported, neither that nor the prior two timeouts proves a universal strong-classical limit.
- Prevent claim laundering: no learned model, no parameter training, no paid model/API/GPU, no frontier reference, no new unseen source-family transfer. Original first-run results and all Q1–Q7 remain OPEN.

## Reproducibility and cost scope
Original solver wall includes process launch but not Rust compilation, package installation or source download. Store build wall separately. GitHub Actions green means the intended diagnostic was recorded, NOT a theorem; science result is in the immutable raw receipt. A failed install is `BLOCKED`, never renamed a solver failure.
