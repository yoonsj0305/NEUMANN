"""R9 appropriate CLASSICAL SPECIALIST baseline for exact original source sum of 3 integer cubes.

Preregistered GitHub issue #232. This is not learned model or structural novelty.
Safe parser: read entire original SMT-LIB, locate genuine TOP-LEVEL required
asserted equality, require exact three distinct declared nullary Int variable
cubes with a literal integer RHS. All unsupported formats fail CLOSED.
Return mathematical mod9 UNSAT only after full residue proof and independent
finite-remainder cross-check. DO NOT interpret absent proof as SAT.
No Z3 or SymPy imports; this is an appropriate low-overhead tailored solver.
"""
import hashlib,itertools,json,sys,time
from pathlib import Path

def tokens(data):
    """Lex only supported SMT2 lexical classes, guarding quotes & comments."""
    s=data.decode("utf8")
    i=0;n=len(s)
    while i<n:
        c=s[i]
        if c.isspace():i+=1;continue
        if c==";":
            end=s.find("\n",i)
            i=n if end<0 else end+1
            continue
        if c=="(" or c==")":
            yield c;i+=1;continue
        if c=="|":
            end=i+1
            while end<n and s[end]!="|":
                if s[end]=="\\" and end+1<n:end+=2
                else:end+=1
            if end>=n:raise ValueError("UNTERMINATED_QUOTED_SYMBOL")
            yield s[i:end+1];i=end+1;continue
        if c=='"':
            end=i+1
            while end<n:
                if s[end]=='"':
                    if end+1<n and s[end+1]=='"':end+=2;continue
                    break
                end+=1
            if end>=n:raise ValueError("UNTERMINATED_STRING")
            yield s[i:end+1];i=end+1;continue
        end=i
        while end<n and not s[end].isspace() and s[end] not in "()\";|":
            end+=1
        if end==i:raise ValueError("INVALID_UNQUOTED_TOKEN")
        yield s[i:end];i=end

def parse(data):
    roots=[];stack=[]
    count=0
    for t in tokens(data):
        count+=1
        if count>250000:raise ValueError("TOO_MANY_TOKENS")
        if t=="(":
            if len(stack)>128:raise ValueError("NESTING_CAP")
            val=[]
            if stack:stack[-1].append(val)
            else:roots.append(val)
            stack.append(val)
        elif t==")":
            if not stack:raise ValueError("UNMATCHED_CLOSE")
            stack.pop()
        else:
            if stack:stack[-1].append(t)
            else:raise ValueError("TOPLEVEL_ATOM_UNSUPPORTED")
    if stack:raise ValueError("UNCLOSED_GROUP")
    return roots

def int_literal(v):
    if isinstance(v,str) and v.isdecimal():return int(v)
    if isinstance(v,list) and len(v)==2 and v[0]=="-" and isinstance(v[1],str) and v[1].isdecimal():
        return -int(v[1])
    return None

def distinct_original_declared_ints(roots):
    out=set()
    for r in roots:
        if isinstance(r,list) and len(r)==4 and r[0]=="declare-fun" and r[2]==[] and r[3]=="Int":
            if isinstance(r[1],str):out.add(r[1])
    return out

def expected_cubes(expr,declared):
    """Exact + of 3 syntactic cubic monomials from original SMT AST."""
    if not isinstance(expr,list) or len(expr)!=4 or expr[0]!="+":return None
    syms=[]
    for term in expr[1:]:
        if not isinstance(term,list) or len(term)!=4 or term[0]!="*":return None
        if any(not isinstance(x,str) or x!=term[1] for x in term[2:]):return None
        if term[1] not in declared:return None
        syms.append(term[1])
    return syms if len(set(syms))==3 else None

def proof_candidate(asserted,declared):
    if not isinstance(asserted,list) or len(asserted)!=3 or asserted[0]!="=":
        return None
    a,b=asserted[1:]
    av=int_literal(a);bv=int_literal(b)
    if av is not None:
        names=expected_cubes(b,declared)
        if names:return names,av
    if bv is not None:
        names=expected_cubes(a,declared)
        if names:return names,bv
    return None

def sexpr(val):
    return "("+" ".join(sexpr(x) for x in val)+")" if isinstance(val,list) else val

def solve(path):
    start=time.perf_counter()
    data=Path(path).read_bytes()
    sha=hashlib.sha256(data).hexdigest()
    roots=parse(data)
    declared=distinct_original_declared_ints(roots)
    assertions=[r[1] for r in roots
                if isinstance(r,list) and len(r)==2 and r[0]=="assert"]
    if not assertions:
        return {"status":"NO_VALID_CERTIFICATE","source_sha256":sha,
                "reason":"NO_TOPLEVEL_NECESSARY_ASSERTION"}
    tested=0
    for original in assertions:
        candidate=proof_candidate(original,declared)
        if candidate is None:continue
        names,n=candidate;tested+=1
        modulus=9
        cube_residues={pow(x,3,modulus) for x in range(modulus)}
        # Faster table convolution is the actual specialized algorithm.
        sums={((u+v+w)%modulus)
             for u in cube_residues for v in cube_residues for w in cube_residues}
        # Second independent direct exhaustive arithmetic replay (729 triples).
        independently={((pow(x,3,modulus)+pow(y,3,modulus)+pow(z,3,modulus))%modulus)
                       for x,y,z in itertools.product(range(modulus),repeat=3)}
        if sums!=independently:
            raise AssertionError("MATH_PROOF_INDEPENDENT_RESIDUES_DISAGREE")
        if (n%modulus) in sums:continue
        # This is a genuine syntactic top-level required asserted equality.
        # Every integer assignment maps to one residue triple, none consistent.
        return {"status":"INDEPENDENT_ORIGINAL_UNSAT_MODULAR_CERTIFICATE",
                "source_sha256":sha,
                "original_required_atom":sexpr(original),
                "original_assertions_total":len(assertions),
                "original_declared_int_symbols":sorted(declared),
                "matched_exact_cubed_variables":names,
                "target_integer_value":n,
                "target_residue":n%9,
                "modulus":9,
                "independent_full_residue_checks":729,
                "allowed_rhs_residues":sorted(sums),
                "target_residue_absent":True,
                "crosscheck_different_enumeration":True,
                "entire_original_formula_unsat":True,
                "status_not_used_in_proof":True,
                "wall_s":round(time.perf_counter()-start,6)}
    return {"status":"NO_VALID_CERTIFICATE","source_sha256":sha,
            "original_assertions_total":len(assertions),
            "supported_original_required_assertions":tested,
            "wall_s":round(time.perf_counter()-start,6)}

if __name__=="__main__":
    try:
        print(json.dumps(solve(sys.argv[1]),sort_keys=True),flush=True)
    except Exception as exc:
        print(json.dumps({"status":"UNSUPPORTED_OR_INVALID_INPUT","error":type(exc).__name__,
                          "description":str(exc)[:160]}),flush=True)
        sys.exit(1)
