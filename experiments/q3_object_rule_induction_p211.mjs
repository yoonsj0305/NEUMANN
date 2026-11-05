/* NEUMANN P2.1 | Verified task-conditioned object rewrite synthesis.
 * All executable primitives and selectors below are human-specified. Task-derived
 * parameters are selected strictly by fitting TRAIN pairs; TEST gold is not read.
 * This does not constitute spontaneous invention of new primitive semantics.
 */
const SPEC = Object.freeze({version:'neumann.q3.p211.v1', maxGrid:30, source:'public ARC-AGI-1 evaluation', neuralCalls:0});
const PARTITIONS=['color4','color8','foreground4','foreground8','color_all'];
const SELECTORS=['largest','smallest','top','bottom','left','right','widest','tallest','rarest'];
const PAINT_MASKS=['object','bbox','border','hole'];
const DIRECTIONS4=[[1,0],[-1,0],[0,1],[0,-1]];
const DIRECTIONS8=DIRECTIONS4.concat([[1,1],[1,-1],[-1,1],[-1,-1]]);
function valid(g){return Array.isArray(g)&&g.length>=1&&g.length<=30&&Array.isArray(g[0])&&g[0].length>=1&&g[0].length<=30&&g.every(row=>Array.isArray(row)&&row.length===g[0].length&&row.every(x=>Number.isInteger(x)&&x>=0&&x<=9));}
function equal(a,b){return valid(a)&&valid(b)&&a.length===b.length&&a.every((row,r)=>row.length===b[r].length&&row.every((v,c)=>v===b[r][c]));}
function clone(g){return g.map(row=>row.slice());}
function key(r,c){return `${r},${c}`;}
function background(g){const hist=new Map();for(const row of g)for(const c of row)hist.set(c,(hist.get(c)||0)+1);const a=[...hist].sort((u,v)=>v[1]-u[1]);return a.length>1&&a[0][1]===a[1][1]?null:a[0][0];}
function makeObject(g,pts){if(!pts.length)return null;const b={r0:Math.min(...pts.map(x=>x[0])),r1:Math.max(...pts.map(x=>x[0])),c0:Math.min(...pts.map(x=>x[1])),c1:Math.max(...pts.map(x=>x[1]))};const colors=[...new Set(pts.map(([r,c])=>g[r][c]))];return {pts,b,width:b.c1-b.c0+1,height:b.r1-b.r0+1,area:pts.length,colors};}
function segment(g,partition){if(!valid(g))return [];const bg=background(g);if(bg===null)return [];const h=g.length,w=g[0].length;
 if(partition==='color_all') {const found=[];for(const color of [...new Set(g.flat())].filter(v=>v!==bg)){let p=[];for(let r=0;r<h;r++)for(let c=0;c<w;c++)if(g[r][c]===color)p.push([r,c]);found.push(makeObject(g,p));}return found;}
 const byColor=partition==='color4'||partition==='color8';const eight=partition==='color8'||partition==='foreground8';if(!PARTITIONS.includes(partition))return [];
 const visited=new Set(),components=[],dirs=eight?DIRECTIONS8:DIRECTIONS4;
 for(let r=0;r<h;r++)for(let c=0;c<w;c++){
  if(g[r][c]===bg||visited.has(key(r,c)))continue;
  const queue=[[r,c]],pts=[];visited.add(key(r,c));let idx=0;
  while(idx<queue.length){const [rr,cc]=queue[idx++];pts.push([rr,cc]);for(const [dr,dc]of dirs){const nr=rr+dr,nc=cc+dc;if(nr<0||nc<0||nr>=h||nc>=w||g[nr][nc]===bg||visited.has(key(nr,nc))||(byColor&&g[nr][nc]!==g[r][c]))continue;visited.add(key(nr,nc));queue.push([nr,nc]);}}
  components.push(makeObject(g,pts));
 }
 return components;
}
function select(g,part,selector){const components=segment(g,part);if(!components.length)return null;const bg=background(g);if(bg===null)return null;
 const hist=new Map();for(const row of g)for(const c of row)hist.set(c,(hist.get(c)||0)+1);
 const feature=o=>{const b=o.b;switch(selector){case 'largest':case 'smallest':return o.area;case 'top':return b.r0;case 'bottom':return b.r1;case 'left':return b.c0;case 'right':return b.c1;case 'widest':return o.width;case 'tallest':return o.height;case 'rarest':return o.colors.length===1?hist.get(o.colors[0]):Infinity;default:return NaN;}};
 const reverse=['largest','bottom','right','widest','tallest'].includes(selector);const sorted=components.map(o=>({o,v:feature(o)})).sort((a,b)=>reverse?b.v-a.v:a.v-b.v);
 if(!Number.isFinite(sorted[0].v)||(sorted.length>1&&sorted[0].v===sorted[1].v))return null;
 return sorted[0].o;
}
function mask(g,obj,style){const h=g.length,w=g[0].length,s=new Set(),points=new Set(obj.pts.map(p=>key(p[0],p[1]))),b=obj.b;
 if(style==='object')return points;
 if(style==='bbox'||style==='border'||style==='hole')for(let r=b.r0;r<=b.r1;r++)for(let c=b.c0;c<=b.c1;c++){
  if(style==='bbox'||style==='border'&&(r===b.r0||r===b.r1||c===b.c0||c===b.c1)||style==='hole'&&!points.has(key(r,c)))s.add(key(r,c));
 }
 return s;
}
function paint(g,obj,style,color){if(!valid(g)||!Number.isInteger(color)||color<0||color>9)return null;const o=clone(g),affected=mask(g,obj,style);if(!affected.size)return null;for(const xy of affected){const [r,c]=xy.split(',').map(Number);o[r][c]=color;}return o;}
function wipeOthers(g,obj){const o=clone(g),bg=background(g),sel=new Set(obj.pts.map(p=>key(p[0],p[1])));if(bg===null)return null;for(let r=0;r<g.length;r++)for(let c=0;c<g[0].length;c++)if(g[r][c]!==bg&&!sel.has(key(r,c)))o[r][c]=bg;return o;}
function move(g,obj,dy,dx){if(!Number.isInteger(dy)||!Number.isInteger(dx)||(dy===0&&dx===0))return null;const h=g.length,w=g[0].length,bg=background(g);if(bg===null)return null;
 const oldPts=new Set(obj.pts.map(p=>key(p[0],p[1]))),out=clone(g);
 for(const [r,c]of obj.pts)out[r][c]=bg;
 for(const [r,c]of obj.pts){const rr=r+dy,cc=c+dx;if(rr<0||cc<0||rr>=h||cc>=w)return null;if(g[rr][cc]!==bg&&!oldPts.has(key(rr,cc)))return null;out[rr][cc]=g[r][c];}
 return out;
}
function run(g,ast){if(!valid(g))return null;const obj=select(g,ast.partition,ast.selector);if(!obj)return null;
 if(ast.action==='paint')return paint(g,obj,ast.mask,ast.colorMode==='background'?background(g):ast.color);
 if(ast.action==='keep')return wipeOthers(g,obj);
 if(ast.action==='move')return move(g,obj,ast.dy,ast.dx);
 return null;
}
function coloredDiff(input,output,mode){const removed=[],added=[];const bg=background(input);if(bg===null||!valid(output)||output.length!==input.length||output[0].length!==input[0].length)return {removed,added};
 for(let r=0;r<input.length;r++)for(let c=0;c<input[0].length;c++){
  if(input[r][c]!==bg&&output[r][c]===bg)removed.push([r,c]);
  if(input[r][c]===bg&&output[r][c]!==bg)added.push([r,c]);
 }
 return {removed,added};
}
function shiftHints(g,out,obj){const {removed,added}=coloredDiff(g,out);if(!removed.length||!added.length)return [];
 const stats=p=>({minR:Math.min(...p.map(x=>x[0])),maxR:Math.max(...p.map(x=>x[0])),minC:Math.min(...p.map(x=>x[1])),maxC:Math.max(...p.map(x=>x[1]))});
 const x=stats(added),y=stats(obj.pts),z=stats(removed);
 const dr=[x.minR-y.minR,x.maxR-y.maxR,x.minR-z.minR,x.maxR-z.maxR],dc=[x.minC-y.minC,x.maxC-y.maxC,x.minC-z.minC,x.maxC-z.maxC];
 const offsets=[],seen=new Set();for(const r of dr)for(const c of dc){const s=key(r,c);if(!seen.has(s)&&!(r===0&&c===0)&&Math.abs(r)<=g.length&&Math.abs(c)<=g[0].length){seen.add(s);offsets.push([r,c]);}}return offsets;
}
function trainFit(ast,train,trace){for(const pair of train){trace.train_replay_calls++;const pred=run(pair.input,ast);if(!equal(pred,pair.output))return false;}return true;}
function propose(train,testInputs){const t0=Date.now();const trace={candidate_programs:0,train_replay_calls:0,test_program_calls:0,train_fit_count:0,distinct_test_predictions:0,abstention:null,wall_ms:0,representative_programs:[],neural_calls:0};
 if(!Array.isArray(train)||train.length===0||!train.every(p=>valid(p.input)&&valid(p.output))||!Array.isArray(testInputs)||!testInputs.length||!testInputs.every(valid)){trace.abstention='INVALID_INPUT';trace.wall_ms=Date.now()-t0;return {prediction:null,trace};}
 const programs=[],observedColor=new Set(train.flatMap(p=>p.output.flat()));
 // A background-relative paint rule is separately tried, rather than only fixed palette constants.
 for(const partition of PARTITIONS)for(const selector of SELECTORS){
  const firstObj=select(train[0].input,partition,selector);if(!firstObj)continue;
  for(const style of PAINT_MASKS)for(const c of ['background',...observedColor]){
   const ast={partition,selector,action:'paint',mask:style,colorMode:c==='background'?'background':'constant',color:c==='background'?null:c};
   trace.candidate_programs++;if(trainFit(ast,train,trace))programs.push(ast);
  }
  const keep={partition,selector,action:'keep'};trace.candidate_programs++;if(trainFit(keep,train,trace))programs.push(keep);
  // Propose motion parameters from observed train differences, not a fixed per-task delta list.
  const shifts=shiftHints(train[0].input,train[0].output,firstObj);
  for(const [dy,dx] of shifts){const ast={partition,selector,action:'move',dy,dx};trace.candidate_programs++;if(trainFit(ast,train,trace))programs.push(ast);}
 }
 trace.train_fit_count=programs.length;
 if(!programs.length){trace.abstention='NO_TRAIN_CONSISTENT_OBJECT_RULE';trace.wall_ms=Date.now()-t0;return {prediction:null,trace};}
 let consensus=null,conflict=false;const signatures=new Set();
 for(const ast of programs){const out=[];for(const input of testInputs){trace.test_program_calls++;const x=run(input,ast);if(!valid(x)){conflict=true;break;}out.push(x);}
  if(out.length!==testInputs.length)continue;
  const sig=JSON.stringify(out);signatures.add(sig);if(consensus===null)consensus=out;else if(JSON.stringify(consensus)!==sig)conflict=true;
  if(trace.representative_programs.length<3)trace.representative_programs.push(ast);
 }
 trace.distinct_test_predictions=signatures.size;
 if(conflict||signatures.size>1)trace.abstention='AMBIGUOUS_TEST_OR_UNSUPPORTED';else if(consensus===null)trace.abstention='NO_VALID_TEST_PROGRAM';
 trace.wall_ms=Date.now()-t0;return {prediction:trace.abstention===null?consensus:null,trace};
}
function scoreOriginal(task,Bpropose,Qgenerate,P20propose){const train=task.train,inputs=task.test.map(x=>x.input);
 const B=Bpropose(train,inputs,'B'),Q=Qgenerate(train,inputs),P20=P20propose(train,inputs);
 const accepted=[B.proposals,Q.prediction,P20.prediction].filter(x=>x!==null);
 const conflicting=accepted.length>1&&accepted.some(x=>JSON.stringify(x)!==JSON.stringify(accepted[0]));
 const baseline=conflicting?null:accepted[0]||null;
 const C=accepted.length===0?propose(train,inputs):null;
 const final=conflicting?null:baseline||C?.prediction||null;
 // Gold has not been read by B, Q, P20 or C; only scored after all proposals.
 const targets=task.test.map(x=>x.output);const exact=arr=>arr!==null&&arr.length===targets.length&&arr.every((g,i)=>equal(g,targets[i]));
 const cExtra=accepted.length===0&&C!==null&&exact(C.prediction);
 return {B_exact:exact(B.proposals),Q_exact:exact(Q.prediction),P20_exact:exact(P20.prediction),baseline_exact:exact(baseline),combined_exact:exact(final),C_additional_correct:cExtra,C_false_accept:C!==null&&C.prediction!==null&&!exact(C.prediction),combined_false_accept:final!==null&&!exact(final),baseline_conflict:conflicting,C_trace:C?.trace||null,B_trace:B.trace,Q_trace:Q.trace,P20_trace:P20.trace,train_count:train.length,test_count:inputs.length};
}
function fnv32(s){let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619)>>>0;return h>>>0;}
function cohort(files){return files.filter(n=>n.endsWith('.json')).map(name=>({name,h:fnv32('neumann-q3-p21-20261105|'+name)})).sort((a,b)=>a.h-b.h||a.name.localeCompare(b.name)).slice(0,48).map(x=>x.name);}
export {SPEC,PARTITIONS,SELECTORS,PAINT_MASKS,valid,background,segment,select,mask,paint,move,run,shiftHints,propose,scoreOriginal,cohort};
