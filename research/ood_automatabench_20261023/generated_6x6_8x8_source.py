"""Deterministic 6x6/8x8 generated reversible CA observable-state stress cohort.

No truth or metadata in the source-only inference file. A physically separate
original-initial-state truth file is only used in independent grade CI job.
All generated records admitted without selecting only the solver's successes.
"""
import argparse,hashlib,json,pathlib,random
from reversible_ca_solver import roll_one

SEED=20261023064

def choose_obs(rng,grid,t,n):
    h=len(grid);w=len(grid[0])
    locations=list(range(h*w));rng.shuffle(locations)
    return [{"t":t,"x":int(pos%w),"y":int(pos//w),"value":int(grid[pos//w][pos%w])}
            for pos in locations[:min(n,h*w)]]

def create(root):
    rng=random.Random(SEED)
    source=[];truth=[];group_n={}
    specs=[(6,6,"dense_terminal",60),(8,8,"dense_terminal",60),
           (6,6,"sat_fallback",10),(8,8,"sat_fallback",10),
           (6,6,"ambiguous",10),(8,8,"ambiguous",10)]
    for h,w,group,total in specs:
        for idx in range(total):
            permutation=list(range(16));rng.shuffle(permutation)
            T=rng.choice((4,5,6,7))
            initial=[[rng.randrange(2) for _ in range(w)] for __ in range(h)]
            hist=[initial]
            for t in range(T):hist.append(roll_one(hist[-1],t,permutation))
            if group=="dense_terminal":
                # Source never includes a complete initial or final state.
                hidden=5 if h==6 else 8
                obs=choose_obs(rng,hist[T],T,h*w-hidden)
                obs+=choose_obs(rng,hist[0],0,12 if h==6 else 18)
                for t in range(1,T):
                    obs+=choose_obs(rng,hist[t],t,8 if h==6 else 13)
            elif group=="sat_fallback":
                # Fully known initial state makes positive unique control certain,
                # but many unknown terminal bits disallow cheap backward enumeration.
                obs=choose_obs(rng,hist[0],0,h*w)
                obs+=choose_obs(rng,hist[T],T,7 if h==6 else 12)
            else:
                # Constructively very underdetermined; solver MUST fail-closed.
                obs=choose_obs(rng,hist[T],T,1)
                obs+=choose_obs(rng,hist[0],0,1)
            rng.shuffle(obs)
            ident=f"independent_author_ca_{h}x{w}_{group}_{idx:03}"
            case={"id":ident,"task":"initial_state_recovery",
                  "grid":{"height":h,"width":w,"boundary":"torus"},
                  "time_horizon":T,
                  "rule":{"type":"margolus_block_ca","permutation":permutation},
                  "observations":obs}
            assert "answer" not in case and "metadata" not in case
            source.append(case)
            truth.append({"id":ident,"group":group,"height":h,"width":w,
                          "answer":{"initial_state":["".join(map(str,row)) for row in initial]}})
            group_n[f"{h}x{w}_{group}"]=group_n.get(f"{h}x{w}_{group}",0)+1
    assert len(source)==len(truth)==160
    assert len({x["id"] for x in source})==160
    root=pathlib.Path(root);(root/"source").mkdir(parents=True,exist_ok=True)
    (root/"sealed_truth").mkdir(parents=True,exist_ok=True)
    out=root/"source"/"SYNTHETIC_160_NO_TRUTH.jsonl"
    target=root/"sealed_truth"/"SYNTHETIC_160_TRUTH_ONLY_FOR_GRADER.jsonl"
    out.write_text("".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in source))
    target.write_text("".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in truth))
    receipt={"schema":"NEUMANN_2D_REVERSIBLE_CA_GENERATED_160_SOURCE_SPLIT.v1",
       "n":160,"seed":SEED,"registered_groups":group_n,
       "source_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
       "truth_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
       "generated_other_author_rule_schema_not_original_benchmark_cases":True}
    (root/"sealed_truth"/"MANIFEST.json").write_text(json.dumps(receipt,sort_keys=True)+"\n")
    # No truth hash, group labels, or sealed targets are included in source artifact.
    print("GENERATED_6X6_8X8_REGISTERED_160_BEFORE_MODEL",json.dumps(receipt,sort_keys=True),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out-root",required=True)
    create(p.parse_args().out_root)
