"""Failure-to-extend structural gate from end-to-end observations only.

A one-state deterministic bit-stream transducer must map identical current
symbols to identical emitted bits. This code detects the contradictory-output
witness and asks for more state capacity, without receiving hidden carry labels.
The capacity-growth controller itself is HUMAN-CODED classical software.
"""

def observe_conflict(examples):
    seen={}
    for ex in examples:
        for symbol,output in zip(ex["input_symbols"],ex["output_bits"]):
            symbol=tuple(symbol)
            if symbol in seen and seen[symbol]!=int(output):
                return {"same_symbol":symbol,"first_output":seen[symbol],
                        "second_output":int(output),"minimum_required_states":2}
            seen.setdefault(symbol,int(output))
    return None

def addition_end_to_end_demonstrations():
    # Input/output bit streams only. No intermediate state/carry target.
    examples=[]
    for n in (1,2):
        for a in range(1<<n):
            for b in range(1<<n):
                pairs=[((a>>i)&1,(b>>i)&1) for i in range(n+1)]
                output=[((a+b)>>i)&1 for i in range(n+1)]
                examples.append({"input_symbols":pairs,"output_bits":output})
    return examples

def propose_minimal_expansion():
    conflict=observe_conflict(addition_end_to_end_demonstrations())
    if conflict is None:
        return {"status":"INSUFFICIENT_EVIDENCE"}
    return {"status":"NEED_ADDITIONAL_STATE","lower_bound":2,
            "witness":conflict,"upper_bound":"NOT_PROVEN_BY_THIS_GATE"}
