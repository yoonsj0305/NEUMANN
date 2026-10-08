"""Declared data-role loader; training and fresh evaluation remain unadmitted.

This guards this loader API, not arbitrary Python or the operating system.
"""
from pathlib import Path
import hashlib,json
from neumann1.structural_data_rights import authorize,DataUseError


class ExperienceStore:
    def __init__(self,root,index_sha256):
        self.root=Path(root).resolve();p=self.root/'index.json';raw=p.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=index_sha256:raise DataUseError('Index identity mismatch')
        self.index=json.loads(raw);self.records={r['record_id']:r for r in self.index['records']}
        if len(self.records)!=len(self.index['records']):
            raise DataUseError('Duplicate record identifiers require distinct execution labels')

    def view(self,record_id,field,purpose):
        asset=self.records[record_id]['assets'][field]
        authorize(asset,purpose)  # Must precede payload path resolution and I/O.
        path=(self.root/asset['path']).resolve()
        if not path.is_relative_to(self.root)or path==self.root:raise DataUseError('Payload escapes declared root')
        raw=path.read_bytes()
        if len(raw)>8*1024*1024:raise DataUseError('Bounded experience payload exceeded')
        if hashlib.sha256(raw).hexdigest()!=asset['sha256']:raise DataUseError('Experience identity mismatch')
        value=json.loads(raw)
        if purpose=='development_problem':
            allowed={'source','commands','declared_entrypoints','erased_type_signatures','author_sampling_config'}
            if set(value)!=allowed:raise DataUseError('Original functional public view whitelist')
        return value
