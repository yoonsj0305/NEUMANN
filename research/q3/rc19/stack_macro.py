"""RC19 compact extracted from OWN PyTorch learned six-parameter policy.
Human-supplied semantic VM / storage-type grammar, model chose among 128 options.
No new foundation-level stack or metalanguage invented by model.
Full original checkpoint and first-pred sealed evidence in separate ZIP.
"""
from hashlib import sha256
from json import dumps
from math import ceil,log2
LEARNED_PROGRAM=(0,0,0,0,0,0)

def learned_stack_stream(stream):
    """Return one bit after each prefix: valid AND completely closed."""
    stack=[];bad=False;out=[]
    for phase,kind in stream:
        if phase not in (0,1) or not isinstance(kind,int) or kind<0:
            raise ValueError('expected typed binary-phase symbols')
        if phase==0:stack.append(kind)
        elif not stack or stack.pop()!=kind:bad=True
        out.append(int(not bad and not stack))
    return tuple(out)

def grammar_token_from_program(program):
    program=tuple(program)
    if len(program)!=6 or any(not isinstance(x,int) for x in program):
        raise ValueError('bad program shape')
    text=dumps({'macro_kind':'DYNAMIC_NESTED_TYPED_STREAM',
      'memory_store':program[1],'open_polarity':program[0],
      'comparison':program[2],'sticky_error':program[3],
      'emit_when_empty':program[4],'type_storage':program[5],
      'vm_schema':'human-authored-v1'},sort_keys=True,separators=(',',':'))
    return 'LEARNED_DMEM_'+sha256(text.encode()).hexdigest()[:12]

def proof_gate(program):
    """Induction valid ONLY for exact six low-level rule classes."""
    return tuple(program)==LEARNED_PROGRAM

class ProofGatedGrammar:
    def __init__(self):self.operators={}
    def register(self,code,source_sha):
        if not isinstance(source_sha,str) or len(source_sha)<32:
            return 'REJECT_UNSEALED'
        if not proof_gate(code):return 'UNKNOWN_UNPROVED'
        token=grammar_token_from_program(code)
        self.operators[token]=tuple(code)
        return token
    def run(self,name,stream):
        if name not in self.operators:raise ValueError('unverified new language token')
        return learned_stack_stream(stream)
    @staticmethod
    def fallback(stream):
        stack=[];bad=False;out=[]
        for phase,kind in stream:
            if phase not in (0,1) or not isinstance(kind,int) or kind<0:raise ValueError('bad token')
            if phase==0:stack.append(kind)
            else:
                if len(stack)==0:bad=True
                elif stack[-1]!=kind:bad=True
                else:stack.pop()
            out.append(int(not bad and len(stack)==0))
        return tuple(out)

def necessary_information_bits(depth,type_count):
    if depth<1 or type_count<2:raise ValueError('depth>=1,k>=2')
    return ceil(depth*log2(type_count))
