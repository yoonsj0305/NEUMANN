"""SHA-locked exact author tenth32 grammar failure taxonomy after first grading.

This is an AFTER-GRADE diagnostic, never 'fresh' evaluation, and cannot
retroactively change first learned 5/32 and classical 6/32 scores.
"""
import argparse,ast,collections,hashlib,json,pathlib
import sympy as sp
from erbench_original_tenth import allowed_formula,calc,SYM
X=sp.Symbol("x")
SHA_TRUE="7d7ed619194535ff3fb87b27593eee04eeddf10cc96e1ec9afe9b3513cfa5df5"
SHA_GRADE="5b7448bb5a9d81f9cb6063ca5a40af7b4b6235ed1e8ab2f4f6a00e7f4ec401d9"
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def depth(t):
    xs=list(ast.iter_child_nodes(t));return 1+max((depth(x) for x in xs),default=0)
def scan(gold,firstgrade,out):
    assert sha(gold)==SHA_TRUE and sha(firstgrade)==SHA_GRADE
    original=json.loads(pathlib.Path(gold).read_text())["private_true_equations"]
    scores=json.loads(pathlib.Path(firstgrade).read_text())["all_original32_case_receipts"]
    solved={k:{v["id"] for v in vals if v["status"]=="COMPLETE_ORIGINAL_SYMBOLICALLY_EXACT"}
            for k,vals in scores.items()}
    assert len(original)==32
    counts=collections.Counter();records=[]
    for item in original:
        n,variable=allowed_formula(item["original_expression"])
        kinds=[x.func.id for x in ast.walk(n) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name)]
        kinds=sorted(kinds)
        math=calc(n,{variable:X},SYM)
        try:
            rat=bool(sp.cancel(sp.together(math)).is_rational_function(X))
        except Exception:rat=False
        if rat:
            typ="RATIONAL"
        elif any(k in kinds for k in ("sin","cos","tan","sinh","cosh","tanh","asin","acos","atan")):
            typ="TRIG_OR_HYPERBOLIC"
        elif any(k in kinds for k in ("exp","log")):
            typ="EXP_OR_LOG"
        elif any(k in kinds for k in ("sqrt","abs")):
            typ="SQRT_ABS"
        else:typ="NONRATIONAL_OTHER"
        counts["type_"+typ]+=1
        for k in kinds:counts["call_"+k]+=1
        stats={"id":item["id"],
               "name":item["collection"]+":"+item["task_ID"],
               "true_expression":item["original_expression"],
               "method_true_exact":{k:item["id"] in s for k,s in solved.items()},
               "author_type":typ,
               "call_operators":kinds,
               "syntax_nodes":len(list(ast.walk(n))),
               "AST_max_depth":depth(n),
               "binary_ops":sum(isinstance(z,ast.BinOp) for z in ast.walk(n)),
               "known_human_unary_atom_primitive_alphabet_miss":sorted(set(kinds)-set(
                 ("sin","cos","exp","log","sqrt","abs","tanh","atan","sinh","cosh","tan")))}
        records.append(stats)
    ret={"schema":"NEUMANN_Q3_TENTH32_ORIGINAL_TRUE_FORMULA_FAILURE_TAXONOMY.v1",
         "locked_gold_SHA256":SHA_TRUE,"locked_first_grade_SHA256":SHA_GRADE,
         "originals":records,"counts":dict(counts),
         "original32_exact_scores":{k:len(v) for k,v in solved.items()},
         "posthoc_truth_assisted_analysis":True,
         "novel_independent_learned_invention":"NOT_PROVED",
         "first_original_scores_UNCHANGED":True,"G1":"HOLD"}
    p=pathlib.Path(out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(ret,sort_keys=True,indent=2)+"\n")
    print("Q3_TENTH32_SHA_LOCKED_UNSOLVED_REAL_AUTHOR_GRAMMAR_TAXONOMY",
       json.dumps({"operator_counts":dict(counts),
          "nonrational_unresolved_examples":[{"name":r["name"],"expression":r["true_expression"],"ops":r["call_operators"],"nodes":r["syntax_nodes"]} for r in records if r["author_type"]!="RATIONAL" and not r["method_true_exact"]["A_full_five_structure_actions"]][:18],
          "sha256":sha(p)},sort_keys=True),flush=True)
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--truth",required=True);a.add_argument("--grade",required=True);a.add_argument("--out",required=True)
    q=a.parse_args();scan(q.truth,q.grade,q.out)
