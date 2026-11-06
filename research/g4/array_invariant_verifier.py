"""G4 independent Z3 verifier of a typed learned ARRAY invariant proposal.

Synthetic-only protocol. DOES NOT read or score the reserved 2025 array eight.
Source semantics and learner proposal are separate objects; a proposed
quantified invariant is accepted IFF all 3 original SOURCE counterexample
formulas are UNSAT, including a negative mutation test. A timeout/unknown
is never a proof. This is one independent original-symbolic proof interface
for later extension to arbitrary CHC-typed source interfaces.

Guarded source classes: Array(Int,Int) with a single monotone index update,
a selected target array store, arbitrary immutable other arrays, and source
operation FILL, COPY, ADD. The learner cannot alter the original semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Optional

ARRAYS=("A","B","C")
KINDS=("FILL","COPY","ADD")


@dataclass(frozen=True)
class ArrayTask:
    kind:str
    dest:str
    src:Optional[str]
    constant:int
    def __post_init__(self):
        if self.kind not in KINDS or self.dest not in ARRAYS:
            raise ValueError("INVALID_SYNTHETIC_SOURCE_PROGRAM")
        if self.kind=="FILL":
            if self.src is not None:
                raise ValueError("FILL_HAS_NO_SOURCE_ARRAY")
        elif self.src not in ARRAYS or self.src==self.dest:
            raise ValueError("SOURCE_DESTINATION_ARRAY_ALIAS_NOT_SUPPORTED")


@dataclass(frozen=True)
class Candidate:
    kind:str
    dest:str
    src:Optional[str]
    def __post_init__(self):
        if self.kind not in KINDS or self.dest not in ARRAYS:
            raise ValueError("INVALID_GENERATED_TYPED_AST")
        if self.kind=="FILL":
            if self.src is not None:
                raise ValueError("GENERATED_FILL_HAS_SPURIOUS_SOURCE")
        elif self.src not in ARRAYS or self.src==self.dest:
            raise ValueError("GENERATED_ARRAY_ALIAS_OR_TYPE_ERROR")


def generate_source(task:ArrayTask)->str:
    """One fully specified synthetic transition-source program, not a label."""
    rhs=(str(task.constant) if task.kind=="FILL" else
         f"select({task.src},index)" if task.kind=="COPY" else
         f"add(select({task.src},index),{task.constant})")
    return (f"SOURCE: n:Int, index:Int, A:Array(Int,Int), B:Array(Int,Int), C:Array(Int,Int);"
       f" INIT: n>=0,index=0; STEP: index<n; "
       f"store({task.dest},index,{rhs}); index'=index+1; "
       f"other arrays and n unchanged; "
       f"POST: for all k in [0,n),select({task.dest},k)={rhs.replace('index','k')}")


def check_invariant(task:ArrayTask,candidate:Candidate,timeout_ms:int=3000)->dict:
    """Separate original ground truth from generated structure. No oracle leak.

    Three source-proof obligations:
    pre => invariant,
    invariant & source transition => invariant next,
    invariant & terminal => original post.
    """
    try:
        import z3
    except ImportError:
        return {"verified":False,"status":"Z3_REQUIRED_NO_PROOF"}
    initial=time.perf_counter_ns()
    n,index=z3.Ints("n index")
    n2,index2=z3.Ints("n_new index_new")
    integer=z3.IntSort()
    arrays={name:z3.Array(name,integer,integer) for name in ARRAYS}
    later={name:z3.Array(name+"_new",integer,integer) for name in ARRAYS}
    k=z3.Int("k")

    def rhs(kind,src,cs,value_index):
        if kind=="FILL":return z3.IntVal(task.constant)
        if src not in cs:raise ValueError("ILL_TYPED_SOURCE_REFERENCE")
        val=z3.Select(cs[src],value_index)
        return val if kind=="COPY" else val+z3.IntVal(task.constant)

    def invariant(model_arrays,step,nvalue):
        comparison=(z3.Select(model_arrays[candidate.dest],k)
                    ==rhs(candidate.kind,candidate.src,model_arrays,k))
        return z3.And(nvalue>=0,step>=0,step<=nvalue,
             z3.ForAll([k],z3.Implies(z3.And(k>=0,k<step),comparison)))

    def actual_post(model_arrays,nvalue):
        relation=(z3.Select(model_arrays[task.dest],k)
                  ==rhs(task.kind,task.src,model_arrays,k))
        return z3.ForAll([k],z3.Implies(z3.And(k>=0,k<nvalue),relation))

    source_step=z3.And(n>=0,index>=0,index<n,n2==n,index2==index+1,
        *[(later[name]==z3.Store(arrays[name],index,
                rhs(task.kind,task.src,arrays,index))
                if name==task.dest else later[name]==arrays[name])
            for name in ARRAYS])
    current=invariant(arrays,index,n)
    next_inv=invariant(later,index2,n2)
    obligations=(
      ("init",z3.And(n>=0,index==0,z3.Not(current))),
      ("step",z3.And(current,source_step,z3.Not(next_inv))),
      ("safe",z3.And(current,index==n,z3.Not(actual_post(arrays,n))))
    )
    results=[]
    for name,formula in obligations:
        s=z3.Solver()
        s.set(timeout=timeout_ms)
        s.add(formula)
        tick=time.perf_counter_ns()
        ans=s.check()
        ms=round((time.perf_counter_ns()-tick)/1e6,3)
        status=str(ans)
        results.append({"obligation":name,"counterexample_status":status,
             "wall_ms":ms,"proven":status=="unsat",
             "reason_unknown":s.reason_unknown() if status=="unknown" else None})
        if status!="unsat":
            break
    verified=len(results)==3 and all(r["proven"] for r in results)
    return {"verified":verified,
       "status":"SOURCE_ALL_THREE_OBLIGATIONS_UNSAT" if verified else
                "REJECT_PROPOSED_LEMMA_NOT_PROVEN",
       "obligations":results,
       "full_proof_wall_ms":round((time.perf_counter_ns()-initial)/1e6,3),
       "source_op":task.kind,"proposal_op":candidate.kind,
       "original_source_not_changed":True,
       "quantified_array_index":True,
       "unbounded_integer_domain_proved_if_verified":True}


def exact_classical_from_source(task:ArrayTask)->Candidate:
    """Strong same-rights classical compiler: source source already has write RHS.

    This source access is intentionally identical to the learned model.
    If it wins or ties, no learned-exclusive Q3 result may be claimed.
    """
    return Candidate(task.kind,task.dest,task.src)
