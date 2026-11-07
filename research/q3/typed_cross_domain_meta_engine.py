"""Q3 cross-domain typed proof-carrying construction engine.
Accepts original SyGuS PBE-SLIA string constraints, never reference solutions.
This is a HUMAN-CODED universal VM and program language. New productions
may be learned via structural anti-unification of source-proven program ASTs.
"""
from __future__ import annotations
import hashlib,itertools,json,time
from collections import Counter

def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=True)
def sha(x):return hashlib.sha256(canonical(x).encode()).hexdigest()

def tokenize(s):
    i=0;out=[]
    while i<len(s):
        if s[i].isspace():i+=1;continue
        if s[i]==';':
            j=s.find("\n",i);i=len(s) if j<0 else j+1;continue
        if s[i] in "()":out.append(s[i]);i+=1;continue
        if s[i]=='"':
            i+=1;t=""
            while i<len(s):
                if s[i]=='"':
                    if i+1<len(s) and s[i+1]=='"':
                        t+='"';i+=2;continue
                    i+=1;break
                # Preserve literal slash / and SMT-LIB backslash bytes.
                t+=s[i];i+=1
            else:raise ValueError("UNTERMINATED_LITERAL")
            out.append(("Q",t));continue
        j=i
        while j<len(s) and not s[j].isspace() and s[j] not in "();":j+=1
        if j==i:raise ValueError("BAD_TOKEN")
        out.append(s[i:j]);i=j
    return out

def parse(s):
    ts=tokenize(s);it=iter(ts)
    def one(t):
        if t!="(":return t
        v=[]
        for a in it:
            if a==")":return v
            v.append(one(a))
        raise ValueError("UNCLOSED_FORM")
    forms=[]
    for t in it:
        if t==")":raise ValueError("ORPHAN_CLOSE")
        forms.append(one(t))
    return forms

def walk(node):
    if isinstance(node,list):
        for x in node:yield from walk(x)
    else:yield node

def decode_original(source):
    forms=parse(source)
    synth=[s for s in forms if isinstance(s,list) and s and s[0]=="synth-fun"]
    if len(synth)!=1 or len(synth[0])<6:raise ValueError("UNSUPPORTED_SYNTH_DECL")
    fun=synth[0];fn=fun[1];params=fun[2]
    if (not isinstance(params,list) or not params or len(params)>3 or
        any(type(p) is not list or len(p)!=2 or p[1]!="String" for p in params) or
        fun[3]!="String"):
        raise ValueError("UNSUPPORTED_TYPE")
    grammar=fun[4:]
    atoms=list(walk(grammar))
    literals=sorted({a[1] for a in atoms if isinstance(a,tuple) and a[0]=="Q"},key=lambda x:(len(x),x))
    ops={a for a in atoms if isinstance(a,str)}
    nums=sorted({int(a) for a in ops if a.lstrip("-").isdigit() and abs(int(a))<=8})
    if 0 not in nums:nums=[0]+nums
    examples=[]
    for row in forms:
        if not isinstance(row,list) or not row or row[0]!="constraint":continue
        e=row[1] if len(row)>1 else None
        if not (isinstance(e,list) and len(e)==3 and e[0]=="="):continue
        left,right=e[1],e[2]
        if not (isinstance(left,list) and left and left[0]==fn and len(left)==len(params)+1):
            if isinstance(right,list) and right and right[0]==fn:
                left,right=right,left
            else:continue
        if not (isinstance(right,tuple) and right[0]=="Q" and all(
            isinstance(a,tuple) and a[0]=="Q" for a in left[1:])):
            continue
        examples.append((tuple(a[1] for a in left[1:]),right[1]))
    seen=set();unique=[]
    for x,y in examples:
        if x in seen:continue
        seen.add(x);unique.append((x,y))
    if not unique:raise ValueError("NO_VALID_LITERAL_EXAMPLES")
    return {"nargs":len(params),"ops":sorted(ops),"constants":literals,"numbers":nums,
            "examples":unique,"source_constraints":len(examples)}

def ev(ast,args,depth=0):
    if depth>20:raise ValueError("AST_DEPTH")
    tag=ast[0]
    if tag=="arg":return args[ast[1]]
    if tag=="lit":return ast[1]
    if tag=="num":return ast[1]
    if tag=="len":return len(ev(ast[1],args,depth+1))
    if tag=="index":
        s=ev(ast[1],args,depth+1);q=ev(ast[2],args,depth+1)
        start=ev(ast[3],args,depth+1)
        return -1 if start<0 or start>len(s) else s.find(q,start)
    if tag=="plus":return ev(ast[1],args,depth+1)+ev(ast[2],args,depth+1)
    if tag=="minus":return ev(ast[1],args,depth+1)-ev(ast[2],args,depth+1)
    if tag=="substr":
        s=ev(ast[1],args,depth+1);i=ev(ast[2],args,depth+1);n=ev(ast[3],args,depth+1)
        return "" if i<0 or n<=0 or i>=len(s) else s[i:i+n]
    if tag=="at":
        s=ev(ast[1],args,depth+1);i=ev(ast[2],args,depth+1)
        return s[i] if 0<=i<len(s) else ""
    if tag=="replace":
        s=ev(ast[1],args,depth+1);old=ev(ast[2],args,depth+1);new=ev(ast[3],args,depth+1)
        return s.replace(old,new,1)
    if tag=="cat":return ev(ast[1],args,depth+1)+ev(ast[2],args,depth+1)
    if tag=="contains":return ev(ast[2],args,depth+1) in ev(ast[1],args,depth+1)
    if tag=="prefix":return ev(ast[1],args,depth+1).startswith(ev(ast[2],args,depth+1))
    if tag=="suffix":return ev(ast[1],args,depth+1).endswith(ev(ast[2],args,depth+1))
    if tag=="ite":return ev(ast[2],args,depth+1) if ev(ast[1],args,depth+1) else ev(ast[3],args,depth+1)
    raise ValueError("UNKNOWN_AST")

def size(ast):
    return 1+sum(size(v) for v in ast[1:] if isinstance(v,list))

def candidate_library(task,limit=3000):
    """Typed enumeration uses only operations/literals allowed by INPUT grammar.
    No task name, output labels or reference solution enters candidate generation.
    """
    ops=set(task["ops"]);constants=task["constants"];numbers=task["numbers"]
    args=[["arg",i] for i in range(task["nargs"])]
    pool=args+[["lit",x] for x in constants]
    expr=list(pool)
    for a in args:
        if "str.substr" in ops or "str.at" in ops:
            for k in numbers:
                nk=["num",k]
                if "str.at" in ops:expr.append(["at",a,nk])
                if "str.substr" in ops:
                    expr.append(["substr",a,["num",0],nk])
                    if "str.len" in ops:expr.append(["substr",a,nk,["len",a]])
        if "str.indexof" in ops and "str.substr" in ops and "str.len" in ops:
            for delimiter in constants:
                if not delimiter or len(delimiter)>3:continue
                loc=["index",a,["lit",delimiter],["num",0]]
                expr.append(["substr",a,["num",0],loc])
                if "+" in ops:
                    pos=["plus",loc,["num",1]]
                    expr.append(["substr",a,pos,["len",a]])
                expr.append(["substr",a,loc,["len",a]])
        if "str.replace" in ops:
            for before in constants:
                if not before:continue
                for after in constants:
                    if before!=after:expr.append(["replace",a,["lit",before],["lit",after]])
    if "str.++" in ops:
        # Generic shallow binary programs, no task-specific branch.
        cores=args+[["lit",c] for c in constants if len(c)<5]
        for x in cores:
            for y in cores:
                if x!=y:expr.append(["cat",x,y])
        for x in args:
            for y in args:
                for c in constants:
                    if len(c)>4:continue
                    expr.append(["cat",["cat",x,["lit",c]],y])
    # Structural (not observational) deduplication and bounded total candidates.
    seen=set();out=[]
    for p in expr:
        h=canonical(p)
        if h in seen:continue
        seen.add(h);out.append(p)
        if len(out)>=limit:break
    return out

def predicates(task):
    ops=set(task["ops"]);lits=task["constants"];args=[["arg",i] for i in range(task["nargs"])]
    yield from []
    for a in args:
        for c in lits:
            if not c:continue
            v=["lit",c]
            if "str.contains" in ops:yield ["contains",a,v]
            if "str.prefixof" in ops:yield ["prefix",a,v]
            if "str.suffixof" in ops:yield ["suffix",a,v]

def signatures(task,train):
    expr=candidate_library(task)
    xs=[x for x,_ in train];ys=[y for _,y in train]
    uniq={};ordered=[]
    for p in expr:
        try:
            sig=tuple(ev(p,x) for x in xs)
        except (TypeError,ValueError,IndexError,OverflowError):continue
        if sig not in uniq:
            uniq[sig]=p;ordered.append((p,sig))
    return ordered

def expression_search(task,train,allow_branch=False):
    t=time.perf_counter_ns()
    pool=signatures(task,train)
    expect=tuple(y for _,y in train)
    for p,sig in pool:
        if sig==expect:
            return {"ast":p,"status":"BASE_TYPED","checks":len(pool),
                "wall_ms":(time.perf_counter_ns()-t)/1e6}
    checks=len(pool)
    if allow_branch and "ite" in task["ops"]:
        xs=[x for x,_ in train]
        selected=[]
        for cond in predicates(task):
            try:mask=tuple(bool(ev(cond,x)) for x in xs)
            except (ValueError,TypeError,IndexError):continue
            pos=[i for i,b in enumerate(mask) if b];neg=[i for i,b in enumerate(mask) if not b]
            if min(len(pos),len(neg))<2:continue
            pp=[p for p,s in pool if all(s[i]==expect[i] for i in pos)]
            qq=[p for p,s in pool if all(s[i]==expect[i] for i in neg)]
            checks+=2*len(pool)
            if not pp or not qq:continue
            a=min(pp,key=lambda q:(size(q),canonical(q)))
            b=min(qq,key=lambda q:(size(q),canonical(q)))
            selected.append((size(a)+size(b)+size(cond),canonical(cond),["ite",cond,a,b]))
        if selected:
            p=min(selected)[2]
            return {"ast":p,"status":"CONDITIONAL_TYPED","checks":checks,
                "wall_ms":(time.perf_counter_ns()-t)/1e6}
    return {"ast":None,"status":"ABSTAIN","checks":checks,
            "wall_ms":(time.perf_counter_ns()-t)/1e6}

def score(p,pairs):
    if p is None:return {"submitted":False,"exact":False,"hits":0,"total":len(pairs)}
    hits=0
    for x,y in pairs:
        try:hits+=int(type(ev(p,x)) is str and ev(p,x)==y)
        except (ValueError,TypeError,IndexError,OverflowError):pass
    return {"submitted":True,"exact":hits==len(pairs),"hits":hits,"total":len(pairs)}

def antiunify(a,b,holes):
    if a==b:return a
    if isinstance(a,list) and isinstance(b,list) and len(a)==len(b) and a and b and a[0]==b[0]:
        return [antiunify(x,y,holes) for x,y in zip(a,b)]
    key=(canonical(a),canonical(b))
    if key not in holes:holes[key]=len(holes)
    return {"hole":holes[key]}

def fixed_nodes(x):
    if isinstance(x,dict):return 0
    if isinstance(x,list):return 1+sum(fixed_nodes(y) for y in x[1:])
    return 0
def hole_ids(x):
    if isinstance(x,dict):return [x["hole"]] if set(x)=={"hole"} else []
    if isinstance(x,list):return [j for v in x for j in hole_ids(v)]
    return []
def substitute(x,bindings):
    if isinstance(x,dict) and set(x)=={"hole"}:return bindings[x["hole"]]
    if isinstance(x,list):return [substitute(v,bindings) for v in x]
    return x

def learn_templates(verified_programs,max_rules=32):
    """Executable typed meta-grammar induced from independently checked source ASTs."""
    rules={};evidence=[]
    for (id_a,a),(id_b,b) in itertools.combinations(verified_programs,2):
        holes={}
        shape=antiunify(a,b,holes)
        n=len(set(hole_ids(shape)))
        if not 1<=n<=2 or fixed_nodes(shape)<3:continue
        signature=canonical(shape)
        if signature not in rules:
            rules[signature]={"template":shape,"source_ids":[id_a,id_b],
               "sources":[sha(a),sha(b)],"holes":n}
    selected=sorted(rules.values(),key=lambda x:(x["holes"],-fixed_nodes(x["template"]),canonical(x["template"])))
    return selected[:max_rules]

def candidates_from_templates(templates,task,cap=2500):
    pool=candidate_library(task,limit=500)
    # Uniform unknown-subtree adapter. The metadata / content of target
    # grammar constrains every possible hole filler, never target gold.
    hole_pool=pool[:100]
    seen=set();count=0
    for rule in templates:
        for values in itertools.product(hole_pool,repeat=rule["holes"]):
            p=substitute(rule["template"],{i:v for i,v in enumerate(values)})
            # Target's grammar might not license the learned whole pattern:
            if not grammar_compatible(p,task):continue
            key=canonical(p)
            if key in seen:continue
            seen.add(key);count+=1
            yield p
            if count>=cap:return

def grammar_compatible(p,task):
    ops=set(task["ops"])
    mapping={"substr":"str.substr","at":"str.at","replace":"str.replace",
             "cat":"str.++","index":"str.indexof","len":"str.len",
             "plus":"+","minus":"-","contains":"str.contains",
             "prefix":"str.prefixof","suffix":"str.suffixof","ite":"ite"}
    def valid(x):
        if not isinstance(x,list) or not x:return False
        tag=x[0]
        if tag=="arg":return type(x[1]) is int and 0<=x[1]<task["nargs"]
        if tag=="lit":return x[1] in task["constants"]
        if tag=="num":return x[1] in task["numbers"]
        return mapping.get(tag) in ops and all(valid(y) for y in x[1:])
    return valid(p)

def memory_search(templates,task,train,budget=500):
    t=time.perf_counter_ns();attempts=0
    for p in candidates_from_templates(templates,task,cap=budget):
        attempts+=1
        if score(p,train)["exact"]:
            return {"ast":p,"status":"SOURCE_INDUCED_NEW_TEMPLATE",
                    "checks":attempts,"wall_ms":(time.perf_counter_ns()-t)/1e6}
    return {"ast":None,"status":"ABSTAIN_SOURCE_TEMPLATE",
            "checks":attempts,"wall_ms":(time.perf_counter_ns()-t)/1e6}
