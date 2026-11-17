import test from "node:test";
import assert from "node:assert/strict";
import {admitNewOriginalIds,admitManifest} from "../experiments/q3_global_original_provenance.mjs";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
const reg={schema:"neumann.q3.arc-original-global-ledger-verified.v1",verified:true,remaining_unscored:1,alreadyUsed:{"known.json":["P19"],"fresh.json":[]}};
test("new 1-file truly untouched cohort is admitted with explicit new-reserve accounting",()=>{
 assert.deepEqual(admitNewOriginalIds(reg,["fresh.json"]),{admitted:true,new_unique_originals:1,remaining_after:0});
});
test("a previously evaluated file must cause explicit duplicate-identity failure",()=>{
 assert.throws(()=>admitNewOriginalIds(reg,["known.json"]),/NOT_A_TRULY_UNSEEN_ORIGINAL_COHORT/);
});
test("unknown file IDs, duplicate IDs and oversized registration fail closed",()=>{
 assert.throws(()=>admitNewOriginalIds(reg,["unknown.json"]),/NOT_A_TRULY_UNSEEN_ORIGINAL_COHORT/);
 assert.throws(()=>admitNewOriginalIds(reg,["fresh.json","fresh.json"]),/BAD_IDENTITIES/);
 assert.throws(()=>admitNewOriginalIds(reg,["fresh.json","known.json"]),/NOT_A_TRULY_UNSEEN_ORIGINAL_COHORT/);
});
test("future experiment must provide proof-carrying global registry",()=>{
 assert.throws(()=>admitNewOriginalIds({verified:false},["fresh.json"]),/GLOBAL_LEDGER_REQUIRED/);
});

test("future manifest admission requires pinned source, filename-only selection and untouched IDs",()=>{
 const d=fs.mkdtempSync(path.join(os.tmpdir(),"neumann-original-admit-"));
 const f=path.join(d,"cohort.json");
 const write=o=>fs.writeFileSync(f,JSON.stringify(o));
 try{
  const valid={ids:["fresh.json"],source_folder:"data/evaluation",upstream_commit:"399030444e0ab0cc8b4e199870fb20b863846f34",filename_selection_only:true};
  write(valid);
  const r=admitManifest(reg,f);
  assert.equal(r.admitted,true);
  assert.equal(r.new_unique_originals,1);
  assert.match(r.source_manifest_sha256,/^[a-f0-9]{64}$/);
  write({...valid,ids:["known.json"]});
  assert.throws(()=>admitManifest(reg,f),/NOT_A_TRULY_UNSEEN_ORIGINAL_COHORT/);
  write({...valid,upstream_commit:"unfrozen"});
  assert.throws(()=>admitManifest(reg,f),/NEW_COHORT_SOURCE_OR_PROTOCOL_NOT_FROZEN/);
  write({...valid,filename_selection_only:false});
  assert.throws(()=>admitManifest(reg,f),/NEW_COHORT_SOURCE_OR_PROTOCOL_NOT_FROZEN/);
 }finally{fs.rmSync(d,{recursive:true,force:true});}
});
