"""Q3 RC1: finite-evidence operator library + generation-on-miss tests.

Existing GPT-6 source code is replayed as a fixture. There is no NEUMANN-own
neural generator here; no attempt to infer withheld benchmark outputs.
"""
import pathlib, sys, random, pytest
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "q3" / "contextual_operator"))
from verified_library import VerifiedLibrary

MODEL_AUTHORED_SOURCE = '''def invented(grid):
    h=len(grid)
    k=next(i for i in range(1,h+1) if all(grid[j]==grid[j%i] for j in range(h)))
    return [[2 if v==1 else v for v in grid[j%k]] for j in range(9)]
'''
BASE = [[0,1,0],[1,0,1],[0,1,0],[1,0,1],[0,1,0],[1,0,1]]
SECOND = [[0,1,0],[1,1,0],[0,1,0],[0,1,1],[0,1,0],[1,1,0]]
THIRD = [[0,1,0],[1,1,0],[0,1,0],[0,1,0],[1,1,0],[0,1,0]]

def expected(grid, src, dst):
    h=len(grid);period=next(k for k in range(1,h+1) if all(grid[i]==grid[i%k] for i in range(h)))
    return [[dst if v==src else v for v in grid[i%period]] for i in range(9)]

def recolor(grid, src, dst):
    return [[dst if v==src else v for v in row] for row in grid]

def evidence(src,dst):
    xs=[recolor(x,1,src) for x in [BASE,SECOND,THIRD]]
    return [{'input':x,'output':expected(x,src,dst)} for x in xs]

def test_one_generator_call_then_100_contexts_without_generation():
    rng=random.Random(4816)
    lib=VerifiedLibrary();d=evidence(3,7);requests=[]
    def propose(demos):
        requests.append(1)
        return {'id':'previous-GPT6-proposal','source':MODEL_AUTHORED_SOURCE,
                'function':'invented','origin':'EXTERNAL_GPT6_FROZEN_REPLAY'}
    first=lib.solve_or_invent(d[:2],d[2:],THIRD,proposer=propose)
    assert first['status']=='PREDICTED_UNVERIFIED' and len(requests)==1
    assert lib.stats['registered']==1
    for _ in range(100):
        c=list(range(1,10));rng.shuffle(c);a,b=c[:2];v=evidence(a,b)
        result=lib.solve_or_invent(v[:2],v[2:],v[2]['input'],proposer=propose)
        assert result['status']=='PREDICTED_UNVERIFIED'
        assert result['output']==v[2]['output']
    assert len(requests)==1 and lib.stats['proposal_requests']==1
    assert lib.items[0].origin=='EXTERNAL_GPT6_FROZEN_REPLAY'

def test_unseen_operator_without_generator_abstains():
    lib=VerifiedLibrary();d=evidence(2,8)
    assert lib.solve_or_invent(d[:2],d[2:],d[2]['input'],proposer=None)['status']=='UNKNOWN'

def test_single_example_and_conflicting_examples_abstain():
    lib=VerifiedLibrary();d=evidence(3,7)
    assert lib.admit('p',MODEL_AUTHORED_SOURCE,'invented',d[:2],d[2:],'GPT6')
    assert lib.reuse(d[:1],d[2]['input'])['status']=='UNKNOWN'
    contradictions=[dict(d[0]),dict(d[0])]
    wrong=[list(row) for row in d[0]['output']]
    wrong[0][0]=99
    contradictions[1]['output']=wrong
    assert lib.reuse(contradictions,d[2]['input'])['status']=='UNKNOWN'

def test_lookup_attack_abstains_and_duplicate_fails():
    lib=VerifiedLibrary();d=evidence(3,7)
    evil='def lookup(grid):\\n'+''.join('    if grid == '+repr(q['input'])+': return '+repr(q['output'])+'\\n' for q in d)+'    return [[0]]\\n'
    evil=evil.replace('\\n','\n')
    assert not lib.admit('fake',evil,'lookup',d[:2],d[2:],'FAKE')
    assert lib.admit('real',MODEL_AUTHORED_SOURCE,'invented',d[:2],d[2:],'GPT6')
    assert not lib.admit('again',MODEL_AUTHORED_SOURCE,'invented',d[:2],d[2:],'GPT6')

def test_unsafe_code_refused():
    lib=VerifiedLibrary();d=evidence(3,7)
    assert not lib.admit('bad','import os\\ndef x(g): return g\\n'.replace('\\n','\n'),
                         'x',d[:2],d[2:],'MALICIOUS')
