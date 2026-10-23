"""Q3 independent static contract for first Keijzer/Neat original benchmark.

This guard constrains what is claimed from the source-only neural learner:
the first inference graph edits must not import author formula registries,
and the prospective author task cohort must stay the externally selected 12.
Not a security proof of code sandboxing; the original public dataset is
accessible online, so publication-quality claims must say PUBLIC author originals.
"""
from pathlib import Path
import ast

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'first_keijzer_neat_source_only.py'
LEARNER=ROOT/'learned_dynamic_graph_family_2authors.py'
assert SOURCE.exists() and LEARNER.exists()
src=SOURCE.read_text(encoding='utf8')
learn=LEARNER.read_text(encoding='utf8')
source_tree=ast.parse(src)
learner_tree=ast.parse(learn)
selected=next(v.value for v in source_tree.body if isinstance(v,ast.Assign)
              for v in v.targets if isinstance(v,ast.Name) and v.id=='TARGETS')
chosen=ast.literal_eval(selected)
assert len(chosen)==12 and len(set(chosen))==12
assert sum(x.startswith('Keijzer-') for x in chosen)==7
assert sum(x.startswith('Neat-') for x in chosen)==5
assert not any(x.startswith(('Nguyen-','Livermore-')) for x in chosen)
imports=[node.module or '' for node in ast.walk(learner_tree)
         if isinstance(node,ast.ImportFrom)]
assert 'first_keijzer_neat_source_only' not in imports
assert 'livermore_original_source_eight' not in imports
fn={n.name:n for n in learner_tree.body if isinstance(n,ast.FunctionDef)}
for entrypoint in ('train_synthetic','infer','compose_from_grammar','execute'):
    assert entrypoint in fn
    body=ast.get_source_segment(learn,fn[entrypoint]) or ''
    assert 'author_formula(' not in body
    assert 'original_expression' not in body
assert 'grade' in fn
assert 'original_expression' in ast.get_source_segment(learn,fn['grade'])
print('Q3_12_AUTHOR_ORIGINAL_BLIND_SOURCE_COHORT_AND_INFERENCE_PROGRAM_STATIC_CONTRACT_PASS',
      {'cohort':chosen,'source_only_learner_modules':imports})
