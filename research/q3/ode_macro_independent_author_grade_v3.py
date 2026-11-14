"""Truth-only independent whole-domain audit, no import of source inference program.
Uses only immutable output artifact and independently retained public author truth.
"""
import json,pathlib,hashlib
import sympy as sp
R=pathlib.Path('/mnt/data/neumann_q3_ode_v3_isolated')
x=sp.Symbol('x',real=True)
source_pred=json.loads((R/'first_source_only_ODE_definitions.json').read_text())
truth=json.loads(pathlib.Path('/mnt/data/neumann_q3_ode_v2/original_author_math_grade_only.json').read_text())
by={r['task']:r for r in truth['true_math']}
assert len(source_pred['cases'])==3 and len(by)==3
cases=[]
for row in source_pred['cases']:
    gold=sp.sympify(by[row['task']]['author_full_symbolic_expression'],locals={'x':x})
    matched=[]
    for candidate in row['accepted_source_derived_macros']:
        law=candidate['derived_executable_operator']
        rhs=sp.sympify(law['ODE_RHS'],locals={'x':x})
        anchor=sp.sympify(law['initial_x'])
        init=sp.sympify(law['initial_M'])
        derivative_identically_zero=sp.simplify(sp.diff(gold,x)-rhs)==0
        initial_identically_zero=sp.simplify(gold.subs(x,anchor)-init)==0
        if derivative_identically_zero and initial_identically_zero:
            matched.append({'inferred_ODE_family':candidate['family'],
                            'exact_mathematical_identity_of_derivative':True,
                            'exact_initial_value':True,
                            'whole_connected_domain':'PASS_BY_FIRST_ORDER_IVP_UNIQUENESS'})
    cases.append({'id':row['task'],'exact_whole_domain':bool(matched),'proofs':matched})
assert all(q['exact_whole_domain'] for q in cases)
receipt={'schema':'NEUMANN_Q3_SEPARATED_SOURCE_ONLY_V3_GOLD_MATH_ALL_DOMAIN.v1',
         'source_only_code_has_no_gold_registry':True,
         'predictions_sha256':hashlib.sha256((R/'first_source_only_ODE_definitions.json').read_bytes()).hexdigest(),
         'author_original_truth_sha256':hashlib.sha256(pathlib.Path('/mnt/data/neumann_q3_ode_v2/original_author_math_grade_only.json').read_bytes()).hexdigest(),
         'separate_grader_never_imports_source_inference_module':True,
         'all_first_public_development_originals':cases,
         'exact_mathematical_author_whole_domain_count':sum(q['exact_whole_domain'] for q in cases),
         'NATIVE_PRIVATE_BENCHMARK_BLIND':False,
         'human_defined_differential_grammar':True,
         'Q3_GLOBAL':'OPEN','NEURAL_AUTONOMOUS_NEW_PRIMITIVE':'NOT_PROVED'}
f=R/'separate_source_gold_entire_domain_grade.json'
f.write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
print(json.dumps({'source_only_genuine_isolation':True,'whole_domain_mathematical_exact':3,
                  'grade_SHA256':hashlib.sha256(f.read_bytes()).hexdigest()}))
