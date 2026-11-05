/* NEUMANN 1 | Cross-branch original ARC-AGI-1 evaluation provenance ledger.
 *
 * Both a research audit and a mandatory preflight for future original
 * evaluation cohorts. No original task content or hidden target is accessed.
 * A random unseen filename set is not "new" if ANY other branch already used it.
 */
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {createHash} from "node:crypto";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
export const LEDGER_PATH="docs/experiments/q3_GLOBAL_ARC_EVALUATION_PROVENANCE_2026_11_05.json";
const equal=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
const read=p=>JSON.parse(fs.readFileSync(p,"utf8"));
const sha256=s=>createHash("sha256").update(s).digest("hex");
const blob=p=>{
 const raw=fs.readFileSync(p);
 return createHash("sha1").update("blob "+raw.length+"\0").update(raw).digest("hex");
};
const requireState=(ok,why)=>{if(!ok)throw Error("Q3_GLOBAL_ORIGINAL_LEDGER_FAILURE:"+why);};

export function computeRegistry(arcRoot) {
 const ledger=read(path.join(ROOT,LEDGER_PATH));
 requireState(ledger.schema==="neumann.q3.arc-agi-1.global-original-evaluation-ledger.v1","SCHEMA");
 requireState(ledger.upstream_sha==="399030444e0ab0cc8b4e199870fb20b863846f34","UPSTREAM");
 const dir=path.join(arcRoot,"data/evaluation");
 const names=fs.readdirSync(dir).filter(x=>x.endsWith(".json")).sort();
 requireState(names.length===400&&ledger.official_eval_original_count===400,"OFFICIAL_FILENAME_CENSUS");
 const official=new Set(names);
 const seen=new Map(),rows=[];
 for(const stage of ledger.registered_or_scored_cohorts){
  const full=path.join(ROOT,stage.path);
  requireState(blob(full)===stage.source_blob_sha,"SOURCE_HASH:"+stage.tag);
  const manifest=read(full);
  const ids=manifest.ids;
  requireState(Array.isArray(ids)&&ids.length===stage.taskCount&&
    new Set(ids).size===ids.length,"COHORT_SIZE_OR_DUPLICATES:"+stage.tag);
  requireState(ids.every(x=>official.has(x)),"NOT_IN_OFFICIAL_EVALUATION:"+stage.tag);
  const reused=ids.filter(x=>seen.has(x));
  const introduced=ids.filter(x=>!seen.has(x));
  for(const id of ids) {
   if(!seen.has(id))seen.set(id,{first:stage.tag,first_run_id:stage.first_run_id,by:[stage.tag]});
   else seen.get(id).by.push(stage.tag);
  }
  requireState(seen.size===stage.expectedCumulativeUnique,"CUMULATIVE_COUNT:"+stage.tag);
  rows.push({tag:stage.tag,source:stage.path,source_sha:stage.source_blob_sha,
    source_run:stage.first_run_id,
    total:ids.length,reused:reused.length,first_time:introduced.length,
    cumulative_unique:seen.size});
 }
 requireState(seen.size===ledger.exact_project_union_unique&&seen.size===389,"GLOBAL_UNION_CHANGED");
 const remaining=names.filter(x=>!seen.has(x));
 requireState(remaining.length===ledger.unused_original_evaluation_files&&remaining.length===11,
  "REMAINING_UNSEEN_COUNT_CHANGED");
 const tag=(id)=>seen.get(id)?.first??null;
 requireState(tag("0692e18c.json")==="P29_first_A","P29_NEW_EXACT_NOT_FIRST_USE");
 requireState(tag("c7d4e6ad.json")==="P30_first","P30_SELECTED_EXACT_NOT_FIRST_USE");
 const by=(t)=>rows.find(x=>x.tag===t);
 requireState(by("P29_first_A").reused===23&&by("P29_first_A").first_time===25,"P29_A_OVERLAP");
 requireState(by("P29_first_B_parallel").reused===35&&by("P29_first_B_parallel").first_time===13,"P29_B_OVERLAP");
 requireState(by("P30_first").reused===25&&by("P30_first").first_time===23,"P30_OVERLAP");
 const users=Object.fromEntries(names.map(id=>[id,seen.get(id)?.by??[]]));
 return {
  schema:"neumann.q3.arc-original-global-ledger-verified.v1",
  upstream:ledger.source+"@"+ledger.upstream_sha,
  source_folder:ledger.source_folder,
  verified:true,
  stage_count:rows.length,unique_registered_or_scored:seen.size,
  total_official_eval:400,remaining_unscored:remaining.length,
  remaining_ids_sha256:sha256(remaining.join("\n")+"\n"),
  independent_source_task_bodies_opened:false,
  P29_A_original_correct_novel:tag("0692e18c.json")==="P29_first_A",
  P30_original_correct_novel:tag("c7d4e6ad.json")==="P30_first",
  claims_reclassified:"P29/P30 original first runs had overlapping evaluation bodies from other branches; cannot call entire 48 new or global Q6 PASS.",
  rows,alreadyUsed:users
 };
}
/** Call directly BEFORE any future evaluation data body is read. */
export function admitNewOriginalIds(registry,ids){
 if(!registry?.verified||registry.schema!=="neumann.q3.arc-original-global-ledger-verified.v1")
  throw Error("GLOBAL_LEDGER_REQUIRED");
 if(!Array.isArray(ids)||!ids.length||new Set(ids).size!==ids.length)
  throw Error("NEW_COHORT_BAD_IDENTITIES");
 const reused=ids.filter(id=>!id.endsWith(".json")||!Object.hasOwn(registry.alreadyUsed,id)||
   registry.alreadyUsed[id].length>0);
 if(reused.length)throw Error("NOT_A_TRULY_UNSEEN_ORIGINAL_COHORT:"+reused.length);
 if(ids.length>registry.remaining_unscored)throw Error("EXCEEDS_LAST_UNOPENED_ORIGINAL_BUDGET");
 return {admitted:true,new_unique_originals:ids.length,remaining_after:registry.remaining_unscored-ids.length};
}
/** Strict admission of an unmodified manifest from a new prospective experiment.
 * Call before any original TEST data body is opened, never after first scoring.
 */
export function admitManifest(registry,manifestPath) {
 const doc=read(manifestPath);
 const ids=doc.ids;
 if(doc.source_folder!=="data/evaluation"||
    doc.upstream_commit!=="399030444e0ab0cc8b4e199870fb20b863846f34"||
    doc.filename_selection_only!==true)
  throw Error("NEW_COHORT_SOURCE_OR_PROTOCOL_NOT_FROZEN");
 const result=admitNewOriginalIds(registry,ids);
 return {...result,source_manifest_sha256:sha256(fs.readFileSync(manifestPath)),
  note:"Preflight admission only; no claim of model generalization or original scoring"};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length<3||process.argv.length>4){console.error("Usage: node experiments/q3_global_original_provenance.mjs PINNED_ARC_ROOT [NEW_COHORT_MANIFEST.json]");process.exitCode=2;}
 else{try {
  const output=computeRegistry(process.argv[2]);
  // Never leak future first evaluation filenames into a printed report.
  const {alreadyUsed,...publicReceipt}=output;
  console.log(JSON.stringify(process.argv[3]?{global_registry:publicReceipt,new_cohort_admission:admitManifest(output,process.argv[3])}:publicReceipt,null,2));
 }catch(e){console.error(String(e.stack||e));process.exitCode=1;}}
}
