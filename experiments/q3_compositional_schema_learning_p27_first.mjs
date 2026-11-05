/* NEUMANN P2.7 | Preregistered first ORIGINAL ARC-AGI-1 evaluation.
 * Input manifests + source SHAs frozen before task bodies or TEST oracle are inspected.
 * Uses training corpus only for meta-policy, evaluation target outputs solely for scoreOriginal().
 */
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {createHash} from "node:crypto";
import {learnPrior,evaluateOriginal,aggregate} from "./q3_compositional_schema_learning_p27_scorer.mjs";
const ROOT=path.join(path.dirname(fileURLToPath(import.meta.url)),"..");
const load=p=>JSON.parse(fs.readFileSync(p,"utf8"));
const blobSha=file=>{
 const b=fs.readFileSync(file);
 return createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex");
};
const fnv32=s=>{let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619)>>>0;return h>>>0;};
function invariant(ok,reason){if(!ok)throw new Error("P27_SOURCE_OR_COHORT_CONTRACT_FAILURE: "+reason);}
export function verifyPinnedData(arcRoot){
 const lock=load(path.join(ROOT,"docs/experiments/q3_p27_SOURCE_FROZEN.json"));
 const cohortPath=path.join(ROOT,"docs/experiments/q3_p27_COHORT_FROZEN.json");
 const cohort=load(cohortPath);
 invariant(blobSha(cohortPath)===lock.cohort_sha,"COHORT_SHA");
 for(const [p,sha]of Object.entries(lock.sources))
  invariant(blobSha(path.join(ROOT,p))===sha,"SOURCE_SHA "+p);
 const evalDir=path.join(arcRoot,"data/evaluation"),trainDir=path.join(arcRoot,"data/training");
 const evalNames=fs.readdirSync(evalDir).filter(s=>s.endsWith(".json")),trainNames=fs.readdirSync(trainDir).filter(s=>s.endsWith(".json"));
 invariant(evalNames.length===400&&trainNames.length===400,"UPSTREAM_COUNT");
 const excluded=new Set();
 for(const item of cohort.previous_evaluation_manifest_files){
  const m=load(path.join(ROOT,"docs/experiments",item));
  for(const id of m.ids||[])excluded.add(id.endsWith(".json")?id:id+".json");
 }
 invariant(excluded.size===200&&cohort.previous_excluded_unique===200,"PRIOR_EVAL_EXCLUSION");
 const pool=evalNames.filter(name=>!excluded.has(name));
 const picked=pool.map(name=>({name,v:fnv32("neumann-q3-p27-preregistered-20261105|"+name)}))
  .sort((a,b)=>a.v-b.v||a.name.localeCompare(b.name)).slice(0,32).map(x=>x.name);
 invariant(JSON.stringify(picked)===JSON.stringify(cohort.ids),"COHORT_RESELECTION");
 invariant(cohort.ids.every(id=>!excluded.has(id)),"TASK_ALREADY_OPENED");
 invariant(lock.max_candidate_per_P27_arm===157&&lock.max_compose_depth===2,"BUDGET_DRIFT");
 return {cohort,trainNames:trainNames.sort(),evalDir,trainDir,lock};
}
export function runFirst(arcRoot){
 const started=process.hrtime.bigint(),v=verifyPinnedData(arcRoot);
 const tasks=v.trainNames.map(name=>load(path.join(v.trainDir,name)));
 const prior=learnPrior(tasks);
 invariant(prior.trainedTasks===400,"META_TRAIN_NOT_FULL");
 const priorSha=createHash("sha256").update(JSON.stringify(prior.prior)).digest("hex");
 const rows=[];
 for(const file of v.cohort.ids){
  const task=load(path.join(v.evalDir,file));
  const result=evaluateOriginal(task,prior.prior);
  rows.push({id:file.replace(".json",""),...result});
 }
 const scored=aggregate(rows,prior);
 return {
  ...scored,
  source_lock_sha:blobSha(path.join(ROOT,"docs/experiments/q3_p27_SOURCE_FROZEN.json")),
  cohort_sha:v.lock.cohort_sha,
  meta_prior_sha256:priorSha,
  meta_prior:prior.prior,
  first_result_date:"2026-11-05",
  full_runner_wall_ms:Number(process.hrtime.bigint()-started)/1e6,
  process_peak_rss_approx_bytes:process.memoryUsage().rss,
  evaluation_scope:"Official public ARC-AGI-1 data/evaluation. Previously unopened files at preregistering time; not sealed/private ARC-AGI-2.",
  status:scored.local_gate==="LOCAL_PASS_NOT_GLOBAL_Q3"?"LOCAL_PASS_NOT_GLOBAL":"FIRST_FAIL_OR_INCONCLUSIVE",
  Q3_autonomous_new_primitive:"NOT_PROVEN",
  Q3_unseen_semantic_family:"NOT_PROVEN",
  full_compute_cost_10x:"NOT_PROVEN"
 };
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(!process.argv[2]){process.stderr.write("Usage: node experiments/q3_compositional_schema_learning_p27_first.mjs <pinned-ARC-AGI-root>\n");process.exitCode=2;}
 else{try{process.stdout.write(JSON.stringify(runFirst(process.argv[2]),null,2)+"\n");}
  catch(err){process.stderr.write(String(err.stack||err)+"\n");process.exitCode=1;}}
}
