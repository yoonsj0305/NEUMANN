/* NEUMANN P3.0 | Higher-order relational object rewrites.
 * A single task-conditioned, typed map/filter action over all objects.
 * The *program* (segmentation, property predicate, action) is induced
 * solely from TRAIN pairs. No task IDs, labels of original TEST, NN, teacher.
 * Every accepted candidate is exact-replayed on TRAIN and safely ABSTAINS
 * on conflicting predictions. This IS human-specified metagrammar, not
 * general autonomous invention of unknown semantic primitives.
 */
export const CONTRACT=Object.freeze({
 schema:"neumann.q3.p30.object-relational.v1",maxGrid:30,
 maxPrograms:60000,neuralCalls:0,teacherCalls:0,
 outputOnlySameShape:true,firstPrinciple:"Object-as-set, predicate, map action, invariant output replay",
 Q3_autonomousOpcode:"NOT_PROVEN"
});
const EQ=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
const grid=g=>Array.isArray(g)&&g.length>0&&g.length<=30&&Array.isArray(g[0])&&g[0].length>0&&g[0].length<=30&&
 g.every(row=>Array.isArray(row)&&row.length===g[0].length&&row.every(v=>Number.isInteger(v)&&v>=0&&v<=9));
const valid=(tr,q)=>Array.isArray(tr)&&tr.length>0&&tr.length<=12&&
 tr.every(x=>grid(x.input)&&grid(x.output)&&x.input.length===x.output.length&&x.input[0].length===x.output[0].length)&&
 Array.isArray(q)&&q.length>0&&q.length<=5&&q.every(grid);
const NEIGHBORS={four:[[1,0],[-1,0],[0,1],[0,-1]],
 eight:[[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]]};
function dominant(g){
 const c=new Map();for(const row of g)for(const x of row)c.set(x,(c.get(x)||0)+1);
 const a=[...c].sort((x,y)=>y[1]-x[1]||x[0]-y[0]);
 return a.length>1&&a[0][1]===a[1][1]?null:a[0]?.[0]??null;
}
export function background(g,mode){return mode==="zero"?0:dominant(g);}
function extract(g,seg,mode){
 const bg=background(g,mode);
 if(bg===null)return null;
 const h=g.length,w=g[0].length,seen=new Set(),objects=[];
 const connectivity=seg.endsWith("8")?"eight":"four";
 const colorsPartition=seg.startsWith("color");
 if(seg==="color_all"){
  for(const c of [...new Set(g.flat())].sort((a,b)=>a-b)){
   if(c===bg)continue;
   const pts=[];for(let r=0;r<h;r++)for(let x=0;x<w;x++)if(g[r][x]===c)pts.push([r,x]);
   if(pts.length)objects.push(pts);
  }
 } else {
  const offsets=NEIGHBORS[connectivity];
  for(let r=0;r<h;r++)for(let x=0;x<w;x++){
   const id=r*w+x;
   if(g[r][x]===bg||seen.has(id))continue;
   const origin=g[r][x],pts=[],q=[[r,x]];seen.add(id);
   for(let i=0;i<q.length;i++){
    const [y,z]=q[i];pts.push([y,z]);
    for(const [dy,dx]of offsets){
     const yy=y+dy,xx=z+dx,k=yy*w+xx;
     if(yy<0||yy>=h||xx<0||xx>=w||seen.has(k)||g[yy][xx]===bg)continue;
     if(colorsPartition&&g[yy][xx]!==origin)continue;
     seen.add(k);q.push([yy,xx]);
    }
   }
   objects.push(pts);
  }
 }
 return objects.map(points=>{
  const minR=Math.min(...points.map(x=>x[0])),maxR=Math.max(...points.map(x=>x[0]));
  const minC=Math.min(...points.map(x=>x[1])),maxC=Math.max(...points.map(x=>x[1]));
  const colors=new Set(points.map(([r,c])=>g[r][c]));
  return {points,area:points.length,box:[minR,minC,maxR,maxC],
   height:maxR-minR+1,width:maxC-minC+1,monoColor:colors.size===1?[...colors][0]:null,
   touchesBorder:minR===0||minC===0||maxR===h-1||maxC===w-1,
   bboxArea:(maxR-minR+1)*(maxC-minC+1)};
 });
}
export function objects(g,{segment="color4",bg="zero"}={}){
 if(!grid(g)||!["color4","color8","fg4","fg8","color_all"].includes(segment))return null;
 return extract(g,segment,bg);
}
const VALUE_FEATURES=["area","height","width","bboxArea"];
const SELECTOR_ORDER=["all","uniqueLargest","uniqueSmallest","border","interior","square","nonSquare","monochrome"];
function select(o,all,p){
 if(p.kind==="all")return true;
 if(p.kind==="border")return o.touchesBorder;
 if(p.kind==="interior")return !o.touchesBorder;
 if(p.kind==="square")return o.width===o.height;
 if(p.kind==="nonSquare")return o.width!==o.height;
 if(p.kind==="monochrome")return o.monoColor!==null;
 if(p.kind==="uniqueLargest"||p.kind==="uniqueSmallest"){
  const areas=all.map(z=>z.area);
  const target=p.kind==="uniqueLargest"?Math.max(...areas):Math.min(...areas);
  return o.area===target&&areas.filter(x=>x===target).length===1;
 }
 if(p.kind==="color")return o.monoColor===p.color;
 if(p.kind==="ge")return o[p.feature]>=p.bound;
 if(p.kind==="le")return o[p.feature]<=p.bound;
 return false;
}
function predicateCandidates(trainViews){
 const all=[...SELECTOR_ORDER.map(kind=>({kind}))];
 const feats=new Map(VALUE_FEATURES.map(k=>[k,new Set()]));
 const colors=new Set();
 for(const olist of trainViews)for(const o of olist){
  for(const f of VALUE_FEATURES)feats.get(f).add(o[f]);
  if(o.monoColor!==null)colors.add(o.monoColor);
 }
 for(const color of [...colors].sort((a,b)=>a-b))all.push({kind:"color",color});
 for(const feature of VALUE_FEATURES) {
  for(const n of [...feats.get(feature)].sort((a,b)=>a-b)){
   all.push({kind:"ge",feature,bound:n});
   all.push({kind:"le",feature,bound:n});
  }
 }
 return all;
}
const SEGMENTS=["color4","color8","fg4","fg8","color_all"];
const BGS=["zero","dominant"];
const ACTIONS=["paint","erase","bboxFill","bboxBorder","holeFill"];
function writeAction(out,g,o,action,color,bg){
 const [r0,c0,r1,c1]=o.box,points=o.points;
 if(action==="paint"||action==="erase"){
  for(const [r,c]of points)out[r][c]=action==="erase"?bg:color;
  return;
 }
 const occupied=new Set(points.map(([r,c])=>r+","+c));
 for(let r=r0;r<=r1;r++)for(let c=c0;c<=c1;c++){
  if(action==="bboxFill" ||
     action==="bboxBorder"&&(r===r0||r===r1||c===c0||c===c1) ||
     action==="holeFill"&&!occupied.has(r+","+c)&&g[r][c]===bg)
       out[r][c]=color;
 }
}
export function interpret(program,g) {
 if(!grid(g)||!program||!SEGMENTS.includes(program.segment)||!BGS.includes(program.bg)||
    !ACTIONS.includes(program.action)||!program.predicate)return null;
 const bg=background(g,program.bg),os=extract(g,program.segment,program.bg);
 if(os===null||os.length===0)return null;
 if(!Number.isInteger(program.color)||program.color<0||program.color>9)return null;
 const copy=g.map(r=>r.slice()),chosen=os.filter(o=>select(o,os,program.predicate));
 if(!chosen.length)return null;
 // Reject output-dependent selection collisions from overlapping objects.
 if(program.action!=="paint"&&program.action!=="erase"){
  const set=new Set();
  for(const o of chosen){
   const [r0,c0,r1,c1]=o.box;
   for(let r=r0;r<=r1;r++)for(let c=c0;c<=c1;c++){
    if(program.action==="bboxBorder"&&r!==r0&&r!==r1&&c!==c0&&c!==c1)continue;
    if(program.action==="holeFill"&&g[r][c]!==bg)continue;
    const key=r+","+c;
    if(set.has(key))return null;
    set.add(key);
   }
  }
 }
 for(const o of chosen)writeAction(copy,g,o,program.action,program.color,bg);
 return copy;
}
function programCost(program) {
 const cost={all:0,border:2,interior:2,square:2,nonSquare:2,monochrome:1,
  uniqueLargest:3,uniqueSmallest:3,color:3,ge:4,le:4};
 const action={paint:2,erase:1,bboxFill:4,bboxBorder:4,holeFill:5};
 return cost[program.predicate.kind]+action[program.action]+
    (program.bg==="dominant"?1:0)+(program.segment==="color_all"?2:program.segment.endsWith("8")?1:0);
}
export function synthesize(train,testInputs) {
 const started=process.hrtime.bigint(),trace={
  schema:CONTRACT.schema,attempted:0,trainReplay:0,
  trainFitted:0,distinctTest:0,minCost:null,
  status:"NOT_EVALUATED",selected:null,wallMs:0,
  countCandidatesTruncated:false,neuralCalls:0,teacherCalls:0};
 const finish=(prediction,status)=>{
  trace.status=status;trace.wallMs=Number(process.hrtime.bigint()-started)/1e6;
  return {prediction,trace};
 };
 if(!valid(train,testInputs))return finish(null,"UNSUPPORTED_OR_BAD_SHAPE");
 const palette=[...new Set(train.flatMap(x=>x.output.flat()))].sort((a,b)=>a-b);
 const best=[],allPredictions=new Map();let bestCost=Infinity;
 for(const bg of BGS)for(const segment of SEGMENTS){
  const trainViews=train.map(x=>extract(x.input,segment,bg));
  if(trainViews.some(x=>x===null||x.length===0))continue;
  const predicates=predicateCandidates(trainViews);
  for(const predicate of predicates)for(const action of ACTIONS)for(const color of (action==="erase"?[0]:palette)){
   const p={kind:"object-map-rewrite",bg,segment,predicate,action,color};
   trace.attempted++;
   if(trace.attempted>CONTRACT.maxPrograms){trace.countCandidatesTruncated=true;return finish(null,"PROGRAM_BUDGET_EXCEEDED");}
   let fits=true;
   for(const x of train){
    trace.trainReplay++;
    const output=interpret(p,x.input);
    if(output===null||!EQ(output,x.output)){fits=false;break;}
   }
   if(!fits)continue;
   trace.trainFitted++;
   const outputs=testInputs.map(g=>interpret(p,g));
   if(outputs.some(x=>x===null))continue;
   const score=programCost(p),signature=JSON.stringify(outputs);
   if(score<bestCost){bestCost=score;allPredictions.clear();best.length=0;}
   if(score===bestCost){
    if(!allPredictions.has(signature))allPredictions.set(signature,{outputs,p});
    best.push(p);
   }
  }
 }
 trace.minCost=Number.isFinite(bestCost)?bestCost:null;
 trace.distinctTest=allPredictions.size;
 if(!trace.trainFitted)return finish(null,"NO_TRAIN_CONSISTENT_OBJECT_PROGRAM");
 if(!allPredictions.size)return finish(null,"NO_VALID_TEST_PROGRAM");
 if(allPredictions.size>1)return finish(null,"AMBIGUOUS_MIN_COST_PROGRAMS");
 const chosen=allPredictions.values().next().value;
 trace.selected=chosen.p;
 if(!train.every(x=>EQ(interpret(chosen.p,x.input),x.output)))
  throw Error("P30_ORIGINAL_TRAIN_REPLAY_FAILED");
 if(!testInputs.every((g,i)=>EQ(interpret(chosen.p,g),chosen.outputs[i])))
  throw Error("P30_TEST_REPLAY_FAILED");
 return finish(chosen.outputs,"UNIQUE_PROOF_REPLAY");
}
