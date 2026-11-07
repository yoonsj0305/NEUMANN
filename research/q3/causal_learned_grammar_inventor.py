"""Q3: discover a NEW executable grammar production from independently
certified source operator ASTs; source-frozen transfer to new author corpus.

Base VM has item, literal, eq, mod, lt, not and generic fold.
It does NOT predefine modulo-equality as an atomic predicate or a registered
operator constructor. A domain-level grammar production is anti-unified from
TWO actually independently heldout-verified programs in #714.

The grammar extends a search policy, not the Turing computability of the base.
Human coded: VM, old source lowering, AST antiunification, candidate matcher,
cold base-grammar enumeration. Source-specific correct ASTs NOT hardcoded.
"""
from __future__ import annotations
from collections import Counter
from hashlib import sha256
import json
import time

SCHEMA="neumann.q3.causally_learned_meta_grammar.v1"

def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True)
def digest(x):
    return sha256(canonical(x).encode()).hexdigest()

def is_seq(v):
    return type(v) in (list,tuple,str)

def pred_eval(expr,item):
    tag=expr[0]
    if tag=="item":
        return item
    if tag=="lit":
        return expr[1]
    if tag=="eq":
        return pred_eval(expr[1],item)==pred_eval(expr[2],item)
    if tag=="lt":
        x=pred_eval(expr[1],item);y=pred_eval(expr[2],item)
        if type(x) not in (int,float) or type(y) not in (int,float):
            raise ValueError("TYPE")
        return x<y
    if tag=="mod":
        x=pred_eval(expr[1],item);y=pred_eval(expr[2],item)
        if type(x) is not int or type(y) is not int or y==0:
            raise ValueError("NONINTEGER_MODULO")
        return x%y
    if tag=="not":
        return not pred_eval(expr[1],item)
    if tag=="character":
        if type(item) is not str or len(item)!=1:
            raise ValueError("NONCHARACTER")
        property=expr[1]
        if property=="space":return item.isspace()
        if property=="digit":return item.isdigit()
        if property=="alpha":return item.isalpha()
        raise ValueError("UNSUPPORTED_CHARACTER_PROPERTY")
    raise ValueError("UNKNOWN_INSTRUCTION")

def run_operator(program,args):
    try:
        if program is None or len(args)!=1:return None
        if program[0]!="fold" or program[1]!="keep_if_false":
            return None
        seq=args[0]
        if not is_seq(seq) or len(seq)>1024:return None
        pred=program[2]
        out=type(seq)()
        for item in seq:
            if not pred_eval(pred,item):
                if type(seq) is str:out+=item
                elif type(seq) is tuple:out+=(item,)
                else:out+=[item]
        return out
    except (ValueError,TypeError,KeyError,IndexError,OverflowError):
        return None

def decompose_examples(examples):
    """Output must be an ordered subsequence, tokens uniformly kept/dropped.
    Rejects non-causal changes, unhashable tokens and conflicting observations.
    """
    roles={}
    if len(examples)<2:return None
    for args,goal in examples:
        if len(args)!=1:return None
        seq=args[0]
        if not is_seq(seq) or type(seq) is not type(goal):return None
        if len(seq)>1024 or len(goal)>1024:return None
        try:
            it=iter(seq)
            if not all(any(v==want for v in it) for want in goal):
                return None
            left=Counter(seq);right=Counter(goal)
            if any(n>left[val] for val,n in right.items()):return None
            for symbol,n in left.items():
                if type(symbol) not in (str,int,float,bool):return None
                if right[symbol]==n:label=False
                elif right[symbol]==0:label=True
                else:return None
                if symbol in roles and roles[symbol]!=label:return None
                roles[symbol]=label
        except (TypeError,ValueError):
            return None
    if not any(roles.values()) or not any(not x for x in roles.values()):
        return None
    return roles

def source_lowering(program):
    """Explicit HUMAN-CODED adapter for old Q3 #714 operator syntax.
    It does not provide parameter values or invented source programs.
    """
    if program.get("kind")!="DefineGeneratedOperator":
        raise ValueError("NOT_CERTIFIED_Q3_INVENTED")
    ast=program.get("ast")
    pred=program.get("predicate")
    if not (isinstance(ast,list) and ast[0]=="fold" and
            ast[3][0]=="if" and isinstance(pred,list)):
        raise ValueError("BAD_SOURCE_PROGRAM")
    if pred[0]=="mod_equals":
        return ["fold","keep_if_false",
                ["eq",["mod",["item"],["lit",pred[1]]],["lit",pred[2]]]]
    if pred[0]=="unicode_class" and pred[1] in ("space","digit","alpha"):
        return ["fold","keep_if_false",["character",pred[1]]]
    if pred[0]=="eq":
        return ["fold","keep_if_false",["eq",["item"],["lit",pred[1]]]]
    raise ValueError("NOT_LOWERABLE_WITHOUT_HUMAN_ADDED_OPERATION")

def antiunify(left,right,holes):
    if left==right:return left
    if type(left) is list and type(right) is list and len(left)==len(right):
        if left and right and left[0]==right[0] and left[0]!="lit":
            return [antiunify(x,y,holes) for x,y in zip(left,right)]
    key=(canonical(left),canonical(right))
    if key not in holes:holes[key]=len(holes)
    return ["hole",holes[key]]

def substitute(program,arguments):
    if type(program) is list:
        if len(program)==2 and program[0]=="hole":
            return arguments[program[1]]
        return [substitute(x,arguments) for x in program]
    return program

def learn_production(source_programs):
    if len(source_programs)<2:raise ValueError("NEED_MULTIPLE_VERIFIED_SOURCES")
    for item in source_programs:
        if not item["original_heldout_exact"]:
            raise ValueError("SOURCE_NOT_INDEPENDENTLY_VERIFIED")
    programs=[source_lowering(s["program"]) for s in source_programs]
    holes={}
    grammar=antiunify(programs[0],programs[1],holes)
    def structural_ops(x):
        if not isinstance(x,list):return []
        found=[x[0]] if x and x[0] in ("eq","mod","lt","not","character") else []
        for v in x[1:]:
            found+=structural_ops(v)
        return found
    if (len(holes)!=1 or not isinstance(grammar,list) or
        grammar[:2]!=["fold","keep_if_false"] or
        grammar[2]==["hole",0] or
        len(structural_ops(grammar[2]))<2):
        # General scientific novelty gate: the entire predicate cannot
        # be a single blank hole. At least TWO compositional operators
        # must remain from the paired learned programs. No named target
        # predicate class or k=2 code in the grammar-induction rule.
        raise ValueError("NO_USEFUL_SOURCE_ABSTRACTION")
    learned={
        "type":"DefineNewGrammarProduction",
        "name":"invented_grammar_"+digest(grammar)[:16],
        "source_operator_programs":[x["task_id"] for x in source_programs],
        "pattern_ast":grammar,
        "variable_parameters":1,
        "prior_binding_literals":[program[2][2] for program in programs],
        "human_compiler_adapter":True,
        "base_vm_modified":False,
        "causal_expected_gain":"candidate ordering only, at fixed budget",
    }
    return learned

def matches(pred,roles):
    try:return all(bool(pred_eval(pred,v))==expected
                   for v,expected in roles.items())
    except (ValueError,TypeError):return False

def base_expression_candidates(roles):
    # Generic, type-correct primitive compositions; NO named mod_equals.
    items=sorted(roles,key=lambda x:repr(x))
    numeric=all(type(v) is int for v in items)
    if numeric:
        for a in items:
            yield ["eq",["item"],["lit",a]]
        for a in items:
            yield ["lt",["item"],["lit",a]]
        # Unrestricted base composition under a finite grammar/budget.
        for divisor in range(2,11):
            for residue in range(divisor):
                yield ["eq",["mod",["item"],["lit",divisor]],
                       ["lit",residue]]
    elif all(type(v) is str and len(v)==1 for v in items):
        for a in items:
            yield ["eq",["item"],["lit",a]]
        for prop in ("space","digit","alpha"):
            yield ["character",prop]
    else:
        for a in items:
            yield ["eq",["item"],["lit",a]]

def learned_production_candidates(grammar,roles):
    # Choose hole values from SOURCE-derived rule, then observed target
    # roles. Search program grammar is generated from verified program AST.
    if grammar is None:return
    p=grammar["pattern_ast"]
    values=list(grammar["prior_binding_literals"])
    for x in (0,1,2,3):
        pair=["lit",x]
        if pair not in values:values.append(pair)
    for val in values:
        if type(val) is list and val[0]=="lit":
            yield substitute(p,[val])

def solve(train,rule=None,budget=16):
    t0=time.perf_counter_ns()
    roles=decompose_examples(train)
    if roles is None:return {"program":None,"status":"ABSTAIN_PRECONDITION",
                              "attempts":0,"wall_ms":0.0}
    seen=set();checked=0
    def choose(expressions,origin):
        nonlocal checked
        for prog in expressions:
            if checked>=budget:return None
            key=canonical(prog)
            if key in seen:continue
            seen.add(key);checked+=1
            pred=prog[2] if prog[0]=="fold" else prog
            if matches(pred,roles):
                compiled=prog if prog[0]=="fold" else [
                    "fold","keep_if_false",prog]
                if all(run_operator(compiled,args)==goal for args,goal in train):
                    return {"program":compiled,"status":origin,
                            "attempts":checked,"wall_ms":round(
                                (time.perf_counter_ns()-t0)/1e6,5)}
        return None
    if rule is not None:
        result=choose(learned_production_candidates(rule,roles),
                      "INVENTED_GRAMMAR_PRODUCTION")
        if result:return result
    result=choose(base_expression_candidates(roles),"COLD_BASE_COMPOSITION")
    if result:return result
    return {"program":None,"status":"ABSTAIN_BUDGET",
            "attempts":checked,
            "wall_ms":round((time.perf_counter_ns()-t0)/1e6,5)}

def scorable(program,args,target):
    if program is None:return False
    out=run_operator(program,args)
    return type(out) is type(target) and out==target
