#!/usr/bin/env python3
"""Opened external original PRE_27_1000 finite-example component triage.

NO single executable source program produced. Classify EACH of 1000 published
ground labels as one of three already grammar-expressible 64bit operations.
Exact modular bitvector semantics; no unknown target oracle inference.
"""
import collections,hashlib,json,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
SOURCE="lib/PBE_BV_Track/from_2018/PRE_27_1000.sl"
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("official_pre27_pbe_components_postfirst")
MASK=(1<<64)-1
EXAMPLES=re.compile(r"^\(\s*constraint\s+\(=\s+\(f\s+(#x[0-9a-fA-F]{16})\)\s+(#x[0-9a-fA-F]{16})\)\s*\)$")

def name_of_class(x,y):
    possibilities={
      "PLUS_ONE":(x+1)&MASK,
      "PLUS_TWO":(x+2)&MASK,
      "AND_SHIFT_ONE":x&((x<<1)&MASK),
    }
    matching=[k for k,v in possibilities.items() if v==y]
    if len(matching)!=1:raise ValueError("NOT_EXACTLY_ONE_CLASS_"+repr((hex(x),hex(y),matching)))
    return matching[0]

def main():
    start=time.process_time()
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],
                                   text=True).strip()==PIN
    raw=(ROOT/SOURCE).read_bytes()
    forms=[(get_cmd(f[2]),f[2]) for f in top_level_forms(raw.decode("utf8"))]
    cs=[f for op,f in forms if op=="constraint"]
    synth=[f for op,f in forms if op=="synth-fun"]
    helpers=[f for op,f in forms if op=="define-fun"]
    assert len(cs)==1000 and len(synth)==1
    assert any(re.search(r"^\(\s*define-fun\s+smol\b",f) and "bvshl" in f for f in helpers)
    assert all(token in synth[0] for token in ("(bvadd Start Start)","(bvand Start Start)",
         "(smol Start)","(im Start Start Start)","#x0000000000000001"))
    original=[]
    for i,form in enumerate(cs):
        m=EXAMPLES.fullmatch(form)
        if not m:raise ValueError("NON_PBE_GROUND_CONSTRAINT_"+str(i))
        x=int(m.group(1)[2:],16);y=int(m.group(2)[2:],16)
        cls=name_of_class(x,y)
        original.append({"index":i,"x_hex":f"{x:016x}","y_hex":f"{y:016x}","component":cls})
    assert len({r["x_hex"] for r in original})==1000
    counts=dict(collections.Counter(r["component"] for r in original))
    assert counts=={"PLUS_ONE":665,"PLUS_TWO":234,"AND_SHIFT_ONE":101},counts
    for r in original:
        x=int(r["x_hex"],16);cat=r["component"]
        if cat=="PLUS_TWO":assert x&3==1
        if cat=="AND_SHIFT_ONE":assert (x&1)==0 and ((x>>16)&1)==1
    b="\n".join(f"{r['index']}|{r['x_hex']}|{r['y_hex']}|{r['component']}" for r in original).encode()
    res={
      "research_scope":"POSTFIRST_OPENED_EXTERNAL_SOURCE_PBE_PATTERN_ANALYSIS",
      "official_source_git_commit":PIN,
      "original_source_path":SOURCE,"original_source_sha256":sha256(raw),
      "original_example_count":1000,
      "original_input_values_unique":True,
      "source_all_example_components_exhaustive":True,
      "source_each_example_has_exactly_one_component":True,
      "source_grammar_operator_membership_necessary_subexpressions_checked":True,
      "component_counts":counts,
      "source_pattern_annotations_sha256":sha256(b),
      "representative_ground_example_by_component":{
          cls:next(r for r in original if r["component"]==cls) for cls in counts},
      "original_published_native_CVC5_142_status":"CPU12_BUDGET_HOLD",
      "selector_program_found":False,
      "unseen_ideal_target_output_oracle_available":False,
      "original_full_program_semantic_proof":"NOT_RUN",
      "model_trained":False,
      "global_Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN",
      "CPU_process_seconds":round(time.process_time()-start,6)}
    OUT.mkdir(exist_ok=True)
    (OUT/"PRE27_ALL1000_ORIGINAL_SOURCE_COMPONENTS.tsv").write_bytes(b+b"\n")
    p=OUT/"PRE27_ALL1000_THREE_OUTPUT_COMPONENTS_POSTFIRST.json"
    p.write_text(json.dumps(res,indent=2,sort_keys=True))
    print("PRE27_EXACT_1000",json.dumps(counts,sort_keys=True),flush=True)
    print("PRE27_OPEN_NOT_SOLVED",res["selector_program_found"],flush=True)
    print("PRE27_SHA256",sha256(p.read_bytes()),flush=True)
if __name__=="__main__":main()
