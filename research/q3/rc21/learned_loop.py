"""RC21: extracted compact proof-gated neural-generated loop opcode.
The raw policy logits are in the standalone research archive, not this file.
Human gave WHILE, ADD, SUB, CMP and five slot types; no DIV/REM builtin in VM.
"""
import json,hashlib

OWN_WEIGHT_SELECTED_CODE=(0,0,0,0,0)
PROVED_PROGRAM=(0,0,0,0,0)

def proof_gate(code):
    # A sound sufficient rule: loop maintains x=q*b+r, r>=0;
    # each step subtracts b and increases q by one; halts with r<b.
    return tuple(code)==PROVED_PROGRAM

def name_for_compiled(code):
    payload={"v":1,"primitive_vm":"register-add-sub-compare-loop",
             "selected_program":tuple(code),"type":"uint-divrem"}
    return "LEARNED_LOOP_"+hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:12]

class SafeLearnedLoopLanguage:
    def __init__(self):self.registry={}
    def register(self,code,source_receipt_sha):
        if not isinstance(source_receipt_sha,str) or len(source_receipt_sha)!=64:
            return {"status":"REJECT_UNSEALED"}
        if not proof_gate(code):return {"status":"UNKNOWN_UNPROVED"}
        name=name_for_compiled(code)
        self.registry[name]=tuple(code)
        return {"status":"SCOPED_CERTIFIED","token":name}

    def execute(self,name,x,b,step_cap=100000):
        if name not in self.registry:raise ValueError("unverified opcode")
        if any(not isinstance(v,int) or isinstance(v,bool) for v in (x,b)) or x<0 or b<2:
            raise ValueError("unsigned x, integer base>=2")
        q=0;r=x
        for _ in range(step_cap):
            if not r>=b:return {"status":"EXACT","q":q,"r":r}
            r-=b;q+=1
        return {"status":"UNKNOWN_STEP_CAP"}

    @staticmethod
    def fallback(x,b):
        if any(not isinstance(v,int) or isinstance(v,bool) for v in (x,b)) or x<0 or b<2:
            raise ValueError("invalid")
        return {"status":"EXACT","q":x//b,"r":x%b}

    def carry_normalize(self,name,digits):
        carry=0;output=0;length=0
        for d in digits:
            if not isinstance(d,int) or isinstance(d,bool) or d<0:raise ValueError("invalid digit")
            receipt=self.execute(name,carry+d,2)
            if receipt["status"]!="EXACT":return {"status":"UNKNOWN_COST_CAP"}
            output|=receipt['r']<<length
            carry=receipt['q'];length+=1
        return {"status":"EXACT","low_bits":output,"carry":carry,"length":length}
