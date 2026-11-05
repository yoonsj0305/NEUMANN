/* NEUMANN P1.5 | Bitter Lesson control: enumerative vs feedback-evolutionary program search.
 * Shared primitive interpreter belongs to frozen P1.1. NO new ARC task specific operators,
 * no neural model, no test-label access during program generation.
 */
const VERSION="neumann.q3.bitter-lesson.p15.v1";
const MAX_CANDIDATES=1024;
const BASE_SEED=2026110515;
function validGrid(g){
 return Array.isArray(g)&&g.length>0&&g.length<=30&&Array.isArray(g[0])&&g[0].length>0&&g[0].length<=30&&g.every(row=>Array.isArray(row)&&row.length===g[0].length&&row.every(v=>Number.isInteger(v)&&v>=0&&v<=9));
}
function eqGrid(a,b){
 return validGrid(a)&&validGrid(b)&&a.length===b.length&&a.every((row,i)=>row.length===b[i].length&&row.every((v,j)=>v===b[i][j]));
}
function stringHash(s){let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619)>>>0;return h>>>0;}
function rng(seed){let state=seed>>>0;return ()=>{state=(state+0x6D2B79F5)>>>0;let x=state;x=Math.imul(x^(x>>>15),x|1);x^=x+Math.imul(x^(x>>>7),x|61);return ((x^(x>>>14))>>>0)/4294967296;};}
function execute(program,input,applyGrid){
 let g=input;
 if(!validGrid(g))return null;
 for(const op of program){
  try{g=applyGrid(g,op);}catch(e){return null;}
  if(!validGrid(g))return null;
 }
 return g;
}
function frac(a,b){
 if(!validGrid(a)||!validGrid(b))return 0;
 const H=a.length,W=a[0].length,hh=b.length,ww=b[0].length;
 if(H!==hh||W!==ww){
  const hratio=Math.min(H,hh)/Math.max(H,hh),wratio=Math.min(W,ww)/Math.max(W,ww);
  return 0.08*hratio*wratio;
 }
 let match=0;
 for(let r=0;r<H;r++)for(let c=0;c<W;c++)if(a[r][c]===b[r][c])match++;
 return 0.1+0.9*match/(H*W);
}
function fitness(outputs,train){
 let score=0;
 for(let i=0;i<train.length;i++)score+=frac(outputs[i],train[i].output);
 return score/train.length;
}
function uniformPrograms(ops,budget=MAX_CANDIDATES){
 const out=[],n=ops.length;
 for(let depth=1;depth<=3&&out.length<budget;depth++){
  const N=Math.pow(n,depth);
  for(let k=0;k<N&&out.length<budget;k++){
   let code=[],id=k;for(let p=0;p<depth;p++){code.push(ops[id%n]);id=Math.floor(id/n);}
   out.push(code);
  }
 }
 return out;
}
function change(program,ops,rand){
 let p=program.slice(),type=Math.floor(rand()*6);
 if(type===0&&p.length<3)p.push(ops[Math.floor(rand()*ops.length)]);
 else if(type===1&&p.length<3)p.unshift(ops[Math.floor(rand()*ops.length)]);
 else if(type===2)p[Math.floor(rand()*p.length)]=ops[Math.floor(rand()*ops.length)];
 else if(type===3&&p.length>1)p.splice(Math.floor(rand()*p.length),1);
 else if(type===4&&p.length>1){let a=Math.floor(rand()*p.length),b=Math.floor(rand()*p.length);[p[a],p[b]]=[p[b],p[a]];}
 else if(type===5&&p.length>=2){let idx=Math.floor(rand()*(p.length-1));p.splice(idx,2,ops[Math.floor(rand()*ops.length)]);}
 else if(p.length<3)p.push(ops[Math.floor(rand()*ops.length)]);
 else p[Math.floor(rand()*p.length)]=ops[Math.floor(rand()*ops.length)];
 return p;
}
function evaluateProgram(program,train,applyGrid){
 const outputs=[];let valid=true;
 for(const e of train){const g=execute(program,e.input,applyGrid);outputs.push(g);if(!g)valid=false;}
 const allExact=valid&&outputs.every((g,i)=>eqGrid(g,train[i].output));
 return {allExact,feedback:fitness(outputs,train),executions:train.length};
}
function search(train,inputs,mode,ops,applyGrid,budget=MAX_CANDIDATES){
 const start=Date.now();
 const trace={mode,seed:null,budget,proposals:0,pair_executions:0,test_executions:0,first_train_fit_at:null,train_fit_count:0,train_fitness_max:0,duplicates_rejected:0,candidates_invalid:0,abstention:null,search_ms:null,exact_programs:[],n_unique:0};
 if(!Array.isArray(train)||!train.length||!Array.isArray(inputs)||!inputs.length||!inputs.every(validGrid)||!train.every(e=>validGrid(e.input)&&validGrid(e.output))){trace.abstention="INVALID_OR_EMPTY";trace.search_ms=Date.now()-start;return {prediction:null,trace};}
 const exact=[],visited=new Set(),elites=[],uniform=uniformPrograms(ops,budget);
 const taskHash=stringHash(JSON.stringify(train));
 const rand=rng(BASE_SEED^taskHash);trace.seed=BASE_SEED^taskHash;
 let uniIndex=0,stalls=0;
 function nextUniform(){while(uniIndex<uniform.length){const p=uniform[uniIndex++];if(!visited.has(p.join("~")))return p;}return null;}
 while(trace.proposals<budget){
  let program=null;
  if(mode==="U")program=nextUniform();
  else{
   if(trace.proposals<ops.length)program=[ops[trace.proposals]];
   else if(rand()<0.18 || elites.length===0 || stalls>100)program=nextUniform();
   else{
    let chosen=null;
    for(let n=0;n<4;n++){
     const member=elites[Math.floor(rand()*Math.min(60,elites.length))];
     if(!chosen||member.fitness>chosen.fitness)chosen=member;
    }
    if(chosen)program=change(chosen.code,ops,rand);
   }
   if(program&&visited.has(program.join("~"))){
    trace.duplicates_rejected++;stalls++;program=null;
   }
   if(program===null){
    for(let attempt=0;attempt<40;attempt++){
     const p=elites.length?change(elites[Math.floor(rand()*elites.length)].code,ops,rand):[ops[Math.floor(rand()*ops.length)]];
     if(!visited.has(p.join("~"))){program=p;break;}
     trace.duplicates_rejected++;
    }
   }
   if(program===null)program=nextUniform();
  }
  if(!program)break;
  const key=program.join("~");
  if(visited.has(key)){trace.duplicates_rejected++;continue;}
  visited.add(key);trace.proposals++;stalls=0;
  const evaluated=evaluateProgram(program,train,applyGrid);
  trace.pair_executions+=evaluated.executions;
  trace.train_fitness_max=Math.max(trace.train_fitness_max,evaluated.feedback);
  if(evaluated.feedback===0)trace.candidates_invalid++;
  if(evaluated.allExact){
   if(trace.first_train_fit_at===null)trace.first_train_fit_at=trace.proposals;
   exact.push(program);
   trace.train_fit_count++;
  }
  if(mode==="E"){
   elites.push({code:program,fitness:evaluated.feedback-0.0001*program.length});
   elites.sort((a,b)=>b.fitness-a.fitness||a.code.length-b.code.length);
   if(elites.length>90)elites.pop();
  }
 }
 trace.n_unique=visited.size;
 if(!exact.length){trace.abstention="NO_EXACT_TRAIN_PROGRAM";trace.search_ms=Date.now()-start;return {prediction:null,trace};}
 // Do not make an unverified choice when train-consistent programs disagree on test INPUTS.
 let agreed=null;
 for(const program of exact){
  let predictions=[];
  for(const input of inputs){trace.test_executions++;predictions.push(execute(program,input,applyGrid));}
  if(predictions.some(x=>x===null)){trace.abstention="INVALID_TEST_OUTPUT";trace.search_ms=Date.now()-start;return {prediction:null,trace};}
  if(agreed!==null && predictions.some((p,i)=>!eqGrid(p,agreed[i]))){
   trace.abstention="DISAGREEING_PROGRAMS";trace.search_ms=Date.now()-start;return {prediction:null,trace};
  }
  agreed=predictions;
 }
 trace.exact_programs=exact.slice(0,3);
 trace.search_ms=Date.now()-start;return {prediction:agreed,trace};
}
function scoreTask(task,ops,applyGrid,strongBaseline){
 const train=task.train,inputs=task.test.map(v=>v.input);
 const U=search(train,inputs,"U",ops,applyGrid),E=search(train,inputs,"E",ops,applyGrid);
 const S=strongBaseline?strongBaseline(train,inputs,"B"):null;
 // Oracle answers only accessed here, after all programs and routes are frozen.
 const gold=task.test.map(v=>v.output),exact=(p)=>p!==null&&p.length===gold.length&&p.every((g,i)=>eqGrid(g,gold[i]));
 return {U_correct:exact(U.prediction),E_correct:exact(E.prediction),S_correct:S?exact(S.proposals):null,
         U_false_accept:U.prediction!==null&&!exact(U.prediction),
         E_false_accept:E.prediction!==null&&!exact(E.prediction),
         U:U.trace,E:E.trace,S_attempts:S?S.trace.attempted:null,S_ms:S?S.trace.elapsed_ms:null,
         train_count:train.length,test_count:task.test.length};
}
export {VERSION,MAX_CANDIDATES,BASE_SEED,uniformPrograms,search,scoreTask};
