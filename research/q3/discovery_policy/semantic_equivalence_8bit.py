"""Fail-closed finite-semantic-quotient gate for tiny 8-bit program research.

A PASS in this module means only equivalence relative to the explicitly supplied
finite grammar. Never promote it to cross-domain model-discovery intelligence.
"""
from dataclasses import dataclass
from hashlib import sha256
from itertools import product
from typing import Iterable, Iterator

BYTE_DOMAIN=range(256)
OPERATORS=('A','X','R')

@dataclass(frozen=True)
class Program8:
    pair: str
    params: tuple[int,int]
    def __post_init__(self):
        if len(self.pair)!=2 or any(op not in OPERATORS for op in self.pair):
            raise ValueError('Only two typed A/X/R operations admitted')
        for op,n in zip(self.pair,self.params):
            if not (1<=n<=7 if op=='R' else 0<=n<=255):
                raise ValueError('Parameter outside admitted domain')


def apply(op:str,x:int,p:int)->int:
    if op=='A':return (x+p)&255
    if op=='X':return x^p
    if op=='R':return ((x<<p)|(x>>(8-p)))&255
    raise ValueError('Unsupported primitive')


def execute(program:Program8,x:int)->int:
    if not 0<=x<=255:raise ValueError('Invalid byte input')
    for op,p in zip(program.pair,program.params):x=apply(op,x,p)
    return x


def truth_table(program:Program8)->bytes:
    return bytes(execute(program,x) for x in BYTE_DOMAIN)


def parameter_range(op:str)->range:
    return range(1,8) if op=='R' else range(256)


def legal_programs(pairs:Iterable[str])->Iterator[Program8]:
    for pair in pairs:
        if len(pair)!=2 or any(op not in OPERATORS for op in pair):
            raise ValueError('Unknown operator type pair')
        for a,b in product(parameter_range(pair[0]),parameter_range(pair[1])):
            yield Program8(pair,(a,b))


def build_exact_index(pairs:Iterable[str])->dict[bytes,Program8]:
    # Full truth-table byte strings are map keys: no hash collision assumption.
    library={}
    for p in legal_programs(pairs):
        library.setdefault(truth_table(p),p)
    return library


def library_membership(target:Program8,index:dict[bytes,Program8]):
    """Return (CLASSICAL_EQUIVALENT,witness) or (NOT_IN_THIS_LIBRARY,None).

    This is exact on all 256 inputs for *this explicitly enumerated library*.
    """
    witness=index.get(truth_table(target))
    if witness is None:return 'NOT_IN_THIS_LIBRARY',None
    return 'CLASSICAL_EQUIVALENT',witness


def xor_rotate_rewrite(c:int,r:int)->tuple[Program8,Program8]:
    """Constructively prove XR(c,r) is RX(r, ROL(c,r))."""
    p=Program8('XR',(c,r))
    q=Program8('RX',(r,apply('R',c,r)))
    assert truth_table(p)==truth_table(q)
    return p,q
