"""Q3G first REAL-SOURCE CPU neural variable-length invariant-string generation.

Only Microsoft Loopy programs whose actual ancestor license body is recognized
as Apache 2 or BSD 3. Source family entire held out; no training on escrow Q3F.
Not an SMT certificate or typed AST generator. Strong classical verifier absent.
"""
from __future__ import annotations
import argparse, collections, difflib, hashlib, io, json, random, re, time, zipfile
from pathlib import Path
import numpy as np
import torch
from torch import nn
from link_real_invariants import run as pair_index
from license_body_audit import class_license

SEED=20261018
CAP_SOURCE=2600
CAP_TARGET=180
VOCAB_LIMIT=100
FEATURES=512
EMBED=24
HIDDEN=64
EPOCHS=12
BATCH=16
HOLDOUT_GROUPS={
 "dataset/loop_invariants/LinearArbitrary-SeaHorn/VeriMAP",
 "dataset/loop_invariants/sv-benchmarks/loop-lit",
}
PERMISSIVE={"APACHE_2_0","MIT","BSD_3_CLAUSE"}
REGEX=re.compile(r"[A-Za-z_][A-Za-z_0-9]*|\d+|==|>=|<=|!=|&&|\|\||==>|[^\s]")

def vector(text):
    v=np.zeros(FEATURES,dtype=np.float32)
    chunks=REGEX.findall(text[:CAP_SOURCE])
    for i,tok in enumerate(chunks):
        # Include local token neighborhoods; no Python hash randomization.
        for value in (tok, tok+" "+chunks[i+1] if i+1<len(chunks) else tok):
            slot=int.from_bytes(hashlib.blake2s(value.encode(),digest_size=4).digest(),"big")%FEATURES
            v[slot]+=1.0
    norm=np.sqrt((v*v).sum())
    if norm:v/=norm
    return v

class EncoderDecoder(nn.Module):
    def __init__(self,vocab):
        super().__init__()
        self.context=nn.Linear(FEATURES,HIDDEN)
        self.embed=nn.Embedding(vocab,EMBED)
        self.rnn=nn.GRU(EMBED,HIDDEN,batch_first=True)
        self.out=nn.Linear(HIDDEN,vocab)
    def forward(self,inputs,prefix):
        h=torch.tanh(self.context(inputs))[None,:,:].contiguous()
        out,_=self.rnn(self.embed(prefix),h)
        return self.out(out)
    def generate(self,inputs,bos,eos,max_steps):
        state=torch.tanh(self.context(inputs))[None,:,:].contiguous()
        prev=torch.full((len(inputs),1),bos,dtype=torch.long)
        tokens=[[] for _ in range(len(inputs))]
        alive=[True]*len(inputs)
        with torch.no_grad():
            for _ in range(max_steps):
                logits,state=self.rnn(self.embed(prev),state)
                prev=self.out(logits[:,-1:,:]).argmax(-1)
                for i,v in enumerate(prev.flatten().tolist()):
                    if not alive[i]:continue
                    if v==eos:alive[i]=False
                    else:tokens[i].append(v)
                if not any(alive):break
        return tokens

def load_published_pairs(wb,archive):
    indexed=pair_index(wb,archive)
    examples=indexed["per_pair_identity_only"]
    with zipfile.ZipFile(io.BytesIO(archive.read_bytes())) as z:
        license_types={}
        for p in {x["license_path_hint"] for x in examples if x["license_path_hint"]}:
            license_types[p]=class_license(z.read(p))
        rows=[];rejected=collections.Counter()
        for x in examples:
            lic=license_types.get(x["license_path_hint"],"UNLICENSED")
            if lic not in PERMISSIVE:
                rejected["LICENSE_NOT_CONFIRMED"]+=1;continue
            source=z.read(x["program_path"]).decode("utf-8",errors="replace")
            # Invariants must be aligned with exact row identity without
            # committing third-party source or answer texts.
            row_file=x["published_row_source"]
            # Source path + hash is unique across 398.
            label=None
            for row in indexed.get("workbook_rows",[]):
                if row.get("A")==row_file:label=row.get("B")
            # workbook_rows intentionally absent from public hash-only index.
            rows.append({"source":source,"source_sha256":x["source_sha256"],
                "published_row_source":row_file,"group":x["source_group"],
                "license":lic,"label":label})
    return rows,rejected

def exact_inputs(wb,archive):
    from inventory_real_corpus import workbook_tables
    rows,rej=load_published_pairs(wb,archive)
    table=workbook_tables(wb.read_bytes())["Sheet1"]
    mapping=collections.defaultdict(list)
    for row in table[1:]:
        mapping[row.get("A","").strip()].append(row.get("B","").strip())
    clean=[]
    for row in rows:
        labels=mapping[row["published_row_source"]]
        if len(labels)!=1 or not labels[0]:
            rej["AMBIGUOUS_PUBLISHED_LABEL"]+=1;continue
        target=labels[0].replace("\r\n","\n")
        if len(target)>CAP_TARGET:
            rej["TARGET_LONGER_THAN_PREDECLARED_CAP"]+=1;continue
        if target in row["source"]:
            rej["LABEL_VISIBLE_VERBATIM_IN_SOURCE"]+=1;continue
        row["label"]=target
        clean.append(row)
    return clean,rej

def train_eval(wb,archive,checkpoint):
    torch.manual_seed(SEED);np.random.seed(SEED);random.seed(SEED)
    torch.set_num_threads(2)
    rows,rejections=exact_inputs(wb,archive)
    train=[r for r in rows if r["group"] not in HOLDOUT_GROUPS]
    test=[r for r in rows if r["group"] in HOLDOUT_GROUPS]
    if not train or not test:raise RuntimeError("TRAIN_OR_HELDOUT_EMPTY")
    assert not {x["source_sha256"] for x in train}&{x["source_sha256"] for x in test}
    # Group split and syntax vocabulary are frozen before looking at labels.
    chars=collections.Counter(c for row in train for c in row["label"])
    abc=[c for c,_ in chars.most_common(VOCAB_LIMIT-4)]
    tokens=["<PAD>","<BOS>","<EOS>","<UNK>"]+abc
    pad,bos,eos,unk=0,1,2,3
    ids={v:i for i,v in enumerate(tokens)}
    maxseq=max(len(row["label"]) for row in train)+1
    def encode(row):
        s=[ids.get(c,unk) for c in row["label"]]+[eos]
        return [bos]+s[:-1]+[pad]*(maxseq-len(s)),s+[pad]*(maxseq-len(s))
    inputs=torch.tensor(np.stack([vector(r["source"]) for r in train]))
    encoder=[encode(r) for r in train]
    pin=torch.tensor([p for p,_ in encoder],dtype=torch.long)
    goal=torch.tensor([g for _,g in encoder],dtype=torch.long)
    net=EncoderDecoder(len(tokens));optimizer=torch.optim.Adam(net.parameters(),lr=0.004)
    lossf=nn.CrossEntropyLoss(ignore_index=pad)
    start=time.perf_counter()
    losses=[]
    net.train()
    for epoch in range(EPOCHS):
        order=torch.randperm(len(train))
        cumul=0.0
        for chunk in order.split(BATCH):
            prediction=net(inputs[chunk],pin[chunk])
            loss=lossf(prediction.reshape(-1,len(tokens)),goal[chunk].reshape(-1))
            optimizer.zero_grad();loss.backward();nn.utils.clip_grad_norm_(net.parameters(),1.0)
            optimizer.step()
            cumul+=loss.item()*len(chunk)
        losses.append(round(cumul/len(train),6))
    wall=(time.perf_counter()-start)*1000
    net.eval()
    testinputs=torch.tensor(np.stack([vector(r["source"]) for r in test]))
    produced=net.generate(testinputs,bos,eos,CAP_TARGET)
    predictions=["".join(tokens[i] if 4<=i<len(tokens) else "" for i in chars) for chars in produced]
    nearest=[]
    with torch.no_grad():
        similarity=(testinputs @ inputs.T)
        best=similarity.argmax(1).tolist()
        nearest=[train[i]["label"] for i in best]
    target=[r["label"] for r in test]
    def similarity_metric(a,b):
        return difflib.SequenceMatcher(None,a,b,autojunk=False).ratio()
    nn_exact=sum(a==b for a,b in zip(predictions,target))
    retrieval_exact=sum(a==b for a,b in zip(nearest,target))
    nn_char=sum(similarity_metric(a,b) for a,b in zip(predictions,target))/len(test)
    retrieval_char=sum(similarity_metric(a,b) for a,b in zip(nearest,target))/len(test)
    checkpoint.parent.mkdir(parents=True,exist_ok=True)
    torch.save({"state_dict":net.state_dict(),"vocabulary":tokens,
        "feature_definition":"blake2s-hashed-token-unigrams-and-bigrams/512",
        "checkpoint_requires_training_seal":True,
        "train_source_hashes":[r["source_sha256"] for r in train],
        "test_source_hashes":[r["source_sha256"] for r in test],
        "train_source_groups":sorted({r["group"] for r in train}),
        "holdout_groups":sorted(HOLDOUT_GROUPS)},checkpoint)
    data=checkpoint.read_bytes()
    return {"status":"REAL_LICENSED_GROUP_DISJOINT_CPU_TRAINING_COMPLETE",
       "data_provenance":"Microsoft Loopy published successful invariant report (NOT independently recertified here)",
       "training_examples":len(train),"heldout_examples":len(test),
       "training_source_groups":len({r["group"] for r in train}),
       "heldout_groups":sorted(HOLDOUT_GROUPS),
       "excluded_by_reason":dict(rejections),
       "train_cross_holdout_exact_source_hash_overlap":0,
       "architecture":"source hashed 512-d token features + neural GRU autoregressive character generator",
       "operator_structure":"VARIABLE_LENGTH_TEXT_NOT_A_TYPED_AST",
       "parameters":sum(p.numel() for p in net.parameters()),
       "epochs":EPOCHS,"loss_per_epoch":losses,
       "train_wall_ms":round(wall,3),
       "model_exact_heldout":nn_exact,
       "retrieval_exact_heldout":retrieval_exact,
       "model_avg_character_match":round(nn_char,6),
       "retrieval_avg_character_match":round(retrieval_char,6),
       "model_outputs_sha256":[hashlib.sha256(x.encode()).hexdigest() for x in predictions],
       "source_group_blind_group_split":True,
       "checkpoint_sha256":hashlib.sha256(data).hexdigest(),
       "checkpoint_bytes":len(data),
       "has_original_independent_proof":False,
       "is_q3_full_autonomous_relational_AST":False,
       "is_real_competition_holdout_test":False,
       "trained_before_q3f_escrow_release":True,
       "all_q1_q7":"OPEN"}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--workbook",required=True,type=Path)
    p.add_argument("--dataset",required=True,type=Path)
    p.add_argument("--checkpoint",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    r=train_eval(a.workbook,a.dataset,a.checkpoint)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2)+"\n")
    print("REAL_LEARNED_NEUMANN_PRETRAIN",r["status"])
    print("TRAIN_TEST",r["training_examples"],r["heldout_examples"])
    print("EXACT_MODEL_VS_RETRIEVAL",r["model_exact_heldout"],r["retrieval_exact_heldout"])
    print("CHAR_MODEL_VS_RETRIEVAL",r["model_avg_character_match"],r["retrieval_avg_character_match"])
    print("LOSS",r["loss_per_epoch"])
    print("GLOBAL",r["all_q1_q7"])
