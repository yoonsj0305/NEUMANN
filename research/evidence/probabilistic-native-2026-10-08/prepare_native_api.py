"""Native input parser preflight; no model building/checking or performance."""
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib
import json
import re
import sys
root = Path('/kaggle/working/neumann_probabilistic')
sys.path.insert(0, str(root / 'deps'))
import stormpy
ROWS = __PUBLIC_NATIVE_SOURCES__
cases = {c['case_id']: c for c in json.loads((root / 'execution-cases-first.json').read_text())}
results = []
for row in ROWS:
    case = cases[row['case_id']]
    result = {'case_id': case['case_id'], 'kind': 'NATIVE_PARSER_ONLY'}
    try:
        for source in row['originals']:
            path = root / 'native-inputs' / row['family'] / source['name']
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                with urlopen(Request(source['url'], headers={'User-Agent': 'NEUMANN-public-source-audit'}), timeout=30) as response:
                    data = response.read(8_000_001)
                assert len(data) <= 8_000_000
                assert hashlib.sha256(data).hexdigest() == source['sha256']
                with path.open('xb') as out:
                    out.write(data)
        if row['prism'] is None:
            result.update(status='NOT_APPLICABLE', reason='Original is PGCL, not supported PRISM API')
        else:
            prism = root / 'native-inputs' / row['family'] / row['prism']['name']
            properties = root / 'native-inputs' / row['family'] / row['properties']['name']
            # Remove published RESULT comments, never pass Oracle answers to parser.
            property_text = re.sub(r'//[^\n]*', '', properties.read_text())
            program = stormpy.parse_prism_program(str(prism))
            props = stormpy.parse_properties_for_prism_program(property_text, program)
            chosen = [p for p in props if p.name == case['goal']]
            assert len(chosen) == 1
            constants = ','.join(f'{p["name"]}={p["value"]}' for p in case['parameters'])
            description, chosen = stormpy.preprocess_symbolic_input(program, chosen, constants)
            result.update(status='ENGINEERING_PASS', formula=str(chosen[0].raw_formula),
                          outer_filter=case['goal_expression']['fun'], constants=constants,
                          published_result_comments_supplied=False)
    except Exception as exc:
        result.update(status='NOT_VERIFIED', error_type=type(exc).__name__, error=str(exc))
    results.append(result)
    print(json.dumps(result), flush=True)
with (root / 'native-source-api-first.json').open('x') as out:
    json.dump({'kind': 'ENGINEERING_ONLY', 'rows': results, 'performance': 'NOT_MEASURED'}, out, indent=2)
with (root / 'native-sources-first.json').open('x') as out:
    json.dump(ROWS, out, indent=2)
