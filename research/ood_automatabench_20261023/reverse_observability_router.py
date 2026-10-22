"""Exact observability-driven inverse-CA dispatch, for reversible Margolus grids up to 64 bits.

Given a known bijective 2x2 block rule and partially observed last time slice,
there are exactly 2^m compatible terminal grids where m is the number of
unobserved terminal cells. Reverse every candidate through the uniquely
invertible Margolus transitions and filter observations at each previous
time slice. Unique initial state => exact. Does not scale as 2^total_bits,
unless terminal observations are absent. For m>bound use proven exact SAT.
"""
from __future__ import annotations
import collections,time
import numpy as np
from reversible_ca_solver import blocks,valid_task,native_verify,solve
from exact_16bit_filter import exhaustive_4x4

MAX_TERMINAL_MISSING=10

def reverse_step_vector(states,permutation,height,width,forward_time):
    """Backward inverse transition over a vector of <=64-bit grid states."""
    invert=[0]*16
    assert len(permutation)==16 and sorted(permutation)==list(range(16))
    for inp,out in enumerate(permutation):invert[out]=inp
    inv=np.asarray(invert,dtype=np.uint64)
    nxt=np.zeros_like(states,dtype=np.uint64)
    for block in blocks(height,width,forward_time):
        idx=np.zeros_like(states,dtype=np.uint64)
        locations=[y*width+x for y,x in block]
        for j,pos in enumerate(locations):
            idx|=((states>>np.uint64(pos)) & np.uint64(1))<<np.uint64(j)
        previous=inv[idx]
        for j,pos in enumerate(locations):
            nxt|=((previous>>np.uint64(j))&np.uint64(1))<<np.uint64(pos)
    return nxt

def solve_terminal_inverse(task,miss_cap=MAX_TERMINAL_MISSING):
    t0=time.process_time()
    h,w,T,perm=valid_task(task)
    if h*w>64 or T<1:
        return {"status":"INELIGIBLE_64BIT_OR_HORIZON",
                "prediction":None,"cpu_s":time.process_time()-t0}
    observations=collections.defaultdict(list)
    for o in task["observations"]:observations[int(o["t"])].append(o)
    terminal={}
    for o in observations[T]:
        pos=int(o["y"])*w+int(o["x"])
        val=int(o["value"])
        if pos in terminal and terminal[pos]!=val:
            return {"status":"UNSAT_CONTRADICTORY_OBSERVATIONS","prediction":None,"cpu_s":time.process_time()-t0}
        terminal[pos]=val
    absent=[p for p in range(h*w) if p not in terminal]
    m=len(absent)
    if m>miss_cap:
        return {"status":"INELIGIBLE_TOO_MANY_UNOBSERVED_TERMINAL",
                "prediction":None,"unobserved_terminal":m,"cpu_s":time.process_time()-t0}
    fixed=sum(np.uint64(val)<<np.uint64(pos) for pos,val in terminal.items()) if terminal else np.uint64(0)
    candidates=np.arange(1<<m,dtype=np.uint64)
    states=np.full(len(candidates),np.uint64(fixed),dtype=np.uint64)
    for j,pos in enumerate(absent):
        states|=((candidates>>np.uint64(j))&np.uint64(1))<<np.uint64(pos)
    size_by_time={}
    for time_index in range(T,-1,-1):
        for o in observations[time_index]:
            pos=int(o["y"])*w+int(o["x"]);val=int(o["value"])
            states=states[((states>>np.uint64(pos))&np.uint64(1))==val]
            if len(states)==0:break
        size_by_time[str(time_index)]=len(states)
        if not len(states):break
        if time_index>0:
            states=reverse_step_vector(states,perm,h,w,time_index-1)
    if len(states)!=1:
        return {"status":"UNKNOWN_NO_UNIQUE_REVERSE" if len(states)>1 else "UNSAT_NO_REVERSE",
                "prediction":None,"remaining_states":len(states),
                "terminal_unknown":m,"survivors_per_t":size_by_time,
                "cpu_s":time.process_time()-t0}
    bits=int(states[0])
    answer=["".join("1" if (bits>>(y*w+x))&1 else "0" for x in range(w)) for y in range(h)]
    if not native_verify(task,answer):
        raise AssertionError("Reverse bitboard solution fails independent unoptimized CA forward verification")
    return {"status":"PROVEN_UNIQUE_BY_TERMINAL_ENUMERATION","prediction":answer,
            "uniqueness":"EXHAUSTIVE_ON_TERMINAL_COMPLETIONS",
            "terminal_unknown":m,"survivors_per_t":size_by_time,
            "cpu_s":time.process_time()-t0}

def adaptive_solve(task,terminal_cap=MAX_TERMINAL_MISSING):
    begin=time.process_time()
    h,w,T,_=valid_task(task)
    if h*w==16 and h==w==4:
        v=exhaustive_4x4(task)
        route="EXACT_16BIT_ENUM"
    else:
        # Take no decision based on held-out answers or difficulty labels.
        reverse=solve_terminal_inverse(task,terminal_cap)
        if reverse["status"] not in ("INELIGIBLE_64BIT_OR_HORIZON",
                                     "INELIGIBLE_TOO_MANY_UNOBSERVED_TERMINAL"):
            v=reverse;route="REVERSE_OBSERVATION_ENUM"
        else:
            v=solve(task,policy="propagation")
            route="PROVEN_SAT_FALLBACK"
    result=dict(v)
    result["route"]=route
    result["cpu_s"]=time.process_time()-begin
    return result
