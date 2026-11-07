"""NEUMANN Q3 core: learn to GENERATE variable-length typed operator ASTs.

This module intentionally contains no COPY_PREFIX/ADD1/learned classifier,
no hardcoded target predicates, no teacher-produced correct operators, and no
target-source-specific code. The policy emits typed executable SMT ASTs by
composing primitive productions. A verifier callback supplies proof/CEGIS
feedback for gradient updates, with unknown results always rejected.

Important: this is a necessary generator interface, NOT a successful Q3
discovery. The human primitive grammar remains a strong source of inductive
bias. Novel ability vs full equal-rights GP/CEGIS on unseen originals must
be independently demonstrated before Q3 can be marked PASS.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import time
from dataclasses import dataclass
from typing import Callable

# No target-answer macro. One node at a time can synthesize a new typed
# algebraic or quantified relation, rather than pick a prewritten operator.
# j is bound only by a forall node. A candidate without a binder may still
# be a valid predicate, but is not called a proof of any loop invariant.
PRODUCTIONS = {
    "Int": (
        ("zero", ()),
        ("one", ()),
        ("cursor", ()),
        ("bound", ()),
        ("base_dst", ()),
        ("base_src", ()),
        ("j", ()),
        ("add", ("Int", "Int")),
        ("sub", ("Int", "Int")),
        ("read_src", ("Int",)),
        ("read_dst", ("Int",)),
    ),
    "Bool": (
        ("eq", ("Int", "Int")),
        ("le", ("Int", "Int")),
        ("lt", ("Int", "Int")),
        ("and", ("Bool", "Bool")),
        ("implies", ("Bool", "Bool")),
        ("forall", ("Bool",)),
    ),
}
BY_NAME = {kind: {name: children for name, children in rows}
           for kind, rows in PRODUCTIONS.items()}
DIM = 6


@dataclass(frozen=True)
class AST:
    kind: str
    name: str
    children: tuple["AST", ...] = ()

    def to_data(self):
        return [self.kind, self.name, [c.to_data() for c in self.children]]

    def to_smt(self):
        v = [c.to_smt() for c in self.children]
        if self.name in ("zero", "one"):
            return "0" if self.name == "zero" else "1"
        if self.name in ("cursor", "bound", "base_dst", "base_src", "j"):
            return self.name
        if self.name == "add":
            return f"(+ {v[0]} {v[1]})"
        if self.name == "sub":
            return f"(- {v[0]} {v[1]})"
        if self.name in ("read_src", "read_dst"):
            arr = "src" if self.name == "read_src" else "dst"
            return f"(select {arr} {v[0]})"
        if self.name in ("eq", "le", "lt"):
            symbol = {"eq": "=", "le": "<=", "lt": "<"}[self.name]
            return f"({symbol} {v[0]} {v[1]})"
        if self.name in ("and", "implies"):
            symbol = "and" if self.name == "and" else "=>"
            return f"({symbol} {v[0]} {v[1]})"
        if self.name == "forall":
            return f"(forall ((j Int)) {v[0]})"
        raise ValueError("UNKNOWN_OPERATOR")


def check_ast(node: AST, *, bound_j: bool = False, ceiling: int = 99) -> int:
    if not isinstance(node, AST):
        raise ValueError("INVALID_NODE")
    choices = BY_NAME.get(node.kind, {})
    if node.name not in choices:
        raise ValueError("UNKNOWN_TYPED_PRODUCTION")
    expected = choices[node.name]
    if len(expected) != len(node.children):
        raise ValueError("ARITY_MISMATCH")
    if node.name == "j" and not bound_j:
        raise ValueError("UNBOUND_INDEX")
    size = 1
    for child, kind in zip(node.children, expected):
        if child.kind != kind:
            raise ValueError("TYPE_MISMATCH")
        size += check_ast(child, bound_j=bound_j or node.name == "forall",
                          ceiling=ceiling)
    if size > ceiling:
        raise ValueError("AST_NODE_BUDGET_EXCEEDED")
    return size


def novelty_signature(ast: AST) -> dict:
    def walk(n):
        yield n.name
        for c in n.children:
            yield from walk(c)
    ops = list(walk(ast))
    return {
        "variable_nodes": len(ops),
        "has_quantifier": "forall" in ops,
        "has_both_array_reads": "read_src" in ops and "read_dst" in ops,
        "has_compositional_arithmetic": "add" in ops or "sub" in ops,
        "productions": len(set(ops)),
    }


def softmax(logits):
    m = max(logits)
    ex = [math.exp(x - m) for x in logits]
    s = sum(ex)
    return [x / s for x in ex]


class Generator:
    """Autoregressive typed AST generator with actual REINFORCE weight updates.

    The grammar is public and the same language must be given to classical
    comparators. Learned weights score each possible next production from
    observable failure context and partial-tree depth. No teacher AST targets.
    """
    def __init__(self, seed: int = 23):
        self.rng = random.Random(seed)
        self.weights = {
            kind: [[self.rng.gauss(0, 0.02) for _ in range(DIM)]
                   for _ in rules]
            for kind, rules in PRODUCTIONS.items()
        }
        self.ema = 0.0
        self.gradient_steps = 0

    def parameters_hash(self) -> str:
        raw = json.dumps(self.weights, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def features(kind, depth, max_depth, collision, failed_proofs, quantifier_open):
        # No target-answer label or source identity. Observable features only.
        return (1.0, float(collision), min(1., failed_proofs/12.0),
                depth/max(1, max_depth), float(kind == "Bool"),
                float(quantifier_open))

    def sample(self, *, collision: bool, failed_proofs: int,
               max_depth: int = 6, max_nodes: int = 96):
        if max_depth < 2 or max_depth > 15 or max_nodes < 3:
            raise ValueError("INVALID_SAMPLING_BUDGET")
        events = []
        def expand(kind, depth, scope):
            choices = PRODUCTIONS[kind]
            allowed = [
                i for i,(name,children) in enumerate(choices)
                if all(depth + 1 + (1 if child_kind == "Bool" else 0) <= max_depth
                       for child_kind in children)
                and (name != "j" or scope)
            ]
            if not allowed:
                raise ValueError("NO_TYPED_PRODUCTION")
            f = self.features(kind, depth, max_depth, collision, failed_proofs, scope)
            logits = [sum(w*x for w,x in zip(self.weights[kind][i], f))
                      for i in allowed]
            probabilities = softmax(logits)
            t = self.rng.random()
            p = 0.
            selected = allowed[-1]
            for idx, pr in zip(allowed, probabilities):
                p += pr
                if t <= p:
                    selected = idx
                    break
            name, children = choices[selected]
            events.append((kind, tuple(allowed), tuple(probabilities),
                           selected, f))
            return AST(kind, name,
                tuple(expand(c, depth+1, scope or name == "forall")
                      for c in children))
        root = expand("Bool", 0, False)
        check_ast(root, ceiling=max_nodes)
        return root, events

    def apply_feedback(self, events, reward: float, *, lr: float = 0.04):
        if not math.isfinite(reward) or not -1.0 <= reward <= 1.0:
            raise ValueError("INVALID_PROOF_REWARD")
        if not 0.0 < lr <= 0.2:
            raise ValueError("INVALID_LEARNING_RATE")
        advantage = reward - self.ema
        self.ema = 0.9*self.ema + 0.1*reward
        for kind, allowed, probs, selected, f in events:
            for i, pr in zip(allowed, probs):
                coefficient = ((1.0 if i == selected else 0.0) - pr)
                for k in range(DIM):
                    self.weights[kind][i][k] += lr * advantage * coefficient * f[k]
        self.gradient_steps += 1


def learn_from_independent_checker(
    model: Generator,
    checker: Callable[[AST], dict],
    *,
    episodes: int,
    collision: bool,
    failed_proofs: int,
    max_depth: int = 6,
    max_nodes: int = 96,
    max_seconds: float = 20.,
):
    """Train only using checker verdict and proof progress.

    Checker must return a dict: verdict in PROVED, CEX, UNKNOWN; and
    validated_fraction in [0,1] for independently checked obligations.
    False/unknown can NEVER be interpreted as Q3 success.
    """
    if not 1 <= episodes <= 100000 or not 0 < max_seconds <= 3600:
        raise ValueError("INVALID_RESOURCE_BUDGET")
    started = time.perf_counter()
    initial_sha = model.parameters_hash()
    total_calls = 0
    unknowns = 0
    counterexamples = 0
    proved = 0
    generated = set()
    recorded = []
    for episode in range(episodes):
        if time.perf_counter() - started >= max_seconds:
            break
        try:
            candidate, actions = model.sample(collision=collision,
                failed_proofs=failed_proofs,max_depth=max_depth,
                max_nodes=max_nodes)
        except ValueError:
            recorded.append({"attempt":episode,"status":"INVALID_TYPED_AST"})
            continue
        candidate_hash = hashlib.sha256(
            json.dumps(candidate.to_data(), separators=(",", ":")).encode()
        ).hexdigest()
        generated.add(candidate_hash)
        # A checker must be independent: feedback is only a number, never a
        # human-authored correct replacement expression or target macro.
        start = time.perf_counter()
        outcome = checker(candidate)
        verifier_ms = round((time.perf_counter()-start)*1000,3)
        status = outcome.get("verdict")
        fraction = outcome.get("validated_fraction")
        if status not in ("PROVED", "CEX", "UNKNOWN"):
            raise ValueError("INDEPENDENT_CHECKER_INVALID_VERDICT")
        if type(fraction) not in (float, int) or not 0 <= fraction <= 1:
            raise ValueError("INVALID_VERIFIER_PROGRESS")
        if status == "PROVED" and fraction != 1:
            raise ValueError("FALSE_PROOF_REWARD")
        total_calls += 1
        if status == "UNKNOWN":
            unknowns += 1
            reward = -0.15
        elif status == "CEX":
            counterexamples += 1
            reward = 0.8*float(fraction)-0.3
        else:
            proved += 1
            reward = 1.0
        model.apply_feedback(actions,reward)
        recorded.append({"attempt":episode,"status":status,
                         "fraction":fraction,"candidate_sha256":candidate_hash,
                         "nodes":novelty_signature(candidate)["variable_nodes"],
                         "checker_ms":verifier_ms})
    return {
      "schema":"neumann.q3.variable-length-typed-generative-policy.v1",
      "actual_grad_steps":model.gradient_steps,
      "initial_parameters_sha256":initial_sha,
      "final_parameters_sha256":model.parameters_hash(),
      "independent_checker_calls":total_calls,
      "verified_programs":proved,
      "counterexamples":counterexamples,
      "unknown_checker_outcomes":unknowns,
      "distinct_AST_sha256":len(generated),
      "full_train_wall_s":round(time.perf_counter()-started,4),
      "fixed_operator_library_used":False,
      "typed_primitive_grammar_human_authored":True,
      "Q3":"OPEN",
      "receipts":recorded
    }
