/* RC50 stronger pre-gold classical development baseline: generic grid logic and object rules. DO NOT claim full classic impossibility. */
export const solveExpanded=function solveExpanded(d) {
 const tr=d.train,te=d.test; const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
 const palette=[...new Set(tr.flatMap(e=>e.output.flat()))].sort((a,b)=>a-b);
 const allColors=[...new Set(tr.flatMap(e=>e.input.flat()).concat(palette))].sort((a,b)=>a-b);
 const programs=[];const add=(id,fn)=>programs.push({id,fn});
 const zeros=(h,w,b=0)=>Array.from({length:h},()=>Array(w).fill(b));
 function layerSplit(g,axis,sep){const h=g.length,w=g[0].length,options=[];
 if(axis==="v"){for(let mid=1;mid<w;mid++)if(g.every(row=>row[mid]===sep)&&mid===w-mid-1)options.push([g.map(row=>row.slice(0,mid)),g.map(row=>row.slice(mid+1))]);if(w%2===0)options.push([g.map(row=>row.slice(0,w/2)),g.map(row=>row.slice(w/2))]);}
 else{for(let mid=1;mid<h;mid++)if(g[mid].every(v=>v===sep)&&mid===h-mid-1)options.push([g.slice(0,mid),g.slice(mid+1)]);if(h%2===0)options.push([g.slice(0,h/2),g.slice(h/2)]);}
 return options;
 }
 for(const ax of ["v","h"])for(const sep of allColors)for(const bg of [0,7,8])for(const truth of [1,2,3,4,5,6,7,8,9,10,11,12,13,14])for(const color of palette) {
  add(`BOOLEAN_${ax}_sep${sep}_bg${bg}_truth${truth}_to${color}`,g=>{
  const ps=layerSplit(g,ax,sep);if(ps.length!==1)throw Error("ambiguous split");
  const [a,b]=ps[0];if(!a.length||!b.length||a.length!==b.length||a[0].length!==b[0].length)throw Error("bad splits");
  return a.map((row,r)=>row.map((v,c)=>((truth>>((Number(v!==bg)<<1)+Number(b[r][c]!==bg)))&1)?color:0));
  });
 }
 for(const ax of ["v","h"])for(const sep of [0,4,5])for(const bg of [0,8])for(const firstWins of [true,false]){
 add(`PANELS_${ax}_sep${sep}_bg${bg}_${firstWins?"FIRST":"LAST"}`,g=>{
 const h=g.length,w=g[0].length;
 const parts=[];if(ax==="v"){const bars=[];for(let j=0;j<w;j++)if(g.every(row=>row[j]===sep))bars.push(j);if(bars.length<2)throw Error("few sep");let boundary=[-1,...bars,w];for(let i=0;i<boundary.length-1;i++){let p=g.map(row=>row.slice(boundary[i]+1,boundary[i+1]));if(p[0].length)parts.push(p)}}
 else{const bars=[];for(let i=0;i<h;i++)if(g[i].every(v=>v===sep))bars.push(i);if(!bars.length)throw Error("few sep");let boundary=[-1,...bars,h];for(let i=0;i<boundary.length-1;i++){let p=g.slice(boundary[i]+1,boundary[i+1]);if(p.length)parts.push(p)}}
 if(parts.length<2||parts.some(p=>p.length!==parts[0].length||p[0].length!==parts[0][0].length))throw Error("parts");
 const out=zeros(parts[0].length,parts[0][0].length,bg);for(const p of (firstWins?[...parts].reverse():parts)){for(let r=0;r<out.length;r++)for(let c=0;c<out[0].length;c++)if(p[r][c]!==bg)out[r][c]=p[r][c]}return out;
 });
 }
 for(let color of palette)for(let bg of [0,7,8])for(let mode of ["OR","AND","XOR"]){add(`MATRIX_BOOLEAN_${mode}_${bg}_${color}`,g=>{
 const h=g.length,w=g[0].length;if(h%2)throw Error("odd");return g.slice(0,h/2).map((row,r)=>row.map((v,c)=>{const a=v!==bg,b=g[r+h/2][c]!==bg;return (mode==="OR"?(a||b):mode==="AND"?(a&&b):(a!==b))?color:0;}));
 });}
 for(let color of palette)for(let bg of [0,7,8])add(`CHECKERGRID_${bg}_${color}`,g=>{
 if(!g.every(row=>row.every(v=>v===bg)))throw Error("not empty");
 return g.map((row,i)=>row.map((_,j)=>i%2===0||j%2===0?color:bg))
 });
 for(const inputcolor of [8,2,4,5,6,7,9])for(const fillColor of palette)add(`COMPLETE_L${inputcolor}_${fillColor}`,g=>{
 const out=g.map(r=>[...r]),h=g.length,w=g[0].length;
 for(let r=0;r<h-1;r++)for(let c=0;c<w-1;c++){const pos=[[r,c],[r,c+1],[r+1,c],[r+1,c+1]],v=pos.map(([a,b])=>g[a][b]);if(v.filter(x=>x===inputcolor).length===3&&v.filter(x=>x===0).length===1){const q=pos[v.indexOf(0)];out[q[0]][q[1]]=fillColor}}
 return out;
 });
 for(let marker of [1,2,3])for(let base of [4,5,7])add(`DROP_MARKER_${marker}_${base}`,g=>{
 const h=g.length,w=g[0].length;if(h<4)throw Error("short");let out=g.map(r=>[...r]);
 const places=[];for(let r=0;r<h-1;r++)for(let c=0;c<w;c++)if(g[r][c]===marker&&g[r+1][c]===base)places.push([r,c]);
 if(!places.length)throw Error("no marker");
 for(const [r,c] of places){out[r][c]=0;out[h-1][c]=marker}return out;
 });
 // Exact source-only image template matching: distinguish genuine colored template vs single-color 8 objects.
 for(let sourceColor of [8,5,4])for(let bg of [0,8])add(`TEMPLATE_REPLACE_obj${sourceColor}_bg${bg}`,g=>{
  const h=g.length,w=g[0].length;let mark=new Set(),nonmark=[];
  for(let r=0;r<h;r++)for(let c=0;c<w;c++)if(g[r][c]!==bg){if(g[r][c]===sourceColor)mark.add(`${r},${c}`);else nonmark.push([r,c])}
  if(!nonmark.length||!mark.size)throw Error("no template");
  let r0=Math.min(...nonmark.map(x=>x[0])),r1=Math.max(...nonmark.map(x=>x[0])),c0=Math.min(...nonmark.map(x=>x[1])),c1=Math.max(...nonmark.map(x=>x[1]));
  const th=r1-r0+1,tw=c1-c0+1;const pattern=g.slice(r0,r1+1).map(row=>row.slice(c0,c1+1));
  const out=g.map(row=>[...row]);
  for(let r=0;r+th<=h;r++)for(let c=0;c+tw<=w;c++){
   if(r===r0&&c===c0)continue;
   let fits=true,count=0;for(let i=0;i<th;i++)for(let j=0;j<tw;j++){const v=g[r+i][c+j];if((pattern[i][j]!==bg)!==(v===sourceColor))fits=false;if(v===sourceColor)count++}
   if(fits&&count){for(let i=0;i<th;i++)for(let j=0;j<tw;j++)if(pattern[i][j]!==bg)out[r+i][c+j]=pattern[i][j];}
  }for(let r=r0;r<=r1;r++)for(let c=c0;c<=c1;c++)out[r][c]=bg;return out;
 });
 let checked=0,compatible=[],predClasses=new Map();
 for(const p of programs){checked++;let works=true;for(const ex of tr){try{if(!eq(p.fn(ex.input),ex.output)){works=false;break}}catch(e){works=false;break}}if(!works)continue;
 compatible.push(p.id);try{const pred=te.map(x=>p.fn(x.input));const key=JSON.stringify(pred);if(!predClasses.has(key))predClasses.set(key,{operator:p.id,pred,n:0});predClasses.get(key).n++;}catch(e){}}
 const status=predClasses.size===0?"HOLD_NO_SOURCE_PROGRAM":predClasses.size>1?"HOLD_OUTPUT_AMBIGUITY":"SOURCE_CONSENSUS_ONLY";
 return {status,checked,n_compatible:compatible.length,n_prediction_classes:predClasses.size,representatives:[...predClasses.values()].slice(0,3),new_neural_forwards:0}
};
