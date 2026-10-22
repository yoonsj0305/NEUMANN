"""Independent-author AutomataBench reversible 2D Margolus CA: verified exact inverse.

Solver gets only public task definition (rule and partial space-time observations),
NEVER dataset metadata or heldout 'answer'. Two policies:
  zero-fill: author's published observation-only baseline.
  propagation+SAT: explicit constraint-domain propagation then exact Z3 completion.
Check reconstructed answer through an entirely separate pure-Python forward rollout.
SAT second solution query proves uniqueness (or marks unverified).
This is a classical solver adapting a known task schema, not neural invention.
"""
from __future__ import annotations
import collections,time
from z3 import And,Bool,BoolVal,Not,Or,Solver,sat,unsat,unknown

def valid_task(task):
    grid=task["grid"]
    height=int(grid["height"]);width=int(grid["width"]);T=int(task["time_horizon"])
    perm=[int(i) for i in task["rule"]["permutation"]]
    assert grid["boundary"]=="torus" and height>0 and width>0 and height%2==width%2==0
    assert len(perm)==16 and sorted(perm)==list(range(16))
    assert task["rule"]["type"]=="margolus_block_ca"
    assert 0<=T<=30 and height*width<=256
    for o in task["observations"]:
        assert 0<=int(o["x"])<width and 0<=int(o["y"])<height
        assert 0<=int(o["t"])<=T and int(o["value"]) in (0,1)
    assert "answer" not in task and "metadata" not in task
    return height,width,T,perm

def blocks(height,width,t):
    offset=t%2
    for y in range(offset,height,2):
        for x in range(offset,width,2):
            yield ((y,x),(y,(x+1)%width),((y+1)%height,x),((y+1)%height,(x+1)%width))

def roll_one(state,t,permutation):
    h=len(state);w=len(state[0]);out=[[0]*w for _ in range(h)]
    for block in blocks(h,w,t):
        value=sum(state[y][x]<<j for j,(y,x) in enumerate(block))
        nxt=permutation[value]
        for j,(y,x) in enumerate(block):out[y][x]=(nxt>>j)&1
    return out

def native_verify(task,initial):
    height,width,T,perm=valid_task(task)
    state=[[int(x) for x in row] for row in initial]
    if len(state)!=height or any(len(row)!=width for row in state):return False
    obs=collections.defaultdict(list)
    for o in task["observations"]:obs[int(o["t"])].append(o)
    for t in range(T+1):
        for o in obs[t]:
            if state[int(o["y"])][int(o["x"])]!=int(o["value"]):return False
        if t<T:state=roll_one(state,t,perm)
    return True

def published_zero_fill(task):
    h,w,_,_=valid_task(task)
    state=[[0]*w for _ in range(h)]
    for o in task["observations"]:
        if int(o["t"])==0:state[int(o["y"])][int(o["x"])]=int(o["value"])
    return ["".join(map(str,row)) for row in state]

def source_domains(task,use_propagation=True):
    h,w,T,perm=valid_task(task)
    domains=[[[3]*w for _ in range(h)] for _ in range(T+1)]
    for o in task["observations"]:
        t=int(o["t"]);y=int(o["y"]);x=int(o["x"])
        v=1<<int(o["value"])
        domains[t][y][x]&=v
        if domains[t][y][x]==0:return None,0,0
    initial_fixed=sum(v in (1,2) for matrix in domains for row in matrix for v in row)
    if not use_propagation:return domains,initial_fixed,0
    events=0
    changed=True
    while changed:
        changed=False
        for t in range(T):
            for block in blocks(h,w,t):
                survivors=[]
                for input_pattern in range(16):
                    output_pattern=perm[input_pattern]
                    if all((domains[t][y][x] & (1<<((input_pattern>>j)&1))) and
                           (domains[t+1][y][x] & (1<<((output_pattern>>j)&1)))
                           for j,(y,x) in enumerate(block)):
                        survivors.append((input_pattern,output_pattern))
                if not survivors:return None,initial_fixed,events
                for j,(y,x) in enumerate(block):
                    p_in=0;p_out=0
                    for a,b in survivors:
                        p_in|=1<<((a>>j)&1)
                        p_out|=1<<((b>>j)&1)
                    new_in=domains[t][y][x]&p_in
                    new_out=domains[t+1][y][x]&p_out
                    if not new_in or not new_out:return None,initial_fixed,events
                    if new_in!=domains[t][y][x]:
                        domains[t][y][x]=new_in;changed=True;events+=1
                    if new_out!=domains[t+1][y][x]:
                        domains[t+1][y][x]=new_out;changed=True;events+=1
    return domains,initial_fixed,events

def solve(task,policy="propagation",time_limit_ms=12000):
    assert policy in ("plain","propagation")
    start=time.process_time()
    h,w,T,perm=valid_task(task)
    dom,initial_fixed,events=source_domains(task,policy=="propagation")
    if dom is None:return {"status":"UNSAT_CONTRADICTION","prediction":None,"cpu_s":time.process_time()-start}
    total=(T+1)*h*w
    known=sum(v!=3 for matrix in dom for row in matrix for v in row)
    if known==total:
        initial=["".join("0" if v==1 else "1" for v in row) for row in dom[0]]
        if not native_verify(task,initial):raise AssertionError("propagated all-fixed solution fails independently")
        return {"status":"EXACT_PROPAGATION_COMPLETE","prediction":initial,"uniqueness":"PROVEN",
                "known_before":initial_fixed,"known_after":known,"propagation_events":events,
                "cpu_s":time.process_time()-start}
    cells=[[[Bool(f"b_{t}_{y}_{x}") for x in range(w)] for y in range(h)] for t in range(T+1)]
    solver=Solver();solver.set("timeout",time_limit_ms)
    # Fixed source observations + all unary facts entailed by exact arc-consistency.
    for t in range(T+1):
        for y in range(h):
            for x in range(w):
                if dom[t][y][x]!=3:solver.add(cells[t][y][x] == BoolVal(dom[t][y][x]==2))
    for t in range(T):
        for block in blocks(h,w,t):
            clauses=[]
            for pattern in range(16):
                mapped=perm[pattern]
                if not all((dom[t][y][x] & (1<<((pattern>>j)&1))) and
                           (dom[t+1][y][x] & (1<<((mapped>>j)&1)))
                           for j,(y,x) in enumerate(block)):continue
                current=[cells[t][y][x] == BoolVal(bool((pattern>>j)&1)) for j,(y,x) in enumerate(block)]
                future=[cells[t+1][y][x] == BoolVal(bool((mapped>>j)&1)) for j,(y,x) in enumerate(block)]
                clauses.append(And(*(current+future)))
            if not clauses:raise AssertionError("propagation did not see empty source")
            solver.add(Or(*clauses))
    outcome=solver.check()
    if outcome!=sat:
        return {"status":"TIMEOUT_OR_UNSAT" if outcome==unknown else "UNSAT",
            "prediction":None,"known_before":initial_fixed,"known_after":known,
            "cpu_s":time.process_time()-start}
    model=solver.model()
    initial=["".join("1" if bool(model.eval(cells[0][y][x],model_completion=True)) else "0"
                     for x in range(w)) for y in range(h)]
    # Pure native forward simulation is separate from SAT's transition encoding.
    if not native_verify(task,initial):
        raise AssertionError("Z3 SAT prediction fails native independently implemented dynamics")
    # Uniqueness check: prevent model promotion when more than one initial grid fits.
    solver.add(Or(*(cells[0][y][x] != BoolVal(initial[y][x]=="1")
                    for y in range(h) for x in range(w))))
    second=solver.check()
    status="EXACT_SAT_UNIQUE" if second==unsat else ("ABSTAIN_SECOND_SOLUTION" if second==sat else "ABSTAIN_UNIQUENESS_TIMEOUT")
    return {"status":status,"prediction":initial if second==unsat else None,
            "uniqueness":"PROVEN" if second==unsat else "NOT_PROVEN",
            "known_before":initial_fixed,"known_after":known,
            "propagation_events":events,"cpu_s":time.process_time()-start}
