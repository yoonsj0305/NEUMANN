"""Q3 exploratory universal-recursive metagrammar inventor.

A single human-coded Python-safe instruction set for integers, sequences,
strings and homoiconic ASTs. No target task names or hand-written domain
operator definitions in the inventor. Source I/O -> executable recursion AST,
then two programs -> NEW typed grammar pattern, then re-instantiate pattern.

This IS program synthesis with a human-given universal recursive core, NOT
a proof of unrestricted general intelligence, trained neural Q3, or a newly
discovered primitive machine instruction. Explicitly retain failure receipts.
"""
from __future__ import annotations
import hashlib
import itertools
import json
import time
from functools import lru_cache

DEFAULT_BUDGET=34000
SAFE_MAX_SEQUENCE=10000

def pack(x):
    return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True)
def digest(x):
    return hashlib.sha256(pack(x).encode()).hexdigest()[:18]
def typeid(v):
    if type(v) is bool:return "bool"
    if type(v) is int:return "int"
    if type(v) is float:return "float"
    if type(v) is list:return "list"
    if type(v) is str:return "str"
    if type(v) is tuple:return "tuple"
    return "unsupported"

def interpret(ast,env):
    tag=ast[0]
    if tag=="v":return env[ast[1]]
    if tag=="c":return ast[1]
    if tag=="unit":return [interpret(ast[1],env)]
    if tag=="len":return len(interpret(ast[1],env))
    if tag=="abs":return abs(interpret(ast[1],env))
    if tag=="int":return int(interpret(ast[1],env))
    if tag=="not":return not interpret(ast[1],env)
    if tag=="head":return interpret(ast[1],env)[0]
    if tag=="tail":return interpret(ast[1],env)[1:]
    if tag=="last":return interpret(ast[1],env)[-1]
    if tag=="if":
        return interpret(ast[2],env) if interpret(ast[1],env) else interpret(ast[3],env)
    left=interpret(ast[1],env)
    right=interpret(ast[2],env)
    if tag=="add":
        if type(left) not in (int,float) or type(right) not in (int,float):
            raise TypeError("add is numeric")
        return left+right
    if tag=="sub":return left-right
    if tag=="mul":return left*right
    if tag=="mod":return left%right
    if tag=="eq":return left==right
    if tag=="lt":return left<right
    if tag=="in":return right in left
    if tag=="cat":
        if type(left) is not type(right) or type(left) not in (list,str,tuple):
            raise TypeError("cat requires same sequence type")
        return left+right
    raise ValueError("unknown base instruction")

def safe_eval(ast,env):
    try:
        v=interpret(ast,env)
        if type(v) not in (int,float,bool,list,str,tuple):return False,None
        if type(v) in (int,float) and abs(v)>100_000_000:return False,None
        if type(v) in (list,str,tuple) and len(v)>SAFE_MAX_SEQUENCE:
            return False,None
        return True,v
    except (TypeError,ValueError,IndexError,ZeroDivisionError,
            OverflowError,RecursionError,KeyError):
        return False,None

def run(program,args):
    try:
        if program[0]=="expr":
            if not args:return None
            ok,v=safe_eval(program[1],{"a":args[0],
                        "b":args[1] if len(args)>1 else None})
            return v if ok else None
        if program[0]!="recur" or len(args)!=1:return None
        _,initial,update,post,emit=program
        source=args[0]
        if type(source) not in (list,tuple,str) or len(source)>100:return None
        state=initial
        emitted=[]
        for index,item in enumerate(source):
            ok,state_new=safe_eval(update,{"s":state,"x":item,"i":index})
            if not ok:return None
            state=state_new
            if emit=="scan":emitted.append(state)
        if emit=="scan":state=emitted
        elif emit!="fold":return None
        ok,final=safe_eval(post,{"s":state})
        return final if ok else None
    except (TypeError,ValueError,KeyError,RecursionError):
        return None

def signature(program,examples):
    output=[]
    for args,goal in examples:
        observed=run(program,args)
        if observed is None:return None
        output.append((typeid(observed),pack(observed)))
    return tuple(output)

@lru_cache(maxsize=1)
def generic_step_expressions():
    atoms=[["v","s"],["v","x"],["c",0],["c",1],["c",2],
           ["c",-1],["c",[]],["c",""]]
    already=set();terms=[]
    def add(node):
        key=pack(node)
        if key not in already:
            already.add(key);terms.append(node)
    for term in atoms:add(term)
    for term in atoms:
        for opcode in ("unit","len","not","abs"):
            add([opcode,term])
    atomlike=terms[:]
    for a in atomlike:
        for b in atomlike:
            for opcode in ("cat","add","sub","mul","mod","eq","lt","in"):
                if opcode in ("eq","add","mul") and pack(a)>pack(b):
                    continue
                add([opcode,a,b])
    small=terms[:]
    for a in atomlike:
        for b in small[:350]:
            for opcode in ("cat","add","sub","mul","eq"):
                add([opcode,a,b])
                if opcode in ("cat","sub"):add([opcode,b,a])
    predicates=[]
    for a in atomlike:
        for b in atomlike:
            for opcode in ("eq","lt","in"):
                predicates.append([opcode,a,b])
    branches=(
        ["v","s"],["v","x"],["c",0],["c",1],
        ["c",[]],["c",""],["unit",["v","x"]],
        ["cat",["v","s"],["unit",["v","x"]]],
        ["cat",["unit",["v","x"]],["v","s"]],
    )
    for condition in predicates[:180]:
        for a in branches:
            for b in branches:
                if a!=b:add(["if",condition,a,b])
    return tuple(sorted(terms,key=lambda ast:(len(pack(ast)),pack(ast))))

def input_constants(examples):
    pool=[0,1,2,-1]
    for args,_ in examples:
        for value in args:
            if type(value) is int and -5<=value<=8 and value not in pool:
                pool.append(value)
    return pool[:10]

def enumerate_solution(examples,budget=DEFAULT_BUDGET,
                       allow_recursive=True):
    start=time.perf_counter_ns();attempts=0
    target=tuple((typeid(y),pack(y)) for _,y in examples)
    arity=len(examples[0][0])
    if not 1<=arity<=2:
        return {"status":"abstain","program":None,"attempts":0}
    atoms=[["v","a"]]+([["v","b"]] if arity==2 else [])
    atoms += [["c",v] for v in input_constants(examples)]
    candidate=atoms[:]
    for a in atoms:
        for op in ("len","int","abs","not","unit"):candidate.append([op,a])
    for a in candidate[:]:
        for b in candidate[:]:
            for op in ("add","sub","mul","mod","cat","eq","lt","in"):
                candidate.append([op,a,b])
    for expression in candidate[:min(budget//2,len(candidate))]:
        attempts+=1
        program=["expr",expression]
        if signature(program,examples)==target:
            return {"status":"new_expression","program":program,
                    "attempts":attempts,
                    "time_ms":round((time.perf_counter_ns()-start)/1e6,3)}
        if attempts>=budget:break
    if allow_recursive and attempts<budget and arity==1:
        output_type=typeid(examples[0][1])
        initial={
            "list":([],0,1,"",False),
            "str":("",[],0,1,False),
            "int":(0,1,[],False,""),
            "bool":(False,0,1,[],""),
            "float":(0,1,[],False,""),
        }.get(output_type,(0,[],1,"",False))
        posts=([["len",["v","s"]],["v","s"]]
               if output_type=="int" else [["v","s"]])
        for update in generic_step_expressions():
            for seed in initial:
                for post in posts:
                    candidate=["recur",seed,update,post,"fold"]
                    attempts+=1
                    if signature(candidate,examples)==target:
                        return {"status":"invented_recursive_operator",
                                "program":candidate,
                                "attempts":attempts,
                                "time_ms":round((time.perf_counter_ns()-start)/1e6,3)}
                    if attempts>=budget:break
                if attempts>=budget:break
            if attempts>=budget:break
    return {"status":"abstain","program":None,"attempts":attempts,
            "time_ms":round((time.perf_counter_ns()-start)/1e6,3)}

def generalize_two_programs(a,b):
    holes=[]
    def unify(left,right):
        if left==right:return left
        if type(left) is list and type(right) is list and len(left)==len(right):
            return [unify(x,y) for x,y in zip(left,right)]
        index=len(holes)
        holes.append((left,right))
        return ["$hole",index]
    if not (a[0]==b[0]=="recur" and a[4]==b[4]):return None
    pattern=unify(a,b)
    if not 1<=len(holes)<=3:return None
    syntax=pack(pattern)
    if sum(syntax.count(k) for k in ('"v"','"recur"','"fold"'))<3:
        return None
    return pattern,holes

def instantiate(node,choices):
    if type(node) is list:
        if len(node)==2 and node[0]=="$hole":
            return choices[node[1]]
        return [instantiate(item,choices) for item in node]
    return node

def expand_learned_rule(rule,train,max_candidates=500):
    small=[0,1,2,-1,False,[],"",()]
    for args,goal in train:
        for arg in args:
            if type(arg) in (int,float,bool,str) and len(str(arg))<10:
                if arg not in small:small.append(arg)
    candidate_values=[]
    for a,b in rule["holes"]:
        if type(a) is str and type(b) is str and a in (
                "add","sub","mul","mod","cat","eq","lt","in"):
            pool=["add","sub","mul","mod","cat","eq","lt","in"]
        elif type(a) in (int,float,list,str,tuple,bool):
            pool=[]
            for v in [a,b]+small:
                if type(v) is type(a) and v not in pool:pool.append(v)
        else:pool=[a,b]
        candidate_values.append(pool[:12])
    for i,choice in enumerate(itertools.product(*candidate_values)):
        if i>=max_candidates:break
        yield instantiate(rule["pattern"],choice)

class InventingLanguage:
    def __init__(self):
        self.definitions=[]
        self.grammar=[]
        self.history=[]

    def solve(self,train,budget=DEFAULT_BUDGET,enable_meta=True):
        target=tuple((typeid(y),pack(y)) for _,y in train)
        for known in self.definitions:
            if signature(known["program"],train)==target:
                return {"status":"reused","program":known["program"],
                        "attempts":1,"source_rule":known["symbol"],
                        "time_ms":0.0}
        if enable_meta:
            trials=0
            for rule in self.grammar:
                for program in expand_learned_rule(rule,train):
                    trials+=1
                    if signature(program,train)==target:
                        return self._register({
                            "status":"learned_meta_grammar",
                            "program":program,"attempts":trials,
                            "source_rule":rule["symbol"],"time_ms":None})
        result=enumerate_solution(train,budget,allow_recursive=True)
        if result["program"] is None:return result
        return self._register(result)

    def _register(self,result):
        program=result["program"]
        symbol="invented_"+digest(program)
        for known in self.definitions:
            new=generalize_two_programs(known["program"],program)
            if new is not None:
                pattern,holes=new
                name="grammar_"+digest(pattern)
                if not any(g["symbol"]==name for g in self.grammar):
                    self.grammar.append({"symbol":name,"pattern":pattern,
                      "holes":holes,"sources":[known["symbol"],symbol]})
        self.definitions.append({"symbol":symbol,"program":program})
        self.history.append({"status":result["status"],"symbol":symbol,
                             "rule":result.get("source_rule")})
        result["symbol"]=symbol
        return result

    def dump(self):
        return {"schema":"neumann.q3.universal-recursive-metasyntax.v1",
                "definitions":self.definitions,
                "grammar":self.grammar,"history":self.history}
