#!/usr/bin/env python3
"""Strict after-grade only bounded partial-output and paired CPU-work accounting.

Decision: output inner cells only, mask the maximum tested radius (3) at ends.
This is a heuristic selective output, NOT a universal certificate unless true
system's one-step local-radius<=3 membership is independently justified.
"""
import argparse,collections,hashlib,json,pathlib,statistics
SPLITS=('test_interpolation','test_extrapolation')
METHODS=('legacy','halo','halo_cv')

def main():
 p=argparse.ArgumentParser();p.add_argument('--before',required=True);p.add_argument('--original-dir',required=True);p.add_argument('--out',required=True)
 a=p.parse_args();before_path=pathlib.Path(a.before);d=json.loads(before_path.read_text())
 assert d['n']==2000 and not d['sees_original_truth'] and not d['sees_metadata']
 results={}
 for split in SPLITS:
    totals={m:collections.Counter() for m in METHODS}
    elapsed={m:[] for m in METHODS}
    allsource=list((pathlib.Path(a.original_dir)/(split+'.jsonl')).read_text().splitlines());assert len(allsource)==1000
    for line in allsource:
        true=json.loads(line)
        row=d['rows'][split][true['id']]
        expected=true['solution'];n=len(expected)
        data={'legacy':row['legacy'],'halo':row['halo'],'halo_cv':row['halo'].get('cv',{})}
        for method,record in data.items():
            ct=totals[method]
            pred=record.get('prediction')
            if method!='halo_cv':
                elapsed[method].append(float(record.get('s',0)))
            ct['tasks_total']+=1
            ct['total_query_cells']+=n
            if pred is None:continue
            assert len(pred)==n
            ct['attempted_full_tasks']+=1
            ct['whole_exact']+=int(pred==expected)
            ct['whole_wrong']+=int(pred!=expected)
            # Conservative max radius3: no assumption that the cropped
            # training segment is itself periodic; original labels are unseen
            # until THIS evaluation job.
            lo=3;hi=max(lo,n-3)
            if lo>=hi:
                ct['no_interior_cells']+=1;continue
            pred_part=pred[lo:hi];expected_part=expected[lo:hi]
            ct['interior_reported_cells']+=len(pred_part)
            ct['interior_exact_cells']+=sum(int(x==y) for x,y in zip(pred_part,expected_part))
            ct['interior_wrong_cells']+=sum(int(x!=y) for x,y in zip(pred_part,expected_part))
            ct['tasks_all_reported_interior_correct']+=int(pred_part==expected_part)
            ct['tasks_any_interior_error']+=int(pred_part!=expected_part)
    times={m:{"sum_source_solver_instrumented_s":sum(elapsed[m]),
              "mean_source_call_s":statistics.mean(elapsed[m]) if elapsed[m] else None,
              "count_source_calls":len(elapsed[m])} for m in METHODS}
    result={m:dict(ct) for m,ct in totals.items()}
    result['cpu_source_instrumentation']=times
    # Instrumentation timestamps are one pass only, not a statistically
    # replicated whole-pipeline comparison.
    correct0=totals['legacy']['whole_exact'];correct1=totals['halo']['whole_exact']
    t0=times['legacy']['sum_source_solver_instrumented_s'];t1=times['halo']['sum_source_solver_instrumented_s']
    result['diagnostic_useful_solves_per_sum_source_solver_s']={
       "legacy":correct0/t0 if t0>0 else None,
       "halo":correct1/t1 if t1>0 else None,
       "ratio_halo_to_legacy":(correct1/t1)/(correct0/t0) if t0>0 and t1>0 and correct0>0 else None}
    results[split]=result
    print('PARTIAL_CELLS_AND_CPU_SOURCE_COST',split,json.dumps(result,sort_keys=True),flush=True)
 out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
 report={'schema':'NEUMANN_CELLARC2000_PARTIAL_DEGRADED_MODE_CPU_ACCOUNTING.v1',
         'n':2000,'grids_have_masked_output_edge_cells':True,'excluded_edge_cells_per_side':3,
         'postgrade_only':True,'input_model_target_blind_sha256':hashlib.sha256(before_path.read_bytes()).hexdigest(),
         'true_class_not_available_in_deployment':True,
         'partial_output_does_not_prove_correctness_of_unknown_CA_family':True,
         'elapsed_excludes_dataset_download_and_separate_grader':True,
         'not_end_to_end_10x':True,'results':results}
 out.write_text(json.dumps(report,sort_keys=True,separators=(',',':'))+'\n')
 print('PARTIAL_COST_VERDICT_SHA256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
