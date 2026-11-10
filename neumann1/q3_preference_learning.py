"""Q3 task-agnostic preference learning on real executable SOURCE repairs.

Not an answer-language or domain-specific solver. Given SAME current SOURCE +
falsified previous executable, prefer an independently SOURCE-certified
corrected program to the actual model's refuted program. The frozen base
policy provides the reference distribution; LoRA adjusts one shared model.

All references to original author TEST are prohibited.
"""
from __future__ import annotations


def preference_loss(model,tokenizer,prompt,positive,negative,*,device,
                    beta=1.0,max_length=4096):
    import torch
    import torch.nn.functional as F
    from .q3_prompt_contract import model_training_ids
    if not (0.01<=beta<=5.0 and 128<=max_length<=8192):
        raise ValueError("bounded preference objective required")
    if positive==negative:
        raise ValueError("positive and refuted executable programs identical")
    def logp(program):
        ids,labels=model_training_ids(
            tokenizer,prompt,program+tokenizer.eos_token,
            max_length=max_length)
        x=torch.tensor([ids],dtype=torch.long,device=device)
        y=torch.tensor([labels],dtype=torch.long,device=device)
        logits=model(input_ids=x).logits
        # Causal shift: the final prompt token predicts first code token.
        target=y[:,1:]
        good=(target!=-100).sum()
        if int(good)<2:
            raise ValueError("empty program continuation")
        ce=F.cross_entropy(
            logits[:,:-1,:].transpose(1,2),target,
            ignore_index=-100,reduction="sum")
        return -ce/good
    # Reference uses the SAME original model, not a different model size
    # or a reference loaded with unstated hardware/weights.
    with torch.no_grad(),model.disable_adapter():
        reference_advantage=(logp(positive)-logp(negative)).detach()
    learned_advantage=logp(positive)-logp(negative)
    delta=learned_advantage-reference_advantage
    loss=F.softplus(-beta*delta)
    return loss, {
        "preference_margin":float(learned_advantage.detach().cpu()),
        "reference_margin":float(reference_advantage.detach().cpu()),
        "margin_uplift":float(delta.detach().cpu()),
    }
