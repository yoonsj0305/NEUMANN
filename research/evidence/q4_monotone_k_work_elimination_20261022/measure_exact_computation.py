#!/usr/bin/env python3
"""Paired, no-cheating source-matched lower-certificate work comparison.
Common setup: exact source-only automatic upper candidate synthesis; independent
original 3VC check for minimal upper K. Both arms get the SAME certified upper;
naive reruns EVERY k from 1..n-1; adaptive tests ONLY k=K-1 and uses projection
hierarchy monotonicity to infer all smaller k. No model training.
"""
import argparse,hashlib,json,pathlib,subprocess,sys,time,statistics

def run_cmd(cmd):
 t=time.perf_counter();p=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
 return p,time.perf_counter()-t

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source-dir',type=pathlib.Path,required=True);ap.add_argument('--upper-k',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True)
 ap.add_argument('--baseline',type=pathlib.Path,required=True);ap.add_argument('--optimized',type=pathlib.Path,required=True)
 ap.add_argument('--repetitions',type=int,default=7);ap.add_argument('--cvc5',action='store_true')
 a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 upper=json.loads(a.upper_k.read_text());expected=upper['proven_upper_k'];assert len(expected)==4
 rows=[]
 for i in range(a.repetitions):
  for arm in (('baseline','adaptive') if i%2==0 else ('adaptive','baseline')):
   filename=a.out/f'{arm}_{i:02d}.json';smt=a.out/f'smt_{arm}_{i:02d}';smt.mkdir(exist_ok=True)
   cmd=[sys.executable,str(a.baseline if arm=='baseline' else a.optimized),'--source-dir',str(a.source_dir),'--out',str(filename),'--smt-out',str(smt)]
   if arm=='adaptive':cmd+=['--target-k-map',str(a.upper_k)]
   if a.cvc5:cmd.append('--cvc5')
   p,secs=run_cmd(cmd)
   (a.out/f'{arm}_{i:02d}.log').write_text(p.stdout+'\nSTDERR\n'+p.stderr)
   if p.returncode:raise RuntimeError(f'FAILED_{arm}_{i}: '+p.stdout[-800:]+p.stderr[-800:])
   d=json.loads(filename.read_text());verified={c['original_sha']:c['necessary_support_at_least'] for c in d['certified'].values()}
   actual={name:r['necessary_support_at_least'] for name,r in d['certified'].items()}
   assert actual==expected,(arm,actual,expected)
   assert d['query_count_verified']==d['totals']['sat_verified_queries']
   for r in d['certified'].values():
    k=expected[[key for key,v in d['certified'].items() if v is r][0]]-1
    assert r['witnesses_by_k'].get(str(k)) is not None
   row={'round':i,'arm':arm,'wall_s':secs,'engine_wall_s':d['wall_time_s'],'verified_original_smt_queries':d['query_count_verified'],
   'generator_sat_queries':d['totals']['generator_sat_queries'],'generator_unsat_queries':d['totals']['generator_unsat_queries'],
   'generator_queries':d['totals']['generator_sat_queries']+d['totals']['generator_unsat_queries'],
   'total_z3_queries_including_final_model_and_independent_rechecks':d['totals']['generator_sat_queries']*2+d['totals']['generator_unsat_queries']+d['query_count_verified'],
   'original_result_sha256':hashlib.sha256(filename.read_bytes()).hexdigest(),'fully_correct_upper_and_lower':True}
   rows.append(row);print('PAIRED_Q4',row,flush=True)
 summary={}
 for arm in ('baseline','adaptive'):
  subset=[r for r in rows if r['arm']==arm]
  summary[arm]={'rounds':len(subset),'median_wall_s':round(statistics.median(r['wall_s'] for r in subset),5),'median_engine_wall_s':round(statistics.median(r['engine_wall_s'] for r in subset),5),
  'rechecked_original_smt_queries':subset[0]['verified_original_smt_queries'],'generator_queries':subset[0]['generator_queries'],
  'total_z3_calls':subset[0]['total_z3_queries_including_final_model_and_independent_rechecks']}
  assert len({r['generator_queries'] for r in subset})==1
  assert len({r['verified_original_smt_queries'] for r in subset})==1
 ratio=summary['baseline']['median_wall_s']/summary['adaptive']['median_wall_s']
 o={'schema':'NEUMANN.Q4.frozen_pairwise_no_training_source_exact_cost.v1','upper_k_admission_sha256':hashlib.sha256(a.upper_k.read_bytes()).hexdigest(),
    'same_original_safety_results':expected,'upper_k_original_3vc_preprocess_queries':upper['z3_original_vc_queries'],
    'upper_k_original_3vc_preprocess_wall_s':upper['wall_s'],
    'paired_trials':rows,'summary':summary,'lower_only_median_speedup':round(ratio,3),
    'fraction_original_recheck_calls_deleted':round(1-summary['adaptive']['rechecked_original_smt_queries']/summary['baseline']['rechecked_original_smt_queries'],4),
    'no_training':True,'scope':'Four already opened genuine SyGuS sources; lower-bound proof-certificate cost only; full training/upper-generation/guidance excluded from lower-only speedups; budget-limited search, exact source checks'}
 (a.out/'COST_COMPARISON.json').write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')
 print('NEUMANN_Q4_COST_COMPARISON',json.dumps({'median_baseline_wall_s':summary['baseline']['median_wall_s'],'median_adaptive_wall_s':summary['adaptive']['median_wall_s'],'lower_only_speedup':ratio,'queries':{x:summary[x]['total_z3_calls'] for x in summary}}),flush=True)
if __name__=='__main__':main()
