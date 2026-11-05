/* P3.0 opened ORIGINAL TRAIN400 representation and classical headroom.
 * No new original evaluation files consumed. This is OPENED model development.
 * Original P29 and strongest five-classical baseline receipts remain immutable.
 */
import fs from "node:fs";
import path from "node:path";
import {createHash} from "node:crypto";
import {fileURLToPath} from "node:url";
import * as P30 from "./q3_p30_object_relational_recolor.mjs";
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const sha=b=>createHash("sha256").update(b).digest("hex");
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function loadReport(file,expected){
 const bytes=fs.readFileSync(file),json=JSON.parse(bytes);
 if(json.rows?.length!==400)throw Error("WRONG_400_REFERENCE:"+file);
 if(expected&&sha(bytes)!==expected)throw Error("PRIOR_FIRST_SHA_DRIFT:"+file);
 return json;
}
export function census(arc,p29File,matchedFile) {
 const started=process.hrtime.bigint();
 const p29=loadReport(p29File,"d26186c52c2b3f6f7c969476aeeef47ff55dff3c026d220ee6e7a51a3670651a");
 const matched=loadReport(matchedFile);
 const names=fs.readdirSync(path.join(arc,"data/training")).filter(x=>x.endsWith(".json")).sort();
 if(names.length!==400)throw Error("UPSTREAM_400_SOURCE_CHANGED");
 const rows=[];
 for(let i=0;i<names.length;i++) {
   const name=names[i],ref=p29.rows[i],base=matched.rows[i];
   if(ref.id!==name||base.id!==name)throw Error("SOURCE_IDENTITY_DRIFT:"+name);
   const task=JSON.parse(fs.readFileSync(path.join(arc,"data/training",name),"utf8"));
   const testInputs=task.test.map(t=>t.input);
   const r=P30.synthesize(task.train,testInputs);
   if(r.prediction!==null) {
     if(r.trace.ast===null||!task.train.every(x=>eq(P30.execute(r.trace.ast,x.input),x.output)))
       throw Error("P30_TRAIN_REPLAY_FAIL:"+name);
     if(!testInputs.every((x,k)=>eq(P30.execute(r.trace.ast,x),r.prediction[k])))
       throw Error("P30_TEST_REPLAY_FAIL:"+name);
   }
   // Gold only AFTER P3.0 proposal, P2.9 and old baseline receipts immutable.
   const gold=task.test.map(t=>t.output);
   const exact=r.prediction!==null&&eq(r.prediction,gold);
   const oldCorrect=base.old_exact||ref.correct;
   rows.push({id:name,train:task.train.length,oldCorrect,priorP29:ref.correct,
    P30_submitted:r.prediction!==null,P30_correct:exact,
    P30_wrong:r.prediction!==null&&!exact,P30_newCorrect:exact&&!oldCorrect,
    trace:r.trace});
 }
 const count=k=>rows.filter(x=>x[k]).length;
 return {schema:"neumann.q3.p30.train400-opened-original-headroom.v1",
  source:"fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34/data/training",
  first_p29_sha256:"d26186c52c2b3f6f7c969476aeeef47ff55dff3c026d220ee6e7a51a3670651a",
  matched_old_sha256:sha(fs.readFileSync(matchedFile)),
  scope:"OPENED_PUBLIC_400_TRAINING_DIAGNOSTIC_ONLY",
  human_specified_relational_rule_family:true,zero_model_calls:true,zero_training_updates:true,
  gold_read_only_after_program_selection:true,
  stats:{N:400,oldCombined:count("oldCorrect"),P30_submitted:count("P30_submitted"),
    P30_correct:count("P30_correct"),P30_wrong:count("P30_wrong"),
    additionalOverP29AndFiveClassical:count("P30_newCorrect"),
    P30_trainFit:rows.filter(x=>x.trace.trainConsistent>0).length,
    P30_ambiguous:rows.filter(x=>x.trace.reason==="AMBIGUOUS_MIN_COST_OBJECT_RELATION").length,
    totalCandidatePrograms:rows.reduce((s,r)=>s+r.trace.candidatePrograms,0),
    totalWallMs:Number(process.hrtime.bigint()-started)/1e6},
  rows,Q3:"OPEN",Q6:"OPEN",frontier:"OPEN",cost10x:"NOT_PROVEN"};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==5)throw Error("node experiments/q3_p30_training400_census.mjs ARC_ROOT P29_FIRST MATCHED_FIRST");
 try{console.log(JSON.stringify(census(process.argv[2],process.argv[3],process.argv[4]),null,2));}
 catch(e){console.error(String(e.stack||e));process.exitCode=1;}
}
