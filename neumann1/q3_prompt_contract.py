"""One canonical Q3 program-discovery prompt for inference AND gradient learning.

No target outputs, reference implementations, task IDs or oracle gold here.
Avoid the earlier training/inference distribution mismatch.
"""
from __future__ import annotations
import json


SYSTEM_TEXT=(
    "You synthesize correct general Python algorithms from source "
    "input/output. Output only a single transform(x) function, "
    "no imports, no comments outside Python source."
)


def source_discovery_prompt(pairs, *, method_context=""):
    if not pairs:
        raise ValueError("SOURCE examples required")
    if not isinstance(method_context,str) or len(method_context)>12000:
        raise ValueError("source-only method context must be bounded")
    prefix=(
        "Verified prior SOURCE examples can suggest method structure but "
        "DO NOT determine this task's answer. Infer from current SOURCE.\n"
        + method_context + "\n"
        if method_context else "")
    return prefix + (
        "Infer a general executable operator. Respond ONLY with Python "
        "code: exactly one function def transform(x) that returns output. "
        "No imports, other functions, globals, reflection or file access. "
        "Use arithmetic, loops, conditionals and list operations to "
        "express your own new algorithm. Do NOT memorize examples.\n"
        + "\n".join(
            "Source input: "+json.dumps(x,ensure_ascii=True,separators=(',',':'))
            + "\nExpected source output: "+json.dumps(y,ensure_ascii=True,separators=(',',':'))
            for x,y in pairs))


def model_prefix(tokenizer,prompt):
    messages=[
        {"role":"system","content":SYSTEM_TEXT},
        {"role":"user","content":prompt}
    ]
    if tokenizer.chat_template is not None:
        return tokenizer.apply_chat_template(
            messages,tokenize=False,add_generation_prompt=True)
    return SYSTEM_TEXT+"\n"+prompt+"\nPROGRAM:\n"


def model_training_ids(tokenizer,prompt,completion,*,max_length=1536):
    """Return exactly the token prefix inference uses and a code-only loss.

    Training prompt must be source_discovery_prompt(SOURCE pairs), and the
    completion must be independently SOURCE-certified executable code.
    """
    prefix=model_prefix(tokenizer,prompt)
    input_prefix=list(tokenizer(
        prefix,add_special_tokens=False)["input_ids"])
    code_ids=list(tokenizer(
        completion,add_special_tokens=False)["input_ids"])
    if not code_ids:
        raise ValueError("empty teacher completion")
    if len(input_prefix)+len(code_ids)>max_length:
        raise ValueError("SOURCE teacher would truncate code or prompt")
    return (input_prefix+code_ids,
            [-100]*len(input_prefix)+code_ids)
