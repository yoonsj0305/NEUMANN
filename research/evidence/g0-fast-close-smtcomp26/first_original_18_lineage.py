"""One frozen original 18 structural lineage screen; no solves, no hints, no neural.

Preregistered in GitHub NEUMANN Issue #218 comment 6247912445.
Audit only opened 2026 historical development cases. Not new blind G1/G2.
"""
import collections,hashlib,importlib.util,json,re,sys
from pathlib import Path
import z3
ROOT=Path(__file__).resolve().parent
SOURCE_SCRIPT=ROOT/"first_original_18_modern_classical_replay.py"
SPEC=importlib.util.spec_from_file_location("frozen18",SOURCE_SCRIPT)
M=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
OUT=Path("/tmp/g0_mathproblems18_source_lineage_first.json")

def source_banner(s):
    m=re.search(r"Problem:\s*([^\r\n|]*)",s)
    return m.group(1).strip()[:120] if m else "SOURCE_HEADER_NOT_IDENTIFIED"

def canonical_formula(s):
    """Lossless lexical structure of unmodified original ASSERT expressions.
    Avoid quadratic Z3 get_vars on large 350KB hard original AST trees.
    Exact original Z3 parse happens in pinned source retrieval function.
    """
    decls=re.findall(r"\(declare-fun\s+([^\s()]+)\s+\(\)\s+Int\s*\)",s)
    symbols={name:"AUDIT_SYMBOL_"+str(i) for i,name in enumerate(sorted(set(decls)))}
    forms=[]
    for m in re.finditer(r"\(assert\b",s):
        start=m.start()
        depth=0
        stop=None
        for offset in range(start,len(s)):
            if s[offset]=="(":depth+=1
            elif s[offset]==")":
                depth-=1
                if depth==0:
                    stop=offset+1
                    break
        if stop is None:raise RuntimeError("UNBALANCED_ORIGINAL_ASSERT_FORM")
        forms.append(s[start:stop])
    if not forms:raise RuntimeError("NO_ASSERTIONS_IN_ORIGINAL_SOURCE")
    words=re.findall(r"\(|\)|[^\s()]+","\n".join(forms))
    canon=[]
    for t in words:
        if t in symbols:canon.append(symbols[t])
        elif re.fullmatch(r"[0-9]+",t) and t not in ("0","1"):canon.append("AUDIT_NUM")
        else:canon.append(t)
    return hashlib.sha256(" ".join(canon).encode()).hexdigest(),len(decls),len(forms)

def main():
    receipts=[]
    source_root=Path("/tmp/g0_mathproblems18_lineage_inputs")
    source_root.mkdir(exist_ok=True,parents=True)
    for key,label in M.frozen_original_keys():
        source,sha,size=M.get_original(key,source_root)
        raw=source.read_text(encoding="utf-8")
        fingerprint,numvars,nassert=canonical_formula(raw)
        receipts.append({
            "frozen_original_identity_sha256":M.original_sha(key),
            "source_sha256":sha,
            "source_bytes":size,
            "formula_template_hash_normalized_numeric_and_variable_names":fingerprint,
            "nvariables":numvars,
            "nassertions":nassert,
            "source_problem_header":source_banner(raw),
            "official_status_2026":label,
            "original_filename":key[2]})
    groups=collections.defaultdict(list)
    for r in receipts:
        groups[r["formula_template_hash_normalized_numeric_and_variable_names"]].append(r)
    clusters=sorted(groups.values(),key=lambda x:(-len(x),x[0]["original_filename"]))
    report={
        "status":"FIRST_18_FIXED_SOURCE_FINGERPRINT_AUDIT_COMPLETE",
        "prereg_issue_comment":6247912445,
        "source_original_git_commit":M.SOURCE_COMMIT,
        "input_selection_pinned_git_commit":M.INPUT_COMMIT,
        "originals":len(receipts),
        "unique_conservative_formula_templates":len(clusters),
        "major_cluster_count":sum(len(g)>=2 for g in clusters),
        "max_template_cluster_size":max(map(len,clusters)),
        "template_clusters":[{
            "shape_sha256":group[0]["formula_template_hash_normalized_numeric_and_variable_names"],
            "count":len(group),
            "problem_headers":dict(collections.Counter(t["source_problem_header"] for t in group)),
            "expected_status_distribution":dict(collections.Counter(t["official_status_2026"] for t in group)),
            "filenames":[t["original_filename"] for t in group],
            "source_files_sha256":[t["source_sha256"] for t in group]
        } for group in clusters],
        "caveat":"Exact normalization can miss semantic isomorphism; cluster count is an UPPER bound on independently distinct structures. All are same 2022 upstream generator origin and are NOT independent external domains.",
        "same_originals_no_removal":True,
        "no_neural_call_or_learning":True,
        "no_original_solver_run":True,
        "no_oracle_cost_measured":True,
        "G0":"OPEN",
        "G1":"HOLD_LEARNING",
        "G2":"BLOCKED",
        "Q1_to_Q7_global":"OPEN",
    }
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("G0_18_FIRST_LINEAGE",json.dumps({
         "cases":len(receipts),"shape_classes":len(clusters),
         "sizes":[len(g) for g in clusters],
         "headings":[group[0]["source_problem_header"] for group in clusters],
         "status":"COMPLETE"}),flush=True)
if __name__=="__main__":main()
