#!/usr/bin/env python3
"""First ConceptARC transfer. Import actual frozen ARC2 proposer only; no labels, no retuning."""
import argparse, pathlib, json, sys, hashlib, time

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--masked',required=True);a.add_argument('--meta',required=True);a.add_argument('--out',required=True)
    args=a.parse_args()
    sys.path.insert(0,str(pathlib.Path('research/evidence/q0_arcagi2_fullfirst_20261022').resolve()))
    sys.path.insert(0,str(pathlib.Path('research/evidence/q0_arcagi2_trainholdout_first_20261022').resolve()))
    sys.path.insert(0,str(pathlib.Path('research/evidence/q0_arc2_typed_intermediate_20261022').resolve()))
    from arc_compositional_grammar import find_programs,choose_program,predict as old_predict
    from relational_pipeline_selector_memo_v2 import task_rules,complexity,predict as typed_predict
    meta=json.loads(pathlib.Path(args.meta).read_text())
    assert meta['labels_masked'] and meta['n']==160 and meta['test_grids']==480
    files=sorted(pathlib.Path(args.masked).glob('*.json'))
    assert len(files)==160
    rows=[];start=time.perf_counter()
    for path in files:
        task=json.loads(path.read_text())
        assert len(task['test'])==3 and all('output' not in r for r in task['test'])
        t=time.perf_counter()
        old_prog=find_programs(task);old=choose_program(old_prog)
        pred_old=old_predict(task,old) if old else None
        old_t=time.perf_counter()-t
        t=time.perf_counter()
        rules=task_rules(task);best=min(rules,key=complexity) if rules else None
        pred_typed=typed_predict(task,best) if best else None
        typed_t=time.perf_counter()-t
        assert pred_old is None or len(pred_old)==3
        assert pred_typed is None or len(pred_typed)==3
        uid=path.stem
        rows.append({'id':uid,'group':uid.split('__')[0],'n_old':len(old_prog),'n_typed':len(rules),
          'old':pred_old,'typed':pred_typed,'fallback':pred_old if pred_old is not None else pred_typed,
          'ast':best,'old_wall_s':old_t,'typed_wall_s':typed_t})
        if len(rows)%40==0: print('PREGRADE',len(rows),'coverage',sum(r['n_old']>0 for r in rows),sum(r['n_typed']>0 for r in rows),flush=True)
    assert len({r['id'] for r in rows})==160
    out={'schema':'Q0_CONCEPTARC_SOURCE_UNOPENED160.v1','n':160,'test_grids':480,'labels_seen':False,
         'neural_calls':0,'frozen_same_ARC2_typed_AST':True,'wall_s':time.perf_counter()-start,'rows':rows}
    blob=(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n').encode()
    dest=pathlib.Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(blob)
    print('PRE_GRADE_IMMUTABLE_SHA256',hashlib.sha256(blob).hexdigest(),'runtime',out['wall_s'],flush=True)
if __name__=='__main__':main()
