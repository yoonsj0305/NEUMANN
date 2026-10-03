"""P1.1 balanced coded routing. Advisory scores, never generated control.

Development only. Balancing cancels a fixed additive code prior; it does not
prove invariance to code/problem interactions or useful executor selection.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from time import perf_counter_ns

from neumann1.control_plane_v1 import ROUTES, canonical, digest, finite, public_view, snapshot
from neumann1.control_plane_p1_contract import MODEL, PUBLIC_SHA256, TASK_IDS
from neumann1.general_runtime_v106 import sha as original_core_sha

SCHEMA = "neumann.control-plane-p1.1.v1"
CODES = ("A", "B", "C", "D")
SEMANTICS = {
    "DIRECT": "Normal neural answer reasoning when the other executors are insufficient.",
    "ARITHMETIC": "Exact scalar arithmetic evaluation using explicitly supplied expressions and values.",
    "CSP": "Finite constraint search using explicitly supplied domains and constraints.",
    "PYTHON": "Bounded general Python algorithm implementation and execution when algorithmic work is required.",
}
# Route-index -> code-index. Two disjoint balanced Latin-square schedules;
# each route occupies every code exactly once in each schedule. Not all 24 maps.
SCHEDULES = tuple(tuple(tuple((base[i]+shift)%4 for i in range(4)) for shift in range(4))
                  for base in ((0,1,2,3), (0,2,1,3)))
CRITERIA = {"numeric_tolerance_nats":0.05, "centered_schedule_tolerance_nats":0.5,
            "stable_winner_margin_nats":0.5, "distinct_winners":2,
            "dominant_winner_max":10, "centered_task_range_min_nats":0.001}


@dataclass(frozen=True)
class Budget:
    context_tokens: int = 4096
    evaluated_tokens: int = 196608
    padded_tokens: int = 196608
    input_rows: int = 288
    score_rows: int = 1152
    scored_tokens: int = 1152
    forward_calls: int = 144
    task_wall_ms: float = 120000.0
    controller_wall_ms: float = 180000.0
    study_wall_ms: float = 1800000.0


def contract():
    return {"schema":SCHEMA, "model":dict(MODEL), "codes":list(CODES), "semantics":dict(SEMANTICS),
            "schedules":snapshot(SCHEDULES), "criteria":dict(CRITERIA), "budget":asdict(Budget()),
            "development_public_sha256":PUBLIC_SHA256,
            "modes":["batch4","unbatched1","reverse_batch4"],
            "statistic":"mean_logprob_after_balanced_route_to_code_assignment",
            "token_boundary":"frozen chat prefix followed by one separately encoded non-special code token",
            "code_audit":"exact frozen vocabulary SHA256, single token, distinct, non-special, exact decode",
            "development_only":True, "p2_admitted":False, "decision3_admitted":False,
            "fresh_validation":"UNREGISTERED_UNOPENED_PENDING_DEVELOPMENT_AND_ARCHITECTURE_FREEZE",
            "generated_calls":0, "tool_calls":0, "new_training":False, "frontier_calls":0,
            "sealed_data_opened":False, "calibration_from_tasks":False, "all_24_permutations":False}


def validate_schedules(schedules=SCHEDULES):
    if len(schedules)!=2 or any(len(group)!=4 for group in schedules):
        raise ValueError("two registered four-map schedules required")
    flat=[tuple(p) for group in schedules for p in group]
    if len(set(flat))!=8 or any(sorted(p)!=list(range(4)) for p in flat):
        raise ValueError("eight distinct permutations required")
    for group in schedules:
        if any(sorted(p[r] for p in group)!=list(range(4)) for r in range(4)):
            raise ValueError("each route must occupy every code once per schedule")


def audit_codes(tokenizer):
    # Only a frozen tokenizer is needed; no model, fitting or task rows.
    if original_core_sha(tokenizer.get_vocab()) != MODEL["tokenizer_sha256"]:
        raise ValueError("exact frozen tokenizer vocabulary required")
    ids=[]
    for code in CODES:
        tokens=tokenizer.encode(code, add_special_tokens=False)
        if len(tokens)!=1 or type(tokens[0]) is not int or tokens[0]<0:
            raise ValueError("registered code must be exactly one token: "+code)
        if tokens[0] in tokenizer.all_special_ids or tokenizer.decode(tokens, skip_special_tokens=False)!=code:
            raise ValueError("non-special exact code roundtrip required")
        ids.append(tokens[0])
    if len(set(ids))!=4:
        raise ValueError("distinct code token IDs required")
    return {"codes":list(CODES), "token_ids":ids, "tokenizer_sha256":MODEL["tokenizer_sha256"],
            "single_token":True, "special_tokens":False, "model_inference":False}


def prompt_for(view, mapping):
    original=public_view(view)
    if tuple(sorted(mapping))!=tuple(range(4)):
        raise ValueError("route/code permutation required")
    legend=[]
    for code_index,code in enumerate(CODES):
        route=ROUTES[mapping.index(code_index)]
        legend.append({"code":code,"executor":route,"contract":SEMANTICS[route]})
    return ("Select the computationally sufficient executor for the original public problem. "
            "The legend defines executor capability, not a hidden problem-family label. "
            "No execution or answer is requested. The scored response is one code token.\n"
            +canonical({"legend":legend,"problem":original})+"\nCode:")


@dataclass(frozen=True)
class CodePlan:
    prefixes: tuple[tuple[int,...],...]
    code_ids: tuple[int,...]

    def validate(self):
        if not self.prefixes or len(self.code_ids)!=4 or len(set(self.code_ids))!=4:
            raise ValueError("nonempty prefix rows and four distinct codes required")
        if any(not p or len(p)+1>Budget().context_tokens for p in self.prefixes):
            raise ValueError("nonempty context with one forced code; no truncation")
        if any(type(t) is not int or t<0 for p in self.prefixes for t in p) or any(
                type(t) is not int or t<0 for t in self.code_ids):
            raise ValueError("nonnegative integer token IDs required")


def plan_cost(plan, batch_size):
    plan.validate()
    if type(batch_size) is not int or batch_size<1:
        raise ValueError("positive batch size required")
    rows=len(plan.prefixes)
    return {"input_rows":rows,"score_rows":4*rows,"scored_tokens":4*rows,
            "evaluated_tokens":sum(map(len,plan.prefixes)),
            "padded_tokens":sum(max(map(len,plan.prefixes[i:i+batch_size]))*len(plan.prefixes[i:i+batch_size])
                                for i in range(0,rows,batch_size)),
            "forward_calls":(rows+batch_size-1)//batch_size}


class CodedFailure(RuntimeError):
    def __init__(self, message, known_cost, complete_ms):
        super().__init__(message)
        self.known_cost=dict(known_cost)
        self.complete_ms=complete_ms


class NextCodeBackend:
    """One prefix evaluation supplies all four next-code likelihoods.

    No duplicate prefill per code, no appended labels, KV cache or generation.
    A single forced token's likelihood is the causal final-prefix distribution.
    Attempted model-input rows/tokens are charged before every forward.
    """
    def __init__(self, model, pad_token_id, device):
        self.model=model;self.pad_token_id=pad_token_id;self.device=device
        if type(pad_token_id) is not int or pad_token_id<0:
            raise ValueError("valid pad token required")
        self.versions=tuple(p._version for p in model.parameters())
        self.frozen()

    def frozen(self):
        if self.model.training or any(p.requires_grad for p in self.model.parameters()) or tuple(
                p._version for p in self.model.parameters())!=self.versions:
            raise ValueError("frozen/eval model identity required")

    def evaluate(self, plan, batch_size, remaining_ms):
        import torch
        plan.validate();self.frozen()
        if finite(remaining_ms,True)<=0:raise TimeoutError("no scoring time left")
        device=torch.device(self.device)
        def sync():
            if device.type=="cuda":torch.cuda.synchronize(device)
        sync()
        if device.type=="cuda":torch.cuda.reset_peak_memory_stats(device)
        began=perf_counter_ns();values=[]
        known={k:0 for k in plan_cost(plan,batch_size)}
        try:
            for first in range(0,len(plan.prefixes),batch_size):
                if (perf_counter_ns()-began)/1e6>=remaining_ms:raise TimeoutError("scoring deadline")
                chunk=plan.prefixes[first:first+batch_size];width=max(map(len,chunk))
                ids=torch.full((len(chunk),width),self.pad_token_id,dtype=torch.long,device=device)
                mask=torch.zeros_like(ids)
                positions=sorted({len(p)-1 for p in chunk});index={p:i for i,p in enumerate(positions)}
                for row,prefix in enumerate(chunk):
                    ids[row,:len(prefix)]=torch.tensor(prefix,dtype=torch.long,device=device)
                    mask[row,:len(prefix)]=1
                keep=torch.tensor(positions,dtype=torch.long,device=device)
                known['forward_calls']+=1;known['input_rows']+=len(chunk)
                known['evaluated_tokens']+=sum(map(len,chunk));known['padded_tokens']+=len(chunk)*width
                with torch.inference_mode():
                    output=self.model(input_ids=ids,attention_mask=mask,use_cache=False,logits_to_keep=keep,return_dict=True)
                    if output.logits.shape[:2]!=(len(chunk),len(positions)):
                        raise ValueError("selected causal positions unsupported")
                    logprobs=torch.log_softmax(output.logits.float(),dim=-1)
                    code_ids=torch.tensor(plan.code_ids,dtype=torch.long,device=device)
                    for row,prefix in enumerate(chunk):
                        scores=tuple(finite(v) for v in logprobs[row,index[len(prefix)-1],code_ids].tolist())
                        if any(v>0 for v in scores):raise ValueError("positive log probability")
                        values.append(scores);known['score_rows']+=4;known['scored_tokens']+=4
                sync()
                if (perf_counter_ns()-began)/1e6>=remaining_ms:raise TimeoutError("completed forward deadline")
            self.frozen()
        except Exception as exc:
            raise CodedFailure(type(exc).__name__+": "+str(exc),known,(perf_counter_ns()-began)/1e6) from exc
        peak=int(torch.cuda.max_memory_allocated(device)) if device.type=="cuda" else None
        return {"scores":values,"cost":known,"peak_accelerator_memory_bytes":peak}


def aggregate(matrix):
    validate_schedules()
    if len(matrix)!=8 or any(len(row)!=4 for row in matrix):
        raise ValueError("eight four-code distributions required")
    matrix=[[finite(v) for v in row] for row in matrix]
    if any(v>0 for row in matrix for v in row):raise ValueError("log probabilities required")
    groups=[]
    for group_index,group in enumerate(SCHEDULES):
        groups.append([math.fsum(matrix[4*group_index+i][mapping[r]] for i,mapping in enumerate(group))/4
                       for r in range(4)])
    scores=[math.fsum((groups[0][r],groups[1][r]))/2 for r in range(4)]
    centered=[[v-math.fsum(g)/4 for v in g] for g in groups]
    delta=max(abs(a-b) for a,b in zip(*centered))
    def winner(g):return ROUTES[max(range(4),key=lambda i:(g[i],-i))]
    order=sorted(scores,reverse=True);margin=order[0]-order[1]
    stable=margin<=CRITERIA['stable_winner_margin_nats'] or all(winner(g)==winner(scores) for g in groups)
    return {"scores":dict(zip(ROUTES,scores)),"schedule_scores":groups,"winner":winner(scores),
            "margin_nats":margin,"centered_schedule_delta_nats":delta,"stable_schedule_winner":stable}


def score_development(view, encode_prefix, code_ids, backend, ledger, remaining_ms):
    original=public_view(view);began=perf_counter_ns();passes=[]
    maps=[m for group in SCHEDULES for m in group]
    try:
        # Always evaluate both schedules, all maps and all three execution modes.
        for mode,size,order in (("batch4",4,list(range(8))),("unbatched1",1,list(range(8))),
                                ("reverse_batch4",4,list(reversed(range(8))))):
            start=perf_counter_ns();observation={"mode":mode,"status":"STARTED","order":order,"batch_size":size}
            passes.append(observation)
            plan=CodePlan(tuple(tuple(encode_prefix(prompt_for(original,maps[i]))) for i in order),tuple(code_ids))
            costs=plan_cost(plan,size)
            observation.update(prefixes=snapshot(plan.prefixes),code_ids=list(code_ids),planned=costs)
            if any(ledger[k]+v>getattr(Budget(),k) for k,v in costs.items()):raise ValueError("study cost admission cap")
            left=min(Budget().task_wall_ms-(perf_counter_ns()-began)/1e6,remaining_ms())
            if left<=0:raise TimeoutError("complete task/study/controller deadline")
            try:result=backend.evaluate(plan,size,left)
            except CodedFailure as exc:
                for k,v in exc.known_cost.items():ledger[k]+=v
                observation.update(known_partial_cost=exc.known_cost,backend_complete_ms=exc.complete_ms)
                raise
            actual=result['cost']
            for k,v in actual.items():ledger[k]+=v
            if actual!=costs:raise ValueError("exact backend accounting mismatch")
            scores=result['scores']
            if len(scores)!=8 or any(len(row)!=4 for row in scores):raise ValueError("exact score matrix required")
            if any(finite(v)>0 for row in scores for v in row):raise ValueError("invalid log probability")
            canonical_matrix=[None]*8
            for i,row in zip(order,scores):canonical_matrix[i]=list(row)
            observation.update(status="COMPLETE",matrix=canonical_matrix,actual=actual,
                               peak_accelerator_memory_bytes=result['peak_accelerator_memory_bytes'],
                               complete_ms=(perf_counter_ns()-start)/1e6)
            if remaining_ms()<=0 or (perf_counter_ns()-began)/1e6>Budget().task_wall_ms:
                raise TimeoutError("completed scoring over deadline; retained")
        matrices=[p['matrix'] for p in passes]
        delta=max(abs(matrices[0][r][c]-matrix[r][c]) for matrix in matrices[1:] for r in range(8) for c in range(4))
        result={"status":"COMPLETE","summary":aggregate(matrices[0]),"numeric_delta_nats":delta}
    except Exception as exc:
        result={"status":"FAILED","error":type(exc).__name__+": "+str(exc)}
    result.update(passes=passes,complete_ms=(perf_counter_ns()-began)/1e6,view_sha256=digest(original),
                  trace_sha256=digest(passes))
    return result


def evaluate_development(records, unchanged, accounting_complete, generated_calls, controller_ms, study_ms):
    boundary={"p2_admitted":False,"decision3_admitted":False,"general_capability_gate":"NOT_EVALUATED",
              "global_questions_closed":[],"development_only":True,"fresh_validation_registered":False}
    if generated_calls!=0:return {**boundary,"verdict":"FAIL","reason":"GENERATION_FORBIDDEN"}
    if len(records)!=12 or unchanged is not True or not accounting_complete:
        return {**boundary,"verdict":"NOT_EVALUATED","reason":"INCOMPLETE_OR_IDENTITY_DRIFT"}
    if tuple(r.get('task_id') for r in records)!=TASK_IDS:
        return {**boundary,"verdict":"NOT_EVALUATED","reason":"DEVELOPMENT_COVERAGE_DRIFT"}
    if finite(controller_ms,True)>Budget().controller_wall_ms or finite(study_ms,True)>Budget().study_wall_ms:
        return {**boundary,"verdict":"FAIL","reason":"COMPLETE_COST_WALL_CAP"}
    winners=[];centered=[]
    for record in records:
        if record['status']!='COMPLETE':return {**boundary,"verdict":"NOT_EVALUATED","reason":"INCOMPLETE"}
        if finite(record['complete_ms'],True)>Budget().task_wall_ms:
            return {**boundary,"verdict":"FAIL","reason":"TASK_WALL_CAP"}
        s=record['summary']
        if finite(record['numeric_delta_nats'],True)>CRITERIA['numeric_tolerance_nats'] or finite(
                s['centered_schedule_delta_nats'],True)>CRITERIA['centered_schedule_tolerance_nats'] or s['stable_schedule_winner'] is not True:
            return {**boundary,"verdict":"FAIL","reason":"NUMERIC_OR_PERMUTATION_INSTABILITY"}
        winners.append(s['winner']);row=[finite(s['scores'][r]) for r in ROUTES]
        centered.append([v-math.fsum(row)/4 for v in row])
    spread=max(max(row[r] for row in centered)-min(row[r] for row in centered) for r in range(4))
    okay=len(set(winners))>=CRITERIA['distinct_winners'] and max(winners.count(r) for r in ROUTES)<=CRITERIA[
        'dominant_winner_max'] and spread>=CRITERIA['centered_task_range_min_nats']
    return {**boundary,"verdict":"PASS" if okay else "FAIL", "reason":"DEVELOPMENT_DIAGNOSTIC_ONLY" if okay else "DEGENERATE_ROUTE_SELECTION",
            "winner_counts":{r:winners.count(r) for r in ROUTES},"centered_task_range_nats":spread,
            "next":"FREEZE_ARCHITECTURE_THEN_REGISTER_FRESH_OPENED_VALIDATION" if okay else "PRESERVE_FIRST_DEVELOPMENT_FAILURE"}
