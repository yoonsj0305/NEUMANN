"""Opened engineering protocol,not a G0/G1 cost/capability gate."""
import argparse
import itertools
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.representation_headroom import digest,package_identity,save
from experiments.recursive_summary_cases import known_summary,lifted_prefix,tree
from neumann1.recursive_summary import CertifiedSummary,check_summary,reference
from neumann1.recursive_symbolic_baseline import propose
from neumann1.synduce_reference import reference_projection

SOURCES=["neumann1/recursive_summary.py","neumann1/recursive_symbolic_baseline.py",
         "neumann1/synduce_reference.py","neumann1/recursive_summary_data.py",
         "experiments/recursive_summary_cases.py","experiments/recursive_summary_integration.py"]


def read(path):return json.loads(path.read_text(encoding="utf-8"))


def freeze(source,preparation):
    manifest=read(source/"manifest.json")
    assert all(digest(source/r["path"])==r["sha256"] for r in manifest["files"])
    preparation.mkdir(parents=True,exist_ok=False)
    reg={"identity":"RECURSIVE_SUMMARY_ENGINEERING_V1","kind":"OPENED_ADAPTED_REFERENCES_NOT_G0_G1",
         "source_commit":manifest["commit"],"upstream_manifest_sha256":digest(source/"manifest.json"),
         "reference_cases":["sum","mps","mts","mss"],"fixture_cases":["lifted_prefix"],
         "alphabet":[-2,0,3],"max_length":5,"tree_shapes":["left","right","balanced"],
         "native_synthesis_timeout_ms":5000,"native_worker_deadline_seconds":20,
         "source_semantics":"projected mathematical integer Nil/Cons reference only,not whole OCaml machine-int/representation/Synduce protocol",
         "native":"public-only Houdini plus bounded CVC5 SyGuS,fixed reference width,max/pairwise-sum grammar; not full Synduce",
         "preview_exposure":"sum public native preview and all source reads/test fixtures opened before registration",
         "O_role":"known offline formulas explicitly supplied,no learned discovery claim",
         "performance_gate":None,"fresh_eligible":0,"G0_passed":False,"G1_admitted":False,
         "sources":{p:digest(ROOT/p) for p in SOURCES},
         "packages":{p:package_identity(p) for p in ["cvc5","z3-solver","sympy","mpmath"]}}
    save(preparation/"registration.json",reg)
    for name in SOURCES:
        target=preparation/"source"/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((ROOT/name).read_bytes())
    save(preparation/"freeze-receipt.json",{"registration_sha256":digest(preparation/"registration.json"),"engineering_only":True})
    print(digest(preparation/"registration.json"),flush=True)


def worker(public,output,timeout_ms):
    output.mkdir(parents=True,exist_ok=False)
    problem=read(public)
    save(output/"progress.json",{"phase":"public loaded,no Oracle input"})
    result=propose(problem,timeout_ms=timeout_ms,checkpoint=lambda value:save(output/"progress.json",value))
    save(output/"result.json",result)


def run(source,preparation,output):
    reg=read(preparation/"registration.json")
    assert digest(preparation/"registration.json")==read(preparation/"freeze-receipt.json")["registration_sha256"]
    assert digest(source/"manifest.json")==reg["upstream_manifest_sha256"]
    assert all(digest(ROOT/p)==pin for p,pin in reg["sources"].items())
    assert all(package_identity(p)==pin for p,pin in reg["packages"].items())
    output.mkdir(parents=True,exist_ok=False)
    for sub in ["public","offline","fixtures","native"]:(output/sub).mkdir()
    summaries=[];queries=0;identities=0
    values=[list(v) for n in range(reg["max_length"]+1) for v in itertools.product(reg["alphabet"],repeat=n)]
    with (output/"witnesses.jsonl").open("w",encoding="utf-8") as stream:
        for identifier in reg["reference_cases"]+reg["fixture_cases"]:
            fixture=identifier in reg["fixture_cases"]
            if fixture:problem,manual=lifted_prefix()
            else:
                original=source/"benchmarks/list"/(identifier+".ml")
                problem=reference_projection(original.read_text(encoding="utf-8"))
                manual=known_summary(problem,identifier)
            path=output/("fixtures" if fixture else "public")/(identifier+".json")
            save(path,problem)
            certificate=check_summary(problem,manual)
            assert certificate["accepted"]
            save(output/"offline"/(identifier+".json"),{"proposal":manual,"certificate":certificate,"role":"O,known formula not discovery"})
            candidates={"KNOWN_OFFLINE_REFERENCE":manual}
            if not fixture:
                folder=output/"native"/identifier
                try:
                    child=subprocess.run([sys.executable,"-X","utf8",str(Path(__file__).resolve()),"worker",
                        "--public",str(path),"--output",str(folder),"--timeout-ms",str(reg["native_synthesis_timeout_ms"])],
                        capture_output=True,text=True,timeout=reg["native_worker_deadline_seconds"])
                    event={"exit_code":child.returncode,"stderr":child.stderr[-4000:],"timeout":False}
                except subprocess.TimeoutExpired as error:
                    event={"exit_code":None,"timeout":True,"stderr":str(error.stderr or "")[-4000:]}
                if (folder/"result.json").exists():
                    native=read(folder/"result.json")
                    event["synthesis_status"]=native["status"];event["accepted"]=native["accepted"]
                    if child.returncode==0 and native["accepted"]:candidates["PUBLIC_SYGUS_GENERATED"]=native["proposal"]
                else:event["accepted"]=False
                save(output/"native"/(identifier+".receipt.json"),event)
            case={"id":identifier,"source_role":"F" if fixture else "D","routes":list(candidates),"witnesses":0}
            for route,candidate in candidates.items():
                engine=CertifiedSummary(problem,candidate)
                identities+=len(engine.certificate["obligations"])
                for sequence in values:
                    expected=reference(problem,sequence)
                    for shape in reg["tree_shapes"]:
                        t=tree(sequence,shape);actual=engine.run(t)
                        assert actual==expected
                        stream.write(json.dumps({"case":identifier,"route":route,"values":sequence,"shape":shape,"tree":t,"actual":actual,"reference":expected})+"\n")
                        queries+=1;case["witnesses"]+=1
                stream.flush()
            summaries.append(case)
            print(json.dumps(case),flush=True)
    fixture_problem,fixture_proposal=lifted_prefix()
    controls={}
    import copy
    for name in ["wrong_order","vacuous_invariant","wrong_goal"]:
        bad=copy.deepcopy(fixture_proposal)
        if name=="wrong_order":bad["merge"]["outputs"][0]=["max","r0",["add","r1","l0"]]
        elif name=="vacuous_invariant":bad["invariant"]["outputs"]=[False]
        else:bad["decode"]["outputs"]=["z1"]
        result=check_summary(fixture_problem,bad)
        assert result["status"]=="REFUTED"
        controls[name]={"proposal":bad,"check":result}
    save(output/"false_proposals.json",controls)
    insufficient={"left1":[],"left2":[-5],"right":[4],"same_left_prefix":[0],
                  "concat_outputs":[reference(fixture_problem,[4]),reference(fixture_problem,[-5,4])],
                  "scope":"prefix-alone fixed statistic cannot determine ordered concat goal; not all scalar encodings impossible"}
    assert insufficient["concat_outputs"][0]!=insufficient["concat_outputs"][1]
    save(output/"insufficient_fixed_statistic.json",insufficient)
    report={"identity":reg["identity"],"status":"PASS_ENGINEERING_ADAPTED_REFERENCE_CHECKS_ONLY","cases":summaries,
            "paired_numeric_queries":queries,"universal_obligations_for_accepted_routes":identities,
            "public_native_accepted_cases":sum("PUBLIC_SYGUS_GENERATED" in c["routes"] for c in summaries),
            "public_reference_cases":4,"manual_lifted_fixture_cases":1,"false_proposals_rejected":3,
            "fresh_eligible":0,"learned_policy_implemented":False,"G0_passed":False,"G1_admitted":False,
            "performance_measured":False,"full_Synduce_installed_or_run":False}
    save(output/"report.json",report)
    save(output/"manifest.json",{str(p.relative_to(output)):digest(p) for p in output.rglob("*") if p.is_file() and p.name!="manifest.json"})
    save(preparation/"first-result-receipt.json",{"report_sha256":digest(output/"report.json"),"manifest_sha256":digest(output/"manifest.json")})
    print(json.dumps(report),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=["freeze","run","worker"])
    for key in ["source","preparation","output","public"]:parser.add_argument("--"+key,type=Path)
    parser.add_argument("--timeout-ms",type=int,default=5000)
    args=parser.parse_args()
    if args.mode=="freeze":freeze(args.source,args.preparation)
    elif args.mode=="run":run(args.source,args.preparation,args.output)
    else:worker(args.public,args.output,args.timeout_ms)
