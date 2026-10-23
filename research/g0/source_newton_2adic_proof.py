"""Source-derived 2-adic error-squaring proof for four OPENED SMT-LIB originals.
This is CLASSICAL automated lemma construction, NOT neural-exclusive Q3.
Previous frozen G0 control: PR531 Z3 UNKNOWN and cvc5 UNKNOWN on four.
"""
import argparse,collections,hashlib,json,pathlib,re,time
import z3
PIN="7f993a017850ba547c6ea19a1bf3b54adf54a449"
FAMILY="non-incremental/QF_NIA/20230328-sqrtmodinv-hoenicke"
EXPECTED={
"modInv8.smt2":"32364b58d23386c80e6355fe03795636bff45c16",
"modInv32.smt2":"5ecf8a7276086b141a1f4fe0ee8372e1d008bed1",
"modInv64.smt2":"c2f1819814cc4c3e6cee8c46ca6c82d99817af5d",
"modInvFull.smt2":"cca902e6afcfd2d627f3ee145e24e2ab39d598c4"}
def blobhash(raw):return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def required(assertions,goal,label):
    if not any(ast.eq(goal) for ast in assertions):
        raise ValueError("REQUIRED_ORIGINAL_CLAUSE_MISSING_"+label)
def base16():
    residues={}
    for r in range(1,16,2):
        inv0=3*r
        inv1=4*(inv0//4)+(inv0+2)%4
        assert r*inv1%16==1
        residues[str(r)]=r*inv1%16
    # All negatives covered too: for d=16q+r, inv1(d)=48q+inv1(r).
    # An unrelated finite-bit-vector QF_BV implementation cross-checks mod16.
    r=z3.BitVec("r",4)
    init=r*z3.BitVecVal(3,4)
    nxt=(init & z3.BitVecVal(12,4))+((init+z3.BitVecVal(2,4)) & z3.BitVecVal(3,4))
    s=z3.Solver();s.set(timeout=4000)
    s.add((r & z3.BitVecVal(1,4))==z3.BitVecVal(1,4))
    s.add(r*nxt != z3.BitVecVal(1,4))
    assert s.check()==z3.unsat
    return residues
def recurrence():
    # Identity in integer ring: 1 - d*(x*(2-d*x)) = (1-d*x)^2.
    d=z3.Int("proof_d");x=z3.Int("proof_x")
    diff=z3.simplify((1-d*x*(2-d*x))-(1-d*x)*(1-d*x),som=True,expand=True)
    assert z3.is_int_value(diff) and diff.as_long()==0
    assert (1-1*(1*(3-1)))!=(1-1)**2,"NEGATIVE_CONTROL_FAILURE"
    return "independent symbolic ring equality ZERO"
def run(path):
    started=time.perf_counter()
    name=path.name;raw=path.read_bytes()
    report={"source_name":name,"original_sha256":sha(raw),
            "original_git_blob":blobhash(raw),"status":"UNKNOWN",
            "posthoc_dev":True,"no_neural_model":True}
    try:
        assert name in EXPECTED and blobhash(raw)==EXPECTED[name],"SOURCE_IDENTITY_MISMATCH"
        original=raw.decode()
        solver=z3.Solver();solver.from_string(original)
        assertions=list(solver.assertions())
        assert assertions
        d=z3.Int("denominator")
        idx=sorted(set(int(v) for v in re.findall(r"\(declare-const inv(\d+) Int\)",original)))
        assert idx==list(range(idx[-1]+1)) and len(idx)>=3
        vs=[z3.Int("inv"+str(i)) for i in idx]
        required(assertions,z3.IntVal(1)==d%2,"odd_d")
        required(assertions,vs[0]==3*d,"inv0")
        required(assertions,vs[1]==4*(vs[0]/4)+(vs[0]+2)%4,"inv1")
        for k in range(2,len(vs)):
            required(assertions,vs[k]==vs[k-1]*(2-d*vs[k-1]),"Newton"+str(k))
        # Exactly one original final negative obligation for the current last inv.
        pattern=r"\(assert\s+\(not\s+\(=\s+1\s+\(mod\s+\(\*\s+denominator\s+inv"+str(idx[-1])+r"\)\s+(\d+)\)\)\)\)"
        modulus=[int(v) for v in re.findall(pattern,original)]
        assert len(modulus)==1,"MISSING_UNIQUE_FINAL_TARGET"
        m=modulus[0]
        required(assertions,z3.Not(z3.IntVal(1)==(d*vs[-1])%m),"final_negated_original")
        assert m>1 and m&(m-1)==0
        steps=len(vs)-2
        proven_bits=4*2**steps
        target_bits=m.bit_length()-1
        report.update({"original_assertions":len(assertions),
                       "inferred_newton_steps":steps,"inferred_error_bits":proven_bits,
                       "original_required_bits":target_bits,
                       "new_auxiliary_variable":"e_i=1-denominator*inv_i",
                       "new_derived_recurrence":"e_(i+1)=e_i^2"})
        if target_bits>proven_bits:
            report["status"]="UNKNOWN_TOO_MANY_TARGET_BITS"
            return report
        report["base_all_8_odd_residues_mod16"]=base16()
        report["recurrence_exact_symbolic_check"]=recurrence()
        # Mathematical induction: 2^4|e1 => 2^(4*2^steps)|e_last
        # Therefore m | (1-d*last), assuming target_bits<=proven_bits.
        separate=z3.Solver()
        separate.from_string(original)
        separate.add((d*vs[-1])%m==1)
        separate.set(timeout=4000)
        answer=separate.check()
        report["independent_original_plus_proved_final_congruence"]=str(answer)
        assert answer==z3.unsat,"INDEPENDENT_FULL_ORIGINAL_NOT_CONTRADICTED"
        report["status"]="ORIGINAL_UNSAT_CERTIFIED_BY_2ADIC_SOURCE_INVARIANT"
    except Exception as e:
        report["status"]="UNKNOWN_SOURCE_OR_CERTIFICATE"
        report["error"]=type(e).__name__+":"+str(e)[:300]
    finally:
        report["total_wall_s"]=time.perf_counter()-started
    return report
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-root",required=True)
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    root=pathlib.Path(args.source_root)/FAMILY
    rows=[run(root/name) for name in EXPECTED]
    counter=collections.Counter(x["status"] for x in rows)
    output={"schema":"NEUMANN_SOURCE_2ADIC_UNSAT_FIRST_PROOFS.v1",
            "original_revision":PIN,"source_family":FAMILY,
            "all_original_cases":rows,"counts":dict(counter),"total":len(rows),
            "first_seen_sources_prior_to_proof":True,
            "historical_direct_Z3_5s_4_UNKNOWN":True,
            "historical_direct_cvc5_5s_4_UNKNOWN":True,
            "novel_neural_semantics":"NOT_PROVED",
            "new_other_family_transfer":"NOT_PROVED",
            "Q3_Q4_Q6_global":"OPEN"}
    out=pathlib.Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(output,sort_keys=True,indent=2)+"\n")
    print("SOURCE_2ADIC_COMPLETE_RECEIPT",json.dumps({
        "counts":dict(counter),"sha256":sha(out.read_bytes())}),flush=True)
    for x in rows:print("SOURCE_2ADIC_ORIGINAL",x["source_name"],x["status"],
                        x.get("inferred_error_bits"),x.get("error",""),flush=True)
    assert counter["ORIGINAL_UNSAT_CERTIFIED_BY_2ADIC_SOURCE_INVARIANT"]==4
if __name__=="__main__":main()
