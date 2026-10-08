"""P1.12 fresh semantic registry; independent of P1.11 score-bearing tasks."""
from __future__ import annotations

from neumann1.control_plane_p17 import build_candidates

SCHEMA = "neumann.control-plane-p1.12.semantic-registry.v1"

SEMANTIC_INSTRUCTIONS = [
    "X is the certificate revocation list and Y is the trusted timestamp authority. Resolve 'It' to the service that certifies when a digital record existed, then return a complete assignment.",
    "A is the associative map, B is the stack, and C is the heap. Resolve 'It' to the container retrieving stored records by lookup key, then return a complete assignment.",
    "P is the planetary coronagraph, Q is the spectrometer, R is the radio dish, and S is the photometer. Resolve 'It' to the instrument that spreads incoming electromagnetic radiation into different wavelengths, then return a complete assignment.",
    "M is the lysosome and N is the ribosome. Resolve 'It' to the cellular machinery translating messenger RNA into chains of amino acids, then return a complete assignment.",
    "A is the transfer warehouse, B is the cold-storage facility, and C is the cross-dock terminal. Resolve 'It' to the hub moving incoming freight straight onto outgoing vehicles without long dwell time, then return a complete assignment.",
    "P is the demodulator, Q is the equalizer, R is the interleaver, and S is the frequency synthesizer. Resolve 'It' to the circuit recovering the original message bits from a modulated waveform, then return a complete assignment.",
    "M is the request dispatcher, N is the consensus engine, and O is the cache eviction policy. Resolve 'It' to the protocol component bringing replicas to agreement on operation ordering, then return a complete assignment.",
    "X is the annealing furnace and Y is the milling cutter. Resolve 'It' to the equipment that softens work-hardened metal through controlled heating, then return a complete assignment.",
    "A is the rudder, B is the propeller, and C is the ballast tank. Resolve 'It' to the vessel compartment admitting seawater to adjust buoyancy, then return a complete assignment.",
    "P is the optical fiber coupler, Q is the polarization rotator, R is the diffraction grating, and S is the photomultiplier. Resolve 'It' to the periodic surface splitting white illumination into colored beams through interference, then return a complete assignment.",
    "M is the amygdala, N is the hippocampus, and O is the cerebellum. Resolve 'It' to the brain region supporting long-term formation of autobiographical recollections, then return a complete assignment.",
    "X is the checksum calculator and Y is the watchdog timer. Resolve 'It' to the hardware supervisor that resets unresponsive embedded software, then return a complete assignment."
]

def parser_view(view):
    if type(view) is not dict or set(view) != {"instruction", "public"}:
        raise ValueError("exact P1.12 semantic view required")
    if view["instruction"] not in SEMANTIC_INSTRUCTIONS:
        raise ValueError("unregistered P1.12 instruction")
    public = view["public"]
    if type(public) is not dict or set(public) != {"query"} or type(public["query"]) is not str or not public["query"]:
        raise ValueError("exact P1.12 nonempty query-only payload required")
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
        "p111_task_reuse":False,
        "model_inference":False,
    }
