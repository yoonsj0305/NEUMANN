"""Q3H first design-only inspection: source AND label shapes for a small
license-qualified development subset of authentic Loopy C programs.

This is NOT test inference nor proof, and does not inspect Q3F escrow targets.
"""
import argparse,collections,io,zipfile,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3g-real-corpus-20261018"))
from link_real_invariants import run as pair_index
from inventory_real_corpus import workbook_tables
from license_body_audit import class_license

def inspect(workbook,archive):
    metadata=pair_index(workbook,archive)["per_pair_identity_only"]
    table=workbook_tables(workbook.read_bytes())["Sheet1"]
    labels={x.get("A","").strip():x.get("B","").strip() for x in table[1:]}
    rows=[]
    with zipfile.ZipFile(io.BytesIO(archive.read_bytes())) as z:
        licenses={name:class_license(z.read(name))
                  for name in {x["license_path_hint"] for x in metadata if x["license_path_hint"]}}
        for m in metadata:
            if licenses.get(m["license_path_hint"]) not in ("APACHE_2_0","BSD_3_CLAUSE","MIT"):continue
            code=z.read(m["program_path"]).decode("utf-8",errors="replace")
            label=labels.get(m["published_row_source"],"")
            if not label or len(label)>180 or label in code:continue
            rows.append((m,code,label))
    counts=collections.Counter(r[0]["source_group"] for r in rows)
    print("REAL_LICENSED_ELIGIBLE",len(rows),"GROUPS",dict(counts))
    groups=sorted(counts)
    selected=[]
    for g in groups:
        available=[r for r in rows if r[0]["source_group"]==g]
        available=sorted(available,key=lambda r:(len(r[1]),len(r[2])))
        selected.extend(available[:1])
    for m,code,label in selected[:16]:
        print("\n","="*18,"SOURCE",m["program_path"],"group",m["source_group"],"bytes",len(code))
        print("LABEL",repr(label[:280]))
        print("PROGRAM_FIRST_1200",repr(code[:1200]))
    print("INSPECTED_DEVELOPMENT_RECORDS",min(len(selected),16))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--workbook",type=Path,required=True);p.add_argument("--dataset",type=Path,required=True)
    a=p.parse_args();inspect(a.workbook,a.dataset)
