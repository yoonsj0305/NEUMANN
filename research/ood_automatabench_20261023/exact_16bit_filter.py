"""Exact 4x4 binary CA state-space filter: enumerate only 2^16 candidates once.

No SAT, no learned parameters, no private data. Complete exhaustive search is
mathematically exact at 16 bits; not scalable to 64-bit unbounded worlds.
Every reversible Margolus step matches the independent native simulator.
Output only for one surviving initial state and after independent replay.
"""
from __future__ import annotations
import collections,time
import numpy as np
from reversible_ca_solver import valid_task,native_verify,blocks,solve

def step_vectorized(states,rule,height,width,t):
    perm=np.asarray(rule,dtype=np.uint16)
    nxt=np.zeros_like(states)
    for block in blocks(height,width,t):
        positions=[y*width+x for y,x in block]
        nibble=np.zeros_like(states)
        for j,pos in enumerate(positions):
            nibble|=((states>>pos)&np.uint16(1))<<j
        out=perm[nibble]
        for j,pos in enumerate(positions):
            nxt|=((out>>j)&np.uint16(1))<<pos
    return nxt

def exhaustive_4x4(row):
    start=time.process_time()
    h,w,T,perm=valid_task(row)
    if (h,w)!=(4,4):
        fallback=solve(row,policy="propagation")
        return {"status":"FALLBACK_NON4X4_"+fallback["status"],
                "prediction":fallback.get("prediction"),
                "cpu_s":time.process_time()-start,
                "method":"SAT_FOR_GENERAL_GRID"}
    initial=np.arange(65536,dtype=np.uint16)
    states=initial.copy()
    obs=collections.defaultdict(list)
    for o in row["observations"]:obs[int(o["t"])].append(o)
    survivor_count_by_t=[]
    for t in range(T+1):
        if len(states):
            for o in obs[t]:
                pos=int(o["y"])*w+int(o["x"]);value=int(o["value"])
                mask=((states>>pos)&np.uint16(1))==value
                states=states[mask]
                initial=initial[mask]
                if len(states)==0:break
        survivor_count_by_t.append(len(states))
        if t<T and len(states):states=step_vectorized(states,perm,h,w,t)
    if len(initial)!=1:
        return {"status":"UNKNOWN_NO_UNIQUE_16BIT_STATE","prediction":None,
                "candidate_count":len(initial),"candidate_counts":survivor_count_by_t,
                "cpu_s":time.process_time()-start,
                "method":"EXHAUSTIVE_CONSTRAINT_FILTER"}
    bitfield=int(initial[0])
    solution=["".join("1" if (bitfield>>(y*w+x))&1 else "0" for x in range(w)) for y in range(h)]
    if not native_verify(row,solution):
        raise AssertionError("independent 2D forward dynamics rejects exact 16bit survivor")
    return {"status":"PROVEN_UNIQUE_EXHAUSTIVE_16BIT",
            "prediction":solution,"candidate_count":1,
            "candidate_counts":survivor_count_by_t,
            "cpu_s":time.process_time()-start,
            "method":"EXHAUSTIVE_CONSTRAINT_FILTER"}
