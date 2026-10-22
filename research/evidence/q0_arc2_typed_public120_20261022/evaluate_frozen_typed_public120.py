#!/usr/bin/env python3
"""Answer-free transfer test of PREEXISTING ARC2 code; no model changes and no target labels."""
import argparse, hashlib, json, pathlib, sys, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--masked', required=True)
    ap.add_argument('--baseline-dir', required=True)
    ap.add_argument('--typed-dir', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    sys.path.insert(0, str(pathlib.Path('research/evidence/q0_arcagi2_fullfirst_20261022').resolve()))
    sys.path.insert(0, str(pathlib.Path(args.baseline_dir).resolve()))
    sys.path.insert(0, str(pathlib.Path(args.typed_dir).resolve()))
    from arc_compositional_grammar import find_programs,choose_program,predict as basic_predict
    from relational_pipeline_selector_memo_v2 import task_rules,complexity,predict as typed_predict
    fs = sorted(pathlib.Path(args.masked).glob('*.json'))
    assert len(fs)==120, f'expected 120 original evaluation tasks, got {len(fs)}'
    ids = [p.stem for p in fs]
    assert len(set(ids))==120
    rows=[]
    start=time.perf_counter()
    for i,p in enumerate(fs):
        task=json.loads(p.read_text())
        assert task['train'] and task['test']
        assert all('output' not in x for x in task['test']), 'GRADING ANSWER LEAK'
        t=time.perf_counter()
        old_programs=find_programs(task)
        b=choose_program(old_programs)
        old_pred=basic_predict(task,b) if b else None
        old_s=time.perf_counter()-t
        t=time.perf_counter()
        new_programs=task_rules(task)
        n=min(new_programs,key=complexity) if new_programs else None
        new_pred=typed_predict(task,n) if n else None
        new_s=time.perf_counter()-t
        hybrid_pred=old_pred if old_pred is not None else new_pred
        row={'id':p.stem,'n_legacy':len(old_programs),'n_typed':len(new_programs),
             'old_pred':old_pred,'typed_pred':new_pred,'hybrid_pred':hybrid_pred,
             'typed_best_AST':n,'legacy_wall_s':old_s,'typed_wall_s':new_s}
        rows.append(row)
        if (i+1)%30==0:print('PREGRADE_PROGRESS',i+1,'old_covered',sum(x['n_legacy']>0 for x in rows),'typed_covered',sum(x['n_typed']>0 for x in rows),flush=True)
    out={'schema':'Q0_EXISTING_FROZEN_TYPED_AST_ARC2_PUBLIC120.v1','source_original': 'arcprize/ARC-AGI-2@f3283f727488ad98fe575ea6a5ac981e4a188e49',
         'evaluation_tree':'8d04288aac3146b7c47d0b799c18bc9c0217d838',
         'n':120,'label_free':True,'previously_evaluated_public_corpus':True,
         'new_AST_is_unchanged_previously_implemented_classical_not_a_neural_model':True,
         'total_wall_s':time.perf_counter()-start,'rows':rows}
    output=pathlib.Path(args.out)
    output.parent.mkdir(parents=True,exist_ok=True)
    b=(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n').encode()
    output.write_bytes(b)
    print('FROZEN_ARC2_PUBLIC120_PRE_GRADE_SHA256',hashlib.sha256(b).hexdigest(),'COVERAGE',sum(x['n_legacy']>0 for x in rows),sum(x['n_typed']>0 for x in rows),'TOTAL_WALL',out['total_wall_s'],flush=True)

if __name__=='__main__':main()
