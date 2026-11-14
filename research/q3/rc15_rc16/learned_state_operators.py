"""RC15/RC16 frozen extracted OWN-trained finite-state operators.

Full real PyTorch source-training/weights SHA in separate reproducible research ZIP.
Human supplied finite-state DSL; these are NOT self-invented new ISA instructions.
"""
PARITY_CODE=(1,1,0,1,2,0) # allocated, XOR(register,digit), NONZERO, keep
SEEN_ONE_CODE=(1,2,1,0,2,1) # allocated, OR(digit,register), NONZERO, divide1
MOD3_TRANSITION=(0,1,1,2,2,0)
MOD3_EMIT=(1,0,0,0,0,1)

def prefix_parity(bits):
    register=0;out=[]
    for digit in bits:
        if digit not in (0,1):raise ValueError("binary")
        register ^= digit
        out.append(int(register!=0))
    return tuple(out)

def prefix_seen_one(bits):
    register=0;out=[]
    for digit in bits:
        if digit not in (0,1):raise ValueError("binary")
        register |= digit
        out.append(int(register!=0))
    return tuple(out)

def prefix_multiple_of_three(bits):
    state=0;out=[]
    for digit in bits:
        if digit not in (0,1):raise ValueError("binary")
        idx=2*state+digit
        out.append(MOD3_EMIT[idx])
        state=MOD3_TRANSITION[idx]
    return tuple(out)

def machine_bisimulation(nxt,emit):
    # Independent product-state comparison to the human-specified MOD3 goal.
    if len(nxt)!=len(emit) or len(emit)%2: return False
    m=len(emit)//2
    if not all(isinstance(s,int) and 0<=s<m for s in nxt):return False
    if not all(x in (0,1) for x in emit):return False
    q=[(0,0)];seen={(0,0)}
    for state,residue in q:
        for bit in (0,1):
            idx=2*state+bit
            rr=(residue+bit)%3
            if emit[idx]!=int(rr==0):return False
            new=(nxt[idx],rr)
            if new not in seen:seen.add(new);q.append(new)
    return True

class ProofGatedStateRegistry:
    def __init__(self):self.operators={}
    def register(self,name,next_states,outputs,source_sha):
        if not name.startswith("LEARNED_") or not source_sha or name in self.operators:
            return "REJECT_PROVENANCE"
        if not machine_bisimulation(next_states,outputs):
            return "UNKNOWN_UNPROVED"
        self.operators[name]=(tuple(next_states),tuple(outputs))
        return "SCOPED_CERTIFIED"
    def run(self,name,bits):
        if name not in self.operators:
            raise ValueError("unknown / unverified")
        nxt,emit=self.operators[name];s=0;out=[]
        for x in bits:
            if x not in (0,1):raise ValueError("binary")
            k=2*s+x;out.append(emit[k]);s=nxt[k]
        return tuple(out)
    @staticmethod
    def fallback(bits):
        residue=0;out=[]
        for digit in bits:
            if digit not in (0,1):raise ValueError("binary")
            residue=(residue+digit)%3
            out.append(int(residue==0))
        return tuple(out)
