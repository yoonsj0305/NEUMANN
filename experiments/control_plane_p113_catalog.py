"""New opened-development roles, authored before either arm is scored.

References are mechanically compiled from the independently declared role label;
no reference is input to the learned judge. These are controlled diagnostic CSP
tasks, not independent external validation or unseen computational families.
"""
from itertools import combinations

SPECS = [
    (["gate valve", "pressure relief valve"], 1,
     "device venting a pressurized vessel when the internal load exceeds a safe limit"),
    (["differential gear", "flywheel", "clutch"], 0,
     "mechanism allowing driven wheels to rotate at unequal speeds while turning"),
    (["branch predictor", "arithmetic logic unit", "cache controller", "memory management unit"], 3,
     "processor component translating virtual addresses into physical locations"),
    (["lipase", "catalase"], 1,
     "enzyme decomposing hydrogen peroxide into water and oxygen"),
    (["sediment filter", "reverse osmosis membrane", "activated carbon bed"], 1,
     "barrier removing dissolved salts from liquid under applied hydraulic force"),
    (["clearinghouse", "currency exchange", "escrow agent", "credit bureau"], 2,
     "intermediary holding funds until both sides meet agreed conditions"),
    (["electrocardiograph", "pulse oximeter"], 0,
     "instrument recording electrical activity of the heart over time"),
    (["domain name server", "DHCP server", "router"], 1,
     "service leasing numerical network addresses to newly connected machines"),
    (["accelerometer", "magnetometer", "barometer", "gyroscope"], 3,
     "sensor maintaining an angular reference to detect changes in orientation"),
    (["rivet", "screw"], 0,
     "fastener permanently joining sheets by deforming its tail"),
    (["spleen", "thymus", "lymph node"], 2,
     "organ filtering tissue fluid and hosting immune cell activation"),
    (["rectifier", "inverter", "surge suppressor", "voltage regulator"], 1,
     "device converting direct electric supply into alternating output"),
]


def catalog():
    rows, refs = [], []
    for index, (roles, expected, target) in enumerate(SPECS, 1):
        names = list("ABCD"[:len(roles)])
        values = [1000 + index*31 + j*7 for j in range(len(roles))]
        special = values[-1]
        declarations = ", ".join(f"{e} is the {r}" for e,r in zip(names,roles))
        instruction = f"{declarations}. Resolve 'It' to the {target}, then return a complete assignment."
        constraints = [["ne",a,b] for a,b in combinations(names,2)]
        rules = [f"{a} differs from {b}" for a,b in combinations(names,2)]
        query = (f"Choose {', '.join(names)} from {{{','.join(map(str,values))}}}. "
                 + ", ".join(rules + [f"It equals {special}"]) + ". Return a complete assignment.")
        task_id = f"p113d_b{index:02d}"
        rows.append({"task_id":task_id, "view":{"instruction":instruction,"public":{"query":query}}})
        witness = {names[expected]:special}
        witness.update(zip((e for i,e in enumerate(names) if i != expected),values[:-1]))
        refs.append({"task_id":task_id,"family":"constraint_planning",
            "expected_candidate":expected,"semantic_grounding":f"{roles[expected]}: {target}",
            "private":{"domains":{e:list(values) for e in names},
                       "constraints":constraints + [["eq",names[expected],special]]},
            "witness":witness})
    return rows, refs
