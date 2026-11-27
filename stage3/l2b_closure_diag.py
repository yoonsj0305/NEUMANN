# diagnostic of the 11.7-2 closure failure (hand table = table 0; recorded only): for the long sequences' steps whose
# key is not in K(L): share with a bit-0 read at t or t-1; closure if the token of every bit-0 read is masked
import sys, json, torch
sys.path.insert(0, "stage3"); import l2b_h as H
out = {}
for mod in ("add", "mul1"):
    H._setup(mod)
    import c1a
    tab = H.table_of(mod, 0); nh = len(c1a.moving(tab))
    def masked_and_flag(K):
        k = K.clone(); flag = torch.zeros_like(K, dtype=torch.bool); res = torch.zeros_like(K); shift = 0
        # layout from the low bits: [t-1 block: nh x (bit, tok)] x_{t-1} [t block] x_t -- see l2b_h.batch_keys
        for blk in range(2):
            for h in range(nh):
                b = k & 1; k = k >> 1; tok = k & 127; k = k >> 7
                flag |= b == 0
                tok = torch.where(b == 0, torch.zeros_like(tok), tok)
                res |= (b | (tok << 1)) << shift; shift += 8
            res |= (k & 127) << shift; k = k >> 7; shift += 7
        return res, flag
    exK = H.exhaustive(mod, True)
    KK, _, _ = H.keys_of(exK, tab)
    exL = H.long_random(mod, 100000, "L2b-0:closure:%s" % mod)
    KL_, _, SL = H.keys_of(exL, tab, bs=256)
    miss = ~torch.isin(KL_, KK.unique())
    mK, _ = masked_and_flag(KK); mL, fL = masked_and_flag(KL_)
    miss_m = ~torch.isin(mL, mK.unique())
    out[mod] = {"long_steps": len(KL_), "missing_steps": int(miss.sum()),
                "missing_steps_with_a_bit0_read": int((miss & fL).sum()),
                "missing_steps_without_bit0_read": int((miss & ~fL).sum()),
                "masked_bit0_tokens": {"missing_steps": int(miss_m.sum()), "distinct": len(mL[miss_m].unique()),
                                       "sequences": len(SL[miss_m].unique()),
                                       "examples": [H.decode_key(int(k), nh) for k in mL[miss_m].unique()[:10]]}}
    print(mod, json.dumps(out[mod]), flush=True)
json.dump(out, open("stage3/results/L2b-0/H/closure_diag_hand.json", "w"), indent=1)
