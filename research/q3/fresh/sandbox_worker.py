"""Runs ONE reference function in a restricted namespace.  Started only by sandbox.py inside a network
namespace without interfaces, with CPU / memory / file-size / file-descriptor limits, an empty working
directory and an empty environment.  Protocol: first stdin line {"code", "entry"}; then one JSON input list
per line; one JSON reply per line: {"ok": output} or {"error": kind}."""
import builtins, json, signal, sys

ALLOWED = {"math", "collections", "itertools", "heapq", "functools", "operator", "bisect", "re", "string",
           "statistics", "typing", "array"}
_real_import = builtins.__import__


def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name.split(".")[0] not in ALLOWED:
        raise ImportError("blocked: " + name)
    return _real_import(name, globals, locals, fromlist, level)


SAFE = {k: getattr(builtins, k) for k in dir(builtins) if k not in {
    "open", "exec", "eval", "compile", "input", "breakpoint", "exit", "quit", "help", "globals", "locals",
    "vars", "memoryview", "__import__"}}
SAFE["__import__"] = guarded_import


class Timeout(Exception):
    pass


def _alarm(*_):
    raise Timeout


def main():
    spec = json.loads(sys.stdin.readline())
    ns = {"__builtins__": SAFE, "__name__": "reference"}
    exec(spec["code"], ns)
    fn = ns[spec["entry"]]
    signal.signal(signal.SIGALRM, _alarm)
    for line in sys.stdin:
        x = json.loads(line)
        try:
            signal.alarm(1)
            y = fn(list(x))
            signal.alarm(0)
            if isinstance(y, bool):
                out = {"ok": y}
            elif isinstance(y, int):
                out = {"ok": y}
            elif isinstance(y, (list, tuple)) and all(isinstance(e, int) and not isinstance(e, bool) for e in y):
                out = {"ok": list(y)}
            else:
                out = {"error": "type"}
        except Timeout:
            out = {"error": "timeout"}
        except Exception as e:
            signal.alarm(0)
            out = {"error": type(e).__name__}
        sys.stdout.write(json.dumps(out) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
