"""Source-observed training output alphabet lower bound, without any held-out targets."""
import argparse,collections,hashlib,json,pathlib
from debruijn_structural_model import infer
def compare(d):
    old=infer(d)
    guarded=dict(old)
    info=old.get('structural_model')
    observed=[z for p in d['train'] for z in p['output']]
    if not observed:raise ValueError('source output missing')
    minimum_k=max(observed)+1
    if info is not None and int(info['k'])<minimum_k:
        guarded={'status':'ABSTAIN_ALPHABET_EXCLUDES_OBSERVED_OUTPUT',
                 'source_observed_min_alphabet':minimum_k,
                 'rejected_candidate_k':info['k'],'prediction':None}
    return {'old':old,'symbol_guarded':guarded}

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=('infer','grade'),required=True)
    p.add_argument('--input');p.add_argument('--source');p.add_argument('--sealed');p.add_argument('--out',required=True)
    a=p.parse_args()
    if a.mode=='infer':
        rows={};counts=collections.Counter()
        for line in pathlib.Path(a.input).read_text().splitlines():
            t=json.loads(line);assert 'solution' not in t and 'meta' not in t and 'program' not in t
            assert t['id'] not in rows
            val=compare(t);rows[t['id']]=val
            for k in ('old','symbol_guarded'):counts[k+'/'+val[k]['status']]+=1
        assert len(rows)==1000
        data={'schema':'NEUMANN_CELLARC_SOURCE_SYMBOL_FRESH_TRAIN1000_BEFORE_GRADE.v1',
            'n':1000,'source_only':True,'source_observed_output_contract':True,
            'original_model_blob':'fb12bc217178f7f3e89f0865987078e5dc367074',
            'test_solution_seen':False,'hidden_generator_meta_seen':False,
            'rows':rows,'counts':dict(counts)}
        print('FIRST_SOURCE_TRAIN1000_BEFORE_GRADE',json.dumps(dict(counts),sort_keys=True),flush=True)
    else:
        prefile=pathlib.Path(a.sealed);data=json.loads(prefile.read_text())
        assert data['n']==1000 and data['source_only'] and not data['test_solution_seen']
        ctr=collections.Counter();rows={}
        for line in pathlib.Path(a.source).read_text().splitlines():
            task=json.loads(line);guess=data['rows'][task['id']]
            result={}
            for label in ('old','symbol_guarded'):
                p=guess[label]['prediction'];exact=p is not None and p==task['solution']
                result[label]=bool(exact)
                ctr[label+'_attempted']+=int(p is not None)
                ctr[label+'_correct']+=int(exact)
                ctr[label+'_wrong']+=int(p is not None and not exact)
            ctr['total_originals']+=1
            ctr['guard_rejected_predictions']+=int(guess['old']['prediction'] is not None and guess['symbol_guarded']['prediction'] is None)
            ctr['guard_rejected_old_wrong']+=int(guess['old']['prediction'] is not None and not result['old'] and guess['symbol_guarded']['prediction'] is None)
            ctr['guard_rejected_old_right']+=int(result['old'] and guess['symbol_guarded']['prediction'] is None)
            rows[task['id']]=result
        assert ctr['total_originals']==len(rows)==1000
        data={'schema':'NEUMANN_CELLARC_FIRST_TRAIN1000_SYMBOL_GUARD_INDEPENDENT_GRADE.v1',
              'n':1000,'originals':dict(ctr),'rows':rows,
              'frozen_prediction_sha256':hashlib.sha256(prefile.read_bytes()).hexdigest(),
              'metadata_not_used_by_either_model':True,
              'no_global_frontier_performance_claim':True}
        print('FIRST_TRAIN1000_REAL_SYMBOL_ABLATION',json.dumps(dict(ctr),sort_keys=True),flush=True)
    o=pathlib.Path(a.out);o.parent.mkdir(parents=True,exist_ok=True)
    o.write_text(json.dumps(data,sort_keys=True,separators=(',',':'))+'\n')
    print('FRESH_TRAIN1000_EVIDENCE_SHA256',hashlib.sha256(o.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
