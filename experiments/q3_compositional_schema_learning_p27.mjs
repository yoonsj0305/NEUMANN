/* NEUMANN P2.7 | Teacher-free cross-task macro prior + typed compositional grid programs.
 * The atoms ARE fixed by human design. Data selects/composes whole AST macros.
 * This is not autonomous opcode invention, JEPA, or proof of frontier intelligence.
 * Original TEST GOLD is never accessed by inference.
 */
import {inGrid} from "./q3_cached_typed_guard_p24.mjs";
export const CONTRACT=Object.freeze({
 schema:"neumann.q3.p27.compositional-cross-task-macro.v1",
 maxDepth:2,maxGrid:30,teacherCalls:0,neuralCalls:0,
 primitives:["r90","r180","r270","flipH","flipV","transpose",
             "cropNZ","cropBG","cropLargest","scale2","tileH2","tileV2"]});
const eq=(a,b)=>inGrid(a)&&inGrid(b)&&JSON.stringify(a)===JSON.stringify(b);
const copy=g=>g.map(r=>r.slice());
const r90=g=>g[0].map((_,c)=>g.map(row=>row[c]).reverse());
const histogram=g=>{const h=new Map();for(const row of g)for(const x of row)h.set(x,(h.get(x)||0)+1);return h;};
function dominant(g){
 const sorted=[...histogram(g)].sort((a,b)=>b[1]-a[1]||a[0]-b[0]);
 return sorted.length>1&&sorted[0][1]===sorted[1][1]?null:sorted[0]?.[0]??null;
}
function cropMask(g,pred){
 const points=[];for(let r=0;r<g.length;r++)for(let c=0;c<g[0].length;c++)if(pred(g[r][c]))points.push([r,c]);
 if(!points.length)return null;
 const a=Math.min(...points.map(x=>x[0])),b=Math.max(...points.map(x=>x[0]));
 const x=Math.min(...points.map(x=>x[1])),y=Math.max(...points.map(x=>x[1]));
 return g.slice(a,b+1).map(row=>row.slice(x,y+1));
}
function cropLargest(g){
 const h=g.length,w=g[0].length,seen=new Set(),objs=[];
 for(let r=0;r<h;r++)for(let c=0;c<w;c++){
  if(g[r][c]===0||seen.has(r+","+c))continue;
  const q=[[r,c]],pts=[];seen.add(r+","+c);
  for(let k=0;k<q.length;k++){const [y,x]=q[k];pts.push([y,x]);
   for(const [dy,dx]of [[0,1],[0,-1],[1,0],[-1,0]]){
    const yy=y+dy,xx=x+dx,id=yy+","+xx;
    if(yy>=0&&xx>=0&&yy<h&&xx<w&&g[yy][xx]!==0&&!seen.has(id)){seen.add(id);q.push([yy,xx]);}
   }}
  objs.push(pts);
 }
 if(!objs.length)return null;
 objs.sort((a,b)=>b.length-a.length);
 if(objs.length>1&&objs[0].length===objs[1].length)return null;
 const pts=objs[0],r0=Math.min(...pts.map(x=>x[0])),r1=Math.max(...pts.map(x=>x[0]));
 const c0=Math.min(...pts.map(x=>x[1])),c1=Math.max(...pts.map(x=>x[1]));
 return g.slice(r0,r1+1).map(row=>row.slice(c0,c1+1));
}
function applyAtom(op,g){
 if(!inGrid(g))return null;
 if(op==="r90")return r90(g);
 if(op==="r180")return r90(r90(g));
 if(op==="r270")return r90(r90(r90(g)));
 if(op==="flipH")return g.map(r=>r.slice().reverse());
 if(op==="flipV")return copy(g).reverse();
 if(op==="transpose")return g[0].map((_,c)=>g.map(row=>row[c]));
 if(op==="cropNZ")return cropMask(g,v=>v!==0);
 if(op==="cropBG"){const bg=dominant(g);return bg===null?null:cropMask(g,v=>v!==bg);}
 if(op==="cropLargest")return cropLargest(g);
 if(op==="scale2")return g.flatMap(row=>[row.flatMap(x=>[x,x]),row.flatMap(x=>[x,x])]);
 if(op==="tileH2")return g.map(row=>row.concat(row));
 if(op==="tileV2")return copy(g).concat(copy(g));
 return null;
}
export function executeGeometry(g,ops){
 if(!inGrid(g)||!Array.isArray(ops)||ops.length>CONTRACT.maxDepth)return null;
 let out=g;
 for(const op of ops){if(!CONTRACT.primitives.includes(op))return null;out=applyAtom(op,out);if(!inGrid(out))return null;}
 return copy(out);
}
export const allASTs=(()=>{
 const ret=[[]];for(const op of CONTRACT.primitives)ret.push([op]);
 for(const a of CONTRACT.primitives)for(const b of CONTRACT.primitives)ret.push([a,b]);
 return ret;
})();
function derivePalette(train,ops){
 const map=new Map(),counts=new Map();
 for(const {input,output} of train){
  const g=executeGeometry(input,ops);
  if(!inGrid(g)||g.length!==output.length||g[0].length!==output[0].length)return null;
  for(let r=0;r<g.length;r++)for(let c=0;c<g[0].length;c++){
   const k=g[r][c],v=output[r][c];
   if(map.has(k)&&map.get(k)!==v)return null;
   map.set(k,v);counts.set(k,(counts.get(k)||0)+1);
  }
 }
 // Prevent invented per-task correspondences from a single observation.
 if([...counts.values()].some(n=>n<2))return null;
 return [...map].sort((a,b)=>a[0]-b[0]);
}
export function runProgram(program,g){
 const raw=executeGeometry(g,program.ops);if(!raw)return null;
 const map=new Map(program.palette);
 if(raw.some(row=>row.some(v=>!map.has(v))))return null;
 return raw.map(row=>row.map(v=>map.get(v)));
}
function mdCost(program){
 let c=program.ops.length;
 for(const op of program.ops)c+=(op==="scale2"||op.startsWith("tile"))?1.0:op.startsWith("crop")?0.25:0;
 c+=0.06*program.palette.filter(([a,b])=>a!==b).length;
 return c;
}
function shapeFamily(train){
 const t=train[0];if(!t)return "unknown";
 const h=t.input.length,w=t.input[0].length,H=t.output.length,W=t.output[0].length;
 return h===H&&w===W?"same":h===W&&w===H?"swapped":H>h||W>w?"expand":"shrink";
}
export function synthesize(train,testInputs,{prior=null,selector="classical",maxCandidates=allASTs.length}={}){
 const start=process.hrtime.bigint(),trace={
  schema:CONTRACT.schema,selector,geometry_attempts:0,train_replays:0,
  train_fit_count:0,test_replays:0,abstention:null,selected_AST:null,
  min_cost_ties:0,distinct_test_predictions:0,teacher_calls:0,neural_calls:0,
  wall_ms:0,candidate_budget:maxCandidates
 };
 const finish=(prediction,reason)=>{
  trace.abstention=reason;trace.wall_ms=Number(process.hrtime.bigint()-start)/1e6;
  return {prediction,trace};
 };
 if(!Array.isArray(train)||!train.length||!train.every(p=>inGrid(p.input)&&inGrid(p.output))||
    !Array.isArray(testInputs)||!testInputs.length||!testInputs.every(inGrid))return finish(null,"INVALID_INPUT");
 if(!Number.isInteger(maxCandidates)||maxCandidates<1)return finish(null,"INVALID_BUDGET");
 const family=shapeFamily(train);
 const scored=allASTs.map(ops=>{
  const sig=ops.join("+")||"identity";
  const weight=prior?.[family]?.[sig]||0;
  const pseudo={ops,palette:[]};
  return {ops,shape:family,prior_hits:weight,code:sig,baseCost:mdCost(pseudo)};
 });
 if(selector==="learned"&&prior)scored.sort((a,b)=>b.prior_hits-a.prior_hits||a.baseCost-b.baseCost||a.code.localeCompare(b.code));
 else scored.sort((a,b)=>a.baseCost-b.baseCost||a.code.localeCompare(b.code));
 const fits=[];
 // Search is identical across arms except a meta-trained ordering prior.
 for(const c of scored.slice(0,Math.min(maxCandidates,scored.length))){
  trace.geometry_attempts++;
  const map=derivePalette(train,c.ops);
  trace.train_replays+=train.length;
  if(map===null)continue;
  const p={kind:"program",ops:c.ops,palette:map};
  // Independent exact replay; no mathematical shortcut is allowed.
  if(!train.every(pair=>eq(runProgram(p,pair.input),pair.output)))continue;
  trace.train_fit_count++;
  // Learned prior supplies an ordering only. Without external teacher no grammar expansion.
  fits.push({p,cost:mdCost(p),prior_hits:c.prior_hits,code:c.code});
 }
 if(!fits.length)return finish(null,"NO_TRAIN_CONSISTENT_PROGRAM");
 fits.sort((a,b)=>{
  if(selector==="learned"&&prior&&a.prior_hits!==b.prior_hits)return b.prior_hits-a.prior_hits;
  return a.cost-b.cost||a.code.localeCompare(b.code);
 });
 const best=fits[0],tie=fits.filter(x=>
   (selector==="learned"&&prior)?x.prior_hits===best.prior_hits&&Math.abs(x.cost-best.cost)<1e-9:
   Math.abs(x.cost-best.cost)<1e-9);
 trace.min_cost_ties=tie.length;
 const preds=new Map();let unsupported=false;
 for(const x of tie){
  const out=[];for(const g of testInputs){trace.test_replays++;const y=runProgram(x.p,g);if(y===null){unsupported=true;break;}out.push(y);}
  if(out.length===testInputs.length)preds.set(JSON.stringify(out),{output:out,p:x.p});
 }
 trace.distinct_test_predictions=preds.size;
 if(unsupported)return finish(null,"UNSUPPORTED_TIED_PROGRAM");
 if(preds.size===0)return finish(null,"NO_VALID_TEST_REPLAY");
 if(preds.size>1)return finish(null,"AMBIGUOUS_TEST_PREDICTIONS");
 const win=preds.values().next().value;
 trace.selected_AST=win.p;
 return finish(win.output,null);
}
export function learnPrior(tasks){
 const start=process.hrtime.bigint(),prior={},stats={seen:0,correct:0,abstained:0,false_accepts:0};
 for(const task of tasks){
  if(!Array.isArray(task.train)||!Array.isArray(task.test)||!task.test.length)continue;
  const g=task.test.map(t=>t.input);
  if(g.some(x=>!inGrid(x)))continue;
  const result=synthesize(task.train,g);
  stats.seen++;
  const correct=result.prediction!==null&&result.prediction.length===task.test.length&&
   result.prediction.every((x,i)=>eq(x,task.test[i].output));
  if(!result.prediction)stats.abstained++;
  else if(!correct)stats.false_accepts++;
  if(correct){
   stats.correct++;
   const family=shapeFamily(task.train),key=result.trace.selected_AST.ops.join("+")||"identity";
   (prior[family]??={})[key]=(prior[family][key]||0)+1;
  }
 }
 stats.wall_ms=Number(process.hrtime.bigint()-start)/1e6;
 return {schema:"neumann.q3.p27.meta-prior.v1",
  semantics:"Empirical cross-task program-frequency prior from official public TRAINING tasks only.",
  allAtomsHumanSpecified:true,trainedTasks:stats.seen,stats,prior};
}
export {shapeFamily,eq};
