"""RC29: minimal executable OWN learned semantic instruction.
Real 12 PyTorch checkpoints and 2 failed conditional GRU controls reside in
the 38-file reproducible ZIP. It is invalid to call this a self-invented parser
or pure-from-nothing machine language: human supplied truth-table shape,
per-position sharing, AND fold, and this proof gate.
"""
from hashlib import sha256
import json,re

LEARNED_4BIT_SEMANTICS=(1,0,0,1)  # 00,01,10,11; source-only own PyTorch sign

def name(table):
    content=json.dumps({"arity":2,"kind":"BITOP","table":list(table)},sort_keys=True,separators=(",",":"))
    return "OWN_"+sha256(content.encode()).hexdigest()[:12]

def source_from_learned_weights(table=LEARNED_4BIT_SEMANTICS):
    if len(table)!=4 or any(v not in (0,1) for v in table):raise ValueError("invalid weights")
    return "DEF "+name(table)+"(bit,bit)\nTABLE "+''.join(map(str,table))+"\nEND\n"

class ProofGatedGrammar:
    def __init__(self):self.ops={}
    def register(self,source):
        if type(source)!=str or len(source)>256:return {"status":"UNKNOWN_SOURCE"}
        lines=source.splitlines()
        if len(lines)!=3:return {"status":"UNKNOWN_SYNTAX"}
        a=re.fullmatch(r"DEF (OWN_[a-f0-9]{12})\(bit,bit\)",lines[0])
        b=re.fullmatch(r"TABLE ([01]{4})",lines[1])
        if not (a and b and lines[2]=="END"):return {"status":"UNKNOWN_SYNTAX"}
        table=tuple(map(int,b.group(1)))
        if a.group(1)!=name(table):return {"status":"UNKNOWN_IDENTITY"}
        if any(table[2*x+y]!=int(x==y) for x in (0,1) for y in (0,1)):
            return {"status":"UNKNOWN_SEMANTIC_PROOF"}
        self.ops[a.group(1)]=table
        return {"status":"SCOPED_CERTIFIED","opcode":a.group(1)}
    def apply(self,op,x,y):
        if op not in self.ops:raise ValueError("unregistered instruction")
        if x not in (0,1) or y not in (0,1):raise ValueError("binary only")
        return self.ops[op][2*x+y]
    def compare(self,op,word,pattern):
        if len(word)!=len(pattern):return False
        return all(self.apply(op,a,b)==1 for a,b in zip(word,pattern))
    def suffix_stream(self,op,word,pattern):
        if not pattern:raise ValueError("pattern cannot be empty")
        return tuple(0 if i<len(pattern)-1 else
                     int(self.compare(op,word[i-len(pattern)+1:i+1],pattern))
                     for i in range(len(word)))

SCOPED_ADMISSION={
 "own_weight_bit_opcode":"SCOPED_PASS",
 "unseen_pattern_generalization":"SCOPED_PASS",
 "variable_length_correctness_given_human_fold":"PROVED",
 "unstructured_meta_gru_unseen_patterns":"FAIL",
 "classical_same_information_cheaper":"YES",
 "model_self_invented_host_meta_grammar":"OPEN",
 "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN"
}
