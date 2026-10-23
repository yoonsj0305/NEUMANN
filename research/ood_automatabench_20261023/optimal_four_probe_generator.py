"""Four diagnostic 4x4 CA one-step interventions identify all sixteen hidden
2x2 reversible block transitions. All four input grids are chosen WITHOUT
reading rule parameters, output answers or original task label. Each probe
contains FOUR distinct patterns; four probes cover inputs 0..15 exactly.

Universal lower bound: any three one-step whole-grid probes expose <=12
distinct 2x2 block inputs, leaving >=4 unmapped input symbols. For an
arbitrary bijection p of 16 patterns those >=4 unmapped outputs can be
permuted in >=4! ways while preserving every source observation. Therefore
four whole-grid interventions are information-theoretically NECESSARY to
identify the full unconstrained rule permutation in the worst case and are
SUFFICIENT by the construction here. Not a lower bound for identifying a
specific query answer, which may need less information.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,random
from reversible_ca_solver import roll_one,blocks
from hidden_rule_inference import source_pair_mapping

PIN="7d86373fdb63fe1bd3592ddf71d923ceebc5acd9"
RAND_SEED=202610230909
KINDS=("random4","random6","random12","designed4")

def design_probe(probe_no):
    assert 0<=probe_no<4
    board=[[0]*4 for _ in range(4)]
    for block_idx,positions in enumerate(blocks(4,4,0)):
        pattern=4*probe_no+block_idx
        for bit,(y,x) in enumerate(positions):
            board[y][x]=(pattern>>bit)&1
    return board

def build_demo(board,rule):
    after=roll_one(board,0,rule)
    return {"before":["".join(map(str,row)) for row in board],
            "after":["".join(map(str,row)) for row in after]}

def create(original_file,directory):
    raw=pathlib.Path(original_file).read_bytes()
    tasks=[json.loads(x) for x in raw.splitlines()]
    assert len(tasks)==len(set(t["id"] for t in tasks))==300
    rng=random.Random(RAND_SEED)
    samples=[]
    for idx,task in enumerate(tasks):
        rule=task["rule"]["permutation"]
        assert sorted(rule)==list(range(16))
        # Identical random sequence/budget to preceding PR520/521, for
        # transparent paired ablation with designed-four sample efficiency.
        random_demos=[]
        for j in range(12):
            random_board=[[rng.randrange(2) for _ in range(4)] for _ in range(4)]
            random_demos.append(build_demo(random_board,rule))
        optimal_demos=[build_demo(design_probe(j),rule) for j in range(4)]
        mapping,error=source_pair_mapping(optimal_demos)
        assert error is None and len(mapping)==16
        assert tuple(mapping[i] for i in range(16))==tuple(rule)
        mapping3,error=source_pair_mapping(optimal_demos[:3])
        assert error is None and len(mapping3)==12
        assert len(set(rule)-set(mapping3.values()))==4
        masked={k:v for k,v in task.items() if k not in ("answer","metadata")}
        masked["rule"]={"type":"margolus_block_ca"}
        assert "permutation" not in masked["rule"]
        for name,budget in (("random4",4),("random6",6),("random12",12),("designed4",4)):
            demos=optimal_demos if name=="designed4" else random_demos[:budget]
            row={"id":task["id"]+"__"+name,
                 "original_id":task["id"],"calibration":name,
                 "n_source_probes":budget,
                 "task":masked,"demos":demos}
            assert "answer" not in json.dumps(row) and "permutation" not in json.dumps(row)
            samples.append(row)
    assert len(samples)==1200 and len({v["id"] for v in samples})==1200
    directory=pathlib.Path(directory);directory.mkdir(parents=True,exist_ok=True)
    path=directory/"BLIND_300x4_ACTIVE_VS_RANDOM_SOURCE.jsonl"
    path.write_text("".join(json.dumps(v,sort_keys=True,separators=(",",":"))+"\n" for v in samples))
    ident={"schema":"NEUMANN_Q3_OPTIMAL_EXPERIMENT_DESIGN_CA_SOURCE_ONLY.v1",
        "original_source_sha256":hashlib.sha256(raw).hexdigest(),
        "n_distinct_original":300,"n_source_episodes":1200,
        "designed_calibration_input_patterns":list(range(16)),
        "three_probe_max_distinct_rule_inputs":12,
        "three_probe_min_rule_completions":24,
        "four_probe_theorem":"COMPLETE_16x16_UNKNOWN_PERMUTATION_MAPPING",
        "source_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "random_comparison_seed":RAND_SEED,"source_true_rule_absent":True}
    (directory/"DESIGNED_VS_RANDOM_SOURCE_RECEIPT.json").write_text(json.dumps(ident,sort_keys=True)+"\n")
    print("OPTIMAL_FOUR_PROBE_THEOREM_ALL_300_SOURCE_RULE_MAPS_RECONSTRUCTED",json.dumps(ident,sort_keys=True),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--original",required=True);p.add_argument("--out",required=True)
    a=p.parse_args();create(a.original,a.out)
