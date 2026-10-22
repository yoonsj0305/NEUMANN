"""Identical frozen original 1k source task baseline vs indexed whole solver cost.
No solution/metadata ever fetched. Paired 5 passes alternating order, exact
predictions and all abstention semantics must match at every task and pass.
"""
import argparse,collections,hashlib,json,pathlib,statistics,time,sys
BASE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(BASE.parent/'q3_cellarc2000_20261022'))
from indexed_cycle import infer_indexed,equivalence_theorem_exhaustive,index
import debruijn_structural_model as original

def all_source_tasks(path):
    tasks=[]
    for line in pathlib.Path(path).read_text().splitlines():
        d=json.loads(line)
        assert 'solution' not in d and 'meta' not in d and 'program' not in d
        tasks.append(d)
    assert len(tasks)==1000
    return tasks

def run_batch(tasks,use_indexed):
    f=infer_indexed if use_indexed else original.infer
    t=time.perf_counter_ns();cpu=time.process_time_ns()
    outputs=[f(d) for d in tasks]
    end=time.perf_counter_ns();ecpu=time.process_time_ns()
    return outputs,{"wall_ns":end-t,"cpu_ns":ecpu-cpu}

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();tasks=all_source_tasks(a.input)
    exhaustive=equivalence_theorem_exhaustive()
    # Warm caches with TRUE INPUTS ONLY; zero hidden answers.
    _=original.infer(tasks[0]);_=infer_indexed(tasks[0])
    records={'baseline':[],'indexed':[]}
    checksum={}
    for trial in range(5):
        order=('baseline','indexed') if trial%2==0 else ('indexed','baseline')
        results={}
        for model in order:
            outputs,cost=run_batch(tasks,model=='indexed')
            results[model]=outputs
            records[model].append(cost)
        mismatch=[tasks[i]['id'] for i,(x,y) in enumerate(zip(results['baseline'],results['indexed'])) if x!=y]
        assert not mismatch,(trial,mismatch[:8])
        raw=json.dumps(results['baseline'],sort_keys=True,separators=(',',':')).encode()
        checksum[str(trial)]=hashlib.sha256(raw).hexdigest()
        print('FULL_SOURCE_SOLVER_EQUALITY',trial,'PASS','baseline_wall_ns',records['baseline'][-1]['wall_ns'],
              'indexed_wall_ns',records['indexed'][-1]['wall_ns'],flush=True)
    before=[v['wall_ns']/1e9 for v in records['baseline']]
    after=[v['wall_ns']/1e9 for v in records['indexed']]
    cpu_before=[v['cpu_ns']/1e9 for v in records['baseline']]
    cpu_after=[v['cpu_ns']/1e9 for v in records['indexed']]
    ratio=statistics.median(before)/statistics.median(after)
    cpu_ratio=statistics.median(cpu_before)/statistics.median(cpu_after)
    results={'schema':'NEUMANN_Q4_EXACT_DEBRUIJN_FULL_SOURCE_SOLVER_1000.v1','n':1000,
         'task_input_only':True,'no_original_output_test_targets_seen':True,
         'no_hidden_metadata_seen':True,
         'full_ast_result_identical_for_each_trial':True,'repeats':5,
         'exhaustive_short_k_gram_membership_comparisons':exhaustive,
         'median_baseline_wall_s':statistics.median(before),'median_indexed_wall_s':statistics.median(after),
         'median_baseline_cpu_s':statistics.median(cpu_before),'median_indexed_cpu_s':statistics.median(cpu_after),
         'wall_speedup':ratio,'cpu_speedup':cpu_ratio,
         'model_source_commit_identity':'fb12bc217178f7f3e89f0865987078e5dc367074',
         'all_solver_predictions_SHA_by_run':checksum,'raw_timing':records,
         'full_neumann_end_to_end_compute_speedup_proven':False,
         'excluded_from_timing':['dataset download','Python interpreter startup','validation labels','grading','future online training','GPU/energy']}
    dest=pathlib.Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(results,sort_keys=True)+'\n')
    print('Q4_EXACT_WHOLE_SOURCE_FULL_SOLVER_SPEED',json.dumps({
       'n':1000,'all_output_equal':True,'exhaustive_patterns':exhaustive,
       'baseline_median_s':results['median_baseline_wall_s'],
       'indexed_median_s':results['median_indexed_wall_s'],
       'wall_speedup':ratio,'cpu_speedup':cpu_ratio},sort_keys=True),flush=True)
    print('Q4_SHA256',hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
