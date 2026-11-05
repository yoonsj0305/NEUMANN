/* P3.0 first source-frozen public 400 training ORIGINAL diagnostic.
 * Not blind eval, not cross-family transfer. Every candidate generated from
 * only TRAIN examples and TEST inputs, then exact original test score.
 */
import fs from "node:fs";
import path from "node:path";
import {createHash} from "node:crypto";
import {fileURLToPath} from "node:url";
import {synthesize,interpret} from "./q3_p30_object_rewrite_language.mjs";
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const json=p=>JSON.parse(fs.readFileSync(p,"utf8"));
const blob=p=>{const b=fs.readFileSync(p);return createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex");};
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export function first(arcRoot) {
 const lock=json(path.join(ROOT,"docs/experiments/q3_p30_PUBLIC_TRAIN400_SOURCE_LOCK.json"));
 for(const [file,sha]of Object.entries(lock.source_blobs))
   if(blob(path.join(ROOT,file))!==sha)throw Error("P30_SOURCE_DRIFT:"+file);
 const original=path.join(arcRoot,"data/training");
 const names=fs.readdirSync(original).filter(x=>x.endsWith(".json")).sort();
 if(names.length!==400)throw Error("OFFICIAL_400_TRAINING_EXPECTED");
 const started=process.hrtime.bigint(),rows=[];
 for(const file of names){
   const task=json(path.join(original,file));
   const inputs=task.test.map(x=>x.input);
   const result=synthesize(task.train,inputs);
   const candidate=result.prediction;
   if(candidate!==null){
      const ast=result.trace.selected;
      if(!ast||!task.train.every(x=>eq(interpret(ast,x.input),x.output)))
        throw Error("EXACT_SOURCE_TRAIN_REPLAY_FAILED:"+file);
      if(!inputs.every((x,i)=>eq(interpret(ast,x),candidate[i])))
        throw Error("EXACT_SOURCE_TEST_REPLAY_FAILED:"+file);
   }
   // Gold is first read only AFTER generated program + verification.
   const gold=task.test.map(x=>x.output);
   const correct=candidate!==null&&eq(candidate,gold);
   rows.push({id:file,train:task.train.length,test:task.test.length,
    program:result.trace.selected,
    train_fit:result.trace.trainFitted>0,
    submitted:candidate!==null,correct,false_submit:candidate!==null&&!correct,
    reason:result.trace.status,candidates:result.trace.attempted,
    train_replays:result.trace.trainReplay,wall_ms:result.trace.wallMs});
 }
 const count=k=>rows.filter(x=>x[k]).length;
 return {schema:"neumann.q3.p30.first-public-original-training400.v1",
  source:"fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34",
  scope:"OPENED_ORIGINAL_TRAINING_NOT_FRESH_HOLDOUT",
  source_lock_git_blob:blob(path.join(ROOT,"docs/experiments/q3_p30_PUBLIC_TRAIN400_SOURCE_LOCK.json")),
  prior_test_gold_not_visible_to_proposer:true,
  human_supplied_object_rewrite_metagrammar:true,
  neural_calls:0,teacher_calls:0,autonomous_new_opcode:"NOT_PROVEN",
  stats:{N:rows.length,train_fit:count("train_fit"),submitted:count("submitted"),
   correct:count("correct"),false_submit:count("false_submit"),
   abstentions:rows.length-count("submitted"),
   candidates:rows.reduce((sum,x)=>sum+x.candidates,0),
   train_replays:rows.reduce((sum,x)=>sum+x.train_replays,0),
   total_wall_ms:Number(process.hrtime.bigint()-started)/1e6},
  rows};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==3)throw Error("node experiments/q3_p30_public400_first.mjs ARC_ROOT");
 try{process.stdout.write(JSON.stringify(first(process.argv[2]),null,2)+"\n");}
 catch(e){process.stderr.write(String(e.stack||e)+"\n");process.exitCode=1;}
}
