"""Verifiable research contract, not a trained-model or blind ARC benchmark claim."""
import pathlib,sys,random,pytest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'research'/'q3'/'contextual_operator'))
from contextual_operator import bind_operator,UnknownContext

MODEL_CODE='''def discovered(grid):
    h=len(grid)
    k=next(i for i in range(1,h+1) if all(grid[j]==grid[j%i] for j in range(h)))
    return [[2 if v==1 else v for v in grid[j%k]] for j in range(9)]
'''
INPUT=[[0,1,0],[1,0,1],[0,1,0],[1,0,1],[0,1,0],[1,0,1]]
def paint(grid, m):return [[m[v] for v in row] for row in grid]
def expected(grid,src,dst):
    k=next(i for i in range(1,len(grid)+1) if all(grid[j]==grid[j%i] for j in range(len(grid))))
    return [[dst if v==src else v for v in grid[j%k]] for j in range(9)]

def test_context_rebind_200_new_palettes():
    rng=random.Random(735311)
    for _ in range(200):
        colors=list(range(1,10));rng.shuffle(colors);p={0:0,**dict(zip(range(1,10),colors))}
        x=paint(INPUT,p);y=expected(x,p[1],p[2]);second=paint(INPUT[1:]+INPUT[:1],p)
        operator=bind_operator(MODEL_CODE,[{'input':x,'output':y},
          {'input':second,'output':expected(second,p[1],p[2])}])
        assert operator(x)==y
        assert operator(second)==expected(second,p[1],p[2])

def test_inadequate_and_contradictory_demonstrations_abstain():
    y=expected(INPUT,1,2)
    with pytest.raises(UnknownContext):bind_operator(MODEL_CODE,[])
    with pytest.raises(UnknownContext):bind_operator(MODEL_CODE,[{'input':INPUT,'output':y}])
    bad=[[3 if v==2 else v for v in row] for row in y]
    with pytest.raises(UnknownContext):bind_operator(MODEL_CODE,[{'input':INPUT,'output':y},{'input':INPUT,'output':bad}])

@pytest.mark.parametrize('source',["def discovered(x):\n import os\n return x", "def discovered(x):\n return eval('1')", "def discovered(x):\n while True: pass\n return x", "def discovered(x):\n return x.__class__"])
def test_unsafe_ast_rejected(source):
    with pytest.raises(UnknownContext):bind_operator(source,[])
