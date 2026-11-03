// NEUMANN P1.0 — frozen public ARC-AGI-1 opened blind evaluation implementation.
// No neural inference, no frontier claim; only original train examples enter each learner.
// Task gold outputs are scored only after all proposals are constructed.

function grid(g) {
  if (!Array.isArray(g)||g.length<1||g.length>30||!Array.isArray(g[0])||g[0].length<1||g[0].length>30) return null;
  const w=g[0].length;
  if (!g.every(r=>Array.isArray(r)&&r.length===w&&r.every(v=>Number.isInteger(v)&&v>=0&&v<=9)))return null;
  return g;
}

function equal(a,b){return a!==null&&b!==null&&JSON.stringify(a)===JSON.stringify(b);}

function transpose(g){return g[0].map((_,c)=>g.map(r=>r[c]));}

function rot90(g){let h=g.length,w=g[0].length;return Array.from({length:w},(_,r)=>Array.from({length:h},(_,c)=>g[c][w-r-1]));}

function tile(g,k){if(g.length*k>30||g[0].length*k>30)return null;return Array.from({length:g.length*k},(_,r)=>Array.from({length:g[0].length*k},(_,c)=>g[r%g.length][c%g[0].length]));}

function kron(g,order) {
 const h=g.length,w=g[0].length;if(h*h>30||w*w>30)return null;
 return Array.from({length:h*h},(_,r)=>Array.from({length:w*w},(_,c)=>{
  const a=g[Math.floor(r/h)][Math.floor(c/w)],b=g[r%h][c%w];
  return order===1?(a!==0?b:0):(b!==0?a:0);
 }));
}

function columnRank(g){
 const h=g.length,w=g[0].length;
 let cols=[];
 for(let c=0;c<w;c++){let colors=new Set(),n=0;for(let r=0;r<h;r++)if(g[r][c]!==0){colors.add(g[r][c]);n++;}
  if(n){if(colors.size!==1)return null;cols.push([n,c]);}
 }
 if(cols.length<2||cols.length>9||new Set(cols.map(x=>x[0])).size!==cols.length)return null;
 cols.sort((a,b)=>b[0]-a[0]);let out=g.map(r=>r.map(_=>0));
 for(let i=0;i<cols.length;i++)for(let r=0;r<h;r++)if(g[r][cols[i][1]]!==0)out[r][cols[i][1]]=i+1;
 return out;
}

function inferPalette(train){
 let m=new Map();
 for(let p of train){const x=grid(p.input),y=grid(p.output);if(!x||!y||x.length!==y.length||x[0].length!==y[0].length)return null;
  for(let i=0;i<x.length;i++)for(let j=0;j<x[0].length;j++){let a=x[i][j],b=y[i][j];if(m.has(a)&&m.get(a)!==b)return null;m.set(a,b);}
 }return m;
}

function fixedCandidates(train){
 const cmap=inferPalette(train);
 const entries=[
 ["identity",x=>x],
 ["flip_lr",x=>x.map(r=>r.slice().reverse())],
 ["flip_ud",x=>x.slice().reverse()],
 ["rot90",x=>rot90(x)],
 ["rot180",x=>rot90(rot90(x))],
 ["rot270",x=>rot90(rot90(rot90(x)))],
 ["transpose",x=>transpose(x)],
 ["tile_2x2",x=>tile(x,2)],
 ["tile_3x3",x=>tile(x,3)],
 ["kron_nonzero_first",x=>kron(x,1)],
 ["kron_nonzero_second",x=>kron(x,2)],
 ["column_rank_by_height",x=>columnRank(x)]
 ];
 if(cmap!==null)entries.push(["inferred_color_map",x=>x.every(r=>r.every(v=>cmap.has(v)))?x.map(r=>r.map(v=>cmap.get(v))):null]);
 let matches=[],evaluations=0;
 for(const [name,f] of entries){let ok=true;for(const p of train){evaluations++;let x=grid(p.input),y=grid(p.output);if(!x||!y){ok=false;break;}try{if(!equal(f(x),y)){ok=false;break;}}catch(e){ok=false;break;}}
  if(ok)matches.push([name,f]);}
 return {matches,evaluations,eligible:entries.length};
}

function predictFixed(fitted,x){
 if(fitted.matches.length===0)return null;
 let arr=[];for(const [,f]of fitted.matches){try{let z=f(grid(x));if(!grid(z))return null;arr.push(z);}catch(e){return null;}}
 if(!arr.every(v=>equal(arr[0],v)))return null;
 return arr[0];
}

function twoObjects(x){
 const g=grid(x);if(!g)return null;
 const colors=[...new Set(g.flat())].filter(c=>c!==0);
 if(colors.length!==2)return null;
 let objs=[];
 for(const color of colors){let pts=[];for(let r=0;r<g.length;r++)for(let c=0;c<g[0].length;c++)if(g[r][c]===color)pts.push([r,c]);
  let visited=new Set(),stack=[pts[0]],set=new Set(pts.map(p=>p.join(",")));
  while(stack.length){let [r,c]=stack.pop(),key=r+","+c;if(visited.has(key))continue;visited.add(key);
   for(const [rr,cc]of [[r-1,c],[r+1,c],[r,c-1],[r,c+1]])if(set.has(rr+","+cc)&&!visited.has(rr+","+cc))stack.push([rr,cc]);}
  if(visited.size!==pts.length)return null;
  const rs=pts.map(p=>p[0]),cs=pts.map(p=>p[1]);
  objs.push({color,pts,area:pts.length,r0:Math.min(...rs),r1:Math.max(...rs),c0:Math.min(...cs),c1:Math.max(...cs)});
 }
 if(objs[0].area===objs[1].area)return null;
 return objs;
}

function selectMoving(x,role){
 const ob=twoObjects(x);if(!ob)return null;
 if(role==="max_area")return ob[0].area>ob[1].area?ob:[ob[1],ob[0]];
 if(role==="min_area")return ob[0].area<ob[1].area?ob:[ob[1],ob[0]];
 return null;
}

function geometryDirection(m,a){
 const rowOverlap=Math.max(m.r0,a.r0)<=Math.min(m.r1,a.r1);
 const colOverlap=Math.max(m.c0,a.c0)<=Math.min(m.c1,a.c1);
 if(colOverlap&&!rowOverlap){
  return m.r1<a.r0?{sr:1,sc:0,gap:a.r0-m.r1-1}:{sr:-1,sc:0,gap:m.r0-a.r1-1};
 }
 if(rowOverlap&&!colOverlap){
  return m.c1<a.c0?{sr:0,sc:1,gap:a.c0-m.c1-1}:{sr:0,sc:-1,gap:m.c0-a.c1-1};
 }
 return null;
}

function executeMacro(input,ast){
 const x=grid(input),choice=x?selectMoving(x,ast.role):null;if(!choice)return null;
 const [m,a]=choice,d=geometryDirection(m,a);if(!d||d.gap<ast.clearance)return null;
 const dist=d.gap-ast.clearance,dr=d.sr*dist,dc=d.sc*dist;
 let out=x.map(r=>r.slice());
 for(const [r,c]of m.pts)out[r][c]=0;
 for(const [r,c]of m.pts){let rr=r+dr,cc=c+dc;
  if(rr<0||cc<0||rr>=x.length||cc>=x[0].length||out[rr][cc]!==0)return null;
  out[rr][cc]=m.color;}
 return out;
}

function fitMacro(train){
 let candidates=[],checks=0;
 for(const role of ["max_area","min_area"]){let clears=[],valid=true;
  for(const p of train){
   const x=grid(p.input),y=grid(p.output),pair=x?selectMoving(x,role):null;
   if(!x||!y||!pair||x.length!==y.length||x[0].length!==y[0].length){valid=false;break;}
   const [m,a]=pair,d=geometryDirection(m,a);if(!d){valid=false;break;}
   const anchorX=new Set(a.pts.map(v=>v.join(",")));
   const anchorY=new Set();let dst=[];
   for(let r=0;r<y.length;r++)for(let c=0;c<y[0].length;c++){
     if(y[r][c]===a.color)anchorY.add(r+","+c);
     if(y[r][c]===m.color)dst.push([r,c]);
   }
   if(anchorX.size!==anchorY.size||[...anchorX].some(v=>!anchorY.has(v))||dst.length!==m.pts.length){valid=false;break;}
   let dr=Math.min(...dst.map(v=>v[0]))-m.r0,dc=Math.min(...dst.map(v=>v[1]))-m.c0;
   if(!dst.every(v=>m.pts.some(q=>q[0]+dr===v[0]&&q[1]+dc===v[1]))||(d.sr!==0&&dc!==0)||(d.sc!==0&&dr!==0)){valid=false;break;}
   const clear=d.gap-(dr*d.sr+dc*d.sc);
   if(clear<0||clear>4||!Number.isInteger(clear)){valid=false;break;}clears.push(clear);
  }
  if(!valid||new Set(clears).size!==1)continue;
  const ast={role,clearance:clears[0]};
  for(const p of train){checks++;if(!equal(executeMacro(p.input,ast),p.output)){valid=false;break;}}
  if(valid)candidates.push(ast);
 }
 return {candidates,checks};
}

function predictMacro(fitted,x){
 if(!fitted.candidates.length)return null;
 let outputs=fitted.candidates.map(a=>executeMacro(x,a));
 return outputs.every(o=>equal(o,outputs[0]))?outputs[0]:null;
}

function rowKey(x,i,r,b){
 let v=0;for(let off=-r;off<=r;off++){let pos=i+off;v=2*v+(b==="periodic"?x[(pos+x.length)%x.length]:(pos>=0&&pos<x.length?x[pos]:0));}return v;
}

function fitRowCA(train){
 const rows=[];
 for(const p of train){
  const x=grid(p.input),y=grid(p.output);
  if(!x||!y||x.length!==y.length||x[0].length!==y[0].length||x[0].length<5)return null;
  if(!x.flat().concat(y.flat()).every(v=>v===0||v===1))return null;
  for(let i=0;i<x.length;i++)rows.push({x:x[i],y:y[i]});
 }
 for(let r=0;r<=2;r++){
  const variants=r===0?["none"]:["periodic","zero-pad"];
  let matches=[];
  for(const b of variants){
   let table=Array(1<<(2*r+1)).fill(null),valid=true;
   for(const {x,y}of rows){for(let i=0;i<x.length;i++){
     let idx=rowKey(x,i,r,b);
     if(table[idx]===null)table[idx]=y[i];else if(table[idx]!==y[i]){valid=false;break;}
   }if(!valid)break;}
   if(valid&&table.every(v=>v!==null))matches.push({r,b,table});
  }
  if(matches.length>1)return null;
  if(matches.length===1)return matches[0];
 }
 return null;
}

function predictRowCA(op,input){
 const g=grid(input);if(!op||!g||!g.flat().every(v=>v===0||v===1)||g[0].length<5)return null;
 return g.map(row=>row.map((_,i)=>op.table[rowKey(row,i,op.r,op.b)]));
}

function evaluateTask(task){
 if(!task||!Array.isArray(task.train)||!Array.isArray(task.test)||!task.train.length||!task.test.length)return {error:"invalid_task"};
 const fixed=fixedCandidates(task.train);
 const baseline=task.test.map(v=>predictFixed(fixed,v.input));
 let route={P03:0,P07:0,P09:0,ABSTAIN:0},extra=0;
 let macro=null,ca=null;
 const cascade=task.test.map((v,i)=>{
  if(baseline[i]!==null){route.P03++;return baseline[i];}
  if(macro===null)macro=fitMacro(task.train);
  const p=predictMacro(macro,v.input);
  if(p!==null){route.P07++;extra++;return p;}
  if(ca===null)ca=fitRowCA(task.train);
  const q=predictRowCA(ca,v.input);
  if(q!==null){route.P09++;extra++;return q;}
  route.ABSTAIN++;return null;
 });
 // Gold outputs are read ONLY now, after all proposals.
 const target=task.test.map(x=>x.output);
 const baseline_exact=baseline.every((p,i)=>p!==null&&equal(p,target[i]));
 const cascade_exact=cascade.every((p,i)=>p!==null&&equal(p,target[i]));
 const original_exact_cascade=cascade.map((p,i)=>p!==null&&equal(p,target[i]));
 return {baseline_exact,cascade_exact,original_exact_cascade,baseline_abstained:baseline.some(v=>v===null),
         cascade_abstained:cascade.some(v=>v===null),route,train_examples:task.train.length,
         test_examples:task.test.length,fixed_candidates:fixed.matches.map(v=>v[0]),
         candidate_evaluations:fixed.evaluations,macro_candidates:macro?.candidates||[],
         ca_inferred:ca?{radius:ca.r,boundary:ca.b}:null};
}

function cohort(names){
 const ex=new Set(["007bbfb7.json","08ed6ac7.json","0d3d703e.json","05f2a901.json"]);
 function fnv(s){let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619)>>>0;return h>>>0;}
 return names.filter(x=>x.endsWith(".json")&&!ex.has(x)).map(name=>({name,score:fnv("neumann-prh-p10-20261103|"+name)})).sort((a,b)=>a.score-b.score||a.name.localeCompare(b.name)).slice(0,32).map(x=>x.name);
}

export {evaluateTask,cohort};
