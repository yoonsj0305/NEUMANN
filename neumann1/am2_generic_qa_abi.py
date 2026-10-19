"""Capability-neutral public QA ABI for future OPENED AM2 matched development.

Engineering only. Not real model inference, a new original-task admission,
or permission to open the Decision-3 sealed cohort. Original private checker
remains a separate callback and never enters the model-visible public view.
"""
from __future__ import annotations
import hashlib
import json
import re
from typing import Any, Callable

SCHEMA="neumann.am2.generic-qa-public.v1"
SUPPORTED={"short_text","integer","choice","smt_invariant"}
BAD_KEYS={"answer","gold","solution","rationale","checker","private","private_tests","reference_answer","ground_truth","model_response"}
MAX_QUESTION=16000
MAX_ANSWER=1500
MAX_SMT_INVARIANT=4096
SMT_FINAL_RE=re.compile(r"^<answer>(.{1,4096})</answer>$",flags=re.DOTALL)
FINAL_RE=re.compile(r"^<answer>([^<>\n]{1,1500})</answer>$",flags=re.DOTALL)
INTEGER_RE=re.compile(r"^-?(?:0|[1-9][0-9]*)$")

class InterfaceBlocked(ValueError):
    pass

def canonical(obj:Any)->str:
    return json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False)

def sha(obj:Any)->str:
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()

def _find_forbidden(value:Any)->bool:
    if isinstance(value,dict):
        return any(str(k).lower() in BAD_KEYS or _find_forbidden(v) for k,v in value.items())
    if isinstance(value,list):
        return any(_find_forbidden(v) for v in value)
    return False

def validate_public(view:dict)->dict:
    """Reject any task/private-answer material masquerading as public metadata."""
    if type(view) is not dict or view.get("schema")!=SCHEMA:
        raise InterfaceBlocked("PUBLIC_SCHEMA_INVALID")
    kind=view.get("answer_kind")
    if type(kind) is not str or kind not in SUPPORTED:
        raise InterfaceBlocked("ANSWER_FORMAT_UNSUPPORTED")
    allowed={"schema","question","answer_kind","choices"}
    if set(view)-allowed or _find_forbidden(view):
        raise InterfaceBlocked("PRIVATE_OR_UNAPPROVED_FIELD")
    question=view.get("question")
    if type(question) is not str or not question.strip() or len(question)>MAX_QUESTION:
        raise InterfaceBlocked("PUBLIC_QUESTION_INVALID")
    result={"schema":SCHEMA,"question":question,"answer_kind":kind}
    if kind=="choice":
        choices=view.get("choices")
        if type(choices) is not list or not (2<=len(choices)<=8):
            raise InterfaceBlocked("CHOICE_LABELS_INVALID")
        if any(type(x) is not str or not re.fullmatch(r"[A-H]",x) for x in choices):
            raise InterfaceBlocked("CHOICE_LABELS_INVALID")
        if len(set(choices))!=len(choices):
            raise InterfaceBlocked("CHOICE_LABELS_DUPLICATE")
        result["choices"]=choices[:]
    elif "choices" in view:
        raise InterfaceBlocked("CHOICES_WITHOUT_CHOICE_KIND")
    return result

def format_public_messages(view:dict)->list[dict]:
    """Identical baseline public content until costed extra machinery is added."""
    clean=validate_public(view)
    instruction=("Answer the public problem. Return ONLY <answer>VALUE</answer>. "
       "For smt_invariant, VALUE is exactly one standalone SMT-LIB Boolean term "
       "and may contain whitespace, parentheses or comparison operators. "
       "No extra SMT commands, no explanations, and no private checker data." if clean["answer_kind"]=="smt_invariant" else
       "Answer the public problem. Return exactly one final line as "
       "<answer>VALUE</answer>, with no other text. Do not include reasoning. "
       "Use only the supplied public fields.")
    return [{"role":"system","content":instruction},
            {"role":"user","content":canonical(clean)}]

def extract_answer(raw:str,view:dict)->str:
    clean=validate_public(view)
    if type(raw) is not str or not raw or len(raw)>12000:
        raise InterfaceBlocked("EMPTY_OR_OVERSIZE_OUTPUT")
    if "<|channel>thought" in raw and "<|channel>final" not in raw:
        raise InterfaceBlocked("NO_FINAL_CHANNEL_IN_THOUGHT_OUTPUT")
    if "<|channel>final" in raw:
        raw=raw.rsplit("<|channel>final",1)[-1]
    for suffix in ("<|end|>","<|eot_id|>","<eos>"):
        raw=raw.replace(suffix,"")
    if clean["answer_kind"]=="smt_invariant":
        match=SMT_FINAL_RE.fullmatch(raw.strip())
        if match is None:
            raise InterfaceBlocked("FINAL_SINGLE_SMT_INVARIANT_NOT_FOUND")
        answer=match.group(1).strip()
        if (not answer or len(answer)>MAX_SMT_INVARIANT or
            "<answer>" in answer or "</answer>" in answer):
            raise InterfaceBlocked("INVALID_SMT_INVARIANT_ENVELOPE")
        return answer
    match=FINAL_RE.fullmatch(raw.strip())
    if match is None:
        raise InterfaceBlocked("FINAL_SINGLE_ANSWER_NOT_FOUND")
    answer=match.group(1).strip()
    if not answer or len(answer)>MAX_ANSWER:
        raise InterfaceBlocked("INVALID_ANSWER_LENGTH")
    if clean["answer_kind"]=="integer" and not INTEGER_RE.fullmatch(answer):
        raise InterfaceBlocked("INTEGER_ANSWER_NOT_CANONICAL")
    if clean["answer_kind"]=="choice" and answer not in clean["choices"]:
        raise InterfaceBlocked("ANSWER_NOT_A_VALID_CHOICE")
    return answer

def verify_candidate(view:dict,raw:str,original_checker:Callable[[str],bool])->dict:
    """Only an externally owned original checker can affirm an answer.

    This function accounts for no model work and has NO knowledge of any original
    private test set. Its receipt is a local formatting/verification result,
    never a trained-model performance receipt.
    """
    public=validate_public(view)
    receipt={"schema":"neumann.am2.generic-qa-verification.v1",
       "public_sha256":sha(public),"model_work_in_this_function":0,
       "source":"CALLER_SUPPLIED_RAW_NOT_A_REAL_MODEL_RUN",
       "status":"ABSTAIN","accepted":False,
       "global_Q1_Q7":"OPEN","sealed_rows_opened":False}
    try:
        answer=extract_answer(raw,public)
        receipt["answer_sha256"]=hashlib.sha256(answer.encode()).hexdigest()
        decision=original_checker(answer)
        if type(decision) is not bool:
            raise InterfaceBlocked("CHECKER_RETURN_NOT_BOOLEAN")
        receipt["status"]="ORIGINAL_CHECKER_PASS" if decision else "ORIGINAL_CHECKER_REJECT"
        receipt["accepted"]=decision
    except Exception as exc:
        receipt["status"]="ABSTAIN"
        receipt["reason"]=type(exc).__name__+":"+str(exc)[:100]
    return receipt
