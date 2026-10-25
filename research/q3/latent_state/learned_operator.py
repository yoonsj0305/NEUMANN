"""Auto-extracted binary transducer from NEUMANN OWN-WEIGHT neural checkpoint.
This operator is a scoped proof: target is known binary addition, 2-state prior was
human-provided, and strong classical enumeration dominates cost. NOT global Q3.
Weight SHA256 4cc8498de9ebecc2f5e629027686524e143ee31149496978a643fb1ea02bd935
First frozen out-of-length prediction SHA256 6c34f5e6b07c88ede7334adebc09b6225c106c694177f87bb30e9487cc6a5f1d
The actual torch weights, training and full 6-seed records are in the research ZIP.
"""
EMIT = (0, 1, 1, 0, 1, 0, 0, 1)
NEXT = (0, 0, 0, 1, 0, 1, 1, 1)

def H_LEARNED_ADD(a: int, b: int, n: int) -> int:
    if not (isinstance(a,int) and isinstance(b,int) and isinstance(n,int) and
            n>=1 and 0<=a<2**n and 0<=b<2**n):
        raise ValueError("Expected two nonnegative n-bit integers")
    state=0
    output=0
    for bit in range(n+1):
        symbol=((a>>bit)&1)+2*((b>>bit)&1)
        index=state*4+symbol
        output |= EMIT[index]<<bit
        state=NEXT[index]
    return output
