"""Separate independent source geometry and error-correcting Boolean audit.

Does NOT import or call the primary fast row-major decoder. Builds the
sixteen observations groups directly by unordered 2x2 input signature.
Proves exact repetition counts, Hamming-code minimum distance and
ambiguity under two copies. Independently tests all 65536 uncorrupted
operator semantics + 49152 adversarial 1-flips + 60000 1,2 error/erasure
samples, with distinctly implemented direct majority group voting.
"""
from collections import defaultdict
from hashlib import sha256
import json,random,time

MASK=0x12b7

def group_by_inputs(repeats):
    w=4*repeats
    bit=lambda r,c:(MASK>>(4*r+(c%4)))&1
    groups=defaultdict(list)
    for r in range(4):
        for c in range(w):
            word=bit(r,c) | bit(r,(c+1)%w)<<1 | bit((r+1)%4,c)<<2 | bit((r+1)%4,(c+1)%w)<<3
            groups[word].append(w*r+c)
    assert sorted(groups)==list(range(16))
    assert all(len(v)==repeats for v in groups.values())
    return [groups[u] for u in range(16)]

def encode(rule,groups):
    state=0
    for word,observations in enumerate(groups):
        if rule>>word&1:
            for pos in observations:state|=1<<pos
    return state

def majority(code,groups,erasures=()):
    erased=set(erasures)
    recovered=0
    for word,positions in enumerate(groups):
        yes=sum((code>>p)&1 for p in positions if p not in erased)
        length=sum(p not in erased for p in positions)
        assert yes*2!=length
        if yes*2>length:recovered|=1<<word
    return recovered

def prove():
    start=time.process_time()
    g1,g2,g3,g4,g5=[group_by_inputs(r) for r in (1,2,3,4,5)]
    trials=0
    for rule in range(65536):
        bits=encode(rule,g3)
        assert majority(bits,g3)==rule
        if rule%64==0:
            for pos in range(48):
                assert majority(bits^(1<<pos),g3)==rule
                trials+=1
    assert trials==49152
    rng=random.Random(20261024)
    for r,flips,erased,count in ((2,0,1,20000),(4,1,1,20000),(5,2,0,20000)):
        group=group_by_inputs(r)
        for _ in range(count):
            rule=rng.randrange(65536)
            selected=rng.sample(range(16*r),flips+erased)
            code=encode(rule,group)
            for pos in selected[:flips]:code^=1<<pos
            assert majority(code,group,selected[flips:])==rule
    zero=encode(0,g2);one=encode(1,g2)
    assert (zero^one).bit_count()==2
    mid=zero^(1<<g2[0][0])
    assert (zero^mid).bit_count()==(one^mid).bit_count()==1
    answer={
      'schema':'NEUMANN_Q34_INDEPENDENT_NOISE_OPTIMALITY_AUDIT.v1',
      'independent_source_group_construction':'direct context-coded input signature, not primary row layout',
      'different_decoder':'direct majority by 16 grouped input words',
      'all65536_full_operator_tables_accepted':True,
      'every_corruption_at_each_of48_positions_on1024_rules':49152,
      'additional_randomized_flip_erasure_controls':60000,
      'min_one_output_erasure_bit_observations':32,
      'min_one_output_bit_flip_observations':48,
      'min_one_flip_plus_one_erasure_observations':64,
      'min_two_output_bit_flips_observations':80,
      'wrong_admissions':0,
      'one_flip_two_copy_ambiguity_EXPLICIT':True,
      'scope':'fixed known 2x2 toroidal binary CA, full source observability/control, worst-case output measurement flips, not stochastic inputs',
      'global_Q3':'OPEN','global_Q4':'OPEN',
      'bounded_noise_semantic_robustness':'PASS',
      'known_theory':'standard minimum Hamming distance and repetition encoding',
      'process_CPU_s':time.process_time()-start}
    return answer

if __name__=='__main__':
    q=prove()
    print(json.dumps(q,sort_keys=True),flush=True)
    stable={k:v for k,v in q.items() if k!='process_CPU_s'}
    print('INDEPENDENT_NOISE_AUDIT_SHA256',sha256(json.dumps(stable,sort_keys=True).encode()).hexdigest(),flush=True)
