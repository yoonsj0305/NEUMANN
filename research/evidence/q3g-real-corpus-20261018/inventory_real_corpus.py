"""Q3G: provenance-first Loopy authentic program/invariant data inventory.

Uses only Python standard library to read ZIP metadata and SpreadsheetML cells.
No third-party program text or model-target content is committed or distributed.
No claim of independent original verification until per-instance recheck.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,re,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parent
LOOPY_REV="91fe89245a0894ec8ad3741d85ae91ce3b552b2e"
LOOPY_WORKBOOK_GIT_BLOB="3e974edea4c856fee68d723cf867140d57094957"
LOOPY_DATASET_GIT_BLOB="17cac0f6734a39f0fe73558199cc2ad8d5c1a810"
COMPETITION_ESCROW_SOURCE_HASHES=(
  "9d112660de0da6924b01676ecf3398230fba61872fdcfa8ef74996bdec6977a1",
  "eb2bd76dc61c8b6554e481202fdf2c351ae9ff3a2a5d8e913bc9be984bd601bf",
)
NS={
 "m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main",
 "r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships",
 "p":"http://schemas.openxmlformats.org/package/2006/relationships",
}

def git_blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()

def workbook_tables(raw):
    tables={}
    with zipfile.ZipFile(raw) as z:
        shared=[]
        if "xl/sharedStrings.xml" in z.namelist():
            shared_xml=ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in shared_xml.findall("m:si",NS):
                shared.append("".join(t.text or "" for t in si.iter("{"+NS["m"]+"}t")))
        wb=ET.fromstring(z.read("xl/workbook.xml"))
        rels=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        targets={x.attrib["Id"]:x.attrib["Target"].lstrip("/") for x in rels}
        for sheet in wb.findall("m:sheets/m:sheet",NS):
            sid=sheet.attrib.get("{"+NS["r"]+"}id","")
            dest=targets.get(sid,"")
            if not dest.startswith("xl/"):dest="xl/"+dest
            if dest not in z.namelist():raise ValueError("MISSING_WORKSHEET_XML")
            xml=ET.fromstring(z.read(dest))
            rows=[]
            for row in xml.findall(".//m:sheetData/m:row",NS):
                vals={}
                for c in row.findall("m:c",NS):
                    address=c.attrib["r"]
                    col=re.match(r"[A-Z]+",address).group()
                    el=c.find("m:v",NS)
                    if c.attrib.get("t")=="inlineStr":
                        ss=c.find("m:is",NS)
                        value="".join(x.text or "" for x in ss.iter("{"+NS["m"]+"}t")) if ss is not None else ""
                    elif el is None:value=""
                    elif c.attrib.get("t")=="s":value=shared[int(el.text)]
                    else:value=el.text or ""
                    if value:vals[col]=value
                if vals:rows.append(vals)
            tables[sheet.attrib["name"]]=rows
    return tables

def scan(xlsx,archive):
    xl=xlsx.read_bytes();raw=archive.read_bytes()
    if git_blob(xl)!=LOOPY_WORKBOOK_GIT_BLOB or git_blob(raw)!=LOOPY_DATASET_GIT_BLOB:
        raise ValueError("MISMATCH_PUBLIC_PINNED_DATASET")
    tables=workbook_tables(xl)
    with zipfile.ZipFile(raw) as z:
        files=[i for i in z.infolist() if not i.is_dir()]
        names=[i.filename for i in files]
        paths=collections.Counter(n.split("/")[1] if len(n.split("/"))>1 else "root" for n in names)
        # Only file paths and sizes for aggregate inventory; actual program content is not accessed.
    return {
       "status":"REAL_DATA_ASSET_INVENTORY_COMPLETE_NOT_TRAINING",
       "loopy_commit":LOOPY_REV,
       "workbook_git_blob":LOOPY_WORKBOOK_GIT_BLOB,
       "dataset_git_blob":LOOPY_DATASET_GIT_BLOB,
       "workbook_sha256":hashlib.sha256(xl).hexdigest(),
       "dataset_sha256":hashlib.sha256(raw).hexdigest(),
       "workbook_bytes":len(xl),"dataset_bytes":len(raw),
       "xlsx_sheets":[{
            "name":name,"populated_rows":len(rows),
            "first_two_row_metadata":[
                {col:str(v)[:110] for col,v in sorted(row.items())}
                for row in rows[:2]
            ]
       } for name,rows in tables.items()],
       "program_archive_file_count":len(files),
       "archive_second_segment_counts":dict(paths),
       "exclusions":list(COMPETITION_ESCROW_SOURCE_HASHES),
       "holdout_original_source_bodies_accessed":False,
       "learned_model_calls":0,
       "independent_original_proof_replays":0,
       "global_q1_q7":"OPEN"
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--workbook",type=Path,required=True)
    p.add_argument("--dataset",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    report=scan(args.workbook,args.dataset)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print("REAL_DATA_STATUS",report["status"])
    print("TABULAR_ROWS",[(t["name"],t["populated_rows"]) for t in report["xlsx_sheets"]])
    print("ARCHIVE_FILES",report["program_archive_file_count"])
    print("ARCHIVE_GROUPS",report["archive_second_segment_counts"])
