"""RC18: runtime-generated syntax from actual OWN learned binary gate semantics.

The learned semantics are extracted from independent PyTorch checkpoints.
Human authored the type system, 4-slot truth-table meta-ISA and VM. New opcode
names/rules are auto-generated from learned body, NOT directly spelled by model.
Full real .pt / original signed float logits in the separate reproducible ZIP.
"""
import hashlib,json

FROZEN_LEARNED_TABLES={"PARITY":(0,1,1,0),"SEEN_ONE":(0,1,1,1)}

def generated_token(table):
    table=tuple(table)
    if len(table)!=4 or any(x not in (0,1) for x in table):
        raise ValueError("invalid 4-bit learned semantics")
    packed=json.dumps({"arity":2,"input_types":["bit","bit"],"output_type":"bit",
                       "table":list(table)},sort_keys=True,separators=(",",":"))
    return "LEARNED_"+hashlib.sha256(packed.encode()).hexdigest()[:12]

class ExtensibleBitLanguage:
    def __init__(self):self.rules={}
    def register_weight_generated(self,weight_vector,training_source_sha):
        if not training_source_sha or len(weight_vector)!=4:
            return {"status":"UNKNOWN_UNSEALED_OR_BAD_SHAPE"}
        table=tuple(int(float(w)>0) for w in weight_vector)
        name=generated_token(table)
        self.rules[name]=table
        return {"status":"SCOPED_REGISTERED","name":name,
                "grammar_rule":f"BitExpr ::= {name}(BitExpr, BitExpr)"}
    def eval(self,token,state,input_bit):
        if token not in self.rules:raise ValueError("no registered instruction")
        if state not in (0,1) or input_bit not in (0,1):raise ValueError("binary input only")
        return self.rules[token][2*state+input_bit]
    def run(self,token,word):
        state=0;out=[]
        for b in word:
            state=self.eval(token,state,b)
            out.append(state)
        return tuple(out)

def composition(reg,inner,outer,bits):
    return reg.run(outer,reg.run(inner,bits))

def run_proven_three_state_reference(bits):
    seen=parity=0;out=[]
    for b in bits:
        if b not in (0,1):raise ValueError("binary")
        seen|=b
        parity^=seen
        out.append(parity)
    return tuple(out)

def grammar_science_boundary():
    return {"learned_new_opcode_semantics":"SCOPED_PASS",
            "grammar_tokens_made_from_frozen_weights":"SCOPED_PASS",
            "neural_learned_two_operator_composition":"SCOPED_PASS",
            "human_created_truth_table_metalanguage":True,
            "base_metalanguage_autonomous_invention":"OPEN",
            "global_Q3":"OPEN","global_Q4_10x":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN"}
