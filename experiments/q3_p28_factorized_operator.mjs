/**
 * NEUMANN 1 / P2.8 feasibility: generate a typed executable spatial operator
 * by cross-example factorization, not a task-ID lookup or a fixed-name ARC macro.
 * This solver is deterministic, gold-blind, and abstains on train inconsistency.
 * Scope is NxM -> N^2 x M^2 only. Does NOT establish general autonomous invention.
 */
export const CONTRACT = Object.freeze({
  schema: 'neumann.q3.p28.factorized-operator.v1',
  sourceGrammar: 'two independently input-indexed cells; zero-tested selectors; result in {0,outer,inner}',
  maxPrograms: 81,
  maxGrid: 30,
  teacherCalls: 0,
  neuralCalls: 0,
  goldBlind: true,
});
const Z = ['zero', 'outer', 'inner'];
const sig = x => JSON.stringify(x);
const valid = x => Array.isArray(x) && x.length > 0 && x.length <= 30 &&
    Array.isArray(x[0]) && x[0].length > 0 && x[0].length <= 30 &&
    x.every(row => Array.isArray(row) && row.length === x[0].length &&
        row.every(v => Number.isInteger(v) && v >= 0 && v <= 9));
function shapeSupported(x) {
    return valid(x) && x.length ** 2 <= CONTRACT.maxGrid && x[0].length ** 2 <= CONTRACT.maxGrid;
}
// Scheme invented by the factorization: take two copies of the *input* with
// independent spatial indices; infer a 4-row truth-table mapping zero masks
// to one of three typed source expressions. No output cells are memorized.
export function interpret(ast, x) {
    if (!shapeSupported(x) || !ast || !Array.isArray(ast.selector) || ast.selector.length !== 4 ||
        ast.selector.some(v => !Z.includes(v))) return null;
    const h=x.length,w=x[0].length, out=[];
    for(let row=0; row<h*h; row++) {
        const line=[];
        for(let col=0; col<w*w; col++) {
            const outer=x[Math.floor(row/h)][Math.floor(col/w)];
            const inner=x[row%h][col%w];
            const key=(outer===0?2:0)+(inner===0?1:0);
            const kind=ast.selector[key];
            line.push(kind==='zero'?0:kind==='outer'?outer:inner);
        }
        out.push(line);
    }
    return out;
}
function equal(a,b) { return a!==null && sig(a)===sig(b); }
export function candidatePrograms() {
    const ans=[];
    for (let n=0;n<81;n++) {
        let r=n,sel=[];
        for(let k=0;k<4;k++){sel.push(Z[r%3]);r=Math.floor(r/3);}
        ans.push({kind:'factorized-zero-conditional',selector:sel});
    }
    return ans;
}
export function propose(train, testInputs) {
    const t0=process.hrtime.bigint();
    const trace={schema:CONTRACT.schema, enumerated:0, train_pair_evaluations:0,
        exact_train_programs:0, distinct_test_predictions:0, elapsed_ms:null,
        abstention:null, generated_AST:null};
    const finish=(prediction,reason=null)=>{
        trace.abstention=reason;
        trace.elapsed_ms=Number(process.hrtime.bigint()-t0)/1e6;
        return {prediction,trace};
    };
    if(!Array.isArray(train)||train.length===0||!train.every(p=>shapeSupported(p?.input)&&valid(p?.output))||
       !Array.isArray(testInputs)||!testInputs.length||!testInputs.every(shapeSupported))
       return finish(null,'INVALID_OR_OUT_OF_SCOPE_INPUT');
    const candidates=[];
    for(const ast of candidatePrograms()) {
        trace.enumerated++;
        let ok=true;
        for(const p of train){
            trace.train_pair_evaluations++;
            if(!equal(interpret(ast,p.input),p.output)){ok=false;break;}
        }
        if(ok) candidates.push(ast);
    }
    trace.exact_train_programs=candidates.length;
    if(!candidates.length) return finish(null,'NO_TRAIN_CONSISTENT_OPERATOR');
    const preds = new Map();
    for(const ast of candidates){
        const values=testInputs.map(g=>interpret(ast,g));
        if(values.some(v=>v===null))return finish(null,'UNSUPPORTED_TEST_EXECUTION');
        const key=sig(values);
        if(!preds.has(key))preds.set(key,{values,ast});
    }
    trace.distinct_test_predictions=preds.size;
    if(preds.size!==1)return finish(null,'AMBIGUOUS_TRAIN_CONSISTENT_OPERATORS');
    const chosen=preds.values().next().value;
    trace.generated_AST=chosen.ast;
    return finish(chosen.values);
}

// Shape-only proof for 3x3 -> 9x9: P2.7 depth <=2 has only
// transpose/rotation, cropping, scale2, and 2x tiling. A 3x3 input
// cannot become 9x9 in two such steps. The proof is conditional on that
// frozen grammar and no unlisted primitives.
export function p27ShapeCeilingFor3x3To9x9() {
    const reachable=new Set(['3x3']);
    let frontier=[[3,3]];
    for(let depth=0;depth<2;depth++) {
        const next=[];
        for(const [h,w] of frontier) {
            const cases=[[h,w],[w,h],[2*h,2*w],[2*h,w],[h,2*w]];
            // Cropping can only shrink dimensions; include every legal size.
            for(let hh=1;hh<=h;hh++)for(let ww=1;ww<=w;ww++)cases.push([hh,ww]);
            for(const [a,b] of cases) {
                if(a>30||b>30)continue;
                const key=a+'x'+b;
                if(!reachable.has(key))next.push([a,b]);
                reachable.add(key);
            }
        }
        frontier=next;
    }
    return !reachable.has('9x9');
}
