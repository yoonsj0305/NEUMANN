"""Q3: derive NEW algebraic data types and executable transition operators from I/O.

A fixed, generic finite-state transducer hypothesis class is human supplied.
State constructors, state counts, output chunks, and transition laws are NOT.
Both plain complete input/output training and prefix-observed training work.

This does NOT prove unrestricted creativity or an independently novel AI
method. It proves scoped, causal data-type/operator invention beyond the
previous elementwise scalar/map/filter VM.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from hashlib import sha256
import json


def fingerprint(obj):
    return sha256(json.dumps(obj,sort_keys=True,
                 separators=(",",":")).encode()).hexdigest()[:16]


class NotRepresentable(ValueError):
    pass


def learn_prefix_graph(examples):
    by_input={}
    for x,y in examples:
        if type(x) not in (list,tuple) or type(y) not in (list,tuple):
            raise NotRepresentable("only finite input-output sequences")
        x=tuple(x);y=tuple(y)
        if any(type(s) not in (int,str) for s in x+y):
            raise NotRepresentable("unrecognized symbol")
        if x in by_input and by_input[x]!=y:
            raise NotRepresentable("ambiguous supervised output")
        by_input[x]=y
    if not by_input or by_input.get(())!=():
        raise NotRepresentable("missing empty-sequence observation")
    for seq in by_input:
        for i in range(len(seq)):
            if seq[:i] not in by_input:
                raise NotRepresentable("requires prefix I/O observations")
    ordered=sorted(by_input,key=lambda x:(len(x),x))
    state={prefix:i for i,prefix in enumerate(ordered)}
    edges={i:{} for i in range(len(ordered))}
    for prefix in ordered:
        if not prefix:continue
        parent=prefix[:-1];symbol=prefix[-1]
        old,new=by_input[parent],by_input[prefix]
        if new[:len(old)]!=old:
            raise NotRepresentable("output prefix violated")
        edges[state[parent]][symbol]=(new[len(old):],state[prefix])
    return state[()],edges


def closure_partition(edges,pairs,previous=None):
    """Congruence-closed state merging. Output conflicts reject hypothesis."""
    n=len(edges);parent=list(range(n))
    def root(x):
        while x!=parent[x]:
            parent[x]=parent[parent[x]]
            x=parent[x]
        return x
    groups={}
    for i,group in enumerate(previous if previous is not None else range(n)):
        groups.setdefault(group,[]).append(i)
    for group in groups.values():
        first=group[0]
        for v in group[1:]:parent[v]=first
    outgoing={}
    for i in range(n):
        q=root(i);targets=outgoing.setdefault(q,{})
        for sym,(chunk,to) in edges[i].items():
            if sym in targets:
                existing,oldto=targets[sym]
                if existing!=chunk or root(oldto)!=root(to):
                    raise RuntimeError("previous type partition inconsistent")
            else:targets[sym]=(chunk,to)
    work=list(pairs)
    while work:
        a,b=work.pop();a,b=root(a),root(b)
        if a==b:continue
        if a>b:a,b=b,a
        left=outgoing.setdefault(a,{})
        right=outgoing.pop(b,{})
        for sym,(chunk,to) in right.items():
            if sym in left:
                prev,prevto=left[sym]
                if prev!=chunk:return None
                work.append((prevto,to))
            else:left[sym]=(chunk,to)
        parent[b]=a
    return tuple(root(i) for i in range(n))


def canonical_edges(edges,partition,initial):
    transitions={}
    for u,outs in edges.items():
        state=partition[u]
        for symbol,(emit,target) in outs.items():
            key=(state,symbol)
            value=(tuple(emit),partition[target])
            if key in transitions and transitions[key]!=value:
                raise RuntimeError("inconsistent learned type")
            transitions[key]=value
    outgoing={}
    for (q,sym),(emit,to) in transitions.items():
        outgoing.setdefault(q,{})[sym]=(emit,to)
    names={partition[initial]:0}
    queue=deque([partition[initial]])
    while queue:
        q=queue.popleft()
        for sym,(_,to) in sorted(outgoing.get(q,{}).items(),
                                  key=lambda p:str(p[0])):
            if to not in names:
                names[to]=len(names);queue.append(to)
    if len(names)!=len(set(partition)):
        raise RuntimeError("unreachable invented type constructor")
    cases=tuple(sorted(
        ((names[q],sym,tuple(chunk),names[to])
         for (q,sym),(chunk,to) in transitions.items()),
        key=lambda x:(x[0],str(x[1]))))
    return cases,len(names)


@dataclass(frozen=True)
class LearnedOperator:
    num_states:int
    transitions:tuple

    def to_ast(self):
        name="invented_state_type_"+fingerprint(
            [self.num_states,self.transitions])
        return ["DefineAlgebraicType",name,
                ["Variant",["S"+str(i) for i in range(self.num_states)]],
                ["DefineOperator","invented_transition_"+name[-16:],
                 ["Product",[name,"InputSymbol"]],
                 ["Product",["OutputSequence",name]],
                 ["Cases",[[q,sym,list(out),to]
                           for q,sym,out,to in self.transitions],
                  ["Abstain","UNSEEN_TRANSITION"]]]]

    def apply(self,word):
        rules={(q,sym):(chunk,to)
               for q,sym,chunk,to in self.transitions}
        state=0;result=[]
        for symbol in word:
            if (state,symbol) not in rules:return None
            chunk,state=rules[state,symbol]
            result.extend(chunk)
        return result


def merge_prefix_graph(initial,edges):
    """Blue-fringe construction; dynamically discovers number of states."""
    n=len(edges)
    partition=tuple(range(n));red={partition[initial]}
    attempts=0
    while True:
        blue=set()
        for u,outs in edges.items():
            if partition[u] not in red:continue
            blue.update(partition[v] for _,v in outs.values()
                        if partition[v] not in red)
        if not blue:break
        candidate=min(blue);merged=False
        for prior_state in sorted(red):
            attempts+=1
            new_partition=closure_partition(
                edges,[(prior_state,candidate)],partition)
            if new_partition is None or new_partition==partition:continue
            partition=new_partition
            red={partition[v] for v in red}
            merged=True
            break
        if not merged:red.add(candidate)
        if attempts>n*n:raise RuntimeError("type search budget exceeded")
    cases,k=canonical_edges(edges,partition,initial)
    return LearnedOperator(k,cases),attempts


def learn_new_type(examples):
    """Known prefix traces, including variable-length output chunks."""
    root,edges=learn_prefix_graph(examples)
    op,attempts=merge_prefix_graph(root,edges)
    if any(op.apply(x)!=list(y) for x,y in examples):
        raise RuntimeError("learned type fails TRAIN constraint")
    return op,attempts


def elementwise_impossibility_witness(examples):
    """Witness against old stateless pointwise map/filter language."""
    seen={};conflicts=[];expansion=0
    for word,out in examples:
        if len(out)>len(word):expansion+=1
        if len(out)!=len(word):continue
        for symbol,y in zip(word,out):
            if symbol in seen and seen[symbol]!=y:
                conflicts.append((symbol,seen[symbol],y))
            seen[symbol]=y
    return {"same_symbol_different_outputs":len(conflicts),
            "outputs_longer_than_inputs":expansion,
            "old_elementwise_map_impossible":bool(conflicts or expansion)}


def learn_position_aligned_graph(examples):
    """Infer prefix transition outputs from ordinary equal-length whole I/O."""
    seen={():()}
    for x,y in examples:
        if len(x)!=len(y):raise NotRepresentable("non-aligned output lengths")
        for i in range(len(x)):
            prefix=tuple(x[:i+1])
            result=tuple(y[:i+1])
            if prefix in seen and seen[prefix]!=result:
                raise NotRepresentable("noncausal position alignment")
            seen[prefix]=result
    ordered=sorted(seen,key=lambda x:(len(x),x))
    index={w:i for i,w in enumerate(ordered)}
    edges={i:{} for i in range(len(ordered))}
    for w in ordered:
        if not w:continue
        edges[index[w[:-1]]][w[-1]]=((seen[w][-1],),index[w])
    return index[()],edges


def longest_prefix(words):
    if not words:return ()
    prefix=tuple(words[0]);n=len(prefix)
    for word in words[1:]:
        m=min(n,len(word));j=0
        while j<m and word[j]==prefix[j]:j+=1
        n=j
        if n==0:break
    return prefix[:n]


@dataclass(frozen=True)
class LearnedSubsequentialOperator:
    initial_emission:tuple
    internal:LearnedOperator

    def to_ast(self):
        return ["DefineSubsequentialOperator",
                "invented_recursive_language_"+fingerprint([
                    self.initial_emission,self.internal.to_ast()]),
                ["InitialEmission",list(self.initial_emission)],
                self.internal.to_ast()]

    def apply(self,word):
        result=self.internal.apply(word)
        return None if result is None else list(self.initial_emission)+result


def learn_from_complete_io(examples):
    """No intermediate output values, states, or transitions supplied."""
    by_input={}
    for xs,ys in examples:
        x=tuple(xs);y=tuple(ys)
        if x in by_input and by_input[x]!=y:
            raise NotRepresentable("conflicting target outputs")
        by_input[x]=y
    if not by_input:raise NotRepresentable("empty target task")
    if all(len(x)==len(y) for x,y in by_input.items()):
        root,edges=learn_position_aligned_graph(examples)
        op,attempts=merge_prefix_graph(root,edges)
        program=LearnedSubsequentialOperator((),op)
        if any(program.apply(x)!=list(y) for x,y in examples):
            raise RuntimeError("invented aligned operator invalid")
        return program,attempts
    prefixes=set()
    for word in by_input:
        prefixes.update(word[:i] for i in range(len(word)+1))
    ordered=sorted(prefixes,key=lambda w:(len(w),w))
    index={w:i for i,w in enumerate(ordered)}
    prefix_out={}
    for prefix in ordered:
        suffix_outputs=[out for word,out in by_input.items()
                        if word[:len(prefix)]==prefix]
        prefix_out[prefix]=longest_prefix(suffix_outputs)
    for word,out in by_input.items():
        if prefix_out[word]!=out:
            raise NotRepresentable("noncausal final output")
    edges={i:{} for i in range(len(ordered))}
    for word in ordered:
        if not word:continue
        parent=word[:-1]
        a,b=prefix_out[parent],prefix_out[word]
        if b[:len(a)]!=a:
            raise NotRepresentable("incompatible output prefix")
        edges[index[parent]][word[-1]]=(b[len(a):],index[word])
    op,attempts=merge_prefix_graph(index[()],edges)
    program=LearnedSubsequentialOperator(prefix_out[()],op)
    if any(program.apply(x)!=list(y) for x,y in examples):
        raise RuntimeError("invented subsequential operator invalid")
    return program,attempts


class SelfExtendingLanguage:
    """Persistent generated type library; reuses exact programs or invents."""
    def __init__(self,prior=None):
        self.definitions=dict(prior or {})
        self.history=[]

    def solve(self,examples):
        for name,obj in sorted(self.definitions.items()):
            program=self._decode(obj)
            if all(program.apply(x)==list(y) for x,y in examples):
                self.history.append({"kind":"reuse","symbol":name})
                return name,program,"reuse"
        learned,_=learn_from_complete_io(examples)
        new_ast=learned.to_ast();name=new_ast[1]
        self.definitions[name]={
            "ast":new_ast,"initial_emission":list(learned.initial_emission),
            "states":learned.internal.num_states,
            "rules":[[q,s,list(chunk),to] for q,s,chunk,to
                     in learned.internal.transitions]}
        self.history.append({
            "kind":"invent_type_and_transition_operator",
            "symbol":name,"new_state_count":learned.internal.num_states,
            "new_rule_count":len(learned.internal.transitions)})
        return name,learned,"invent"

    @staticmethod
    def _decode(obj):
        rules=tuple((q,s,tuple(chunk),to) for q,s,chunk,to in obj["rules"])
        model=LearnedSubsequentialOperator(
            tuple(obj["initial_emission"]),
            LearnedOperator(obj["states"],rules))
        if obj["ast"]!=model.to_ast():
            raise ValueError("TAMPERED_GENERATED_LANGUAGE_DEFINITION")
        return model

    def dump(self):
        return {"schema":"neumann.self-extending-state-type-language.v1",
                "definitions":self.definitions,"history":self.history}

    @classmethod
    def load(cls,record):
        if record.get("schema")!="neumann.self-extending-state-type-language.v1":
            raise ValueError("UNKNOWN_SAVED_LANGUAGE_SCHEMA")
        obj=cls(record["definitions"]);obj.history=list(record["history"])
        for definition in obj.definitions.values():obj._decode(definition)
        return obj
