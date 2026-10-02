"""Receipt-only Frontier Gap audit. No model calls or global closure claims.

Trusted callbacks must independently establish original-task validity and actual
complete execution provenance. Hashes alone do not prove either. Unit fixtures
are not research observations; this module provides an interface, not attestation.
"""
from __future__ import annotations

import hashlib
import json
import math
from statistics import mean

NAMESPACE = "north_star_2026_10_02"
ROLES = ("small", "frontier", "neumann")
METRICS = ("compute", "ram_bytes", "vram_bytes", "latency_ms", "energy_j", "cost")
QUESTIONS = {
    "Q1": "structure_reduces_compute", "Q2": "original_capability_preserved",
    "Q3": "oracle_free_hidden_structure", "Q4": "cheap_discovery",
    "Q5": "complete_end_to_end_less_than_direct", "Q6": "unseen_open_set_scaling_transfer",
    "Q7": "real_frontier_capability_gap_recovery",
}


def digest(raw):
    if type(raw) is not bytes:
        raise ValueError("retained artifact bytes required")
    return hashlib.sha256(raw).hexdigest()


def manifest_digest(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def _number(value, label, minimum=0, maximum=None):
    if (type(value) not in (int, float) or not math.isfinite(value) or value < minimum
            or (maximum is not None and value > maximum)):
        raise ValueError("invalid " + label)
    return value


def _hash(value, length=64):
    if type(value) is not str or len(value)!=length or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("explicit lowercase content/head hash required")
    return value


def _text(value):
    if type(value) is not str or not value.strip():
        raise ValueError("explicit identity/unit required")
    return value


def _artifact(ref, blobs):
    _hash(ref)
    if ref not in blobs or digest(blobs[ref])!=ref:
        raise ValueError("missing or replaced retained artifact")
    return blobs[ref]


def validate_manifest(m):
    if (m["schema"]!="neumann.frontier-gap.manifest.v1" or m["question_namespace"]!=NAMESPACE
            or m["candidate_input_policy"]!="original_task_only"
            or m["gap_membership"]!="small_and_frontier_only" or m["new_fitting"] is not False):
        raise ValueError("Frontier Gap authority drift")
    _hash(m["frozen_head"],40);_text(m["verifier_id"])
    if type(m["repeats"]) is not int or m["repeats"]<1:
        raise ValueError("frozen repeat count required")
    if (not m["tasks"] or len({t["id"] for t in m["tasks"]})!=len(m["tasks"])):
        raise ValueError("unique nonempty frozen original corpus required")
    for t in m["tasks"]:
        _text(t["id"]);_text(t["family"]);_hash(t["problem_sha256"])
        _text(t["source"]);_text(t["license"])
        if t["split"]!="fresh_evaluation":
            raise ValueError("opened development is not a fresh final set")
    if set(m["systems"])!=set(ROLES):
        raise ValueError("all three frozen system identities required")
    authorities=[]
    for role in ROLES:
        s=m["systems"][role];_text(s["id"]);_text(s["revision"])
        budget=s["budget"]
        if type(budget["max_calls"]) is not int or budget["max_calls"]<1:
            raise ValueError("explicit positive call cap required")
        _number(budget["max_cost"],"cost cap")
        if _number(budget["max_latency_ms"],"deadline")==0:
            raise ValueError("explicit positive deadline required")
        if type(s["tools"]) is not list or len(s["tools"])!=len(set(s["tools"])):
            raise ValueError("explicit unique tool authority required")
        for tool in s["tools"]:_text(tool)
        authorities.append(sorted(s["tools"]))
    if len({(s["id"],s["revision"]) for s in m["systems"].values()})!=3:
        raise ValueError("distinct small/frontier/system comparators required")
    if authorities[0]!=authorities[1] or authorities[0]!=authorities[2]:
        raise ValueError("unequal eligible tool authority")
    p=m["thresholds"]
    for k in ("small_success_max","frontier_success_min","neumann_success_min","quality_delta_max"):
        _number(p[k],k,0,1)
    if p["small_success_max"]>=p["frontier_success_min"]:
        raise ValueError("degenerate capability gap thresholds")
    for k in ("min_gap_cases","min_gap_families"):
        if type(p[k]) is not int or p[k]<1:raise ValueError("positive frozen gap coverage required")
    if set(m["metric_units"])!=set(METRICS) or set(p["resource_ratio_max"])!=set(METRICS):
        raise ValueError("all explicit resource axes required")
    fixed={"ram_bytes":"bytes","vram_bytes":"bytes","latency_ms":"ms","energy_j":"J"}
    for metric in METRICS:
        _text(m["metric_units"][metric])
        if metric in fixed and m["metric_units"][metric]!=fixed[metric]:
            raise ValueError("invalid resource unit")
        v=_number(p["resource_ratio_max"][metric],metric,0,1)
        if v==0 or v==1:raise ValueError("strict positive saving threshold required")
    _text(m["compute_metric"]);_text(m["accounting_policy"])
    _text(m["cold_start_policy"]);_text(m["investment_accounting"])


def _resources(checked, ids, iso):
    ratios={};statuses={};totals={r:{} for r in ("frontier","neumann")}
    for metric in METRICS:
        values={r:[x["resources"][metric] for x in checked if x["task_id"] in ids and x["role"]==r]
                for r in totals}
        flat=[v for group in values.values() for v in group]
        measured=bool(flat and all(v["status"]=="measured" for v in flat))
        statuses[metric]="measured" if measured else ("unavailable" if not flat or any(v["status"]=="unavailable" for v in flat) else "estimated")
        for role,group in values.items():
            known=group and all(v["value"] is not None for v in group)
            aggregate=max if metric in ("ram_bytes","vram_bytes") else mean
            totals[role][metric]=aggregate(v["value"] for v in group) if known else None
        denom=totals["frontier"][metric]
        ratios[metric]=(totals["neumann"][metric]/denom if measured and denom>0 and iso else None)
    return totals,ratios,statuses


def audit(manifest, records, blobs, *, verify_original, validate_trace):
    """Recompute gap/capability from trusted checks, retain failures and unknowns.

    verify_original(problem_bytes,answer_bytes,verifier_id) -> bool.
    validate_trace(raw_trace_bytes,record,manifest) -> bool must independently
    validate actual system identity, EVERY attempt and complete resource costs.
    Neither callback has a default. They are trusted adapters, not auto-proven.
    """
    validate_manifest(manifest)
    if not callable(verify_original) or not callable(validate_trace):
        raise ValueError("independent verifier and provenance adapters required")
    tasks={t["id"]:t for t in manifest["tasks"]};mh=manifest_digest(manifest)
    expected={(t,r,i) for t in tasks for r in ROLES for i in range(manifest["repeats"])}
    seen=set();checked=[]
    for row in records:
        if type(row["repeat"]) is not int:raise ValueError("integer repeat required")
        key=(row["task_id"],row["role"],row["repeat"])
        if key not in expected or key in seen:raise ValueError("duplicate/unregistered observation")
        seen.add(key);task=tasks[row["task_id"]];system=manifest["systems"][row["role"]]
        if (row["manifest_sha256"]!=mh or row["problem_sha256"]!=task["problem_sha256"]
                or row["system_id"]!=system["id"] or row["system_revision"]!=system["revision"]
                or row["complete"] is not True):
            raise ValueError("receipt/original/system authority drift")
        problem=_artifact(row["problem_sha256"],blobs)
        answer=_artifact(row["answer_sha256"],blobs)
        trace=_artifact(row["trace_sha256"],blobs)
        if not problem:raise ValueError("empty original task")
        if set(row["resources"])!=set(METRICS):raise ValueError("missing resource axis")
        for metric,value in row["resources"].items():
            status=value["status"]
            if value["unit"]!=manifest["metric_units"][metric]:raise ValueError("incompatible units")
            _artifact(value["trace_sha256"],blobs)
            if status=="unavailable":
                if value["value"] is not None:raise ValueError("unknown is not zero")
            elif status in ("measured","estimated"):_number(value["value"],metric)
            else:raise ValueError("unknown measurement provenance")
        provenance=validate_trace(trace,row,manifest)
        if type(provenance) is not bool or not provenance:
            raise ValueError("complete execution provenance rejected")
        error=None
        try:
            accepted=verify_original(problem,answer,manifest["verifier_id"])
        except Exception as exc:
            accepted=False;error=f"{type(exc).__name__}: {exc}"
        if type(accepted) is not bool:
            raise ValueError("verifier must return actual Boolean")
        checked.append({"task_id":key[0],"role":key[1],"repeat":key[2],
            "verified_original":accepted,"verification_error":error,"resources":row["resources"]})
    if seen!=expected:raise ValueError("incomplete paired coverage including failures")
    quality={t:{r:mean(x["verified_original"] for x in checked if x["task_id"]==t and x["role"]==r)
                for r in ROLES} for t in tasks}
    p=manifest["thresholds"]
    eligible={t for t in tasks if not any(x["verification_error"] for x in checked
              if x["task_id"]==t and x["role"] in ("small","frontier"))}
    gap=[t["id"] for t in manifest["tasks"] if t["id"] in eligible and quality[t["id"]]["small"]<=p["small_success_max"]
         and quality[t["id"]]["frontier"]>=p["frontier_success_min"]]
    families=sorted({tasks[t]["family"] for t in gap});cells=[]
    for family in families:
        ids=[t for t in gap if tasks[t]["family"]==family]
        q={r:mean(quality[t][r] for t in ids) for r in ROLES}
        cells.append({"family":family,"cases":len(ids),"quality":q,
            "iso_capability":q["neumann"]>=p["neumann_success_min"]
                and q["neumann"]>=q["frontier"]-p["quality_delta_max"]})
    q={r:mean(quality[t][r] for t in gap) if gap else None for r in ROLES}
    iso=bool(gap and all(c["iso_capability"] for c in cells)
        and q["neumann"]>=p["neumann_success_min"] and q["neumann"]>=q["frontier"]-p["quality_delta_max"])
    totals,ratios,statuses=_resources(checked,gap,iso)
    for cell in cells:
        ids=[t for t in gap if tasks[t]["family"]==cell["family"]]
        ct,cr,cs=_resources(checked,ids,iso)
        cell.update(resource_totals=ct,resource_ratios=cr,resource_status=cs)
    coverage=len(gap)>=p["min_gap_cases"] and len(families)>=p["min_gap_families"]
    if not gap:decision="NO_VERIFIED_FRONTIER_GAP"
    elif not coverage:decision="INSUFFICIENT_GAP_COVERAGE"
    elif not iso:decision="CAPABILITY_UNREACHED_NO_ISO_CAPABILITY_CLAIM"
    elif any(ratios[k] is None for k in METRICS):decision="PARTIAL_RESOURCE_EVIDENCE_NO_FULL_NORTH_STAR_CLAIM"
    elif (any(ratios[k]>p["resource_ratio_max"][k] for k in METRICS)
          or any(c["resource_ratios"][k] is None or c["resource_ratios"][k]>p["resource_ratio_max"][k]
                 for c in cells for k in METRICS)):decision="MEASURED_RESOURCE_GATE_FAILED"
    else:decision="CASE_SET_GATE_PASSED_NOT_GLOBAL_CLOSURE"
    return {"question_namespace":NAMESPACE,"decision":decision,"gap_task_ids":gap,
        "quality_on_gap":q,"family_cells":cells,"iso_capability":iso,
        "observations":len(checked),"failed_original_verifications":sum(not x["verified_original"] for x in checked),
        "resource_totals":totals,"resource_ratios":ratios,"resource_status":statuses,
        "all_task_quality":quality,"verification_errors":[x for x in checked if x["verification_error"]],
        "global_questions":{k:"OPEN" for k in QUESTIONS},
        "boundary":"Trusted callback receipt audit; no provider attestation, statistical or global closure proof."}
