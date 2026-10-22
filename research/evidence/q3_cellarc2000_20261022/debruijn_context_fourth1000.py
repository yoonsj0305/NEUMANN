"""First evaluation original CellARC train indices 3001-4000: old vs source alphabet vs global context."""
import argparse,collections,hashlib,json,pathlib,time
from debruijn_full_context import infer_aligned
from debruijn_observed_output_support_fresh1000 import compare

def source_proposals(task):
    structural=infer_aligned(task)
    alphabet=compare(task)['symbol_guarded']
    return {'old':structural['original'],'alphabet':alphabet,'aligned':structural['aligned']}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=('infer','grade'),required=True)
    p.add_argument('--input');p.add_argument('--source');p.add_argument('--sealed');p.add_argument('--out',required=True)
    a=p.parse_args();names=('old','alphabet','aligned')
    if a.mode=='infer':
        result={};counters=collections.Counter();start=time.perf_counter()
        for line in pathlib.Path(a.input).read_text().splitlines():
            task=json.loads(line);uid=task['id']
            assert uid not in result and 'solution' not in task and 'meta' not in task and 'program' not in task
            z=source_proposals(task);result[uid]=z
            for name in names:
                counters[name+':'+z[name]['status']]+=1
                counters[name+':attempted']+=int(z[name].get('prediction') is not None)
        assert len(result)==1000
        d={'schema':'NEUMANN_CA_CANONICAL_BOUNDARY_SOURCE_ONLY_FOURTH1000.v1',
          'n':1000,'target_truth_seen':False,'oracle_meta_seen':False,
          'input_original_lines':'train.jsonl 3001-4000',
          'assumed_known_prior':'public generator canonical de Bruijn cycle only',
          'model_classes_trained_on_val_labels':False,
          'inference_wall_s':time.perf_counter()-start,'counts':dict(counters),'rows':result}
        print('FOURTH1000_SOURCE_ONLY_MODEL_COUNTS',json.dumps(dict(counters),sort_keys=True),flush=True)
    else:
        before=pathlib.Path(a.sealed);pregen=json.loads(before.read_text())
        assert pregen['n']==1000 and not pregen['target_truth_seen'] and not pregen['oracle_meta_seen']
        totals=collections.Counter();rows={}
        for line in pathlib.Path(a.source).read_text().splitlines():
            obj=json.loads(line);uid=obj['id'];pred=pregen['rows'][uid]
            row={}
            for name in names:
                v=pred[name].get('prediction')
                ok=v is not None and v==obj['solution']
                totals[name+':attempted']+=int(v is not None)
                totals[name+':exact']+=int(ok)
                totals[name+':wrong']+=int(v is not None and not ok)
                row[name]={'attempted':v is not None,'exact':bool(ok)}
            totals['originals']+=1
            totals['aligned_new_exact_vs_old']+=int(row['aligned']['exact'] and not row['old']['exact'])
            totals['aligned_lost_prior_exact']+=int(not row['aligned']['exact'] and row['old']['exact'])
            rows[uid]=row
        assert totals['originals']==len(rows)==1000
        d={'schema':'NEUMANN_CA_CANONICAL_FULL_SOURCE_CONTEXT_ORIGINAL_FOURTH1000_GRADE.v1',
           'n':1000,'first_source_pregrade_sha256':hashlib.sha256(before.read_bytes()).hexdigest(),
           'metrics':dict(totals),'per_task':rows,'global_q3_neural_discovery':'OPEN',
           'global_q4_total_cost_10x':'OPEN','true_process_class_automatically_proved':False}
        print('INDEPENDENT_REAL_FOURTH1000_CANONICAL_CONTEXT_GRADE',json.dumps(dict(totals),sort_keys=True),flush=True)
    file=pathlib.Path(a.out);file.parent.mkdir(exist_ok=True,parents=True)
    file.write_text(json.dumps(d,separators=(',',':'),sort_keys=True)+'\n')
    print('FOURTH1000_MODEL_RECEIPT_SHA256',hashlib.sha256(file.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
