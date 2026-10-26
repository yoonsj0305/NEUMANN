/* Actual frozen RC50 strong classical source-consensus baseline. NOT neural. Original GitHub ARC Prize public training, 12 sequential lexicographic <=2500-byte entries index49..60. */
export const solveClassical=function solveClassical(d){
const tr=d.train,te=d.test;
const gshape=g=>[g.length,g[0].length];
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const rotate=g=>g[0].map((_,c)=>g.map(row=>row[c]).reverse());
const mirrorH=g=>g.map(r=>[...r].reverse());
const mirrorV=g=>[...g].reverse().map(r=>[...r]);
const transpose=g=>g[0].map((_,c)=>g.map(row=>row[c]));
const transform=(g,t)=>{let z=g.map(r=>[...r]);if(t>=4)z=mirrorH(z);for(let k=0;k<t%4;k++)z=rotate(z);return z};
const crop=(g,bg)=>{let pts=[];g.forEach((r,i)=>r.forEach((v,j)=>{if(v!==bg)pts.push([i,j])}));if(!pts.length)throw Error("empty");let r0=Math.min(...pts.map(x=>x[0])),r1=Math.max(...pts.map(x=>x[0])),c0=Math.min(...pts.map(x=>x[1])),c1=Math.max(...pts.map(x=>x[1]));return g.slice(r0,r1+1).map(r=>r.slice(c0,c1+1))};
const zeros=(h,w,b=0)=>Array.from({length:h},()=>Array(w).fill(b));
const shift=(g,dx,dy,bg)=>g.map((r,i)=>r.map((_,j)=>(g[i-dy]||[])[j-dx]??bg));
const period=(g,h,w)=>Array.from({length:h},(_,i)=>Array.from({length:w},(_,j)=>g[i%g.length][j%g[0].length]));
const nonzeroColors=(d)=>[...new Set(d.train.flatMap(e=>e.output.flat()).concat(d.train.flatMap(e=>e.input.flat())))].sort((a,b)=>a-b);
const colors=nonzeroColors(d);
const programs=[];
const add=(id,fun)=>programs.push({id,fun});
for(let t=0;t<8;t++)add(`DIHEDRAL${t}`,g=>transform(g,t));
for(let bg of [0,8,7]){add(`CROP_${bg}`,g=>crop(g,bg));for(let t=0;t<8;t++)add(`CROP${bg}_T${t}`,g=>transform(crop(g,bg),t))}
for(let dx of [-2,-1,0,1,2])for(let dy of [-2,-1,0,1,2])if(dx||dy)for(let bg of [0,5,7,8])add(`SHIFT${dx}_${dy}_${bg}`,g=>shift(g,dx,dy,bg));
for(let to of colors)for(let from of [0,1,2,3,4,5,6,7,8,9])if(from!==to){add(`RECOLOR${from}_${to}`,g=>g.map(row=>row.map(v=>v===from?to:v)));add(`BACKGROUND${from}_${to}`,g=>g.map(row=>row.map(v=>v===from?to:v)))}
for(let color of colors){add(`MASK_FOREGROUND${color}`,g=>g.map(row=>row.map(v=>v?color:0)));add(`MASK_BACKGROUND${color}`,g=>g.map(row=>row.map(v=>v?0:color)));for(let bg of [0,5,7,8]){add(`SHIFTLEFT_FILL${bg}_${color}`,g=>shift(g,-1,0,bg).map(row=>row.map(v=>v===bg?color:v)));}}
for(let s of [2,3])add(`EXPAND${s}`,g=>g.flatMap(row=>Array.from({length:s},()=>row.flatMap(v=>Array(s).fill(v)))));
for(let h of [2,3,4])for(let w of [2,3,4])add(`TILE${h}_${w}`,g=>period(g,g.length*h,g[0].length*w));
for(let bg of [0,5,7,8])for(let method of ["xor","or","and","left","right","overlap"]){
for(let axis of ["v","h"])add(`MERGE_${axis}_${method}_bg${bg}`,g=>{
 const [h,w]=gshape(g);let z=axis==="v"?(w%2===1?g.map(r=>r.slice(0,(w-1)/2)):null):(h%2===1?g.slice(0,(h-1)/2):null);
 if(!z)throw Error("shape");let a=z,b=axis==="v"?g.map(r=>r.slice((w+1)/2)):g.slice((h+1)/2);
 if(!a.length||a.length!==b.length||a[0].length!==b[0].length)throw Error("shape");return a.map((r,i)=>r.map((va,j)=>{const vb=b[i][j];const aa=va!==bg,bb=vb!==bg;
 if(method==="xor")return (aa!==bb)?(aa?va:vb):bg;
 if(method==="or")return aa?va:vb;
 if(method==="and")return (aa&&bb)?va:bg;
 if(method==="left")return va;
 if(method==="right")return vb;
 return bb?vb:va}))
})}
for(let axis of ["v","h"])for(let bg of [0,8,7])add(`PANEL_OVERLAY_${axis}_${bg}`,g=>{
 const [h,w]=gshape(g),pieces=[];
 if(axis==="v"){const bars=[];for(let j=0;j<w;j++)if(g.every(row=>row[j]===bg))bars.push(j);if(bars.length<2)throw Error("bars");let starts=[0,...bars.map(x=>x+1)],ends=[...bars,w];for(let k=0;k<starts.length;k++)if(ends[k]>starts[k])pieces.push(g.map(r=>r.slice(starts[k],ends[k])));}
 else{const bars=[];for(let i=0;i<h;i++)if(g[i].every(v=>v===bg))bars.push(i);if(!bars.length)throw Error("bars");let starts=[0,...bars.map(x=>x+1)],ends=[...bars,h];for(let k=0;k<starts.length;k++)if(ends[k]>starts[k])pieces.push(g.slice(starts[k],ends[k]));}
 if(pieces.length<2||pieces.some(p=>!p.length||p.length!==pieces[0].length||p[0].length!==pieces[0][0].length))throw Error("unequal pieces");
 let out=zeros(pieces[0].length,pieces[0][0].length,bg);for(let p of pieces){for(let i=0;i<out.length;i++)for(let j=0;j<out[0].length;j++)if(p[i][j]!==bg)out[i][j]=p[i][j]}return out;
});
let checked=0,compatible=[];
for(const p of programs){checked++;let pass=true;for(const ex of tr){try{if(!eq(p.fun(ex.input),ex.output)){pass=false;break}}catch(e){pass=false;break}}if(pass)compatible.push(p);}
const unique=new Map();for(const p of compatible){try{const outputs=te.map(e=>p.fun(e.input));const key=JSON.stringify(outputs);if(!unique.has(key))unique.set(key,{names:[],outputs});unique.get(key).names.push(p.id)}catch(e){}}
const status=unique.size===0?"HOLD_NO_SOURCE_PROGRAM":unique.size>1?"HOLD_OUTPUT_AMBIGUITY":"SOURCE_CONSENSUS_ONLY";
return {status,programs_checked:checked,compatible:compatible.length,prediction_classes:unique.size,representatives:[...unique.values()].slice(0,3).map(x=>({name:x.names[0],n_equiv:x.names.length,output:x.outputs})),new_neural_forwards:0}
};
