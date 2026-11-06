"""Read-only independent transfer audit of one genuine upstream Stitch macro.

Real published corpus; deliberately researcher-opened, not source-blind Q3.
Stitch sees TRAIN only. Heldout sites are matched by an independent S-expression
parser, expanded back and compared structurally to the original full AST.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/experiments/Q3_EXP2_STITCH_REAL_CORPUS_TRAIN_HOLDOUT_PREREG_2026_11_06.json"


def fileblob(b: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()


def h(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical(tree):
    return "(" + " ".join(canonical(x) for x in tree) + ")" if isinstance(tree, tuple) else tree


def parse(text: str):
    tokens = re.findall(r"\(|\)|[^\s()]+", text)
    if not tokens or len(tokens) > 50000:
        raise ValueError("empty or too long S-expression")
    def rec(i, depth):
        if depth > 200 or i >= len(tokens):
            raise ValueError("unbalanced or too deep S-expression")
        if tokens[i] == ")":
            raise ValueError("unexpected close")
        if tokens[i] != "(":
            return tokens[i], i + 1
        result = []
        i += 1
        while i < len(tokens) and tokens[i] != ")":
            node, i = rec(i, depth + 1)
            result.append(node)
        if i >= len(tokens) or not result:
            raise ValueError("empty/unbalanced application")
        return tuple(result), i + 1
    node, end = rec(0, 0)
    if end != len(tokens):
        raise ValueError("trailing tokens")
    return node


def match(pattern, value, env):
    if isinstance(pattern, str) and re.fullmatch(r"#\d+", pattern):
        old = env.get(pattern)
        if old is not None and old != value:
            return False
        env[pattern] = value
        return True
    if isinstance(pattern, str):
        return pattern == value
    if not isinstance(value, tuple) or len(pattern) != len(value):
        return False
    return all(match(p, v, env) for p, v in zip(pattern, value))


def replace_macro(node, pattern, arity):
    env = {}
    if match(pattern, node, env) and all("#" + str(i) in env for i in range(arity)):
        return ("fn_0",) + tuple(env["#" + str(i)] for i in range(arity)), 1
    if not isinstance(node, tuple):
        return node, 0
    rows = [replace_macro(x, pattern, arity) for x in node]
    return tuple(x[0] for x in rows), sum(x[1] for x in rows)


def expand(node, pattern, arity):
    if isinstance(node, str):
        return node
    if node and node[0] == "fn_0":
        if len(node) != arity + 1:
            raise ValueError("macro call arity")
        args = tuple(expand(v, pattern, arity) for v in node[1:])
        def substitute(t):
            if isinstance(t, str):
                if re.fullmatch(r"#\d+", t):
                    k = int(t[1:])
                    if k >= arity:
                        raise ValueError("unbound macro argument")
                    return args[k]
                return t
            return tuple(substitute(v) for v in t)
        return substitute(pattern)
    return tuple(expand(x, pattern, arity) for x in node)


def mutate_nonhole(node):
    if isinstance(node, str):
        if not re.fullmatch(r"#\d+", node):
            return "__NEGATIVE_CONTROL_WRONG_OPERATOR__"
        return None
    for i, x in enumerate(node):
        changed = mutate_nonhole(x)
        if changed is not None:
            return tuple(changed if j == i else node[j] for j in range(len(node)))
    # A macro can consist entirely of reusable argument holes, e.g.
    # (#0 #0 #0); corrupt a direct hole rather than silently skip the
    # mandatory negative control.
    for i, x in enumerate(node):
        if isinstance(x, str) and re.fullmatch(r"#\d+", x):
            return tuple("__NEGATIVE_CONTROL_WRONG_HOLE__" if j == i else node[j]
                         for j in range(len(node)))
    return None


def macro_from_stdout(stdout):
    candidates = []
    for line in stdout.splitlines():
        m = re.search(r"body:\s*\[fn_0 arity=(\d+):\s*(.+)\]\s*$", line)
        if m:
            candidates.append((int(m.group(1)), parse(m.group(2).strip())))
    # Upstream writes the same one invention in its search trace, chosen
    # invention and final summary. Multiple text sightings are NOT multiple
    # discovered macros; conflicting definitions still fail closed.
    unique = list(dict.fromkeys(candidates))
    if len(unique) != 1:
        raise ValueError("exactly one consistent actual new Stitch fn_0 macro required")
    arity, pattern = unique[0]
    if not 1 <= arity <= 3:
        raise ValueError("unexpected macro arity")
    holes = set(re.findall(r"#\d+", canonical(pattern)))
    if not holes or any(int(t[1:]) >= arity for t in holes):
        raise ValueError("nonempty all-bound macro holes required")
    if mutate_nonhole(pattern) is None:
        raise ValueError("nontrivial abstraction body required")
    return arity, pattern


def prepare(source: Path, output: Path):
    contract = json.loads(CONTRACT.read_text())
    raw = source.read_bytes()
    if fileblob(raw) != contract["origin"]["git_blob_sha1"] or len(raw) != contract["origin"]["bytes"]:
        raise ValueError("upstream published dataset source drift")
    corpus = json.loads(raw)
    if not isinstance(corpus, list) or len(corpus) < 30 or not all(type(x) is str for x in corpus):
        raise ValueError("published corpus invalid")
    for row in corpus:
        parse(row)
    seed = contract["split"]["seed"]
    is_train = [int.from_bytes(hashlib.sha256((seed + ":" + str(i)).encode()).digest()[:8], "big") % 5 != 4 for i in range(len(corpus))]
    train = [s for s, keep in zip(corpus, is_train) if keep]
    heldout = [s for s, keep in zip(corpus, is_train) if not keep]
    if len(train) < 20 or len(heldout) < 5:
        raise ValueError("minimum cohort size")
    output.mkdir(parents=True, exist_ok=False)
    (output / "train.json").write_text(json.dumps(train) + "\n")
    (output / "heldout.json").write_text(json.dumps(heldout) + "\n")
    statement = {
        "corpus_git_blob": fileblob(raw), "corpus_sha256": h(raw),
        "num_total": len(corpus), "num_train": len(train), "num_holdout": len(heldout),
        "train_sha256": h(json.dumps(train).encode()), "holdout_sha256": h(json.dumps(heldout).encode()),
        "split_policy": contract["split"]["algorithm"],
        "learner_train_only": True, "heldout_content_claim": "ALREADY_PUBLIC_RESEARCHER_OPENED"
    }
    (output / "split_receipt.json").write_text(json.dumps(statement, indent=2, sort_keys=True) + "\n")
    return statement


def audit(directory: Path):
    c = json.loads(CONTRACT.read_text())
    train = json.loads((directory / "train.json").read_text())
    holdout = json.loads((directory / "heldout.json").read_text())
    r = json.loads((directory / "split_receipt.json").read_text())
    if h(json.dumps(train).encode()) != r["train_sha256"] or h(json.dumps(holdout).encode()) != r["holdout_sha256"]:
        raise ValueError("source-split drift")
    stdout_bytes = (directory / "stitch.stdout").read_bytes()
    arity, pattern = macro_from_stdout(stdout_bytes.decode())
    negative = mutate_nonhole(pattern)
    if negative is None:
        raise ValueError("mutation failed")
    total_sites = 0
    affected = 0
    for text in holdout:
        tree = parse(text)
        rewritten, sites = replace_macro(tree, pattern, arity)
        recovered = expand(rewritten, pattern, arity)
        if recovered != tree:
            raise ValueError("INDEPENDENT_HOLDOUT_MACRO_EXPANSION_FAILURE")
        if sites:
            affected += 1
            total_sites += sites
            if expand(rewritten, negative, arity) == tree:
                raise ValueError("WRONG_MUTANT_UNEXPECTEDLY_RECOVERED_ORIGINAL")
    outcome = {
        "schema": "neumann.exp2.stitch-real-corpus-readonly-macro-holdout-first.v1",
        "source_upstream_commit": c["origin"]["commit"],
        "source_upstream_blob": c["origin"]["git_blob_sha1"],
        "source_upstream_sha256": r["corpus_sha256"],
        "first_stitch_actual_stdout_sha256": h(stdout_bytes),
        "actual_macro_source": canonical(pattern),
        "actual_macro_arity": arity,
        "train_count": len(train), "holdout_count": len(holdout),
        "holdout_programs_with_macro": affected, "total_holdout_sites": total_sites,
        "all_holdout_macro_rewrites_expand_exactly": True,
        "wrong_macro_mutation_rejected": affected > 0,
        "nontrivial_holdout_reuse": total_sites > 0,
        "model_training": False,
        "original_problem_solved": False,
        "source_unopened_original_test": False,
        "static_macro_transfer_scope": "ORIGINAL_PROGRAM_AST_REUSE_NOT_NEW_SEMANTICS",
        "Q3": "OPEN", "Q4": "OPEN", "Q6": "OPEN", "Q7": "OPEN"
    }
    (directory / "first_audit.json").write_text(json.dumps(outcome, indent=2, sort_keys=True) + "\n")
    if total_sites <= 0:
        raise ValueError("NO_HOLDOUT_TRANSFER_NOT_SCIENTIFIC_PASS")
    return outcome


def main():
    p = argparse.ArgumentParser()
    p.add_argument("phase", choices=["prepare", "audit"])
    p.add_argument("--source", type=Path)
    p.add_argument("--directory", type=Path, required=True)
    args = p.parse_args()
    if args.phase == "prepare":
        if args.source is None:
            p.error("prepare needs source")
        result = prepare(args.source, args.directory)
    else:
        result = audit(args.directory)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
