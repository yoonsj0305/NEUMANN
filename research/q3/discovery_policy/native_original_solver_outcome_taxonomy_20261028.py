"""Fail-closed NEUMANN research native SyGuS solver outcome taxonomy.

A candidate is NEVER proven correct merely because native solver returned it.
A solver timeout in stderr must NOT be mistaken for a parser failure.
Original frozen receipts never rewritten; this gate is a postfirst diagnosis.
"""
import re

def classify_native_process(stdout, stderr, returncode, forced=False):
    stdout=stdout or ""
    stderr=stderr or ""
    full=stdout+"\n"+stderr
    if forced or returncode in (-9,-24,-25) or re.search(
        r"(?:interrupted by timeout|time limit exceeded|resource limit reached|timeout(?:\s|\.|$))",
        full,re.I):
        return "BUDGET_HOLD_UNPROVED"
    if returncode != 0 or re.search(
        r"(?:\(error|parse error|symbol .* not declared|unsupported|unknown function)",
        full,re.I):
        return "NATIVE_PARSER_OR_UNSUPPORTED_HOLD"
    if re.search(r"\(\s*define-fun\s",stdout):
        return "NATIVE_CANDIDATE_REQUIRES_INDEPENDENT_ORIGINAL_PROOF"
    if re.search(r"(?:^|\n)\s*infeasible\s*(?:\n|$)",stdout,re.I):
        return "NATIVE_INFEASIBLE_CLAIM_REQUIRES_PROOF"
    return "NATIVE_NO_PROGRAM_UNDETERMINED_HOLD"
