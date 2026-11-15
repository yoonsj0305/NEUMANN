"""DEVELOPMENT ONLY: first-failure CASE of each run (P0-F of the budgeted-reachability directive), from machine events.

  python research/q3/budgeted_reach_cases_dev.py E rows.jsonl [...]
"""
import json, sys, collections
def case(r):
    if r['solved']:
        return 'solved'
    ms = r['machines']
    if not ms:
        return 'no machine attempted'
    m = ms[0]
    ev = [e for e in m['events'] if not e.startswith('reachability')]
    if m['formed'] and m['challenge'] is False:
        return 'CASE 4: fold passed, independent challenge refuted'
    if any('self-test counterexample' in e for e in ev):
        return 'CASE 4: fold passed, self-test counterexample (then not formed)'
    if m['W'] and any('no update for component 1' in e for e in ev):
        return 'CASE 3: state component added, its Update not synthesised'
    if ev and ev[0].startswith('no update for component 0'):
        return 'CASE 2: no Update on the first observed table'
    if any(e.startswith('round') for e in ev) and any('no update for component' in e for e in ev):
        return 'CASE 2b: Update found, fold fails, re-synthesis fails'
    if any('too few defined transitions' in e for e in ev):
        return 'states undefined (too few defined transitions)'
    if ev and ev[-1] == 'query limit':
        return 'CASE 1: query limit before an Update'
    if any('counterexample not localisable' in e for e in ev):
        return 'counterexample not localisable'
    return 'other: ' + (ev[-1] if ev else '')
if __name__ == '__main__':
    arm = sys.argv[1]
    for f in sys.argv[2:]:
        rs = [json.loads(l) for l in open(f) if json.loads(l)['arm'] == arm]
        c = collections.Counter(case(r) for r in rs)
        print(f.split('/')[-1], arm, len(rs), dict(c.most_common()))
