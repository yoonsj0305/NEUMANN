"""C-0a, before any training (stage2/DESIGN.md 11.7): does the head-path coupling as defined leak the answer?

The 11.7 key ID of position i is the order in which head h's path first visits i.  On a teacher-forced sequence
(prompt + answer + <eos>) the path is only defined up to the last token, so a prompt position that the head would visit
only after the answer has ended gets key ID 0.  The answer-phase moves do not depend on the answer tokens (every token
after '=' is the "answer phase" kind, stage1/pf.py token_classes), so the path is a function of the prompt and the step
index; but how far it gets is a function of the answer LENGTH.  Where the answer length is not fixed by the prompt
(addition: the final carry; N x 1: the final carry / d = 0), the key IDs on prompt positions -- which are inputs at
those positions, before the answer -- then carry information about the answer.

Per task and bin (hand tables: G-0a; reverse: the H-0a BOS table; 200 examples per bin of the evaluation sets):
  literal_vs_prompt_only   share of examples whose prompt key IDs differ between the literal definition (path over the
                           actual sequence) and a prompt-only definition (the same path continued with answer-phase
                           tokens until every head has stopped visiting new positions)
  depends_on_answer_length share of examples whose literal prompt key IDs change when the answer is one token longer
  answer_length_not_fixed  share of examples whose answer length differs from the most common answer length among
                           examples with the same prompt length profile (operand lengths) -- answer information

  python stage2/c0a_coupling_check.py        # writes stage2/results/c0a/coupling_check.json
"""
from __future__ import annotations
import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "stage1"), str(HERE)]
import torch                     # noqa: E402
import tasks as T1               # noqa: E402
import g_tasks as G              # noqa: E402
import h_tasks as HT             # noqa: E402
import g0a                       # noqa: E402
import h0a                       # noqa: E402

TAB = {"addition": g0a.ADDITION_HAND, "copy": g0a.TABLES["copy"], "mul1": g0a.TABLES["mul1"],
       "prefix_sum": g0a.TABLES["prefix_sum"], "reverse": h0a.TABLES["reverse"]}
N = 200
FILL = G.TOK["0"]          # any token after '=' is the answer-phase kind


def sets(t):
    if t == "addition":
        return T1.eval_sets(t, N, N)
    if t == "reverse":
        return HT.eval_sets(t, N, N)
    return G.eval_sets(t, N, N)


def keys(path, n):
    k = [[0] * n for _ in range(3)]
    cnt = [0, 0, 0]
    for st in path:
        for h in range(3):
            i = st[h]
            if i < n and k[h][i] == 0:
                cnt[h] += 1
                k[h][i] = cnt[h]
    return k


def profile(p):
    """operand lengths of the prompt (runs of digits)"""
    out, run = [], 0
    for x in p:
        if x in g0a.DIG:
            run += 1
        elif run:
            out.append(run)
            run = 0
    return tuple(out + ([run] if run else []))


def main():
    torch.set_num_threads(1)
    res = {}
    for t, tab in TAB.items():
        res[t] = {}
        for lab, ex in sets(t).items():
            lit = dep = 0
            lens = collections.defaultdict(collections.Counter)
            for p, a in ex:
                s = p + a
                n = len(s)
                path = g0a.head_path(s, tab)
                kf = keys(path, n)
                ke = keys(g0a.head_path(s + [FILL] * (n + 5), tab), n)
                k1 = keys(g0a.head_path(s + [FILL], tab), n + 1)
                lit += [r[:len(p)] for r in kf] != [r[:len(p)] for r in ke]
                dep += [r[:len(p)] for r in kf] != [r[:len(p)] for r in k1]
                lens[profile(p)][len(a)] += 1
            notfixed = sum(sum(c.values()) - max(c.values()) for c in lens.values())
            res[t][lab] = {"examples": len(ex), "literal_vs_prompt_only": lit / len(ex),
                           "depends_on_answer_length": dep / len(ex), "answer_length_not_fixed": notfixed / len(ex)}
            print(t, lab, json.dumps(res[t][lab]), flush=True)
    out = HERE / "results" / "c0a"
    out.mkdir(parents=True, exist_ok=True)
    (out / "coupling_check.json").write_text(json.dumps(
        {"design": "stage2/DESIGN.md 11.7 (key / query channels); check before training", "results": res}, indent=1))


if __name__ == "__main__":
    main()
