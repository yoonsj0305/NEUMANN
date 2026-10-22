"""Two-stage CellARC original 2000 prediction sealing + independent scoring."""
import argparse,collections,hashlib,json,pathlib,time
from debruijn_structural_model import infer

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',choices=('infer','grade'),required=True)
    parser.add_argument('--input-dir');parser.add_argument('--source-dir');parser.add_argument('--sealed');parser.add_argument('--out',required=True)
    a=parser.parse_args();start=time.perf_counter()
    if a.mode=='infer':
        reports={};statistics={}
        for split in ('test_interpolation','test_extrapolation'):
            rows={};counts=collections.Counter()
            for line in (pathlib.Path(a.input_dir)/(split+'.jsonl')).read_text().splitlines():
                record=json.loads(line)
                assert 'solution' not in record and 'meta' not in record and 'program' not in record
                ident=record['id'];assert ident not in rows
                z=infer(record)
                rows[ident]=z;counts[z['status']]+=1
            assert len(rows)==1000
            reports[split]=rows;statistics[split]=dict(counts)
            print('BLIND_SOURCE_GENERATIVE_STRUCTURE',split,json.dumps(dict(counts),sort_keys=True),flush=True)
        result={'schema':'NEUMANN_CELLARC_DEBRUIJN_SOURCE_ONLY.v1','n':2000,
                'test_truth_seen':False,'hidden_metadata_seen':False,
                'models':reports,'source_structure_counts':statistics,'elapsed_s':time.perf_counter()-start}
    else:
        original=pathlib.Path(a.sealed);before=json.loads(original.read_text())
        assert before['n']==2000 and not before['test_truth_seen'] and not before['hidden_metadata_seen']
        scores={};details={}
        for split in ('test_interpolation','test_extrapolation'):
            totals=collections.Counter();rows={}
            for line in (pathlib.Path(a.source_dir)/(split+'.jsonl')).read_text().splitlines():
                d=json.loads(line);z=before['models'][split][d['id']]
                prediction=z.get('prediction');right=prediction is not None and prediction==d['solution']
                totals['n']+=1;totals['attempted']+=int(prediction is not None)
                totals['correct']+=int(right);totals['wrong']+=int(prediction is not None and not right)
                totals['unique_source_structure']+=int(z['status'] in ('SOURCE_INDUCED_CYCLE_PREDICTION','NO_UNIQUE_PREDICTION'))
                rows[d['id']]={'status':z['status'],'exact':bool(right)}
            assert len(rows)==1000
            scores[split]=dict(totals);details[split]=rows
            print('INDEPENDENT_ORIGINAL_GENERATIVE_SOLVE',split,json.dumps(dict(totals),sort_keys=True),flush=True)
        result={'schema':'NEUMANN_CELLARC_DEBRUIJN_INDEPENDENT_2000.v1',
                'n':2000,'exact_pregrade_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),
                'scores':scores,'details':details,'no_neural_model_training':True,
                'q3_novel_autonomous_primitive':'NOT_PROVED','global_q4_10x':'OPEN'}
    dst=pathlib.Path(a.out);dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n')
    print('CELLARC_GENERATOR_RECEIPT_SHA256',hashlib.sha256(dst.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
