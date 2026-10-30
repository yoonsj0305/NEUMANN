"""Reusable fail-closed NEUMANN typed-AST, coordinate symmetry and EOS gate.

Research-only pure helpers; does not claim neural novelty or SMT certification.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class TypedPolynomialAST:
    degree: int
    coefficient: int
    constant: int
    x_origin: int

def canonicalize_observations(observations):
    if not observations:
        raise ValueError("EMPTY_OBSERVATION")
    x0=observations[0][0]
    return tuple((x-x0,y) for x,y in observations)

def decode_multiply_eos(tokens, max_multiplications=6):
    """Positive NEXT_MUL=1 and EOS=0. Missing EOS is invalid AST."""
    degree=0
    for tok in tokens:
        if tok==0:
            return degree if 1<=degree<=max_multiplications else None
        if tok!=1:
            return None
        degree+=1
        if degree>max_multiplications:
            return None
    return None

def compile_executable_ast(ast: Optional[TypedPolynomialAST]):
    if ast is None or not isinstance(ast,TypedPolynomialAST):
        return None
    d,a,c,o=ast.degree,ast.coefficient,ast.constant,ast.x_origin
    if not 1<=d<=6 or a==0:
        return None
    rel=f'(- x {o})'
    power=rel if d==1 else '(* '+' '.join([rel]*d)+')'
    return f'(define-fun inv ((x Int) (y Int)) Bool (= y (+ (* {a} {power}) {c})))'

def exact_trace_match_does_not_imply_proof(trace_fits,source_3vc_results):
    """Only formal full original semantic checks can be a proof."""
    return bool(trace_fits) and tuple(source_3vc_results)==('unsat',)*3

def classify_architecture_result(has_independent_external_authors,
                                 trained_generates_novel_operator,
                                 stronger_classic_beaten,
                                 full_original_3vc_proven):
    if all((has_independent_external_authors,trained_generates_novel_operator,
            stronger_classic_beaten,full_original_3vc_proven)):
        return 'NEEDS_INDEPENDENT_SCIENTIFIC_REVIEW'
    return 'G1_HOLD'
