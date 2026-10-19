"""SELF-SUPERVISED continuous source-invariant discovery, REAL published SyGuS.

Preregistered GitHub Issue #273 BEFORE first attempt.
ONE-NEURON source-local learned linear representation by fixed-iteration
projected gradient descent on ONLY public Pre/Trans examples, not Post/gold,
not a pretrained/learned language model. Strong exact classical nullspace is
an eligible comparator; do NOT claim uniqueness if it also solves.
"""
from __future__ import annotations
import argparse, hashlib, json, math, time
from fractions import Fraction
from functools import reduce
from pathlib import Path
import numpy as np
import sympy as sp
import z3

from experiments.q3_source_prove import (
    sexprs, extract_mixed_original, native_original_relations,
    check_parity, check_formula, source_proof, EXPECTED,
)
from experiments.am2_sygus_native_three_vc_checker import (
    check_original_candidate,
)

SOURCE_DIR="comp/2018/Inv_Track"
TARGETS=(
 "cggmp2005_variant_true-unreach-call_true-termination.sl",
 "cggmp2005_true-unreach-call_true-termination.sl",
)
SCHEMA="neumann.q3.real-source-selfsupervised-one-neuron-first.v1"
N_PRE=12
N_TRANS=20
SOURCE_BOUND=32
NEURAL_SEED=17
STEPS=2500
ETA=0.15
RATIONAL_DENOMINATOR_LIMIT=12

def sha(data):
    return hashlib.sha256(data).hexdigest()

def canonical(x):
    return json.dumps(x,sort_keys=True,ensure_ascii=True,separators=(",",":"))

def sample_native(formula,variables,num,seed):
    solver=z3.Solver()
    solver.set(random_seed=seed,timeout=3000)
    solver.add(formula)
    solver.add(*(z3.And(v>=-SOURCE_BOUND,v<=SOURCE_BOUND) for v in variables))
    out=[]
    while len(out)<num:
        verdict=solver.check()
        if verdict!=z3.sat:break
        m=solver.model()
        state=tuple(m.eval(x,model_completion=True).as_long() for x in variables)
        out.append(state)
        solver.add(z3.Or(*[x!=a for x,a in zip(variables,state)]))
    return out

def source_samples(original,native):
    pre=sample_native(native["pre"],original["now"],N_PRE,3)
    both=original["now"]+original["next"]
    transitions=sample_native(native["trans"],both,N_TRANS,7)
    if not pre or not transitions:
        raise RuntimeError("PUBLIC_PRE_OR_TRANS_NO_SAMPLES")
    n=len(original["now"])
    # Preserve exact integer difference vectors for strong classical control.
    rows=[tuple(b[i+n]-b[i] for i in range(n)) for b in transitions]
    rows += [tuple(a[i]-pre[0][i] for i in range(n)) for a in pre[1:]]
    rows=[r for r in rows if any(r)]
    if not rows:raise RuntimeError("ALL_SOURCE_EXAMPLES_ZERO_CONSTRAINT")
    return pre,transitions,rows

def normalize_rows(rows):
    v=np.asarray(rows,dtype=np.float64)
    norms=np.linalg.norm(v,axis=1)
    return v/norms[:,None]

def learned_gradient_coefficients(rows,n):
    """One trainable linear neuron, no supervised structure labels at all.

    Objective: E[(w·(s'-s))²] and Pre-state constancy; unit norm projection
    prevents the trivial all-zero solution. Training gradients are computed
    from public transition examples, never from original Post or proof labels.
    """
    data=normalize_rows(rows)
    rng=np.random.default_rng(NEURAL_SEED+n)
    w=rng.normal(size=n)
    w=w/np.linalg.norm(w)
    initial_w=w.copy()
    initial_loss=float(np.mean(np.square(data@w)))
    began=time.perf_counter_ns()
    for _ in range(STEPS):
        grad=(2.0/len(data))*(data.T@(data@w))
        w=w-ETA*grad
        norm=float(np.linalg.norm(w))
        if norm<1e-12:raise RuntimeError("NEURON_COLLAPSED")
        w=w/norm
    train_ms=(time.perf_counter_ns()-began)/1e6
    final_loss=float(np.mean(np.square(data@w)))
    return {"trainable_parameter_count":n,"seed":NEURAL_SEED+n,
       "iterations":STEPS,"initial_weights":[float(x) for x in initial_w],
       "trained_weights":[float(x) for x in w],
       "trained_weights_sha256":sha(w.tobytes()),
       "initial_loss":initial_loss,"final_loss":final_loss,
       "train_wall_ms":round(train_ms,3)}

def primitive_integer_coefficients(weights):
    """Frozen generic rational readout: not a family/filename solution table."""
    weights=np.asarray(weights,dtype=np.float64)
    pivot=int(np.argmax(np.abs(weights)))
    if abs(weights[pivot])<1e-8:raise ValueError("ZERO_NEURAL_VECTOR")
    ratios=[Fraction(float(x/weights[pivot])).limit_denominator(
       RATIONAL_DENOMINATOR_LIMIT) for x in weights]
    lcm=math.lcm(*[f.denominator for f in ratios])
    ints=[int(f*lcm) for f in ratios]
    g=math.gcd(*[abs(x) for x in ints])
    if g==0:raise ValueError("ALL_ZERO_RATIONAL_CANDIDATE")
    ints=[x//g for x in ints]
    if ints[pivot]<0:ints=[-x for x in ints]
    return ints

def exact_classical_nullspace(rows,n):
    """Strongest exact linear-algebra baseline on IDENTICAL public observations."""
    began=time.perf_counter_ns()
    null=sp.Matrix(rows).nullspace()
    elapsed=(time.perf_counter_ns()-began)/1e6
    if len(null)!=1:
        return None,round(elapsed,3),len(null)
    rationals=[sp.Rational(x) for x in null[0]]
    m=sp.ilcm(*[f.q for f in rationals])
    ints=[int(v*m) for v in rationals]
    g=math.gcd(*[abs(x) for x in ints])
    ints=[x//g for x in ints]
    return ints,round(elapsed,3),len(null)

def source_nonnegative_bounds(original,native):
    """Only public Pre/Trans inductive nonnegative constraints, never Post."""
    assertions=[]
    now,nxt=original["now"],original["next"]
    for a,b in zip(now,nxt):
        pre_bad=z3.And(native["pre"],a<0)
        step_bad=z3.And(a>=0,native["trans"],b<0)
        if check_formula(pre_bad)=="unsat" and check_formula(step_bad)=="unsat":
            assertions.append(a>=0)
    return assertions

def source_only_equality(weights,initial_state,variables):
    c=sum(int(a)*int(v) for a,v in zip(weights,initial_state))
    lhs=sum((int(v)*x for v,x in zip(weights,variables)),z3.IntVal(0))
    return lhs==c,c

def candidates_form(original,native,weights,initial_state,bounds):
    relation,c=source_only_equality(weights,initial_state,original["now"])
    candidate=z3.And(relation,*bounds,native["post"])
    return candidate,relation,c

def actual_certificate(path,formula):
    start=time.perf_counter_ns()
    verdict=check_original_candidate(path,formula,expected_source_sha256=
        sha(path.read_bytes()))
    elapsed=(time.perf_counter_ns()-start)/1e6
    return {"status":verdict["status"],
        "native_original_three_vc":verdict.get("native_original_three_vc"),
        "cvc5_original_three_vc":verdict.get("cvc5_original_three_vc"),
        "checker_wall_ms":round(elapsed,3),
        "original_source_bound":verdict["original_source_bound"],
        "accepted":verdict["status"]=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5"}

def first_actual_source(path):
    data=path.read_bytes()
    parsed=sexprs(data)
    original=extract_mixed_original(parsed)
    native=native_original_relations(parsed,original)
    native.update({"now":original["now"],"next":original["next"]})
    parity=check_parity(original,native)
    if len(parity)!=3 or any(x!="unsat" for x in parity.values()):
        raise RuntimeError("SOURCE_CUSTOM_NATIVE_SEMANTICS_MISMATCH")
    if check_formula(native["pre"])!="sat":
        raise RuntimeError("PRE_NOT_SAT")
    n=len(original["now"])
    pre,trans,rows=source_samples(original,native)
    gradients=learned_gradient_coefficients(rows,n)
    learned_ints=primitive_integer_coefficients(gradients["trained_weights"])
    untrained_ints=primitive_integer_coefficients(gradients["initial_weights"])
    classical_ints,classical_ms,nullity=exact_classical_nullspace(rows,n)
    nonnegative=source_nonnegative_bounds(original,native)
    def check_ints(ints):
        if ints is None:return {"accepted":False,"status":"NO_UNIQUE_EXACT_NULLSPACE"}
        formula,relation,c=candidates_form(original,native,ints,pre[0],nonnegative)
        receipt=actual_certificate(path,formula.sexpr())
        receipt.update({
            "source_only_integer_coefficients":ints,
            "source_relation_constant":c,
            "source_relation_sexpr":relation.sexpr(),
            "final_source_inductive_invariant_sha256":sha(formula.sexpr().encode()),
            "post_used_only_after_coefficients_frozen":True,
        })
        return receipt
    positive=check_ints(learned_ints)
    negative=check_ints(untrained_ints)
    strongest=check_ints(classical_ints)
    post_only=source_proof(native["post"],native)
    # Distinguish original Post alone from a newly discovered relation.
    return {
      "official_source":str(path.name),"original_source_sha256":sha(data),
      "source_state_dimension":n,
      "public_pre_sample_count":len(pre),
      "public_transition_pair_count":len(trans),
      "source_only_constraints_count":len(rows),
      "sampled_constraint_rows_sha256":sha(canonical(rows).encode()),
      "independent_native_custom_source_parser_parity":parity,
      "neural_gradient_training":gradients,
      "source_only_positive_bounds_count":len(nonnegative),
      "learned_original":positive,
      "untrained_seeded_control":negative,
      "strong_exact_classical_nullspace":strongest,
      "strong_exact_classical_nullspace_wall_ms":classical_ms,
      "strong_classical_nullspace_dimension":nullity,
      "post_only_original_3vc":post_only["vcs"],
      "post_only_accepted":post_only["accepted"],
    }

def run(root):
    rows=[first_actual_source(root/SOURCE_DIR/p) for p in TARGETS]
    byname={r["official_source"]:r for r in rows}
    novel=byname["cggmp2005_variant_true-unreach-call_true-termination.sl"]
    checks={
     "exact_two_opened_official_originals":len(rows)==2,
     "both_original_source_parity_three_unsat":all(
        all(v=="unsat" for v in r[
           "independent_native_custom_source_parser_parity"].values()) for r in rows),
     "actual_gradient_trained_nonzero_and_loss_decreased":all(
        r["neural_gradient_training"]["trainable_parameter_count"]>=2
        and r["neural_gradient_training"]["iterations"]==STEPS
        and r["neural_gradient_training"]["final_loss"]<
           r["neural_gradient_training"]["initial_loss"] for r in rows),
     "both_trained_source_invariants_original_3vc_cvc5_certified":all(
        r["learned_original"]["accepted"] for r in rows),
     "formerly_spacer_only_real_source_now_has_explicit_inductive_invariant":
        novel["learned_original"]["accepted"],
     "post_alone_not_inductive_for_both":all(
        not r["post_only_accepted"] for r in rows),
     "at_least_one_untrained_first_source_not_3vc":any(
        not r["untrained_seeded_control"]["accepted"] for r in rows),
     "strong_full_classical_baseline_measured_and_recorded":all(
        r["strong_exact_classical_nullspace"]["accepted"] for r in rows),
    }
    return {
        "schema":SCHEMA,"preregistered_issue":273,
        "official_repository":"SyGuS-Org/benchmarks",
        "upstream_commit":"13c8deb68a873635879c9a69bc78caebd340f646",
        "sources_already_opened":True,"new_unseen_authored_families":0,
        "training_method":"SOURCE_LOCAL_UNSUPERVISED_ONE_LINEAR_NEURON_PROJECTED_GRADIENT",
        "train_labels_supplied":0,
        "source_post_used_by_learned_gradient":False,
        "source_post_used_only_for_final_invariant_strengthening_and_checker":True,
        "historical_variant_first_status":"SOURCE_ONLY_SPACER_UNSAT_WITHOUT_INDUCTIVE_INVARIANT",
        "first_real_original_learned_gate_pass":all(checks.values()),
        "frozen_gate_checks":checks,
        "real_original_receipts":rows,
        "full_classical_unique_neural_capability":False,
        "no_claim_of_pretrained_generalizing_model":True,
        "cpu_solver_and_neural_costs_recorded":True,
        "energy_and_real_dollar_cost":"UNKNOWN",
        "gemma_model_calls":0,"frontier_model_calls":0,"gpu_calls":0,
        "Q3_global":"OPEN","global_Q1_Q7":"OPEN",
        "sealed_original_D3":"BLOCKED",
        "historical_AM1":"FAIL_UNCHANGED",
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    result=run(a.source_root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    for r in result["real_original_receipts"]:
        print("REAL_SYGUS_SELF_SUPERVISED",r["official_source"],
            "learned",r["learned_original"]["accepted"],
            "random",r["untrained_seeded_control"]["accepted"],
            "full_classical",r["strong_exact_classical_nullspace"]["accepted"],
            "n_params",r["neural_gradient_training"]["trainable_parameter_count"])
    print("FIRST_OFFICIAL_UNSUPERVISED_NEURAL_GATE",
          result["first_real_original_learned_gate_pass"])
    print("GATE_CHECKS",json.dumps(result["frozen_gate_checks"],sort_keys=True))
    print("GLOBAL_Q1_Q7",result["global_Q1_Q7"])

if __name__=="__main__":main()
