"""AM2 identical-hypothesis kill gate on already OPENED 12 tasks.

The fixture provides a common fixed code response for both arms; it is NOT a
learned model and its 12/12 successes are not capability evidence. This proves
that AM2's current TOOL and NEUMANN routes have no distinct problem-solving
semantics on these tasks, under the deterministic same-model-response contract.

Do not spend GPU time comparing algorithmically identical hypotheses.
"""
from __future__ import annotations
import json
from experiments.am2_dual_plane_runtime import run_observation,coding_prompt
from experiments.general_multiplier_tasks import multiplier_tasks,model_view
from neumann1.general_runtime_v106 import canonical,sha

SOURCE_FIXTURES=(
    "def solve(items):\n    return len(set(x for x in items if x < 0))",
    "def solve(items):\n    return sum(set(x for x in items if x % 2 == 0))",
    "def solve(items):\n    return len(set(x for x in items if x > 0 and x % 2 == 1))",
    "def solve(items):\n    return sum(abs(x) for x in set(items) if x != 0)",
)
SCHEMA="neumann.am2.same-hypothesis-no-headroom.v1"

class FixedFixtureCore:
    def __init__(self,source):
        self.source=source
        self.identity={"weights_frozen":True,"accelerator_class":True,
                       "evidence_kind":"NON_MODEL_FIXTURE_NEVER_USE_FOR_CAPABILITY",
                       "revision":"simulation-only"}
        self.prompts=[]
    def count_tokens(self,messages,thinking):
        assert thinking is False
        self.prompts.append(canonical(messages))
        return 100
    def generate(self,messages,max_tokens,thinking,deadline_ms):
        assert thinking is False
        self.prompts.append(canonical(messages))
        return {"raw":self.source,"input_tokens":100,
                "output_tokens":min(30,max_tokens),"thinking_enabled":False,
                "deadline_reached":False,"peak_accelerator_memory_bytes":1}

def assay():
    rows=[]
    coding=0
    for task,private in multiplier_tasks():
        view=model_view(task)
        is_code=task["family"]=="coding"
        if is_code:
            source=SOURCE_FIXTURES[coding]
            coding+=1
            a,b=FixedFixtureCore(source),FixedFixtureCore(source)
        else:
            a=b=None
        tool=run_observation(task,private,view,"TOOL",a)
        neumann=run_observation(task,private,view,"NEUMANN",b)
        if tool["accepted"]!=neumann["accepted"] or canonical(tool["answer"])!=canonical(neumann["answer"]):
            raise AssertionError("TOOL_NEUMANN_SEMANTIC_MISMATCH")
        if tool["model_calls"]!=neumann["model_calls"]:
            raise AssertionError("MODEL_CALLS_DIFFER")
        if tool["tool_calls"]!=neumann["tool_calls"]:
            raise AssertionError("EQUAL_TOOL_RIGHTS_BROKEN")
        if neumann["representation_certified"] is not True or tool["representation_certified"] is True:
            raise AssertionError("NOT_DISTINCT_CERTIFICATION_PATHS")
        if is_code:
            expected=canonical(coding_prompt(view))
            if a.prompts!=[expected,expected] or b.prompts!=[expected,expected]:
                raise AssertionError("DIFFERENT_MODEL_PROMPT_OR_THINKING")
            if tool["model_calls"]!=1 or neumann["model_calls"]!=1:
                raise AssertionError("EXPECTED_ONE_CODING_CALL_EACH")
        elif tool["model_calls"]!=0:
            raise AssertionError("NEURAL_FOR_DETERMINISTIC_TASK")
        rows.append({
            "kind":task["family"],"same_candidate":True,
            "tool_model_calls":tool["model_calls"],
            "neumann_model_calls":neumann["model_calls"],
            "same_checker_result":True,
            "tool_actual_checker":tool["checker_calls"],
            "neumann_actual_checker":neumann["checker_calls"],
            "extra_neumann_certificate":neumann["representation_certified"],
            "fixture_only":is_code
        })
    assert len(rows)==12 and coding==4
    assert sum(r["tool_model_calls"] for r in rows)==4
    assert sum(r["neumann_model_calls"] for r in rows)==4
    return {
        "schema":SCHEMA,"status":"STOP_CURRENT_AM2_BEFORE_EXPENSIVE_MODEL_RUN",
        "scope":"opened author-constructed 12 only, conditional deterministic-model equivalence",
        "proof_kind":"Common inputs, identical model prompts on coding, same deterministic exact tools/checker, original-field certified reduction",
        "fixtures_not_real_model":True,
        "actual_model_calls":0,
        "independent_real_model_capability":"NOT_EVALUATED",
        "frontier_capability":"NOT_EVALUATED",
        "sealed_unseen_transfer":"NOT_EVALUATED",
        "architecture_multiplier":"NOT_EVALUATED",
        "same_semantic_result_under_matched_responses":12,
        "equal_model_call_count":12,
        "identical_coding_prompts":4,
        "need_for_meaningfully_different_architecture":True,
        "conclusion":"This AM2 prototype does not propose a different learning hypothesis than TOOL. No capability multiplier can be causally attributed to its extra certificate on the existing opened 12 tasks.",
        "rows":rows
    }

if __name__=="__main__":
    print(json.dumps(assay(),sort_keys=True,indent=2))
