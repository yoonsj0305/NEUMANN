"""P1.9 fresh opened-development semantic registry.

This file freezes the finite public semantic instructions for the first P1.9
opened-development score.  It only normalizes the instruction string for the
unchanged P1.7 bounded query parser; query bytes are preserved exactly.
"""
from __future__ import annotations

from neumann1.control_plane_v1 import snapshot
from neumann1.control_plane_p17 import build_candidates

SCHEMA = "neumann.control-plane-p1.9.semantic-registry.v1"

SEMANTIC_INSTRUCTIONS = (
    "X is the nominal path and Y is the contingency path. Resolve 'It' to the fallback path, then return a complete assignment.",
    "A is the receiving queue, B is the processing queue, and C is the delivery queue. Resolve 'It' to the entry queue, then return a complete assignment.",
    "P is thermal control, Q is propulsion, R is radio, and S is navigation. Resolve 'It' to the communications subsystem, then return a complete assignment.",
    "M is the coordinator and N is the operator. Resolve 'It' to the managerial role, then return a complete assignment.",
    "A is the hot tier, B is the warm tier, and C is the archive tier. Resolve 'It' to the long-term storage tier, then return a complete assignment.",
    "P is ascent, Q is coast, R is descent, and S is touchdown. Resolve 'It' to the landing phase, then return a complete assignment.",
    "M is the detector, N is the predictor, and O is the logger. Resolve 'It' to the forecasting component, then return a complete assignment.",
    "X is the uplink and Y is the downlink. Resolve 'It' to the ground-to-space link, then return a complete assignment.",
)

def parser_view(view):
    if type(view) is not dict or set(view) != {"instruction","public"}:
        raise ValueError("exact P1.9 semantic view required")
    if view.get("instruction") not in SEMANTIC_INSTRUCTIONS:
        raise ValueError("unregistered P1.9 semantic instruction")
    public=view.get("public")
    if type(public) is not dict or set(public) != {"query"} or type(public.get("query")) is not str or not public["query"]:
        raise ValueError("exact nonempty P1.9 query-only payload required")
    return {"instruction":"Return a complete assignment.","public":{"query":public["query"]}}

def build_bundle(view):
    parsed=parser_view(view)
    return parsed,build_candidates(parsed)

def contract():
    return {
      "schema":SCHEMA,
      "semantic_instructions":list(SEMANTIC_INSTRUCTIONS),
      "normalized_parser_instruction":"Return a complete assignment.",
      "query_bytes_changed":False,
      "free_form_instruction_acceptance":False,
      "hidden_reference_access":False,
      "p18_task_reuse":False,
    }
