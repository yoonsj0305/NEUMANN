"""P1.10 fresh opened-development semantic registry."""
from __future__ import annotations
from neumann1.control_plane_p17 import build_candidates

SCHEMA="neumann.control-plane-p1.10.semantic-registry.v1"

SEMANTIC_INSTRUCTIONS=(
 "X is the primary route and Y is the reserve route. Resolve 'It' to the emergency path, then return a complete assignment.",
 "A is the intake node, B is the transform node, and C is the output node. Resolve 'It' to the terminal node, then return a complete assignment.",
 "P is the sensor, Q is the controller, R is the actuator, and S is the recorder. Resolve 'It' to the component that physically changes the system, then return a complete assignment.",
 "M is the leader and N is the deputy. Resolve 'It' to the succession role, then return a complete assignment.",
 "A is the volatile cache, B is the persistent store, and C is the archive. Resolve 'It' to the fastest temporary tier, then return a complete assignment.",
 "P is launch, Q is cruise, R is braking, and S is docking. Resolve 'It' to the rendezvous completion phase, then return a complete assignment.",
 "M is the estimator, N is the controller, and O is telemetry. Resolve 'It' to the state-inference component, then return a complete assignment.",
 "X is the transmit path and Y is the receive path. Resolve 'It' to the inbound link, then return a complete assignment.",
)

def parser_view(view):
    if type(view) is not dict or set(view)!={"instruction","public"}:
        raise ValueError("exact P1.10 semantic view required")
    if view.get("instruction") not in SEMANTIC_INSTRUCTIONS:
        raise ValueError("unregistered P1.10 semantic instruction")
    public=view.get("public")
    if type(public) is not dict or set(public)!={"query"} or type(public.get("query")) is not str or not public["query"]:
        raise ValueError("exact nonempty query-only payload required")
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
      "p19_task_reuse":False,
    }
