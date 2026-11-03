"""Advisory typed spatial macro induction for NEUMANN, P0.7.

Fits a new *parameterized program instance* from train input/output examples.
All primitives are hand-designed and remain entirely classical. This does not
show novel opcode invention, JEPA value or general Q3/Q4/Q5/Q6/Q7 closure.
Do not import into production routing until a separately preregistered gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

import numpy as np

SCHEMA = "neumann.prh.advisory-relational-macro.p07.v1"
MAX_COLOR = 9
MAX_DIM = 30
MAX_CLEARANCE = 4


class Abstain(ValueError):
    """Incompatible or ambiguous observations; do not guess."""


@dataclass(frozen=True)
class Object:
    color: int
    pixels: tuple[tuple[int, int], ...]
    box: tuple[int, int, int, int]  # (rmin, rmax, cmin, cmax)

    @property
    def area(self) -> int:
        return len(self.pixels)


def _grid(raw: Any) -> np.ndarray:
    x = np.asarray(raw)
    if x.ndim != 2 or not (1 <= x.shape[0] <= MAX_DIM and 1 <= x.shape[1] <= MAX_DIM):
        raise Abstain("grid_shape")
    if not np.issubdtype(x.dtype, np.integer) or np.any(x < 0) or np.any(x > MAX_COLOR):
        raise Abstain("grid_palette")
    return x.astype(np.int64)


def _connected(points: tuple[tuple[int, int], ...]) -> bool:
    all_points = set(points)
    if not all_points:
        return False
    visited = {points[0]}
    work = [points[0]]
    while work:
        r, c = work.pop()
        for adj in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
            if adj in all_points and adj not in visited:
                visited.add(adj)
                work.append(adj)
    return visited == all_points


def _objects(x: np.ndarray) -> tuple[Object, Object]:
    colors = [int(c) for c in np.unique(x) if c != 0]
    if len(colors) != 2:
        raise Abstain("two_color_objects_required")
    objects = []
    for color in colors:
        pts = tuple((int(r), int(c)) for r, c in np.argwhere(x == color))
        if not _connected(pts):
            raise Abstain("disconnected_object")
        rs, cs = [r for r, _ in pts], [c for _, c in pts]
        objects.append(Object(color, pts, (min(rs), max(rs), min(cs), max(cs))))
    return objects[0], objects[1]


def _select(x: np.ndarray, name: str) -> tuple[Object, Object]:
    a, b = _objects(x)
    if a.area == b.area:
        raise Abstain("role_area_tie")
    if name == "max_area":
        return (a,b) if a.area > b.area else (b,a)
    if name == "min_area":
        return (a,b) if a.area < b.area else (b,a)
    raise Abstain("invalid_role_predicate")


def _relation(move: Object, anchor: Object) -> tuple[int, int, int]:
    m0,m1,m2,m3 = move.box
    a0,a1,a2,a3 = anchor.box
    rows = max(m0,a0) <= min(m1,a1)
    cols = max(m2,a2) <= min(m3,a3)
    if cols and not rows:
        if m1 < a0:
            return 1, 0, a0-m1-1
        return -1, 0, m0-a1-1
    if rows and not cols:
        if m3 < a2:
            return 0, 1, a2-m3-1
        return 0, -1, m2-a3-1
    raise Abstain("no_unique_projected_direction")


def execute(raw: Any, ast: dict[str, Any]) -> list[list[int]]:
    """Typed interpreter. Never eval/exec strings supplied by a learned core."""
    if not isinstance(ast, dict) or set(ast) != {"schema", "role", "clearance"}:
        raise Abstain("illtyped_ast")
    if ast["schema"] != SCHEMA or ast["role"] not in ("max_area", "min_area"):
        raise Abstain("unknown_operator")
    clearance = ast["clearance"]
    if type(clearance) is not int or not (0 <= clearance <= MAX_CLEARANCE):
        raise Abstain("invalid_clearance")
    x = _grid(raw)
    moving, anchor = _select(x, ast["role"])
    dr_sign, dc_sign, gap = _relation(moving, anchor)
    if gap < clearance:
        raise Abstain("unreachable_clearance")
    distance = gap-clearance
    dr, dc = dr_sign*distance, dc_sign*distance
    out = x.copy()
    for r,c in moving.pixels:
        out[r,c] = 0
    for r,c in moving.pixels:
        rr,cc = r+dr,c+dc
        if not (0 <= rr < x.shape[0] and 0 <= cc < x.shape[1]):
            raise Abstain("out_of_bounds")
        if out[rr,cc] != 0:
            raise Abstain("occupied_destination")
        out[rr,cc] = moving.color
    return out.tolist()


def _observed_delta(x: np.ndarray, y: np.ndarray, moving: Object, anchor: Object) -> tuple[int, int]:
    if x.shape != y.shape or not np.array_equal(x == anchor.color, y == anchor.color):
        raise Abstain("anchor_changed")
    src = np.argwhere(x == moving.color)
    dst = np.argwhere(y == moving.color)
    if src.shape != dst.shape:
        raise Abstain("pixel_count_changed")
    delta = dst.min(axis=0) - src.min(axis=0)
    original = {tuple(int(v) for v in row+delta) for row in src}
    transformed = {tuple(int(v) for v in row) for row in dst}
    if original != transformed:
        raise Abstain("not_a_translation")
    return int(delta[0]), int(delta[1])


def fit(train: list[dict]) -> dict:
    """Create a new parameterized AST from visible train pairs only.

    Never provide test examples, latent labels or tool oracle to this function.
    Returns a traceable abstention on ambiguous or contradictory evidence.
    """
    if not isinstance(train, list) or not train:
        return {"status":"ABSTAIN_NO_TRAIN", "candidates":[], "executions":0}
    candidates: list[dict] = []
    executions = 0
    reasons: dict[str, int] = {}
    for role in ("max_area", "min_area"):
        try:
            inferred: list[int] = []
            for example in train:
                x = _grid(example["input"])
                y = _grid(example["output"])
                moving, anchor = _select(x, role)
                sign_r,sign_c,gap = _relation(moving, anchor)
                shift_r,shift_c = _observed_delta(x, y, moving, anchor)
                if (sign_r and shift_c) or (sign_c and shift_r):
                    raise Abstain("unexpected_axis")
                clearance = gap - (shift_r*sign_r+shift_c*sign_c)
                if not 0 <= clearance <= MAX_CLEARANCE:
                    raise Abstain("clearance_range")
                inferred.append(int(clearance))
            if len(set(inferred)) != 1:
                raise Abstain("inconsistent_clearance")
            ast = {"schema":SCHEMA, "role":role, "clearance":inferred[0]}
            for example in train:
                executions += 1
                if execute(example["input"], ast) != example["output"]:
                    raise Abstain("whole_grid_mismatch")
            candidates.append(ast)
        except (Abstain, KeyError, TypeError, ValueError) as exc:
            k = str(exc) if str(exc) else type(exc).__name__
            reasons[k] = reasons.get(k,0)+1
    return {"status":"CONSISTENT_AST" if candidates else "ABSTAIN_NO_PROGRAM",
            "candidates":candidates, "executions":executions, "rejections":reasons,
            "train_sha256":sha256(json.dumps(train,sort_keys=True).encode()).hexdigest()}


def predict(raw: Any, fitted: dict) -> dict:
    """Deliver only unanimous original-grid prediction; otherwise abstain."""
    candidates = fitted.get("candidates", [])
    if not candidates:
        return {"status":"ABSTAIN_NO_PROGRAM", "output":None}
    try:
        outputs = [execute(raw, ast) for ast in candidates]
    except (Abstain, TypeError, ValueError):
        return {"status":"ABSTAIN_INVALID_SCENE", "output":None}
    if any(output != outputs[0] for output in outputs[1:]):
        return {"status":"ABSTAIN_CONFLICTING_AST", "output":None}
    return {"status":"PROPOSE_ORIGINAL_VERIFIER_REQUIRED", "output":outputs[0]}
