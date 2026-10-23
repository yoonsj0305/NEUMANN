"""Exact observability-driven inverse-CA dispatch, for reversible Margolus grids up to 64 bits.

Given a known bijective 2x2 block rule and partially observed last time slice,
there are exactly 2^m compatible terminal grids where m is the number of
unobserved terminal cells. Reverse every candidate through the uniquely
invertible Margolus transitions and filter observations at each previous
time slice. Unique initial state => exact. Does not scale as 2^total_bits,
unless terminal observations are absent. For m>bound use proven exact SAT.
"""
from __future__ import annotations
import collections,time,hashlib,json,random
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
    # Build all candidate bitfields with Python integers FIRST. NumPy 1.26 can
    # silently lose upper bits in mixed scalar/array uint64 shift expressions.
    # <=2^10 candidates is tiny, so this removes a correctness hazard without
    # changing the exhaustive search semantics or the vectorized CA inverse.
    fixed=sum(int(val)<<int(pos) for pos,val in terminal.items())
    states=np.asarray([
        fixed | sum(((assignment>>j)&1)<<int(pos) for j,pos in enumerate(absent))
        for assignment in range(1<<m)
    ],dtype=np.uint64)
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
    if len(states)>1:
        # Bijection means distinct terminal completions map to DISTINCT
        # initial states. Independently replay two source-compatible initial
        # states to give a constructive, rather than heuristic, nonuniqueness
        # proof. This is a complete decision within the <=2^10 terminal class.
        witnesses=list(dict.fromkeys(int(v) for v in states))[:2]
        if len(witnesses)!=2:
            raise AssertionError("distinct terminal states collapsed during bijective inversion")
        witness_grids=[["".join(str((value>>(y*w+x))&1) for x in range(w)) for y in range(h)]
                       for value in witnesses]
        assert witness_grids[0]!=witness_grids[1]
        for candidate in witness_grids:
            assert native_verify(task,candidate),"invalid reverse-model nonuniqueness proof"
        return {"status":"PROVEN_NONUNIQUE_EXHAUSTIVE_TERMINAL_COMPLETIONS",
                "prediction":None,"uniqueness":"DISPROVEN_BY_TWO_EXACT_INITIAL_STATES",
                "remaining_states":len(states),"witness_count":2,
                "witness_initial_states":witness_grids,
                "witness_identity_sha256":hashlib.sha256(
                    (str(witnesses[0])+":"+str(witnesses[1])).encode()).hexdigest(),
                "terminal_unknown":m,"survivors_per_t":size_by_time,
                "cpu_s":time.process_time()-t0}
    if len(states)==0:
        return {"status":"UNSAT_NO_REVERSE","prediction":None,
                "remaining_states":0,"terminal_unknown":m,"survivors_per_t":size_by_time,
                "cpu_s":time.process_time()-t0}
    bits=int(states[0])
    answer=["".join("1" if (bits>>(y*w+x))&1 else "0" for x in range(w)) for y in range(h)]
    if not native_verify(task,answer):
        raise AssertionError("Reverse bitboard solution fails independent unoptimized CA forward verification")
    return {"status":"PROVEN_UNIQUE_BY_TERMINAL_ENUMERATION","prediction":answer,
            "uniqueness":"EXHAUSTIVE_ON_TERMINAL_COMPLETIONS",
            "terminal_unknown":m,"survivors_per_t":size_by_time,
            "cpu_s":time.process_time()-t0}

def solve_fully_observed_initial(task):
    """Exact no-search theorem: all N initial bits are supplied by t=0 source."""
    began=time.process_time()
    h,w,T,perm=valid_task(task)
    observed={}
    for o in task["observations"]:
        if int(o["t"])!=0:continue
        loc=int(o["y"])*w+int(o["x"])
        v=int(o["value"])
        if loc in observed and observed[loc]!=v:
            return {"status":"UNSAT_CONFLICTING_INITIAL_OBSERVATIONS",
                    "prediction":None,"cpu_s":time.process_time()-began}
        observed[loc]=v
    if len(observed)!=h*w:return None
    init=["".join(str(observed[y*w+x]) for x in range(w)) for y in range(h)]
    if not native_verify(task,init):
        return {"status":"UNSAT_COMPLETE_INITIAL_CONTRADICTS_LATER_OBSERVATIONS",
                "prediction":None,"cpu_s":time.process_time()-began}
    return {"status":"PROVEN_UNIQUE_ALL_INITIAL_BITS_OBSERVED",
            "prediction":init,"uniqueness":"PROVEN_BY_COMPLETE_T0_OBSERVATION",
            "cpu_s":time.process_time()-began}

def prove_nonunique_two_reversible_witnesses(task,trial_cap=256):
    """Return a proof of nonuniqueness ONLY if two distinct exact trajectories
    satisfy ALL source observations. Failure to find a pair is not evidence
    of uniqueness and callers MUST fallback to an exact solver.
    """
    start=time.process_time()
    h,w,T,perm=valid_task(task)
    if h*w>64 or T<1:return None
    by_t=collections.defaultdict(list)
    for o in task["observations"]:by_t[int(o["t"])].append(o)
    fixed={}
    for o in by_t[T]:
        pos=int(o["y"])*w+int(o["x"]);v=int(o["value"])
        if pos in fixed and fixed[pos]!=v:
            return {"status":"UNSAT_CONTRADICTORY_TERMINAL_OBSERVATIONS",
                    "prediction":None,"cpu_s":time.process_time()-start}
        fixed[pos]=v
    missing=[pos for pos in range(h*w) if pos not in fixed]
    if len(missing)<=MAX_TERMINAL_MISSING:return None
    first=sum(int(v)<<int(pos) for pos,v in fixed.items())
    key=json.dumps({"grid":task["grid"],"rule":task["rule"],
                    "time_horizon":T,"observations":task["observations"]},
                   sort_keys=True,separators=(",",":"))
    rng=random.Random(int(hashlib.sha256(key.encode()).hexdigest()[:16],16))
    # Must build high bits with Python integers before NumPy 1.26 conversion.
    proposals=[]
    for _ in range(trial_cap):
        assignment=rng.getrandbits(len(missing))
        completed=first | sum(((assignment>>j)&1)<<int(pos) for j,pos in enumerate(missing))
        proposals.append(completed)
    states=np.asarray(proposals,dtype=np.uint64)
    for t in range(T,-1,-1):
        for o in by_t[t]:
            pos=int(o["y"])*w+int(o["x"])
            states=states[((states>>np.uint64(pos))&np.uint64(1))==int(o["value"])]
            if len(states)==0:break
        if not len(states):break
        if t>0:states=reverse_step_vector(states,perm,h,w,t-1)
    witnesses=list(dict.fromkeys(int(v) for v in states))[:2]
    if len(witnesses)!=2:return None
    witness_grids=[["".join(str((bits>>(y*w+x))&1) for x in range(w)) for y in range(h)]
                   for bits in witnesses]
    assert witnesses[0]!=witnesses[1] and witness_grids[0]!=witness_grids[1]
    for initial in witness_grids:
        assert native_verify(task,initial),"false nonunique proof"
    return {"status":"PROVEN_NONUNIQUE_TWO_DISTINCT_INITIAL_STATES",
            "prediction":None,"witnesses_verified_by_forward_simulation":2,
            "witness_initial_states":witness_grids,
            "witness_identity_sha256":hashlib.sha256(
                (str(witnesses[0])+":"+str(witnesses[1])).encode()).hexdigest(),
            "source_terminal_unobserved":len(missing),
            "sampled_completions":trial_cap,
            "cpu_s":time.process_time()-start}

def adaptive_solve(task,terminal_cap=MAX_TERMINAL_MISSING):
    begin=time.process_time()
    h,w,T,_=valid_task(task)
    if h*w==16 and h==w==4:
        v=exhaustive_4x4(task)
        route="EXACT_16BIT_ENUM"
    else:
        # Cheapest source-certificate first. Both are exact: complete t0 fixes
        # every initial bit, and two witnessed trajectories disprove uniqueness.
        directly=solve_fully_observed_initial(task)
        if directly is not None:
            v=directly;route="DIRECT_FULL_INITIAL_OBSERVATION"
        else:
            # Take no decision based on held-out answers or difficulty labels.
            reverse=solve_terminal_inverse(task,terminal_cap)
            if reverse["status"] not in ("INELIGIBLE_64BIT_OR_HORIZON",
                                         "INELIGIBLE_TOO_MANY_UNOBSERVED_TERMINAL"):
                v=reverse;route="REVERSE_OBSERVATION_ENUM"
            else:
                proof=prove_nonunique_two_reversible_witnesses(task)
                if proof is not None:
                    v=proof;route="CONSTRUCTIVE_NONUNIQUENESS_CERTIFICATE"
                else:
                    v=solve(task,policy="propagation")
                    route="PROVEN_SAT_FALLBACK"
    result=dict(v)
    result["route"]=route
    result["cpu_s"]=time.process_time()-begin
    return result
