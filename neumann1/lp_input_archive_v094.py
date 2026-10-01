"""Byte-exact retained input-compaction evidence, with explicit timing limits."""
import gzip,hashlib,io,json
from pathlib import Path


def load_archive(path):
    path=Path(path);m=json.loads(path.read_text());data=b''
    parts=m.get('parts') or [{'name':m['file'],'bytes':m['gzip_bytes'],'sha256':m['gzip_sha256']}]
    seen=set()
    for part in parts:
        name=part['name']
        if type(name) is not str or Path(name).name!=name or name in seen:raise ValueError('unsafe archive part')
        seen.add(name);b=(path.parent/name).read_bytes()
        if len(b)!=part['bytes'] or hashlib.sha256(b).hexdigest()!=part['sha256']:raise ValueError('archive part drift')
        data+=b
    if len(data)!=m['gzip_bytes'] or hashlib.sha256(data).hexdigest()!=m['gzip_sha256']:raise ValueError('gzip identity drift')
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:raw=stream.read(128*1024*1024+1)
    if len(raw)>128*1024*1024 or len(raw)!=m['json_bytes'] or hashlib.sha256(raw).hexdigest()!=m['json_sha256']:raise ValueError('decoded identity drift')
    r=json.loads(raw)
    if m['rerun'] is not False or r['summary']['decision']!=m['decision']:raise ValueError('first verdict drift')
    expected={'neumann.lp-input-probe.archive.v1':('neumann.lp-input-probe.v1','f9951a814c2ddfd8bdbdeabec79ad68bd2ef1d33'),
        'neumann.lp-input-cost.archive.v1':('neumann.lp-input-cost.v1','7e4b58ea2051ba0bec567c9f37f448854b69f057')}
    if m['format'] not in expected or (r['protocol']['schema'],m['preregistration_head'])!=expected[m['format']]:raise ValueError('archive protocol drift')
    if m['format']=='neumann.lp-input-cost.archive.v1' and (m['timing_validity']!='CONCURRENT_FOCUSED_TEST_CONTAMINATION' or m['positive_cost_claim_allowed'] is not False):raise ValueError('timing notice drift')
    return r
