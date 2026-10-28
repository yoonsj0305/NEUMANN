#!/usr/bin/env python3
"""Official SyGuS12 diverse-source NEW original native strong C 1.4.2 headroom.
Filename selection precommitted before body access; no NEUMANN neural training.
ONE real original FULL benchmark per task, no dropped parser/timeouts.
"""
import collections,hashlib,json,pathlib,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_official_multifamily_classical_first_20261027 import run_solver

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
INVENTORY_SHA="9cdc403f8515900c72605d674dd96a7cacb57af1355153e93a7df4b66968584e"
SOURCE="SyGuS-Org/benchmarks"
PREF="neumann1-g1-headroom-diverse-v1/"
GROUPS=(
    "lib/General_Track/woosuk/",
    "lib/General_Track/from_2018/",
    "lib/Inv_Track/andrew_lustre/",
    "lib/General_Track/bv-invertibility-conditions/"
)
LOCKED=[
"lib/General_Track/woosuk/avg-opt-old.eqn_sygus_iter_24_3.sl",
"lib/General_Track/woosuk/odd_even_3input-opt.eqn_sygus_iter_92_1.sl",
"lib/General_Track/woosuk/sorting_naive.eqn_sygus_iter_256_0.sl",
"lib/General_Track/from_2018/max6.sl",
"lib/General_Track/from_2018/unbdd_inv_gen_fig1.sl",
"lib/General_Track/from_2018/hd-04-d0-prog.sl",
"lib/Inv_Track/andrew_lustre/rtp_7.lus.sl",
"lib/Inv_Track/andrew_lustre/FIREFLY_luke_1b_e1_1139_e2_2893.lus.sl",
"lib/Inv_Track/andrew_lustre/rtp_3.lus.sl",
"lib/General_Track/bv-invertibility-conditions/ic_bvule_bvmul.sl",
"lib/General_Track/bv-invertibility-conditions/ic_bvule_bvshl1.sl",
"lib/General_Track/bv-invertibility-conditions/ic_bvuge_bvlshr1.sl",
]
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("official_four_family_new12_first")
RELEASE_SHA="0af677313c8277dc558d3049b192389db4d975d31c968fbd6f31cf0849ee411d"

def choose():
    files=subprocess.check_output(["git","-C",str(ROOT),"ls-tree","-r","--name-only","HEAD"],text=True).splitlines()
    result=[]
    for group in GROUPS:
        pool=[p for p in files if p.startswith(group) and p.endswith(".sl")
              and (group!=GROUPS[1] or "/" not in p[len(group):])]
        pool.sort(key=lambda p:(sha256((PREF+p).encode()),p))
        assert len(pool)>=3
        result.extend(pool[:3])
    assert result==LOCKED,("PREREG_FILENAME_DRIFT",result)
    return result

def original_metadata(b):
    try:
        fs=top_level_forms(b.decode("utf8"))
        tags=collections.Counter(get_cmd(f[2]) for f in fs)
        return {k:int(v) for k,v in tags.items() if k in
              ("constraint","inv-constraint","synth-fun","synth-inv",
               "check-synth","set-logic","define-fun","declare-var")}
    except Exception as e:
        return {"parse_metadata_error":type(e).__name__+":"+str(e)[:120]}

def main():
    original=subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()
    assert original==PIN
    v=subprocess.check_output(["cvc5","--version"],text=True).strip().splitlines()[0]
    assert v.startswith("cvc5 1.4.2 "),v
    OUT.mkdir(exist_ok=True)
    rows=[]
    for i,path in enumerate(choose()):
        raw=(ROOT/path).read_bytes()
        row={"index":i,"original_filename":path,"source_file_sha256":sha256(raw),
             "source_bytes":len(raw),"source_form_counts":original_metadata(raw),
             "native_candidate_verification":"NOT_YET_INDEPENDENTLY_VERIFIED",
             "strong_baseline_full_source":True,"original_unchanged":True}
        stdout,stderr,cost=run_solver(ROOT/path)
        (OUT/("%02d.native.stdout"%i)).write_text(stdout)
        (OUT/("%02d.native.stderr"%i)).write_text(stderr)
        row["native_cost"]=cost
        lowered=(stdout+"\n"+stderr).lower()
        row["native_define_fun_count"]=stdout.count("(define-fun")
        if cost["forced"] or cost["returncode"] in (-6,-9,-24):
            row["status"]="C_NATIVE_BUDGET_HOLD"
        elif cost["returncode"]!=0 or any(
            x in lowered for x in ("(error","parse error","unsupported","exception")):
            row["status"]="HOLD_FORMAT_OR_NATIVE_ERROR"
        elif row["native_define_fun_count"]>0:
            row["status"]="C_NATIVE_PROGRAM_RETURNED_UNVERIFIED"
        elif "infeasible" in lowered:
            row["status"]="C_DECLARED_INFEASIBLE_UNVERIFIED"
        else:
            row["status"]="HOLD_NO_PROGRAM_OR_INDETERMINATE"
        rows.append(row)
        print("OFFICIAL_FOUR_FAMILY_12",i,path,row["status"],
              cost["wall_seconds"],flush=True)
    output={
        "intent":"New original official four-family modern CVC5 strong baseline FIRST only",
        "original_repository":SOURCE,"original_commit":PIN,
        "prior_filenames_only_inventory_json_sha256":INVENTORY_SHA,
        "pre_content_selection_seed":PREF,
        "original_filename_order":LOCKED,
        "strong_professional_cvc5_version":v,
        "strong_cvc5_release_asset_sha256":RELEASE_SHA,
        "cost_limits":"CPU 12 hard / wall 15 hard / RSS sampled >=800MiB hard",
        "native_candidate_proof":"NOT_RUN",
        "neural_train_on_new_originals":"NOT_RUN",
        "n_task_denominator":12,
        "native_status_counts":dict(collections.Counter(r["status"] for r in rows)),
        "source_track_unique":4,
        "independent_real_world_original_authors":"NOT_VERIFIED",
        "G1":"HOLD","G2":"NOT_RUN","global_Q1_Q7":"OPEN",
        "rows":rows}
    file=OUT/"FOUR_FAMILY_NEW12_OFFICIAL_CVC5_142_FIRST.json"
    file.write_text(json.dumps(output,sort_keys=True,indent=2))
    print("FIRST_SHA256",sha256(file.read_bytes()),flush=True)
    print("SUMMARY",json.dumps(output["native_status_counts"],sort_keys=True),flush=True)
    print("NATIVE_PROCESS_CPU_SUM",round(sum(
        r["native_cost"]["cpu_user_seconds"]+r["native_cost"]["cpu_system_seconds"]
        for r in rows),6),flush=True)
if __name__=="__main__":main()
