"""Prepare opened public inputs and inspect parser semantics, without solving."""
from pathlib import Path
import hashlib
import json
import sys
from urllib.request import Request, urlopen

root = Path('/kaggle/working/neumann_probabilistic')
sys.set_int_max_str_digits(100_000)
sys.path.insert(0, str(root / 'deps'))
import stormpy

CASES = __PUBLIC_EXECUTION_CASES__
rows = []
for case in CASES:
    row = {'case_id': case['case_id'], 'kind': 'PARSER_ONLY'}
    try:
        dest = root / 'inputs' / case['family'] / case['file']
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            with urlopen(Request(case['source_url'], headers={'User-Agent': 'NEUMANN-public-source-audit'}), timeout=30) as response:
                raw = response.read(8_000_001)
            assert len(raw) <= 8_000_000
            assert hashlib.sha256(raw).hexdigest() == case['file_sha256']
            with dest.open('xb') as out:
                out.write(raw)
        assert hashlib.sha256(dest.read_bytes()).hexdigest() == case['file_sha256']
        model, properties = stormpy.parse_jani_model(str(dest))
        chosen = [p for p in properties if p.name == case['goal']]
        assert len(chosen) == 1
        constants = ','.join(f'{p["name"]}={p["value"]}' for p in case['parameters'])
        description, chosen = stormpy.preprocess_symbolic_input(model, chosen, constants)
        model = description.as_jani_model()
        chosen = stormpy.eliminate_reward_accumulations(model, chosen)
        row.update(status='ENGINEERING_PASS', formula=str(chosen[0].raw_formula),
                   outer_filter=case['goal_expression']['fun'], constants=constants,
                   parsed_model_type=str(model.model_type))
    except Exception as exc:
        row.update(status='NOT_VERIFIED', error_type=type(exc).__name__, error=str(exc))
    rows.append(row)
    print(json.dumps(row), flush=True)
report = {'kind': 'PARSER_ENGINEERING_ONLY', 'rows': rows, 'scientific_performance': 'NOT_MEASURED',
          'G0': 'NOT_EXECUTED', 'learning': 'HOLD', 'oracle_answers_supplied_to_parser': False}
with (root / 'source-api-first.json').open('x') as out:
    json.dump(report, out, indent=2)
with (root / 'execution-cases-first.json').open('x') as out:
    json.dump(CASES, out, indent=2)
