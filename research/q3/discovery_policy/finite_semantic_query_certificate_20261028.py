#!/usr/bin/env python3
"""NEUMANN G1: self-contained exact 8-bit semantic query optimum certificate.

STD LIB ONLY, full finite grammar enumeration, independent of torch / pretrained
weight files. This is a CLASSICAL finite-space theorem, NOT neural intelligence.
21 concrete ops, max length3; 16 original source anchors. For each of the
110 observational ambiguity classes (<=5 distinct semantic functions), exhaustive
Bellman DP proves minimum total source oracle labels under UNIFORM functions.
"""
import collections
import functools
import hashlib
import itertools
import json
import pathlib
import time

PARAMS=(0,1,2,3,5,7,11,13)
OPS=tuple([('A',p) for p in PARAMS]+[('X',p) for p in PARAMS]
          +[('R',p) for p in (1,2,3)]+[('S',p) for p in (1,2)])
ANCHORS=(0,1,2,3,4,7,8,15,16,31,63,64,127,128,200,255)
assert len(OPS)==21 and len(ANCHORS)==16

def run_op(x,op):
    kind,n=op
    if kind=='A':return (x+n)&255
    if kind=='X':return x^n
    if kind=='R':return ((x<<n)|(x>>(8-n)))&255
    if kind=='S':return x>>n
    raise AssertionError(kind)

def full_library():
    library={}
    for depth in (1,2,3):
        for seq in itertools.product(OPS,repeat=depth):
            table=bytes(functools.reduce(run_op,seq,x) for x in range(256))
            if table not in library:library[table]=seq
    assert len(library)==3639
    return library

def signature(table):
    return bytes(table[x] for x in ANCHORS)

def groups_by_observation(tables):
    groups=collections.defaultdict(list)
    for t in tables:groups[signature(t)].append(t)
    return groups

def best_class_certificate(group):
    n=len(group)
    if not 2<=n<=5:raise ValueError('unexpected ambiguous class size')
    anchors=set(ANCHORS)
    @functools.lru_cache(maxsize=None)
    def optimal(mask):
        size=mask.bit_count()
        if size<=1:return (0,None)
        best=(float('inf'),None)
        for x in range(256):
            if x in anchors:continue
            buckets={}
            for i in range(n):
                if mask & (1<<i):
                    y=group[i][x]
                    buckets[y]=buckets.get(y,0)|(1<<i)
            if len(buckets)==1:continue
            cost=size+sum(optimal(submask)[0] for submask in buckets.values())
            if cost<best[0] or (cost==best[0] and x<best[1]):
                best=(cost,x)
        if best[1] is None:raise RuntimeError('source collision even with all256 inputs')
        return best
    def greedy(mask):
        best=None
        for x in range(256):
            if x in anchors:continue
            bins=collections.Counter(group[i][x] for i in range(n) if mask&(1<<i))
            if len(bins)==1:continue
            cur=(sum(v*v for v in bins.values()),x)
            if best is None or cur<best:best=cur
        if best is None:raise RuntimeError('no separating query')
        return best[1]
    def replay(strategy,target):
        mask=(1<<n)-1
        transcript=[]
        while mask.bit_count()>1:
            x=optimal(mask)[1] if strategy=='optimal' else greedy(mask)
            y=group[target][x]
            before=mask.bit_count()
            mask=sum(1<<j for j in range(n) if mask&(1<<j) and group[j][x]==y)
            assert mask.bit_count()<before
            transcript.append((x,y,before,mask.bit_count()))
        assert mask==(1<<target)
        return transcript
    root=(1<<n)-1
    best_total,best_first=optimal(root)
    exact_paths=[replay('optimal',i) for i in range(n)]
    greedy_paths=[replay('greedy',i) for i in range(n)]
    assert sum(len(x) for x in exact_paths)==best_total
    total_greedy=sum(len(x) for x in greedy_paths)
    assert total_greedy>=best_total
    return {'candidate_count':n,'DP_min_total':best_total,
            'greedy_total':total_greedy,'optimal_first_input':best_first,
            'verified_dp_subsets':optimal.cache_info().currsize,
            'greedy_query_lengths':[len(x) for x in greedy_paths],
            'optimal_query_lengths':[len(x) for x in exact_paths]}

def certify():
    t0=time.process_time()
    lib=full_library()
    groups=groups_by_observation(lib)
    assert len(groups)==3492
    amb=[v for v in groups.values() if len(v)>1]
    assert len(amb)==110
    ambiguous_count=sum(len(v) for v in amb)
    assert ambiguous_count==257
    certs=[best_class_certificate(v) for v in amb]
    optimum=sum(c['DP_min_total'] for c in certs)
    greedy=sum(c['greedy_total'] for c in certs)
    assert optimum==greedy==333
    hist=collections.Counter(c['candidate_count'] for c in certs)
    counts=collections.Counter(q for c in certs for q in c['greedy_query_lengths'])
    assert dict(sorted(hist.items()))=={2:85,3:15,4:8,5:2}
    assert dict(sorted(counts.items()))=={1:185,2:68,3:4}
    evidence={
        'kind':'REPRODUCIBLE_CLASSICAL_FINITE_DOMAIN_OPTIMALITY',
        'model_trained':False,
        'original_full_semantic_functions':3639,
        'original_16_observation_signatures':3492,
        'original_unidentifiable_without_more_observations':257,
        'original_ambiguity_classes':110,
        'source_inputs_initial':list(ANCHORS),
        'ambiguous_class_size_histogram':dict(sorted(hist.items())),
        'DP_minimum_total_extra_queries_uniform_semantics':optimum,
        'greedy_total_extra_queries_uniform_semantics':greedy,
        'greedy_query_depth_histogram':dict(sorted(counts.items())),
        'globally_optimal_under_this_known_finite_grammar_and_uniform_prior':True,
        'compared_more_general_external_SyGuS':False,
        'G1':'HOLD','global_Q1_Q7':'OPEN','G2':'NOT_RUN',
        'full_256_truth_tables_sha256':hashlib.sha256(b''.join(lib)).hexdigest(),
        'certificate_cpu_seconds':round(time.process_time()-t0,6)}
    return evidence

if __name__=='__main__':
    result=certify()
    path=pathlib.Path('FINITE_8BIT_QUERY_OPTIMALITY_CERTIFICATE.json')
    path.write_text(json.dumps(result,sort_keys=True,indent=2))
    print('G1_FINITE_QUERY_CERTIFICATE',json.dumps(result,sort_keys=True))
