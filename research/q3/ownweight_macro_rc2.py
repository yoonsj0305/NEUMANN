"""Research-only frozen 32 learned named operator proposals from existing NEUMANN own-weight model.

Origin SHA of the full unabridged serialized library is
71ce8777335007c18d31c935fc3c7677dd49a337d3423034be3f3cbaea6dd9a3.
Proposals were mined from model rollouts on TRAIN ONLY; this registry is
not new trainable weights or an independently novel foundational primitive.

All macro bodies are compositions of previously human-defined operations.
"""
from collections.abc import Sequence

MOD = 11
FROZEN_MACRO_BODIES = {
    "NEU_DEF_00": (6, 6),
    "NEU_DEF_01": (3, 6),
    "NEU_DEF_02": (9, 6),
    "NEU_DEF_03": (6, 8),
    "NEU_DEF_04": (7, 6),
    "NEU_DEF_05": (6, 0),
    "NEU_DEF_06": (6, 3),
    "NEU_DEF_07": (4, 6),
    "NEU_DEF_08": (3, 9),
    "NEU_DEF_09": (6, 7),
    "NEU_DEF_10": (8, 6),
    "NEU_DEF_11": (3, 8),
    "NEU_DEF_12": (6, 9),
    "NEU_DEF_13": (5, 6),
    "NEU_DEF_14": (3, 4),
    "NEU_DEF_15": (7, 9),
    "NEU_DEF_16": (9, 9),
    "NEU_DEF_17": (6, 1),
    "NEU_DEF_18": (7, 3),
    "NEU_DEF_19": (9, 4),
    "NEU_DEF_20": (9, 7),
    "NEU_DEF_21": (7, 8),
    "NEU_DEF_22": (8, 0),
    "NEU_DEF_23": (9, 3),
    "NEU_DEF_24": (7, 7),
    "NEU_DEF_25": (3, 3),
    "NEU_DEF_26": (6, 2),
    "NEU_DEF_27": (2, 6),
    "NEU_DEF_28": (8, 1),
    "NEU_DEF_29": (4, 9),
    "NEU_DEF_30": (0, 6),
    "NEU_DEF_31": (9, 8),
}

def apply_one(x: Sequence[int], op: int) -> list[int]:
    v=list(map(int, x))
    if len(v) != 6 or not all(0<=y<MOD for y in v):
        raise ValueError("Expected a 6-vector over Z_11")
    if op==0: return v[1:]+v[:1]
    if op==1: return v[-1:]+v[:-1]
    if op==2: return v[::-1]
    if op==3: return [(y+1)%MOD for y in v]
    if op==4: return [(2*y)%MOD for y in v]
    if op==5: return [(-y)%MOD for y in v]
    if op==6:
        out=[];acc=0
        for y in v:
            acc=(acc+y)%MOD;out.append(acc)
        return out
    if op==7: return [(v[i]-v[i-1])%MOD for i in range(6)]
    if op==8: return sorted(v)
    if op==9: return [(y*y)%MOD for y in v]
    raise ValueError("Unknown primitive")

def execute(body: Sequence[int], x: Sequence[int]) -> list[int]:
    state=list(x)
    for action in body: state=apply_one(state,action)
    return state

def call_named(name: str, x: Sequence[int]) -> list[int]:
    if name not in FROZEN_MACRO_BODIES:
        raise KeyError("Not in frozen registry")
    return execute(FROZEN_MACRO_BODIES[name],x)

def compile_named_program(names: Sequence[str]) -> tuple[int,...]:
    if not names: raise ValueError("No empty invented program")
    p=[]
    for name in names:
        if name not in FROZEN_MACRO_BODIES: raise KeyError(name)
        p.extend(FROZEN_MACRO_BODIES[name])
    return tuple(p)
