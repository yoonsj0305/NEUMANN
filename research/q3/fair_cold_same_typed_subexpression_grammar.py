"""POSTFIRST fair cold baseline, same typed Int subexpressions as learned template.

Previously 'strong_full' omitted str.substr lengths such as
minus(indexof(input, "Inc"), 1) that learned templates could generate.
This comparator grants generic classical search the SAME expression language.
No source memory or template is read by the classical arm.
"""
from __future__ import annotations
import itertools,time
import typed_cross_domain_meta_engine as core
import typed_domain_interface_postfirst as typed
import typed_meta_hole_binder_v2 as binder

def all_direct_candidates(task):
    orig=typed.candidate_typed(task)
    if task["output"]!="String" or "str.substr" not in task["ops"]:
        yield from orig;return
    ints=binder.scalar_grammar(task)
    args=[["arg",i] for i in range(task["nargs"])]
    seen=set()
    # Enumerate all typable atom/primitive programs. The grammar permits
    # all source candidates; no source-verified programs or target labels.
    generated=iter(orig)
    for p in generated:
        k=core.canonical(p)
        if k not in seen:
            seen.add(k);yield p
    for a in args:
        for start,length in itertools.product(ints,repeat=2):
            p=["substr",a,start,length]
            if not core.grammar_compatible(p,task):continue
            key=core.canonical(p)
            if key not in seen:
                seen.add(key);yield p
        if "str.at" in task["ops"]:
            for idx in ints:
                p=["at",a,idx]
                if not core.grammar_compatible(p,task):continue
                key=core.canonical(p)
                if key not in seen:
                    seen.add(key);yield p

def solve(task,train,budget=25000):
    begin=time.perf_counter_ns();attempts=0
    for p in all_direct_candidates(task):
        if attempts>=budget:
            return {"status":"ABSTAIN_BUDGET","ast":None,
                    "checks":attempts,"ms":(time.perf_counter_ns()-begin)/1e6}
        attempts+=1
        if typed.score_any(p,train)["exact"]:
            return {"status":"UNRESTRICTED_SAME_LANGUAGE_CLASSICAL",
                    "ast":p,"checks":attempts,
                    "ms":(time.perf_counter_ns()-begin)/1e6}
    return {"status":"ABSTAIN_FULL_EXPRESSION_GRAMMAR","ast":None,
            "checks":attempts,"ms":(time.perf_counter_ns()-begin)/1e6}
