"""RC25 extracted exact own-weight-generated MEALY grammar text.

The model-generated state labels came from signed behavioral signatures on
frozen PyTorch tensors, not researcher-provided carry/seen/parity labels.
SOURCE Python compiler/parser architecture HUMAN-provided (see original ZIP).
These runnable minimal programs are only 3 selected from 11 certified seeds.
"""
import re
GENERATED = {
 "add": """MACHINE MEALY_BOOL_V1
INITIAL ST_b5d1f15c17
ON ST_b5d1f15c17 00 -> ST_b5d1f15c17 0
ON ST_b5d1f15c17 01 -> ST_b5d1f15c17 1
ON ST_b5d1f15c17 10 -> ST_b5d1f15c17 1
ON ST_b5d1f15c17 11 -> ST_3743df1303 0
ON ST_3743df1303 00 -> ST_b5d1f15c17 1
ON ST_3743df1303 01 -> ST_3743df1303 0
ON ST_3743df1303 10 -> ST_3743df1303 0
ON ST_3743df1303 11 -> ST_3743df1303 1
END
""",
 "seen": """MACHINE MEALY_BOOL_V1
INITIAL ST_923682bea6
ON ST_923682bea6 00 -> ST_923682bea6 0
ON ST_923682bea6 10 -> ST_e718fe8edf 1
ON ST_e718fe8edf 00 -> ST_e718fe8edf 1
ON ST_e718fe8edf 10 -> ST_e718fe8edf 1
END
""",
 "parity": """MACHINE MEALY_BOOL_V1
INITIAL ST_923682bea6
ON ST_923682bea6 00 -> ST_923682bea6 0
ON ST_923682bea6 10 -> ST_fad748aa45 1
ON ST_fad748aa45 00 -> ST_fad748aa45 1
ON ST_fad748aa45 10 -> ST_923682bea6 0
END
"""
}
def parse(text):
 if not isinstance(text,str) or len(text)>15000:raise ValueError("bound")
 lines=text.strip().splitlines()
 if len(lines)<4 or lines[0]!="MACHINE MEALY_BOOL_V1" or lines[-1]!="END":raise ValueError("syntax header")
 m=re.fullmatch(r"INITIAL (ST_[0-9a-f]{10})",lines[1])
 if m is None:raise ValueError("initial")
 table={}
 for line in lines[2:-1]:
  m=re.fullmatch(r"ON (ST_[0-9a-f]{10}) ([01]{1,2}) -> (ST_[0-9a-f]{10}) ([01])",line)
  if not m:raise ValueError("invalid instruction")
  src,symbol,target,out=m.groups()
  row=table.setdefault(src,{})
  if symbol in row:raise ValueError("duplicate")
  row[symbol]=(target,int(out))
 if m and len(table)>16:raise ValueError("state cap")
 if m is None or lines[1].split()[-1] not in table:raise ValueError("missing initial")
 alphabet=set(next(iter(table.values())))
 if any(set(row)!=alphabet for row in table.values()):raise ValueError("incomplete alphabet")
 if any(t not in table for row in table.values() for t,_ in row.values()):raise ValueError("unbound state")
 return lines[1].split()[-1],table,alphabet

def run(text,word):
 state,table,alph=parse(text)
 result=[]
 for letter in word:
  name=''.join(str(c) for c in letter)
  if name not in alph:raise ValueError("unexpected input")
  state,y=table[state][name]
  result.append(y)
 return tuple(result)
