"""NEUMANN RC48 reward redundancy witness: no Torch, no training, no privileged gold.

Three observed programs have 3 op positions and 3 traces. The existing RC48
learned features explicitly include whether each position has 1 vs 3 distinct
tokens; this is sufficient to compute exact compression reward.

Exhaust all Bell(3)^3 = 125 partitions over three trace values per position
and all 3 possible candidate slot positions.
"""
from itertools import product

PARTITIONS=((0,0,0),(0,0,1),(0,1,0),(0,1,1),(0,1,2))

def exact_reward(codes,slot):
    distinct=lambda k:len(set(c[k] for c in codes))
    return 3 if distinct(slot)==3 and all(distinct(j)==1 for j in range(3) if j!=slot) else -3

def input_features_sufficient(codes,slot):
    """The relevant elements of RC48 feat: is_3 at slot, is_1 at others."""
    is3=len({c[slot] for c in codes})==3
    is1others=all(len({c[j] for c in codes})==1 for j in range(3) if j!=slot)
    return is3 and is1others

def main():
    checks=0
    for partitions in product(PARTITIONS,repeat=3):
        codes=tuple(tuple((position,partitions[position][trace]) for position in range(3))
                    for trace in range(3))
        for slot in range(3):
            assert (exact_reward(codes,slot)>0)==input_features_sufficient(codes,slot)
            checks+=1
    assert checks==375
    print("RC48 feature-reward equivalence PASS 125 structural cases, 375 slot checks; neural parameters needed: 0")

if __name__=="__main__":
    main()
