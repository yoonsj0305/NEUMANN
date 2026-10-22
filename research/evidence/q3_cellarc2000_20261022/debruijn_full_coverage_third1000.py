"""First untouched original train lines 2001..3000: three frozen source-only policies."""
import argparse,collections,hashlib,json,pathlib
from debruijn_observed_output_support_fresh1000 import compare
def three(d):
    z=compare(d);base=z['symbol_guarded'];guard=dict(base)
    if guard.get('prediction') is not None and 'full' not in guard.get('compatible_model_families',[]):
        guard={'status':'ABSTAIN_UNSEEN_FULL_EFFECTIVE_NEIGHBORHOOD',
             'prediction':None,'original_structural_model':guard.get('structural_model')}
    z['full_observation_guarded']=guard
    return z
def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['infer','grade'],required=True)
    p.add_argument('--input');p.add_argument('--source');p.add_argument('--sealed');p.add_argument('--out',required=True)
    a=p.parse_args();names=('old','symbol_guarded','full_observation_guarded')
    if a.mode=='infer':
        rows={};counts=collections.Counter()
        for line in pathlib.Path(a.input).read_text().splitlines():
            d=json.loads(line)
            assert 'solution' not in d and 'meta' not in d and 'program' not in d and d['id'] not in rows
            r=three(d);rows[d['id']]=r
            for mode in names:counts[mode+':'+r[mode]['status']]+=1
        assert len(rows)==1000
        record={'schema':'NEUMANN_DEBRUIJN_THIRD_UNSEEN_TRAIN1000_SOURCE_ONLY.v1',
          'n':1000,'original_true_query_labels_available':False,
          'hidden_source_meta_available':False,'three_models_before_grade':dict(counts),'rows':rows}
        print('FROZEN_THIRD_TRAIN1000_ALL_UNGRADED',json.dumps(dict(counts),sort_keys=True),flush=True)
    else:
        f=pathlib.Path(a.sealed);d=json.loads(f.read_text())
        assert d['n']==1000 and not d['original_true_query_labels_available']
        ctr=collections.Counter();audit={}
        for line in pathlib.Path(a.source).read_text().splitlines():
            z=json.loads(line);pred=d['rows'][z['id']];q={}
            for mode in names:
                p=pred[mode].get('prediction')
                correct=p is not None and p==z['solution'];q[mode]=correct
                ctr[mode+'_attempted']+=int(p is not None)
                ctr[mode+'_correct']+=int(correct)
                ctr[mode+'_wrong']+=int(p is not None and not correct)
            ctr['n']+=1;audit[z['id']]=q
            if pred['symbol_guarded'].get('prediction') is not None and pred['full_observation_guarded']['prediction'] is None:
                ctr['full_guard_rejected_predictions']+=1
                ctr['full_guard_rejected_right']+=int(q['symbol_guarded'])
                ctr['full_guard_rejected_wrong']+=int(not q['symbol_guarded'])
        assert ctr['n']==len(audit)==1000
        record={'schema':'NEUMANN_THIRD_FRESH_TRAIN1000_INDEPENDENT_FULL_COVERAGE.v1','n':1000,
            'counts':dict(ctr),'rows':audit,
            'pregrade_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),
            'oracle_metadata_never_used_to_choose_model':True,
            'claims':'postulated original finite effective t-step neighborhood model; global Q3/Q4 OPEN'}
        print('INDEPENDENT_THIRD_TRAIN1000_THREE_MODEL_GRADE',json.dumps(dict(ctr),sort_keys=True),flush=True)
    out=pathlib.Path(a.out);out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps(record,sort_keys=True,separators=(',',':'))+'\n')
    print('THIRD_FRESH1000_EVIDENCE_SHA256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
