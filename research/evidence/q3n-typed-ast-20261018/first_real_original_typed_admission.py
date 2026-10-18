"""Q3N: authentic typed AST / original-proof corpus admission, not a learned model.

Keep 2026-10-18 source-group split and exactly 150 licensed Loopy sources.
No target text or source body in receipt. Does not read sealed CHC-COMP tasks.
"""
from __future__ import annotations
import argparse,collections,hashlib,io,json,sys,zipfile
from pathlib import Path
from pycparser import c_ast
import z3

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3g-real-corpus-20261018"))
sys.path.insert(0,str(HERE.parent/"q3h-real-source-proof-20261018"))
from inventory_real_corpus import workbook_tables,git_blob,LOOPY_WORKBOOK_GIT_BLOB,LOOPY_DATASET_GIT_BLOB
from link_real_invariants import run as index_sources
from license_body_audit import class_license
from replay_real_c_loop_invariants import model_original,parse_expression,verify

EVAL_GROUPS={
 "dataset/loop_invariants/LinearArbitrary-SeaHorn/VeriMAP",
 "dataset/loop_invariants/sv-benchmarks/loop-lit",
}
PERMISSIVE={"APACHE_2_0","BSD_3_CLAUSE","MIT"}
EXPECTED_PERMISSIVE=150

class InvalidTypedAST(Exception): pass

def make_ast(node, bound):
    """Return (canonical AST, strict sort) of a source-bound typed formula."""
    if isinstance(node,c_ast.ID):
        if node.name not in bound:
            raise InvalidTypedAST("UNBOUND_VARIABLE")
        return ["VAR",bound[node.name]],"INT"
    if isinstance(node,c_ast.Constant):
        if node.type!="int":raise InvalidTypedAST("NONINTEGER_CONSTANT")
        try:value=int(node.value,0)
        except ValueError:
            if not node.value.isdecimal():raise InvalidTypedAST("NONSTANDARD_INTEGER")
            value=int(node.value)
        if abs(value)>2**31:raise InvalidTypedAST("LITERAL_OUTSIDE_SUPPORTED_DOMAIN")
        return ["INT",value],"INT"
    if isinstance(node,c_ast.UnaryOp):
        child,sort=make_ast(node.expr,bound)
        if node.op=="!" and sort=="BOOL":return ["NOT",child],"BOOL"
        if node.op=="-" and sort=="INT":return ["NEG",child],"INT"
        if node.op=="+" and sort=="INT":return child,"INT"
        raise InvalidTypedAST("UNARY_TYPE_OR_OPERATOR_MISMATCH")
    if isinstance(node,c_ast.BinaryOp):
        l,ls=make_ast(node.left,bound)
        r,rs=make_ast(node.right,bound)
        op=node.op
        if op in ("+","-","*","%"):
            if ls!=rs or ls!="INT":raise InvalidTypedAST("ARITH_SORT_ERROR")
            return [op,l,r],"INT"
        if op in ("<","<=",">",">="):
            if ls!=rs or ls!="INT":raise InvalidTypedAST("ORDER_SORT_ERROR")
            return [op,l,r],"BOOL"
        if op in ("==","!="):
            if ls!=rs:raise InvalidTypedAST("EQUALITY_SORT_ERROR")
            return [op,l,r],"BOOL"
        if op in ("&&","||"):
            if ls!=rs or ls!="BOOL":raise InvalidTypedAST("BOOLEAN_SORT_ERROR")
            return [op,l,r],"BOOL"
        raise InvalidTypedAST("UNSUPPORTED_OPERATOR")
    raise InvalidTypedAST("UNSUPPORTED_AST_NODE")

def depth(tree):
    if not isinstance(tree,list):return 0
    return 1+max([depth(child) for child in tree[1:] if isinstance(child,list)],default=0)

def ops(tree):
    yield tree[0]
    for v in tree[1:]:
        if isinstance(v,list):yield from ops(v)

def convert_public_label(label,names):
    pieces=[q.strip() for q in label.replace("\r\n","\n").split(";") if q.strip()]
    if not pieces or len(pieces)>40:raise InvalidTypedAST("INVALID_CONJUNCTION_SIZE")
    bound={name:i for i,name in enumerate(sorted(names))}
    trees=[]
    for expr in pieces:
        item,sort=make_ast(parse_expression(expr),bound)
        if sort!="BOOL":raise InvalidTypedAST("NONBOOLEAN_PREDICATE")
        trees.append(item)
    if len(trees)==1:return trees[0],len(pieces)
    return ["AND",*trees],len(pieces)

def collect(workbook,dataset):
    if git_blob(workbook.read_bytes())!=LOOPY_WORKBOOK_GIT_BLOB:
        raise ValueError("WORKBOOK_CHANGED")
    raw=dataset.read_bytes()
    if git_blob(raw)!=LOOPY_DATASET_GIT_BLOB:
        raise ValueError("ORIGINAL_DATASET_CHANGED")
    pair_index=index_sources(workbook,dataset)["per_pair_identity_only"]
    table=workbook_tables(workbook.read_bytes())["Sheet1"]
    labels=collections.defaultdict(list)
    for row in table[1:]:
        labels[row.get("A","").strip()].append(row.get("B","").strip())
    result=[];reject=collections.Counter()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        license_paths={r["license_path_hint"] for r in pair_index if r["license_path_hint"]}
        types={p:class_license(z.read(p)) for p in license_paths}
        admissible=[r for r in pair_index if types.get(r["license_path_hint"]) in PERMISSIVE]
        if len(admissible)!=EXPECTED_PERMISSIVE:raise ValueError("LICENSE_POOL_NOT_150")
        if len({r["source_sha256"] for r in admissible})!=EXPECTED_PERMISSIVE:
            raise ValueError("DUPLICATE_ORIGINAL_C_SOURCE_IDENTITY")
        for entry in admissible:
            group=entry["source_group"]
            split="HELDOUT" if group in EVAL_GROUPS else "TRAIN"
            source_bytes=z.read(entry["program_path"])
            if hashlib.sha256(source_bytes).hexdigest()!=entry["source_sha256"]:
                raise ValueError("ORIGINAL_BYTES_SHA_CHANGED")
            raw_label=labels.get(entry["published_row_source"],[])
            verdict="NOT_PROVEN"
            info={"source_sha256":entry["source_sha256"],
                  "source_group":group,"split":split,
                  "license":types[entry["license_path_hint"]],
                  "published_invariant_sha256":entry["invariant_sha256"]}
            if len(raw_label)!=1 or not raw_label[0]:
                info["status"]="REJECT_NO_UNIQUE_PUBLISHED_LABEL"
            elif hashlib.sha256(raw_label[0].encode()).hexdigest()!=entry["invariant_sha256"]:
                raise ValueError("PUBLISHED_LABEL_SHA_CHANGED")
            else:
                original=source_bytes.decode("utf-8",errors="strict")
                try:
                    model=model_original(original,"1")
                    names=sorted(model["loop_state"])
                    typed,parts=convert_public_label(raw_label[0],names)
                    evidence=verify(original,raw_label[0])
                    verified=evidence["status"]=="ALL_ORIGINAL_LOOP_OBLIGATIONS_UNSAT"
                    info.update({
                        "status":"INDEPENDENT_ORIGINAL_C_PROOF_AND_TYPED_AST"
                            if verified else "TYPED_AST_ORIGINAL_C_NOT_PROVEN",
                        "source_integer_variable_count":len(names),
                        "typed_predicate_clauses":parts,
                        "typed_ast_depth":depth(typed),
                        "typed_ast_nodes":sum(1 for _ in ops(typed)),
                        "typed_ast_operators":dict(collections.Counter(ops(typed))),
                        "typed_ast_sha256":hashlib.sha256(
                            json.dumps(typed,separators=(",",":")).encode()
                        ).hexdigest(),
                        "proof_original_contract":{
                            "status":evidence["status"],
                            "checks":evidence.get("checks",{})
                        } if verified else {"status":evidence["status"]},
                        "typed_variable_binding_valid":True,
                        "typed_sort_valid":True,
                        "original_C_assertion_site_checked":True
                    })
                except Exception as err:
                    info["status"]="REJECT_UNSUPPORTED_AST_C_OR_ORIGINAL"
                    info["rejection_type"]=type(err).__name__
                    info["rejection_reason_category"]=str(err).split(":")[0][:100]
            reject[info["status"]]+=1
            result.append(info)
    observed={}
    for split in ("TRAIN","HELDOUT"):
        rows=[r for r in result if r["split"]==split]
        proven=[r for r in rows if r["status"]=="INDEPENDENT_ORIGINAL_C_PROOF_AND_TYPED_AST"]
        per_group=collections.Counter(r["source_group"] for r in proven)
        observed[split]={
            "total_license_accepted_source_files":len(rows),
            "distinct_source_groups":len({r["source_group"] for r in rows}),
            "strict_typed_original_proof_pairs":len(proven),
            "strict_typed_original_proof_source_groups":len(per_group),
            "per_group_independently_reproved":dict(sorted(per_group.items())),
            "groups_with_at_least_two_independent_proofs":sum(n>=2 for n in per_group.values()),
            "typed_ast_canonical_depths":dict(collections.Counter(
                r["typed_ast_depth"] for r in proven)),
            "fail_or_unproved":len(rows)-len(proven),
        }
    train=observed["TRAIN"]
    go=train["groups_with_at_least_two_independent_proofs"]>=20 and observed["HELDOUT"]["total_license_accepted_source_files"]>0
    return {
        "study":"Q3N_REAL_PROOF_TYPED_AST_TRAINING_DATA_ADMISSION",
        "status":"GO_REAL_TYPED_OPERATOR_TRAINING" if go else "STOP_INSUFFICIENT_GROUP_DISJOINT_ORIGINAL_PROVEN_TRAINING_DATA",
        "source_revision":"91fe89245a0894ec8ad3741d85ae91ce3b552b2e",
        "original_verified_label_and_license_pool":EXPECTED_PERMISSIVE,
        "group_split":"Q3G_20261018_FROZEN_SOURCE_GROUP_SPLIT",
        "split_census":observed,
        "status_counts_all_source_files":dict(reject),
        "actual_source_identity_count":len(result),
        "goal_training_requirement":"20 source-origin train groups with >=2 independently original-proven typed predicate AST examples per group",
        "training_admitted":go,
        "trained_model_calls":0,"frontier_model_calls":0,
        "q3f_escrow_source_text_opened":False,
        "source_bytes_republished":False,
        "published_invariant_text_republished":False,
        "global_q1_q7":"OPEN",
        "source_identity_and_status_only":result
    }

def test_guards():
    from pycparser import c_parser
    get=lambda expr:c_parser.CParser().parse("int f(){return ("+expr+");}").ext[0].body.block_items[0].expr
    legit=make_ast(get("(x + 1 <= y) && (y>=0)"),{"x":0,"y":1})
    assert legit[1]=="BOOL" and depth(legit[0])>=3
    for expression,reason in [("ghost >= 0","UNBOUND_VARIABLE"),
                              ("x + (x<0) >= 0","ARITH_SORT_ERROR")]:
        try:make_ast(get(expression),{"x":0})
        except InvalidTypedAST as e:
            if str(e)!=reason:raise AssertionError(f"WRONG_NEGATIVE_REASON: {e}")
        else:raise AssertionError("INVALID_AST_ALLOWED")
    return True

if __name__=="__main__":
    assert test_guards()
    p=argparse.ArgumentParser()
    p.add_argument("--workbook",required=True,type=Path)
    p.add_argument("--dataset",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    x=collect(a.workbook,a.dataset)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(x,indent=2)+"\n")
    print("Q3N_DATA_TRAIN",x["split_census"]["TRAIN"])
    print("Q3N_DATA_EVAL",x["split_census"]["HELDOUT"])
    print("Q3N_RESULT",x["status"])
    print("Q3N_CATEGORIES",x["status_counts_all_source_files"])
    print("Q1_TO_Q7",x["global_q1_q7"])
