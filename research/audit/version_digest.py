import re, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
lo,hi=map(int,sys.argv[1:3])
limit=int(sys.argv[3]) if len(sys.argv)>3 else 900
for i in range(lo,hi+1):
 p=root/f'docs/experiments/v0.0.{i}.md'
 if not p.exists():
  print(i,'MISSING HEAD'); continue
 t=p.read_text(encoding='utf-8-sig')
 sections=re.split(r'(?m)^## ', t)
 selected=[]
 for s in sections[1:]:
  title,_,body=s.partition('\n')
  if re.search(r'question|hypothesis|finding|result|decision|interpret|next|conclusion',title,re.I):
   lines=[x for x in body.splitlines() if x.strip()]
   selected.append(title+': '+' '.join(lines)[:limit])
 print(i,t.splitlines()[0],'\n'+'\n'.join(selected)[:limit*3])
