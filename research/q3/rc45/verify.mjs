// RC45 evidence replay. Node >=18, no packages. All upstream ARC records SHA1 verified.
// The after-grade replay does NOT make a new first prediction.
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
import {op} from "./solver.mjs";
import {op2} from "./adaptation.mjs";
import {dispatch17} from "./dispatch17.mjs";
const here=new URL(".",import.meta.url);
const read=(x)=>JSON.parse(readFileSync(new URL(x,here),"utf8"));
const first=read("first_predictions.json").first;
const second=read("first_adapted_predictions.json").first;
const reuse=read("first_reuse_predictions.json").first;
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const assert=(ok,msg)=>{if(!ok)throw Error(msg)};
assert(first.length===12&&second.length===12&&reuse.length===12,"exact 12 per cohort");
assert(new Set([...first,...second,...reuse].map(x=>x.id)).size===36,"no shared tasks");
assert(first.filter(x=>x.source_fit==="SOURCE_FIT").length===9,"first frozen admission");
assert(second.filter(x=>x.status==="SOURCE_FIT").length===8,"second frozen admission");
assert(reuse.every(x=>x.status==="UNKNOWN_NO_SOURCE_FIT"&&x.first_predictions===null),"prospective 0/12 abstention");
async function official(x) {
 const url="https://raw.githubusercontent.com/arcprize/ARC-AGI-2/f3283f727488ad98fe575ea6a5ac981e4a188e49/data/training/"+x.id+".json";
 const resp=await fetch(url,{headers:{"User-Agent":"NEUMANN1-rc45-verifier"}});
 assert(resp.ok,"download "+x.id+" HTTP "+resp.status);
 const raw=Buffer.from(await resp.arrayBuffer());
 const gitHash=createHash("sha1").update(Buffer.concat([Buffer.from("blob "+raw.length+"\0"),raw])).digest("hex");
 assert(gitHash===x.blob_sha1,"official pinned blob SHA mismatch: "+x.id);
 return JSON.parse(raw.toString("utf8"));
}
async function grade(records, fn,field) {
 let tasks=0, tests=0,cells=0;
 for(const x of records) {
   if(x[field]!=="SOURCE_FIT")continue;
   const d=await official(x);
   assert(d.train.every(y=>eq(fn(x.id,y.input),y.output)),"train mismatch "+x.id);
   assert(x.first_predictions.length===d.test.length,"test cardinality "+x.id);
   tasks++;
   d.test.forEach((y,i)=>{
     assert(eq(fn(x.id,y.input),x.first_predictions[i]),"replay prediction mismatch "+x.id);
     assert(eq(x.first_predictions[i],y.output),"first prediction wrong "+x.id);
     tests++;
     cells+=y.output.flat().length;
   });
 }
 return {tasks,tests,cells};
}
async function verifyReuse() {
 for(const x of reuse) {
   const d=await official(x);
   // Intentionally score no official test gold for this cohort.
   const inputOnly={train:d.train,test:d.test.map(t=>({input:t.input}))};
   const result=dispatch17(inputOnly);
   assert(result.status===x.status&&eq(result.compatible,x.operators),"transfer mismatch "+x.id);
   assert(result.status==="UNKNOWN_NO_SOURCE_FIT","unexpected test admission "+x.id);
 }
 return {admitted:0,unknown:12};
}
const online=process.argv.includes("--online");
if(online){
 const a=await grade(first,op,"source_fit");
 const b=await grade(second,op2,"status");
 const c=await verifyReuse();
 assert(a.tasks===9&&a.tests===9&&a.cells===389,"cohort one exact totals");
 assert(b.tasks===8&&b.tests===9&&b.cells===344,"cohort two exact totals");
 console.log(JSON.stringify({status:"REPRO_PASS",first:a,adapted:b,prospective:c,all_first_exact:18,all_cells:733}));
}else{
 console.log(JSON.stringify({status:"FROZEN_RECEIPT_SHAPE_PASS",source_admission_first:9,source_admission_adapted:8,prospective_abstention:12,full_external_gold_replay:"NOT_RUN; use --online"}));
}
