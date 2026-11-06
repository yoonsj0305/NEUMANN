"""Q3 RC36: compiled executable rule semantics extracted from REAL frozen
37-weight PyTorch actors. Source-only trained weights (all 18 including
failures), original first prediction bytes, complete parser and verifier,
are in SHA-verified 58-file standalone ZIP. This code is only the compact
extracted first certified program per task, not original training weights.

The model GENERATED signed -2/+2/-3 relative access and 12-row behavior;
generic READ_REL interpreter/alphabet are HUMAN-DEFINED. Global Q3 OPEN.
"""
import hashlib,json,re

FROZEN_COMPILED={
 "A":{"relative_access_offset":-2,"symbol_table":[[0,0,0,0],[2,1,1,1],[2,2,2,2]]},
 "B":{"relative_access_offset":2,"symbol_table":[[0,0,0,0],[1,1,0,1],[2,2,2,2]]},
 "C":{"relative_access_offset":-3,"symbol_table":[[0,0,1,0],[1,1,1,1],[2,2,2,2]]},
}
ABC="ABC";READS="ABC^"
def token(p):
    txt=json.dumps({"offset":p["relative_access_offset"],
        "table":p["symbol_table"]},sort_keys=True,separators=(",",":"))
    return "AUTO_REL_"+hashlib.sha256(txt.encode()).hexdigest()[:12]

def compiled_text(p):
    off=p["relative_access_offset"]
    if type(off)!=int or abs(off)>7:raise ValueError("unknown read range")
    t=p["symbol_table"]
    if len(t)!=3 or any(len(row)!=4 for row in t):raise ValueError("shape")
    out=[f"DEF {token(p)}",f"ACCESS READ_REL {off:+d}"]
    for i,c in enumerate(ABC):
        for j,n in enumerate(READS):
            z=t[i][j]
            if type(z)!=int or z not in (0,1,2):raise ValueError("bad char")
            out.append(f"CASE CUR={c} LOOK={n} EMIT={ABC[z]}")
    return "\n".join(out+["END"])+"\n"

def parse(s):
    if type(s)!=str or len(s)>1000:raise ValueError("syntax length")
    lines=s.splitlines()
    if len(lines)!=15 or lines[-1]!="END":raise ValueError("syntax")
    name=re.fullmatch(r"DEF (AUTO_REL_[0-9a-f]{12})",lines[0])
    directive=re.fullmatch(r"ACCESS READ_REL ([+-][0-9]+)",lines[1])
    if name is None or directive is None:raise ValueError("access")
    offset=int(directive.group(1))
    if abs(offset)>7:raise ValueError("offset bound")
    mapping={}
    for l in lines[2:14]:
        m=re.fullmatch(r"CASE CUR=([ABC]) LOOK=([ABC^]) EMIT=([ABC])",l)
        if m is None:raise ValueError("undeclared language")
        k=(m.group(1),m.group(2))
        if k in mapping:raise ValueError("duplicate")
        mapping[k]=m.group(3)
    if len(mapping)!=12:raise ValueError("incomplete")
    code={"relative_access_offset":offset,
          "symbol_table":[[ABC.index(mapping[c,n]) for n in READS] for c in ABC]}
    if name.group(1)!=token(code):raise ValueError("wrong program hash")
    return code

def run(s,w):
    if type(w)!=str or any(c not in ABC for c in w):raise ValueError("input")
    p=parse(s);d=p["relative_access_offset"];t=p["symbol_table"];out=[]
    for i,c in enumerate(w):
        j=i+d;n=w[j] if 0<=j<len(w) else "^"
        out.append(ABC[t[ABC.index(c)][READS.index(n)]])
    return "".join(out)

class Gate:
    def __init__(self):self.allowed={}
    def admit(self,s,task,independent_verifier):
        try:p=parse(s)
        except (TypeError,ValueError):return {"status":"UNKNOWN_BAD_GRAMMAR"}
        if task not in FROZEN_COMPILED:return {"status":"UNKNOWN_TASK"}
        if not independent_verifier(p,task):return {"status":"UNKNOWN_NO_PROOF"}
        name=token(p);self.allowed[name]=s
        return {"status":"SCOPED_VERIFIED","token":name}
    def execute(self,name,w):
        if name not in self.allowed:raise ValueError("unauthorized syntax")
        return run(self.allowed[name],w)
