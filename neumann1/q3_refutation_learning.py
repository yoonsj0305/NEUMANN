"""Q3 SOURCE-only self-refutation teacher construction, no domain solvers.

An independently SOURCE-certified model-authored program supplies the
positive executable method. Perturb only its generic Python AST to create
falsifiable hypotheses; execute each variant under the SAME locked sandbox
on original SOURCE, observe real counterexamples, and train the SAME
neural policy to repair to the certified program. Target gold is absent.

AST perturbations are *negative observations*, not a new program-synthesis
operator library or claims that a fixed edit set can solve novel targets.
"""
from __future__ import annotations
import ast
import copy
import hashlib
import json

from .open_program_inventor import validate_code, UnsafeProposal
from .q3_prompt_contract import source_revision_prompt


_MUTATIONS=(
    "literal_shift", "invert_comparison", "swap_arithmetic",
    "invert_guard", "swap_builtin", "return_none",
)


def _mutate(program, kind):
    tree=ast.parse(validate_code(program))
    changed=False
    for node in ast.walk(tree):
        if changed:
            break
        if kind=="literal_shift" and isinstance(node,ast.Constant):
            if type(node.value) is int and abs(node.value)<100000:
                node.value=node.value+1
                changed=True
            elif type(node.value) is str and 0<len(node.value)<=20:
                node.value=node.value+"_"
                changed=True
        elif kind=="invert_comparison" and isinstance(node,ast.Compare):
            flip={ast.Eq:ast.NotEq,ast.NotEq:ast.Eq,
                  ast.Lt:ast.GtE,ast.GtE:ast.Lt,
                  ast.Gt:ast.LtE,ast.LtE:ast.Gt,
                  ast.In:ast.NotIn,ast.NotIn:ast.In}
            if node.ops and type(node.ops[0]) in flip:
                node.ops[0]=flip[type(node.ops[0])]()
                changed=True
        elif kind=="swap_arithmetic" and isinstance(node,ast.BinOp):
            swap={ast.Add:ast.Sub,ast.Sub:ast.Add,
                  ast.Mult:ast.Add,ast.Mod:ast.FloorDiv,
                  ast.FloorDiv:ast.Mod}
            if type(node.op) in swap:
                node.op=swap[type(node.op)]()
                changed=True
        elif kind=="invert_guard" and isinstance(node,ast.If):
            node.test=ast.UnaryOp(op=ast.Not(),operand=node.test)
            changed=True
        elif kind=="swap_builtin" and isinstance(node,ast.Call):
            if isinstance(node.func,ast.Name):
                swap={"min":"max","max":"min","sum":"len",
                      "all":"any","any":"all"}
                if node.func.id in swap:
                    node.func.id=swap[node.func.id]
                    changed=True
        elif kind=="return_none" and isinstance(node,ast.Return):
            node.value=ast.Constant(value=None)
            changed=True
    if not changed:
        return None
    ast.fix_missing_locations(tree)
    result=ast.unparse(tree)
    try:
        return validate_code(result)
    except (TypeError,ValueError,UnsafeProposal):
        return None


def source_refutation_episodes(rows,memory,runner,*,max_per_teacher=2):
    """Return source-verifier-grounded (prompt, code, provenance) pairs.

    All self-teacher programs were recertified in SourceMethodMemory before
    this call. Training examples deliberately exclude their own methods
    from the library. A mutant with no observed source falsification cannot
    count as a repair episode.
    """
    if not 1<=max_per_teacher<=6:
        raise ValueError("bounded SOURCE method-refutation budget")
    from .q3_trainable_code_policy import contextual_training_prompt
    episodes=[]
    for teacher in rows:
        pid=teacher.get("original_id",teacher.get("source_id"))
        if pid is None:
            raise ValueError("source identity required")
        pid=str(pid)
        if not pid.startswith("source-teacher/"):
            pid="source-teacher/"+pid
        if pid not in {e.source_id for e in memory.episodes}:
            raise ValueError("not SOURCE-certified teaching episode")
        base=contextual_training_prompt(teacher,memory)
        pairs=teacher["pairs"]
        train=pairs[:6]
        check=pairs[6:]
        if not train or not check:
            raise ValueError("disjoint original SOURCE verifier required")
        candidates=[]
        for kind in _MUTATIONS:
            broken=_mutate(teacher["program"],kind)
            if not broken:
                continue
            outcome=runner.evaluate(broken,[x for x,y in pairs])
            if (outcome.status not in ("EXECUTED","EXECUTED_WITH_ERRORS")
                    or len(outcome.outputs)!=len(pairs)
                    or len(outcome.errors)!=len(pairs)):
                continue
            correct_train=sum(
                err is None and got==y
                for got,err,(_,y) in zip(
                    outcome.outputs[:len(train)],
                    outcome.errors[:len(train)],train))
            correct_check=sum(
                err is None and got==y
                for got,err,(_,y) in zip(
                    outcome.outputs[len(train):],
                    outcome.errors[len(train):],check))
            if correct_train==len(train) and correct_check==len(check):
                continue  # no real counterexample: not negative evidence
            if correct_train==len(train):
                kind_of_failure="independent_source"
                witness=[
                    {"source_input":x,"source_expected":y,
                     "previous_observed":got,"runtime_error":err}
                    for got,err,(x,y) in zip(
                        outcome.outputs[len(train):],
                        outcome.errors[len(train):],check)
                    if err is not None or got!=y]
            else:
                kind_of_failure="source"
                witness=[
                    ({"input":x,"expected":y,"runtime_failure":err}
                     if err is not None else
                     {"input":x,"expected":y,"got":got})
                    for got,err,(x,y) in zip(
                        outcome.outputs[:len(train)],
                        outcome.errors[:len(train)],train)
                    if err is not None or got!=y]
            if not witness:
                continue
            prompt=source_revision_prompt(
                base,broken,witness[:3],kind=kind_of_failure)
            candidates.append({
                "prompt":prompt,"program":teacher["program"],
                "original_source_id":pid,"negative_program":broken,
                "negative_sha256":hashlib.sha256(
                    broken.encode()).hexdigest(),
                "failure_kind":kind_of_failure,
                "train_correct":correct_train,
                "train_total":len(train),
                "source_only":True,
                "mutation_kind":kind,
                "witness_sha256":hashlib.sha256(
                    json.dumps(witness,sort_keys=True,default=str).encode()
                    ).hexdigest(),
            })
        # Sort by closeness, not target gold. Partial correctness is valuable:
        # the training policy should preserve working computations.
        candidates.sort(key=lambda x:(
            -x["train_correct"],x["mutation_kind"],
            x["negative_sha256"]))
        episodes.extend(candidates[:max_per_teacher])
    return episodes
