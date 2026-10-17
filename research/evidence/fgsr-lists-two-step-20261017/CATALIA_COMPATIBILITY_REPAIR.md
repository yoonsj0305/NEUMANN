# Catalia ABI/CLI compatibility repair, separate from first frozen science result

Date: 2026-10-17. This is a **new, developer-exposed environment repair**, not an amendment to the previous preregistration's first run.

## Immutable first run
- [Catalia first run #39036134708](https://github.com/yoonsj0305/NEUMANN/actions/runs/39036134708), artifact **12102103384**. Catalia git `5ee6493e996863c8ec22c42d786822d6af39c7f6` built SUCCESS in **48,248.814 ms** using Cargo 1.99.0; source identities verified. System Z3 binary was **4.8.12**. Catalia exited code **2** after **225.810 ms**, stdout `(error "Broken pipe (os error 32)")` and verbose Z3 parameter-help text on stderr. Classification `SPECIALIST_ERROR_OR_UNSUPPORTED`, absolutely **NOT** timeout nor inability to prove original. Preserve original raw artifact unchanged.

## Exactly one justified environment repair
- Catalia official README recommends **Z3 4.12.0** and explicitly warns some older/newer Z3 versions may not work. Install **Z3 4.12.5** official prebuilt Linux x64 archive exactly once, no version sweep or solver-flag tuning. Chosen historical supported-version family on documented compatibility grounds, not benchmark performance.
- Frozen official URL: `https://github.com/Z3Prover/z3/releases/download/z3-4.12.5/z3-4.12.5-x64-glibc-2.35.zip`. Record SHA-256, observed exact executable version, and archive file size prior to test. Reject if observed version is not **4.12.5**.
- Keep `Catalia` commit, original RustHorn source SHA, original invocation (`hoice <exact original file>`), compilation command, 30 s solver process cap, CPU environment and no semantic hints unchanged. Provide no second alternative if this version fails.
- The first run belongs to the original frozen screen. This retry receives **`COMPATIBILITY_RETRY`** prefix and cannot count as the first pristine classical outcome. If the second environment fails, verdict is a tooling blocker, not proof of source hardness.
- No neural model calls, no learned success, no source opening reset, Q1–Q7 all remain OPEN. Full human witness invention cost still unmeasured.

## Meaning
Avoid wrong conclusion from Catalia's observed broken pipe. An experiment that tests tool compatibility is not a capability benchmark; a real solver status is required to claim Catalia decided anything.
