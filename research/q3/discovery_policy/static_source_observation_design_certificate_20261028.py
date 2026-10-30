#!/usr/bin/env python3
"""Post-first classical design of static source observations for finite 8bit DSL.

No torch, no pre-trained weights, no oracle outcomes from any hidden target.
Full 3639 source functions are known from the finite grammar. The greedy rule
optimizes pairwise source collisions at each fixed probe, NOT proven globally
minimal probe count. Re-run with Python standard library alone.
"""
import collections
import hashlib
import json
import pathlib
import time

try:
    from research.q3.discovery_policy.finite_semantic_query_certificate_20261028 import (
        ANCHORS,full_library
    )
except ModuleNotFoundError:
    from finite_semantic_query_certificate_20261028 import ANCHORS,full_library

def signature(t,anchors):
    return bytes(t[x] for x in anchors)

def compute_static_design():
    start=time.process_time()
    tables=list(full_library())
    assert len(tables)==3639
    candidates=list(range(256))
    # All 3639 functions are initially observationally equivalent.
    classes=[0]*len(tables)
    probes=[]
    history=[]
    while len(set(classes))<len(tables):
        best=None
        for x in candidates:
            if x in probes:continue
            counts=collections.Counter((classes[i],tables[i][x])
                                        for i in range(len(tables)))
            collision_cost=sum(q*q for q in counts.values())
            singletons=sum(q for q in counts.values() if q==1)
            score=(collision_cost,-singletons,x)
            if best is None or score<best:best=score
        assert best is not None
        x=best[2]
        remap={}
        next_classes=[]
        for old,t in zip(classes,tables):
            key=(old,t[x])
            if key not in remap:remap[key]=len(remap)
            next_classes.append(remap[key])
        assert len(set(next_classes))>len(set(classes))
        classes=next_classes
        probes.append(x)
        cnt=collections.Counter(classes)
        history.append({'n_probes':len(probes),'probe':x,'n_distinct_signatures':len(cnt),
                        'n_ambiguous_functions':sum(v for v in cnt.values() if v>1)})
    fixed=collections.Counter(signature(t,ANCHORS) for t in tables)
    designed=collections.Counter(signature(t,probes) for t in tables)
    assert len(fixed)==3492
    assert sum(n for n in fixed.values() if n>1)==257
    assert len(designed)==3639
    assert len(probes)==14
    assert probes==[207,58,244,253,255,96,250,246,126,123,252,129,242,248]
    return {'research_scope':'POSTFIRST_CLASSICAL_STATIC_OBSERVATION_DESIGN',
            'semantic_full_256_unique':3639,'original_anchor_count':len(ANCHORS),
            'original_source_signature_classes':len(fixed),
            'original_source_ambiguous_functions':257,
            'designed_static_anchor_count':len(probes),
            'designed_static_anchor_inputs':probes,
            'designed_source_signature_classes':len(designed),
            'designed_source_ambiguous_functions':0,
            'stronger_claim_global_minimum_14':'NOT_PROVED',
            'algorithm':'greedy minimize sum squared partition-size; tie maximize singletons then x',
            'original_grammar_pinned':True,
            'target_function_gold_never_used_when_selecting_static_probes':True,
            'all_semantics_exhaustively_verified_by_byte_signatures':True,
            'CPU_seconds':round(time.process_time()-start,6),
            'original_prereg_new_source_query_study':'2a63b09e22b318a48d2fb6b4d9ca33f97ee9d41d',
            'postfirst':True,'global_Q1_Q7':'OPEN','G1':'HOLD',
            'history':history}

if __name__=='__main__':
    result=compute_static_design()
    output=pathlib.Path('STATIC_SOURCE_QUERY_DESIGN_14_INPUTS_CERTIFICATE.json')
    output.write_text(json.dumps(result,sort_keys=True,indent=2))
    print('STATIC14_FULL_GUARANTEE_WITHIN_DSL',len(result['designed_static_anchor_inputs']),
          'unique',result['designed_source_signature_classes'],
          'CPU',result['CPU_seconds'])
    print('SHA256',hashlib.sha256(output.read_bytes()).hexdigest())
