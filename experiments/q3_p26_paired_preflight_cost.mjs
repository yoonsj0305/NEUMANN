/* NEUMANN P2.6.1: paired same-runner cost of P2.5 failed search vs
 * train-only P2.6 representability preflight on the ALREADY OPENED 31 cases.
 * NOT a heldout performance claim. NO test gold and NO changed solver outputs.
 */
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {auditCohort,auditTask} from "./q3_p25_representability_ceiling_p26.mjs";
import {solve as p25Solve} from "./q3_generated_decision_trees_p25.mjs";
const HERE=path.dirname(fileURLToPath(import.meta.url));
const read=p=>JSON.parse(fs.readFileSync(p,"utf8"));
const ms=(a,b)=>Number(b-a)/1e6;
function measure(fn){
 const a=process.hrtime.bigint(),v=fn(),b=process.hrtime.bigint();
 return {elapsed_ms:ms(a,b),value:v};
}
export function compare(arcRoot){
 const cert=auditCohort(arcRoot); // Exact SHA/source/receipt checks excluded from timed region.
 const coh=read(path.join(HERE,"../docs/experiments/q3_generated_decision_trees_p25_COHORT_FROZEN.json"));
 const receipt=read(path.join(HERE,"../docs/experiments/results/q3_generated_decision_trees_p25_FIRST_COMPLETE.json"));
 const known=new Map(receipt.rows.map(x=>[x.id,x]));
 const rows=[];
 for(let i=0;i<coh.ids.length;i++){
  const filename=coh.ids[i],id=filename.replace(/\.json$/,""),prior=known.get(id);
  if(prior.baseline_exact)continue;
  const task=read(path.join(arcRoot,"data/evaluation",filename));
  const times={p25:[],preflight:[]};
  for(let rep=0;rep<2;rep++){
   const order=(i+rep)%2===0?["preflight","p25"]:["p25","preflight"];
   for(const variant of order){
    if(variant==="p25"){
     const run=measure(()=>p25Solve(task.train,task.test.map(x=>x.input)));
     if(run.value.prediction!==null||run.value.trace.train_exact_candidates!==0)
      throw new Error("P25_FIRST_RECEIPT_DRIFT "+id);
     times.p25.push(run.elapsed_ms);
    }else{
     const run=measure(()=>auditTask({train:task.train}));
     if(!run.value.verdict.startsWith("PROVED_"))throw new Error("PREFLIGHT_NOT_SOUND "+id);
     times.preflight.push(run.elapsed_ms);
    }
   }
  }
  rows.push({id,original_p25_train_fits:prior.P25_trace.train_exact_candidates,
   preflight_cert:cert.rows.find(x=>x.id===id).verdict,
   p25_ms:times.p25,preflight_ms:times.preflight});
 }
 const sums={p25_ms:rows.reduce((v,x)=>v+x.p25_ms.reduce((a,b)=>a+b,0),0),
  preflight_ms:rows.reduce((v,x)=>v+x.preflight_ms.reduce((a,b)=>a+b,0),0)};
 return {schema:"neumann.q3.p261.paired-preflight-cost.v1",
  scope:"Opened public ARC cohort, failed P25 calls only, two interleaved orders per task. NOT all-in 10x proof.",
  environment:"Single GitHub Actions runner, Node process.hrtime.bigint. Input file reads, source verification, CI/setup excluded.",
  original_tasks:coh.ids.length,baseline_solved:1,compared_unsolved_tasks:rows.length,
  repetitions_per_variant:2,source_commit:coh.source_commit,
  ...sums,p25_over_preflight_ratio:sums.p25_ms/sums.preflight_ms,
  neural_calls:0,teacher_calls:0,all_predictions_abstained:true,rows};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{if(!process.argv[2])throw new Error("Usage: node experiments/q3_p26_paired_preflight_cost.mjs <ARC-root>");
  process.stdout.write(JSON.stringify(compare(process.argv[2]),null,2)+"\n");}
 catch(e){process.stderr.write(String(e.stack||e)+"\n");process.exitCode=1;}
}
