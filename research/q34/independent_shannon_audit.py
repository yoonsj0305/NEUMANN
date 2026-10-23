"""Independent reduced ordered Boolean decision-graph synthesis, all 65536.
Distinct algorithm from ANF Mobius recovery in one_shot_boolean_operator.
"""
from collections import Counter
from one_shot_boolean_operator import rows,windows

def bdd(table):
    nodes={0:None,1:None}
    seen={}
    def build(bits,level):
        if all(z==0 for z in bits):return 0
        if all(z==1 for z in bits):return 1
        assert level>=0
        half=len(bits)//2
        lo,hi=build(bits[:half],level-1),build(bits[half:],level-1)
        if lo==hi:return lo
        key=(level,lo,hi)
        if key not in seen:
            idx=len(nodes)
            seen[key]=idx
            nodes[idx]=key
        return seen[key]
    return nodes,build(table,3)

def execute(nodes,root,word):
    while root not in (0,1):
        bit,lo,hi=nodes[root]
        root=hi if word & (1<<bit) else lo
    return root

def certify():
    grid=rows(0x12b7)
    patch=windows(grid)
    assert len(set(patch))==16
    distribution=Counter()
    for rule in range(65536):
        output=[(rule>>input_word)&1 for input_word in patch]
        # Recover as independently keyed dictionary, no Mobius routine.
        recovered={input_word:output[index] for index,input_word in enumerate(patch)}
        truth=tuple(recovered[x] for x in range(16))
        nodes,root=bdd(truth)
        assert all(execute(nodes,root,x)==((rule>>x)&1) for x in range(16))
        distribution[len(nodes)-2]+=1
    assert sum(distribution.values())==65536
    assert max(distribution)==9
    return {'independent_BDD_synthesis_verified':65536,
            'BDD_node_count_distribution':dict(distribution),
            'bounded_Q34':'PASS','neural_original_semantics':'NOT_PROVED'}

if __name__=='__main__':
    import json
    print(json.dumps(certify(),sort_keys=True))
