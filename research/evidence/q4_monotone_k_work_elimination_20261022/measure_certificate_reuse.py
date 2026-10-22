#!/usr/bin/env python3
"""Paired identical ORIGINAL dual-SMT 3VC proof replays of raw and compact certificates.
Charges compaction separately. Does not claim lower total cost without break-even.
"""
import argparse,json,pathlib,subprocess,statistics,sys,time,hashlib

def main():
 p=argparse.ArgumentParser();p.add_argument('--source-dir',type=pathlib.Path,required=True);p.add_argument('--manifest',type=pathlib.Path,required=True);p.add_argument('--original',type=pathlib.Path,required=True);p.add_argument('--compact',type=pathlib.Path,required=True);p.add_argument('--checker',type=pathlib.Path,required=True);p.add_argument('--pruner-evidence',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--pairs',type=int,default=13);p.add_argument('--backend',choices=['dual','z3'],default='dual')
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 i=json.loads(a.original.read_text());j=json.loads(a.compact.read_text());p=json.loads(a.pruner_evidence.read_text())
 assert len(i['cases'])==len(j['cases'])==len(p['cases'])==4
 rows=[]
 for trial in range(a.pairs):
  for arm in (('full','compact') if trial%2==0 else ('compact','full')):
   out=a.out/f'checker_{arm}_{trial:02d}.json';log=a.out/f'checker_{arm}_{trial:02d}.log'
   cmd=[sys.executable,str(a.checker),'--receipt',str(a.original if arm=='full' else a.compact),'--input',str(a.source_dir),'--manifest',str(a.manifest),'--backend',a.backend,'--out',str(out)]
   start=time.perf_counter();r=subprocess.run(cmd,capture_output=True,text=True,timeout=80);elapsed=time.perf_counter()-start
   log.write_text(r.stdout+'\n'+r.stderr)
   if r.returncode:raise RuntimeError(f'FAILED_{arm}_{trial}: '+r.stdout[-500:]+r.stderr[-500:])
   d=json.loads(out.read_text());tot=d['totals']
   assert tot['dual_safe_certified']==4 if a.backend=='dual' else tot['z3_safe_certified']==4
   assert tot['original_checked']==4 and tot['unsat_vc']==12 and tot['negative_controls']==8
   rows.append({'trial':trial,'arm':arm,'process_wall_s':round(elapsed,6),'checker_reported_wall_s':d['wall_s'],
    'Z3_checks':tot['q_z3'],'independent_cvc5_checks':tot['q_cvc5'],'all_4_certified':True,'receipt_sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
  print('VALID_REUSE_TRIAL',trial,'full',round(rows[-2]['process_wall_s'],4),'compact',round(rows[-1]['process_wall_s'],4),flush=True)
 summary={}
 for arm in ('full','compact'):
  v=[r for r in rows if r['arm']==arm]
  summary[arm]={'median_process_wall_s':round(statistics.median(r['process_wall_s'] for r in v),6),
                'median_checker_wall_s':round(statistics.median(r['checker_reported_wall_s'] for r in v),6),
                'n':len(v)}
 gain=summary['full']['median_process_wall_s']-summary['compact']['median_process_wall_s']
 cost=p['wall_s'];break_even=None if gain<=0 else int(cost//gain)+1
 out={'schema':'NEUMANN.Q4.reused_certificate_compaction_economics.v1','source_count':4,'paired_dual_trials':a.pairs,'backend':a.backend,
 'full_clause_count':p['total_old_atoms'],'compacted_clause_count':p['total_compacted_atoms'],
 'full_chars':p['total_old_characters'],'compacted_chars':p['total_compacted_characters'],
 'size_compression_ratio':round(p['total_old_characters']/p['total_compacted_characters'],4),
 'extra_compaction_z3_checks':p['total_original_z3_vc_calls'],'extra_compaction_wall_s':cost,
 'times':rows,'summary':summary,
 'observed_per_replay_delta_full_minus_compact_s':round(gain,6),
 'breakeven_replays_for_compaction_under_this_approx_median_delta':break_even,
 'important_limitations':'4 known programs only, benchmark variable hardware/cache; negative or zero proof speed gain => no break-even; candidate generator/upper selector costs are common or excluded. No frontier or learned-only claim.'}
 (a.out/'DUAL_CERTIFICATE_REUSE_ECONOMICS.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print('DUAL_CERTIFICATE_REUSE_SUMMARY',json.dumps({k:out[k] for k in ['full_clause_count','compacted_clause_count','size_compression_ratio','extra_compaction_z3_checks','extra_compaction_wall_s','observed_per_replay_delta_full_minus_compact_s','breakeven_replays_for_compaction_under_this_approx_median_delta']}),flush=True)
if __name__=='__main__':main()
