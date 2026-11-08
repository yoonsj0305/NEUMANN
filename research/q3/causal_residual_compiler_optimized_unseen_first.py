"""Q3 optimize causal residual synthesis, then NEW untouched 32 originals.

The first DNF version repeated full sorting for each candidate, an
unnecessary superlinear bottleneck. This replacement uses only a small
pre-ranked sufficient-set beam and a simple maximum on residual coverage.
The original attempt stays preserved as a failed/blocked development run.
Targets ic_bvule + ic_bvult have not been read at implementation freeze.
"""
import time,itertools,sys
import causal_invariant_boolean_existence_first as old
import source_proven_duality_and_residual_dnf_first as parent

NEW_TARGET=[f"ic_{rel}_{op}.sl" for rel in ("bvule","bvult") for op in old.base.OPS]
assert len(NEW_TARGET)==32 and len(set(NEW_TARGET))==32
assert set(NEW_TARGET).isdisjoint(old.SOURCE+old.TARGET+parent.TARGET)

def fast_residual(y,atoms,max_terms=3,pair_limit=28):
    if y==0:return ("const",False),0,{"terms":0}
    if y==old.FULL:return ("const",True),0,{"terms":0}
    literals=parent.atoms_with_negations(atoms)
    implicants={};checked=0
    def insert(mask,node):
        if not mask or (mask&~y):return
        if mask not in implicants or old.n_nodes(node)<old.n_nodes(implicants[mask]):
            implicants[mask]=node
    for p,m in literals:
        checked+=1;insert(m,p)
    for i,(p,m) in enumerate(literals):
        for q,n in literals[i+1:]:
            checked+=1
            intersection=m&n
            if not intersection or intersection&(~y):continue
            insert(intersection,("and",p,q))
    if not implicants:
        return None,checked,{"candidate_implicants":0}
    ordered=sorted(implicants.items(),key=lambda item:(
       -item[0].bit_count(),old.n_nodes(item[1]),old.canon(item[1])))
    # Semantic masking means each term is a proved sufficient condition.
    # Search only the strongest bounded beam; failing to find a complete
    # cover produces ABSTAIN, NEVER an incorrect program.
    best=[]
    for first in [None]+ordered[:pair_limit]:
        prefix=[] if first is None else [(first[1],first[0])]
        uncovered=y if first is None else y&~first[0]
        chosen=prefix[:]
        while uncovered and len(chosen)<max_terms:
            checked+=len(ordered)
            mask,node=max(ordered,key=lambda item:(
              (item[0]&uncovered).bit_count(),
              -old.n_nodes(item[1])))
            if (mask&uncovered)==0:break
            chosen.append((node,mask))
            uncovered &= ~mask
        if uncovered:continue
        ast=chosen[0][0]
        for p,m in chosen[1:]:
            ast=("or",ast,p)
        if old.independently_check(ast,y):
            best.append((old.n_nodes(ast),old.canon(ast),ast,len(chosen)))
    if best:
        _,_,ast,k=min(best)
        return ast,checked,{"terms":k,"total_valid_implicants":len(ordered),
                            "beam":pair_limit}
    return None,checked,{"candidate_implicants":len(implicants),
                         "beam":pair_limit}

parent.dnf_from_residual=fast_residual
parent.TARGET=NEW_TARGET

if __name__=="__main__":
    if sys.argv[1:]==["source"]:
        parent.source_only()
    elif sys.argv[1:]==["target"]:
        parent.target_only()
    else:raise SystemExit("source|target")
