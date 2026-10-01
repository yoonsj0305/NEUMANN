"""Same parameterization, but shortlist after two full graph updates."""
import base64
import numpy as np
import torch
from experiments.lp_state_models_v087 import GraphStateModel, PointwiseModel
from experiments.lp_model_study_v088 import pack_weights


class LateGraphStateModel(GraphStateModel):
    def forward(self, matrix, row_features, col_features):
        m,n=matrix.shape
        rows,cols=self.rows(row_features),self.cols(col_features)
        rd=matrix.abs().sum(1).clamp_min(1e-6).unsqueeze(1)
        cd=matrix.abs().sum(0).clamp_min(1e-6).unsqueeze(1)
        for layer in (0,1):
            rows=self.to_row[layer](torch.cat((rows,matrix@cols/rd),1))
            cols=self.to_col[layer](torch.cat((cols,matrix.T@rows/cd),1))
        coarse=self.coarse(cols).squeeze(1)
        selected=(torch.argsort(coarse,descending=True,stable=True)[:min(n,2*m)]
                  if self.compact else torch.arange(n,device=matrix.device))
        edges,states=matrix[:,selected],cols[selected]
        rd=edges.abs().sum(1).clamp_min(1e-6).unsqueeze(1)
        cd=edges.abs().sum(0).clamp_min(1e-6).unsqueeze(1)
        rows=self.to_row[2](torch.cat((rows,edges@states/rd),1))
        states=self.to_col[2](torch.cat((states,edges.T@rows/cd),1))
        scores=torch.full_like(coarse,-1e6).scatter(0,selected,self.refine(states).squeeze(1))
        x=torch.zeros_like(coarse).scatter(0,selected,self.primal(states).squeeze(1))
        return {'scores':scores,'coarse':coarse,'x':x,'y':self.dual(rows).squeeze(1),
            'selected':selected,'state_columns':int(selected.numel()),
            'edge_multiply_terms':int(m*n*self.width*4+m*selected.numel()*self.width*2)}


def roster(seed):
    models={}
    for name,make in (('compact16',lambda:LateGraphStateModel(16,True)),
        ('full16',lambda:LateGraphStateModel(16,False)),
        ('point16',lambda:PointwiseModel(16)),
        ('full128',lambda:LateGraphStateModel(128,False))):
        torch.manual_seed(seed);models[name]=make().eval()
    return models


def restore_models(training):
    result={}
    for seed in (87001,87002):
        for name,model in roster(seed).items():
            key=f'{name}_s{seed}';t=training[key]
            state={k:torch.tensor(np.frombuffer(base64.b64decode(v['base64'],validate=True),
                dtype='<f4').reshape(v['shape']).copy()) for k,v in t['weights'].items()}
            model.load_state_dict(state,strict=True)
            if pack_weights(model)[1]!=t['weights_sha256']:raise ValueError('late checkpoint drift')
            result[key]=model.eval()
    return result
