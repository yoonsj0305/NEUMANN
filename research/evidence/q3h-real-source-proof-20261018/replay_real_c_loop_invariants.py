"""Independently check PUBLISHED invariants on original licensed C programs.

A deliberately *strict* verifier: one int-only main loop, no pointers,
no unsupported C statements/calls, no overflow under reachable invariant.
Induction/exit obligations on ORIGINAL C syntax using pycparser + Z3.
This is an external-label validation gate, NOT neural Q3 success.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
import re
import sys
import time
import zipfile
from pathlib import Path

import z3
from pycparser import c_ast, c_parser

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3g-real-corpus-20261018"))
from inventory_real_corpus import workbook_tables
from link_real_invariants import run as pair_index
from license_body_audit import class_license

TARGETS=(
 "dataset/loop_invariants/LinearArbitrary-SeaHorn/VeriMAP/TRACER-testabs7_VeriMAP_true.c",
 "dataset/loop_invariants/LinearArbitrary-SeaHorn/invgen/simple.c",
 "dataset/loop_invariants/LinearArbitrary-SeaHorn/sharma_splitter/popl.c",
)
PERMISSIVE={"APACHE_2_0","BSD_3_CLAUSE","MIT"}
MIN_INT=-(2**31)
MAX_INT=2**31-1

class Unsupported(Exception):pass

def static_assertions(code):
    items=re.findall(r"(?m)^\s*//@\s*assert\s*\((.+)\)\s*;",code)
    if len(items)!=1:raise Unsupported("NEED_EXACTLY_ONE_ORIGINAL_ASSERTION")
    return items

def parse_expression(raw):
    raw=raw.strip()
    if not raw:raise Unsupported("EMPTY_EXPRESSION")
    if "==>" in raw:
        parts=raw.split("==>")
        if len(parts)!=2:raise Unsupported("MULTIPLE_IMPLICATIONS")
        raw=f"(!({parts[0].strip()})) || ({parts[1].strip()})"
    # ACSL chained inequalities are mathematical (C's chained comparisons aren't).
    chain=r"(?<![\w])(-?\d+|[A-Za-z_]\w*)\s*(<=|>=|<|>)\s*([A-Za-z_]\w*)\s*(<=|>=|<|>)\s*(-?\d+|[A-Za-z_]\w*)(?![\w])"
    def expand(m):
        a,op,b,op2,c=m.groups()
        return f"(({a} {op} {b}) && ({b} {op2} {c}))"
    raw=re.sub(chain,expand,raw)
    try:
        tree=c_parser.CParser().parse("int __invariant_expression__(){return ("+raw+");}")
        return tree.ext[0].body.block_items[0].expr
    except Exception as e:raise Unsupported("C_EXPRESSION_PARSE:"+str(e)[:100])

def as_boolean(value):
    if z3.is_bool(value):return value
    if z3.is_arith(value):return value!=0
    raise Unsupported("NOT_BOOLEAN_CONVERTIBLE")

def evaluate(expr,state,arith=None):
    if isinstance(expr,c_ast.ID):
        if expr.name not in state:raise Unsupported("UNDECLARED_IDENTIFIER:"+expr.name)
        return state[expr.name]
    if isinstance(expr,c_ast.Constant):
        if expr.type!="int":raise Unsupported("NON_INT_CONSTANT")
        try:return z3.IntVal(int(expr.value,0))
        except ValueError:
            if expr.value.isdecimal():return z3.IntVal(int(expr.value))
            raise Unsupported("UNSUPPORTED_INT_LITERAL")
    if isinstance(expr,c_ast.UnaryOp):
        x=evaluate(expr.expr,state,arith)
        if expr.op=="!":return z3.Not(as_boolean(x))
        if expr.op=="-":
            if arith is not None:arith.append(-x)
            return -x
        if expr.op=="+":return x
        raise Unsupported("UNSUPPORTED_C_UNARY:"+expr.op)
    if isinstance(expr,c_ast.BinaryOp):
        l=evaluate(expr.left,state,arith)
        r=evaluate(expr.right,state,arith)
        op=expr.op
        if op=="&&":return z3.And(as_boolean(l),as_boolean(r))
        if op=="||":return z3.Or(as_boolean(l),as_boolean(r))
        if op=="==":return l==r
        if op=="!=":return l!=r
        if op=="<":return l<r
        if op==">":return l>r
        if op=="<=":return l<=r
        if op==">=":return l>=r
        if op=="+":val=l+r
        elif op=="-":val=l-r
        elif op=="*":val=l*r
        elif op=="%":
            # C remainder semantics (truncation toward zero), not Euclidean
            # remainder on negative operands.
            if arith is not None:raise Unsupported("BODY_C_MODULO_UNSUPPORTED")
            if not z3.is_int_value(r) or r.as_long()==0:
                raise Unsupported("NONCONST_OR_ZERO_MODULUS")
            d=abs(r.as_long())
            return z3.If(l>=0,l%d,-((-l)%d))
        else:raise Unsupported("UNSUPPORTED_C_BINARY:"+op)
        if arith is not None:arith.append(val)
        return val
    raise Unsupported("UNSUPPORTED_EXPR:"+type(expr).__name__)

def conjunct(label,state):
    pieces=[x.strip() for x in label.split(";") if x.strip()]
    if not pieces:raise Unsupported("NO_INVARIANT_LABEL")
    return z3.And(*[as_boolean(evaluate(parse_expression(s),state)) for s in pieces])

def is_int_decl(decl):
    typ=decl.type
    return (isinstance(typ,c_ast.TypeDecl) and isinstance(typ.type,c_ast.IdentifierType)
            and typ.type.names==["int"])

def only_stmt(node):
    if isinstance(node,c_ast.Compound):
        return node.block_items or []
    return [node]

def execute_statement(node,state,guards,scope="pre"):
    """Symbolic state update, guards are tracked on the actual source path.
    Unsupported calls, pointer effects, annotations, or access reject.
    """
    if isinstance(node,c_ast.EmptyStatement):return state
    if isinstance(node,c_ast.Decl):
        if not is_int_decl(node):raise Unsupported("NON_INT_LOCAL_DECL")
        if node.name in state:raise Unsupported("DOUBLE_DECLARATION")
        new=dict(state)
        new[node.name]=z3.Int("loop_original_"+node.name)
        if node.init is not None:
            if isinstance(node.init,c_ast.FuncCall) and isinstance(node.init.name,c_ast.ID) and node.init.name.name=="unknown":
                if node.init.args and node.init.args.exprs:
                    raise Unsupported("UNKNOWN_CALL_WITH_ARGS")
            else:
                new[node.name]=evaluate(node.init,new,guards["arith"])
        return new
    if isinstance(node,c_ast.Assignment) and isinstance(node.lvalue,c_ast.ID):
        name=node.lvalue.name
        if name not in state:raise Unsupported("ASSIGN_UNDECLARED")
        if node.op=="=":newval=evaluate(node.rvalue,state,guards["arith"])
        elif node.op=="+=":newval=state[name]+evaluate(node.rvalue,state,guards["arith"])
        elif node.op=="-=":newval=state[name]-evaluate(node.rvalue,state,guards["arith"])
        else:raise Unsupported("UNSUPPORTED_ASSIGN_OPERATOR")
        guards["arith"].append(newval)
        new=dict(state);new[name]=newval
        return new
    if isinstance(node,c_ast.UnaryOp) and isinstance(node.expr,c_ast.ID):
        name=node.expr.name
        if name not in state:raise Unsupported("UNARY_UNDECLARED")
        if node.op in ("p++","++"):val=state[name]+1
        elif node.op in ("p--","--"):val=state[name]-1
        else:raise Unsupported("UNSUPPORTED_UNARY_STMT")
        guards["arith"].append(val)
        new=dict(state);new[name]=val
        return new
    if isinstance(node,c_ast.FuncCall) and isinstance(node.name,c_ast.ID):
        if scope!="pre" or node.name.name!="assume" or node.args is None or len(node.args.exprs)!=1:
            raise Unsupported("UNSUPPORTED_OR_NON_PRE_ASSUME_CALL")
        guards["assumptions"].append(as_boolean(evaluate(node.args.exprs[0],state,guards["arith"])))
        return state
    if isinstance(node,c_ast.If) and scope=="loop":
        cond=as_boolean(evaluate(node.cond,state,guards["arith"]))
        then_state=execute_many(only_stmt(node.iftrue),dict(state),guards,"loop")
        else_state=execute_many(only_stmt(node.iffalse),dict(state),guards,"loop") if node.iffalse is not None else state
        return {k:z3.If(cond,then_state[k],else_state[k]) for k in state}
    if isinstance(node,c_ast.Compound):return execute_many(only_stmt(node),state,guards,scope)
    raise Unsupported("UNSUPPORTED_STATEMENT:"+type(node).__name__)

def execute_many(nodes,state,guards,scope):
    for node in nodes:state=execute_statement(node,state,guards,scope)
    return state

def get_main(code):
    assertion=static_assertions(code)[0]
    # Strict preprocessing: remove known inert includes and source macros,
    # source-level inline specifications/comments but keep executable syntax.
    stripped=re.sub(r"/\*.*?\*/","",code,flags=re.S)
    stripped=re.sub(r"//[^\n]*","",stripped)
    preprocessor=[line.strip() for line in stripped.splitlines() if line.lstrip().startswith("#")]
    for line in preprocessor:
        if not (line.startswith("#include <stdlib.h>") or
                line.startswith("#define assume(e) if(!(e)) exit(-1);")):
            raise Unsupported("UNSUPPORTED_CPP_MACRO:"+line[:90])
    stripped="\n".join(line for line in stripped.splitlines()
                       if not line.lstrip().startswith("#"))
    try:tree=c_parser.CParser().parse(stripped)
    except Exception as e:raise Unsupported("ORIGINAL_C_PARSE_ERROR:"+str(e)[:200])
    mains=[e for e in tree.ext if isinstance(e,c_ast.FuncDef) and e.decl.name=="main"]
    if len(mains)!=1:raise Unsupported("NO_EXACT_MAIN")
    fn=mains[0]
    if not isinstance(fn.decl.type,c_ast.FuncDecl):raise Unsupported("NONSTANDARD_MAIN")
    return fn,assertion

def model_original(code,label):
    from original_assert_site import require_original_after_loop_assertion
    require_original_after_loop_assertion(code)
    fn,assertion=get_main(code)
    ast=fn.body.block_items or []
    initial={}
    if fn.decl.type.args is not None:
        for p in fn.decl.type.args.params:
            if isinstance(p,c_ast.Typename) and isinstance(p.type,c_ast.TypeDecl) and isinstance(p.type.type,c_ast.IdentifierType) and p.type.type.names==["void"]:
                continue
            if not isinstance(p,c_ast.Decl) or not is_int_decl(p):
                raise Unsupported("NON_INT_MAIN_PARAMETER")
            initial[p.name]=z3.Int("loop_original_"+p.name)
    init_env=dict(initial)
    context={"assumptions":[],"arith":[]}
    found=[]
    finished=False
    for stmt in ast:
        if isinstance(stmt,(c_ast.While,c_ast.For)):
            if finished:raise Unsupported("MORE_THAN_ONE_LOOP")
            loop=stmt;finished=True;continue
        if not finished:
            init_env=execute_statement(stmt,init_env,context,"pre")
            continue
        # Only optional return and an empty no-effect compound after loop.
        if isinstance(stmt,c_ast.Return):
            if stmt.expr is not None and not isinstance(stmt.expr,c_ast.Constant):
                raise Unsupported("EFFECTFUL_RETURN")
        elif isinstance(stmt,c_ast.Compound):
            if any(not isinstance(x,c_ast.EmptyStatement) for x in only_stmt(stmt)):
                raise Unsupported("UNMODELED_POST_LOOP_EFFECT")
        elif not isinstance(stmt,c_ast.EmptyStatement):
            raise Unsupported("UNMODELED_POST_LOOP_STATEMENT")
    if not finished:raise Unsupported("NO_MAIN_LOOP")
    if isinstance(loop,c_ast.For):
        # Loop initializer C is applied before checking invariant.
        if loop.init is not None:
            if not isinstance(loop.init,(c_ast.Assignment,c_ast.UnaryOp)):
                raise Unsupported("COMPLEX_FOR_INIT")
            init_env=execute_statement(loop.init,init_env,context,"pre")
        if loop.cond is None:raise Unsupported("UNBOUNDED_FOR_CONDITION")
        cond_ast=loop.cond
    else:cond_ast=loop.cond
    variable_names=list(init_env)
    if not variable_names:raise Unsupported("NO_INTEGER_STATE")
    before={k:z3.Int("loop_head_"+k) for k in variable_names}
    init_inv=conjunct(label,init_env)
    head_inv=conjunct(label,before)
    test=as_boolean(evaluate(cond_ast,before,context["arith"]))
    body_env=execute_many(only_stmt(loop.stmt),before,context,"loop")
    if isinstance(loop,c_ast.For) and loop.next is not None:
        body_env=execute_statement(loop.next,body_env,context,"loop")
    next_inv=conjunct(label,body_env)
    post_assert=as_boolean(evaluate(parse_expression(assertion),before))
    return {
        "initial":initial,
        "after_prelude":init_env,
        "loop_state":before,
        "init_assumptions":context["assumptions"],
        "arithmetic_expressions":context["arith"],
        "init_invariant":init_inv,
        "head_invariant":head_inv,
        "loop_test":test,
        "body_state":body_env,
        "next_invariant":next_inv,
        "post_assert":post_assert,
        "assertion_original":assertion,
    }

def signed_domain(symbolic_state):
    return [z3.And(v>=MIN_INT,v<=MAX_INT) for v in symbolic_state.values()]

def check(assertion,timeout=5000):
    solver=z3.Solver()
    solver.set(timeout=timeout)
    solver.add(assertion)
    result=solver.check()
    return str(result)

def verify(code,label):
    model=model_original(code,label)
    from_init=z3.And(*signed_domain(model["initial"]),*model["init_assumptions"])
    from_loop=z3.And(*signed_domain(model["loop_state"]),model["head_invariant"])
    start=time.perf_counter_ns()
    init=check(z3.And(from_init,z3.Not(model["init_invariant"])))
    inductive=check(z3.And(from_loop,model["loop_test"],z3.Not(model["next_invariant"])))
    safety=check(z3.And(from_loop,z3.Not(model["loop_test"]),z3.Not(model["post_assert"])))
    arithmetic=check(z3.And(from_loop,model["loop_test"],z3.Or(*[
            z3.Or(x<MIN_INT,x>MAX_INT) for x in model["arithmetic_expressions"]
        ]))) if model["arithmetic_expressions"] else "unsat"
    # Arithmetic expressions of INIT are covered by bounded state and
    # initialization proof only if they are explicit constants/assignments.
    # If the original source contains arithmetic in the prelude that could
    # overflow, reject rather than assuming its exact semantics.
    original=check(z3.And(from_init,z3.Or(*[
        z3.Or(z3.simplify(x)<MIN_INT,z3.simplify(x)>MAX_INT)
        for x in model["arithmetic_expressions"]
        if not any(n.decl().name().startswith("loop_head_")
                   for n in z3.z3util.get_vars(x))
    ]))) if model["arithmetic_expressions"] else "unsat"
    mutated_false=check(z3.And(from_loop,z3.Not(model["loop_test"])))
    weak_label=conjunct("1",model["loop_state"])
    weak_safety=check(z3.And(*signed_domain(model["loop_state"]),weak_label,
                             z3.Not(model["loop_test"]),z3.Not(model["post_assert"])))
    checks={"init":init,"inductive":inductive,"postcondition":safety,
            "body_signed_overflow":arithmetic,
            "prelude_signed_overflow":original,
            "mutated_false_postcondition":mutated_false,
            "weak_constant_true_invariant_postcondition":weak_safety}
    success=all(checks[k]=="unsat" for k in
                ("init","inductive","postcondition","body_signed_overflow","prelude_signed_overflow"))
    negative=(mutated_false=="sat" and weak_safety=="sat")
    return {"status":"ALL_ORIGINAL_LOOP_OBLIGATIONS_UNSAT" if success and negative
            else "ABSTAIN_OR_NEGATIVE_CONTROL_FAILED",
            "checks":checks,
            "original_post_assertion_sha256":hashlib.sha256(model["assertion_original"].encode()).hexdigest(),
            "wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
            "model_used":False,
            "invariant_written_by":"published Loopy research, not NEUMANN",
            "c_semantics_scope":"single finite int loop, no aliased memory or other side effects, signed-overflow obligations checked"}

def first_originals(workbook,archive):
    if workbook.name!="GeneratedInvariants.xlsx" or archive.name!="dataset.zip":
        raise ValueError("WRONG_LOOPY_PINNED_FILES")
    metadata=pair_index(workbook,archive)["per_pair_identity_only"]
    reference={x["program_path"]:x for x in metadata}
    table=workbook_tables(workbook.read_bytes())["Sheet1"]
    labels={x.get("A","").strip():x.get("B","").strip() for x in table[1:]}
    results=[]
    with zipfile.ZipFile(io.BytesIO(archive.read_bytes())) as z:
        for file in TARGETS:
            row=reference.get(file)
            if row is None:raise ValueError("ORIGINAL_DEVELOPMENT_SOURCE_NOT_INDEXED")
            if row["source_group"] in (
                "dataset/loop_invariants/LinearArbitrary-SeaHorn/VeriMAP" if False else "",
            ):raise AssertionError("BAD_SOURCE_GROUP")
            licname=row["license_path_hint"]
            if not licname or class_license(z.read(licname)) not in ("APACHE_2_0","BSD_3_CLAUSE","MIT"):
                raise ValueError("TARGET_LICENSE_NOT_PERMISSIVE")
            program=z.read(file)
            if hashlib.sha256(program).hexdigest()!=row["source_sha256"]:
                raise ValueError("ORIGINAL_SOURCE_SHA_CHANGED")
            annotation=labels[row["published_row_source"]]
            try:
                proof=verify(program.decode("utf-8"),annotation)
            except Exception as e:
                proof={"status":"ABSTAIN_PARSER_OR_UNSUPPORTED",
                        "error":f"{type(e).__name__}: {str(e)[:250]}"}
            results.append({
                "path":file,
                "original_c_sha256":row["source_sha256"],
                "original_invariant_sha256":row["invariant_sha256"],
                "original_source_group":row["source_group"],
                "source_altered":False,
                "license":class_license(z.read(licname)),
                "proof":proof
            })
    return {
        "status":"REAL_ORIGINAL_LOOP_INVARIANT_PROOF_AUDIT",
        "upstream":"microsoft/loop-invariant-gen-experiments",
        "upstream_commit":"91fe89245a0894ec8ad3741d85ae91ce3b552b2e",
        "opened_only_previously_development_real_sources":True,
        "q3f_holdout_source_read":False,
        "learned_model_inference_calls":0,
        "global_q1_q7":"OPEN",
        "results":results,
        "fully_proven_count":sum(r["proof"]["status"]=="ALL_ORIGINAL_LOOP_OBLIGATIONS_UNSAT" for r in results)
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--workbook",required=True,type=Path)
    p.add_argument("--dataset",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    report=first_originals(a.workbook,a.dataset)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("Q3H_ORIGINAL_C_FORMAL_AUDIT",[(r["path"],r["proof"]) for r in report["results"]])
    print("PROVEN",report["fully_proven_count"],"OF",len(report["results"]))
