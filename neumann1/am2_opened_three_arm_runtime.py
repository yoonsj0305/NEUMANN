"""Opened AM2 real-core three-arm execution boundary, NOT an admitted EX1 study.

The same actual frozen core and public question can be used by DIRECT, TOOL+,
and NEUMANN. Strong TOOL+/semantic proposals are caller-provided registered
implementations, NEVER mocked as scientific evidence. No source retrieval,
sealed cohort access, model download, training or paid operation in this module.

Parent: PR #254 public QA ABI; scientific authority: Issue #253.
"""
from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter_ns
from typing import Any, Callable
import hashlib
import json

from neumann1.am2_generic_qa_abi import (
    InterfaceBlocked, canonical, format_public_messages, sha, validate_public,
    verify_candidate,
)

ARMS=("DIRECT","TOOL+","NEUMANN")
SCHEMA="neumann.am2.opened-real-core-boundary.v1"

@dataclass(frozen=True)
class OpenedBudget:
    max_new_tokens: int = 512
    wall_ms: float = 120000.0
    provider_ms: float = 30000.0

    def __post_init__(self):
        if not (1<=self.max_new_tokens<=2048 and 1000<=self.wall_ms<=600000
                and 1<=self.provider_ms<self.wall_ms):
            raise ValueError("INVALID_OPENED_BUDGET")


def _elapsed_ms(start: int)->float:
    return (perf_counter_ns()-start)/1e6


def _public_context(provider:Callable,view:dict,budget:OpenedBudget):
    """Executes a real caller-owned tool interface, billed per arm.

    An external claim about internal calls is untrusted; never label it strong
    or complete without external signed evidence and full cost accounting.
    """
    started=perf_counter_ns()
    result=provider(view)
    elapsed=_elapsed_ms(started)
    if type(result) is not dict or set(result)!={"context","tool_id","internal_calls"}:
        raise InterfaceBlocked("UNREGISTERED_OR_INCOMPLETE_TOOL_RESULT")
    if (type(result["context"]) is not str or len(result["context"])>12000
        or type(result["tool_id"]) is not str or not result["tool_id"]
        or type(result["internal_calls"]) is not int or result["internal_calls"]<1):
        raise InterfaceBlocked("ILL_TYPED_TOOL_RESULT")
    if elapsed>budget.provider_ms:
        raise InterfaceBlocked("TOOL_PROVIDER_WALL_EXCEEDED")
    return result,elapsed


def _structure(proposer:Callable,certifier:Callable,view:dict,budget:OpenedBudget):
    if not callable(proposer) or not callable(certifier):
        raise InterfaceBlocked("ACTUAL_STRUCTURAL_PROPOSER_AND_CERTIFIER_REQUIRED")
    started=perf_counter_ns()
    proposal=proposer(view)
    if type(proposal) is not dict or set(proposal)!={"representation","method_id"}:
        raise InterfaceBlocked("UNBOUND_STRUCTURAL_PROPOSAL")
    if (type(proposal["representation"]) is not str
        or not proposal["representation"] or len(proposal["representation"])>12000
        or type(proposal["method_id"]) is not str
        or not proposal["method_id"]):
        raise InterfaceBlocked("ILL_TYPED_STRUCTURAL_PROPOSAL")
    certificate=certifier(view,proposal)
    elapsed=_elapsed_ms(started)
    if (type(certificate) is not dict
        or type(certificate.get("valid")) is not bool
        or certificate["valid"] is not True
        or certificate.get("source_sha256")!=sha(view)
        or certificate.get("proposal_sha256")!=sha(proposal)
        or type(certificate.get("proof_sha256")) is not str
        or len(certificate["proof_sha256"])!=64
        or any(c not in "0123456789abcdef" for c in certificate["proof_sha256"])):
        raise InterfaceBlocked("ORIGINAL_STRUCTURE_CERTIFICATION_FAILED")
    if elapsed>budget.provider_ms:
        raise InterfaceBlocked("STRUCTURAL_PROPOSER_WALL_EXCEEDED")
    return proposal,certificate,elapsed


def _frozen_core_identity(core:Any,production:bool)->dict:
    raw=getattr(core,"identity",None)
    if type(raw) is not dict:
        raise InterfaceBlocked("MISSING_FROZEN_CORE_IDENTITY")
    if production and not (
        raw.get("evidence_kind")=="actual_frozen_model"
        and raw.get("weights_frozen") is True
        and raw.get("accelerator_class") is True
        and raw.get("model_id")=="google/gemma-4-E2B-it"
        and raw.get("model_revision")=="3e22461f65e89153144f8adb70e3b8c2cc9845a7"
        and raw.get("artifact_sha256")=="bf6d4f9d506f536db6255143e5f21e05b9ccadfea54af281ac278bd49c178d66"
        and raw.get("tokenizer_sha256")=="8552955a1513c80096c4155aa2de30079a20d4c3f255b9d1acf9162c859b4207"
        and raw.get("precision")=="bfloat16"
        and raw.get("deterministic") is True
        and raw.get("do_sample") is False
    ):
        raise InterfaceBlocked("UNQUALIFIED_ACTUAL_CORE_IDENTITY")
    if production:
        # The old AM1 core only checked the tensor dtype; a Tesla T4 can emulate
        # BF16 but has no native BF16 math. Reject before any new generation.
        t=getattr(core,"torch",None)
        if t is None:
            raise InterfaceBlocked("REAL_PYTORCH_NATIVE_BF16_ATTESTATION_REQUIRED")
        try:
            if not t.cuda.is_available() or t.cuda.device_count()<1:
                raise InterfaceBlocked("ACTUAL_CUDA_REQUIRED")
            props=t.cuda.get_device_properties(0)
            if int(props.major)<8 or int(props.total_memory)<14*1024**3:
                raise InterfaceBlocked("ACTUAL_NATIVE_BF16_GPU_MINIMUM_NOT_MET")
            if t.cuda.is_bf16_supported(including_emulation=False) is not True:
                raise InterfaceBlocked("ACTUAL_NONEMULATED_BF16_NOT_SUPPORTED")
        except (AttributeError,TypeError) as exc:
            raise InterfaceBlocked("CANNOT_INDEPENDENTLY_ATTEST_NATIVE_BF16") from exc
    return raw


def run_one_opened(
    view:dict,
    arm:str,
    core:Any,
    original_checker:Callable[[str],bool],
    *,
    shared_tool:Callable|None=None,
    proposer:Callable|None=None,
    certifier:Callable|None=None,
    budget:OpenedBudget=OpenedBudget(),
    production:bool=True,
)->dict:
    """Actual evaluation path only if production identity and connectors qualify.

    original_checker alone has private answer authority. It is never passed to
    tool or proposer. All tool and proposal wall times are charged. Do NOT infer
    actual model forward counts or dollars from generated token counts.
    """
    if arm not in ARMS:
        raise InterfaceBlocked("UNKNOWN_ARM")
    if not callable(original_checker):
        raise InterfaceBlocked("ORIGINAL_CHECKER_NOT_BOUND")
    public=validate_public(view)
    identity=_frozen_core_identity(core,production)
    baseline_identity=sha(identity)
    started=perf_counter_ns()
    rec={
        "schema":SCHEMA,"arm":arm,
        "scope":"OPENED_SOFTWARE_BOUNDARY_NOT_SCIENTIFIC_ADMISSION",
        "public_sha256":sha(public),"core_identity_sha256":baseline_identity,
        "production_mode":bool(production),
        "accepted":False,"status":"ABSTAIN",
        "original_checker_calls":0,"tool_provider_invocations":0,
        "structure_proposals":0,"structure_verifications":0,
        "model_generate_invocations":0,"actual_model_generate_calls":0,
        "model_forward_calls_measured":None,
        "token_input":None,"token_output":None,
        "peak_allocated_vram_bytes":None,
        "peak_reserved_vram_bytes":None,
        "tool_provider_wall_ms":0.0,"structure_wall_ms":0.0,
        "checker_wall_ms":0.0,"model_generation_wall_ms":0.0,
        "cold_start_ms":getattr(core,"startup_ms",None) if production else None,
        "electricity_joules":None,"dollar_cost":None,
        "complete_cost_measurement":"INCOMPLETE_UNTIL_REGISTERED_BUDGET_AND_HARDWARE",
        "frontier_calls":0,"sealed_rows_opened":False,"global_Q1_Q7":"OPEN",
        "learned_new_operator_verified":False,
        "strong_TOOL_qualified":False,
    }
    try:
        messages=format_public_messages(public)
        shared_result=None
        if arm in ("TOOL+","NEUMANN"):
            if not callable(shared_tool):
                raise InterfaceBlocked("STRONG_SHARED_TOOL_PROVIDER_NOT_BOUND")
            shared_result,tms=_public_context(shared_tool,public,budget)
            rec["tool_provider_invocations"]+=1
            rec["tool_id"]=shared_result["tool_id"]
            rec["tool_context_sha256"]=sha(shared_result)
            rec["tool_provider_wall_ms"]=round(tms,3)
            messages[1]["content"]+="\nPUBLIC_SOURCE_TOOL_CONTEXT:\n"+shared_result["context"]

        if arm=="NEUMANN":
            proposal,certificate,pms=_structure(proposer,certifier,public,budget)
            rec["structure_proposals"]+=1
            rec["structure_verifications"]+=1
            rec["structure_wall_ms"]=round(pms,3)
            rec["structure_method_id"]=proposal["method_id"]
            rec["structure_proposal_sha256"]=sha(proposal)
            rec["structure_certificate_sha256"]=certificate["proof_sha256"]
            messages[1]["content"]+="\nPUBLIC_SOURCE_STRUCTURE_VERIFIED_BY_CALLER_CERTIFIER:\n"+proposal["representation"]
        rec["model_input_sha256"]=sha(messages)

        remaining=budget.wall_ms-_elapsed_ms(started)
        if remaining<=0:
            raise InterfaceBlocked("QUERY_WALL_CAP_BEFORE_MODEL")
        gen_started=perf_counter_ns()
        rec["model_generate_invocations"]+=1
        generated=core.generate(messages,max_tokens=budget.max_new_tokens,
            thinking=False,deadline_ms=remaining)
        rec["model_generation_wall_ms"]=round(_elapsed_ms(gen_started),3)
        if production:
            rec["actual_model_generate_calls"]+=1
        if type(generated) is not dict:
            raise InterfaceBlocked("ILL_TYPED_CORE_RECEIPT")
        rec["token_input"]=generated.get("input_tokens")
        rec["token_output"]=generated.get("output_tokens")
        rec["peak_allocated_vram_bytes"]=generated.get("peak_accelerator_memory_bytes")
        rec["peak_reserved_vram_bytes"]=generated.get("peak_accelerator_reserved_bytes")
        raw=generated.get("raw")
        if type(raw) is not str:
            raise InterfaceBlocked("NO_RAW_FINAL_GENERATION")
        rec["raw_output_sha256"]=hashlib.sha256(raw.encode()).hexdigest()
        if generated.get("deadline_reached") is True:
            raise InterfaceBlocked("ACTUAL_MODEL_GENERATION_DEADLINE")
        if sha(core.identity)!=baseline_identity:
            raise InterfaceBlocked("FROZEN_CORE_IDENTITY_CHANGED")
        ck_started=perf_counter_ns()
        def counted_checker(answer:str)->bool:
            rec["original_checker_calls"]+=1
            return original_checker(answer)
        judgement=verify_candidate(public,raw,counted_checker)
        rec["checker_wall_ms"]=round(_elapsed_ms(ck_started),3)
        rec["status"]=judgement["status"]
        rec["accepted"]=judgement["accepted"]
        if "reason" in judgement:
            rec["reason"]=judgement["reason"]
        if judgement.get("answer_sha256"):
            rec["answer_sha256"]=judgement["answer_sha256"]
        if _elapsed_ms(started)>budget.wall_ms:
            rec["status"]="ABSTAIN"
            rec["accepted"]=False
            rec["reason"]="QUERY_WALL_CAP_EXCEEDED"
    except Exception as exc:
        rec["status"]="ABSTAIN"
        rec["accepted"]=False
        rec["reason"]=type(exc).__name__+":"+str(exc)[:180]
    rec["opened_observation_wall_ms"]=round(_elapsed_ms(started),3)
    rec["full_investment_amortization"]=None
    return rec


def run_matched_opened(
    view:dict,core:Any,original_checker:Callable[[str],bool],*,
    shared_tool:Callable|None,
    proposer:Callable|None,
    certifier:Callable|None,
    budget:OpenedBudget=OpenedBudget(),production:bool=True,
)->dict:
    """All arms use one core instance and the same bound strong-tool callback.

    No success/failure from this wrapper authorizes scientific admission.
    Missing proposer, checker or tool gives explicit ABSTAIN.
    """
    core_id=sha(_frozen_core_identity(core,production))
    receipts=[run_one_opened(view,arm,core,original_checker,
                 shared_tool=shared_tool,proposer=proposer,certifier=certifier,
                 budget=budget,production=production) for arm in ARMS]
    if sha(core.identity)!=core_id:
        raise InterfaceBlocked("MODEL_CORE_DRIFT_ACROSS_ARMS")
    t,n=receipts[1:]
    same_tool_context=(
        t.get("tool_context_sha256") is not None
        and t.get("tool_context_sha256")==n.get("tool_context_sha256")
        and t.get("tool_id")==n.get("tool_id")
    )
    scientific_admitted=False
    if not same_tool_context:
        for row in receipts:
            row["accepted"]=False
            row["status"]="ABSTAIN"
            row["reason"]="MATCHED_SHARED_TOOL_PARITY_FAILURE"
    return {
        "schema":"neumann.am2.opened-matched-execution.v1",
        "receipts":receipts,"shared_tool_context_identical":same_tool_context,
        "model_core_sha256":core_id,
        "actual_opened_model_comparison_admitted":scientific_admitted,
        "missing_science":["24_PLUS_AUTHENTIC_UNSATURATED_ORIGINALS",
          "3_PLUS_INDEPENDENT_ORIGINS","ORIGINAL_CHECKER_AUDIT",
          "STRONGEST_TOOL_PLUS_ATTESTATION",
          "REAL_NATIVE_BF16_GPU_WITH_AUTHORIZATION",
          "LEARNED_SOURCE_STRUCTURE_AND_CAUSAL_ABLATIONS",
          "COMPLETE_COLD_AND_ALL_IN_COSTS"],
        "historical_AM1_first_verdict":"FAIL_UNCHANGED",
        "sealed_D3":"BLOCKED","global_Q1_Q7":"OPEN",
    }
