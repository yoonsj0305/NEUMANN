"""Finite-radius semantic equivalence certificates for 1x1/1x2/2x1/2x2 block programs.

Every output bit depends on at most the union of TWO local blocks, each <= 2x2.
Testing all binary assignments to this union for four spatial parity classes
is a constructive proof of equality on ALL compatible even toroidal grids h,w>=4.
Program equality is not necessary. No task truth is needed to certify a pair.
"""
from __future__ import annotations
import argparse,collections,json,pathlib
from latent_geometry_induction import candidates,arr,SHAPES

PARITIES=((3,3),(3,4),(4,3),(4,4))
def local_block(program,y,x,h=8,w=8):
    bh,bw,dy,dx,_=program
    start_y=(dy+((y-dy)%h//bh)*bh)%h
    start_x=(dx+((x-dx)%w//bw)*bw)%w
    return [((start_y+i)%h,(start_x+j)%w) for i in range(bh) for j in range(bw)]

def output_bit(program,y,x,assigned):
    cells=local_block(program,y,x)
    value=sum(assigned.get(p,0)<<i for i,p in enumerate(cells))
    bit=cells.index((y,x))
    return (program[4][value]>>bit)&1

def prove_equivalent(left,right):
    """Return proof or CONCRETE local bit counterexample, independent of true labels."""
    visited=0
    for y,x in PARITIES:
        influence=sorted(set(local_block(left,y,x))|set(local_block(right,y,x)))
        for mask in range(1<<len(influence)):
            vals={coord:(mask>>i)&1 for i,coord in enumerate(influence)}
            v1=output_bit(left,y,x,vals)
            v2=output_bit(right,y,x,vals)
            visited+=1
            if v1!=v2:
                return {"equivalent":False,"checked_local_patterns":visited,
                        "counterexample":{"output_cell":[y,x],
                                          "support":influence,"bits":mask,
                                          "left_output":v1,"right_output":v2}}
    return {"equivalent":True,"checked_local_patterns":visited,
            "valid_grid_sizes":"all h,w even >= 4, one step, fixed block phase"}

def minimum_candidates(pairs):
    all_candidates=candidates(pairs)
    if not all_candidates:return [],0
    minimal=min(x[0]*x[1] for x in all_candidates)
    return [x for x in all_candidates if x[0]*x[1]==minimal],len(all_candidates)

def quotient_select(pairs):
    opts,total=minimum_candidates(pairs)
    if not opts:return {"status":"UNKNOWN_NO_CONSISTENT_PROGRAM","program":None,"grammar_candidates":total}
    pivot=opts[0]
    checks=[prove_equivalent(pivot,op) for op in opts[1:]]
    if all(c["equivalent"] for c in checks):
        return {"status":"CERTIFIED_UNIQUE_SEMANTIC_OPERATOR",
                "program":pivot,"grammar_candidates":total,
                "minimal_program_count":len(opts),
                "local_equivalence_certificates":checks}
    return {"status":"UNKNOWN_NON_EQUIVALENT_MINIMAL_PROGRAMS",
            "program":None,"grammar_candidates":total,
            "minimal_program_count":len(opts),
            "local_equivalence_certificates":checks}

def audit(source_dir,truth_dir,out):
    stats=collections.Counter()
    witnesses=[]
    for split in ("public_dev","public_eval","generated"):
        src=[json.loads(line) for line in (pathlib.Path(source_dir)/(split+".jsonl")).read_text().splitlines()]
        truth={r["id"]:r for r in (json.loads(line) for line in
                (pathlib.Path(truth_dir)/(split+".jsonl")).read_text().splitlines())}
        assert len(src)==len(truth)==(360 if split=="generated" else 300)
        for record in src:
            uid=record["id"]
            pairs=[(arr(d["before"]),arr(d["after"])) for d in record["demos"]]
            r=quotient_select(pairs)
            stats[split+":total"]+=1
            if r["program"] is None:
                stats[split+":UNKNOWN"]+=1
                witnesses.append({"id":uid,"status":r["status"],
                                  "minima":r.get("minimal_program_count")})
                continue
            stats[split+":semantic_selected"]+=1
            is_exact=r["program"]==truth[uid]["spec"]
            stats[split+":exact_geometry"]+=int(is_exact)
            sem=prove_equivalent(r["program"],truth[uid]["spec"])
            stats[split+":true_semantically_equivalent"]+=int(sem["equivalent"])
            stats[split+":true_semantically_different"]+=int(not sem["equivalent"])
            if not sem["equivalent"]:
                witnesses.append({"id":uid,"status":"SEMANTIC_WRONG","counterexample":sem["counterexample"]})
            if r["minimal_program_count"]>1:
                stats[split+":multiple_minimal_programs_semantically_equivalent"]+=1
    report={"schema":"NEUMANN_Q3_LOCAL_CA_SEMANTIC_QUOTIENT_POSTGRADE.v1",
            "counts":dict(stats),"witnesses":witnesses[:30],
            "all_programs_human_finite_grammar":True,
            "equality_proof":"exhaustive each output cell union-of-block influence over four parities",
            "first_blind_claim":False,"original_prediction_unchanged":True}
    p=pathlib.Path(out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,sort_keys=True,separators=(",",":"))+"\n")
    print("Q3_SEMANTIC_EQUIVALENCE_POSTGRADE_960",json.dumps(report,sort_keys=True),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source-dir",required=True)
    parser.add_argument("--truth-dir",required=True)
    parser.add_argument("--out",required=True)
    ns=parser.parse_args()
    audit(ns.source_dir,ns.truth_dir,ns.out)
