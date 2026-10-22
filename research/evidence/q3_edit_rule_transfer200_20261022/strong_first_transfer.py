#!/usr/bin/env python3
"""Transferred source-only ARC2 reserved train200, strongest historical symbolic first."""
import argparse,collections,hashlib,json,pathlib,sys,time
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path[:0]=[str(ROOT/'q3_strong_classical_union_20261022'),
              str(ROOT/'q3_relational_edit_masks_20261022')]
import historical_strong_composer as strong
from infer_edit_rule import infer

def main():
 p=argparse.ArgumentParser();p.add_argument('--masked',required=True);p.add_argument('--out',required=True)
 a=p.parse_args();fs=sorted(pathlib.Path(a.masked).glob('*.json'),key=lambda x:hashlib.sha256(x.stem.encode()).hexdigest())
 assert len(fs)==200
 assert hashlib.sha256(('\n'.join(f.stem for f in fs)+'\n').encode()).hexdigest()=='9f9f9f80d9c51dd31e0ad999e7d2cf7289fcd2791f785ba41fd74d1b86c8dc9b'
 begin=time.perf_counter();rows={}
 for f in fs:
    d=json.loads(f.read_text())
    assert all('output' not in q for q in d['test'])
    tic=time.perf_counter()
    try:
        ss=strong.find_programs(d); best=strong.choose_program(ss)
        if best is not None:
            r={'status':'STRONG_HISTORICAL_CLASSICAL','prediction':strong.predict(d,best),
               'strong_source_candidates':len(ss)}
        else:
            r=infer(d);r['strong_source_candidates']=0
        r['task_wall_s']=time.perf_counter()-tic
    except Exception as e:
        r={'status':'ERROR','prediction':None,
           'error':type(e).__name__+': '+str(e)[:160],'task_wall_s':time.perf_counter()-tic}
    rows[f.stem]=r
    if len(rows)%40==0:print('REAL_ARC200_TRANSFER_SOURCE_PROGRESS',len(rows),
                            dict(collections.Counter(x['status'] for x in rows.values())),flush=True)
 doc={'schema':'NEUMANN_Q3_ADAPTIVE_STRONGEST_SOURCE200.v1',
      'source_ref':'arcprize ARC-AGI-2 f3283f727488ad98fe575ea6a5ac981e4a188e49',
      'test_labels_seen':False,'n':200,
      'source_first_precedence':'original 96+64 classical -> prior objects -> 2-stage -> learned edit masks',
      'total_source_wall_s':time.perf_counter()-begin,
      'counts':dict(collections.Counter(x['status'] for x in rows.values())),
      'rows':rows}
 out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(doc,sort_keys=True,separators=(',',':'))+'\n')
 print('SEALED_TRANSFER200',json.dumps(doc['counts'],sort_keys=True),'wall_s',doc['total_source_wall_s'],
       'sha256',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
