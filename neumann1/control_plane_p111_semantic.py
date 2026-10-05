"""P1.11 fresh opened-development semantic registry.

No model scores are observed or computed here.
"""
from __future__ import annotations

from neumann1.control_plane_p17 import build_candidates

SCHEMA = "neumann.control-plane-p1.11.semantic-registry.v1"

SEMANTIC_INSTRUCTIONS = (
    "X is the active replica and Y is the warm standby. Resolve 'It' to the failover copy, then return a complete assignment.",
    "A is the tokenizer, B is the syntax analyzer, and C is the optimizer. Resolve 'It' to the stage that builds the parse tree, then return a complete assignment.",
    "P is the compressor, Q is the condenser, R is the expansion valve, and S is the evaporator. Resolve 'It' to the component that rejects heat to the surroundings, then return a complete assignment.",
    "M is the public verification key and N is the private signing key. Resolve 'It' to the credential used to check whether a signature is valid, then return a complete assignment.",
    "A is the scheduler, B is the worker, and C is the audit logger. Resolve 'It' to the component that assigns jobs to executors, then return a complete assignment.",
    "P is the image sensor, Q is the inertial sensor, R is the satellite navigation receiver, and S is the fusion engine. Resolve 'It' to the module that combines multiple measurements into one state estimate, then return a complete assignment.",
    "M is the circuit breaker, N is the transformer, and O is the battery. Resolve 'It' to the device that stores electrical energy, then return a complete assignment.",
    "X is the upstream channel and Y is the downstream channel. Resolve 'It' to the path carrying requests from the client toward the service, then return a complete assignment.",
    "A is the pump, B is the control valve, and C is the reservoir. Resolve 'It' to the element that meters fluid flow, then return a complete assignment.",
    "P is the source text, Q is the intermediate representation, R is the object code, and S is the executable image. Resolve 'It' to the relocatable machine instructions emitted before final linking, then return a complete assignment.",
    "M is the camera, N is the wheel encoder, and O is the localization filter. Resolve 'It' to the module that estimates robot pose from sensor evidence, then return a complete assignment.",
    "X is the traction motor and Y is the friction brake. Resolve 'It' to the component that removes kinetic energy to stop the machine, then return a complete assignment.",
)


def parser_view(view):
    if type(view) is not dict or set(view) != {"instruction", "public"}:
        raise ValueError("exact P1.11 semantic view required")
    if view.get("instruction") not in SEMANTIC_INSTRUCTIONS:
        raise ValueError("unregistered P1.11 semantic instruction")
    public = view.get("public")
    if (
        type(public) is not dict
        or set(public) != {"query"}
        or type(public.get("query")) is not str
        or not public["query"]
    ):
        raise ValueError("exact nonempty query-only payload required")
    return {
        "instruction": "Return a complete assignment.",
        "public": {"query": public["query"]},
    }


def build_bundle(view):
    parsed = parser_view(view)
    return parsed, build_candidates(parsed)


def contract():
    return {
        "schema": SCHEMA,
        "semantic_instructions": list(SEMANTIC_INSTRUCTIONS),
        "normalized_parser_instruction": "Return a complete assignment.",
        "query_bytes_changed": False,
        "free_form_instruction_acceptance": False,
        "hidden_reference_access": False,
        "p110_task_reuse": False,
        "model_inference": False,
    }
