from experiments.inductive_complete_cost import summarize


def configuration():
    return {"experiment_id": "COST_GATE_FIXTURE", "reuse_counts": [1,16], "routes": ["PUBLIC_INTEGER_NATIVE","FREE_COORDINATES"], "repetitions":3, "cases":6,
            "positive":"HEADROOM_ONLY", "negative":"NO_HEADROOM", "incomplete":"INCOMPLETE"}


def observations():
    return [{"case_id":f"fixture{i}", "count":n, "repetition":rep, "route":route,
             "accepted":True, "complete_operational_seconds":1.0, "actual_queries":n}
            for i in range(6) for n in [1,16] for rep in range(3) for route in ["PUBLIC_INTEGER_NATIVE","FREE_COORDINATES"]]


def test_one_case_loss_cannot_be_replaced_by_a_subset_average():
    rows = observations()
    for row in rows:
        if row["case_id"] == "fixture5" and row["route"] == "PUBLIC_INTEGER_NATIVE":
            row["accepted"] = False
    result = summarize(rows, configuration())
    assert result["decision"] == "INCOMPLETE"
    assert result["regimes"]["1"]["geomean_native_over_free"] is None


def test_failed_comparators_are_retained_and_cannot_be_qualified_by_partial_repetitions():
    rows = observations()
    rows[0]["accepted"] = False
    result = summarize(rows, configuration())
    assert result["failed_workers"] == 1 and result["decision"] == "INCOMPLETE"
    complete = summarize(observations(), configuration())
    assert complete["decision"] == "NO_HEADROOM" and complete["regimes"]["16"]["individual_10x_count"] == 0
