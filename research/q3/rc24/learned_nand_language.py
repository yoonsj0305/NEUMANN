"""Q3 RC24: LIVE learned primitive semantics from own PyTorch NAND-only policy.
This file contains the extracted GREEDY executable codes, NOT training weights.
Original 19 actual .pt tensors, original source-only samples/outputs, and a
separate retrain comparison are in the user-visible full-study SHA zip.
Human supplied NAND as the only primitive, wire-based interpreter, source IO,
Adam/CEM reward and new-language parser, all from preexisting semantics.
"""
import hashlib,json,re

LEARNED_NAND_GRAMMAR = {
  "xor":((1,0),(1,2),(2,0),(0,2),(4,4),(3,4)),
  "and":((0,1),(2,0),(1,3),(2,0),(2,2)),
  "or": ((0,0),(1,1),(3,2)),
}
TASK_SPEC = {"xor":lambda a,b:a^b,"and":lambda a,b:a&b,
             "or":lambda a,b:a|b}

def eval_nand_dag(program,a,b):
    if a not in (0,1) or b not in (0,1):raise ValueError("bit input")
    wires=[a,b]
    for p in program:
        if not isinstance(p,(tuple,list)) or len(p)!=2:
            raise ValueError("syntax")
        i,j=p
        if any(type(k)!=int or not 0<=k<len(wires) for k in (i,j)):
            raise ValueError("unbound wire")
        wires.append(1-(wires[i]&wires[j]))
    if len(wires)==2:raise ValueError("empty definition")
    return wires[-1]

def token(program):
    # Human compiler gives a stable lexical spelling to the model-authored body.
    body=json.dumps({"host":"NAND-only","new_body":program},separators=(",",":"))
    return "AUTO_"+hashlib.sha256(body.encode()).hexdigest()[:12]

def emit_grammar(program):
    return "DEF "+token(program)+"(a,b)\n"+"".join(
       "NAND %d %d\n"%(i,j) for i,j in program)+"END\n"

def parse_grammar(source,gate_budget=6):
    if type(source)!=str or len(source)>1024:raise ValueError("source")
    lines=source.splitlines()
    if len(lines)<3 or lines[-1]!="END":raise ValueError("END required")
    header=re.fullmatch(r"DEF ([a-zA-Z_][a-zA-Z_0-9]*)\(a,b\)",lines[0])
    if not header:raise ValueError("no valid definition")
    instructions=[]
    for line in lines[1:-1]:
        g=re.fullmatch(r"NAND ([0-9]+) ([0-9]+)",line)
        if not g:raise ValueError("unrecognized primitive")
        instructions.append((int(g.group(1)),int(g.group(2))))
        if len(instructions)>gate_budget:raise ValueError("program budget")
        if any(k>=1+len(instructions) for k in instructions[-1]):
            raise ValueError("forward reference")
    if not instructions:raise ValueError("empty instructions")
    return header.group(1),tuple(instructions)

class VerifiedOpcodeRegistry:
    def __init__(self):self.allowed={}
    def register(self,source,expected_behavior):
        if expected_behavior not in TASK_SPEC:
            return {"status":"UNKNOWN_NO_TASK_CONTRACT"}
        try:name,body=parse_grammar(source)
        except ValueError:return {"status":"UNKNOWN_UNTRUSTED_GRAMMAR"}
        if name!=token(body):
            return {"status":"UNKNOWN_UNBOUND_IDENTITY"}
        if any(eval_nand_dag(body,a,b)!=TASK_SPEC[expected_behavior](a,b)
              for a in (0,1) for b in (0,1)):
            return {"status":"UNKNOWN_UNPROVED_SEMANTICS"}
        self.allowed[name]=body
        return {"status":"SCOPED_CERTIFIED","token":name}
    def apply(self,name,a,b):
        if name not in self.allowed:raise ValueError("new instruction unregistered")
        return eval_nand_dag(self.allowed[name],a,b)

def compiled_learned_instructions():
    vm=VerifiedOpcodeRegistry();names={}
    for task,body in LEARNED_NAND_GRAMMAR.items():
        rec=vm.register(emit_grammar(body),task)
        if rec["status"]!="SCOPED_CERTIFIED":raise AssertionError(rec)
        names[task]=rec["token"]
    return vm,names

def add_assembled_by_researcher(vm,names,a,b,n):
    if any(type(x)!=int or x<0 for x in (a,b,n)) or n<1 or a>=1<<n or b>=1<<n:
        raise ValueError("unsigned width/operand")
    carry=0;ans=0
    for i in range(n):
        x=(a>>i)&1;y=(b>>i)&1
        ab=vm.apply(names["xor"],x,y)
        bit=vm.apply(names["xor"],ab,carry)
        carry=vm.apply(names["or"],vm.apply(names["and"],x,y),
                                         vm.apply(names["and"],ab,carry))
        ans|=bit<<i
    return ans|(carry<<n)

def scoped_science_gate():
    return {"new_own_weight_boolean_gate_semantics":"SCOPED_PASS",
            "all_16_boolean_binary_semantics":"SCOPED_PASS",
            "single_preexisting_base_primitive":"NAND",
            "base_meta_grammar_and_new_token_naming":"HUMAN",
            "arith_composition":"HUMAN",
            "complete_self_invented_metalanguage":"OPEN",
            "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
            "global_Q6":"OPEN","global_Q7":"OPEN"}
