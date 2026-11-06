"""RC38 compact compiled program, not source trainer or Torch checkpoints.
Original model grew 0..4 remote read instructions using 62 separately fitted
new-opcode scorer weight tensors. Human defined READ_REL syntax, CREATE
control, source conflicts, minimizer, verifier and parser.
"""
from itertools import product
import re,hashlib
ABC="ABC"
REFERENCE={"zero":(), "one":((-3,"A"),),
 "two":((-2,"A"),(3,"C")),
 "three":((-4,"A"),(1,"C"),(5,"B")),
 "alternate":((-5,"C"),(-1,"A"),(4,"B")),
 "four":((-6,"A"),(-2,"C"),(2,"B"),(6,"A"))}
# Semantically minimized original weight-derived READ_REL declarations.
LEARNED={"zero":(), "one":((-3,"A"),),
 "two":((3,"C"),(-2,"A")),
 "three":((5,"B"),(-4,"A"),(1,"C")),
 "alternate":((-5,"C"),(4,"B"),(-1,"A")),
 "four":((6,"A"),(-6,"A"),(2,"B"),(-2,"C"))}
class Rejected(ValueError):pass
def emit(reads):
 if len(reads)>6 or len(set(d for d,v in reads))!=len(reads):
  raise Rejected("duplicate or excess")
 body=["DEF AUTO_GROW","WHEN CUR=B"]
 for d,v in reads:
  if type(d)!=int or not -7<=d<=7 or d==0 or v not in ABC:
   raise Rejected("unsupported offset or symbol")
  body.append(f"CREATE_READ_REL {d:+d} REQUIRE {v}")
 return "\n".join(body+["EMIT A","ELSE COPY","END"])+"\n"
def parse(src):
 if type(src)!=str or len(src)>1000:raise Rejected("budget")
 lines=src.splitlines()
 if len(lines)<5 or lines[:2]!=["DEF AUTO_GROW","WHEN CUR=B"] or lines[-3:]!=["EMIT A","ELSE COPY","END"]:
  raise Rejected("unknown syntax")
 out=[]
 for line in lines[2:-3]:
  m=re.fullmatch(r"CREATE_READ_REL ([+-][1-7]) REQUIRE ([ABC])",line)
  if not m or any(int(m[1])==d for d,v in out) or len(out)==6:
   raise Rejected("invalid instruction")
  out.append((int(m[1]),m[2]))
 return tuple(out)
def run(reads,word):
 if type(word)!=str or any(c not in ABC for c in word):raise Rejected("word")
 return "".join("A" if c=="B" and all(0<=i+d<len(word) and word[i+d]==v for d,v in reads)
                else c for i,c in enumerate(word))
def prove_under_supplied_contract(task,reads):
 ref=REFERENCE.get(task)
 return ref is not None and len(reads)==len(ref) and dict(reads)==dict(ref)
def authorize(task,src):
 try:reads=parse(src)
 except Rejected:return {"status":"UNKNOWN_BAD_SYNTAX"}
 if not prove_under_supplied_contract(task,reads):
  return {"status":"UNKNOWN_NOT_ALL_LENGTHS_PROVEN"}
 return {"status":"SCOPED_CERTIFIED",
         "token":"AUTO_GROW_"+hashlib.sha256(src.encode()).hexdigest()[:12]}
def lower_bound_witness(task,d):
 requirements=dict(REFERENCE[task]);assert d in requirements
 n=41;i=20;a=list("B"*n)
 for offset,c in requirements.items():a[i+offset]=c
 b=a.copy();b[i+d]=next(c for c in ABC if c!=a[i+d])
 u,v="".join(a),"".join(b)
 assert all(u[i+x]==v[i+x] for x in requirements if x!=d)
 assert run(REFERENCE[task],u)[i]!=run(REFERENCE[task],v)[i]
 return u,v
