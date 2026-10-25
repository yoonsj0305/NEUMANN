"""Own-weight trained *categorical CEM policy* emitted these two programs.
Human supplied syntax, buffer operations, interpreter, instruction set and optimizer.
Generated combinations are frozen source-only RC12.1 / RC13 decisions.
Not a new autonomous programming language or frontier model.
"""
def learned_gf2_low(a: int,b: int,n: int)->int:
    _validate(a,b,n)
    history_a=[];history_b=[];result=0
    for i in range(n):
        history_a.append((a>>i)&1)
        history_b.append((b>>i)&1)
        acc=0
        for j in range(i+1):
            acc ^= history_a[i-j] & history_b[j]
        result |= acc<<i
    return result

def learned_integer_low(a: int,b: int,n: int)->int:
    _validate(a,b,n)
    history_a=[];history_b=[];scalar=0;result=0
    for i in range(n):
        history_a.append((a>>i)&1)
        history_b.append((b>>i)&1)
        acc=scalar
        for j in range(i+1):
            acc += history_a[j]*history_b[i-j]
        result |= (acc & 1)<<i
        scalar = acc>>1
    return result

def _validate(a,b,n):
    if not all(isinstance(v,int) and not isinstance(v,bool) for v in (a,b,n)):
        raise ValueError("Expected exactly n-bit nonnegative unsigned integers")
    if n<1 or a<0 or b<0 or a>=1<<n or b>=1<<n:
        raise ValueError("bad operand width or sign")

def provable_emitted_programs():
    return {
      "gf2":{"buffers":2,"scalar":False,"address":["i-j","j"],
             "combine":"XOR","all_width_proof":"GF2 convolution"},
      "integer":{"buffers":2,"scalar":True,"address":["j","i-j"],
             "combine":"ADD","state_update":"SHR1",
             "all_width_proof":"diagonal sum + carry invariant"},
      "global_new_DSL":"OPEN", "strong_classical_advantage":True
    }
