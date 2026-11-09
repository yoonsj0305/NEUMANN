"""CodeARC benchmark's SEALED reference-function oracle, SOURCE-QUERY only.

This adapter is NOT imported by the NEUMANN learner. It is only in the
external evaluation harness. It loads a pinned author original function,
and answers the limited input queries chosen and SHA-frozen by
neumann1.active_oracle_challenges. It must NOT pass the function source,
filename, AST, name or target gold back to the generator. When the reference
cannot execute, the oracle ABSTAINS rather than fabricating a label.

DO NOT count a target already scored as fresh. Source queries are additional
privileged observations, so equal-oracle-budget random and active controls
are obligatory for causal conclusions. External author code executes only
inside networkless restricted Docker, with no host bind mounts.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import subprocess
from time import perf_counter_ns


_WORKER=r"""
import json,sys
p=json.loads(sys.stdin.read())
scope={'__name__':'__main__'}
try:
 exec(compile(p['source'],'<author_original>','exec'),scope,scope)
 fn=scope[p['entrypoint']]
 results=[]
 for item in p['inputs']:
  try:
   args=[item] if p['arity']==1 else item
   answer=fn(*args)
   json.dumps(answer)
   results.append({'ok':True,'value':answer})
  except Exception:
   results.append({'ok':False,'value':None})
 print(json.dumps({'ok':True,'results':results},
                  separators=(',',':')))
except Exception:
 print(json.dumps({'ok':False,'results':[]},
                  separators=(',',':')))
"""


@dataclass(frozen=True)
class OracleBatch:
    status:str
    outputs:tuple
    count:int
    elapsed_ms:float


class AuthorFunctionOracle:
    def __init__(self,*,source_path,entrypoint,arity,
                 image="python:3.11-alpine",timeout_s=9):
        source=Path(source_path).read_text()
        tree=ast.parse(source)
        if (len(source)>45000 or not 1<=arity<=2 or
                not entrypoint.isidentifier() or
                not any(isinstance(x,ast.FunctionDef) and
                        x.name==entrypoint for x in tree.body)):
            raise ValueError("pinned original reference function mismatch")
        if not 2<=timeout_s<=30:
            raise ValueError("finite oracle walltime required")
        self._reference=source
        self._function=entrypoint
        self._arity=arity
        self._image=image
        self._timeout=timeout_s
        self._calls=0

    def batch(self,queries):
        now=perf_counter_ns()
        if not 1<=len(queries)<=12:
            return OracleBatch("ABSTAIN_ORACLE_BUDGET",(),0,0)
        if shutil.which("docker") is None:
            return OracleBatch("ABSTAIN_NO_ORACLE_SANDBOX",(),0,0)
        request=json.dumps(
            {"source":self._reference,"entrypoint":self._function,
             "arity":self._arity,"inputs":queries},
            ensure_ascii=True,separators=(",",":"))
        if len(request)>160000:
            return OracleBatch("ABSTAIN_ORACLE_INPUT_SIZE",(),0,0)
        command=[
            "docker","run","--rm","-i","--network=none","--read-only",
            "--cap-drop=ALL","--security-opt=no-new-privileges",
            "--pids-limit=24","--memory=224m","--memory-swap=224m",
            "--cpus=1","--user=65534:65534",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=16m",
            self._image,"python","-I","-S","-c",_WORKER]
        try:
            proc=subprocess.run(
                command,input=request,text=True,
                capture_output=True,timeout=self._timeout,check=False)
        except (OSError,subprocess.TimeoutExpired):
            return OracleBatch(
                "ABSTAIN_ORACLE_SANDBOX_OR_TIMEOUT",(),0,
                (perf_counter_ns()-now)/1e6)
        self._calls+=len(queries)
        if proc.returncode!=0 or len(proc.stdout)>160000:
            return OracleBatch(
                "ABSTAIN_ORACLE_EXIT",(),len(queries),
                (perf_counter_ns()-now)/1e6)
        try:answer=json.loads(proc.stdout)
        except (ValueError,TypeError):
            return OracleBatch(
                "ABSTAIN_ORACLE_PROTOCOL",(),len(queries),
                (perf_counter_ns()-now)/1e6)
        results=answer.get("results") if isinstance(answer,dict) else None
        if (answer.get("ok") is not True or
                not isinstance(results,list) or
                len(results)!=len(queries)):
            return OracleBatch(
                "ABSTAIN_ORACLE_RUNTIME",(),len(queries),
                (perf_counter_ns()-now)/1e6)
        values=tuple(
            (r["value"] if isinstance(r,dict) and r.get("ok") is True
             else None) for r in results)
        successes=sum(
            isinstance(r,dict) and r.get("ok") is True for r in results)
        return OracleBatch(
            "EXECUTED_ALL" if successes==len(queries)
            else "EXECUTED_PARTIAL",
            values,len(queries),(perf_counter_ns()-now)/1e6)
