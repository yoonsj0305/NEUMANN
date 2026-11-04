/* NEUMANN P1.2 | Joint scene partition + program synthesis.
   Task body is used only in propose(train,testInputs) with no gold test outputs.
   Segmentation and transform schemas are explicitly human-written.
   No neural inference, JEPA, or open-ended primitive invention.
*/
const VERSION="neumann.q3.joint-partition-p12.v1";
const PARTITIONS=["color4","color8","foreground4","foreground8","color_all","row_run","column_run"];
const SELECTORS=["max_area","min_area","top","bottom","left","right","widest","tallest"];
const STYLES=["object_crop","bbox_crop","object_canvas"];
const TRANSFORMS=["id","flipH","flipV","rot90","rot180","rot270","transpose"];
const CAP=2000;
const equal=(a,b)=>a!==null&&b!==null&&JSON.stringify(a)===JSON.stringify(b);
function grid(a){if(!Array.isArray(a)||!a.length||a.length>30||!Array.isArray(a[0])||!a[0].length||a[0].length>30)return null;return a.every(r=>Array.isArray(r)&&r.length===a[0].length&&r.every(v=>Number.isInteger(v)&&v>=0&&v<=9))?a:null;}
function bbox(pts){return {r0:Math.min(...pts.map(x=>x[0])),r1:Math.max(...pts.map(x=>x[0])),c0:Math.min(...pts.map(x=>x[1])),c1:Math.max(...pts.map(x=>x[1]))};}
function pack(points,g){if(!points.length)return null;const b=bbox(points);return {pts:points,color:g[points[0][0]][points[0][1]],area:points.length,b, width:b.c1-b.c0+1,height:b.r1-b.r0+1};}
function segment(g,mode){
 const h=g.length,w=g[0].length,out=[];
 if(mode==="color_all"){for(const value of [...new Set(g.flat())].filter(c=>c!==0)){let pts=[];for(let r=0;r<h;r++)for(let c=0;c<w;c++)if(g[r][c]===value)pts.push([r,c]);if(pts.length)out.push(pack(pts,g));}return out;}
 if(mode==="row_run"||mode==="column_run"){
  const n=mode==="row_run"?h:w,active=[];
  for(let k=0;k<n;k++){let found=false;if(mode==="row_run")found=g[k].some(v=>v!==0);else found=g.some(row=>row[k]!==0);active.push(found);}
  for(let start=0;start<n;){if(!active[start]){start++;continue;}let end=start;while(end+1<n&&active[end+1])end++;let pts=[];
  for(let r=0;r<h;r++)for(let c=0;c<w;c++)if(g[r][c]!==0&&((mode==="row_run"&&r>=start&&r<=end)||(mode==="column_run"&&c>=start&&c<=end)))pts.push([r,c]);
  if(pts.length)out.push(pack(pts,g));start=end+1;}return out;
 }
 const eight=mode==="color8"||mode==="foreground8";
 const perColor=mode==="color4"||mode==="color8";
 if(!["color4","color8","foreground4","foreground8"].includes(mode))return [];
 const directions=eight?[[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]]:[[1,0],[-1,0],[0,1],[0,-1]];
 const seen=Array.from({length:h},()=>Array(w).fill(false));
 for(let r=0;r<h;r++)for(let c=0;c<w;c++){
 if(g[r][c]===0||seen[r][c])continue;const value=g[r][c],stack=[[r,c]],pts=[];seen[r][c]=true;
 while(stack.length){const [rr,cc]=stack.pop();pts.push([rr,cc]);for(const [dr,dc]of directions){const nr=rr+dr,nc=cc+dc;if(nr<0||nc<0||nr>=h||nc>=w||seen[nr][nc]||g[nr][nc]===0)continue;if(perColor&&g[nr][nc]!==value)continue;seen[nr][nc]=true;stack.push([nr,nc]);}}
 out.push(pack(pts,g));
 }return out;
}
function feature(o,sel){const b=o.b;switch(sel){
 case "max_area":case "min_area":return o.area;
 case "top":return b.r0;
 case "bottom":return b.r1;
 case "left":return b.c0;
 case "right":return b.c1;
 case "widest":return o.width;
 case "tallest":return o.height;
 default:return null;
}}
function choose(g,partition,selector){
 const objs=segment(g,partition);if(!objs.length)return null;
 const signs={max_area:-1,min_area:1,top:1,bottom:-1,left:1,right:-1,widest:-1,tallest:-1};
 objs.sort((a,b)=>signs[selector]*(feature(a,selector)-feature(b,selector)));
 if(objs.length>1&&feature(objs[0],selector)===feature(objs[1],selector))return null;
 return objs[0];
}
function extract(g,o,style){const b=o.b,h=g.length,w=g[0].length,pts=new Set(o.pts.map(x=>x.join(",")));
 if(style==="object_canvas")return Array.from({length:h},(_,r)=>Array.from({length:w},(_,c)=>pts.has(r+","+c)?g[r][c]:0));
 if(style==="bbox_crop")return g.slice(b.r0,b.r1+1).map(row=>row.slice(b.c0,b.c1+1));
 if(style==="object_crop")return Array.from({length:b.r1-b.r0+1},(_,r)=>Array.from({length:b.c1-b.c0+1},(_,c)=>pts.has((r+b.r0)+","+(c+b.c0))?g[r+b.r0][c+b.c0]:0));
 return null;
}
function rotate(g){return Array.from({length:g[0].length},(_,r)=>Array.from({length:g.length},(_,c)=>g[g.length-1-c][r]));}
function transform(g,t){if(!g)return null;switch(t){
 case "id":return g.map(r=>r.slice());
 case "flipH":return g.map(r=>r.slice().reverse());
 case "flipV":return g.slice().reverse().map(r=>r.slice());
 case "rot90":return rotate(g);
 case "rot180":return rotate(rotate(g));
 case "rot270":return rotate(rotate(rotate(g)));
 case "transpose":return g[0].map((_,c)=>g.map(row=>row[c]));
 default:return null;
}}
function compile(ast){return raw=>{const g=grid(raw);if(!g)return null;const obj=choose(g,ast.partition,ast.selector);if(!obj)return null;return transform(extract(g,obj,ast.style),ast.transform);};}
function inferMap(outputs,train){
 const m={};for(let k=0;k<outputs.length;k++){const a=outputs[k],b=grid(train[k].output);if(!a||!b||a.length!==b.length||a[0].length!==b[0].length)return null;
  for(let r=0;r<a.length;r++)for(let c=0;c<a[0].length;c++){const key=a[r][c],value=b[r][c];if(Object.prototype.hasOwnProperty.call(m,key)&&m[key]!==value)return null;m[key]=value;}
 }return m;
}
function mapped(g,m){if(!g)return null;const out=[];for(const row of g){let r=[];for(const v of row){if(!Object.prototype.hasOwnProperty.call(m,v))return null;r.push(m[v]);}out.push(r);}return out;}
function candidates(){
 const arr=[];for(const mode of PARTITIONS)for(const select of SELECTORS)for(const style of STYLES)for(const t of TRANSFORMS){
 arr.push({schema:VERSION,partition:mode,selector:select,style,transform:t});
 }return arr.slice(0,CAP);
}
function propose(train,testInputs){
 const t0=Date.now(),trace={attempted:0,train_grid_executions:0,test_grid_executions:0,candidate_matches:0,abstention:null,elapsed_ms:null,programs:[]};
 if(!Array.isArray(train)||!train.length||!Array.isArray(testInputs)||!testInputs.every(x=>grid(x))){trace.abstention="malformed";trace.elapsed_ms=Date.now()-t0;return {prediction:null,trace};}
 const fits=[];
 for(const ast of candidates()){
 trace.attempted++;const fn=compile(ast),outputs=[];let ok=true;
 for(const example of train){trace.train_grid_executions++;let z=null;try{z=fn(example.input);}catch(e){}if(!z){ok=false;break;}outputs.push(z);}
 if(!ok)continue;const p=inferMap(outputs,train);if(p!==null)fits.push({ast,p});
 }
 trace.candidate_matches=fits.length;
 if(!fits.length){trace.abstention="no_candidate";trace.elapsed_ms=Date.now()-t0;return {prediction:null,trace};}
 let predicted=null;for(const fit of fits){const fn=compile(fit.ast),outputs=[];
 for(const input of testInputs){trace.test_grid_executions++;let raw=null;try{raw=fn(input);}catch(e){}const out=mapped(raw,fit.p);if(!out){trace.abstention="unseen_palette_or_invalid";trace.elapsed_ms=Date.now()-t0;return {prediction:null,trace};}outputs.push(out);}
 if(predicted!==null&&!equal(predicted,outputs)){trace.abstention="ambiguous_AST";trace.elapsed_ms=Date.now()-t0;return {prediction:null,trace};}
 predicted=outputs;
 }
 trace.programs=fits.slice(0,3).map(x=>({ast:x.ast,map:x.p}));trace.elapsed_ms=Date.now()-t0;
 return {prediction:predicted,trace};
}
function evaluate(task,existingEvaluate,existingPropose){
 const base=existingEvaluate(task);
 // Baseline B is independently computed by the frozen earlier engine.
 const testInputs=task.test.map(x=>x.input);
 const earlier=existingPropose(task.train,testInputs,"B");
 if(!equal(earlier.proposals===null?[]:earlier.proposals,earlier.proposals===null?[]:earlier.proposals))throw Error("invalid");
 const J=earlier.proposals!==null?{prediction:earlier.proposals,trace:{skipped_due_to_baseline:true,attempted:0,elapsed_ms:0}}:propose(task.train,testInputs);
 const reference=task.test.map(x=>x.output); // accessed only after both proposers finished
 const exact=p=>p!==null&&p.length===reference.length&&p.every((x,i)=>equal(x,reference[i]));
 const j=exact(J.prediction),b=exact(earlier.proposals);
 if(b!==base.B_exact)throw Error("baseline re-evaluation inconsistency");
 return {base_A:base.A_exact,base_B:base.B_exact,J_exact:j,additional:j&&!b,baseline_lost:b&&!j,base_B_trace:base.B_trace,joint_trace:J.trace,test_count:task.test.length};
}
function fnv32(s){let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619)>>>0;return h>>>0;}
function cohort(filenames,excludes){const ban=new Set(excludes);return filenames.filter(x=>x.endsWith(".json")&&!ban.has(x)).map(name=>({name,v:fnv32("neumann-q3-p12-20261105|"+name)})).sort((a,b)=>a.v-b.v||a.name.localeCompare(b.name)).slice(0,24).map(x=>x.name);}
export {VERSION,PARTITIONS,SELECTORS,candidates,propose,evaluate,cohort};
