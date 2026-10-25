"""RC20 compact extract: OWN-weight sampled INTEGER arithmetic memory.
Full PyTorch tensors/first SHA are in independent SHA-audited research ZIP.
Human authored 9-slot ISA/template, training/search engine, oracle and proof.
The neural policy proposed the frozen instruction tuple, not a novel base ISA.
"""
import hashlib,json,math

FROZEN_LEARNED_CODE=(1,1,0,1,0,0,0,0,0)
FROZEN_FIRST_OOD_SHA256="0368e479c458f22ef17ee8ec03507968b152f4103ddfcd064c50e38a225cfa34"

def universal_radix_proof(code):
    """Algebraic class proof for ALL k>=2, all finite streams."""
    try:
        bm,dm,open1,open2,read,update,order,sticky,emit=tuple(code)
    except (ValueError,TypeError):
        return False
    # Stored digits are in [1,k]; base B in {k+1,k+2,2k}.
    # Open: S<- B*S+encoded_type; close: compare S%B then S<-S//B.
    return (bm in (1,2,3) and dm in (1,2)
            and (open1,open2)==(0,1) and read==0 and update==0
            and order==0 and sticky==0 and emit==0)

def learned_radix_execute(code,k,word):
    if not universal_radix_proof(code):
        raise ValueError("unproved numeric memory macro")
    if not isinstance(k,int) or isinstance(k,bool) or k<2:raise ValueError("k>=2")
    bm,dm,*_=code
    base=(k,k+1,k+2,2*k)[bm]
    state=0;invalid=False;out=[]
    for phase,typ in word:
        if phase not in (0,1) or not isinstance(typ,int) or isinstance(typ,bool) or not 0<=typ<k:
            raise ValueError("invalid symbol")
        digit=(typ,typ+1,k-typ)[dm]
        if phase==0:
            state=base*state+digit
        else:
            invalid |= state==0 or state%base!=digit
            state//=base
        out.append(int(state==0 and not invalid))
    return tuple(out)

def token_from_code(code):
    payload=json.dumps({"isa":"human-arithmetic-v1",
                       "program":list(code),
                       "contract":"all-k>=2-typed-nesting"},sort_keys=True,separators=(",",":"))
    return "LEARNED_NUMMEM_"+hashlib.sha256(payload.encode()).hexdigest()[:12]

class VerifiedNumericMacro:
    def __init__(self):self.allowed={}
    def register(self,code,source_receipt_hash):
        if not isinstance(source_receipt_hash,str) or len(source_receipt_hash)!=64:
            return {"status":"REJECT_UNSEALED"}
        # This is NOT cryptographic provenance authentication; the separate
        # sealed ZIP supplies weight identity. This gate proves SEMANTICS only.
        if not universal_radix_proof(code):
            return {"status":"UNKNOWN_NO_UNIVERSAL_PROOF"}
        name=token_from_code(code)
        self.allowed[name]=tuple(code)
        return {"status":"SCOPED_CERTIFIED","token":name}
    def run(self,name,k,word):
        if name not in self.allowed:raise ValueError("unverified opcode")
        return learned_radix_execute(self.allowed[name],k,word)
    @staticmethod
    def degraded_fallback(k,word):
        if not isinstance(k,int) or k<2:raise ValueError("k>=2")
        storage=[];bad=False;out=[]
        for phase,t in word:
            if phase not in (0,1) or not isinstance(t,int) or not 0<=t<k:
                raise ValueError("bad stream")
            if phase==0:storage.append(t)
            else:
                if not storage:bad=True
                elif storage.pop()!=t:bad=True
            out.append(int(not storage and not bad))
        return tuple(out)

def info_bits_bounds(k,d):
    if k<2 or d<0:raise ValueError("invalid params")
    return math.ceil(d*math.log2(k)),math.ceil(d*math.log2(k+1))

def reuse_reverse(code,k,types):
    if not universal_radix_proof(code):raise ValueError("not proven")
    bm,dm,*_=code
    base=(k,k+1,k+2,2*k)[bm]
    state=0
    for t in types:
        if not isinstance(t,int) or not 0<=t<k:raise ValueError("bad type")
        state=base*state+(t+1 if dm==1 else k-t)
    out=[]
    while state:
        digit=state%base
        out.append(digit-1 if dm==1 else k-digit)
        state//=base
    return tuple(out)
