/* NEUMANN P2.9 first genuine FRESH (relative to prior 280) original ARC-AGI-1
 * evaluation against 5 strong preexisting classical TOOL families.
 *
 * Do not change executable P29 metagrammar. Neither training nor oracle leakage.
 * Independently replay each proposed AST from source; read original TEST GOLD
 * only in previously audited assess() after all arms have produced predictions.
 * Same human-authored program language is equally accessible to classical TOOL,
 * thus Q3 autonomous opcode invention NOT established regardless of result.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {assess} from './q3_p29_opened48_dev.mjs';
const ROOT=path.join(path.dirname(fileURLToPath(import.meta.url)),'..');
const load=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const blob=p=>{const v=fs.readFileSync(p);return createHash('sha1').update('blob '+v.length+'\0').update(v).digest('hex');};
const sha256=b=>createHash('sha256').update(b).digest('hex');
const fnv=s=>{let v=2166136261;for(const c of s)v=Math.imul(v^c.charCodeAt(0),16777619)>>>0;return v>>>0;};
const gate=(x,s)=>{if(!x)throw Error('P29_FRESH_SOURCE_CONTRACT:'+s);};
const manifestPath=path.join(ROOT,'docs/experiments/q3_p29_FIRST_FRESH_ORIGINAL48_COHORT.json');
const lockPath=path.join(ROOT,'docs/experiments/q3_p29_FIRST_FRESH_ORIGINAL48_SOURCE_LOCK.json');
export function verifyPinned(arcRoot) {
 const lock=load(lockPath),m=load(manifestPath);
 gate(blob(manifestPath)===lock.manifest_blob,'FROZEN_COHORT_DRIFT');
 gate(m.upstream_commit===lock.upstream_commit,'UPSTREAM_DRIFT');
 for(const [name,expected] of Object.entries(lock.source_blobs))
   gate(blob(path.join(ROOT,name))===expected,'PROGRAM_SOURCE_DRIFT:'+name);
 const excludes=new Set();
 for(const x of m.prior_registration_manifests){
   const p=path.join(ROOT,x.path);
   gate(blob(p)===x.blob,'PRIOR_MANIFEST_BLOB_DRIFT:'+x.path);
   const cohort=load(p);
   gate(cohort.ids.length===x.n,'PRIOR_ID_COUNT_DRIFT:'+x.path);
   for(const id of cohort.ids)excludes.add(id);
 }
 gate(excludes.size===m.prior_seen_unique&&excludes.size===280,'OLD_280_EXCLUSIONS_DRIFT');
 const dir=path.join(arcRoot,'data/evaluation');
 const names=fs.readdirSync(dir).filter(x=>x.endsWith('.json'));
 gate(names.length===400,'ORIGINAL_EVAL_FILE_CENSUS_DRIFT');
 const unseen=names.filter(name=>!excludes.has(name));
 const selected=unseen.map(name=>({name,value:fnv(m.salt+name)})).
   sort((a,b)=>a.value-b.value||a.name.localeCompare(b.name)).
   slice(0,48).map(x=>x.name);
 gate(unseen.length===120&&m.remaining_before_first===120,'PREVIOUS_UNSEEN_COUNT_DRIFT');
 gate(JSON.stringify(selected)===JSON.stringify(m.ids),'FROZEN_FILENAME_SELECTION_DRIFT');
 gate(m.ids.length===48&&new Set(m.ids).size===48&&m.remaining_reserve===72,'EXACT_48_COHORT_DRIFT');
 return {manifest:m,sourceLock:lock,evalDir:dir};
}
export function first(arcRoot) {
 const t0=process.hrtime.bigint(),v=verifyPinned(arcRoot),rows=[];
 for(const filename of v.manifest.ids){
   const bytes=fs.readFileSync(path.join(v.evalDir,filename));
   const task=JSON.parse(bytes);
   const out=assess(task,filename.replace('.json',''),undefined);
   rows.push({...out,original_json_sha256:sha256(bytes)});
 }
 const n=key=>rows.filter(x=>x[key]).length;
 const c={
  n:rows.length,
  previous_union_exact:n('old_correct'),
  P29_original_exact:n('p29_correct'),
  P29_original_submitted:n('p29_submitted'),
  P29_wrong_submitted:n('p29_wrong'),
  P29_new_exact_raw:n('raw_additional'),
  fully_safe_combined_exact:n('safe_correct'),
  fully_safe_combined_submitted:n('safe_submitted'),
  fully_safe_combined_wrong:n('safe_wrong'),
  additional_safe_exact:n('gained'),
  lost_old_exact:n('lost'),
  P29_train_consistent_programs:rows.filter(x=>x.trace.ast!==null).length,
  P29_supported_shape_rules:rows.filter(x=>x.trace.shapePrograms>0).length,
  duration_ms:Number(process.hrtime.bigint()-t0)/1e6,
  energy_joules:null,dollars:null
 };
 const criteria=v.manifest.gate;
 const pass=c.additional_safe_exact>=criteria.minimum_P29_additional_exact_vs_5_strong_old_union&&
      c.P29_wrong_submitted<=criteria.maximum_new_P29_wrong_submissions&&
      c.lost_old_exact<=criteria.maximum_combined_lost_exact&&c.fully_safe_combined_wrong===0;
 return {
  schema:'neumann.q3.p29.first-fresh-original-48.v1',
  source:'fchollet/ARC-AGI@'+v.manifest.upstream_commit,
  manifest_blob:v.sourceLock.manifest_blob,
  earlier_evaluation_files_excluded:280,
  fresh_original_count:48,
  reserved_untouched_remaining:72,
  P29_hypothesis_class:'human-authored coordinate metagrammar; exact deterministic search',
  learned_neural_model_calls:0,teacher_calls:0,
  original_test_gold_accessed_only_after_all_proposals:true,
  task_identity_only_before_first_score:true,
  verified_full_output_replay:true,
  science_status:pass?'OPENED_UNSEEN_COEFFICIENT_TRANSFER_PASS_NOT_AUTONOMOUS_Q3':'P29_FIRST_FRESH_TRANSFER_FAIL_OR_UNSAFE',
  core_Q3:'OPEN',unseen_family_Q6:'OPEN',frontier_Q7:'OPEN',full_cost_10x:'NOT_PROVEN',
  counts:c,rows
 };
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==3){console.error('Usage: node experiments/q3_p29_unseen_first48.mjs ARC_ROOT');process.exitCode=2;}
 else{try{console.log(JSON.stringify(first(process.argv[2]),null,2));}
 catch(e){console.error(String(e.stack||e));process.exitCode=1;}}
}
