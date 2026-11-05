/* P2.9 FIRST truly new original ARC-AGI-1 evaluation.
 * 48 IDs preregistered from 120 remaining unseen original eval files.
 * Core inference program unchanged from previous public development diagnostics.
 * Test OUTPUT remains unavailable to P29 inference and classical baselines.
 */
import fs from "node:fs";
import path from "node:path";
import {createHash} from "node:crypto";
import {fileURLToPath} from "node:url";
import {assess} from "./q3_p29_opened48_dev.mjs";
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const json=path=>JSON.parse(fs.readFileSync(path,"utf8"));
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const blob=p=>{const x=fs.readFileSync(p);return createHash("sha1").update("blob "+x.length+"\0").update(x).digest("hex");};
const sha256=b=>createHash("sha256").update(b).digest("hex");
const fnv=s=>{let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619)>>>0;return h>>>0;};
const prefix="neumann-p29-FIRST-SEMANTIC-TRANSFER-20261105|";
const assert=(yes,why)=>{if(!yes)throw Error("P29_FIRST_SOURCE_LOCK:"+why);};
export function sourcePreflight(arcRoot) {
 const originalDir=path.join(arcRoot,"data/evaluation");
 const cohortPath=path.join(ROOT,"docs/experiments/q3_p29_FIRST_FRESH48_COHORT_FROZEN.json");
 const lock=json(path.join(ROOT,"docs/experiments/q3_p29_FIRST_FRESH48_SOURCE_LOCK.json"));
 const cohort=json(cohortPath);
 assert(blob(cohortPath)===lock.cohort_blob,"COHORT_CHANGED");
 assert(cohort.upstream_commit==="399030444e0ab0cc8b4e199870fb20b863846f34","UPSTREAM_SHA_DRIFT");
 for(const [file,hash]of Object.entries(lock.source_blobs))
  assert(blob(path.join(ROOT,file))===hash,"SOURCE_CHANGED:"+file);
 const used=new Set();
 for(const prev of cohort.historic_previous_manifests){
  const p=path.join(ROOT,prev.path);
  assert(blob(p)===prev.blob_sha,"PREV_MANIFEST_DRIFT:"+prev.path);
  const m=json(p);assert(m.ids?.length===prev.count,"PREV_LENGTH_DRIFT:"+prev.path);
  for(const id of m.ids)used.add(id);
 }
 assert(used.size===280&&cohort.evaluated_prior_unique===280,"HISTORICAL_EVAL_EXCLUSIONS");
 const all=fs.readdirSync(originalDir).filter(x=>x.endsWith(".json"));
 assert(all.length===400&&cohort.source_original_file_count===400,"UPSTREAM_FILE_COUNT");
 const unused=all.filter(x=>!used.has(x));
 assert(unused.length===120,"UNOPENED_REMAINDER");
 const selected=unused.map(name=>({name,key:fnv(prefix+name)})).sort((a,b)=>a.key-b.key||a.name.localeCompare(b.name)).slice(0,48).map(x=>x.name);
 assert(selected.length===48&&eq(selected,cohort.ids),"PRECOMMITTED_COHORT_DRIFT");
 assert(cohort.unopened_after_this_selection===72,"REMAINING_RESERVE_DRIFT");
 return {cohort,lock,originalDir};
}
export function runFirst(arcRoot) {
 const started=process.hrtime.bigint(),{cohort,lock,originalDir}=sourcePreflight(arcRoot),rows=[];
 for(const filename of cohort.ids){
  const taskFile=path.join(originalDir,filename),raw=fs.readFileSync(taskFile),task=JSON.parse(raw);
  const row=assess(task,filename.replace(".json",""));
  row.original_file_sha256=sha256(raw);
  rows.push(row);
 }
 const count=k=>rows.filter(x=>x[k]).length;
 const oldWrong=rows.filter(x=>x.old_submitted&&!x.old_correct).length;
 const safeWrong=count("safe_wrong");
 const stats={
  N:rows.length,
  old_exact:count("old_correct"),old_submitted:count("old_submitted"),old_wrong:oldWrong,
  P29_exact:count("p29_correct"),P29_submitted:count("p29_submitted"),P29_wrong:count("p29_wrong"),
  P29_new_exact_raw:count("raw_additional"),
  safe_exact:count("safe_correct"),safe_submitted:count("safe_submitted"),safe_wrong:safeWrong,
  gained:count("gained"),lost:count("lost"),
  shape_expressible:rows.filter(x=>x.trace.shapePrograms>0).length,
  train_fitting_AST:rows.filter(x=>x.trace.ast!==null).length,
  total_shape_candidates:rows.reduce((a,b)=>a+b.trace.shapePrograms,0),
  total_coordinate_views:rows.reduce((a,b)=>a+b.trace.coordinateViews,0),
  total_geometry_pairs:rows.reduce((a,b)=>a+b.trace.geometryPairs,0),
  inference_wall_ms:rows.reduce((a,b)=>a+b.trace.wallMs,0),
  original_full_wall_ms:Number(process.hrtime.bigint()-started)/1e6,
  measured_energy_joules:null,measured_dollars:null
 };
 const p=cohort.hard_gate;
 const pass=stats.gained>=p.additional_exact_min&&stats.P29_wrong<=p.additional_false_submit_max&&
    stats.lost<=p.lost_correct_max&&stats.safe_wrong<=stats.old_wrong;
 return {schema:"neumann.q3.p29.first-fresh-public-original-eval48.v1",
  original_upstream:"fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34",
  first_frozen_source_manifest_git_blob:blob(path.join(ROOT,"docs/experiments/q3_p29_FIRST_FRESH48_SOURCE_LOCK.json")),
  cohort_sha:lock.cohort_blob,
  cohort_prior_excluded:cohort.evaluated_prior_unique,
  cohort_first_original:rows.length,remaining_original_unopened:72,
  classification:"PRECOMMITTED PUBLIC ARC EVALUATION FILES PREVIOUSLY NOT USED IN EIGHT FROZEN EVAL COHORTS; NOT SEALED OR ARC-AGI-2",
  all_proposals_before_gold_read:true,original_test_gold_used_only_for_final_score:true,
  source_is_human_defined_P29_metagrammar:true,
  P29_neural_calls:0,P29_teacher_calls:0,P29_training_updates:0,
  science_decision:pass?"P29_FIRST_LOCAL_TRANSFER_PASS_ONLY":"P29_FIRST_FRESH_TRANSFER_FAIL_STOP",
  matched_same_language_classical_baseline: "P29 itself deterministically enumerates its human-defined grammar. No learned policy advantage over identical-language classical enumerator.",
  autonomous_Q3:"OPEN",novel_semantic_family_Q6:"OPEN",frontier_Q7:"OPEN",complete_cost_10x:"NOT_PROVEN",
  stats,rows};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==3)throw Error("node experiments/q3_p29_first_fresh48.mjs <pinned ARC ROOT>");
 try{console.log(JSON.stringify(runFirst(process.argv[2]),null,2));}
 catch(e){console.error(String(e.stack||e));process.exitCode=1;}
}
