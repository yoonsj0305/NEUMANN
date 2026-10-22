#!/usr/bin/env python3
"""One-shot preregistered CellARC val1000; frozen source model, separate original grading."""
import argparse,collections,hashlib,json,pathlib,time
from debruijn_structural_model import infer
def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=('infer','grade'),required=True)
    p.add_argument('--input');p.add_argument('--source');p.add_argument('--sealed');p.add_argument('--out',required=True)
    a=p.parse_args()
    if a.mode=='infer':
        rows={};ct=collections.Counter();start=time.perf_counter()
        for line in pathlib.Path(a.input).read_text().splitlines():
            d=json.loads(line)
            assert 'solution' not in d and 'meta' not in d and 'program' not in d
            uid=d['id'];assert uid not in rows
            output=infer(d)
            rows[uid]=output;ct[output['status']]+=1
        assert len(rows)==1000
        data={'schema':'NEUMANN_FIRST_FROZEN_CELLARC_VAL1000_BEFORE_TRUTH.v1',
              'source_only':True,'n':1000,'hidden_meta_accessed':False,
              'model_parameters_changed_since_cellarc_test2000':False,
              'pregrade_counts':dict(ct),'source_solver_wall_s':time.perf_counter()-start,'rows':rows}
        print('FIRST_UNTOUCHED_VAL1000_INFERENCE',json.dumps(data['pregrade_counts'],sort_keys=True),flush=True)
    else:
        frozen=pathlib.Path(a.sealed);prior=json.loads(frozen.read_text())
        assert prior['n']==1000 and prior['source_only'] and not prior['hidden_meta_accessed']
        scores=collections.Counter();rows={}
        for line in pathlib.Path(a.source).read_text().splitlines():
            d=json.loads(line);z=prior['rows'][d['id']]
            prediction=z['prediction'];match=bool(prediction is not None and prediction==d['solution'])
            scores['total']+=1;scores['attempted']+=int(prediction is not None)
            scores['correct']+=int(match);scores['wrong']+=int(prediction is not None and not match)
            scores['source_structure_unique']+=int(z['status'] in ('NO_UNIQUE_PREDICTION','SOURCE_INDUCED_CYCLE_PREDICTION'))
            rows[d['id']]={'status':z['status'],'correct':match}
        assert scores['total']==1000 and len(rows)==1000
        data={'schema':'NEUMANN_FIRST_FROZEN_CELLARC_VAL1000_INDEPENDENT_TRUTH.v1',
              'n':1000,'scores':dict(scores),'rows':rows,
              'sealed_original_predictions_sha256':hashlib.sha256(frozen.read_bytes()).hexdigest(),
              'true_fresh_pre_registered_relative_to_this_project':True,
              'global_frontier_q3':'OPEN','global_frontier_q4':'OPEN'}
        print('FIRST_UNTOUCHED_VAL1000_INDEPENDENT_GRADE',json.dumps(dict(scores),sort_keys=True),flush=True)
    out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,sort_keys=True,separators=(',',':'))+'\n')
    print('FIRST_VAL1000_RECEIPT_SHA256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
