/* NEUMANN P1.4 executable library matcher: zero teacher calls.
  SOURCE functions are supplied by frozen P1.3 module, not selected by task ID.
  Every hypothesis is checked against TRAIN, gold TEST never exposed to matcher.
*/
const TRANSFORMS=["id","flipH","flipV","rot90","rot180","rot270","transpose","antiTranspose"];
const INVERSE={id:"id",flipH:"flipH",flipV:"flipV",rot90:"rot270",rot180:"rot180",rot270:"rot90",transpose:"transpose",antiTranspose:"antiTranspose"};
function isGrid(g){return Array.isArray(g)&&g.length>=1&&g.length<=30&&Array.isArray(g[0])&&g[0].length>=1&&g[0].length<=30&&g.every(row=>Array.isArray(row)&&row.length===g[0].length&&row.every(v=>Number.isInteger(v)&&v>=0&&v<=9));}
function rotate(g){return Array.from({length:g[0].length},(_,r)=>Array.from({length:g.length},(_,c)=>g[g.length-1-c][r]));}
function view(g,name){if(!isGrid(g))return null;switch(name){
 case "id":return g.map(r=>r.slice());
 case "flipH":return g.map(r=>r.slice().reverse());
 case "flipV":return g.slice().reverse().map(r=>r.slice());
 case "rot90":return rotate(g);
 case "rot180":return rotate(rotate(g));
 case "rot270":return rotate(rotate(rotate(g)));
 case "transpose":return g[0].map((_,c)=>g.map(r=>r[c]));
 case "antiTranspose":return rotate(rotate(g[0].map((_,c)=>g.map(r=>r[c]))));
 default:return null;
}}
function gridEq(a,b){return isGrid(a)&&isGrid(b)&&a.length===b.length&&a.every((r,i)=>r.length===b[i].length&&r.every((v,j)=>v===b[i][j]));}
function matchLibrary(train,testInputs,source){
 const trace={candidate_count:0,train_program_calls:0,test_program_calls:0,train_consistent:0,accepted_candidates:[],abstention:null,wall_ms:0,external_teacher_forwards:0};
 const t0=Date.now();
 if(!train.length||!testInputs.length||!testInputs.every(isGrid)){trace.abstention="INVALID_INPUT";trace.wall_ms=Date.now()-t0;return {prediction:null,trace};}
 const matching=[];
 for(const [label,fn]of Object.entries(source)){
  if(typeof fn!=="function")continue;
  for(const transformation of TRANSFORMS){
   trace.candidate_count++;
   const runner=input=>{const normalized=view(input,transformation);if(!normalized)return null;let raw=null;try{raw=fn(normalized);}catch(e){return null;}if(!isGrid(raw))return null;return view(raw,INVERSE[transformation]);};
   let fit=true;
   for(const pair of train){
    trace.train_program_calls++;const output=runner(pair.input);
    if(!gridEq(output,pair.output)){fit=false;break;}
   }
   if(fit){trace.train_consistent++;matching.push({label,transformation,runner});}
  }
 }
 if(!matching.length){trace.abstention="NO_TRAIN_CONSISTENT_OPERATOR";trace.wall_ms=Date.now()-t0;return {prediction:null,trace};}
 let agreed=null;
 for(const candidate of matching){const outputs=[];
  for(const testInput of testInputs){trace.test_program_calls++;const output=candidate.runner(testInput);if(!isGrid(output)){trace.abstention="INVALID_TEST_RESULT";trace.wall_ms=Date.now()-t0;return {prediction:null,trace};}outputs.push(output);}
  if(agreed!==null && (agreed.length!==outputs.length||agreed.some((g,i)=>!gridEq(g,outputs[i])))){
   trace.abstention="AMBIGUOUS_OR_UNSAFE";
   trace.wall_ms=Date.now()-t0;
   return {prediction:null,trace};
  }
  agreed=outputs;
  trace.accepted_candidates.push({operator:candidate.label,transform:candidate.transformation});
 }
 trace.wall_ms=Date.now()-t0;return {prediction:agreed,trace};
}
function scoreOne(task,library,baselinePropose,jointPropose){
 const inputOnly=task.test.map(p=>p.input);
 const A=baselinePropose(task.train,inputOnly,"A");
 const B=baselinePropose(task.train,inputOnly,"B");
 const J=B.proposals!==null?{prediction:B.proposals,trace:{attempted:0}}:(()=>{const out=jointPropose(task.train,inputOnly);return {prediction:out.prediction,trace:out.trace};})();
 const K=matchLibrary(task.train,inputOnly,library);
 // Original gold first becomes visible at this point, AFTER every proposal.
 const original=task.test.map(p=>p.output);
 const correct=v=>v!==null&&v.length===original.length&&v.every((grid,i)=>gridEq(grid,original[i]));
 const a=correct(A.proposals),b=correct(B.proposals),j=correct(J.prediction),k=correct(K.prediction);
 return {A_exact:a,B_exact:b,J_exact:j,K_exact:k,additional:k&&!a&&!b&&!j,
         K_false_accept:K.prediction!==null&&!k,K_abstained:K.prediction===null,
         K_trace:K.trace,A_attempts:A.trace.attempted,B_attempts:B.trace.attempted,J_attempts:J.trace.attempted||0,
         original_test_count:task.test.length};
}
function fnv32(s){let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619)>>>0;return h>>>0;}
function cohort(files,excluded){const banned=new Set(excluded);return files.filter(x=>x.endsWith(".json")&&!banned.has(x)).map(name=>({name,hash:fnv32("neumann-q3-p14-20261105|"+name)})).sort((a,b)=>a.hash-b.hash||a.name.localeCompare(b.name)).slice(0,24).map(x=>x.name);}
export {TRANSFORMS,matchLibrary,scoreOne,cohort,view};
