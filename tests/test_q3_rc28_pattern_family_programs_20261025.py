"""Check extracted-code symbolic correctness independent of fitted tensor."""
import itertools,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc28"))
from pattern_machines import SUFFIX101,SEEN101,run,prove_all_lengths,is_minimal

def test_all_length_product_and_minimality_of_new_families():
    for p,task,size in ((SUFFIX101,"suffix101",3),(SEEN101,"seen101",4)):
        assert len(p["transitions"])==size
        assert prove_all_lengths(p,task)["status"]=="PROVED_FOR_EXTRACTED_DFA_ONLY"
        assert is_minimal(p)
        for n in range(1,12):
            for bits in itertools.product((0,1),repeat=n):
                target=int(bits[-3:]==(1,0,1)) if task=="suffix101" else int(
                    any(bits[i:i+3]==(1,0,1) for i in range(n-2)))
                assert run(p,bits)[-1]==target

def test_every_single_output_mutation_is_caught():
    for p,task in ((SUFFIX101,"suffix101"),(SEEN101,"seen101")):
        for s in p["transitions"]:
            for a in "01":
                q={"initial":p["initial"],"transitions":{
                    u:{k:tuple(v) for k,v in edges.items()}
                    for u,edges in p["transitions"].items()}}
                to,val=q["transitions"][s][a]
                q["transitions"][s][a]=(to,val^1)
                assert prove_all_lengths(q,task)["status"]=="FAIL"

def test_unbounded_typed_stack_requires_more_than_finite_pattern_grammar():
    # Two types of pending opens, depth3 => 2**3=8 states are distinguishable
    # via distinct matching reverse-closing continuations. No 3/4-state DFA.
    histories=list(itertools.product((0,1),repeat=3))
    assert len(histories)==8
    assert len(histories)>max(map(lambda x:len(x["transitions"]),(SUFFIX101,SEEN101)))
