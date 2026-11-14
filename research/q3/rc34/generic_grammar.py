"""RC34: reusable CLASSICAL (not neural) general-language compiler.
Infers any observed alphabet and arbitrary RHS length >=0 without enumerated
max. Exactness is CONDITIONAL on a trusted single-symbol parallel rewrite
contract; raw finite IO cannot prove that contract. Costs membership calls.
"""
from itertools import combinations
import hashlib

def weak_splits(total,n):
    if total<0 or n<1:raise ValueError("bad size")
    for bars in combinations(range(total+n-1),n-1):
        previous=-1;out=[]
        for v in bars:out.append(v-previous-1);previous=v
        out.append(total+n-2-previous);yield tuple(out)

def apply(w,grammar,depth=1):
    if depth<0:raise ValueError("depth")
    for _ in range(depth):w="".join(grammar[c] for c in w)
    return w

def discover(task,max_splits=200000):
    alphabet=task["alphabet"];src=tuple(task["sources"]);answers=tuple(task["io"])
    if not alphabet or len(set(alphabet))!=len(alphabet):return {"status":"UNKNOWN_ALPHABET"}
    if src!=tuple(alphabet[i:]+alphabet[:i] for i in range(len(alphabet))):
        return {"status":"UNKNOWN_LAYOUT"}
    if len(src)!=len(answers) or any(set(w)-set(alphabet) for w in answers):
        return {"status":"UNKNOWN_IO"}
    candidates=[];examined=0;first=answers[0]
    for lengths in weak_splits(len(first),len(alphabet)):
        examined+=1
        if examined>max_splits:return {"status":"UNKNOWN_BUDGET"}
        i=0;grammar={}
        for a,n in zip(alphabet,lengths):grammar[a]=first[i:i+n];i+=n
        if all(apply(w,grammar)==y for w,y in zip(src,answers)):
            candidates.append(grammar)
    return {"status":("UNIQUE_CONDITIONAL" if len(candidates)==1 else
                       "AMBIGUOUS" if candidates else "UNKNOWN_NO_PROGRAM"),
            "candidates":candidates,"examined":examined,
            "assumption":"DETERMINISTIC_ONE_SYMBOL_PARALLEL_REWRITE"}

def admit(discovery,membership=None,max_queries=8):
    if discovery["status"] not in ("UNIQUE_CONDITIONAL","AMBIGUOUS"):
        return {"status":discovery["status"],"queries":0}
    c=discovery["candidates"][:];qcount=0
    while len(c)>1:
        if membership is None or qcount>=max_queries:
            return {"status":"UNKNOWN_NO_ORACLE_OR_BUDGET","queries":qcount}
        letters=tuple(c[0])
        symbol=next((a for a in letters if len({g[a] for g in c})>1),None)
        if symbol is None:return {"status":"UNKNOWN_INDISTINGUISHABLE"}
        ans=membership(symbol);qcount+=1
        c=[g for g in c if g[symbol]==ans]
        if not c:return {"status":"UNKNOWN_CONTRADICTION","queries":qcount}
    return {"status":"CONDITIONAL_CLASS_CERTIFIED","grammar":c[0],
            "queries":qcount,"assumption":"TRUSTED_SINGLE_SYMBOL_PARALLEL_REWRITE"}

def emit(grammar):
    if any(type(k)!=str or len(k)!=1 or type(v)!=str or set(v)-set(grammar)
           for k,v in grammar.items()):raise ValueError("unsupported source")
    return "\n".join(k+" ::= "+(v or "EPS") for k,v in grammar.items())

def parse(text):
    if type(text)!=str or len(text)>100000:raise ValueError("unsafe code")
    gram={}
    for line in text.splitlines():
        if line.count(" ::= ")!=1:raise ValueError("invalid declaration")
        a,b=line.split(" ::= ")
        if len(a)!=1 or not a.isalpha() or not a.isupper() or a in gram:
            raise ValueError("invalid symbol")
        gram[a]="" if b=="EPS" else b
    if not gram or any(set(v)-set(gram) for v in gram.values()):
        raise ValueError("unbound symbol")
    if emit(gram)!=text:raise ValueError("noncanonical")
    return gram
