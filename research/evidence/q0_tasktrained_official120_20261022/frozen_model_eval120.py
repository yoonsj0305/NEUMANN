#!/usr/bin/env python3
"""Official ARC2 EVALUATION120 transfer of unchanged ARC2 TRAIN-only supervised tree grammar.
Saves predictions before any official test output exists in inference environment.
No postgrade tuning or new primitive, prior public eval aggregate exposed in project.
"""
import argparse,pathlib,hashlib,json,sys,time,collections
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[0]))
from learned_local_rule import attempt

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--masked-dir',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
 files=sorted(pathlib.Path(a.masked_dir).glob('*.json'))
 assert len(files)==120
 pred={}; t0=time.perf_counter()
 for f in files:
  task=json.loads(f.read_text());assert all('output' not in x for x in task['test'])
  r=attempt(task)
  pred[f.stem]=r
 result={'schema':'NEUMANN_Q0_UNCHANGED_ACTUALLY_LEARNED_LOCAL_RULE_ARC2_EVAL120.v1',
         'n':120,'eval_labels_seen':False,'prior_model_source_sha256':'0ebb17db4dba8ea047ba6f8f138885dc76bb483a9d52e7c2a4c9487491fd2649',
         'source_pin':'f3283f727488ad98fe575ea6a5ac981e4a188e49','source_tree':'8d04288aac3146b7c47d0b799c18bc9c0217d838',
         'subset':'official_evaluation120_posthoc_project_context','total_inference_s':time.perf_counter()-t0,
         'status_counts':dict(collections.Counter(x['status'] for x in pred.values())),'rows':pred}
 pathlib.Path(a.out).write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n')
 print('OFFICIAL_ARC2_EVAL120_MASKED_PREDICTIONS',result['status_counts'],round(result['total_inference_s'],4),flush=True)
if __name__=='__main__':main()
