"""G0: Exact integer-polynomial Newton lifting proofs on one OPENED DEV cohort.

PRE-REGISTERED GitHub issue #222, before running this new solver.
ALL source files are same fixed 27 Hoenicke originals from failed Issue #221.
No neural, no gold hints, no tuning by output, no claim of blind generalization.
Sound certificate: exact ZZ-polynomial quotient plus necessary source premises.
"""
import collections
import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path

import sympy as sp
import z3

SOURCE_COMMIT="7f993a017850ba547c6ea19a1bf3b54adf54a449"
SOURCE_FAMILY="20230328-sqrtmodinv-hoenicke"
BASE=(f"https://raw.githubusercontent.com/SMT-LIB/benchmark-submission-2023/{SOURCE_COMMIT}/"
      f"non-incremental/QF_NIA/{SOURCE_FAMILY}/")
NAMES=("modInv128.smt2","modInv16.smt2","modInv32.smt2","modInv64.smt2",
"modInv8.smt2","modInvFull.smt2","modInvInitial.smt2","modInvStep.smt2",
"modInvStepSimplified.smt2","modInvVar1.smt2","modSimpleTest.smt2",
"sqrtStep1.smt2","sqrtStep1a.smt2","sqrtStep2.smt2","sqrtStep2a.smt2",
"sqrtStep3.smt2","sqrtStep3a.smt2","sqrtStep4.smt2","sqrtStep4a.smt2",
"sqrtStep5.smt2","sqrtStep5a.smt2","sqrtStep6.smt2","sqrtStep6a.smt2",
"sqrtStep7.smt2","sqrtStep7a.smt2","sqrtStepFinal.smt2","sqrtStepFinala.smt2")
OUT=Path("/tmp/g0_hoenicke27_newton_integer_first.json")
WORK=Path("/tmp/g0_hoenicke_newton_originals")
WORK.mkdir(parents=True,exist_ok=True)
MAX_SYMBOLS=12
MAX_POLY_TERMS=300
MAX_AST_NODES=240

def fetch(name):
    path=WORK/name
    req=urllib.request.Request(BASE+name,headers={"User-Agent":"NEUMANN-exact-G0-Newton-proof"})
    with urllib.request.urlopen(req,timeout=40) as response,path.open("wb") as dst:
        import shutil
        shutil.copyfileobj(response,dst)
    raw=path.read_bytes()
    if not (150<len(raw)<2_000_000):raise ValueError("ORIGINAL_SOURCE_INVALID_SIZE")
    return path,raw

def necessary(expr):
    if z3.is_and(expr):
        for part in expr.children():
            yield from necessary(part)
    else:
        yield expr

def source_var(expr):
    if z3.is_const(expr) and expr.num_args()==0 and expr.decl().kind()==z3.Z3_OP_UNINTERPRETED and z3.is_int(expr):
        return sp.Symbol(expr.decl().name(),integer=True)
    return None

def to_poly(expr,depth=0):
    if depth>MAX_AST_NODES:raise ValueError("TOO_DEEP_POLYNOMIAL")
    if z3.is_int_value(expr):return sp.Integer(expr.as_long())
    val=source_var(expr)
    if val is not None:return val
    op=expr.decl().kind()
    args=[to_poly(c,depth+1) for c in expr.children()]
    if op==z3.Z3_OP_ADD:return sp.Add(*args,evaluate=False)
    if op==z3.Z3_OP_MUL:return sp.Mul(*args,evaluate=False)
    if op==z3.Z3_OP_SUB:
        if len(args)<1:raise ValueError("EMPTY_SUB")
        return args[0]-sum(args[1:])
    if op==z3.Z3_OP_UMINUS:return -args[0]
    raise ValueError("NON_INTEGRAL_POLYNOMIAL_OPERATION_"+str(op))

def canonical_poly(expr):
    x=sp.expand(expr)
    symbols=sorted(x.free_symbols,key=lambda v:v.name)
    if len(symbols)>MAX_SYMBOLS:raise ValueError("SYMBOL_LIMIT")
    if not symbols:
        if not isinstance(x,sp.Integer):raise ValueError("NON_INTEGER_CONSTANT")
        return x
    p=sp.Poly(x,*symbols,domain=sp.ZZ)
    if len(p.terms())>MAX_POLY_TERMS:raise ValueError("POLYNOMIAL_TERMS_LIMIT")
    return x

def exact_integer_divide(numerator,denominator):
    num=canonical_poly(numerator)
    den=canonical_poly(denominator)
    if den==0:return None
    syms=sorted(num.free_symbols|den.free_symbols,key=lambda v:v.name)
    if len(syms)>MAX_SYMBOLS:return None
    try:
        if not syms:
            if int(num)%int(den):return None
            quot=sp.Integer(int(num)//int(den))
        else:
            quot,rem=sp.div(num,den,*syms,domain=sp.ZZ)
            if rem!=0:return None
        if sp.expand(num-den*quot)!=0:return None
        return canonical_poly(quot)
    except (sp.PolynomialError,sp.CoercionFailed,ValueError,TypeError,ZeroDivisionError):
        return None

def is_integer_one(x):
    return z3.is_int_value(x) and x.as_long()==1

def mod_eq_one(expr):
    if not z3.is_eq(expr):return None
    a,b=expr.children()
    mod=b if is_integer_one(a) and b.decl().kind()==z3.Z3_OP_MOD else (
        a if is_integer_one(b) and a.decl().kind()==z3.Z3_OP_MOD else None)
    if mod is None:return None
    return mod.arg(0),mod.arg(1)

def has_gt_one_guard(clauses,variable):
    for a in clauses:
        if z3.is_gt(a):
            lhs,rhs=a.children()
            if source_var(lhs)==variable and is_integer_one(rhs):
                return True
    return False

def possible_modulus_root(modulus,atoms):
    """Source s>1 is required for s or s^2, no unstated positivity."""
    for a in atoms:
        if z3.is_gt(a):
            lhs,rhs=a.children()
            sym=source_var(lhs)
            if sym is None or not is_integer_one(rhs):continue
            if modulus==sym or sp.expand(modulus-sym**2)==0:
                return sym, (1 if modulus==sym else 2)
    return None,None

def source_definitions(atoms):
    defs={}
    for a in atoms:
        if not z3.is_eq(a):continue
        lhs,rhs=a.children()
        for var,term in ((lhs,rhs),(rhs,lhs)):
            symbol=source_var(var)
            if symbol is None or symbol in defs:continue
            try:expr=canonical_poly(to_poly(term))
            except ValueError:continue
            if symbol in expr.free_symbols:continue
            defs[symbol]=expr
            break
    return defs

def eliminate(expr,defs):
    out=canonical_poly(expr)
    for _ in range(min(10,len(defs)+1)):
        nxt=out.xreplace(defs)
        if nxt==out:break
        out=canonical_poly(nxt)
    return canonical_poly(out)

def original_required_negative_mod_one(atom):
    if not z3.is_not(atom):return None
    return mod_eq_one(atom.arg(0))

def poly_predecessors(atoms, base):
    candidates=[]
    for a in atoms:
        me=mod_eq_one(a)
        if me is not None:
            lhs,mod=me
            try:
                if canonical_poly(to_poly(mod))==base:
                    x=canonical_poly(to_poly(lhs))
                    candidates.append(("source_mod_eq_1",x,"original required modular equality"))
            except ValueError:pass
        if z3.is_eq(a):
            lhs,rhs=a.children()
            try:
                x=canonical_poly(to_poly(lhs))
                y=canonical_poly(to_poly(rhs))
            except ValueError:continue
            for c,d in ((x,y),(y,x)):
                q=exact_integer_divide(d-1,base)
                if q is not None and c-1!=0:
                    candidates.append(("source_integer_equality",c,str(q)))
    return candidates

def prove_one_original(path):
    s=z3.Solver()
    s.from_file(str(path))
    atoms=[a for assertion in s.assertions() for a in necessary(assertion)]
    defs=source_definitions(atoms)
    eligible=0
    unsupported=0
    for atom in atoms:
        target=original_required_negative_mod_one(atom)
        if target is None:continue
        eligible+=1
        E,M=target
        try:
            target_numer=canonical_poly(to_poly(E))
            target_mod=canonical_poly(to_poly(M))
            base,power=possible_modulus_root(target_mod,atoms)
            if base is None:continue
            reduced=eliminate(target_numer,defs)
            # Exact target-polynomial-rewriting equality, when original contains
            # E=R or R=E as a necessary formula, no division.
            for eq in atoms:
                if not z3.is_eq(eq):continue
                try:
                    lhs=canonical_poly(to_poly(eq.arg(0)))
                    rhs=canonical_poly(to_poly(eq.arg(1)))
                except ValueError:continue
                if sp.expand(lhs-target_numer)==0:
                    reduced=eliminate(rhs,defs);break
                if sp.expand(rhs-target_numer)==0:
                    reduced=eliminate(lhs,defs);break
            delta=canonical_poly(reduced-1)
            quotient=exact_integer_divide(delta,target_mod)
            if quotient is not None:
                theorem={"method":"direct_integer_polynomial_quotient",
                         "target_numerator_after_source_definitions":str(reduced),
                         "target_modulus":str(target_mod),
                         "source_guard":"s>1 with s or s^2",
                         "integer_quotient":str(quotient),
                         "verified_polynomial_identity":"E-1=M*Q"}
            else:
                theorem=None
                if power==2:
                    for precursor_type,X,detail in poly_predecessors(atoms,base):
                        term=canonical_poly((X-1)**2)
                        q=exact_integer_divide(delta,term)
                        if q is None:continue
                        theorem={"method":"newton_squared_error_ideal_certificate",
                                "target_numerator_after_source_definitions":str(reduced),
                                "target_modulus":str(target_mod),
                                "source_guard":"s>1 with M=s^2",
                                "precursor_source":precursor_type,
                                "precursor_original_expression":str(X),
                                "precursor_equality_or_mod":detail,
                                "integer_quotient":str(q),
                                "verified_polynomial_identity":"E-1=(X-1)^2*Q"}
                        break
            if theorem is None:continue
            # Independent original SMT reader retains all source assertions.
            original=z3.Solver()
            original.from_file(str(path))
            original.add(E % M == 1)
            original.set(timeout=3000)
            independently=original.check()
            if independently!=z3.unsat:
                raise RuntimeError("FULL_ORIGINAL_NOT_REFUTED_AFTER_VERIFIED_LEMMA:"+str(independently))
            theorem.update(status="ORIGINAL_UNSAT_CERTIFIED",
                           original_assertions=len(s.assertions()),
                           source_required_atom_count=len(atoms),
                           target_negative_mod_conjunct_source=atom.sexpr(),
                           independent_original_plus_proven_lemma="unsat",
                           no_source_assertion_removed=True,
                           certificate_origin="sparse_exact_integer_polynomial_certificate")
            return theorem
        except (ValueError,sp.PolynomialError,TypeError,z3.Z3Exception):
            unsupported+=1
            continue
    return {"status":"NO_SOUND_INTEGER_POLYNOMIAL_CERTIFICATE",
            "source_assertions":len(s.assertions()),
            "required_atoms":len(atoms),
            "eligible_negative_mod_eq1_targets":eligible,
            "unsupported_atoms":unsupported}

def main():
    begin=time.perf_counter()
    receipt={"status":"FIRST_RUN_INCOMPLETE","prereg_issue":222,
             "original_repo":"SMT-LIB/benchmark-submission-2023",
             "original_source_sha":SOURCE_COMMIT,"family":SOURCE_FAMILY,
             "frozen_count":27,"source_opened_development_only":True,
             "mechanism":"exact integer polynomial quotient and squared-error Newton lift",
             "no_neural_training_or_inference":True,
             "no_paid_calls_or_gpu":True,
             "no_source_specific_tuning":True,
             "G0_full":"OPEN","G1":"HOLD_LEARNING","G2":"BLOCKED",
             "Q1_to_Q7_global":"OPEN","files":[]}
    def save():OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    save()
    try:
        for name in NAMES:
            original,raw=fetch(name)
            text=raw.decode("utf-8")
            if "(set-logic QF_NIA)" not in text:
                raise RuntimeError("ORIGINAL_LOGIC_CHANGED:"+name)
            if '(set-info :license "https://creativecommons.org/licenses/by/4.0/")' not in text:
                raise RuntimeError("ORIGINAL_LICENSE_CHANGED:"+name)
            started=time.perf_counter()
            proof=prove_one_original(original)
            proof.update(name=name,source_sha256=hashlib.sha256(raw).hexdigest(),
                         bytes=len(raw),
                         wall_seconds_proof_original_checker=round(time.perf_counter()-started,6))
            receipt["files"].append(proof)
            save()
        if len(receipt["files"])!=27:raise RuntimeError("FROZEN_COHORT_INCOMPLETE")
        counts=dict(collections.Counter(row["status"] for row in receipt["files"]))
        receipt["status"]="EXACT_INTEGER_NEWTON_OPENED_DEV_27_COMPLETED"
        receipt["source_verified_unsat_count"]=counts.get("ORIGINAL_UNSAT_CERTIFIED",0)
        receipt["method_counts"]=dict(collections.Counter(
            row.get("method","NO_PROOF") for row in receipt["files"]))
        receipt["total_wall_seconds_including_download"]=round(time.perf_counter()-begin,3)
        receipt["G0_economic_headroom"]="NOT_ESTABLISHED_VS_STRONG_SPECIALISTS"
        save()
        print("G0_NEWTON_INTEGER_PROOF_FIRST",json.dumps({
            "status":receipt["status"],"correct_originals":receipt["source_verified_unsat_count"],
            "methods":receipt["method_counts"],
            "wall_all":receipt["total_wall_seconds_including_download"]}),flush=True)
    except Exception as exc:
        receipt["status"]="FIRST_NEWTON_PROOF_BLOCKED"
        receipt["first_failure"]=type(exc).__name__+": "+str(exc)[:320]
        receipt["total_wall_seconds_including_download"]=round(time.perf_counter()-begin,3)
        save()
        print("G0_NEWTON_FIRST_FAILURE",receipt["first_failure"],flush=True)
        raise

if __name__=="__main__":main()
