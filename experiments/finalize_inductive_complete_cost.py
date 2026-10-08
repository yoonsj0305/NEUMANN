"""Preserve a negative first cost result and register opened data, not training."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.representation_headroom import digest, save
from neumann1.recurrence_data import problem_view
from neumann1.structural_data_rights import DataUseError, authorize
from neumann1.structural_experience import offline_experience


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main(workspace):
    continuation = workspace/"Continuation"
    prep = continuation/"INDUCTIVE_COMPLETE_COST_PREPARATION"
    first = continuation/"INDUCTIVE_COMPLETE_COST_FIRST"
    audit = continuation/"INDUCTIVE_COMPLETE_COST_AUDIT/replay.json"
    final = continuation/"INDUCTIVE_COMPLETE_COST_FINALIZATION"
    reg, report, replay = read(prep/"preregister.json"), read(first/"report.json"), read(audit)
    receipt = read(prep/"first-result-receipt.json")
    assert replay["status"] == "PASS_ORIGINAL_OPERATIONAL_COST_AND_CORRECTNESS"
    assert report["decision"] == reg["negative"] and all(r["all_evaluable"] for r in report["regimes"].values())
    assert digest(prep/"preregister.json") == report["contract_sha256"] == read(prep/"freeze-receipt.json")["contract_sha256"]
    assert digest(first/"report.json") == receipt["report_sha256"] == replay["original_report_sha256"]
    assert digest(first/"manifest.json") == receipt["manifest_sha256"] == replay["original_manifest_sha256"]
    assert all(digest(first/path) == pin for path, pin in read(first/"manifest.json").items())
    assert all(digest(ROOT/path) == pin for path, pin in reg["sources"].items())
    old = read(ROOT/"docs/experiments/inductive_perspective.pins.json")
    prior = {**old["old_first_report_pins_unchanged"], "INDUCTIVE_PERSPECTIVE_FIRST": old["first_report_sha256"]}
    assert all(digest(continuation/folder/"report.json") == pin for folder, pin in prior.items())
    assert all(digest(ROOT/path) == pin for path, pin in old["sources"].items())

    registry = {"schema": "neumann.inductive-operational-opened-assets.v1", "public": {}, "offline": {},
                "fresh_eligible": 0, "training_activated": False, "OS_security_boundary": False}
    denied = 0
    for row in report["regimes"]["1"]["cases"]:
        identifier = row["case_id"]
        common = {"problem_kind": "exact_integer_recurrence", "allowed_use": "opened_development_only",
                  "source_study": reg["experiment_id"], "source_report_sha256": digest(first/"report.json"),
                  "equivalence_group": "opened-coupled-translation/"+identifier,
                  "structural_family": "polynomial_translation_cancellation_antidifference",
                  "historically_opened": True, "fresh_eligible": False, "training_activated": False}
        for role, folder, key in [("D", "public", "public"), ("O", "oracle", "offline")]:
            path = first/folder/(identifier+".json")
            asset = {**common, "role": role, "runtime": role == "D", "path": str(path.relative_to(workspace)), "sha256": digest(path)}
            registry[key][identifier] = asset
            if role == "D":
                assert problem_view(workspace, asset) == read(path)
                prohibited = ["train", "fresh_evaluation"]
            else:
                assert set(offline_experience(workspace, asset)) == {"proposal", "expected", "lineage"}
                prohibited = ["train", "fresh_evaluation", "development_problem"]
            for purpose in prohibited:
                try:
                    authorize(asset, purpose)
                except DataUseError:
                    denied += 1
                else:
                    raise AssertionError("Development evidence unexpectedly promoted")
        requests = read(first/"requests"/(identifier+".json"))
        assert len({(tuple(q["parameters"]), q["steps"]) for q in requests}) == 16

    entry = {"contract": "docs/experiments/inductive_complete_cost.preregister.json", "decision": report["decision"],
             "scope": report["scope"], "cases": 6, "independent_domains": 1, "worker_observations": 144,
             "accepted_workers": 132, "actual_query_outputs": 1122, "distinct_development_requests": 96,
             "failed_workers": 12, "failure_kind": "CAS verification budget UNKNOWN,not proven mathematically false",
             "regimes": {key: {k: value[k] for k in ["all_evaluable", "geomean_native_over_free", "individual_10x_count", "passed"]}
                         for key, value in report["regimes"].items()},
             "result": "../../Continuation/INDUCTIVE_COMPLETE_COST_FIRST/report.json",
             "audit": "../../Continuation/INDUCTIVE_COMPLETE_COST_AUDIT/replay.json",
             "first_evidence_no_replacement": True, "learning_performed": False, "G1_admitted": False,
             "fresh_eligible": 0, "research_investment": "UNKNOWN", "resource_axis": reg["resource_axis"]}
    ledger_path = ROOT/"docs/experiments/experiment_decision_ledger.json"
    plan_path = ROOT/"docs/experiments/minimum_decisive_plan.v1.json"
    portfolio_path = ROOT/"docs/experiments/representation_generation_portfolio.json"
    ledger, plan, portfolio = [read(p) for p in [ledger_path, plan_path, portfolio_path]]
    assert "inductive_complete_cost" not in ledger and not final.exists()
    assert digest(portfolio_path) == old["portfolio_sha256"]
    final.mkdir()
    for path in [ledger_path, plan_path, portfolio_path, workspace/"AGENTS.md", workspace/"CONTINUE_HERE.md"]:
        (final/(path.name+".before")).write_bytes(path.read_bytes())
    registry_path = ROOT/"experiments/inductive_complete_cost_asset_registry.json"
    save(registry_path, registry)
    registration = ROOT/"docs/experiments/inductive_complete_cost.preregister.json"
    registration.write_bytes((prep/"preregister.json").read_bytes())
    ledger["inductive_complete_cost"] = entry
    plan["stages"]["G0"]["inductive_complete_cost"] = entry
    portfolio["evidence_report_pins"]["INDUCTIVE_COMPLETE_COST_FIRST"] = digest(first/"report.json")
    portfolio["deprioritized_in_registered_scope"].append({
        "candidate": "neural addition to registered coupled polynomial cancellation/antidifference family",
        "evidence": "INDUCTIVE_COMPLETE_COST_FIRST", "reason": "capable public native also generates coordinates; supplied valid coordinates have about1x complete operational cost,no10x gate"})
    portfolio["latest_complete_cost_screen"] = entry
    for candidate in portfolio["retained_for_headroom_design"]:
        if candidate["kernel_implemented"]:
            candidate["registered_translation_family_headroom"] = False
            candidate["other_generated_representations_unresolved"] = True
    for path, value in [(ledger_path, ledger), (plan_path, plan), (portfolio_path, portfolio)]:
        save(path, value)

    save(final/"postrun_engineering_failures.json", {
        "first_audit": {"error": "AssertionError at regenerated Oracle JSON comparison", "cause": "lineage.coefficients integer keys become string keys in JSON", "repair": "JSON-normalize regenerated audit object only"},
        "first_added_gate_tests": {"passed": 123, "failed": 2, "error": "KeyError: experiment_id", "cause": "test-only configuration omitted required experiment_id", "repair": "add experiment_id to fixture only"},
        "timed_first_execution_sources_or_results_changed": False,
        "corrected_related_pytest": {"passed": 128, "failed": 0, "seconds": 3.90, "tests_are_capability_gate": False}})
    save(final/"environment_description.json", {"hardware_recorded_after_execution": True,
        "CPU": "Intel(R) Core(TM) i5-10400F CPU @ 2.90GHz", "physical_cores": 6, "logical_processors": 12,
        "platform": sys.platform, "python": sys.version, "environment_image_fully_pinned": False})

    agents = workspace/"AGENTS.md"
    current = """Latest 2026-10-07 result: INDUCTIVE_COMPLETE_COST_V1.
Read `GitHub/NEUMANN/docs/research/inductive_complete_cost_2026-10-07.md`.
Frozen6 constructed coupled integer-recurrence development cases,4 routes,3 repeats,
cold1 and cold16 actual distinct inputs.144 workers,132 accepted,1122 correct query
outputs (96 distinct requests,NOT1122 independent tasks).12 degree6 CAS workers
NOT_VERIFIED on polynomial-work budget UNKNOWN,not mathematically false; retain
48.9635s failure costs and proposals/checks/stderr,do not tune or replace first.
All6 evaluable under registered rule: public integer native and supplied coordinates
fully qualify. Best native is PUBLIC_INTEGER_NATIVE in every case. Native/free
geomean cold1=0.9961369279,cold16=0.9973958195;10x wins0/6 both. First decision
NO_10X_OPERATIONAL_HEADROOM_IN_REGISTERED_SCOPE. Whole study310.3506s.
Public native uses only input coefficients to generate cancellation/antidifference
coordinates and closed form,NOT learned NEUMANN or a novel principle. Do not train
this known-family selector/generator as breakthrough. General generated sufficient
representations and prospective recursive summaries remain unresolved,NOT globally
refuted. New investment requires meaningful independent structure and capable equally
reusable native/composed generation at registered complete cost,not bigger horizons
or removing baseline reuse. Supplied representation is valid,NOT globally optimal.
Primary cost includes Python process/import,reads,discovery/check/compile,actual
queries,writes/exit,parent full answer checks. Current common startup dominates;
NOT intrinsic intelligence lower bound or a warm-service performance claim.
Offline construction0.0287s separate,research investmentUNKNOWN,learningNOT_PERFORMED;
no total R&D/FLOP/energy/money/actual memory claim.7 core sources+2 package identities
pinned,NOT whole environment closure. Keep original source/report/manifest receipts.
Independent audit645 files,6 reconstructed cases,16 distinct verified proposals,
96 certified workers,1122 interpreted outputs,54 short original-spec replays PASS;
large queries rely on independent universal identities/closed DAGs,not full loops.
128 related pytest checks PASS. Postrun audit JSON key/test fixture errors retained,
repair limited to audit/tests. Registry6 D public/6 O offline,30 rights denials,
strict recurrence_data API rejects train/fresh/O before payload I/O (not OS boundary).
PREPARATION/FIRST/AUDIT/FINALIZATION folders in Continuation. Prior5 first reports
and frozen earlier sources unchanged. Fresh0,Q1-Q7 OPEN,G1 not admitted,G2/Decision3
unchanged,noGPU,GitHub push or Notion write. This is evidence of absent10x margin
for the registered candidate,NOT a claim the requested overwhelming goal is achieved.

"""
    agents.write_text(agents.read_text(encoding="utf-8").replace("# Local workspace context\n\n", "# Local workspace context\n\n"+current, 1), encoding="utf-8")
    continue_file = workspace/"CONTINUE_HERE.md"
    text = continue_file.read_text(encoding="utf-8")
    text = text.replace("2026-10-07, 후보 통합 판단과 생성된 좌표·반복 요약의 인증/실행 핵심 구현 완료. 학습 미진입.",
                        "2026-10-07, 전체 운영 비용 검사 완료. 등록 범위의 10배 우위 미입증, 학습 미진입.", 1)
    text = text.replace("## 현재 작업 위치", "## 이전 구현 요약", 1).replace("**최신 작업:**", "**이전 작업:**", 1)
    block = """## 최신 비용 실측

[전체 비용 결과와 한계](GitHub/NEUMANN/docs/research/inductive_complete_cost_2026-10-07.md).
INDUCTIVE_COMPLETE_COST_V1: 공개 계수에서 생성하는 강한 기존 기호 방법과 무료
제공 좌표를 6개 개발 문제에서 비교했다. 144 worker 중 132개가 완료했고 실제
출력 1,122개를 재검증했다(서로 다른 요청96개, 독립 문제1,122개가 아님).
처음/16입력 재사용의 기존 대비 제공 좌표 이득은 기하평균0.9961/0.9974배,
10배 사례는 양쪽0/6. 등록 판정은 NO_10X_OPERATIONAL_HEADROOM_IN_REGISTERED_SCOPE.
차수6 CAS12회는 증명 예산 초과 UNKNOWN으로 비용/제안/검사를 보존했다. 적격
public native와 제공 좌표가 모든 문제에서 완료해 등록 규칙상6개 전부 평가 가능.

독립 검사645파일·16종 제안·1,122출력·54짧은 원래 전이 PASS, 관련pytest128개 PASS.
6 D 공개/6 O offline 자료와 접근 제한을 등록했다. 실행 비용은 시작/import부터
검증/계산/저장/종료/부모의 정답 대조까지 포함한다. 현재 공통 초기화가 크지만
이를 빼서 재판정하지 않는다. 학습/연구 투자까지 포함한 완성 모델 비용이나
지속 서비스/에너지/메모리/프런티어 비교의 결과가 아니다. 제공 좌표 전역 최적성도 미증명.

이 상쇄·다항식 차분 문제군은 GPU 학습 대상으로 삼지 않는다. 기존 알고리즘도
같은 유리한 표현을 생성한다. 일반 표현 생성 가설의 폐기는 아니며, 다음 투자는
독립적이고 의미 있는 구조에서 강한 생성 비교군 대비 전체 비용 여유가 먼저 필요하다.
큰 반복 수·약한 기준선으로 성공을 만들지 않는다. 학습된 관점 정책 없음,
fresh0, Q1~Q7 OPEN, G1 미진입, G2/기존Decision3 봉인 유지.
Continuation의 INDUCTIVE_COMPLETE_COST_PREPARATION/FIRST/AUDIT/FINALIZATION에
동결 소스·계약·원본 관측·독립 검사·권한/판정 receipt가 있다.

"""
    text = text.replace("## 이전 구현 요약", block+"## 이전 구현 요약", 1)
    continue_file.write_text(text, encoding="utf-8")

    report_path = ROOT/"docs/research/inductive_complete_cost_2026-10-07.md"
    pins = {"schema": "neumann.inductive-operational-cost-pins.v1", "contract_sha256": digest(registration),
            "sources": reg["sources"], "first_report_sha256": digest(first/"report.json"),
            "first_manifest_sha256": digest(first/"manifest.json"), "audit_sha256": digest(audit),
            "audit_source_sha256": digest(ROOT/"experiments/inductive_complete_cost_replay.py"),
            "registry_sha256": digest(registry_path), "public_loader_sha256": digest(ROOT/"neumann1/recurrence_data.py"),
            "research_report_sha256": digest(report_path), "decision_ledger_sha256": digest(ledger_path),
            "operating_plan_sha256": digest(plan_path), "portfolio_sha256": digest(portfolio_path),
            "finalization_source_sha256": digest(Path(__file__)), "old_first_report_pins_unchanged": prior,
            "old_frozen_sources_unchanged": old["sources"], "G1_admitted": False, "fresh_eligible": 0}
    pins_path = ROOT/"docs/experiments/inductive_complete_cost.pins.json"
    save(pins_path, pins)
    save(final/"receipt.json", {"status": "PASS_FIRST_NEGATIVE_COST_RESULT_PRESERVED", "decision": report["decision"],
         "first_evidence_unchanged": True, "D_public_registered": 6, "O_offline_registered": 6, "rights_denials": denied,
         "old_first_reports_unchanged": list(prior), "pins_sha256": digest(pins_path), "related_pytest_passed": 128,
         "tests_are_capability_gate": False, "learned_policy_implemented": False, "training_activated": False,
         "G1_admitted": False, "fresh_eligible": 0, "GPU_started": False, "requested_overwhelming_goal_proved": False})
    assert all(digest(first/path) == pin for path, pin in read(first/"manifest.json").items())
    assert all(digest(ROOT/path) == pin for path, pin in reg["sources"].items())
    print((final/"receipt.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
