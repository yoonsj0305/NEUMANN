"""Development-only Q3 conditional operator-selection in a nonpolynomial source family.

A fitted categorical model chooses an operator instance "x mod m" from a
SUPPLIED vocabulary m in [2,20] from raw source transition pairs alone.
It receives neither answer m nor invariant labels in the fitting objective.
Exact source proof is independent Z3 and cvc5 triple VCs; the exact classical
GCD baseline sees the identical pairs. This is NOT a new primitive, nor
frontier superiority or real source-body first-blind transfer.
"""
from __future__ import annotations
import argparse,json,hashlib,math,subprocess,time
from pathlib import Path
import numpy as np
import sympy as sp
PRIMES=(5,7,11,13,17,19)
OPTIONS=np.arange(2,21)
def ms(t):return (time.perf_counter_ns()-t)/1e6
def learn(raw,seed,steps=250):
    rng=np.random.default_rng(seed)
    increments=np.asarray([b-a for a,b in raw],dtype=float)
    energy=np.mean((1-np.cos(2*np.pi*increments[:,None]/OPTIONS[None,:]))**2,axis=0)
    energy+=.0001*OPTIONS
    target=np.exp(-(energy-energy.min())/.0007)
    target/=target.sum()
    logits=rng.normal(size=len(OPTIONS))*.1
    untrained=int(OPTIONS[np.argmax(logits)])
    t=time.perf_counter_ns()
    for step in range(steps):
        p=np.exp(logits-logits.max());p/=p.sum()
        logits-=.4*(p-target)
    elapsed=ms(t)
    p=np.exp(logits-logits.max());p/=p.sum()
    learned=int(OPTIONS[np.argmax(logits)])
    return dict(candidate=learned,untrained_candidate=untrained,train_ms=elapsed,
                fitted_weights=logits.tolist(),fit_probs=p.tolist(),
                raw_transition_structural_losses=energy.tolist(),
                raw_energy_pseudotargets=target.tolist())
def gcd(raw):
    t=time.perf_counter_ns();val=0
    for a,b in raw:val=math.gcd(val,abs(int(b-a)))
    return val,ms(t)
def certified_source(k,m,mutate=False):
    import z3
    x,xp=z3.Ints("source_x source_x_next")
    step=k+1 if mutate else k
    inv=(x-1)%m==0
    inv_next=(xp-1)%m==0
    init=(x==1)
    trans=(xp==x+step)
    goal=(x-1)%k==0
    qs=[z3.And(init,z3.Not(inv)),
        z3.And(inv,trans,z3.Not(inv_next)),
        z3.And(inv,z3.Not(goal))]
    result=[]
    for name,q in zip(("init","consecution","goal"),qs):
        sl=z3.Solver();sl.set(timeout=3000);sl.add(q)
        a=str(sl.check())
        src=sl.to_smt2()
        try:
            proc=subprocess.run(["cvc5","--lang","smt2","--tlimit=3000"],
                   input=src,text=True,capture_output=True,timeout=6)
            entries=[s.strip() for s in proc.stdout.splitlines()
                     if s.strip() in ("sat","unsat","unknown")]
            b=entries[-1] if entries else "UNAVAILABLE"
        except Exception as e:
            b="ERROR:"+str(e)[:100]
        result.append(dict(name=name,Z3=a,cvc5=b,
                    independent_dual_unsat=(a=="unsat" and b=="unsat"),
                    independent_dual_sat=(a=="sat" and b=="sat")))
    return result
def prove_polynomial_ceiling(k):
    reachable=[1+i*k for i in range(4)]
    V=sp.Matrix([[z**i for i in range(4)] for z in reachable])
    det=V.det()
    assert det!=0
    return dict(
      degree_bound=3,actual_original_reachable_states=reachable,
      exact_vandermonde_determinant=str(det),
      zero_polynomial_only_degree_at_most_3_equality_true_on_all_four=True,
      unsafe_state_x=2,unsafe_state_violates_post=(1%k!=0),
      single_degree3_polynomial_equality_unsafe_separation_impossible=True,
      restriction="Only ONE polynomial equality invariant, not inequalities, disjunctions, or full synthesis")
def main():
    a=argparse.ArgumentParser();a.add_argument("--out",required=True)
    args=a.parse_args()
    rows=[]
    for k in PRIMES:
        for repeat in range(4):
            seed=20261022+repeat
            rng=np.random.default_rng(seed)
            raw=[(int(v),int(v+k)) for v in rng.integers(-40,41,size=50)]
            trained=learn(raw,seed)
            classic,ct=gcd(raw)
            model=certified_source(k,trained["candidate"])
            strong=certified_source(k,classic)
            broken=certified_source(k,trained["candidate"],mutate=True)
            correct=all(x["independent_dual_unsat"] for x in model)
            strong_ok=all(x["independent_dual_unsat"] for x in strong)
            wrong_mutant=broken[1]["independent_dual_sat"]
            rows.append(dict(source_original_AST={
                "Pre":"x=1","Trans":"x_next=x+"+str(k),
                "Post":"(x-1) mod "+str(k)+" = 0"},
                experiment_seed=seed,raw_source_pairs=50,
                trained_categorical_operator=trained,
                true_original_dual_source_3VC=model,
                exact_gcd_classical_candidate=classic,
                exact_gcd_classical_candidate_ms=ct,
                exact_gcd_classical_dual_source_3VC=strong,
                trained_full_source_proved=correct,
                exact_classical_full_source_proved=strong_ok,
                mutated_source_trans_k_plus_one_dual_3VC=broken,
                mutated_source_rejected_via_real_SAT=wrong_mutant,
                degree3_single_equality_impossibility=prove_polynomial_ceiling(k)))
            print("Q3_MODULAR_OPERATOR_SOURCE",k,seed,"LEARNED",
                  trained["candidate"],"GCD",classic,
                  "TRAINED_DUAL",correct,"EXACT_DUAL",strong_ok,
                  "MUTANT_REJECT",wrong_mutant,flush=True)
    n=lambda field:sum(bool(q[field]) for q in rows)
    out=dict(schema="neumann.q3.learned_modular_selector_vs_exact_gcd_native_dual_source.v1",
       scientific_scope="synthetic modulo program, nonpolynomial operator chosen FROM designer supplied dictionary",
       source_families=len(PRIMES),repeats_per_family=4,trials=len(rows),
       real_gradient_fitted_categorical_selector=True,
       learned_original_proven=n("trained_full_source_proved"),
       equal_rights_classical_exact_gcd_original_proven=n("exact_classical_full_source_proved"),
       original_mutant_independent_rejected=n("mutated_source_rejected_via_real_SAT"),
       no_fit_random_operator_hits=sum(q["trained_categorical_operator"]["untrained_candidate"]==
                  int(q["source_original_AST"]["Trans"].split("+")[-1]) for q in rows),
       total_operator_selector_fit_ms=sum(q["trained_categorical_operator"]["train_ms"] for q in rows),
       total_strong_classical_gcd_ms=sum(q["exact_gcd_classical_candidate_ms"] for q in rows),
       fixed_polynomial_degree3_single_equality_provably_insufficient=True,
       supplied_mod_operator_IS_NOT_NEW_PRIMITIVE=True,
       strong_classical_gcd_candidate_equal_rights=True,
       end_to_end_10x_classical_superiority_unproven=True,
       external_unseen_real_source_generalization_unproven=True,
       global_Q3="OPEN",global_Q4="OPEN",global_Q6="OPEN",
       original_source_lemmas_and_all_receipts=rows)
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    for key in ("learned_original_proven","equal_rights_classical_exact_gcd_original_proven",
                "original_mutant_independent_rejected","no_fit_random_operator_hits",
                "total_operator_selector_fit_ms","total_strong_classical_gcd_ms"):
        print("Q3_ACTUAL_NEW_OPERATOR_FAMILY_SELECTION",key,out[key],flush=True)
    print("SHA256_RESULTS",hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)
    assert out["learned_original_proven"]==out["equal_rights_classical_exact_gcd_original_proven"]==out["original_mutant_independent_rejected"]==24
if __name__=="__main__":main()
