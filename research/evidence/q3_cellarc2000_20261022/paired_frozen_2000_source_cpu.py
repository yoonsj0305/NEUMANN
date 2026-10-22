"""Paired frozen full-program original CellARC2000 CPU timing and independent exact grading.

Runs OLD frozen debruijn_structural_model.infer against NEW frozen
debruijn_full_context.infer_aligned()['aligned']; new path includes its
actual internal OLD call. Five alternating full 2000-task passes, plus warmup.
No target labels in timed environment. Same CPU runner, source objects,
Python, queries. This is whole Q3 proposal-stage CPU cost, NOT NEUMANN global
training/orchestration, or energy usage.
"""
import argparse,collections,hashlib,json,pathlib,statistics,time
from debruijn_structural_model import infer as old_infer
from debruijn_full_context import infer_aligned

def predict(task,name):
    if name=='old':return old_infer(task).get('prediction')
    if name=='aligned':return infer_aligned(task)['aligned'].get('prediction')
    raise ValueError(name)

def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['benchmark','grade'],required=True)
    p.add_argument('--masked');p.add_argument('--original-fourth');p.add_argument('--original-fifth')
    p.add_argument('--sealed');p.add_argument('--out',required=True)
    a=p.parse_args()
    if a.mode=='benchmark':
        tasks=[json.loads(x) for x in pathlib.Path(a.masked).read_text().splitlines()]
        assert len(tasks)==2000
        ids=[x['id'] for x in tasks];assert len(set(ids))==2000
        for d in tasks:
            assert 'solution' not in d and 'meta' not in d and 'program' not in d
        for d in tasks[:32]:
            predict(d,'old');predict(d,'aligned')
        alltimes={name:[] for name in ('old','aligned')}
        wall={name:[] for name in ('old','aligned')}
        reference={}
        for n in range(5):
            order=('old','aligned') if n%2==0 else ('aligned','old')
            for name in order:
                cpu_start=time.process_time_ns();w_start=time.perf_counter_ns()
                preds={t['id']:predict(t,name) for t in tasks}
                cpu_ns=time.process_time_ns()-cpu_start
                wall_ns=time.perf_counter_ns()-w_start
                digest=hashlib.sha256(json.dumps(preds,sort_keys=True,separators=(',',':')).encode()).hexdigest()
                if name in reference:
                    assert digest==reference[name]['prediction_sha256'],(name,n)
                else:
                    reference[name]={'prediction_sha256':digest,'predictions':preds}
                alltimes[name].append(cpu_ns/1e9)
                wall[name].append(wall_ns/1e9)
                print('PAIRED_CPU_ORIGINAL_SOURCE',json.dumps({'model':name,'rep':n,
                      'process_cpu_s':cpu_ns/1e9,'wall_s':wall_ns/1e9,'sha':digest},sort_keys=True),flush=True)
        result={'schema':'NEUMANN_CELLARC2000_FROZEN_PAIRED_Q3_SOURCE_CPU.v1',
           'n':2000,'source_target_labels_seen':False,'hidden_meta_seen':False,
           'no_further_solver_training':True,'five_alternating_full_dataset_runs':True,
           'warming_samples':32,'source_stage_excludes':[
                'dataset_download','external grader','training','GPU','LLM','orchestration'],
           'runtime':{name:{'cpu_s_five':alltimes[name],'wall_s_five':wall[name],
             'cpu_median_s':statistics.median(alltimes[name]),
             'wall_median_s':statistics.median(wall[name])} for name in ('old','aligned')},
           'raw_predictions':reference,
           'source_original_line_ranges':['train.jsonl 3001-4000','train.jsonl 4001-5000']}
    else:
        before=pathlib.Path(a.sealed);r=json.loads(before.read_text())
        assert r['n']==2000 and not r['source_target_labels_seen'] and not r['hidden_meta_seen']
        truths={}
        for path in (a.original_fourth,a.original_fifth):
            lines=pathlib.Path(path).read_text().splitlines()
            assert len(lines)==1000
            for line in lines:
                t=json.loads(line);uid=t['id'];assert uid not in truths
                truths[uid]=t['solution']
        assert len(truths)==2000
        scores={}
        for name in ('old','aligned'):
            predictions=r['raw_predictions'][name]['predictions']
            assert set(predictions)==set(truths)
            correct=sum(x is not None and x==truths[uid] for uid,x in predictions.items())
            attempted=sum(x is not None for x in predictions.values())
            score={'n':2000,'attempted':attempted,'correct':correct,'wrong':attempted-correct,
                   'cpu_median_s':r['runtime'][name]['cpu_median_s'],
                   'wall_median_s':r['runtime'][name]['wall_median_s']}
            score['whole_exact_tasks_per_cpu_second']=correct/score['cpu_median_s']
            score['whole_exact_tasks_per_wall_second']=correct/score['wall_median_s']
            scores[name]=score
        assert scores['old']['correct']==266 and scores['aligned']['correct']==384, scores
        result={'schema':'NEUMANN_CELLARC2000_PAIRED_Q3_SOURCE_ONLY_CPU_INDEPENDENT.v1',
            'n':2000,'source_receipt_sha256':hashlib.sha256(before.read_bytes()).hexdigest(),
            'scores':scores,
            'correct_per_cpu_second_ratio_new_over_old':scores['aligned']['whole_exact_tasks_per_cpu_second']/scores['old']['whole_exact_tasks_per_cpu_second'],
            'cpu_time_ratio_new_over_old':scores['aligned']['cpu_median_s']/scores['old']['cpu_median_s'],
            'source_stage_only':True,'end_to_end_global_Q4_10x':'OPEN'}
        print('PAIRED_REAL_ORIGINAL_CPU_EFFICIENCY',json.dumps(result['scores'],sort_keys=True),flush=True)
        print('PAIRED_Q3_SOURCE_EXACT_PER_CPU_RATIO',result['correct_per_cpu_second_ratio_new_over_old'],flush=True)
    out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,separators=(',',':'),sort_keys=True)+'\n')
    print('PAIRED_Q4_COST_RECEIPT_SHA256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
