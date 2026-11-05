/* NEUMANN P2.8 STOP CONTRACT: distinguish selection from representability.
 * Based only on the immutable P2.7 FIRST receipt + original TRAIN inputs/outputs.
 * Rebuild the entire P2.7 hypothesis class independently; never run a new
 * official evaluation or read evaluation TEST gold in this proof.
 */
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import {fileURLToPath} from "node:url";
import {allASTs,executeGeometry} from "./q3_compositional_schema_learning_p27.mjs";

export const FIRST_SHA256="c472a96a4b1dc1cbe5e8292323a69455a1ac4deec2c38e27ac3c887a74346671";
export const PINNED_ARC_COMMIT="399030444e0ab0cc8b4e199870fb20b863846f34";
export const CONTRACT=Object.freeze({
  schema:"neumann.q3.p28.rankers-cannot-repair-empty-language.v1",
  firstReceiptSha256:FIRST_SHA256,originalTaskCount:32,metaTrainingTasks:400,
  completeProgramsPerTask:157,metaSuccessCount:9,metaDistinctMacros:6,
  expectationNoTrainFit:31,expectationFitsButUnsupported:1,
  gate:"STOP_FIXED_H_RANKING",globalQ1Q7:"OPEN"
});
const assert=(c,msg)=>{if(!c)throw new Error("GATE_FAIL:"+msg);};
const read=p=>JSON.parse(fs.readFileSync(p,"utf8"));
const hash=x=>crypto.createHash("sha256").update(x).digest("hex");
function fitsTRAIN(train,ops){
  const mapping=new Map(),frequency=new Map();
  for(const p of train){
    const g=executeGeometry(p.input,ops);
    if(g===null||g.length!==p.output.length||g[0].length!==p.output[0].length)return false;
    for(let r=0;r<g.length;r++)for(let c=0;c<g[0].length;c++){
      const x=g[r][c],y=p.output[r][c];
      if(mapping.has(x)&&mapping.get(x)!==y)return false;
      mapping.set(x,y);frequency.set(x,1+(frequency.get(x)||0));
    }
  }
  return [...frequency.values()].every(x=>x>=2);
}
export function proof(arcRepoRoot,receiptPath,{checkTrainOnly=true}={}){
  assert(checkTrainOnly===true,"MUST_VERIFY_TRAIN_ONLY");
  const bytes=fs.readFileSync(receiptPath);
  assert(hash(bytes)===FIRST_SHA256,"FIRST_RECEIPT_CHANGED");
  const first=JSON.parse(bytes);
  const here=path.dirname(fileURLToPath(import.meta.url));
  const root=path.join(here,"..");
  const cohort=read(path.join(root,"docs/experiments/q3_p27_COHORT_FROZEN.json"));
  const lock=read(path.join(root,"docs/experiments/q3_p27_SOURCE_FROZEN.json"));
  assert(cohort.upstream_commit===PINNED_ARC_COMMIT&&lock.upstream_commit===PINNED_ARC_COMMIT,"SOURCE_CHANGED");
  assert(allASTs.length===CONTRACT.completeProgramsPerTask,"PROGRAM_CLASS_CHANGED");
  assert(first.stats.task_count===32&&first.stats.meta_training_tasks===400,"COUNTS_CHANGED");
  assert(first.rows.length===32&&cohort.ids.length===32,"COHORT_LENGTH");
  assert(JSON.stringify(first.rows.map(r=>r.id))===JSON.stringify(cohort.ids.map(id=>id.replace(".json",""))),"COHORT_ORDER_CHANGED");
  const prior=first.meta_prior;
  const metaTotal=Object.values(prior).flatMap(x=>Object.values(x)).reduce((a,b)=>a+b,0);
  const distinct=Object.values(prior).reduce((n,x)=>n+Object.keys(x).length,0);
  assert(metaTotal===9&&distinct===6,"META_SIGNAL_CHANGED");
  let noFit=0,oneFit=0,fitTotal=0,manualReadCount=0;
  const rows=[];
  for(const row of first.rows){
    const task=read(path.join(arcRepoRoot,"data/evaluation",row.id+".json"));
    // Deliberately project the original task to TRAIN only.
    const train=task.train;
    manualReadCount+=train.length;
    let numberOfFitted=0;
    for(const ops of allASTs)if(fitsTRAIN(train,ops))numberOfFitted++;
    assert(numberOfFitted===row.classical_trace.train_fit_count,
        "TRAIN_FITS_DIVERGED:"+row.id);
    assert(numberOfFitted===row.learned_trace.train_fit_count,
        "LEARNED_FITS_DIVERGED:"+row.id);
    assert(row.classical_trace.geometry_attempts===157&&
           row.learned_trace.geometry_attempts===157,"RANKING_BUDGET_DIVERGED:"+row.id);
    if(numberOfFitted===0)noFit++;else if(numberOfFitted===1)oneFit++;
    fitTotal+=numberOfFitted;
    rows.push({id:row.id,full_candidate_space:157,train_fit_count:numberOfFitted,
      selector_independently_cannot_add_train_fit:numberOfFitted===0,
      train_example_count:train.length,
      original_test_gold_read_by_proof:false});
  }
  assert(noFit===31&&oneFit===1&&fitTotal===1,"CEILING_COUNTS_CHANGED");
  assert(first.rows.every(r=>r.classical_trace.selected_AST===null&&r.learned_trace.selected_AST===null),"NEW_PROGRAM_APPEARED");
  assert(first.stats.classical_exact===0&&first.stats.learned_exact===0&&
    first.stats.learned_new_correct_vs_baseline===0,"FIRST_RESULT_MISREPRESENTED");
  const condition= "If H_D = {h in H | h exactly fits TRAIN} is empty, any selector with support restricted to H has zero TRAIN-fitting proposals. Ranking, reweighting, more retries, or neural scoring alone cannot alter this.";
  return {
    schema:CONTRACT.schema,read_only:true,original_first_raw_sha256:hash(bytes),
    original_source_commit:PINNED_ARC_COMMIT,original_count:rows.length,
    programs_per_task:157,programs_independently_rechecked:rows.length*157,
    no_fit:numberOfRows(rows,x=>x.train_fit_count===0),
    exactly_one_fit:numberOfRows(rows,x=>x.train_fit_count===1),
    other_fit:numberOfRows(rows,x=>x.train_fit_count>1),
    training_examples_read:manualReadCount,test_gold_read:false,
    meta_total_public_training_tasks:400,meta_correct_tasks:metaTotal,
    meta_distinct_macro_keys:distinct,meta_positive_fraction:metaTotal/400,
    first_original_correct_legacy:first.stats.baseline_exact,
    first_original_correct_classical:first.stats.classical_exact,
    first_original_correct_learned:first.stats.learned_exact,
    theorem:condition,
    research_decision:"STOP_FIXED_H_RANKING",
    recommendation:"Do not spend further official evaluation or training compute on a prior/ranker until a frozen new representation has independent generalization evidence under matched classical control.",
    global_q1_q7:"OPEN",
    scope:"P2.7 human-authored fixed 157 ASTs; already opened public ARC-AGI-1 32; NOT an ARC universal impossibility theorem or 10x performance.",
    rows
  };
}
const numberOfRows=(rows,fn)=>rows.filter(fn).length;
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const [arc,receipt]=process.argv.slice(2);
  if(!arc||!receipt){process.stderr.write("Usage: node experiments/q3_p28_ranker_ceiling_gate.mjs ARC_ROOT FIRST_RECEIPT\n");process.exitCode=2;}
  else try{process.stdout.write(JSON.stringify(proof(arc,receipt),null,2)+"\n");}
  catch(e){process.stderr.write(String(e.stack||e)+"\n");process.exitCode=1;}
}
