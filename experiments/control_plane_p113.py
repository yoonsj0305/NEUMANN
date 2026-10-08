"""First-only, paired P1.13 diagnostic and independent model-free replay."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
from time import perf_counter_ns

from neumann1.control_plane_v1 import digest
from neumann1.control_plane_p113 import build_bundle, pairs, scores_from_logits, select
from neumann1.control_plane_p17 import compile_references
from neumann1.control_plane_p18 import prune_candidates
from experiments.control_plane_p111_registration import (
    semantic_ir_from_bundle, lexical_overlap_receipt, _all_answers,
)
from experiments.control_plane_p14_registration import _checker
from experiments.control_plane_p113_catalog import catalog

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "docs/experiments/control_plane_p113.preregister.json"
ARMS = ("baseline", "nli")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def registration():
    reg = json.loads(REG.read_bytes())
    rows, refs = catalog()
    if reg["public_sha256"] != digest(rows) or reg["references_sha256"] != digest(refs):
        raise ValueError("registered task/reference drift")
    if reg["scores_seen_at_registration"] is not False or reg["first_only"] is not True:
        raise ValueError("first-only preregistration required")
    for name, expected in reg["source_sha256"].items():
        if sha(ROOT / name) != expected:
            raise ValueError("source drift: " + name)
    return reg, rows, refs


def prepare(row):
    parsed, bundle = build_bundle(row["view"])
    pruning = prune_candidates(parsed,bundle)
    indexes = list(range(len(bundle["candidates"])))
    if pruning["unknown_indexes"] or pruning["sat_indexes"] != indexes:
        raise ValueError("fully multi-feasible construction required")
    ir, entities = semantic_ir_from_bundle(row["view"],parsed,bundle,indexes)
    return parsed,bundle,pruning,ir,entities


def construction():
    _, rows, refs = registration()
    from experiments.control_plane_p111_catalog import catalog as old11
    from experiments.control_plane_p112_catalog import catalog as old12
    old_ir = [prepare(r)[3] for r in old11()[0]+old12()[0]]
    old_roles = {c["role"] for ir in old_ir for c in ir["candidates"]}
    old_queries = {r["view"]["public"]["query"] for r in old11()[0]+old12()[0]}
    probes = 0
    for row, ref in zip(rows,refs):
        parsed,bundle,pruning,ir,entities = prepare(row)
        if row["view"]["public"]["query"] in old_queries:
            raise ValueError("old query reused")
        if any(c["role"] in old_roles for c in ir["candidates"]):
            raise ValueError("old candidate role reused")
        lexical = lexical_overlap_receipt(ir)
        if any(r["score"] for r in lexical["candidates"]):
            raise ValueError("exact-token overlap shortcut")
        for arm in ARMS:
            pairs(ir,arm)
        checker = _checker(ref)
        for i in pruning["sat_indexes"]:
            answers = list(_all_answers(compile_references(parsed,bundle,i)["public"]))
            if not answers or any(checker(a) for a in answers) != (i == ref["expected_candidate"]):
                raise ValueError("original obligation does not distinguish candidates")
        if not checker(ref["witness"]) or checker({e:999999 for e in entities.values()}):
            raise ValueError("checker positive/negative control failure")
        probes += pruning["probe_calls"]
    return {"registration_valid":True,"tasks":len(rows),"multi_feasible":len(rows),
            "feasibility_calls_per_arm":probes,"lexical_unique":0,"weights_loaded":False,
            "model_inference":False,"new_roles_only":True}


def run_item(row, ref, judge):
    began = perf_counter_ns()
    result = {"task_id":row["task_id"],"arm":judge.arm,"status":"FAILED",
        "accepted":False,"selected_candidate":None,"error":None,"model_calls":0,
        "neural_forward_calls":0,"generated_calls":0,"verifier_calls":0,"tool_calls":0,
        "input_rows":None,"input_tokens":None,"padded_tokens":None,
        "feasibility_calls":0,"feasibility_nodes":0,"feasibility_constraint_checks":0}
    try:
        start = perf_counter_ns()
        parsed,bundle,pruning,ir,entities = prepare(row)
        result.update(semantic_ir=ir,candidate_entities=entities,pruning_receipt=pruning,
            deterministic_ms=(perf_counter_ns()-start)/1e6,
            feasibility_calls=pruning["probe_calls"],feasibility_nodes=pruning["nodes"],
            feasibility_constraint_checks=pruning["constraint_checks"])
        result["model_calls"] = 1
        before = judge.forward_calls
        try:
            receipt = judge.score(ir)
        finally:
            result["neural_forward_calls"] = judge.forward_calls-before
            result["partial_selector"] = judge.last_attempt
        result["selector_receipt"] = receipt
        for k in ("input_rows","input_tokens","padded_tokens"):
            result[k] = receipt[k]
        if result["neural_forward_calls"] != 1 or receipt["forward_calls"] != 1:
            raise ValueError("one batched forward required")
        position = select(receipt["scores"])
        if position is None:
            result["status"] = "ABSTAINED"
        else:
            entity = ir["candidates"][position]["entity"]
            chosen = next(i for i,e in entities.items() if e == entity)
            result["selected_candidate"] = chosen
            start = perf_counter_ns()
            project = compile_references(parsed,bundle,chosen)["public"]
            cached = pruning["candidates"][chosen]
            if cached["project_sha256"] != digest(project) or cached["status"] != "SAT":
                raise ValueError("source-bound witness cache drift")
            result["tool_calls"] = 1
            answer = cached["witness"]
            result["answer"] = answer
            result["execution_ms"] = (perf_counter_ns()-start)/1e6
            start = perf_counter_ns()
            result["verifier_calls"] = 1
            result["accepted"] = bool(_checker(ref)(answer))
            result["verification_ms"] = (perf_counter_ns()-start)/1e6
            result["status"] = "ACCEPTED" if result["accepted"] else "REJECTED_BY_ORIGINAL_VERIFIER"
    except Exception as exc:
        result["error"] = type(exc).__name__+": "+str(exc)
        attempt = judge.last_attempt
        if attempt:
            for k in ("input_rows","input_tokens","padded_tokens"):
                result[k] = attempt.get(k)
    finally:
        result["complete_ms"] = (perf_counter_ns()-began)/1e6
    return result


def evaluate(records, reg, arm_costs):
    rows, refs = catalog()
    accepted = {arm:sum(r["accepted"] for r in records if r["arm"] == arm) for arm in ARMS}
    verdict, reason = "NOT_EVALUATED", "INCOMPLETE_OR_ACCOUNTING_DRIFT"
    exact = [(a,r["task_id"]) for a in ARMS for r in rows]
    if [(r["arm"],r["task_id"]) for r in records] == exact:
        valid = all(r["error"] is None and r["model_calls"] == 1 and
            r["neural_forward_calls"] == 1 and r["generated_calls"] == 0 and
            r["status"] in ("ACCEPTED","REJECTED_BY_ORIGINAL_VERIFIER","ABSTAINED") and
            all(type(r[k]) is int and r[k] >= 0 for k in ("input_rows","input_tokens","padded_tokens"))
            for r in records)
        for arm in ARMS:
            chosen_rows = [r for r in records if r["arm"] == arm]
            for r,row in zip(chosen_rows,rows):
                count = len(prepare(row)[3]["candidates"])
                valid &= r["feasibility_calls"] == count and r["input_rows"] == count
                valid &= r["tool_calls"] == r["verifier_calls"] == int(r["selected_candidate"] is not None)
                if r.get("selector_receipt"):
                    receipt = r["selector_receipt"]
                    valid &= receipt["forward_calls"] == 1
                    valid &= all(r[k] == receipt[k] for k in ("input_rows","input_tokens","padded_tokens"))
                    valid &= r["padded_tokens"] >= r["input_tokens"] > 0
                else:
                    valid = False
        valid &= all(type(r["complete_ms"]) in (float,int) and math.isfinite(r["complete_ms"]) and
                     r["complete_ms"] >= 0 for r in records)
        if valid and set(arm_costs) == set(ARMS):
            if any(not math.isfinite(c["complete_ms"]) or c["complete_ms"] < 0 for c in arm_costs.values()):
                return {"verdict":"NOT_EVALUATED","reason":"INVALID_ARM_WALL_RECEIPT"}
            bounded = all(r["complete_ms"] <= reg["gate"]["per_item_wall_ms"] and
                r["selector_receipt"]["complete_ms"] <= reg["gate"]["selector_wall_ms"] for r in records)
            bounded &= all(c["complete_ms"] <= reg["gate"]["per_arm_wall_ms"] for c in arm_costs.values())
            if not bounded:
                verdict,reason = "FAIL","COST_CAP"
            elif accepted["nli"] >= reg["gate"]["accepted_min"] and accepted["nli"] > accepted["baseline"]:
                verdict,reason = "PASS","PAIRED_OPENED_DEVELOPMENT_ONLY"
            else:
                verdict,reason = "FAIL","CAPABILITY_OR_NO_PAIRED_GAIN"
    wins = losses = 0
    if len(records) == 2*len(rows):
        for b,n in zip(records[:len(rows)],records[len(rows):]):
            wins += int(n["accepted"] and not b["accepted"])
            losses += int(b["accepted"] and not n["accepted"])
    return {"verdict":verdict,"reason":reason,"accepted":accepted,"paired_wins":wins,
        "paired_losses":losses,"development_only":True,"fresh_validation_registered":False,
        "p2_admitted":False,"decision3_admitted":False,"global_questions_closed":[],
        "economic_advantage_established":False,"energy":None,"flops":None,"money":None}


def run(out, sources):
    import resource
    from neumann1.control_plane_p113 import FrozenJudge
    import torch
    reg, rows, refs = registration()
    out.mkdir(parents=True,exist_ok=False)
    write(out/"preregister.json",reg)
    write(out/"public.json",rows)
    write(out/"references.json",refs)
    began = perf_counter_ns()
    records, arm_costs, error = [], {}, None
    try:
        for arm in ARMS:
            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
            start = perf_counter_ns()
            judge = FrozenJudge(arm,str(sources[arm]))
            startup_ms = (perf_counter_ns()-start)/1e6
            for row,ref in zip(rows,refs):
                records.append(run_item(row,ref,judge))
                write(out/"records.json",records)
            arm_costs[arm] = {"parameters":judge.parameters,"startup_ms":startup_ms,
                "complete_ms":(perf_counter_ns()-start)/1e6,
                "peak_gpu_allocated_bytes":torch.cuda.max_memory_allocated(),
                "peak_gpu_reserved_bytes":torch.cuda.max_memory_reserved(),
                "process_peak_rss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
            del judge
    except Exception as exc:
        error = type(exc).__name__+": "+str(exc)
    report = {"schema":"neumann.control-plane-p1.13.paired-first.v1",
        "status":"COMPLETE" if len(records) == 24 and error is None else "INCOMPLETE",
        "error":error,"whole_study_ms":(perf_counter_ns()-began)/1e6,
        "arm_costs":arm_costs,"result":evaluate(records,reg,arm_costs),
        "reg_sha256":sha(out/"preregister.json")}
    write(out/"report.json",report)
    write(out/"records.json",records)
    return report


def replay(out):
    reg,rows,refs = registration()
    report = json.loads((out/"report.json").read_bytes())
    records = json.loads((out/"records.json").read_bytes())
    if json.loads((out/"preregister.json").read_bytes()) != reg or report["reg_sha256"] != sha(out/"preregister.json"):
        raise ValueError("retained preregistration drift")
    if json.loads((out/"public.json").read_bytes()) != rows or json.loads((out/"references.json").read_bytes()) != refs:
        raise ValueError("retained task drift")
    for record in records:
        index = next(i for i,r in enumerate(rows) if r["task_id"] == record["task_id"])
        parsed,bundle,pruning,ir,entities = prepare(rows[index])
        if record["error"]:
            continue  # partial record is retained; never promoted to evaluated PASS
        if record["semantic_ir"] != ir or record["pruning_receipt"] != pruning:
            # Pruning includes measured timing; compare identity and deterministic work below.
            if record["semantic_ir"] != ir:
                raise ValueError("semantic source drift")
        retained = record["pruning_receipt"]
        for key in ("probe_calls","nodes","constraint_checks","sat_indexes","unknown_indexes"):
            if retained[key] != pruning[key]:
                raise ValueError("deterministic work drift")
        receipt = record["selector_receipt"]
        if receipt["pairs"] != [list(p) for p in pairs(ir,record["arm"])]:
            raise ValueError("learned input leakage/drift")
        scores = scores_from_logits(receipt["logits"],record["arm"])
        if scores != receipt["scores"]:
            raise ValueError("score derivation drift")
        position = select(scores)
        chosen = None if position is None else next(i for i,e in entities.items() if e == ir["candidates"][position]["entity"])
        if chosen != record["selected_candidate"]:
            raise ValueError("rank decision drift")
        accepted = False
        if chosen is not None:
            answer = pruning["candidates"][chosen]["witness"]
            if record["answer"] != answer:
                raise ValueError("selected witness drift")
            accepted = bool(_checker(refs[index])(answer))
        if accepted != record["accepted"] or record["feasibility_calls"] != pruning["probe_calls"]:
            raise ValueError("original correctness/cost drift")
        expected_status = "ABSTAINED" if chosen is None else ("ACCEPTED" if accepted else "REJECTED_BY_ORIGINAL_VERIFIER")
        if record["status"] != expected_status:
            raise ValueError("terminal status drift")
    derived = evaluate(records,reg,report["arm_costs"])
    if derived != report["result"]:
        raise ValueError("verdict drift")
    return {"integrity":True,"model_loaded":False,"records":len(records),"result":derived}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode",choices=("check","run","replay"))
    p.add_argument("--out",type=Path)
    p.add_argument("--baseline",type=Path)
    p.add_argument("--nli",type=Path)
    args = p.parse_args()
    result = construction() if args.mode == "check" else (
        run(args.out,{"baseline":args.baseline,"nli":args.nli}) if args.mode == "run" else replay(args.out))
    print(json.dumps(result,ensure_ascii=False,indent=2))
