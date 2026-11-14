"""Bounded Q3/Q4: all 65536 unknown 2x2 binary CA operators reconstructed
from one 4x4 toroidal observation, compiled to executable ANF and checked.
Classical de Bruijn/Mobius methods, NOT neural-invented intelligence.
Pure Python 3, no packages or API. Source semantics must be known 2x2 local.
"""
from collections import Counter
from math import comb

def rows(mask):
    return [[(mask >> (4*r+c)) & 1 for c in range(4)] for r in range(4)]

def windows(grid):
    return tuple(grid[r][c] | (grid[r][(c+1)%4] << 1) |
        (grid[(r+1)%4][c] << 2) | (grid[(r+1)%4][(c+1)%4] << 3)
        for r in range(4) for c in range(4))

def anf(table):
    coefficients=[(table >> i)&1 for i in range(16)]
    for bit in range(4):
        for i in range(16):
            if i & (1<<bit):coefficients[i]^=coefficients[i^(1<<bit)]
    return sum(bit<<i for i,bit in enumerate(coefficients))

def execute_anf(coeffs,word):
    return sum((coeffs>>m)&1 for m in range(16) if word & m == m)%2

def prove():
    universal=[v for v in range(65536) if len(set(windows(rows(v))))==16]
    assert len(universal)==32 and universal[0]==0x12B7
    patches=windows(rows(universal[0]));assert sorted(patches)==list(range(16))
    degrees=Counter(); essential=Counter(); errors=0
    for rule in range(65536):
        outputs=sum(((rule>>code)&1)<<i for i,code in enumerate(patches))
        recovered=sum(((outputs>>i)&1)<<code for i,code in enumerate(patches))
        assert recovered==rule
        coefficients=anf(recovered)
        if any(execute_anf(coefficients,i)!=((rule>>i)&1) for i in range(16)):
            errors+=1
        deg=max((i.bit_count() for i in range(16) if (coefficients>>i)&1), default=0)
        degrees[deg]+=1
        ess=sum(any(((rule>>i)&1)!=((rule>>(i^(1<<b)))&1) for i in range(16)) for b in range(4))
        essential[ess]+=1
    assert errors==0 and degrees[4]==32768
    assert all(essential[k]==comb(4,k)*sum((-1)**(k-j)*comb(k,j)*2**(2**j) for j in range(k+1)) for k in range(5))
    return {'schema':'NEUMANN_Q34_ONE_SHOT_MINIMAL_OPERATOR_REPLAY.v1',
        'unique_4x4_universal_probe_count':32,
        'universal_mask':'0x12b7','first_probe_patch_order':list(patches),
        'rules_recovered_and_ANF_domain_verified':65536,
        'incorrect_operators':errors,'highest_degree_four_rules':degrees[4],
        'essential_variable_counts':dict(essential),
        'minimum_binary_output_bits':16,'used_binary_output_bits':16,
        'minimum_experiment_rounds':1,'used_experiment_rounds':1,
        'Q34_bounded':'PASS','Q3_global':'OPEN','Q4_global':'OPEN'}

if __name__=='__main__':
    import json
    print(json.dumps(prove(),sort_keys=True))
