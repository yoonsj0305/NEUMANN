#!/usr/bin/env python3
"""Run only in the independent label-bearing job after immutable prediction artifact."""
import argparse, hashlib, json, pathlib, math

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pred',required=True);ap.add_argument('--truth',required=True);ap.add_argument('--out',required=True)
    a=ap.parse_args();pb=pathlib.Path(a.pred).read_bytes();d=json.loads(pb);rows=d['rows']
    assert d['label_free'] and len(rows)==d['n']==120
    statuses=[];truthdir=pathlib.Path(a.truth)
    for x in rows:
        gt=json.loads((truthdir/(x['id']+'.json')).read_text())
        actual=[case['output'] for case in gt['test']]
        candidate={key:(x[key+'_pred'] is not None and x[key+'_pred']==actual) for key in ('old','typed','hybrid')}
        statuses.append({'id':x['id'],**candidate,'old_covered':x['n_legacy']>0,'typed_covered':x['n_typed']>0})
    assert len({x['id'] for x in statuses})==120
    cnt={k:sum(int(x[k]) for x in statuses) for k in ['old','typed','hybrid','old_covered','typed_covered']}
    cnt['typed_new_wins']=sum(x['typed'] and not x['old'] for x in statuses)
    cnt['typed_regressions']=sum(x['old'] and not x['typed'] for x in statuses)
    cnt['hybrid_new_wins']=sum(x['hybrid'] and not x['old'] for x in statuses)
    cnt['hybrid_regressions']=sum(x['old'] and not x['hybrid'] for x in statuses)
    cnt['baseline_total_wall_s']=sum(x['legacy_wall_s'] for x in rows)
    cnt['typed_total_wall_s']=sum(x['typed_wall_s'] for x in rows)
    cnt['added_compute_on_all120_s']=cnt['typed_total_wall_s']
    n=cnt['typed_new_wins']+cnt['typed_regressions'];k=min(cnt['typed_new_wins'],cnt['typed_regressions'])
    cnt['exact_mcnemar_p']=min(1.0,2*sum(math.comb(n,j) for j in range(k+1))/(2**n)) if n else 1.0
    output={'n':120,'evaluated_public120_not_blind_novel_corpus':True,
            'frozen_prediction_sha256':hashlib.sha256(pb).hexdigest(),
            'source_original_evaluation_tree':d['evaluation_tree'],
            'baseline':'prior ARC2 800-developed exact symbolic composer',
            'new':'preexisting typed object AST source-only proposer with semantic memo, NOT trained neural',
            'counts':cnt,'rows':statuses,
            'GLOBAL_FRONTIER_OR_LEARNED_UNIQUE_Q3':'OPEN','Q4_10x_full':'OPEN'}
    p=pathlib.Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print('INDEPENDENT_ARC2_PUBLIC120_TYPED_TRANSFER',json.dumps(cnt,sort_keys=True),'PRED_SHA',output['frozen_prediction_sha256'],flush=True)
if __name__=='__main__':main()
