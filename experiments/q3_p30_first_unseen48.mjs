/* NEUMANN P3.0 prospective FIRST source-locked 48 original ARC-AGI-1 evaluations.
 * Classical control uses ALL 5 preexisting frozen tools + unchanged P29.
 * Only P30 additional right is typed crop/component -> coordinate composition.
 * Human-supplied primitives, no neural model training. Original TEST gold
 * accessed only AFTER all arms generated their predictions.
 */
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {createHash} from "node:crypto";
import * as B from "./q3_object_headroom_p11.mjs";
import * as P20 from "./q3_shape_pruned_synthesis_p20.mjs";
import * as P24 from "./q3_cached_typed_guard_p24.mjs";
import * as P25 from "./q3_generated_decision_trees_p25.mjs";
import * as P27 from "./q3_compositional_schema_learning_p27.mjs";
import * as P29 from "./q3_p29_induced_coordinate_programs.mjs";
import * as P30 from "./q3_p30_object_coordinate_composition.mjs";
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const lockfile=path.join(ROOT,"docs/experiments/q3_p30_FIRST_UNSEEN48_SOURCE_LOCK.json");
const manifestFile=path.join(ROOT,"docs/experiments/q3_p30_FIRST_UNSEEN48_COHORT_FROZEN.json");
const decode=p=>JSON.parse(fs.readFileSync(p,"utf8"));
const eq=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
const exact=(p,g)=>p!==null&&eq(p,g);
const blob=p=>{const v=fs.readFileSync(p);return createHash("sha1").update("blob "+v.length+"\0").update(v).digest("hex");};
const sha256=v=>createHash("sha256").update(v).digest("hex");
const fail=(s)=>{throw Error("P30_ORIGINAL_FIRST_CONTRACT:"+s);};
const fnv=s=>{let v=2166136261;for(const c of s)v=Math.imul(v^c.charCodeAt(0),16777619)>>>0;return v>>>0;};
export function preflight(arc){
 const manifest=decode(manifestFile),lock=decode(lockfile);
 if(blob(manifestFile)!==lock.manifest_blob)fail("MANIFEST_SHA");
 for(const [name,expected]of Object.entries(lock.source_blobs))
  if(blob(path.join(ROOT,name))!==expected)fail("SOURCE_BLOB:"+name);
 if(manifest.upstream_commit!==lock.upstream_commit)fail("UPSTREAM_DRIFT");
 const previouslyUsed=new Set();
 for(const prior of manifest.previous_manifest_files) {
  const p=path.join(ROOT,prior.path);
  if(blob(p)!==prior.blob)fail("PRIOR_MANIFEST_HASH:"+prior.path);
  const m=decode(p);
  if(m.ids.length!==prior.count)fail("PRIOR_MANIFEST_COUNT:"+prior.path);
  for(const id of m.ids)previouslyUsed.add(id);
 }
 if(previouslyUsed.size!==328||manifest.previous_unique_original_eval_files!==328)fail("REUSED_ORIGINAL_LEAK");
 const dir=path.join(arc,"data/evaluation");
 const files=fs.readdirSync(dir).filter(f=>f.endsWith(".json"));
 if(files.length!==400)fail("UPSTREAM_DATASET_SIZE");
 const fresh=files.filter(name=>!previouslyUsed.has(name));
 if(fresh.length!==72)fail("EXPECTED_FRESH_72");
 const chosen=fresh.map(name=>({name,h:fnv(manifest.seed+name)})).
  sort((a,b)=>a.h-b.h||a.name.localeCompare(b.name)).
  slice(0,48).map(x=>x.name);
 if(!eq(chosen,manifest.ids)||manifest.unconsumed_after_selection!==24)fail("COHORT_SELECTION_DRIFT");
 return {dir,manifest,lock};
}
export function first(arc) {
 const begin=process.hrtime.bigint(),v=preflight(arc),rows=[];
 for(const file of v.manifest.ids) {
  const raw=fs.readFileSync(path.join(v.dir,file));
  const task=JSON.parse(raw),train=task.train,input=task.test.map(t=>t.input);
  const started=process.hrtime.bigint();
  const B1=B.propose(train,input,"B").proposals;
  const B20=P20.propose(train,input).prediction;
  const B24=P24.solve(train,input).prediction;
  const B25=P25.solve(train,input).prediction;
  const B27=P27.synthesize(train,input,{selector:"classical",maxCandidates:P27.allASTs.length}).prediction;
  const B29=P29.synthesize(train,input).prediction;
  const old=[B1,B20,B24,B25,B27,B29];
  const eligible=old.filter(x=>x!==null);
  const oldConflict=eligible.length>1&&!eligible.every(p=>eq(p,eligible[0]));
  const oldConsensus=oldConflict?null:eligible[0]??null;
  const r=P30.propose(train,input),candidate=r.prediction;
  if(candidate!==null) {
   const program=r.trace.selected_program;
   if(!program||!train.every(p=>eq(P30.applyPipeline(program,p.input),p.output))||
      !input.every((g,i)=>eq(P30.applyPipeline(program,g),candidate[i])))
    fail("INDEPENDENT_EXECUTABLE_TRAIN_OR_TEST_REPLAY:"+file);
  }
  const safe=oldConflict?null:
   (oldConsensus!==null&&candidate!==null&&!eq(oldConsensus,candidate)?null:
    (oldConsensus??candidate));
  const compute_ms=Number(process.hrtime.bigint()-started)/1e6;
  // No reference/test gold is consulted for any proposer, only original scoring.
  const testGold=task.test.map(t=>t.output);
  const oldFlags=old.map(p=>exact(p,testGold));
  const oldGood=exact(oldConsensus,testGold),
       p30Good=exact(candidate,testGold),combinedGood=exact(safe,testGold);
  rows.push({
   id:file.slice(0,-5),source_json_sha256:sha256(raw),
   old_six_control_exact:oldFlags,
   old_consensus_conflict:oldConflict,
   old_consensus_submitted:oldConsensus!==null,
   old_consensus_correct:oldGood,
   p30_submitted:candidate!==null,
   p30_exact:p30Good,
   p30_wrong:candidate!==null&&!p30Good,
   p30_new_crop_generated:candidate!==null&&r.trace.source_of_prediction!=="identity_P29_same_source",
   p30_trace:r.trace,
   combined_submitted:safe!==null,combined_correct:combinedGood,combined_wrong:safe!==null&&!combinedGood,
   added_exact:combinedGood&&!oldGood,lost_exact:oldGood&&!combinedGood,
   control_union_exact:oldFlags.some(Boolean),
   time_ms:compute_ms
  });
 }
 const count=key=>rows.filter(x=>x[key]).length;
 const st={
  N:rows.length,legacy_six_classical_consensus_correct:count("old_consensus_correct"),
  legacy_any_of_six_oracle_union_exact:count("control_union_exact"),
  legacy_conflicts:count("old_consensus_conflict"),
  p30_correct:count("p30_exact"),p30_submitted:count("p30_submitted"),
  p30_new_wrong:count("p30_wrong"),p30_new_crop_generated:count("p30_new_crop_generated"),
  safe_combined_correct:count("combined_correct"),safe_combined_wrong:count("combined_wrong"),
  safe_combined_submitted:count("combined_submitted"),
  safe_added_exact:count("added_exact"),safe_lost_exact:count("lost_exact"),
  p30_fitting_programs:rows.filter(r=>r.p30_trace.selected_program!==null).length,
  p30_calls:rows.reduce((a,b)=>a+b.p30_trace.p29_calls,0),
  total_study_wall_ms:Number(process.hrtime.bigint()-begin)/1e6,
  energy_joules:null,cost_usd:null
 };
 const g=v.manifest.hard_gate;
 const passed=st.safe_added_exact>=g.new_P30_exact_vs_strong_5_classical_plus_P29_min&&
   st.p30_new_wrong<=g.P30_new_wrong_submissions_max&&
   st.safe_lost_exact<=g.existing_correct_lost_max&&
   st.safe_combined_wrong<=g.combined_new_wrong_max;
 return {schema:"neumann.q3.p30.first-unseen48-original.v1",
  source:"fchollet/ARC-AGI@"+v.manifest.upstream_commit,
  task_manifest_blob:v.lock.manifest_blob,
  previous_original_evaluation_excluded:328,untouched_eval_reserve:24,
  first_use_of_these_48_original_eval_task_bodies:true,
  original_test_gold_read_only_after_all_predictions:true,
  source_and_task_cohort_frozen_before_scoring:true,
  new_preprocessing_operators_human_defined:true,
  classical_TOOL_with_equal_P30_source_grammar_could_enumerate_same_candidates:true,
  no_neural_training:true,neural_calls:0,teacher_calls:0,
  science_status:passed?"LIMITED_SAME_DOMAIN_FRESH_TRANSFER_PASS_NOT_Q3":"P30_FIRST_UNSEEN_FAIL_OR_UNSAFE",
  Q3_autonomous_new_opcode:"NOT_PROVEN",
  Q6_unseen_semantic_family:"NOT_PROVEN",
  frontier_and_10x:"NOT_PROVEN",
  counts:st,rows};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==3){console.error("Usage: node experiments/q3_p30_first_unseen48.mjs ARC_ROOT");process.exitCode=2;}
 else {try{console.log(JSON.stringify(first(process.argv[2]),null,2));}
 catch(e){console.error(String(e.stack||e));process.exitCode=1;}}
}
