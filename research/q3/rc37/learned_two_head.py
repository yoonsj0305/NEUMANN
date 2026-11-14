"""Own-weight generated semantic code (Torch seed3704), NOT source trainer.
Human supplied two READ_REL heads, tensor memory interface and grammar parser.
"""
from itertools import product
ABC="ABC"
LEARNED={"addresses":(3,-2),"table":(
 ((0,0,0,0),)*4,
 ((1,1,1,1),(1,1,1,1),(0,1,1,1),(1,1,1,1)),
 ((2,2,2,2),)*4)}
def run(code,s):
 if type(s)!=str or any(x not in ABC for x in s):raise ValueError("alphabet")
 a,b=code["addresses"];out=[]
 for i,c in enumerate(s):
  j=i+a;k=i+b
  v=ABC.index(s[j]) if 0<=j<len(s) else 3
  w=ABC.index(s[k]) if 0<=k<len(s) else 3
  out.append(ABC[code["table"][ABC.index(c)][v][w]])
 return "".join(out)
def target(s):
 return "".join("A" if c=="B" and i>=2 and i+3<len(s) and s[i-2]=="A" and s[i+3]=="C" else c for i,c in enumerate(s))
def one_head_witness(d):
 n=31;i=15;a=list("B"*n);a[i-2]="A";a[i+3]="C";b=a.copy()
 b[i+3 if d==-2 else i-2]="B"
 a="".join(a);b="".join(b);j=i+d
 assert (a[j] if 0<=j<n else "^")==(b[j] if 0<=j<n else "^")
 assert a[i]==b[i] and target(a)[i]!=target(b)[i]
 return a,b
def prove_compiled(code):
 a,b=code["addresses"]
 if (a,b) not in ((-2,3),(3,-2)):return "UNKNOWN_BAD_COORDINATES"
 for n in range(1,11):
  for i in range(n):
   places=sorted(set(x for x in (i,i+a,i+b,i-2,i+3) if 0<=x<n))
   for xs in product(ABC,repeat=len(places)):
    m=dict(zip(places,xs))
    s="".join(m.get(k,"B") for k in range(n))
    if run(code,s)[i]!=target(s)[i]:return "FAIL"
 return "PROVED_COMPILED_ALL_FINITE_WORDS"
