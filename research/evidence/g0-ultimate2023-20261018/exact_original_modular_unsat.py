"""Exact original 2023 UltimateAutomizer: constructive QF_NIA UNSAT certificates.

DEVELOPMENT-ONLY after source opened; prereg issue #220 comment 6248280801.
This method discovers source-required NOT(mod(integer-polynomial,m)==0),
then independently proves m | polynomial for EVERY integer using finite residues.
The proof is complete because P(y+m) = P(y) (mod m) for integer polynomials.
No labels, neural model, hand-provided lemma, external search, G1 or Q7.
"""
import hashlib,json,re,time,urllib.request
from collections import Counter
from pathlib import Path

import z3

SRC_SHA="7f993a017850ba547c6ea19a1bf3b54adf54a449"
BASE=f"https://raw.githubusercontent.com/SMT-LIB/benchmark-submission-2023/{SRC_SHA}/non-incremental/QF_NIA/20230321-UltimateAutomizerSvcomp2023/"
FILENAMES=("ps5-ll.c_2.smt2","ps6.c_0.smt2","ps6.c_12.smt2")
OUT=Path("/tmp/g0_ultimate3_exact_polynomial_unsat_proof.json")
MAX_MODULUS=128
MAX_POLY_DEGREE=24

def download(url,file):
    request=urllib.request.Request(url,headers={"User-Agent":"NEUMANN-G0-original-exact-mod-proof"})
    with urllib.request.urlopen(request,timeout=40) as src,file.open("wb") as dst:
        import shutil
        shutil.copyfileobj(src,dst)
    return file.read_bytes()

def lex(s):
    return re.findall(r"\|[^|]*\||\(|\)|[^\s()]+",s)

def parse_expr(words,pos=0):
    if pos>=len(words):raise ValueError("PREMATURE_END")
    w=words[pos]
    if w!="(":
        if w==")":raise ValueError("UNEXPECTED_CLOSE")
        return w,pos+1
    expr=[];pos+=1
    while pos<len(words) and words[pos]!=")":
        node,pos=parse_expr(words,pos)
        expr.append(node)
    if pos>=len(words):raise ValueError("MISSING_CLOSE")
    if not expr:raise ValueError("EMPTY_SEXPR")
    return expr,pos+1

def source_asserts(text):
    # Only actual SMT '(assert ...)' lines: cannot parse untrusted metadata prose.
    exprs=[]
    for line in text.splitlines():
        if not line.startswith("(assert "):continue
        words=lex(line)
        node,pos=parse_expr(words)
        if pos!=len(words) or node[0]!="assert" or len(node)!=2:
            raise ValueError("ORIGINAL_ASSERT_NOT_FULLY_PARSED")
        exprs.append(node[1])
    if not exprs:raise RuntimeError("ORIGINAL_ASSERT_EMPTY")
    return exprs

def required(expr):
    # Soundness: only top-level ANDs may be decomposed into required subconstraints.
    if isinstance(expr,list) and expr and expr[0]=="and":
        for child in expr[1:]:
            yield from required(child)
    else:
        yield expr

def add(a,b):
    d=dict(a)
    for exp,c in b.items():d[exp]=d.get(exp,0)+c
    return {k:v for k,v in d.items() if v}

def mul(a,b):
    d={}
    for p,u in a.items():
        for q,v in b.items():
            d[p+q]=d.get(p+q,0)+u*v
    return {k:v for k,v in d.items() if v}

def poly(node):
    """Pure syntactic polynomial parse over one or more symbols, not a solver."""
    if isinstance(node,str):
        if re.fullmatch(r"\d+",node):return {0:int(node)},set()
        if node.startswith("|") and node.endswith("|"):
            return {1:1},{node[1:-1]}
        raise ValueError("UNSUPPORTED_POLYNOMIAL_ATOM:"+node[:50])
    op=node[0]
    terms=[poly(x) for x in node[1:]]
    variables=set().union(*(v for _,v in terms))
    if len(variables)>1:raise ValueError("POLY_MULTIPLE_SOURCE_VARIABLES")
    if op=="+":
        res={}
        for c,_ in terms:res=add(res,c)
    elif op=="*":
        res={0:1}
        for c,_ in terms:res=mul(res,c)
    elif op=="-":
        res=terms[0][0].copy()
        if len(terms)==1:res={k:-v for k,v in res.items()}
        else:
            for c,_ in terms[1:]:res=add(res,{k:-v for k,v in c.items()})
    else:raise ValueError("UNSUPPORTED_POLY_OPERATOR:"+str(op))
    if any(k>MAX_POLY_DEGREE for k in res):raise ValueError("POLYNOMIAL_DEGREE_EXCEEDED")
    return res,variables

def required_negative_mod_eq_zero(expr):
    if not isinstance(expr,list) or len(expr)!=2 or expr[0]!="not":return None
    eq=expr[1]
    if not isinstance(eq,list) or len(eq)!=3 or eq[0]!="=":return None
    a,b=eq[1:]
    if a=="0":candidate=b
    elif b=="0":candidate=a
    else:return None
    if not isinstance(candidate,list) or len(candidate)!=3 or candidate[0]!="mod":
        return None
    numerator,denom=candidate[1:]
    if not isinstance(denom,str) or not re.fullmatch(r"\d+",denom):return None
    mod=int(denom)
    if not 2<=mod<=MAX_MODULUS:raise ValueError("MODULUS_OUT_OF_REGISTERED_BOUNDS")
    coeff,names=poly(numerator)
    if len(names)!=1:raise ValueError("ONE_POLYNOMIAL_VARIABLE_REQUIRED")
    return {"modulus":mod,"coefficient_by_degree":coeff,"source_var":next(iter(names)),
            "source_expr":expr}

def arithmetic_from_own_parse(node,value):
    # Independent arithmetic evaluator; no coefficient extraction or Z3 solver.
    if isinstance(node,str):
        if re.fullmatch(r"\d+",node):return int(node)
        if node.startswith("|") and node.endswith("|"):return value
        raise ValueError("UNSUPPORTED_OWN_AST")
    a=[arithmetic_from_own_parse(x,value) for x in node[1:]]
    if node[0]=="+":return sum(a)
    if node[0]=="*":
        p=1
        for x in a:p*=x
        return p
    if node[0]=="-":return -a[0] if len(a)==1 else a[0]-sum(a[1:])
    raise ValueError("UNKNOWN_AST_OPERATOR")

def demonstrate_modular_identity(candidate):
    coeff=candidate["coefficient_by_degree"];mod=candidate["modulus"]
    original_num=candidate["source_expr"][1][1][1] if candidate["source_expr"][1][1]!="0" else candidate["source_expr"][1][2][1]
    residues=[]
    for r in range(mod):
        # The two separately implemented integer arithmetic engines must agree.
        via_poly=sum(c*pow(r,degree) for degree,c in coeff.items())%mod
        via_original_ast=arithmetic_from_own_parse(original_num,r)%mod
        if via_poly!=via_original_ast:raise RuntimeError("INDEPENDENT_POLY_PARSER_MISMATCH")
        residues.append(via_poly)
    return residues

def verify_source_unsat_from_proven_identity(original_path,candidate):
    """Independent original Z3 parsing; use proved lemma to discharge original.
    Z3 is NOT asked to invent the lemma, and does NOT validate lemma truth.
    """
    s=z3.Solver();s.from_file(str(original_path))
    orig_assert_count=len(s.assertions())
    if orig_assert_count<1:raise RuntimeError("EMPTY_ORIGINAL_CONSTRAINTS")
    name=candidate["source_var"]
    x=z3.Int(name)
    p=sum(z3.IntVal(c)*x**d for d,c in candidate["coefficient_by_degree"].items())
    # Implement integer powers with multiplication, never Real power coercion.
    terms=[]
    for d,c in candidate["coefficient_by_degree"].items():
        t=z3.IntVal(1)
        for _ in range(d):t=t*x
        terms.append(z3.IntVal(c)*t)
    polynomial=z3.Sum(*terms) if terms else z3.IntVal(0)
    s.add(polynomial % candidate["modulus"]==0)
    s.set(timeout=4000)
    result=s.check()
    return {"original_assertion_count":orig_assert_count,
            "original_plus_proved_congruence_result":str(result),
            "original_plus_proved_congruence_unsat":result==z3.unsat}

def main():
    output={"status":"FIRST_SOURCE_PROOF_INCOMPLETE",
            "original_git_sha":SRC_SHA,
            "posthoc_opened_dev_only":True,
            "preregistration_issue_comment":6248280801,
            "source_family":"20230321-UltimateAutomizerSvcomp2023",
            "registered_cases":list(FILENAMES),
            "method":"source AST required conjunct plus sound finite residue integer-polynomial theorem",
            "max_modulus":MAX_MODULUS,
            "no_neural_forward_or_training":True,
            "no_oracle_parameter_benchmark":True,
            "global_q1_q7":"OPEN","g1":"HOLD_LEARNING","g2":"BLOCKED","cases":[]}
    def persist():OUT.write_text(json.dumps(output,sort_keys=True,indent=2)+"\n")
    persist()
    try:
        for filename in FILENAMES:
            p=Path("/tmp")/filename
            raw=download(BASE+filename,p)
            source=raw.decode("utf-8")
            if "(set-logic QF_NIA)" not in source or \
               '(set-info :status unknown)' not in source:
                raise RuntimeError("ORIGINAL_SOURCE_LOGIC_OR_REFERENCE_MISMATCH")
            if '(set-info :license "https://creativecommons.org/licenses/by/4.0/")' not in source:
                raise RuntimeError("SOURCE_LICENSE_MISMATCH")
            start=time.perf_counter()
            clauses=source_asserts(source)
            negative=[]
            for a in clauses:
                for required_atom in required(a):
                    candidate=required_negative_mod_eq_zero(required_atom)
                    if candidate is not None:negative.append(candidate)
            if len(negative)!=1:raise RuntimeError("EXPECTED_EXACTLY_ONE_REQUIRED_NEGATED_MOD_CLAUSE")
            candidate=negative[0]
            residues=demonstrate_modular_identity(candidate)
            if any(x!=0 for x in residues):
                raise RuntimeError("CONJECTURED_RESIDUE_THEOREM_FALSE")
            independent=verify_source_unsat_from_proven_identity(p,candidate)
            if not independent["original_plus_proved_congruence_unsat"]:
                raise RuntimeError("ORIGINAL_FORMULA_LEMMA_NOT_CONTRADICTORY")
            elapsed=time.perf_counter()-start
            item={"original_filename":filename,
                  "original_bytes":len(raw),"original_sha256":hashlib.sha256(raw).hexdigest(),
                  "original_assert_count_lexical":len(clauses),
                  "modulus":candidate["modulus"],
                  "polynomial_var":candidate["source_var"],
                  "polynomial_coefficients_by_exponent":{str(k):v for k,v in sorted(candidate["coefficient_by_degree"].items())},
                  "all_residues_modulo_m":residues,
                  "residue_count":len(residues),
                  "all_residue_values_zero":True,
                  "independent_original_source_z3_lemma_checker":independent,
                  "proof_wall_s_excluding_network_download":round(elapsed,6),
                  "conclusion":"ORIGINAL_QF_NIA_UNSAT_MATHEMATICALLY_CERTIFIED"}
            output["cases"].append(item)
            persist()
        output["status"]="ALL_3_OPENED_ORIGINAL_QF_NIA_UNSAT_CERTIFIED"
        output["scope_limited"]="posthoc development in one already opened source family"
        output["g0_original_source_exact_new_valid_answer"]="3_3_UNSAT"
        output["g0_free_oracle_full_cost_admitted"]=False
        persist()
        print("G0_ULTIMATE_ORIGINAL_CONGRUENCE_PROOF",json.dumps({
            "status":output["status"],"cases":len(output["cases"]),
            "mods":[c["modulus"] for c in output["cases"]],
            "proof_wall_s":[c["proof_wall_s_excluding_network_download"] for c in output["cases"]],
            "global":output["global_q1_q7"]}),flush=True)
    except Exception as e:
        output["status"]="FIRST_MODULAR_PROOF_FAILED"
        output["error"]=type(e).__name__+":"+str(e)[:300]
        persist()
        print("G0_ULTIMATE_PROOF_FIRST_FAILURE",output["error"],flush=True)
        raise
if __name__=="__main__":main()
