/* NEUMANN 1 P2.6: falsifiable representability ceiling for the frozen P2.5 public cohort.
 * This is a proof of a PARTICULAR source language's limits, not of ARC in general.
 * NO TEST GOLD, new solver, model call, or adaptive search.
 */
import fs from "node:fs";
import path from "node:path";
import {createHash} from "node:crypto";
import {fileURLToPath} from "node:url";
import {inGrid,modeOutput} from "./q3_cached_typed_guard_p24.mjs";
import {createExamples,featureSet,CONTRACT as P25} from "./q3_generated_decision_trees_p25.mjs";

export const MODES=Object.freeze(["same","half_lr","half_tb","shift_0_-1","shift_0_1","shift_-1_0","shift_1_0"]);
export const SCHEMA="neumann.q3.p26.p25-representability-ceiling.v1";
const HERE=path.dirname(fileURLToPath(import.meta.url));
const ROOT=path.join(HERE,"..");
const COHORT_FILE=path.join(ROOT,"docs/experiments/q3_generated_decision_trees_p25_COHORT_FROZEN.json");
const RECEIPT_FILE=path.join(ROOT,"docs/experiments/results/q3_generated_decision_trees_p25_FIRST_COMPLETE.json");

function matchesShape(mode,train){
 return train.every(p=>{
  const sh=modeOutput(mode,p.input);
  return sh!==null&&p.output.length===sh.H&&p.output[0].length===sh.W;
 });
}
function witnessByFeatureCollision(rows,train){
 const f=featureSet(rows,train);
 const seen=new Map();
 let count=0,first=null;
 for(let i=0;i<rows.length;i++){
  // Include both action-source values as well as every Boolean branch feature.
  // This is a SUPERSET of the information visible to P2.5, making a collision
  // a sound impossibility witness even for unlimited depth/beam.
  const sig=JSON.stringify([rows[i].ctx.a,rows[i].ctx.b,...f.values.map(col=>col[i]?1:0)]);
  const prior=seen.get(sig);
  if(prior && prior.target!==rows[i].target){
   count++;
   if(first===null)first={
    first_row:prior.index,second_row:i,
    first_target:prior.target,second_target:rows[i].target,
    signature_sha256:createHash("sha256").update(sig).digest("hex")
   };
  }else if(!prior)seen.set(sig,{target:rows[i].target,index:i});
 }
 return {collisions:count,first_witness:first,unique_augmented_signatures:seen.size,feature_count:f.keys.length};
}
export function auditTask(task){
 if(!task||!Array.isArray(task.train)||!task.train.length||
    !task.train.every(p=>inGrid(p.input)&&inGrid(p.output))){
  throw new Error("INVALID_TRAIN");
 }
 const modes=[];
 for(const mode of MODES){
  if(!matchesShape(mode,task.train))continue;
  const rows=createExamples(task.train,mode);
  if(rows===null){
   modes.push({mode,status:"ROW_CAP_OR_UNSUPPORTED",collisions:null});
   continue;
  }
  const {collisions,first_witness,unique_augmented_signatures,feature_count}=witnessByFeatureCollision(rows,task.train);
  modes.push({mode,status:collisions>0?"FEATURE_COLLISION":"NOT_DISPROVED",
   training_rows:rows.length,collisions,first_witness,unique_augmented_signatures,feature_count});
 }
 const verdict=modes.length===0?"PROVED_SHAPE_IMPOSSIBLE":
  modes.every(m=>m.status==="FEATURE_COLLISION")?"PROVED_FEATURE_COLLISION_ALL_SHAPE_MODES":
  "NOT_PROVED";
 return {verdict,shape_compatible_modes:modes.length,modes};
}
export function gitBlobSha(file){
 const bytes=fs.readFileSync(file);
 return createHash("sha1").update("blob "+bytes.length+"\0").update(bytes).digest("hex");
}
function verifyFrozenSources(cohort){
 const files={P25:path.join(HERE,"q3_generated_decision_trees_p25.mjs"),
              P24:path.join(HERE,"q3_cached_typed_guard_p24.mjs")};
 for(const [k,file]of Object.entries(files)){
  const actual=gitBlobSha(file);
  if(actual!==cohort.code_sha[k])throw new Error("SOURCE_SHA_MISMATCH "+k+" "+actual);
 }
 if(cohort.source_commit!=="399030444e0ab0cc8b4e199870fb20b863846f34")throw new Error("SOURCE_COMMIT_DRIFT");
}
export function auditCohort(arcRoot,{cohortFile=COHORT_FILE,receiptFile=RECEIPT_FILE}={}){
 const cohort=JSON.parse(fs.readFileSync(cohortFile,"utf8"));
 const receipt=JSON.parse(fs.readFileSync(receiptFile,"utf8"));
 verifyFrozenSources(cohort);
 if(cohort.ids.length!==32||receipt.original_task_count!==32)throw new Error("COHORT_SIZE_CHANGED");
 if(receipt.cohort_sha!==gitBlobSha(cohortFile))throw new Error("COHORT_SHA_MISMATCH");
 const rows=[],known=new Map(receipt.rows.map(r=>[r.id,r]));
 for(const filename of cohort.ids){
  const id=filename.replace(/\.json$/,"");
  const localFile=path.join(arcRoot,"data","evaluation",filename);
  const task=JSON.parse(fs.readFileSync(localFile,"utf8"));
  const scan=auditTask({train:task.train}); // test outputs are NEVER read
  const prior=known.get(id);
  if(!prior)throw new Error("RECEIPT_ID_MISSING "+id);
  if(!prior.baseline_exact && prior.P25_trace?.modes!==scan.modes.filter(m=>m.status!=="ROW_CAP_OR_UNSUPPORTED").length){
   throw new Error("P25_MODE_TRACE_MISMATCH "+id);
  }
  rows.push({id,baseline_exact:prior.baseline_exact,...scan});
 }
 const notSolved=rows.filter(r=>!r.baseline_exact);
 const noShape=notSolved.filter(r=>r.verdict==="PROVED_SHAPE_IMPOSSIBLE");
 const collision=notSolved.filter(r=>r.verdict==="PROVED_FEATURE_COLLISION_ALL_SHAPE_MODES");
 const unproved=notSolved.filter(r=>r.verdict==="NOT_PROVED");
 const output={
  schema:SCHEMA,
  cohort_sha:gitBlobSha(cohortFile),
  source_commit:cohort.source_commit,
  P25_sha:cohort.code_sha.P25,P24_sha:cohort.code_sha.P24,
  original_count:rows.length,baseline_solved:rows.filter(r=>r.baseline_exact).length,
  P25_unsolved:notSolved.length,
  disproved_by_shape:noShape.length,
  disproved_by_feature_collision:collision.length,
  not_disproved:unproved.length,
  conclusion:(noShape.length+collision.length===notSolved.length)?
   "P25_CANNOT_ADD_ANY_TRAIN_CONSISTENT_PROGRAM_ON_THIS_FROZEN_COHORT":
   "SOME_TASKS_NOT_PROVED_INEXPRESSIBLE",
  scope:"TRAIN-only proof for frozen P25 modes/features/actions. Not ARC impossibility, frontier or 10x evidence.",
  rows
 };
 if(output.original_count!==32||output.baseline_solved!==1||output.disproved_by_shape!==9||
    output.disproved_by_feature_collision!==22||output.not_disproved!==0){
  throw new Error("FROZEN_COHORT_EXPECTATION_FAILURE "+JSON.stringify({
   original_count:output.original_count,baseline_solved:output.baseline_solved,
   shape:output.disproved_by_shape,feature:output.disproved_by_feature_collision,unknown:output.not_disproved}));
 }
 return output;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const root=process.argv[2];
 if(!root){process.stderr.write("Usage: node experiments/q3_p25_representability_ceiling_p26.mjs <pinned-ARC-AGI-root>\n");process.exitCode=2;}
 else{
  try{process.stdout.write(JSON.stringify(auditCohort(root),null,2)+"\n");}
  catch(e){process.stderr.write(String(e.stack||e)+"\n");process.exitCode=1;}
 }
}
