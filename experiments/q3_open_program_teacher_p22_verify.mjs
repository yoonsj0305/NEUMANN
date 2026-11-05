/* P2.2 independent reproducibility runner, research-only.
 * Usage: node experiments/q3_open_program_teacher_p22_verify.mjs /path/to/ARC-AGI/data/evaluation
 * Requires official pinned public ARC-AGI-1 evaluation JSON files in that directory.
 * Never overwrites or modifies the immutable first score.
 * Source identity is checked before dynamic import of the frozen, trusted teacher module.
 * This is NOT an untrusted code sandbox. Do not run arbitrary generated programs.
 */
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
import {fileURLToPath, pathToFileURL} from "node:url";
import {join, resolve} from "node:path";

function exactGrid(a,b){
 if(!Array.isArray(a)||!Array.isArray(b)||a.length===0||a.length!==b.length)return false;
 for(let r=0;r<a.length;r++){
  if(!Array.isArray(a[r])||!Array.isArray(b[r])||a[r].length===0||a[r].length!==b[r].length)return false;
  for(let c=0;c<a[r].length;c++)if(a[r][c]!==b[r][c])return false;
 }
 return true;
}
function gitBlobSha(bytes){
 const prefix=Buffer.from("blob "+bytes.length+"\0","utf8");
 return createHash("sha1").update(prefix).update(bytes).digest("hex");
}
function assess(prog,task){
 // Create all proposals BEFORE accessing TEST output labels for scoring.
 const originalTrain=task.train.map(p=>({input:p.input,output:p.output}));
 const inputOnly=task.test.map(p=>p.input);
 if(typeof prog!=="function")return {submitted:false,trainExact:false,testExact:false,falseAccept:false,trainCount:originalTrain.length,testCount:inputOnly.length,exception:null};
 let trainPreds=[],testPreds=[],exception=null;
 try{trainPreds=originalTrain.map(p=>prog(p.input));testPreds=inputOnly.map(p=>prog(p));}catch(e){exception=String(e);}
 // Scoring starts here. TEST labels were inaccessible to prog.
 const trainExact=exception===null&&trainPreds.length===originalTrain.length&&trainPreds.every((p,i)=>exactGrid(p,originalTrain[i].output));
 const originalTestTargets=task.test.map(t=>t.output);
 const testExact=trainExact&&testPreds.length===originalTestTargets.length&&testPreds.every((p,i)=>exactGrid(p,originalTestTargets[i]));
 return {submitted:true,trainExact,testExact,falseAccept:trainExact&&!testExact,trainCount:originalTrain.length,testCount:inputOnly.length,exception};
}
async function verify(originalDir,baseUrl=new URL("./",import.meta.url)){
 const dir=resolve(originalDir);
 const sourceUrl=new URL("q3_open_program_teacher_p22_FIRST_PROPOSAL.mjs",baseUrl);
 const sourceBytes=readFileSync(fileURLToPath(sourceUrl));
 const evidenceRoot=new URL("../docs/experiments/",baseUrl);
 const first=JSON.parse(readFileSync(fileURLToPath(new URL("results/q3_open_program_teacher_p22_FIRST_SCORE.json",evidenceRoot)),"utf8"));
 const manifest=JSON.parse(readFileSync(fileURLToPath(new URL("q3_open_program_teacher_p22_COHORT_FROZEN.json",evidenceRoot)),"utf8"));
 const blob=gitBlobSha(sourceBytes);
 if(blob!==first.first_teacher_source_sha)throw Error("FROZEN_TEACHER_SOURCE_DRIFT");
 if(manifest.ids.length!==8)throw Error("COHORT_SIZE_DRIFT");
 const {SOURCE}=await import(sourceUrl.href);
 const rows=[];
 for(const file of manifest.ids){
  if(!/^[0-9a-f]{8}\.json$/.test(file))throw Error("BAD_COHORT_FILENAME");
  const id=file.slice(0,-5),task=JSON.parse(readFileSync(join(dir,file),"utf8"));
  if(!Array.isArray(task.train)||!Array.isArray(task.test))throw Error("BAD_ORIGINAL_TASK");
  rows.push({id,...assess(SOURCE[id],task)});
 }
 const byId=new Map(first.rows.map(x=>[x.id,x]));
 for(const row of rows){
  const prior=byId.get(row.id);
  if(!prior||row.submitted!==prior.teacher_submitted||
    row.trainExact!==prior.teacher_train_exact||
    row.testExact!==prior.teacher_original_task_exact||
    row.falseAccept!==prior.teacher_false_accept)
    throw Error("FIRST_RESULT_REPLAY_MISMATCH: "+row.id);
 }
 const solved=rows.filter(x=>x.testExact).length;
 if(solved!==first.teacher_original_exact)throw Error("FIRST_SOLVED_COUNT_DRIFT");
 return {contract:"neumann.q3.p22.replay.v1",sourceSha:blob,pinnedUpstream:manifest.source_commit,
          originalTaskCount:rows.length,solved,abstained:rows.filter(x=>!x.submitted).length,
          falseAccepted:rows.filter(x=>x.falseAccept).length,firstResultReproduced:true,rows};
}
export {exactGrid,gitBlobSha,assess,verify};
if(process.argv[1]&&pathToFileURL(resolve(process.argv[1])).href===import.meta.url){
 const dir=process.argv[2];if(!dir){console.error("usage: node experiments/q3_open_program_teacher_p22_verify.mjs /path/to/ARC-AGI/data/evaluation");process.exitCode=2;}
 else verify(dir).then(x=>process.stdout.write(JSON.stringify(x,null,2)+"\n")).catch(e=>{console.error(e.message);process.exitCode=1;});
}
