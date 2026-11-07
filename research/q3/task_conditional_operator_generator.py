"""Q3 essential repair: make learned typed-AST proposals depend on problem semantics.

The original Generator from PR #686 had a provable information bottleneck:
features(type,depth,collision,count,scope) ignored the actual transition
program.  For identical meta-inputs its initial proposal distribution is
identical on *all* different tasks, including incompatible operators.

We keep typed primitive AST composition and real gradient updates, but
condition every production logit on the public transition RHS syntax tree.
No hidden correct invariant, candidate target, teacher label, or held-out
result is part of the context.

This is Q3 CORE INFRASTRUCTURE, not autonomous invention proof.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Callable

from research.q3.generative_typed_operator_policy import (
    Generator, PRODUCTIONS, learn_from_independent_checker
)

TOKENS=("select","src","dst","+", "-", "*", "ite", "store",
        "0","1","2","-1","cursor","bound","base_src","base_dst")
VOCAB=frozenset(TOKENS)|{"(",")","j","true","false"}
TOKEN_PATTERN=re.compile(r"\(|\)|[^\s()]+")


def tokens_from_public_rhs(rhs:str)->tuple[str,...]:
    """Strict parser contract. Unknown operators must not be silently mapped."""
    if not isinstance(rhs,str) or len(rhs)>4000:
        raise ValueError("INVALID_PUBLIC_TRANSITION_RHS")
    items=tuple(TOKEN_PATTERN.findall(rhs))
    if not items or len(items)>400:
        raise ValueError("INVALID_PUBLIC_TRANSITION_TOKENS")
    if any(token not in VOCAB for token in items):
        raise ValueError("UNSUPPORTED_OBSERVED_SEMANTIC_OPERATOR")
    stack=0
    for token in items:
        if token=="(":
            stack+=1
        elif token==")":
            stack-=1
            if stack<0:
                raise ValueError("MALFORMED_PUBLIC_TRANSITION")
    if stack:
        raise ValueError("MALFORMED_PUBLIC_TRANSITION")
    return items


HASHED_STRUCTURAL_DIM=64

def public_rhs_tree(rhs:str):
    """Parse *ordered* observed transition tree, preserving operand roles.

    Bag of tokens alone confuses (sub src 1) with (sub 1 src), exactly the
    kind of semantic information collision that broke Q3 before. This tree
    representation is NOT a target solution or supervisor.
    """
    toks=tokens_from_public_rhs(rhs)
    stack=[]
    root=[]
    for token in toks:
        if token=="(":
            new=[]
            if stack: stack[-1].append(new)
            else: root.append(new)
            stack.append(new)
        elif token==")":
            if not stack: raise ValueError("UNMATCHED_RPAREN")
            stack.pop()
        else:
            if stack:stack[-1].append(token)
            else:root.append(token)
    if stack or len(root)!=1:
        raise ValueError("NOT_ONE_PUBLIC_TRANSITION_EXPRESSION")
    def validate(node):
        if isinstance(node,str):return
        if not node or not isinstance(node[0],str):
            raise ValueError("MALFORMED_PUBLIC_TRANSITION_TREE")
        ops={"+","-","*","select","store","ite"}
        if node[0] not in ops:
            raise ValueError("UNSUPPORTED_PUBLIC_TRANSITION_OPERATOR")
        arity={"+":2,"-":2,"*":2,"select":2,"store":3,"ite":3}
        if len(node)!=arity[node[0]]+1:
            raise ValueError("INVALID_PUBLIC_TRANSITION_ARITY")
        for child in node[1:]:validate(child)
    validate(root[0])
    return root[0]


def hashed_tree_features(tree)->tuple[float,...]:
    """Fixed-width structural paths, not unordered bag. SHA256 stable across hosts."""
    acc=[0.]*HASHED_STRUCTURAL_DIM
    def walk(node,ancestor=()):
        head=node if isinstance(node,str) else node[0]
        path=("/".join(ancestor)+"|"+head).encode("utf-8")
        d=hashlib.sha256(path).digest()
        acc[int.from_bytes(d[:4],"big")%HASHED_STRUCTURAL_DIM]+=1.
        if not isinstance(node,str):
            for i,ch in enumerate(node[1:]):
                walk(ch,ancestor+((head+"["+str(i)+"]"),))
    walk(tree)
    return tuple(min(1.0,x/4.0) for x in acc)


@dataclass(frozen=True)
class ObservedProblem:
    transition_rhs: str
    collision: bool
    failed_proofs: int

    def __post_init__(self):
        tokens_from_public_rhs(self.transition_rhs)
        if not isinstance(self.collision,bool):
            raise ValueError("INVALID_COLLISION_FLAG")
        if not isinstance(self.failed_proofs,int) or self.failed_proofs<0:
            raise ValueError("INVALID_CHECKER_HISTORY")

    def sha(self)->str:
        raw=json.dumps({"rhs":self.transition_rhs,"collision":self.collision,
                        "failed":self.failed_proofs},sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()

    def vector(self)->tuple[float,...]:
        tokens=tokens_from_public_rhs(self.transition_rhs)
        lexical=tuple(min(1.,tokens.count(tok)/4.) for tok in TOKENS)
        return lexical + hashed_tree_features(public_rhs_tree(self.transition_rhs))


@dataclass(frozen=True)
class BehavioralProblem:
    """Q3 black-box observed I/O, no source transition or correct AST exposed.

    Only independently measured input/output examples are passed to the actor.
    The hidden semantic program belongs exclusively to the verifier. This
    avoids leaking the target source RHS to a trivial AST-copy classical path.
    """
    observations: tuple[tuple[int,int], ...]
    collision: bool = True
    failed_proofs: int = 0

    def __post_init__(self):
        if (not isinstance(self.observations,tuple)
            or not 8 <= len(self.observations) <= 256
            or any(not isinstance(row,tuple) or len(row)!=2
                   or any(type(v) is not int or abs(v)>100000 for v in row)
                   for row in self.observations)):
            raise ValueError("INVALID_Q3_BEHAVIORAL_OBSERVATIONS")
        if not isinstance(self.collision,bool) or type(self.failed_proofs) is not int or self.failed_proofs<0:
            raise ValueError("INVALID_Q3_BEHAVIORAL_METADATA")

    def sha(self)->str:
        raw=json.dumps({"examples":self.observations,"collision":self.collision,
                        "failed":self.failed_proofs},sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()

    def vector(self)->tuple[float,...]:
        import math
        x=[float(a) for a,b in self.observations]
        y=[float(b) for a,b in self.observations]
        n=len(x)
        mean=lambda v:sum(v)/n
        # Generic moments: no target operator, source code or AST teacher.
        mu=mean(x);mv=mean(y)
        sx=math.sqrt(mean([(z-mu)**2 for z in x])+1.)
        sy=math.sqrt(mean([(z-mv)**2 for z in y])+1.)
        corr=mean([(a-mu)*(b-mv) for a,b in zip(x,y)])/(sx*sy)
        moments=[
            1., min(n/32.,1.), math.tanh(mu/10.),
            math.tanh(mv/10.), math.tanh(sx/10.), math.tanh(sy/10.),
            max(-1.,min(1.,corr)),
            math.tanh(mean([a*b for a,b in zip(x,y)])/50.),
            math.tanh(mean([(a-b)**2 for a,b in zip(x,y)])/30.),
            math.tanh(mean([(a+b)**2 for a,b in zip(x,y)])/30.),
            math.tanh(min(x)/10.),math.tanh(max(x)/10.),
            math.tanh(min(y)/10.),math.tanh(max(y)/10.),
            math.tanh(mean([abs(a) for a in x])/10.),
            math.tanh(mean([abs(b) for b in y])/10.)
        ]
        structural=[0.]*HASHED_STRUCTURAL_DIM
        for a,b in self.observations:
            # Hashed observable numeric cooccurrences, without a gold formula.
            key=f"{a}:{b}".encode()
            index=int.from_bytes(hashlib.sha256(key).digest()[:4],"big")%HASHED_STRUCTURAL_DIM
            structural[index]+=1./n
        return tuple(moments)+tuple(structural)


class TaskConditionalGenerator(Generator):
    """Own-weight autoregressive AST policy with verifiable semantic conditioning."""

    def __init__(self,seed:int=23):
        super().__init__(seed=seed)
        self.observation:ObservedProblem|None=None
        self.weights={
           kind:[[self.rng.gauss(0,0.02) for _ in range(6+len(TOKENS)+HASHED_STRUCTURAL_DIM)]
                for _ in productions]
           for kind, productions in PRODUCTIONS.items()
        }

    def set_observation(self,problem:ObservedProblem)->None:
        if not isinstance(problem,(ObservedProblem,BehavioralProblem)):
            raise ValueError("TASK_SEMANTICS_REQUIRED")
        self.observation=problem

    def features(self,kind,depth,max_depth,collision,failed_proofs,quantifier_open):
        if self.observation is None:
            raise ValueError("TASK_SEMANTICS_REQUIRED")
        if collision != self.observation.collision or failed_proofs != self.observation.failed_proofs:
            raise ValueError("TASK_CONTEXT_AND_CHECKER_HISTORY_DISAGREE")
        base=Generator.features(kind,depth,max_depth,collision,failed_proofs,quantifier_open)
        return base+self.observation.vector()

    def sample_observed(self,problem:ObservedProblem,*,root_kind:str="Bool",
                        bound_index:bool=False,max_depth:int=6,max_nodes:int=96):
        self.set_observation(problem)
        return self.sample(collision=problem.collision,
              failed_proofs=problem.failed_proofs,max_depth=max_depth,
              max_nodes=max_nodes,root_kind=root_kind,bound_index=bound_index)

    def learn_observed(self,problem:ObservedProblem,checker:Callable,**kwargs):
        self.set_observation(problem)
        out=learn_from_independent_checker(self,checker,
             collision=problem.collision,failed_proofs=problem.failed_proofs,
             **kwargs)
        out["semantic_observation_sha256"]=problem.sha()
        out["task_semantic_features_in_logits"]=True
        out["direct_target_operator_labels_received"]=False
        out["Q3"]="OPEN"
        return out


def certify_original_blindness_pair():
    """Executable proof witness: baseline initial proposals ignore task identity.

    It is a no-go for *task-conditioned policy distributions*, NOT a theorem
    that task-blind random search can never find a candidate by chance.
    """
    a=ObservedProblem("(select src cursor)",True,0)
    b=ObservedProblem("(- (select src cursor) 1)",True,0)
    old_a=Generator(seed=61)
    old_b=Generator(seed=61)
    original_a=[old_a.sample(collision=True,failed_proofs=0,
                           max_depth=4,max_nodes=60)[0].to_data()
                for _ in range(24)]
    original_b=[old_b.sample(collision=True,failed_proofs=0,
                           max_depth=4,max_nodes=60)[0].to_data()
                for _ in range(24)]
    if original_a!=original_b:
        raise RuntimeError("BASELINE_NO_GO_WITNESS_INVALID")
    learned_a=TaskConditionalGenerator(seed=61)
    learned_b=TaskConditionalGenerator(seed=61)
    learned_a.set_observation(a)
    learned_b.set_observation(b)
    # Return underlying production logit difference, not unsupported
    # "task solved" evidence.
    fa=learned_a.features("Int",1,5,True,0,True)
    fb=learned_b.features("Int",1,5,True,0,True)
    diff=max(abs(x-y) for x,y in zip(fa,fb))
    if diff<=0:
        raise RuntimeError("SEMANTIC_CONDITIONING_COLLAPSED")
    return {"task_a_sha256":a.sha(),"task_b_sha256":b.sha(),
            "original_identical_first_24_proposals":True,
            "conditional_semantic_feature_difference_max":diff,
            "original_task_mutual_information_given_same_metadata":0,
            "new_policy_input_includes_public_transition_rhs":True,
            "Q3":"OPEN"}
