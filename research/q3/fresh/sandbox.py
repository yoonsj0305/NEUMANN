"""Isolated execution of an independent author's reference function (FRESH oracle).

  * separate process: `unshare -n` (no network interfaces), `python3 -I -S` (no site, no user paths)
  * limits: RLIMIT_CPU 60 s per worker, RLIMIT_AS 1 GiB, RLIMIT_FSIZE 0 (no file writes), RLIMIT_NOFILE 16
  * empty temporary working directory, empty environment
  * restricted builtins and an import whitelist inside the worker; 1 s alarm per call
The agent never sees the code: it gets only outputs through `Oracle.call`.
"""
from __future__ import annotations
import json, os, pathlib, resource, subprocess, tempfile

WORKER = str(pathlib.Path(__file__).with_name("sandbox_worker.py").resolve())


def _limits():
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_AS, (1 << 30, 1 << 30))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (16, 16))
    os.setsid()


class Oracle:
    def __init__(self, code, entry):
        self.dir = tempfile.mkdtemp(prefix="oracle_")
        self.p = subprocess.Popen(["unshare", "-n", "python3", "-I", "-S", WORKER], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, cwd=self.dir, env={},
                                  preexec_fn=_limits, text=True)
        self.p.stdin.write(json.dumps({"code": code, "entry": entry}) + "\n")
        self.p.stdin.flush()

    def call(self, x):
        """Output for input list x, or None (error / timeout / dead worker)."""
        try:
            self.p.stdin.write(json.dumps(list(x)) + "\n")
            self.p.stdin.flush()
            line = self.p.stdout.readline()
        except (BrokenPipeError, OSError):
            return None
        if not line:
            return None
        r = json.loads(line)
        if "ok" not in r:
            return None
        v = r["ok"]
        return tuple(v) if isinstance(v, list) else v

    def close(self):
        try:
            self.p.kill()
        except Exception:
            pass
        try:
            os.rmdir(self.dir)
        except OSError:
            pass
