"""RC14: compact compiled macro; full real torch weights+proof receipts in ZIP.
Human supplied primitive ISA and proof rule. No autonomous new language.
"""
from dataclasses import dataclass
MODEL_SELECTED_CODE=(1,0,1,0,0,2) # frozen own-weight best *sampled*, not greedy
MODEL_SELECTED_SEED=2026102506

def interpret(code,digits):
    allocate,op,left,right,emit,upd=code
    c=0;result=[]
    for d in digits:
        if not isinstance(d,int) or isinstance(d,bool) or d<0:
            raise ValueError("nonnegative integer digit required")
        values=(c if allocate else 0,d,0,1)
        a,b=values[left],values[right]
        val=(a+b,a^b,a|b,max(a,b),a-b,a*b)[op]
        bit=(val&1,(val>>1)&1,int(val!=0),1-(val&1))[emit]
        if allocate:
            c=(val,val,val//2,val//3,val//4,val%2,0,max(val,0))[upd]
        result.append(bit)
    return result,c

def exact_digit_normalization_proof_rule(code):
    allocated,op,left,right,emit,upd=code
    return allocated==1 and op==0 and {left,right}=={0,1} and emit==0 and upd==2

@dataclass(frozen=True)
class Receipt:
    status:str
    name:str
    code:tuple

class MacroRegistry:
    def __init__(self):self.definitions={}
    def add_from_model(self,name,learned_code,frozen_receipt_sha):
        code=tuple(learned_code)
        if not frozen_receipt_sha or not name.startswith("AUTO_"):
            return Receipt("REJECT_UNSEALED",name,code)
        if name in self.definitions:
            return Receipt("REJECT_COLLISION",name,code)
        if not exact_digit_normalization_proof_rule(code):
            return Receipt("UNKNOWN_NO_ALL_LENGTH_PROOF",name,code)
        self.definitions[name]=code
        return Receipt("SCOPED_CERTIFIED",name,code)
    def invoke(self,name,digits):
        if name not in self.definitions:raise ValueError("unverified or unregistered macro")
        return interpret(self.definitions[name],digits)
    @staticmethod
    def reference_fallback(digits):
        ds=tuple(digits)
        if any(not isinstance(x,int) or isinstance(x,bool) or x<0 for x in ds):
            raise ValueError("invalid digit")
        z=sum(x<<i for i,x in enumerate(ds))
        return [(z>>i)&1 for i in range(len(ds))],z>>len(ds)
