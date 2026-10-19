"""Minimal source-pinned PolyRank proof. Classical/posthoc; NOT learned Q3.
Usage: python poly2_two_atom_proof.py /path/to/official/poly2.sl
"""
import hashlib
import json
import sys
from pathlib import Path

BLOB = "17448225fffad0cef48634b9d68f4f9193d616d8"
W = (1, 1, -1, -1, 1)  # c+x-y-x0+y0 <= 0


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def source_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def source_post(state):
    c, x, y, x0, y0 = state
    return (x < y) or (c <= x0 - y0 if x0 >= y0 else c == 0)


def main(path):
    data = Path(path).read_bytes()
    if source_blob(data) != BLOB:
        raise ValueError("FAIL_CLOSED_WRONG_ORIGINAL_GIT_BLOB")

    # The pinned original has Pre (c,x,y,x0,y0)=(0,u,v,u,v).
    assert dot(W, (0,1,0,1,0)) == 0
    assert dot(W, (0,0,1,0,1)) == 0

    # Trans has three cases. For active updates, t>=0 is an integer.
    # dx decrease by >=1: (dc,dx,dy,dx0,dy0)=(1,-1-t,0,0,0).
    # dy increase by >=1: (dc,dx,dy,dx0,dy0)=(1,0,1+t,0,0).
    moves = {
        "idle": ((0,0,0,0,0), (0,0,0,0,0)),
        "decrease_x": ((1,-1,0,0,0), (0,-1,0,0,0)),
        "increase_y": ((1,0,1,0,0), (0,0,1,0,0)),
    }
    for label, (base, t_coefficient) in moves.items():
        assert dot(W,base) == 0, label
        assert dot(W,t_coefficient) <= 0, label
        assert base[0] >= 0 and t_coefficient[0] == 0

    # Thus c>=0 and W*state<=0 are both inductive.
    # If x>=y: c <= x0-y0-(x-y) <= x0-y0.
    # If x0<y0, c>=0 contradicts that strict negative upper bound.
    # The two negative models below prove each chosen atom is required
    # when retaining the other one. They do NOT prove global minimality.
    without_phi = (1,0,0,0,0)
    without_c = (-1,0,0,0,1)
    assert without_phi[0]>=0 and not source_post(without_phi)
    assert dot(W,without_c)<=0 and not source_post(without_c)

    # Post alone is not inductive, even though this predecessor is unreachable.
    before = (0,2,0,0,0)
    after = (1,1,0,0,0)
    assert source_post(before) and not source_post(after)
    assert after[0]==before[0]+1 and after[1]<=before[1]-1
    assert after[2]==before[2] and after[3:]==before[3:]

    result = {
        "status":"PASS_EXACT_BRANCH_ALGEBRA_2_ATOM_PROOF",
        "source_git_blob_sha1":BLOB,
        "source_sha256":hashlib.sha256(data).hexdigest(),
        "I":"c>=0 AND c+x-y-x0+y0<=0",
        "branch_potential_deltas":{
            "idle":"0","decrease_x":"-t","increase_y":"-t"
        },
        "potential_coefficients":list(W),
        "negative_controls":{
            "without_first_atom":True,
            "without_second_atom":True,
            "Post_alone_not_inductive":True,
        },
        "previously_opened_posthoc":True,
        "neural_unique_structure_discovery":False,
        "new_unseen_original_transfer":False,
        "independent_smt_checker_rerun":False,
        "global_Q1_Q7":"OPEN",
    }
    print(json.dumps(result,sort_keys=True,indent=2))
    return result


if __name__ == "__main__":
    main(sys.argv[1])
