"""Source-program independent metamorphic tests for sound modular abstraction.

Synthetic controls are NOT new public original source achievements.
Intent: falsify bad abstraction/unsupported source-constraint handling,
prove mathematical soundness of re-framing, especially that SAT source
cannot ever be marked UNSAT by the compiler (for these controls).
"""
from __future__ import annotations
import random,time
import z3
from research.evidence.q3_cross_prefix_modulo_20261021.first16_general_polynomial_modulus_overapprox_vs_direct import (
    MODULI,build_sound_finite,source_equations,math_discover_true_original_unsat
)

def cert(source,tag,should_refute):
    equations,dropped,_=source_equations(source.assertions())
    result=math_discover_true_original_unsat(source)
    actual=result["real_original_unbounded_unsat_proved"]
    assert actual==should_refute,(tag,should_refute,result)
    assert bool(result.get("first_discovered_sound_proof_modulus"))==should_refute
    if should_refute:
        m=result["first_discovered_sound_proof_modulus"]
        assert m in MODULI
        assert any(
          x["modulus"]==m and x["abstract_Z3"]=="UNSAT" and
          x["independent_original_math_cvc5"]["cvc5_original_math_status"]=="UNSAT"
          for x in result["searched_moduli"])
    print("GENERIC_MODULAR_METAMORPHIC",tag,
          "GOT",actual,"EXPECTED",should_refute,
          "SELECTED_MOD",result.get("first_discovered_sound_proof_modulus"),
          "DROPPED",dropped,flush=True)
    return result

def test():
    x,y,z=z3.Ints("mt_x mt_y mt_z")
    cases=[]
    s=z3.Solver();s.add(x*x==2)
    assert {a*a%3 for a in range(3)}=={0,1}
    cases.append(("UNSAT_TRUE_INT_SQUARE_ROOT_TWO",s,True))
    s=z3.Solver();s.add(x*x+y*y==3)
    assert {(a*a+b*b)%4 for a in range(4) for b in range(4)}=={0,1,2}
    cases.append(("UNSAT_SUM_TWO_SQUARES_EQ3",s,True))
    s=z3.Solver();s.add(x*x*x+y*y*y+z*z*z==4)
    assert 4 not in {((a**3+b**3+c**3)%9)
                       for a in range(9) for b in range(9) for c in range(9)}
    cases.append(("UNSAT_SUM_THREE_CUBES_EQ4",s,True))
    s=z3.Solver();s.add(x*x*x+y*y*y+z*z*z==5)
    cases.append(("UNSAT_SUM_THREE_CUBES_EQ5",s,True))
    s=z3.Solver();s.add(x==0,x>1)
    cases.append(("ABSTAIN_BUT_SOURCE_UNSAT_NEEDS_DROPPED_INEQUALITY",s,False))
    s=z3.Solver();s.add(z3.Or(x==0,x==1))
    cases.append(("ABSTAIN_ORDISJUNCTION_ORIGINAL_SAT",s,False))
    s=z3.Solver();s.add(z3.And(x==0,z3.Not(x==0)))
    cases.append(("ABSTAIN_NEGATED_EQUALITY_SOURCE_UNSAT",s,False))
    s=z3.Solver();s.add(x*x+y*y==0)
    cases.append(("SAT_TRUE_ZERO_SQUARE_SUM",s,False))
    s=z3.Solver();s.add(x*x==1)
    cases.append(("SAT_TRUE_SQUARE_ONE",s,False))
    randomgen=random.Random(20261021)
    for i in range(40):
        a=randomgen.randint(-6,6);b=randomgen.randint(-6,6)
        p=randomgen.randint(-3,3);q=randomgen.randint(-3,3)
        # The reference assignment x=a,y=b makes EVERY original conjunct
        # mathematically true. Any certified UNSAT is therefore UNSOUND.
        rhs=a**3+b*b+p*a+q*b
        s=z3.Solver()
        s.add(x*x*x+y*y+p*x+q*y==rhs)
        s.add(z3.Or(x==a,y==b))  # positive constraint dropped as necessary
        cases.append((f"SAT_CONSTRUCTED_ORIGINAL_{i}",s,False))
    results=[cert(s,tag,good) for tag,s,good in cases]
    assert len(cases)==49
    assert sum(x["real_original_unbounded_unsat_proved"] for x in results)==4
    print("Q3_GENERAL_POLYNOMIAL_SOUNDNESS_METAMORPHIC",len(cases),"/49",
          "UNSAT_DUAL_PROVEN",4,"POSITIVE_OR_ABSTAIN_NOT_FALSE_REFUTED",45)
if __name__=="__main__":
    test()
