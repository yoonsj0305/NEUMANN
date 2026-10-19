"""Actual SyGuS original three-VC verifier CONNECTED to AM2 typed three-arm I/O.

ENGINEERING PROTOCOL only: two ALREADY OPENED public SyGuS 2018 originals.
A dummy core returns a known prior CLASSICAL positive invariant, not real Gemma
or a neural Q3 invention. The actual final submitted candidate is independently
checked by source-bound Z3 + separate cvc5 original-safety verification.

Issue #269 pinned the integration criteria before this first workflow.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from neumann1.am2_generic_qa_abi import (
    SCHEMA as PUBLIC_SCHEMA, InterfaceBlocked, sha, validate_public,
)
from neumann1.am2_opened_three_arm_runtime import (
    run_matched_opened, run_one_opened,
)
from experiments.am2_sygus_native_three_vc_checker import (
    FROZEN_CASES, check_original_candidate,
)
from experiments.q3_source_prove import prove_source, replay_original_source_bound

SCHEMA="neumann.am2.sygus-three-arm-original-checker-wiring.v1"

def sha_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def make_public_source(source_path:Path,original_sha256:str)->dict:
    """The SyGuS original is a PUBLIC task, unlike original verifier outcomes."""
    p=Path(source_path)
    if p.suffix!=".sl" or not p.is_file() or p.is_symlink():
        raise InterfaceBlocked("NOT_REAL_PUBLIC_ORIGINAL")
    data=p.read_bytes()
    if sha_bytes(data)!=original_sha256:
        raise InterfaceBlocked("PUBLIC_ORIGINAL_SHA_MISMATCH")
    try:
        source=data.decode("utf-8",errors="strict")
    except UnicodeDecodeError as e:
        raise InterfaceBlocked("PUBLIC_SOURCE_ENCODING_BLOCKED") from e
    return validate_public({
        "schema":PUBLIC_SCHEMA,
        "question":"Original public SyGuS synthesis-invariant source:\n"+source,
        "answer_kind":"smt_invariant",
    })

class TestOnlyFrozenCore:
    """A SYNTHETIC output injector, NEVER a real model measurement."""
    def __init__(self,output:str):
        self.identity={"evidence_kind":"SYNTHETIC_TEST_ONLY",
                       "model_id":"NO_MODEL_LOADED",
                       "weights_frozen":False,"accelerator_class":False}
        self.output=output
        self.calls=0
        self.messages=[]
    def generate(self,messages,*,max_tokens,thinking,deadline_ms):
        if thinking is not False or deadline_ms<=0:
            raise RuntimeError("TEST_CORE_PROTOCOL_MISMATCH")
        self.calls+=1
        self.messages.append(messages)
        return {"raw":self.output,
                "input_tokens":None,"output_tokens":None,
                "peak_accelerator_memory_bytes":None,
                "peak_accelerator_reserved_bytes":None,
                "deadline_reached":False}

def integration_case(source_path:Path):
    data=source_path.read_bytes()
    source_sha=sha_bytes(data)
    public=make_public_source(source_path,source_sha)
    # Historical classical proposer used only for engineering positive control.
    # Its work is NOT a model-forward or source-family transfer result.
    known=prove_source(source_path)
    if known.get("status")!="ORIGINAL_SOURCE_THREE_VC_CERTIFIED":
        raise RuntimeError("PINNED_KNOWN_SOURCE_POSITIVE_NO_LONGER_VALID")
    if not replay_original_source_bound(source_path,known):
        raise RuntimeError("EXTERNAL_SOURCE_POSITIVE_NOT_REPLAYABLE")
    candidate=known["invariant_sexpr"]
    certification_calls=[0]
    original_checker_calls=[0]
    def real_original_checker(formula):
        original_checker_calls[0]+=1
        verdict=check_original_candidate(source_path,formula,
            expected_source_sha256=source_sha)
        return verdict["status"]=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5"
    def shared_test_tool(view):
        if view!=public:
            raise InterfaceBlocked("TOOL_RECEIVED_DIFFERENT_PUBLIC_TASK")
        return {"context":"TEST_ONLY: use the public original transition relation.",
                "tool_id":"TEST_ONLY_NOT_ELIGIBLE_STRONG_TOOL_PLUS",
                "internal_calls":1}
    def classical_test_proposer(view):
        if view!=public:
            raise InterfaceBlocked("PROPOSER_RECEIVED_WRONG_PUBLIC_TASK")
        return {"representation":candidate,
                "method_id":"OLD_CLASSICAL_FIXED_SOURCE_ONLY_TEST_CONTROL"}
    def actual_source_certifier(view,proposal):
        if view!=public:
            return {"valid":False}
        certification_calls[0]+=1
        proof=check_original_candidate(source_path,proposal["representation"],
                expected_source_sha256=source_sha)
        ok=proof["status"]=="CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5"
        return {"valid":ok,"source_sha256":sha(view),
            "proposal_sha256":sha(proposal),
            "proof_sha256":sha(proof)}
    def invoke(raw:str):
        core=TestOnlyFrozenCore(raw)
        result=run_matched_opened(public,core,real_original_checker,
            shared_tool=shared_test_tool,proposer=classical_test_proposer,
            certifier=actual_source_certifier,production=False)
        return result,core
    good,core=invoke("<answer>"+candidate+"</answer>")
    wrong_true,_=invoke("<answer>true</answer>")
    wrong_false,_=invoke("<answer>false</answer>")
    thought,_=invoke("<|channel>thought privately thinking about source")
    injected,_=invoke("<answer>(assert false)</answer>")
    mismatch=run_one_opened(public,"DIRECT",
        TestOnlyFrozenCore("<answer>"+candidate+"</answer>"),
        lambda formula:check_original_candidate(source_path,formula,
           expected_source_sha256="0"*64)["status"]==
             "CERTIFIED_ORIGINAL_3VC_Z3_AND_CVC5",
        production=False)
    leak={**public,"gold":"hidden"}
    try:
        run_one_opened(leak,"DIRECT",TestOnlyFrozenCore("<answer>true</answer>"),
            lambda answer:True,production=False)
        public_leak_rejected=False
    except InterfaceBlocked:
        public_leak_rejected=True
    checks={
        "actual_source_sha_and_public_input_pinned":public["answer_kind"]=="smt_invariant",
        "all_three_test_core_outputs_pass_live_original_3vc":all(
            x["accepted"] and x["status"]=="ORIGINAL_CHECKER_PASS"
            and x["original_checker_calls"]==1
            for x in good["receipts"]),
        "tool_plus_and_neumann_share_exact_source_context":
            good["shared_tool_context_identical"],
        "true_and_false_wrong_invariants_original_rejected":all(
            not x["accepted"] and x["status"]=="ORIGINAL_CHECKER_REJECT"
            for batch in (wrong_true,wrong_false) for x in batch["receipts"]),
        "thought_only_never_reaches_original_checker":all(
            x["original_checker_calls"]==0 and not x["accepted"]
            for x in thought["receipts"]),
        "SMT_command_injected_candidate_rejected":all(
            not x["accepted"] for x in injected["receipts"]),
        "changed_original_sha_cannot_certify":
            mismatch["accepted"] is False,
        "private_gold_key_rejected_before_model":
            public_leak_rejected,
        "neumann_structural_metadata_source_verified":
            good["receipts"][2]["structure_verifications"]==1,
        "no_actual_neural_core_is_scored":all(
            x["actual_model_generate_calls"]==0
            and x["global_Q1_Q7"]=="OPEN" for x in good["receipts"]),
        "no_scientific_ex1_admission":not good["actual_opened_model_comparison_admitted"],
    }
    return {"real_original_source_sha256":source_sha,
       "real_original_path":source_path.name,
       "classical_original_route":known["selected_route"],
       "real_original_checker_invocations":original_checker_calls[0],
       "real_original_structure_certifier_invocations":certification_calls[0],
       "test_model_generate_invocations":core.calls,
       "real_model_generate_invocations":0,
       "positive_three_arm_receipts":good["receipts"],
       "positive_original_result":good["shared_tool_context_identical"],
       "negative_controls":{
           "true": [r["status"] for r in wrong_true["receipts"]],
           "false":[r["status"] for r in wrong_false["receipts"]],
           "thought":[r["status"] for r in thought["receipts"]],
           "malformed":[r["status"] for r in injected["receipts"]]},
       "checks":checks}

def run(root:Path):
    results=[]
    for rel in FROZEN_CASES:
        p=root/rel
        row=integration_case(p)
        results.append(row)
        print("AM2_REAL_CHECKER_THREE_ARM_WIRING",row["real_original_path"],
              all(row["checks"].values()),
              row["real_original_checker_invocations"])
    return {
        "schema":SCHEMA,"preregister_issue":269,
        "scope":"TWO_ALREADY_OPENED_REAL_SOURCE_CHECKER_WIRING_WITH_FAKE_MODEL_ONLY",
        "cases":results,
        "first_engineering_gate_pass":len(results)==2 and
              all(all(row["checks"].values()) for row in results),
        "original_3vc_and_cvc5_checker_actual_executed":True,
        "actual_model_calls":0,"gpu_calls":0,"frontier_calls":0,"paid_api_calls":0,
        "new_unseen_originals":0,
        "admitted_opened_cohort_24":False,
        "learned_new_operator_proven":False,
        "actual_matched_model_multiplier":"NOT_EVALUATED",
        "historical_first_AM1":"FAIL_UNCHANGED",
        "sealed_D3":"BLOCKED","global_Q1_Q7":"OPEN",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    result=run(args.source_root)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("AM2_ORIGINAL_CHECKER_REAL_WIRING_GATE",
          result["first_engineering_gate_pass"])
    print("AM2_GLOBAL_Q1_Q7",result["global_Q1_Q7"])
if __name__=="__main__":main()
