# CPU R0 installation contract

Scope: classical-only LP, exact rational linear systems and restricted SyGuS
loop invariants. This is a CPU engineering release candidate; it does not admit
learning, establish Frontier Gap or close a global research question.

Install with `python -m pip install -c r0_cpu_windows_constraints.txt "neumann1[cpu-r0] @ file:///absolute/path/to/neumann1-0.0.106-py3-none-any.whl"`
using the release's frozen dependency lock (use a properly escaped wheel URI).
The `cpu-r0` extra adds HiGHS and Z3;
it does **not** install the native cvc5 executable. The existing `recursive`
extra's Python cvc5 bindings do not supply that CLI either.

SyGuS requires **cvc5 CLI 1.4.1** on the process PATH. The existing adapter calls
`cvc5 --sygus --lang=sygus2 input.sy`; independent Z3 verifies initiation,
consecution and safety against the original source. A missing executable returns
UNKNOWN with DEPENDENCY_MISSING and no answer. SAT obligations reject a candidate;
UNKNOWN or checker errors do not certify it and are not counted as counterexamples.

The tested Windows x86_64 dependency is the official
[cvc5 1.4.1 static distribution](https://github.com/cvc5/cvc5/releases/tag/cvc5-1.4.1).
Archive SHA-256: `1aaafe93484b5ed2cc8a74c2079242e85f160044afea647fadd3e794f7f7e50d`.
`bin/cvc5.exe` SHA-256: `04ee0af071fc18796ce9bf809fceac36e23893f8c2e42c829c4461bc9f0bec91`.
Extract it outside the checkout, retain COPYING and bundled license notices,
verify both hashes and `cvc5 --version`, then add its bin directory to the current
shell's PATH. Do not substitute a different release silently. The static binary
includes LGPL-covered dependencies; it is not redistributed inside this wheel.
See the [official installation guidance](https://cvc5.github.io/downloads.html).

Build from a clean, identified source commit with the pinned setuptools/wheel
backend in pyproject.toml. Preserve the build log, wheel hash, METADATA dependency
list and complete installed version lock. Install non-editably in a new venv
without system site packages. Run from a directory outside the development
checkout with PYTHONPATH unset; verify the imported module is in that venv's
site-packages. `python -m neumann1.hybrid_runtime_r0 --jsonl` is the retained entry
point; no new runner is required.

No Q34 checkpoints or research archives are bundled; frozen-model requests
without their authorized assets must fail closed. Runtime never downloads them.
The tested platform and source/wheel identity are recorded in the accompanying
release receipt. Windows validation is not a claim about all supported Python
versions or other operating systems. Remote CI and public release require separate
confirmation; local installation success does not imply either.
