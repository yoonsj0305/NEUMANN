"""P1.8: exact task-sufficiency counterexample, pre-registered synthetic audit.

Not a JEPA implementation, not a statement about all possible decoders. A scene-
only decision interface cannot choose a goal-dependent action when the goal is
independent of every available scene view. The task goal may be supplied to a
joint downstream interface to restore sufficiency.
"""
from __future__ import annotations
import json
import hashlib
import math
import platform
import resource
import time
from pathlib import Path
import numpy as np

CONTRACT = {
    "schema": "neumann.q3.task-sufficiency.p18.v1",
    "data_seed": 20261105,
    "scenes": 2048,
    "shape": [6, 6],
    "foreground_p": 0.30,
    "goals": ["identity", "flip_horizontal"],
    "scenes_must_be_distinct": True,
    "scenes_must_not_be_horizontal_symmetric": True,
    "original_task_records": 4096,
    "global_q1_to_q7": "OPEN",
    "neural_trained": False,
    "JEPA_trained": False,
    "original_arc_task_score": "NOT_RUN",
}


def build_scenes():
    rng = np.random.default_rng(CONTRACT["data_seed"])
    scenes = []
    seen = set()
    rejected_symmetry = 0
    rejected_duplicate = 0
    draws = 0
    while len(scenes) < CONTRACT["scenes"]:
        scene = (rng.random(CONTRACT["shape"]) < CONTRACT["foreground_p"]).astype(np.uint8)
        draws += 1
        if np.array_equal(scene, np.fliplr(scene)):
            rejected_symmetry += 1
            continue
        key = scene.tobytes()
        if key in seen:
            rejected_duplicate += 1
            continue
        scenes.append(scene)
        seen.add(key)
    return scenes, {"draws":draws,"rejected_symmetry":rejected_symmetry,"rejected_duplicate":rejected_duplicate}


def run():
    start = time.perf_counter_ns()
    scenes, generation = build_scenes()
    digest = hashlib.sha256(b"".join(s.tobytes() for s in scenes)).hexdigest()
    output_pairs_different = 0
    scene_only_bayes_correct = 0
    goal_conditioned_correct = 0
    same_world_view_recovery = 0
    conditional_entropy_bits = 0.0
    for s in scenes:
        v1 = s.copy()
        v2 = np.flipud(s).copy()
        if np.array_equal(v1, np.flipud(v2)):
            same_world_view_recovery += 1
        y0, y1 = s, np.fliplr(s)
        if not np.array_equal(y0, y1):
            output_pairs_different += 1
        # For a scene-identical pair and a uniform independent goal, the best
        # scene-only deterministic prediction chooses one of two equally likely
        # mutually exclusive full-grid outputs.
        candidates = (y0, y1)
        best = max(sum(np.array_equal(guess, target) for target in candidates) for guess in candidates)
        scene_only_bayes_correct += best
        # With goal T explicitly in the decision interface, both are exact.
        goal_conditioned_correct += int(np.array_equal(s, y0))
        goal_conditioned_correct += int(np.array_equal(np.fliplr(s), y1))
        # Empirical Y conditional on this unique scene: two equiprobable
        # distinct outputs, yielding H(Y|S)=1 bit.
        conditional_entropy_bits += -2 * 0.5 * math.log2(0.5)
    total = 2 * len(scenes)
    out = {
        "contract": CONTRACT,
        "generation": generation,
        "source_scene_sha256": digest,
        "distinct_scene_count": len(scenes),
        "original_task_record_count": total,
        "different_goal_outputs": output_pairs_different,
        "perfect_scene_view_recovery": same_world_view_recovery,
        "scene_only_bayes_correct": scene_only_bayes_correct,
        "scene_only_accuracy_upper_bound": scene_only_bayes_correct/total,
        "goal_conditioned_correct": goal_conditioned_correct,
        "goal_conditioned_accuracy": goal_conditioned_correct/total,
        "conditional_output_entropy_bits_given_scene": conditional_entropy_bits/len(scenes),
        "global_q1_to_q7": "OPEN",
        "first_gate": "UNDECIDED",
        "environment": {"python": platform.python_version(), "numpy":np.__version__,
                        "process_peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
        "measured_region_ns": time.perf_counter_ns() - start,
        "energy_joule": None,
        "flops": None,
        "dollars": None,
    }
    if (out["distinct_scene_count"] == 2048 and out["different_goal_outputs"] == 2048
        and out["perfect_scene_view_recovery"] == 2048 and out["original_task_record_count"] == 4096
        and out["scene_only_accuracy_upper_bound"] == 0.5
        and out["goal_conditioned_accuracy"] == 1.0
        and out["conditional_output_entropy_bits_given_scene"] == 1.0):
        out["first_gate"] = "PASS_CONSTRUCTED_TASK_SUFFICIENCY_BOUND"
    else:
        out["first_gate"] = "FAIL_CONSTRUCTED_TASK_SUFFICIENCY_BOUND"
    return out


def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    result=run()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("x",encoding="utf-8") as fh:
        json.dump(result,fh,sort_keys=True,indent=2)
        fh.write("\n")
    print(json.dumps({key:result[key] for key in ("first_gate","scene_only_accuracy_upper_bound",
       "goal_conditioned_accuracy","conditional_output_entropy_bits_given_scene","measured_region_ns")},indent=2))

if __name__=="__main__":
    main()
