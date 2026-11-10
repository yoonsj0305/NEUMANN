"""Mathematical gradient check for one shared Q3 source-repair preference policy.

A toy character model tests derivative signs only; it is NOT a Q3 original
benchmark or an independently invented new operator.
"""
import pytest


def test_frozen_reference_preference_gradient_favors_verified_over_refuted():
    torch=pytest.importorskip("torch")
    from contextlib import contextmanager
    from types import SimpleNamespace
    from neumann1.q3_preference_learning import preference_loss

    class Tokenizer:
        eos_token="!"
        chat_template=None
        def __call__(self,s,add_special_tokens=False):
            return {"input_ids":[ord(c)%128 for c in s]}

    class TinyModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.delta=torch.nn.Parameter(torch.zeros(128))
            self.off=False
        @contextmanager
        def disable_adapter(self):
            old=self.off
            self.off=True
            try:yield
            finally:self.off=old
        def forward(self,input_ids):
            n,m=input_ids.shape
            logits=torch.zeros(
                n,m,128,dtype=self.delta.dtype,device=input_ids.device)
            if not self.off:
                logits=logits+self.delta.view(1,1,128)
            return SimpleNamespace(logits=logits)

    model=TinyModel()
    tokenizer=Tokenizer()
    positive="def transform(x):\n    return x+1"
    refuted="def transform(x):\n    return x*1"
    prompt="Source input: 2\nExpected source output: 3\n"
    optimizer=torch.optim.SGD(model.parameters(),lr=2.0)
    first=None
    for _ in range(4):
        optimizer.zero_grad(set_to_none=True)
        loss,diag=preference_loss(
            model,tokenizer,prompt,positive,refuted,device="cpu",
            beta=1.0,max_length=4096)
        assert torch.isfinite(loss)
        if first is None:first=float(loss.detach())
        loss.backward()
        assert model.delta.grad is not None
        optimizer.step()
    last,_=preference_loss(
        model,tokenizer,prompt,positive,refuted,device="cpu",
        beta=1.0,max_length=4096)
    assert float(last.detach())<first
    assert diag["margin_uplift"]>0


def test_preference_requires_distinct_positive_and_negative_programs():
    torch=pytest.importorskip("torch")
    from neumann1.q3_preference_learning import preference_loss
    class Empty:
        pass
    with pytest.raises(ValueError,match="identical"):
        preference_loss(Empty(),Empty(),"prompt","def transform(x):return x",
                        "def transform(x):return x",device="cpu")
