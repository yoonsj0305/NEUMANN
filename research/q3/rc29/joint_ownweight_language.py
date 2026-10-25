"""RC29c executable TWO-opcode language, both meanings supplied by own
PyTorch gate/reducer weights. The loop skeleton, bit types, parser, proof
and task labels remain HUMAN-authored. Full ORIGINAL torch weights are ZIP.
"""
import json,hashlib,re

def token(bits,kind):
    if kind not in ("PAIR","REDUCE") or len(bits)!=4 or any(v not in (0,1) for v in bits):
        raise ValueError("bad learned primitive")
    payload=json.dumps({"kind":kind,"arity":2,"value":list(bits)},sort_keys=True,separators=(",",":"))
    return "OWN_"+hashlib.sha256(payload.encode()).hexdigest()[:12]

# Both meanings really appeared as 12 own PyTorch learned sign vectors.
OWN_LEARNED_PAIRS=(((1,0,0,1),(0,0,0,1),1),  # XNOR + AND
                   ((0,1,1,0),(0,0,1,0),1)) # XOR + NAND-like accumulator

def emit_from_own_weight_signs(g,r,initial):
    if initial not in (0,1):raise ValueError("initial bit")
    return ("DEF "+token(g,"PAIR")+" PAIR\nTABLE "+''.join(map(str,g))+"\nEND\n"
            +"DEF "+token(r,"REDUCE")+" REDUCE\nTABLE "+''.join(map(str,r))
            +"\nEND\nINIT "+str(initial)+"\n")

class CertifiedComposer:
    def __init__(self):self.programs={}
    def register(self,program):
        if type(program)!=str or len(program)>1024:return {"status":"UNKNOWN_BAD_SOURCE"}
        regex=(r"DEF (OWN_[0-9a-f]{12}) PAIR\nTABLE ([01]{4})\nEND\n"
               r"DEF (OWN_[0-9a-f]{12}) REDUCE\nTABLE ([01]{4})\nEND\nINIT ([01])\n")
        m=re.fullmatch(regex,program)
        if not m:return {"status":"UNKNOWN_SYNTAX"}
        g=tuple(map(int,m.group(2)));r=tuple(map(int,m.group(4)));init=int(m.group(5))
        if m.group(1)!=token(g,"PAIR") or m.group(3)!=token(r,"REDUCE"):
            return {"status":"UNKNOWN_IDENTITY"}
        if init!=1 or not all(r[2*s+g[2*a+b]]==s*int(a==b)
                               for s in (0,1) for a in (0,1) for b in (0,1)):
            return {"status":"UNKNOWN_NO_ALL_LENGTH_PROOF"}
        name="PROGRAM_"+hashlib.sha256(program.encode()).hexdigest()[:12]
        self.programs[name]=(g,r,init)
        return {"status":"SCOPED_CERTIFIED","name":name}
    def compare(self,name,word,pattern):
        if name not in self.programs:raise ValueError("unverified grammar")
        if len(word)!=len(pattern):return False
        g,r,s=self.programs[name]
        for a,b in zip(word,pattern):
            if a not in (0,1) or b not in (0,1):raise ValueError("binary only")
            s=r[2*s+g[2*a+b]]
        return s==1
    def stream(self,name,word,pattern):
        if not pattern:raise ValueError("nonempty pattern")
        return tuple(int(i>=len(pattern)-1 and self.compare(name,word[i-len(pattern)+1:i+1],pattern)) for i in range(len(word)))
