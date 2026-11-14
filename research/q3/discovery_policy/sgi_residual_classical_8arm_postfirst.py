#!/usr/bin/env python3
"""Eight classical replays for ALREADY OPENED SGI PRE_76_10 (POST-FIRST).
NO withheld target labels are read, parsed or opened here. The future constraint
is fully deleted from the solver copy. JSON and stdout frozen before grading.
"""
import hashlib,json,pathlib,re,resource,subprocess,time,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms, get_cmd, sha256

COMMIT='e7ae840e5546e9243ff94afb1a29064fc050011c'
SOURCE=pathlib.Path('upstream/data/benchmarks/hard/PRE_76_10/PRE_76_10.sl')
OUT=pathlib.Path('residual_first')
CONFIGS=[
 ('default_seed0',['--seed=0']),
 ('seed1',['--seed=1']),
 ('seed7',['--seed=7']),
 ('seed17',['--seed=17']),
 ('enum_smart',['--sygus-enum=smart']),
 ('enum_fast',['--sygus-enum=fast']),
 ('enum_random_seed1',['--sygus-enum=random','--seed=1']),
 ('unif_cond_igain',['--sygus-unif-pi=cond-enum-igain']),
]
def bounded(path,flags):
    def cpu_lim():
        resource.setrlimit(resource.RLIMIT_CPU,(12,13))
    start=time.monotonic()
    before=resource.getrusage(resource.RUSAGE_CHILDREN)
    proc=subprocess.Popen(['cvc5','--lang=sygus2']+flags+[str(path)],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,errors='replace',text=True,preexec_fn=cpu_lim)
    peak=0;stopped=None
    while proc.poll() is None:
        try:
            status=pathlib.Path(f'/proc/{proc.pid}/status').read_text(errors='replace')
            m=re.search(r'^VmRSS:\s+(\d+)\s+kB',status,re.M)
            if m:
                peak=max(peak,int(m.group(1)))
                if peak>819200:
                    proc.kill();stopped='RSS_CAP'
        except (FileNotFoundError,ProcessLookupError):
            pass
        if time.monotonic()-start>15:
            proc.kill();stopped='WALL_CAP'
        time.sleep(0.012)
    a,b=proc.communicate(timeout=3)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    return a,b,dict(
        exit_code=proc.returncode,forced_stop=stopped,wall_seconds=round(time.monotonic()-start,6),
        cpu_user_seconds=round(after.ru_utime-before.ru_utime,6),
        cpu_system_seconds=round(after.ru_stime-before.ru_stime,6),
        sampled_peak_rss_kib=peak or None,
        stdout_sha256=sha256(a.encode()),stderr_sha256=sha256(b.encode()),
    )

def main():
    assert subprocess.check_output(['git','-C','upstream','rev-parse','HEAD'],text=True).strip()==COMMIT
    OUT.mkdir(exist_ok=True)
    raw=SOURCE.read_bytes()
    s=raw.decode('utf8')
    orig_sha=sha256(raw)
    forms=top_level_forms(s)
    cs=[x for x in forms if get_cmd(x[2])=='constraint']
    assert len(cs)==10
    left,right,heldout=cs[-1]
    sourceonly=s[:left]+s[right:]
    assert len(top_level_forms(sourceonly))==len(forms)-1
    assert heldout not in sourceonly
    tmp=OUT/'source_only_input.sl'
    tmp.write_text(sourceonly)
    v=subprocess.check_output(['cvc5','--version'],text=True)
    r={'upstream_commit':COMMIT,'original_filename':'data/benchmarks/hard/PRE_76_10/PRE_76_10.sl',
       'original_sha256':orig_sha,
       'original_git_blob_sha1':hashlib.sha1(b'blob '+str(len(raw)).encode()+bytes([0])+raw).hexdigest(),
       'sourceonly_sha256':sha256(sourceonly.encode()),
       'withheld_original_constraint_sha256':sha256(heldout.encode()),
       'source_constraint_count':9,
       'config_prereg_commit':'69fbc6acf223c1ce535f6c9b71656c2019ef10a3',
       'historical_original_12task_first':'44047cd18e17e517cf0029329589411b997f53427d8fa3e152b044183d8524f0',
       'version':v,'scope':'POST_FIRST_CLASSICAL_DIAGNOSTIC_NO_ORACLE_NO_NEURAL',
       'heldout_gold_inspected_during_candidate_generation':False,
       'independent_heldout_grade':'NOT_RUN',
       'q1_q7_global':'OPEN','g1':'HOLD','results':[]}
    for i,(name,flags) in enumerate(CONFIGS):
        a,b,z=bounded(tmp,flags)
        out=OUT/f'{i:02d}.stdout';err=OUT/f'{i:02d}.stderr'
        out.write_text(a);err.write_text(b)
        z.update(index=i,name=name,flags=flags,candidate_count=len(re.findall(r'\(\s*define-fun\s+f\s+',a)))
        z['status']='CANDIDATE_UNGRADED' if z['exit_code']==0 and z['forced_stop'] is None and z['candidate_count']==1 and not re.search(r'exception|\(error|unsupported|error:',a+'\n'+b,re.I) else 'HOLD_CONFIG_ERROR_OR_NO_CANDIDATE'
        r['results'].append(z)
        print('POSTFIRST_CLASSICAL',i,name,z['status'],z['wall_seconds'],flush=True)
    tmp.unlink()
    p=OUT/'POSTFIRST_EIGHT_CONFIGS_CANDIDATES_BEFORE_GRADE.json'
    p.write_text(json.dumps(r,indent=2,sort_keys=True))
    print('CANDIDATE_FIRST_SHA256',sha256(p.read_bytes()))
if __name__=='__main__':main()
