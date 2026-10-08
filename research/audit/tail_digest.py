from pathlib import Path
import sys,re
root=Path(__file__).resolve().parents[2]
lo,hi=map(int,sys.argv[1:3])
for i in range(lo,hi+1):
 p=root/f'docs/experiments/v0.0.{i}.md'
 if not p.exists():continue
 t=p.read_text(encoding='utf-8-sig').splitlines(); tail=t[-75:]
 selected=[l for l in tail if re.search(r'result|decision|FAIL|PASS|KEEP|STOP|HOLD|REJECT|VISIBLE|UNREACHED|NO_.*OPPORTUNITY|ratio|headroom|recovery',l)]
 print(i,' '.join(selected)[-1000:])
