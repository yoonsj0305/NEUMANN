"""Q3: counterexample-guided repair of model-authored Python programs.

Unlike source-specific hand-coded algorithms, edits are *AST structural*
mutations applicable to any program expressed in the safe open Python core.
SOURCE train and an input-disjoint SOURCE verifier are the only observations.
Test gold, hidden reference programs, problem IDs, and human-chosen target
operator families are not used.

There are two falsifiable interventions:
  1. Search from failed model programs for a SOURCE-valid causal repair.
  2. Minimize SOURCE-valid but over-conditioned programs under code-length MDL.

A small learned proposal policy updates action utilities from actual changes
in SOURCE fit across tasks. This is true online policy parameter adaptation,
NOT neural generator weight learning or unrestricted Q3/Q6 proof. Preserve
both uniform and adaptive arms in first-original comparisons.

All generated code is re-validated and executed only in a locked Docker
runtime. No Docker => abstain, never in-process exec of model code.
"""
from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
import hashlib
import math
from typing import Iterable

from .open_program_inventor import UnsafeProposal, validate_code


_COMPARISONS=(ast.Eq,ast.NotEq,ast.Lt,ast.LtE,ast.Gt,ast.GtE)
_STABLE_CALLS=frozenset((
    "abs","all","any","bool","chr","dict","divmod","enumerate","filter",
    "float","int","isinstance","len","list","map","max","min","ord",
    "pow","range","reversed","round","set","sorted","str","sum","tuple",
    "zip",
))
_EXCLUDED=(
    ast.NamedExpr,ast.Yield,ast.YieldFrom,ast.Await,
    ast.ListComp,ast.SetComp,ast.DictComp,ast.GeneratorExp,
)


def _complexity(code:str)->tuple[int,int,int]:
    """MDL-like tie-break; not a claim to posterior probability."""
    t=ast.parse(code)
    nodes=tuple(ast.walk(t))
    branching=sum(isinstance(n,(ast.If,ast.IfExp,ast.While))
                  for n in nodes)
    return (len(nodes)+2*branching,len(code),branching)


def _references_only_input(expr:ast.AST)->bool:
    """No unbound local loop indices, helper state or source-specific names."""
    if any(isinstance(n,_EXCLUDED) for n in ast.walk(expr)):
        return False
    names={n.id for n in ast.walk(expr) if isinstance(n,ast.Name)}
    return names.issubset(_STABLE_CALLS|{"x"})


def _replace_expr(root,ordinal,replacement):
    cloned=copy.deepcopy(root)
    target=[x for x in ast.walk(cloned) if isinstance(x,ast.expr)][ordinal]
    if isinstance(target,ast.Name) and not isinstance(target.ctx,ast.Load):
        return None
    for node in ast.walk(cloned):
        for field,value in ast.iter_fields(node):
            if value is target:
                setattr(node,field,copy.deepcopy(replacement))
                ast.fix_missing_locations(cloned)
                return cloned
            if isinstance(value,list):
                for i,child in enumerate(value):
                    if child is target:
                        value[i]=copy.deepcopy(replacement)
                        ast.fix_missing_locations(cloned)
                        return cloned
    return None


def _replace_stmt(root,ordinal,statements):
    cloned=copy.deepcopy(root)
    target=[x for x in ast.walk(cloned) if isinstance(x,ast.stmt)][ordinal]
    for node in ast.walk(cloned):
        for field,value in ast.iter_fields(node):
            if isinstance(value,list):
                for i,child in enumerate(value):
                    if child is target:
                        value[i:i+1]=copy.deepcopy(statements)
                        ast.fix_missing_locations(cloned)
                        return cloned
    return None


def _variants(code:str,max_per_category=64)->Iterable[tuple[str,str]]:
    """Generic AST rewriting, never task/problem-specific operators."""
    base=ast.parse(code)
    all_expr=[e for e in ast.walk(base) if isinstance(e,ast.expr)]
    # Reuse only expressions whose free variables are valid at any return.
    subtree=[e for e in all_expr
             if isinstance(e,(ast.Call,ast.Subscript,ast.BinOp,
                              ast.Compare,ast.IfExp,ast.UnaryOp,
                              ast.BoolOp,ast.Name))
             and _references_only_input(e)]
    seen={code}
    def emit(action,tree):
        if tree is None:return None
        try:
            out=validate_code(ast.unparse(tree))
        except (UnsafeProposal,ValueError,SyntaxError,TypeError):
            return None
        if out in seen:return None
        seen.add(out)
        return (action,out)
    count={}
    def admitted(action):
        count[action]=count.get(action,0)+1
        return count[action]<=max_per_category
    # (A) Remove unjustified conditional branches and statements.
    for i,e in enumerate(all_expr):
        alternatives=[]
        if isinstance(e,ast.IfExp):
            alternatives=[("drop_condition_true",e.body),
                          ("drop_condition_false",e.orelse)]
        elif isinstance(e,ast.BoolOp):
            alternatives=[("drop_boolean_clause",v) for v in e.values]
        elif isinstance(e,ast.BinOp):
            alternatives=[("drop_arithmetic_side",e.left),
                          ("drop_arithmetic_side",e.right)]
        elif isinstance(e,ast.Call):
            alternatives=[("drop_call",v) for v in e.args]
        elif isinstance(e,ast.UnaryOp):
            alternatives=[("drop_unary",e.operand)]
        elif isinstance(e,ast.Compare):
            alternatives=[("drop_comparison",e.left)]
        for action,replacement in alternatives:
            if not admitted(action):continue
            item=emit(action,_replace_expr(base,i,replacement))
            if item is not None:yield item
        if isinstance(e,ast.Compare) and len(e.ops)==1:
            for comparator in _COMPARISONS:
                if type(e.ops[0]) is comparator:continue
                if not admitted("revise_comparison"):continue
                clone=copy.deepcopy(base)
                expressions=[x for x in ast.walk(clone)
                             if isinstance(x,ast.expr)]
                target=expressions[i]
                target.ops=[comparator()]
                item=emit("revise_comparison",clone)
                if item is not None:yield item
    statements=[n for n in ast.walk(base) if isinstance(n,ast.stmt)]
    for i,stmt in enumerate(statements):
        if isinstance(stmt,ast.If):
            for action,pieces in (
                    ("remove_if_guard",stmt.body),
                    ("remove_if_guard",stmt.orelse)):
                if not pieces or not admitted(action):continue
                item=emit(action,_replace_stmt(base,i,pieces))
                if item is not None:yield item
        if isinstance(stmt,ast.Return) and stmt.value is not None:
            for e in subtree[:max_per_category]:
                if not admitted("select_inferred_subexpression"):break
                clone=copy.deepcopy(base)
                j=[n for n in ast.walk(clone)
                   if isinstance(n,ast.stmt)][i]
                j.value=copy.deepcopy(e)
                item=emit("select_inferred_subexpression",clone)
                if item is not None:yield item


@dataclass(frozen=True)
class Repair:
    status:str
    program:str|None
    program_sha256:str|None
    source_checked:int
    source_best:int
    independent_correct:int
    program_cost:int|None
    action:str|None
    policy_updates:int


class SourcePolicyLearner:
    """On-line learning of general AST edit utility from SOURCE outcomes.

    Non-neural lightweight parameter learning. It cannot replace the neural
    proposal generator and is NOT evidence that its weights improved.
    """
    def __init__(self,*,adapt=True):
        self.adapt=bool(adapt)
        self.frozen=False
        self.weights={}
        self.updates=0

    def freeze(self):
        """Retain learned ranking, prohibit updates on heldout task sources."""
        self.frozen=True

    def rank(self,variants):
        def score(item):
            action,src=item
            estimate=self.weights.get(action,0.0) if self.adapt else 0.0
            # Lexical tie-break keeps first candidates deterministic.
            return (-estimate,_complexity(src),action,src)
        return sorted(variants,key=score)

    def learn(self,action,old_fit,new_fit,*,source_total=1,
              independent_verified=None,source_executed=True):
        """Update from genuine disjoint SOURCE evidence, not train fit alone.

        A training-fit gain is a weak search hint (bounded by 0.1); passing
        or failing independent SOURCE dominates that hint by 10x. Missing
        oracle/sandbox evidence is never counted as a failed generalization.
        This is a prior over useful edits, NOT a guarantee on TARGET data.
        """
        if not self.adapt or self.frozen or not source_executed:return
        if not 1<=source_total<=32:
            raise ValueError("bounded source_total required")
        progress=(new_fit-old_fit)/source_total
        evidence=(1.0 if independent_verified is True
                  else -1.0 if independent_verified is False else 0.0)
        reward=0.1*progress+evidence
        self.weights[action]=0.85*self.weights.get(action,0.0)+0.15*reward
        self.updates+=1


class SourceProgramReviser:
    def __init__(self,runner,*,max_source_evals=48,policy=None):
        if not 1<=max_source_evals<=2000:
            raise ValueError("bounded source evaluation budget")
        self.runner=runner
        self.max_source_evals=max_source_evals
        self.policy=policy if policy is not None else SourcePolicyLearner()

    def repair(self,attempts,train,*,independent_source_checks,
               initial_source_verified=None):
        """SOURCE-only correct/shorten with exact disjoint verifier."""
        tr=tuple(train)
        checks=tuple(independent_source_checks)
        if not tr or not checks or len(tr)>32 or len(checks)>32:
            raise ValueError("bounded train and disjoint source required")
        tr_set={str(x) for x,y in tr}
        if tr_set & {str(x) for x,y in checks}:
            raise ValueError("disjoint source inputs required")
        verified=None
        best_cost=None
        best_action=None
        checked=0
        maxfit=0
        inputs=[x for x,y in tr]
        outputs=[y for x,y in tr]
        seen=set()
        seeds=[]
        for a in attempts:
            if not isinstance(getattr(a,"program",None),str):continue
            try:code=validate_code(a.program)
            except UnsafeProposal:continue
            if code not in seen:
                seen.add(code)
                seeds.append(code)
        if initial_source_verified is not None:
            try:
                code=validate_code(initial_source_verified)
                if code not in seen:seeds.insert(0,code)
            except UnsafeProposal:
                pass
        if not seeds:
            return Repair("ABSTAIN_NO_EXECUTABLE_SEED",None,None,0,0,0,
                          None,None,self.policy.updates)
        # Compare original certified hypothesis with edited hypotheses.
        for src in seeds:
            if checked>=self.max_source_evals:break
            result=self.runner.evaluate(src,inputs)
            checked+=1
            fit=0
            if result.status in ("EXECUTED","EXECUTED_WITH_ERRORS"):
                fit=sum(
                    err is None and expected==got
                    for expected,got,err in zip(outputs,result.outputs,
                                                result.errors))
            maxfit=max(maxfit,fit)
            if fit==len(tr):
                val=self.runner.evaluate(src,[x for x,y in checks])
                if val.status=="EXECUTED" and all(
                    got==y for got,(_,y) in zip(val.outputs,checks)):
                    cost=_complexity(src)
                    if best_cost is None or cost<best_cost:
                        verified=src
                        best_cost=cost
                        best_action="unchanged_model"
            candidates=self.policy.rank(list(_variants(src,max_per_category=36)))
            for action,candidate in candidates:
                if checked>=self.max_source_evals:break
                if candidate in seen:continue
                seen.add(candidate)
                result=self.runner.evaluate(candidate,inputs)
                checked+=1
                changed=0
                if result.status in ("EXECUTED","EXECUTED_WITH_ERRORS"):
                    changed=sum(
                        err is None and expected==got
                        for expected,got,err in zip(
                            outputs,result.outputs,result.errors))
                maxfit=max(maxfit,changed)
                independent_verified=None
                if changed==len(tr):
                    cv=self.runner.evaluate(
                        candidate,[x for x,y in checks])
                    if cv.status=="EXECUTED":
                        independent_verified=all(
                            got==y for got,(_,y) in zip(cv.outputs,checks))
                    # A sandbox failure is UNKNOWN, not a negative label.
                self.policy.learn(
                    action,fit,changed,source_total=len(tr),
                    independent_verified=independent_verified,
                    source_executed=result.status in (
                        "EXECUTED","EXECUTED_WITH_ERRORS"))
                if independent_verified is not True:continue
                cost=_complexity(candidate)
                if best_cost is None or cost<best_cost:
                    verified=candidate
                    best_cost=cost
                    best_action=action
        if verified is None:
            return Repair("ABSTAIN_NO_GENERALIZABLE_SOURCE_REPAIR",
                          None,None,checked,maxfit,0,
                          None,None,self.policy.updates)
        return Repair(
            "SOURCE_VERIFIED_REPAIRED_PROGRAM",verified,
            hashlib.sha256(verified.encode()).hexdigest(),
            checked,maxfit,len(checks),best_cost[0],best_action,
            self.policy.updates)
