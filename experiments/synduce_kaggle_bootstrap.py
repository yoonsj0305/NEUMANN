"""CPU-only upstream build setup; not a scored synthesis/performance experiment."""
from pathlib import Path
import hashlib
import json
import os
import platform
import subprocess
import time

ROOT = Path('/kaggle/working/neumann-synduce')
ROOT.mkdir(exist_ok=True)
OUT = ROOT / 'build-evidence'
OUT.mkdir(exist_ok=True)
PIN = 'b5c1d1611d3fbf5d8cdf9a23fde52c2cbba95a89'
ENV = dict(os.environ, OPAMROOT=str(ROOT / 'opam'), OPAMYES='1', OPAMJOBS='4',
           DEBIAN_FRONTEND='noninteractive')
COMMANDS = [
    ['apt-get', 'update', '-qq'],
    ['apt-get', 'install', '-y', '-qq', 'opam', 'build-essential', 'm4', 'pkg-config',
     'z3', 'cvc5', 'git', 'curl', 'unzip', 'libgmp-dev'],
    ['git', 'clone', 'https://github.com/synduce/Synduce.git', str(ROOT / 'source')],
    ['git', '-C', str(ROOT / 'source'), 'checkout', '--detach', PIN],
    ['opam', 'init', '--bare', '--disable-sandboxing', '--no-setup', '-y'],
    ['opam', 'switch', 'create', 'neumann', 'ocaml-base-compiler.5.0.0', '-y', '--jobs=4'],
    ['opam', 'install', '--switch=neumann', str(ROOT / 'source'), '--deps-only', '-y', '--jobs=4'],
    ['opam', 'exec', '--switch=neumann', '--', 'dune', 'build', 'bin/Synduce.exe', '-j', '4'],
    ['opam', 'list', '--switch=neumann', '--installed', '--columns=name,version'],
    ['opam', 'switch', 'export', '--switch=neumann', str(OUT / 'switch.export')],
    ['z3', '--version'],
    ['cvc5', '--version'],
    [str(ROOT / 'source/_build/default/bin/Synduce.exe'), '-h'],
]
events = []
start = time.perf_counter()
for index, command in enumerate(COMMANDS):
    print(f'BUILD_STEP {index}: {command}', flush=True)
    t = time.perf_counter()
    with (OUT / f'step-{index:02}.log').open('w') as log:
        child = subprocess.run(command, cwd=ROOT / 'source' if index >= 7 else ROOT,
                               env=ENV, stdout=log, stderr=subprocess.STDOUT, timeout=3600)
    event = {'index': index, 'command': command, 'exit_code': child.returncode,
             'seconds': time.perf_counter() - t,
             'log_sha256': hashlib.sha256((OUT / f'step-{index:02}.log').read_bytes()).hexdigest()}
    events.append(event)
    (OUT / 'events.json').write_text(json.dumps(events, indent=2) + '\n')
    print(json.dumps(event), flush=True)
    if child.returncode:
        print((OUT / f'step-{index:02}.log').read_text()[-5000:], flush=True)
        raise RuntimeError(f'build step {index} failed; preserve evidence, repair setup separately')
manifest = {'kind': 'ENGINEERING_BUILD_ONLY', 'source_commit': PIN,
            'platform': platform.platform(), 'cpu_count': os.cpu_count(),
            'gpu_requested': False, 'elapsed_seconds': time.perf_counter() - start,
            'events': events, 'benchmarks_executed': False, 'G1_admitted': False}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('PASS_UPSTREAM_BUILD_ONLY', flush=True)
