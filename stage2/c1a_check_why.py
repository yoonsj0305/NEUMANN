"""C-1a: why check (d) is not 1.000 for addition and mul1 (record only): conflicting keys in the training table with two
examples each, and the most common OOD 11-20 keys missing from the table (first 300 examples).

  python stage2/c1a_check_why.py addition > stage2/results/c1a/check_why_addition.txt
"""
import sys, collections
ROOT = __import__('pathlib').Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / 'stage1'), str(ROOT / 'stage2')]
import torch, c0a, c1a
task = sys.argv[1]
c0a.install(task)
import tasks as T, run as R
table = c0a.hand_table(task); mv = c1a.moving(table)
V = T.VOCAB
def keys(x, y, P):
    out = []
    for b in range(x.shape[0]):
        for t in (y[b] != -100).nonzero()[:, 0].tolist():
            k = (int(x[b, t]),) + tuple(int(x[b, P[b, j, t]]) for j in mv) + (int(x[b, t-1]),) + tuple(int(x[b, P[b, j, t-1]]) for j in mv)
            out.append((b, t, k, int(y[b, t])))
    return out
train = T.train_set(task, 100000, 21)
vals = collections.defaultdict(collections.Counter); ex = {}
for i in range(0, len(train), 512):
    x, y = R.make_batch(train[i:i+512]); P = c1a.read_paths(x, table)
    for b, t, k, v in keys(x, y, P):
        vals[k][v] += 1
        ex.setdefault((k, v), (train[i+b], t))
dig = set(T.TOK[d] for d in T.DIGITS)
conf = [k for k, c in vals.items() if len(c) > 1]
nd = sum(1 for k in conf if any(r not in dig for r in k[1:1+len(mv)]))
print(task, "keys", len(vals), "conflicting keys", len(conf), "of which a head reads a non-digit at t:", nd)
for k in conf[:3]:
    print(" key", [V[i] if i >= 0 else '-' for i in k], dict((V[v], n) for v, n in vals[k].items()))
    for v in list(vals[k])[:2]:
        (p, a), t = ex[(k, v)]
        s = p + a
        print("    ", " ".join(V[i] for i in p), "|", " ".join(V[i] for i in a), " step", t, "->", V[v])
# missing keys on OOD
ev = T.eval_sets(task, 1000, 500)
for lab in list(ev)[1:2]:
    miss = collections.Counter(); n = 0
    x, y = R.make_batch(ev[lab][:300]); P = c1a.read_paths(x, table)
    for b, t, k, v in keys(x, y, P):
        n += 1
        if k not in vals:
            miss[tuple(V[i] for i in k)] += 1
    print(lab, "missing", sum(miss.values()), "of", n, "e.g.", miss.most_common(4))
