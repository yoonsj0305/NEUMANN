"""Post-opened generic typed Horn-graph IR & losslessness audit, NOT neural Q3.

The first frozen model outcomes were already retained in run 39040534264.
This separately tests whether a source-neutral parser can represent all original
rules, including varying relation counts/ADTs, without semantic information loss.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

import z3

REV="e5a86a1ad252fe1df75e06814769ec1d14540032"
FIRST_FROZEN_RUN="39040534264"
SOURCES=("inc-max-2-base3-safe.smt2","lists-3-inc-some-safe.smt2")

def digest(raw):
    return {
      "sha256":hashlib.sha256(raw).hexdigest(),
      "git_blob_sha1":hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest(),
      "bytes":len(raw)}

def flatten(f):
    if z3.is_and(f):
        out=[]
        for c in f.children():out.extend(flatten(c))
        return out
    return [f]

def quantifier_body(expr,index):
    if z3.is_quantifier(expr):
        if not expr.is_forall():raise ValueError("NON_UNIVERSAL_QUANTIFIER")
        xs=[z3.Const(f"ir_var_{index}_{j}",expr.var_sort(expr.num_vars()-1-j)) for j in range(expr.num_vars())]
        return z3.substitute_vars(expr.body(),*xs),xs
    return expr,[]

def split_implication(body):
    if z3.is_implies(body):
        p,h=body.children()
        return flatten(p),h
    # A Horn fact without implication is equivalent to true => head.
    return [],body

def bool_uf(expr):
    return (z3.is_app(expr) and expr.decl().kind()==z3.Z3_OP_UNINTERPRETED
            and expr.sort().kind()==z3.Z3_BOOL_SORT)

def eligible_relation(expr,variable_names):
    return bool_uf(expr) and expr.decl().name() not in variable_names

def reconstruct_all(raw):
    original=list(z3.parse_smt2_string(raw.decode("utf-8")))
    if not original:raise ValueError("EMPTY_ORIGINAL")
    prepared=[]
    relations={}
    for i,assertion in enumerate(original):
        body,vars_=quantifier_body(assertion,i)
        atoms,head=split_implication(body)
        prepared.append((assertion,body,atoms,head,vars_))
        if eligible_relation(head,{v.decl().name() for v in vars_}):
            d=head.decl()
            relations[d.name()]=d
    # A relation can appear in body but not as head in a malformed original.
    # Treat that as unsupported to avoid silently dropping constraints.
    rows=[]
    edges=set()
    classifications={"fact":0,"step":0,"goal":0}
    mutcontrol=None
    for i,(assertion,body,atoms,head,vars_) in enumerate(prepared):
        source_vars={v.decl().name() for v in vars_}
        calls=[]
        guards=[]
        for atom in atoms:
            if eligible_relation(atom,source_vars):
                if atom.decl().name() not in relations:
                    raise ValueError("BODY_RELATION_WITHOUT_DEFINITION")
                calls.append(atom)
            else:guards.append(atom)
        head_label=(head.decl().name() if eligible_relation(head,source_vars) else
                    "FALSE" if z3.is_false(head) else "NON_RELATION")
        if head_label=="NON_RELATION":
            raise ValueError("NON_HORN_HEAD")
        classification=("goal" if head_label=="FALSE" else "fact" if not calls else "step")
        classifications[classification]+=1
        for call in calls:edges.add((call.decl().name(),head_label))
        # Recompose from actual original term children, without deleting guards.
        rebuilt=z3.Implies(z3.And(*(guards+calls)),head)
        s=z3.Solver()
        s.set(timeout=3000)
        s.add(z3.Xor(body,rebuilt))
        outcome=str(s.check())
        if outcome!="unsat":
            raise ValueError(f"ORIGINAL_MEANING_NOT_PRESERVED_{i}_{outcome}")
        if mutcontrol is None and head_label!="FALSE":
            # An intentionally false alternative head is NOT semantics preserving
            # if the original rule can fire. Preserves all original conditions.
            corrupted=z3.Implies(z3.And(*(guards+calls)),z3.BoolVal(False))
            mutation=z3.Solver()
            mutation.set(timeout=3000)
            mutation.add(z3.Xor(body,corrupted))
            control=str(mutation.check())
            if control=="sat":
                mutcontrol={"original_clause_index":i,"corrupted_head":"false",
                            "xor_result":control}
        rows.append({
          "original_clause_index":i,
          "universal_variables":len(vars_),
          "body_relation_calls":[c.decl().name() for c in calls],
          "guard_atoms":len(guards),
          "head_relation":head_label,
          "kind":classification,
          "body_horn_sha256":hashlib.sha256(body.sexpr().encode()).hexdigest(),
          "lossless_quantifier_free_xor":"unsat"
        })
    if mutcontrol is None:
        raise ValueError("NO_POSITIVE_FALSIFICATION_CONTROL")
    graph=[{
      "name":name, "arity":d.arity(),
      "arg_sorts":[str(d.domain(i)) for i in range(d.arity())],
      "range_sort":str(d.range())
      } for name,d in sorted(relations.items())]
    return {
      "relations":graph, "relation_count":len(graph),
      "original_clause_count":len(original),
      "original_xor_unsat":len(rows),
      "graph_edges":[list(e) for e in sorted(edges)],
      "classifications":classifications,
      "nonlinear_premise_rules":sum(len(r["body_relation_calls"])>=2 for r in rows),
      "non_int_argument_positions":sum(
          arg!="Int" for rel in graph for arg in rel["arg_sorts"]),
      "typed_rules":rows,
      "negative_control":mutcontrol,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True,type=Path)
    opts=p.parse_args()
    report={"study":"POSTOPEN_EXTERNAL_TYPED_HORN_GRAPH_IR",
      "prior_first_frozen_run":FIRST_FROZEN_RUN,"upstream_commit":REV,
      "original_sources_now_opened":True,"model_calls":0,
      "global_q1_q7":"OPEN","results":[]}
    for name in SOURCES:
        url=f"https://raw.githubusercontent.com/chc-comp/rust-horn/{REV}/{name}"
        try:
            with urllib.request.urlopen(url,timeout=30) as f:raw=f.read()
            rec={"source":name,"identity":digest(raw),"status":"ABSTAIN"}
            rec.update(reconstruct_all(raw))
            rec["status"]="TYPED_GRAPH_ORIGINAL_RULES_LOSSLESS"
        except Exception as e:
            rec={"source":name,"status":"BLOCKED_OR_ERROR",
                 "error":f"{type(e).__name__}: {str(e)[:400]}"}
        report["results"].append(rec)
    report["total_verified_original_rules"]=sum(
        x.get("original_xor_unsat",0) for x in report["results"])
    opts.output.parent.mkdir(parents=True,exist_ok=True)
    opts.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("TYPED_IR",[(r["source"],r["status"],r.get("relation_count"),r.get("original_clause_count"),r.get("non_int_argument_positions")) for r in report["results"]])
    print("XOR_UNSAT",report["total_verified_original_rules"],"GLOBAL",report["global_q1_q7"])
if __name__=="__main__":main()
