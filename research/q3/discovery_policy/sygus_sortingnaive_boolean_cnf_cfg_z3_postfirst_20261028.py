#!/usr/bin/env python3
"""Post-FIRST classical 6-Boolean circuit semantic compression and original
SyGuS depth grammar derivability proof for sorting_naive. NO learned model.
"""
import hashlib,itertools,json,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
SOURCE="lib/General_Track/woosuk/sorting_naive.eqn_sygus_iter_256_0.sl"
ORIGINAL_SHA="07ec6bd54cdf81008dcb273cb7528c3c5ad30843b0642262ef8b8731cb5137e6"
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("official_sortingnaive_bool_specialist")

def parse_s_expr(s):
    tokens=re.findall(r"\(|\)|[^\s()]+",s)
    p=0
    def read():
        nonlocal p
        if p>=len(tokens):raise ValueError("SMTLIB_EOF")
        token=tokens[p];p+=1
        if token=="(":
            items=[]
            while p<len(tokens) and tokens[p]!=")":
                items.append(read())
            if p>=len(tokens):raise ValueError("UNBALANCED")
            p+=1
            return items
        if token==")":raise ValueError("UNEXPECTED_CLOSE")
        return token
    out=read()
    if p!=len(tokens):raise ValueError("EXTRANEOUS_CONTENT")
    return out

def to_sympy(expr,variables):
    from sympy import And,Or,Not,Xor,ITE
    if isinstance(expr,str):
        if expr in variables:return variables[expr]
        if expr=="true":return True
        if expr=="false":return False
        raise ValueError("UNSUPPORTED_ORIGINAL_ATOM_"+expr)
    if not isinstance(expr,list) or not expr:raise ValueError("BAD_ORIGINAL_EXPRESSION")
    op=expr[0];v=[to_sympy(k,variables) for k in expr[1:]]
    if op=="and":return And(*v)
    if op=="or":return Or(*v)
    if op=="not" and len(v)==1:return Not(v[0])
    if op=="xor":return Xor(*v)
    if op=="ite" and len(v)==3:return ITE(*v)
    raise ValueError("UNSUPPORTED_ORIGINAL_BOOL_"+op)

def cnf_leaf(t):
    from sympy import Symbol,Not,Or,And
    if isinstance(t,Symbol):return str(t)
    if isinstance(t,Not):
        q=t.args[0]
        if isinstance(q,Symbol):return ["not",str(q)]
    if isinstance(t,Or):
        neg=[]
        for term in t.args:
            if not isinstance(term,Not) or not isinstance(term.args[0],Symbol):
                raise ValueError("CNF_CLAUSE_NEEDS_DIFFERENT_SPECIALIST")
            neg.append(str(term.args[0]))
        if len(neg)==2:
            return ["not",["and",neg[0],neg[1]]]
    raise ValueError("CNF_CLAUSE_NOT_SUPPORTABLE")

def term_trees(values):
    if len(values)==1:
        yield values[0]
        return
    for split in range(1,len(values)):
        for a in term_trees(values[:split]):
            for b in term_trees(values[split:]):
                yield ["and",a,b]

def get_grammar(synth):
    assert synth[0]=="synth-fun" and synth[1]=="skel"
    nts=synth[4]
    rule_blocks=synth[5]
    assert all(len(n)==2 and n[1]=="Bool" for n in nts)
    g={r[0]:r[2] for r in rule_blocks}
    assert set(g)==set(r[0] for r in nts)
    return g

def original_grammar_membership(root,gram):
    cache={}
    active=set()
    def accepts(expr,nt):
        key=(repr(expr),nt)
        if key in cache:return cache[key]
        if key in active:return False
        active.add(key)
        ans=any(match(p,expr) for p in gram[nt])
        active.remove(key)
        cache[key]=ans
        return ans
    def match(pattern,expr):
        if isinstance(pattern,str):
            return accepts(expr,pattern) if pattern in gram else expr==pattern
        if isinstance(pattern,list) and isinstance(expr,list) and len(pattern)==len(expr):
            return all(match(a,b) for a,b in zip(pattern,expr))
        return False
    return accepts(root,"Start"),len(cache)

def to_smt(node):
    if isinstance(node,str):return node
    return "("+" ".join(to_smt(x) for x in node)+")"

def main():
    import sympy
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    raw=(ROOT/SOURCE).read_bytes()
    assert sha256(raw)==ORIGINAL_SHA
    forms=[(get_cmd(f[2]),f[2]) for f in top_level_forms(raw.decode())]
    helpers=[f for c,f in forms if c=="define-fun"]
    synth=[f for c,f in forms if c=="synth-fun"]
    cons=[f for c,f in forms if c=="constraint"]
    declared=[f for c,f in forms if c=="declare-var"]
    assert len(helpers)==1 and len(synth)==1 and len(cons)==1 and len(declared)==6
    original=parse_s_expr(helpers[0])
    synthesis=parse_s_expr(synth[0])
    assert original[0]=="define-fun" and original[1]=="origCir"
    assert len(original[2])==6 and original[3]=="Bool"
    assert len(synthesis[2])==6 and synthesis[3]=="Bool"
    args=[p[0] for p in original[2]]
    assert all(p[1]=="Bool" for p in original[2])
    assert synthesis[2]==original[2]
    variables={p:sympy.Symbol(p) for p in args}
    t0=time.process_time()
    circuit=to_sympy(original[4],variables)
    cnf=sympy.simplify_logic(circuit,form="cnf",force=True)
    truth_checked=0
    for combination in itertools.product((False,True),repeat=6):
        valuation=dict(zip(variables.values(),combination))
        if bool(circuit.subs(valuation))!=bool(cnf.subs(valuation)):
            raise ValueError("SYMPY_CNF_NOT_64ROW_EQUIVALENT")
        truth_checked+=1
    assert truth_checked==64
    terms=list(cnf.args) if isinstance(cnf,sympy.And) else [cnf]
    leaves=[cnf_leaf(v) for v in terms]
    gram=get_grammar(synthesis)
    chosen=None
    examined=0
    # Finite, fully deterministic grammar-search on exactly simplified
    # Boolean substructures, not cvc5-style open-ended expansion.
    for perm in itertools.permutations(range(len(leaves))):
        for candidate in term_trees([leaves[i] for i in perm]):
            examined+=1
            accept,_=original_grammar_membership(candidate,gram)
            if accept:
                chosen=candidate
                break
        if chosen is not None:break
    if chosen is None:
        raise ValueError("NO_DERIVABLE_AST_OF_SIMPLIFIED_CNF")
    accepted,subgoals=original_grammar_membership(chosen,gram)
    assert accepted
    candidate_smt=to_smt(chosen)
    typed="(define-fun skel ("+" ".join("("+n+" Bool)" for n in args)+") Bool "+candidate_smt+")"
    grammar_cpu=time.process_time()-t0
    OUT.mkdir(exist_ok=True)
    (OUT/"SIMPLIFIED_ORIGINAL_TYPED_CIRCUIT.smt2").write_text(typed+"\n")
    # This original semantics is a universal equality of the two Boolean
    # circuits. Negation UNSAT is exact 2^6-input equivalence proof.
    c=re.fullmatch(r"\(\s*constraint\s+(.+)\s*\)",cons[0],re.S)
    assert c
    prefix=["(set-logic ALL)",helpers[0]]
    prefix.extend(re.sub(r"^\(\s*declare-var\b","(declare-const",f,count=1) for f in declared)
    prefix.append(typed)
    script="\n".join(prefix)+"\n(assert (not "+c.group(1)+"))\n"
    (OUT/"original_complete_universal_Z3_counterexample.smt2").write_text(script)
    z0=time.process_time()
    solver=z3.Solver();solver.set(timeout=12000)
    solver.add(*z3.parse_smt2_string(script))
    check=str(solver.check())
    z_cpu=time.process_time()-z0
    pass_all=(check=="unsat" and accepted and truth_checked==64)
    report={
      "scope":"POSTFIRST_SYMPY_SPECIALIST_ORIGINAL_FULL_GRAMMAR_NOT_NEURAL",
      "original_repo_commit":PIN,
      "original_source_path":SOURCE,
      "source_sha256":ORIGINAL_SHA,
      "source_original_input_count":len(args),
      "source_original_universal_constraint_count":1,
      "original_synth_grammar_start":"Start",
      "original_synth_grammar_nonterminals":list(gram),
      "sympy_version":sympy.__version__,"z3_version":z3.get_version_string(),
      "original_sympy_circuit":str(circuit),"simplified_CNF":str(cnf),
      "original_truth_table_all_64_rows_checked":truth_checked,
      "compiled_candidate_smt":typed,
      "compiled_candidate_ast":chosen,
      "compiled_candidate_sha256":sha256((typed+"\n").encode()),
      "original_grammar_membership":accepted,
      "original_grammar_membership_subgoals":subgoals,
      "grammar_legal_candidates_enumerated_before_first_match":examined,
      "construct_simplify_and_cfg_cpu_seconds":round(grammar_cpu,6),
      "independent_original_Z3_query_result":check,
      "independent_Z3_query_sha256":sha256(script.encode()),
      "independent_Z3_checker_cpu_seconds":round(z_cpu,6),
      "verdict":"POSTFIRST_CLASSICAL_CORRECT_ORIGINAL_GRAMMAR_PROVED" if pass_all else "HOLD",
      "strong_native_cvc5_142_12cpu_first":"TIMEOUT",
      "ownweight_model_training":False,
      "G1":"HOLD","global_Q1_Q7":"OPEN","G2":"NOT_RUN"}
    file=OUT/"SORTING_NAIVE_ORIGINAL_BOOL_COMPRESSED_AST_CFG_Z3_PROOF.json"
    file.write_text(json.dumps(report,indent=2,sort_keys=True))
    print("ORIGINAL_BOOL_CNF",str(cnf))
    print("AST",candidate_smt)
    print("CFG_DERIVABLE",accepted,"TRUTH64",truth_checked,"Z3",check,flush=True)
    print("RESULT_SHA256",sha256(file.read_bytes()))
    print("VERDICT",report["verdict"])
if __name__=="__main__":main()
