"""RC25 formal extracted languages + fail-closed parser regression."""
import pathlib,sys,itertools,random,collections
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc25"))
from learned_grammar import GENERATED,parse,run

def reference(task,word):
 s=0;out=[]
 for a,b in word:
  if task=="add":
   z=a+b+s;y=z%2;s=z//2
  elif task=="seen":s=max(s,a);y=s
  elif task=="parity":s=(s+a)%2;y=s
  out.append(y)
 return tuple(out)

def proof_product(task,text):
 start,table,alphabet=parse(text)
 q=collections.deque([(start,0)]);visited={(start,0)}
 while q:
  state,h=q.popleft()
  for symbol in alphabet:
   a,b=map(int,symbol)
   got,next_out=table[state][symbol]
   if task=="add":n=(a+b+h)//2;y=(a+b+h)%2
   elif task=="seen":n=max(h,a);y=n
   else:n=(h+a)%2;y=n
   assert next_out==y
   pair=(got,n)
   if pair not in visited:visited.add(pair);q.append(pair)
 assert len(visited)==2
 return True

def test_all_three_own_weight_extracted_grammars_proven():
 for task,text in GENERATED.items():
  assert proof_product(task,text)
  letters=[(0,0),(1,0)] if task!="add" else list(itertools.product((0,1),repeat=2))
  for n in range(1,6):
   for word in itertools.product(letters,repeat=n):
    assert run(text,word)==reference(task,word)

def test_undocumented_or_incomplete_grammar_is_rejected():
 original=GENERATED["add"]
 for bad in ("import os",original.replace("END","exec('x')"),original.replace("ON ","MOVE ",1),
             original.replace(" -> "," => ",1),original.replace("INITIAL ST_b5d1f15c17","INITIAL ST_ffffffffff"),
             original.replace("END","ON ST_1111111111 00 -> ST_1111111111 1\nEND"),
             original+original):
  try:parse(bad)
  except ValueError:pass
  else:raise AssertionError("untrusted grammar executed")
