"""RC28: independently checked semantic normal forms of actual GRU-extracted
new machines. Original own-weight tensors & raw AUTO_STATE text in ZIP.
Human authored this interpreter and independent exact verifier. Never assert
all-length original continuous GRU correctness from this finite-state proof.
"""
from collections import deque
from itertools import combinations
SUFFIX101={"initial":"A","transitions":{
"A":{"0":("A",0),"1":("B",0)},
"B":{"0":("C",0),"1":("B",0)},
"C":{"0":("A",0),"1":("B",1)}}}
SEEN101={"initial":"A","transitions":{
"A":{"0":("A",0),"1":("B",0)},
"B":{"0":("C",0),"1":("B",0)},
"C":{"0":("A",0),"1":("D",1)},
"D":{"0":("D",1),"1":("D",1)}}}

def run(machine,stream):
    s=machine["initial"];out=[]
    for x in stream:
        if x not in (0,1):raise ValueError("binary")
        s,y=machine["transitions"][s][str(x)]
        out.append(y)
    return tuple(out)

def ref_next(task,state,bit):
    if task=="seen101" and state==3:return 3,1
    w=(1,0,1)[:state]+(bit,)
    ns=max((j for j in range(1,4) if w[-j:]==(1,0,1)[:j]),default=0)
    return ns,int(ns==3)

def prove_all_lengths(machine,task):
    pair=(machine["initial"],0);q=deque([(pair,())]);seen={pair}
    while q:
        (p,r),prefix=q.popleft()
        for b in (0,1):
            nxt,out=machine["transitions"][p][str(b)]
            rnext,goal=ref_next(task,r,b)
            if out!=goal:
                return {"status":"FAIL","counterexample":prefix+(b,)}
            v=(nxt,rnext)
            if v not in seen:seen.add(v);q.append((v,prefix+(b,)))
    return {"status":"PROVED_FOR_EXTRACTED_DFA_ONLY","product_pairs":len(seen)}

def is_minimal(machine):
    states=list(machine["transitions"])
    reachable={machine["initial"]};q=[machine["initial"]]
    for s in q:
        for b in "01":
            nxt=machine["transitions"][s][b][0]
            if nxt not in reachable:reachable.add(nxt);q.append(nxt)
    if len(reachable)!=len(states):return False
    for a,b in combinations(states,2):
        pairs={(a,b)};todo=deque([(a,b)]);distinct=False
        while todo:
            x,y=todo.popleft()
            for c in "01":
                u,v=machine["transitions"][x][c],machine["transitions"][y][c]
                if u[1]!=v[1]:distinct=True;break
                nxt=(u[0],v[0])
                if nxt not in pairs:pairs.add(nxt);todo.append(nxt)
            if distinct:break
        if not distinct:return False
    return True
