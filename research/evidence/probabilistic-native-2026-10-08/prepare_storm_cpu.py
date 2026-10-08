"""Bounded official-wheel preparation. No new scientific performance measurement."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
import subprocess
import sys
import time

root = Path('/kaggle/working/neumann_probabilistic')
root.mkdir(exist_ok=False)
contract = {
    'kind': 'ENGINEERING_PREPARATION_ONLY', 'candidate': 'Existing G0 A',
    'registered_utc': datetime.now(timezone.utc).isoformat(),
    'budget_seconds': 180, 'install_timeout_seconds': 90,
    'official_package': 'stormpy==1.14.0', 'binary_only': True,
    'expected_wheel_sha256': 'a4ad300dde7b26ce995a750aa1c2363713f5e1a34d3e6d276a0e9d34512676da',
    'source_commit': 'd22615ca859f1518015c065414dd0a36c4615484',
    'no_compilation': True, 'no_gpu': True, 'no_training': True,
    'no_performance_screening': True, 'scope': 'Import and inspect available exact/symbolic/native APIs only'
}
(root/'preparation-contract-first.json').write_text(json.dumps(contract,indent=2))
started=time.monotonic()
log=root/'wheel-install-first.log'
with log.open('wb') as out:
    proc=subprocess.run([sys.executable,'-m','pip','--isolated','install','--index-url','https://pypi.org/simple','--only-binary=:all:',
                         '--target',str(root/'deps'),'--report',str(root/'install-first.json'),'stormpy==1.14.0'],
                         stdout=out,stderr=subprocess.STDOUT,timeout=90)
assert proc.returncode==0, 'Official wheel installation failed; no compilation rescue'
install=json.loads((root/'install-first.json').read_text())
package=next(x for x in install['install'] if x['metadata']['name'].lower()=='stormpy')
assert package['download_info']['archive_info']['hashes']['sha256']==contract['expected_wheel_sha256'], 'Wheel identity mismatch'
sys.path.insert(0,str(root/'deps'))
import stormpy
receipt={'status':'OFFICIAL_WHEEL_IMPORT_READY', 'wall_seconds':time.monotonic()-started,
         'version':stormpy.__version__, 'python':sys.version, 'platform':platform.platform(),
         'cpu_count':os.cpu_count(), 'cpu_info':Path('/proc/cpuinfo').read_text(),
         'available_apis':{k:getattr(stormpy,k).__doc__ for k in ['build_sparse_exact_model','build_sparse_parametric_model','build_symbolic_parametric_model',
                          'perform_sparse_bisimulation','perform_symbolic_bisimulation','transform_to_sparse_model','model_checking','export_to_drn']},
         'G0':'NOT_EXECUTED', 'learning':'HOLD'}
(root/'preparation-first.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({k:v for k,v in receipt.items() if k not in ['cpu_info','available_apis']},indent=2),flush=True)
