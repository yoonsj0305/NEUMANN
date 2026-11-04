/* NEUMANN P1.1: frozen deterministic grid-vs-object hypothesis-space audit.
   Original-task solution proposals use TRAIN inputs/outputs only.
   Original TEST outputs are read solely by scoreOriginal after proposal freeze.
   Strong classical comparison; no JEPA/neural, no autonomous opcode invention.
*/
const SPEC={name:"q3-object-headroom-p11",maxHypotheses:500,minRows:1,maxRows:30,source:"ARC-AGI-1-training",model:"zero-neural"};
const eq=(a,b)=>a!==null&&b!==null&&JSON.stringify(a)===JSON.stringify(b);
const copy=g=>g.map(r=>r.slice());
function grid(raw){
 if(!Array.isArray(raw)||raw.length<1||raw.length>30||!Array.isArray(raw[0])||raw[0].length<1||raw[0].length>30)return null;
 let w=raw[0].length;
 return raw.every(r=>Array.isArray(r)&&r.length===w&&r.every(v=>Number.isInteger(v)&&v>=0&&v<=9))?raw:null;
}
function rot(g){return Array.from({length:g[0].length},(_,r)=>Array.from({length:g.length},(_,c)=>g[g.length-c-1][r]));}
function bb(points){return {r0:Math.min(...points.map(x=>x[0])),r1:Math.max(...points.map(x=>x[0])),c0:Math.min(...points.map(x=>x[1])),c1:Math.max(...points.map(x=>x[1]))};}
function crop(g){let p=[];for(let r=0;r<g.length;r++)for(let c=0;c<g[0].length;c++)if(g[r][c]!==0)p.push([r,c]);if(!p.length)return null;const b=bb(p);return g.slice(b.r0,b.r1+1).map(r=>r.slice(b.c0,b.c1+1));}
function rect(g,style){let out=copy(g),points=[];for(let r=0;r<g.length;r++)for(let c=0;c<g[0].length;c++)if(g[r][c]!==0)points.push([r,c]);if(!points.length)return null;const b=bb(points);let z=out.flat().filter(v=>v!==0),fill=z[0];if(z.some(v=>v!==fill))return null;
 for(let r=b.r0;r<=b.r1;r++)for(let c=b.c0;c<=b.c1;c++)if(style==="solid"||r===b.r0||r===b.r1||c===b.c0||c===b.c1)out[r][c]=fill;return out;
}
function up(g,k){const h=g.length,w=g[0].length;if(h*k>30||w*k>30)return null;return Array.from({length:h*k},(_,r)=>Array.from({length:w*k},(_,c)=>g[Math.floor(r/k)][Math.floor(c/k)]));}
function tile(g,ry,rx){const h=g.length,w=g[0].length;if(h*ry>30||w*rx>30)return null;return Array.from({length:h*ry},(_,r)=>Array.from({length:w*rx},(_,c)=>g[r%h][c%w]));}
function nonzero(g){return g.map(r=>r.map(v=>v===0?0:1));}
function bars(g,dir){const h=g.length,w=g[0].length,out=Array.from({length:h},()=>Array(w).fill(0));if(dir==="rows"){for(let r=0;r<h;r++){let colors=[...new Set(g[r].filter(v=>v!==0))];if(colors.length>1)return null;if(colors.length)out[r].fill(colors[0]);}}else{for(let c=0;c<w;c++){let colors=[...new Set(g.map(r=>r[c]).filter(v=>v!==0))];if(colors.length>1)return null;for(let r=0;r<h;r++)if(colors.length)out[r][c]=colors[0];}}return out;}
function rankColumns(g){let counts=[];for(let c=0;c<g[0].length;c++){let colors=[...new Set(g.map(r=>r[c]).filter(v=>v!==0))],n=g.filter(r=>r[c]!==0).length;if(colors.length>1)return null;if(n)counts.push({c,n});}
 if(counts.length<2||counts.length>9||new Set(counts.map(v=>v.n)).size!==counts.length)return null;
 counts.sort((a,b)=>b.n-a.n);
 let out=g.map(r=>r.map(()=>0));counts.forEach((v,i)=>{for(let r=0;r<g.length;r++)if(g[r][v.c])out[r][v.c]=i+1;});return out;
}
function kron(g,type){const h=g.length,w=g[0].length;if(h*h>30||w*w>30)return null;return Array.from({length:h*h},(_,r)=>Array.from({length:w*w},(_,c)=>{
 let a=g[Math.floor(r/h)][Math.floor(c/w)],b=g[r%h][c%w];return type==="first"?(a!==0?b:0):(b!==0?a:0);
}));}
const GRIDOPS=[
 "id","flipH","flipV","rot90","rot180","rot270","transpose","antiTranspose",
 "cropNZ","maskNZ","scale2","scale3","tile22","tile33","tile12","tile21",
 "rankColumn","fillRows","fillCols","outlineBBox","solidBBox","kronFirst","kronSecond"
];
function applyGrid(g,n){
 if(!g)return null;switch(n){
 case "id":return copy(g);
 case "flipH":return g.map(r=>r.slice().reverse());
 case "flipV":return copy(g).reverse();
 case "rot90":return rot(g);
 case "rot180":return rot(rot(g));
 case "rot270":return rot(rot(rot(g)));
 case "transpose":return g[0].map((_,c)=>g.map(r=>r[c]));
 case "antiTranspose":return rot(rot(g[0].map((_,c)=>g.map(r=>r[c]))));
 case "cropNZ":return crop(g);
 case "maskNZ":return nonzero(g);
 case "scale2":return up(g,2);
 case "scale3":return up(g,3);
 case "tile22":return tile(g,2,2);
 case "tile33":return tile(g,3,3);
 case "tile12":return tile(g,1,2);
 case "tile21":return tile(g,2,1);
 case "rankColumn":return rankColumns(g);
 case "fillRows":return bars(g,"rows");
 case "fillCols":return bars(g,"cols");
 case "outlineBBox":return rect(g,"outline");
 case "solidBBox":return rect(g,"solid");
 case "kronFirst":return kron(g,"first");
 case "kronSecond":return kron(g,"second");
 default:return null;
 }}
function components(g,adjacency){
 let h=g.length,w=g[0].length,seen=Array.from({length:h},()=>Array(w).fill(false)),out=[];
 const dirs=adjacency===8?[[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]]:[[1,0],[-1,0],[0,1],[0,-1]];
 for(let r=0;r<h;r++)for(let c=0;c<w;c++){let color=g[r][c];if(!color||seen[r][c])continue;let stack=[[r,c]],p=[];seen[r][c]=true;while(stack.length){let [rr,cc]=stack.pop();p.push([rr,cc]);for(const [dr,dc]of dirs){let nr=rr+dr,nc=cc+dc;if(nr>=0&&nr<h&&nc>=0&&nc<w&&!seen[nr][nc]&&g[nr][nc]===color){seen[nr][nc]=true;stack.push([nr,nc]);}}}
 out.push({color,points:p,area:p.length,box:bb(p)});
 }return out;
}
function select(g,rule,adj){
 const objs=components(g,adj);if(!objs.length)return null;
 let sorted=objs.slice();
 if(rule==="largest")sorted.sort((a,b)=>b.area-a.area);
 else if(rule==="smallest")sorted.sort((a,b)=>a.area-b.area);
 else if(rule==="top")sorted.sort((a,b)=>a.box.r0-b.box.r0);
 else if(rule==="bottom")sorted.sort((a,b)=>b.box.r1-a.box.r1);
 else if(rule==="left")sorted.sort((a,b)=>a.box.c0-b.box.c0);
 else if(rule==="right")sorted.sort((a,b)=>b.box.c1-a.box.c1);
 else if(rule==="wide")sorted.sort((a,b)=>(b.box.c1-b.box.c0)-(a.box.c1-a.box.c0));
 else if(rule==="tall")sorted.sort((a,b)=>(b.box.r1-b.box.r0)-(a.box.r1-a.box.r0));
 else return null;
 if(sorted.length>1){
 const a=sorted[0],b=sorted[1];
 const key=o=>rule==="largest"||rule==="smallest"?o.area:rule==="top"?o.box.r0:rule==="bottom"?o.box.r1:rule==="left"?o.box.c0:rule==="right"?o.box.c1:rule==="wide"?o.box.c1-o.box.c0:o.box.r1-o.box.r0;
 if(key(a)===key(b))return null;
 }return sorted[0];
}
function objectOp(g,rule,style,adj){
 const o=select(g,rule,adj);if(!o)return null;
 const b=o.box;let h=g.length,w=g[0].length,z=Array.from({length:h},()=>Array(w).fill(0));
 if(style==="erase"){z=copy(g);for(const [r,c]of o.points)z[r][c]=0;return z;}
 if(style==="crop"){return Array.from({length:b.r1-b.r0+1},(_,r)=>Array.from({length:b.c1-b.c0+1},(_,c)=>o.points.some(p=>p[0]===r+b.r0&&p[1]===c+b.c0)?o.color:0));}
 if(style==="mask"){for(const [r,c]of o.points)z[r][c]=o.color;return z;}
 if(style==="bboxCrop"){for(let r=b.r0;r<=b.r1;r++)for(let c=b.c0;c<=b.c1;c++)z[r][c]=g[r][c];return z.slice(b.r0,b.r1+1).map(r=>r.slice(b.c0,b.c1+1));}
 if(style==="bboxFill"||style==="bboxBorder"){for(let r=b.r0;r<=b.r1;r++)for(let c=b.c0;c<=b.c1;c++)if(style==="bboxFill"||r===b.r0||r===b.r1||c===b.c0||c===b.c1)z[r][c]=o.color;return z;}
 return null;
}
function relationalMove(g,role,gapTarget){
 const objects=components(g,4);
 if(objects.length!==2||objects[0].area===objects[1].area)return null;
 const m=role==="largest"?(objects[0].area>objects[1].area?objects[0]:objects[1]):(objects[0].area<objects[1].area?objects[0]:objects[1]);
 const a=objects[0]===m?objects[1]:objects[0],M=m.box,A=a.box;
 const rowOverlap=Math.max(M.r0,A.r0)<=Math.min(M.r1,A.r1);
 const colOverlap=Math.max(M.c0,A.c0)<=Math.min(M.c1,A.c1);
 let dr=0,dc=0,clearance=-1;
 if(colOverlap&&!rowOverlap){if(M.r1<A.r0){clearance=A.r0-M.r1-1;dr=clearance-gapTarget;}else{clearance=M.r0-A.r1-1;dr=gapTarget-clearance;}}
 else if(rowOverlap&&!colOverlap){if(M.c1<A.c0){clearance=A.c0-M.c1-1;dc=clearance-gapTarget;}else{clearance=M.c0-A.c1-1;dc=gapTarget-clearance;}}
 else return null;
 if(clearance<gapTarget)return null;
 const out=copy(g);
 for(const [r,c]of m.points)out[r][c]=0;
 for(const [r,c]of m.points){const rr=r+dr,cc=c+dc;if(rr<0||cc<0||rr>=g.length||cc>=g[0].length||out[rr][cc]!==0)return null;out[rr][cc]=m.color;}
 return out;
}
function inferPalette(srcs,train){
 const mapping={};for(let i=0;i<srcs.length;i++){
 const x=srcs[i],y=grid(train[i].output);
 if(!x||!y||x.length!==y.length||x[0].length!==y[0].length)return null;
 for(let r=0;r<x.length;r++)for(let c=0;c<x[0].length;c++){
 let k=x[r][c],v=y[r][c];if(Object.prototype.hasOwnProperty.call(mapping,k)&&mapping[k]!==v)return null;mapping[k]=v;
 }}
 return mapping;
}
function applyPalette(g,map){if(!g)return null;let out=[];for(let r=0;r<g.length;r++){let row=[];for(let c=0;c<g[0].length;c++){const k=g[r][c];if(!Object.prototype.hasOwnProperty.call(map,k))return null;row.push(map[k]);}out.push(row);}return out;}
function programFn(steps){return raw=>{let g=grid(raw);if(!g)return null;for(const step of steps){g=step.kind==="grid"?applyGrid(g,step.op):step.kind==="rel"?relationalMove(g,step.role,step.clearance):objectOp(g,step.selector,step.style,step.adj);if(!grid(g))return null;}return g;};}
function allCandidates(arm){
 const single=GRIDOPS.map(op=>[{kind:"grid",op}]);
 const pairs=[];for(let a of GRIDOPS)for(let b of GRIDOPS)if(a!=="id"&&b!=="id")pairs.push([{kind:"grid",op:a},{kind:"grid",op:b}]);
 const base=single.concat(pairs);
 if(arm==="A")return base.slice(0,SPEC.maxHypotheses);
 const objs=[];
 for(const role of ["largest","smallest"])for(let clearance=0;clearance<=4;clearance++)objs.push([{kind:"rel",role,clearance}]);
 for(const adj of [4,8])for(const selector of ["largest","smallest","top","bottom","left","right","wide","tall"])
 for(const style of ["crop","mask","erase","bboxCrop","bboxFill","bboxBorder"]){
  objs.push([{kind:"object",adj,selector,style}]);
  for(const op of ["cropNZ","rot90","rot180","transpose","flipH","flipV"])objs.push([{kind:"object",adj,selector,style},{kind:"grid",op}]);
 }
 return base.slice(0,260).concat(objs).slice(0,SPEC.maxHypotheses);
}
function propose(train,testInputs,arm){
 const t0=Date.now();
 const inventory=allCandidates(arm),matches=[],sourceCheck={candidate_count:inventory.length,attempted:0,train_grid_executions:0,test_grid_executions:0,ambiguous:false,match_count:0,elapsed_ms:0,abstention:"",programs:[]};
 if(!Array.isArray(train)||!train.length||!testInputs.every(x=>grid(x))){sourceCheck.abstention="bad_inputs";return {proposals:null,trace:sourceCheck};}
 for(const steps of inventory){sourceCheck.attempted++;
  const f=programFn(steps),outs=[];
  let valid=true;for(const pair of train){sourceCheck.train_grid_executions++;let v=null;try{v=f(pair.input);}catch(e){}if(!v){valid=false;break;}outs.push(v);}
  if(!valid)continue;
  const cmap=inferPalette(outs,train);if(!cmap)continue;
  matches.push({steps,palette:cmap,f});
 }
 sourceCheck.match_count=matches.length;
 if(!matches.length){sourceCheck.abstention="no_consistent_program";sourceCheck.elapsed_ms=Date.now()-t0;return {proposals:null,trace:sourceCheck};}
 let predictions=null;
 for(const m of matches){
  const out=[];for(const input of testInputs){sourceCheck.test_grid_executions++;let g=null;try{g=applyPalette(m.f(input),m.palette);}catch(e){}if(!g){sourceCheck.abstention="unseen_color_or_invalid";sourceCheck.elapsed_ms=Date.now()-t0;return {proposals:null,trace:sourceCheck};}out.push(g);}
  if(predictions!==null&&!eq(predictions,out)){sourceCheck.abstention="ambiguous_programs";sourceCheck.ambiguous=true;sourceCheck.elapsed_ms=Date.now()-t0;return {proposals:null,trace:sourceCheck};}
  predictions=out;
 }
 sourceCheck.programs=matches.slice(0,4).map(m=>m.steps);
 sourceCheck.elapsed_ms=Date.now()-t0;
 return {proposals:predictions,trace:sourceCheck};
}
function evaluateTask(task){
 const x=task.train||[],test=task.test||[];
 if(!x.length||!test.length)return {error:"invalid_task"};
 // Deep structural firewall: never send task.test[i].output to candidate proposer.
 const inputOnly=test.map(p=>p.input);
 const A=propose(x,inputOnly,"A"),B=propose(x,inputOnly,"B");
 const original=test.map(p=>p.output);
 const score=prediction=>prediction!==null&&prediction.length===original.length&&prediction.every((g,i)=>eq(g,original[i]));
 return {A_exact:score(A.proposals),B_exact:score(B.proposals),A_trace:A.trace,B_trace:B.trace,test_count:test.length,
         B_additional:score(B.proposals)&&!score(A.proposals),A_lost:score(A.proposals)&&!score(B.proposals)};
}
function fnv32(s){let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619)>>>0;return h>>>0;}
function cohort(files,excluded){const ban=new Set(excluded);return files.filter(s=>s.endsWith(".json")&&!ban.has(s)).map(name=>({name,rank:fnv32("neumann-q3-p11-20261105|"+name)})).sort((a,b)=>a.rank-b.rank||a.name.localeCompare(b.name)).slice(0,24).map(x=>x.name);}
export {SPEC,propose,evaluateTask,cohort};
