#!/usr/bin/env python3
"""Independent after-prediction source-demo labels scorer; no ARC target tests."""
import argparse,collections,hashlib,json,pathlib
def main():
 p=argparse.ArgumentParser();p.add_argument('--sealed',required=True)
 p.add_argument('--concept-original',required=True);p.add_argument('--arc-original',required=True)
 p.add_argument('--out',required=True);a=p.parse_args()
 s=pathlib.Path(a.sealed);pred=json.loads(s.read_text())
 assert not pred['leftout_original_demo_outputs_given_to_trainer']
 roots={'conceptarc160':pathlib.Path(a.concept_original),'arc2train200':pathlib.Path(a.arc_original)}
 totals={};truth_records={}
 for cohort,rows in pred['rows'].items():
    score=collections.Counter();rr={}
    for uid,row in sorted(rows.items()):
        if cohort=='conceptarc160':
            group,taskname=uid.split('__',1)
            src=roots[cohort]/group/(taskname+'.json')
        else:src=roots[cohort]/(uid+'.json')
        d=json.loads(src.read_text());demos=d['train']
        assert len(row['folds'])==len(demos)
        outcomes=[]
        for fold in row['folds']:
            i=fold['fold'];assert 0<=i<len(demos)
            correct=fold['prediction'] is not None and fold['prediction']==demos[i]['output']
            score['total_demo_folds']+=1;score['eligible_folds']+=int(fold['eligible'])
            score['attempted_folds']+=int(fold['prediction'] is not None)
            score['correct_folds']+=int(correct)
            if fold['eligible']:
                score['eligible_attempted']+=int(fold['prediction'] is not None)
                score['eligible_correct']+=int(correct)
            outcomes.append({'fold':i,'eligible':fold['eligible'],'status':fold['status'],'correct':correct})
        qualifies=len(demos)>=3
        score['tasks']+=1;score['tasks_with_eligible_LOODO']+=int(qualifies)
        if qualifies:
            score['tasks_all_folds_correct']+=int(all(x['correct'] for x in outcomes))
        rr[uid]={'demos':len(demos),'outcomes':outcomes}
        print('TRUE_DEMO_CV_GRADING',cohort,uid,repr([x['correct'] for x in outcomes]),flush=True)
    totals[cohort]=dict(score);truth_records[cohort]=rr
 result={'schema':'NEUMANN_Q3_ORIGINAL_LEAVE_ONE_DEMO_OUT_POST_GRADE.v1',
         'source_test_grid_labels_used':False,'pregrade_sha256':hashlib.sha256(s.read_bytes()).hexdigest(),
         'counts':totals,'rows':truth_records,
         'scope':'posthoc source CV on previously graded 11 real learned programs; not pristine test transfer',
         'global_frontier_Q3':'OPEN'}
 out=pathlib.Path(a.out);out.parent.mkdir(exist_ok=True,parents=True)
 out.write_text(json.dumps(result,sort_keys=True)+'\n')
 print('ORIGINAL_DEMO_CV_SUMMARY',json.dumps(totals,sort_keys=True),
       'sha256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
