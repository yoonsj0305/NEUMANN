"""Deliberately adversarial synthetic source semantics controls for PR354.

This test suite does NOT add authentic public original achievements.
For every input, check the exact source-original concrete integer model when
SAT, or validate the mathematically proved source contradiction with
independent Z3/cvc5 QF_LIA when UNSAT. Exercise missing crucial source
assumptions, different literal/symbolic targets and mixed exponents.

A false positive is a hard failure; ABSTAIN is expected, not evidence
of low Q3 source capability on the 10 genuine original programs.
"""
from __future__ import annotations
import json
import z3
from research.evidence.q3_power_feature_20261021.first_ten_unchanged_power_magic_original_unbounded_unsat import (
    original_exact_geometry,independent_necessary_linear_certificate,
    theorem_positive_injectivity_controls
)

def powterm(x,k):
    if k==1:return x
    result=x
    for i in range(1,k):result=result*x
    return result

def run_case(label,assertions,expected_unsat,assignment=None):
    a=z3.Solver()
    a.add(*assertions)
    if assignment is not None:
        assert not expected_unsat
        # Mathematical concrete SAT witness of EVERY original assertion.
        binds=tuple((k,z3.IntVal(v)) for k,v in assignment.items())
        for q in a.assertions():
            got=z3.simplify(z3.substitute(q,*binds))
            assert z3.is_true(got),(label,q,got)
    proof=original_exact_geometry(list(a.assertions()))
    if expected_unsat:
        assert proof is not None,(label,"MISSING_SOUND_STRUCTURE")
        abstract=independent_necessary_linear_certificate(proof)
        assert abstract["both_independent_unbounded_necessary_condition_UNSAT"],(label,abstract)
    else:
        assert proof is None,(label,"FALSE_ORIGINAL_SOURCE_UNSAT",proof)
    print("Q3_POWER_NEGATIVE_SOURCE_CONTROL",label,
          "DETECTED",proof is not None,
          "SHOULD_UNSAT",expected_unsat,flush=True)
    return bool(proof)

def main():
    a,b,c,t,u=z3.Ints("a b c t u")
    cases=[]
    for k in range(1,9):
        s=[powterm(a,k)+powterm(b,k)==t,
           powterm(a,k)+powterm(c,k)==t,
           b!=c,b>0,c>0]
        cases.append(("PROVE_POSITIVE_DISTINCT_POWER_"+str(k),s,True,None))
        vals={a:1,b:2,c:2,t:1+2**k}
        s=[powterm(a,k)+powterm(b,k)==t,
           powterm(a,k)+powterm(c,k)==t,b>0,c>0]
        cases.append(("ABSTAIN_SOURCE_MISSING_DISTINCT_"+str(k),s,False,vals))
        vals={a:1,b:2,c:3,t:1+2**k,u:1+3**k}
        s=[powterm(a,k)+powterm(b,k)==t,
           powterm(a,k)+powterm(c,k)==u,b!=c,b>0,c>0]
        cases.append(("ABSTAIN_SOURCE_DIFFERENT_SUM_TARGET_"+str(k),s,False,vals))
        vals={a:1,b:2,c:3,t:1+2**k}
        s=[powterm(a,k)+powterm(b,k)==t,b!=c,b>0,c>0]
        cases.append(("ABSTAIN_SOURCE_MISSING_SECOND_EQUALITY_"+str(k),s,False,vals))
        if k%2==0:
            vals={a:1,b:-2,c:2,t:1+2**k}
            s=[powterm(a,k)+powterm(b,k)==t,
               powterm(a,k)+powterm(c,k)==t,b!=c,c>0]
            cases.append(("ABSTAIN_NEGATIVE_BASE_WITH_EVEN_POWER_"+str(k),s,False,vals))
        if k<=7:
            # y^(k+1) == z^k has positive DISTINCT witness if y=2^k,z=2^(k+1).
            y=2**k;z=2**(k+1)
            vals={a:1,b:y,c:z,t:1+y**(k+1)}
            s=[powterm(a,k)+powterm(b,k+1)==t,
               powterm(a,k)+powterm(c,k)==t,b!=c,b>0,c>0]
            cases.append(("ABSTAIN_DIFFERENT_DEGREES_EQUAL_VALUE_"+str(k),s,False,vals))
    positives=sum(run_case(label,assertions,should,vals)
                  for label,assertions,should,vals in cases)
    total=len(cases)
    expected=8+8+8+8+4+7
    assert total==expected==43
    assert positives==8
    math=theorem_positive_injectivity_controls()
    assert len(math)==8 and all(x["distinct_positive_pairs_validated"]==32*31 for x in math)
    print("Q3_POWER_MAGIC_ADVERSARIAL_TRUE_SOURCE_CONTROLS",total,"/43",
          "SOUND_FULL_UNBOUNDED_UNSAT",positives,
          "SOUND_SAT_NON_PROOFS",total-positives)
if __name__=="__main__":
    main()
