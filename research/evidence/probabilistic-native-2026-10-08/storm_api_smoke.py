"""Single official die API fixture; engineering only, no screening by timings."""
from fractions import Fraction
import json
from pathlib import Path
import sys
root=Path('/kaggle/working/neumann_probabilistic')
sys.path.insert(0,str(root/'deps'))
import stormpy
import stormpy.examples.files
rows=[]
program=stormpy.parse_prism_program(stormpy.examples.files.prism_dtmc_die)
props=stormpy.parse_properties('P=? [F "one"]',program)
for route in ['sparse_exact','sparse_parametric_bisim','dd_parametric','dd_parametric_bisim_sparse']:
    try:
        if route=='sparse_exact': model=stormpy.build_sparse_exact_model(program,props)
        elif route=='sparse_parametric_bisim':
            model=stormpy.build_sparse_parametric_model(program,props)
            model=stormpy.perform_sparse_bisimulation(model,props,stormpy.BisimulationType.STRONG)
        else:
            model=stormpy.build_symbolic_parametric_model(program,props)
            if route=='dd_parametric_bisim_sparse':
                model=stormpy.perform_symbolic_bisimulation(model,props,stormpy.QuotientFormat.SPARSE)
            else: model=stormpy.transform_to_sparse_model(model)
        result=stormpy.model_checking(model,props[0],only_initial_states=True)
        values=[str(result.at(i)) for i in model.initial_states]
        assert len(values)==1 and Fraction(values[0])==Fraction(1,6)
        rows.append({'route':route,'status':'ENGINEERING_PASS','states':model.nr_states,'transitions':model.nr_transitions,
                     'values':values,'class':type(model).__name__})
    except Exception as exc:
        rows.append({'route':route,'status':'NOT_VERIFIED','error_type':type(exc).__name__,'error':str(exc)})
report={'kind':'ENGINEERING_ONLY','rows':rows,'preprocess_doc':stormpy.preprocess_symbolic_input.__doc__,
        'solver_environment_attributes':[x for x in dir(stormpy.Environment().solver_environment) if not x.startswith('_')],
        'model_checking_cost':'NOT_MEASURED','G0':'NOT_EXECUTED','learning':'HOLD'}
with (root/'api-smoke-first.json').open('x') as out: json.dump(report,out,indent=2)
print(json.dumps(report,indent=2),flush=True)
