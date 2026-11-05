/** P2.9 public 400 training-task representation census.
 * Not a blind heldout test and NOT autonomous semantic invention.
 * Reveals whether greater search would help, or grammar lacks necessary logic.
 */
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import * as S from "./q3_p29_induced_coordinate_programs.mjs";
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export function census(arcRoot) {
 const started=process.hrtime.bigint();
 const dir=path.join(arcRoot,"data/training");
 const ids=fs.readdirSync(dir).filter(x=>x.endsWith(".json")).sort();
 if(ids.length!==400)throw Error("REQUIRE_OFFICIAL_PUBLIC_TRAINING_400");
 const rows=[];
 for(const file of ids) {
  const task=JSON.parse(fs.readFileSync(path.join(dir,file),"utf8"));
  const inputs=task.test.map(x=>x.input);
  const start=process.hrtime.bigint();
  const r=S.synthesize(task.train,inputs);
  if(r.prediction!==null){
   if(!r.trace.ast||!task.train.every(p=>eq(S.interpret(r.trace.ast,p.input),p.output)))
     throw Error("EXACT_TRAIN_REPLAY_FAIL:"+file);
  }
  // Read source test labels strictly AFTER proposal.
  const gold=task.test.map(x=>x.output);
  const exact=r.prediction!==null&&eq(r.prediction,gold);
  rows.push({id:file,train:task.train.length,test:task.test.length,
   shape_rule_found:r.trace.shapePrograms>0,
   unary_fits:r.trace.unaryFits,binary_fits:r.trace.binaryFits,
   train_fit:r.trace.unaryFits+r.trace.binaryFits>0,
   program:r.trace.ast,submitted:r.prediction!==null,correct:exact,
   false_submit:r.prediction!==null&&!exact,
   reason:r.trace.abstained,
   views:r.trace.coordinateViews,pairs:r.trace.geometryPairs,
   elapsed_ms:Number(process.hrtime.bigint()-start)/1e6});
 }
 const count=k=>rows.filter(x=>x[k]).length;
 const byReason=rows.reduce((a,x)=>(a[x.reason||"SUBMITTED"]=(a[x.reason||"SUBMITTED"]||0)+1,a),{});
 return {
  schema:"neumann.q3.p29.public-training-400-first-representation-audit.v1",
  source:"fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34",
  task_set:"data/training; OPENED DEVELOPMENT, NOT UNSEEN EVALUATION",
  P29_is_classical_human_metagrammar:true,
  no_neural_training:true,no_teacher_calls:true,
  test_gold_read_after_proposal:true,
  stats:{N:rows.length,shape_rule_found:count("shape_rule_found"),
   train_fit:count("train_fit"),submitted:count("submitted"),correct:count("correct"),
   false_submit:count("false_submit"),
   total_coordinate_views:rows.reduce((a,x)=>a+x.views,0),
   total_geometry_pairs:rows.reduce((a,x)=>a+x.pairs,0),
   runtime_ms:Number(process.hrtime.bigint()-started)/1e6},
  reasons:byReason,rows,
  Q3:"OPEN",Q6:"OPEN",Q7:"OPEN"
 };
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==3)throw Error("Usage: node experiments/q3_p29_training400_census.mjs ARC_ROOT");
 try{console.log(JSON.stringify(census(process.argv[2]),null,2));}
 catch(e){console.error(String(e.stack||e));process.exitCode=1;}
}
