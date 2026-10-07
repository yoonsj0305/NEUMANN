"""Register engineered proof access without promoting opened references to G1."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.representation_headroom import digest,save
from neumann1.recursive_summary_data import problem_view
from neumann1.recursive_summary import validate_problem
from neumann1.structural_data_rights import authorize,DataUseError,load_json_view
from neumann1.structural_experience import offline_experience


def read(p):return json.loads(p.read_text(encoding="utf-8"))


def main(workspace):
    c=workspace/"Continuation"
    source=c/"RECURSIVE_SUMMARY_SOURCES"
    prep=c/"RECURSIVE_SUMMARY_PREPARATION_PREFLIGHT_FIXED"
    initial=c/"RECURSIVE_SUMMARY_PREPARATION"
    first=c/"RECURSIVE_SUMMARY_FIRST"
    audit=c/"RECURSIVE_SUMMARY_AUDIT/replay.json"
    final=c/"RECURSIVE_SUMMARY_FINALIZATION"
    reg,report,replay=read(prep/"registration.json"),read(first/"report.json"),read(audit)
    receipt=read(prep/"first-result-receipt.json")
    assert replay["status"]=="PASS_INDEPENDENT_RECURSIVE_SUMMARY_ENGINEERING_AUDIT"
    assert digest(first/"report.json")==receipt["report_sha256"]==replay["original_report_sha256"]
    assert digest(first/"manifest.json")==receipt["manifest_sha256"]==replay["original_manifest_sha256"]
    assert all(digest(first/p)==pin for p,pin in read(first/"manifest.json").items())
    assert all(digest(ROOT/p)==pin for p,pin in reg["sources"].items())
    previous=read(ROOT/"docs/experiments/inductive_complete_cost.pins.json")
    old_reports={**previous["old_first_report_pins_unchanged"],"INDUCTIVE_COMPLETE_COST_FIRST":previous["first_report_sha256"]}
    assert all(digest(c/name/"report.json")==pin for name,pin in old_reports.items())
    assert all(digest(ROOT/p)==pin for p,pin in {**previous["sources"],**previous["old_frozen_sources_unchanged"]}.items())
    assert not (initial/"first-result-receipt.json").exists()
    assert digest(initial/"registration.json")==read(initial/"freeze-receipt.json")["registration_sha256"]
    assert all(digest(initial/"source"/p)==pin for p,pin in read(initial/"registration.json")["sources"].items())
    registry={"schema":"neumann.opened-recursive-summary-assets.v1","public":{},"fixtures":{},"offline":{},
              "upstream_manifest_path":str((source/"manifest.json").relative_to(workspace)),
              "upstream_manifest_sha256":digest(source/"manifest.json"),"fresh_eligible":0,"training_activated":False}
    denied=0
    for case in report["cases"]:
        name=case["id"];fixture=case["source_role"]=="F"
        common={"problem_kind":"integer_list_right_fold","allowed_use":"opened_development_only",
                "source_study":reg["identity"],"source_report_sha256":digest(first/"report.json"),
                "equivalence_group":"opened-list-reference/"+name,"historically_opened":True,"fresh_eligible":False}
        if not fixture:
            original=source/"benchmarks/list"/(name+".ml")
            common.update(source_original_path=str(original.relative_to(workspace)),source_original_sha256=digest(original),
                          projection_semantics=reg["source_semantics"])
        public=first/("fixtures" if fixture else "public")/(name+".json")
        asset={**common,"role":"F" if fixture else "D","runtime":not fixture,
               "path":str(public.relative_to(workspace)),"sha256":digest(public)}
        registry["fixtures" if fixture else "public"][name]=asset
        if fixture:validate_problem(load_json_view(workspace,asset,"fixture"))
        else:assert problem_view(workspace,asset)==read(public)
        prohibited=["train","fresh_eval"]+(["development_problem"] if fixture else [])
        for purpose in prohibited:
            try:authorize(asset,purpose)
            except DataUseError:denied+=1
            else:raise AssertionError("Data authority unexpectedly promoted")
        offline=first/"offline"/(name+".json")
        asset={**common,"role":"O","runtime":False,"path":str(offline.relative_to(workspace)),"sha256":digest(offline)}
        registry["offline"][name]=asset
        assert offline_experience(workspace,asset)["certificate"]["accepted"]
        for purpose in ["train","fresh_eval","development_problem"]:
            try:authorize(asset,purpose)
            except DataUseError:denied+=1
            else:raise AssertionError("Oracle promoted into runtime/training/fresh")
    assert denied==26
    ledger_path=ROOT/"docs/experiments/experiment_decision_ledger.json"
    plan_path=ROOT/"docs/experiments/minimum_decisive_plan.v1.json"
    portfolio_path=ROOT/"docs/experiments/representation_generation_portfolio.json"
    ledger,plan,portfolio=[read(p) for p in [ledger_path,plan_path,portfolio_path]]
    assert "recursive_summary_engineering" not in ledger and not final.exists()
    assert digest(portfolio_path)==previous["portfolio_sha256"]
    final.mkdir()
    for p in [ledger_path,plan_path,portfolio_path,workspace/"AGENTS.md",workspace/"CONTINUE_HERE.md"]:
        (final/(p.name+".before")).write_bytes(p.read_bytes())
    save(final/"preflight_amendment.json",{"initial_registration_sha256":digest(initial/"registration.json"),
        "initial_registration_status":"NOT_EXECUTED_PREFLIGHT_SOURCE_REPAIR",
        "executed_registration_sha256":digest(prep/"registration.json"),
        "reason":"timeout branch could consult a previous child variable; now qualifies only the current non-timeout exit receipt",
        "initial_source_copy_preserved":True,"first_results_or_budgets_replaced":False})
    registry_path=ROOT/"experiments/recursive_summary_asset_registry.json";save(registry_path,registry)
    registration=ROOT/"docs/experiments/recursive_summary.engineering-registration.json"
    registration.write_bytes((prep/"registration.json").read_bytes())
    entry={"kind":reg["kind"],"status":report["status"],"public_adapted_references":4,"manual_fixture":1,
           "native_public_synthesis_accepted":3,"native_mss_status":"UNKNOWN",
           "paired_numeric_queries":8736,"accepted_summary_proposals":8,"universal_obligations":72,
           "independent_Z3_AST_and_saved_SMT_checks":144,"false_proposals_rejected":3,
           "source_commit":reg["source_commit"],"full_Synduce_installed_or_run":False,
           "result":"../../Continuation/RECURSIVE_SUMMARY_FIRST/report.json",
           "audit":"../../Continuation/RECURSIVE_SUMMARY_AUDIT/replay.json",
           "fresh_eligible":0,"learned_policy_implemented":False,"performance_measured":False,
           "G0_passed":False,"G1_admitted":False,"first_evidence_no_replacement":True}
    ledger["recursive_summary_engineering"]=entry
    plan["stages"]["G1"]["recursive_generation_engineering_interface"]=entry
    portfolio["evidence_report_pins"]["RECURSIVE_SUMMARY_FIRST"]=digest(first/"report.json")
    portfolio["latest_generation_engineering"]=entry
    for candidate in portfolio["retained_for_headroom_design"]:
        if candidate["candidate"]=="goal-preserving recursive summaries":
            candidate.update(kernel_implemented=True,native_prototype_implemented=True,learned_policy_implemented=False,
                             implemented_scope="piecewise linear mathematical integer list folds with generated auxiliary summaries",
                             strongest_full_baseline_implemented=False,headroom_admitted=False,
                             engineering_evidence="RECURSIVE_SUMMARY_FIRST")
    for path,value in [(ledger_path,ledger),(plan_path,plan),(portfolio_path,portfolio)]:save(path,value)
    agents=workspace/"AGENTS.md"
    block="""Latest implementation 2026-10-07: RECURSIVE_SUMMARY_ENGINEERING_V1.
Read `GitHub/NEUMANN/docs/research/recursive_summary_engineering_2026-10-07.md`.
Generated piecewise-linear integer list summaries now support min/max/conditions,
auxiliary state,empty/Cons/ordered Concat/decode/invariant.9 sufficient universal
conditions certified by CVC5 QF_LIA plus induction; not complete,not proof objects,
not full OCaml/machine-int/floating/general effects. UNKNOWN/refutation blocks
execution; vacuous invariant rejected; copier/hash binding and tree budgets.
Original polynomial/cost frozen sources unchanged. This is verification/execute
infrastructure,NOT learned NEUMANN or a new computational discovery.
Pinned MIT Synduce b5c1d1611d3fbf5d8cdf9a23fde52c2cbba95a89,8 original files.
Strict small ML parser projects4 mathematical Nil/Cons references only; DOES NOT
replay original repr/target/Synduce protocol or overflow. No official benchmark score.
Public-only bounded known Houdini+CVC5 SyGuS prototype generated sum/mps/mts(3/4).
mss result UNKNOWN under registered5s synthesis budget,not full Synduce failure;
keep native result/invariant progress. Full Synduce OCaml/opam/dune NOT installed/run.
Fixed-reference-width native,max/pairwise-sum grammar,not strongest mature comparator.
Known manually supplied summaries4 plus1 lifted-prefix F fixture are explicit O.
Fixture shows fixed prefix value alone insufficient for concat; added total state
certified. Not autonomous learned state discovery or all scalar encodings impossible.
First engineering result PASS_ENGINEERING_ADAPTED_REFERENCE_CHECKS_ONLY:8 accepted
proposals72 sufficient conditions,8736 numeric tree queries over364 small lists
and3shapes per eligible route,NOT8736 independent tasks or cost/frontier evidence.
Three false proposals refuted. Independent Z3 own AST conditions72 and saved CVC5
queries72,independent numeric interpreter/math references8736 PASS;26 first files
and8 upstream hashes verified.144 related pytest PASS.4 D public,1 F fixture,5 O
offline,26 rights denials; train/fresh/O runtime API denied (not OS security).
Initial PREPARATION registration NOT EXECUTED: preflight timeout stale-child
eligibility bug repaired; corrected freeze PREPARATION_PREFLIGHT_FIXED retained
alongside original,no first result/budget replacement. Source docs/license read
and sum preview/fixture testing before registration explicitly disclosed.
Folders RECURSIVE_SUMMARY_SOURCES/PREPARATION/PREPARATION_PREFLIGHT_FIXED/FIRST/
AUDIT/FINALIZATION in Continuation. CVC5 1.4.1,z3-solver4.15.4.0 added to local
venv and optional recursive dependency; previous SymPy/mpmath identities unchanged.
Next cost admission needs full Synduce/equivalent strong baseline and known summary
library reuse,meaningful independent structure,complete investment/discovery/proof/
execution cost. Do NOT choose only prototype UNKNOWNs as training success or claim
cheap known provided formulas prove10x learned headroom. No new performance study,
learned policy,training,GPU,G0/G1 pass,fresh evaluation,remote publication or G2.
Latest measured cost remains previous INDUCTIVE_COMPLETE_COST_V1 about1x.
Fresh0,Q1-Q7 OPEN,Decision3 sealed unchanged. Completion percent cannot be inferred.

"""
    agents.write_text(agents.read_text(encoding="utf-8").replace("# Local workspace context\n\n","# Local workspace context\n\n"+block,1),encoding="utf-8")
    continue_file=workspace/"CONTINUE_HERE.md";text=continue_file.read_text(encoding="utf-8")
    text=text.replace("2026-10-07, 전체 운영 비용 검사 완료. 등록 범위의 10배 우위 미입증, 학습 미진입.",
                      "2026-10-07, 조건 분기·재귀 요약 검증/실행 기반 확장. 압도적 비용 우위·학습 모델 미입증.",1)
    text=text.replace("## 최신 비용 실측","## 보존한 최신 비용 실측",1)
    latest="""## 최신 구현과 현재 단계

[재귀 요약 구현·검증·한계](GitHub/NEUMANN/docs/research/recursive_summary_engineering_2026-10-07.md).
현재는 D0 이용 가능한 자료와 표현 생성·검증·실행 기반 단계다. 학습된 NEUMANN
관점 정책은 없고 G1/G2 미진입, 압도적 비용 우위 미입증이다. 임의 완성도%를 쓰지 않는다.
조건 분기/min/max를 가진 정확 정수 리스트 요약과 보조 상태를 인증하고 실행한다.
원래 목표·초기 상태·Cons 전이·순서 있는 Concat 결합·불변식을9개 충분 조건으로
검사한다. 반례/UNKNOWN은 실행하지 않는다. 일반 언어·machine overflow·독립 proof
object의 구현은 아니며 이전 동결 다항식/비용 소스는 변경하지 않았다.

MIT Synduce의 공개 reference4개를 pinned commit에서 가져와 수학적 정수 fold로
적응했다(전체 원본 OCaml/repr/프로토콜 재현·공식 benchmark score 아님).
공개 기호 prototype은 sum/mps/mts3개를 생성·인증했고 mss는5초 예산 UNKNOWN이다.
이것은 최강 full Synduce의 실패도 학습된 NEUMANN 성공도 아니다. 알려진 제공
요약4개와 보조 상태 추가 F fixture1개는 별도 O로 보존했다.
8제안/72조건,8736 작은 수치 query,거절3개. 독립 Z3 직접AST72+SMT72와 원래
수학 정의/별도 tree interpreter8736 PASS, 관련 pytest144개 PASS.
4D 공개/1F/5O,26권한 거절, fresh0, 학습/GPU 비활성.
초기 engineering동결은 timeout 분기오류를 첫 통합 실행 전 찾아 미실행으로
보존했고 수정 source를 따로 동결했다. 비용 문턱/첫 결과를 바꾸지 않았다.

다음 비용 투자는 강한 full Synduce/동등 구현과 알려진 요약의 재사용을 포함하고,
독립 구조·발견/검증/실행/투자의 계약이 먼저 필요하다. prototype 미해결만 골라
GPU를 쓰거나 제공 정답의 싼 실행을10배 지능으로 부르지 않는다.
Continuation에 RECURSIVE_SUMMARY_SOURCES, PREPARATION(미실행),
PREPARATION_PREFLIGHT_FIXED, FIRST, AUDIT, FINALIZATION을 보존한다.

"""
    continue_file.write_text(text.replace("## 보존한 최신 비용 실측",latest+"## 보존한 최신 비용 실측",1),encoding="utf-8")
    report_path=ROOT/"docs/research/recursive_summary_engineering_2026-10-07.md"
    pins={"schema":"neumann.recursive-summary-engineering-pins.v1",
          "registration_sha256":digest(registration),"upstream_manifest_sha256":digest(source/"manifest.json"),
          "first_report_sha256":digest(first/"report.json"),"first_manifest_sha256":digest(first/"manifest.json"),
          "sources":reg["sources"],"audit_sha256":digest(audit),"audit_source_sha256":digest(ROOT/"experiments/recursive_summary_replay.py"),
          "registry_sha256":digest(registry_path),"research_report_sha256":digest(report_path),
          "portfolio_sha256":digest(portfolio_path),"decision_ledger_sha256":digest(ledger_path),"plan_sha256":digest(plan_path),
          "pyproject_sha256":digest(ROOT/"pyproject.toml"),"finalization_source_sha256":digest(Path(__file__)),
          "old_first_report_pins_unchanged":old_reports,"G1_admitted":False,"fresh_eligible":0}
    pins_path=ROOT/"docs/experiments/recursive_summary.pins.json";save(pins_path,pins)
    save(final/"receipt.json",{"status":"PASS_RECURSIVE_ENGINEERING_FINALIZATION","pins_sha256":digest(pins_path),
        "D_public_registered":4,"F_fixture_registered":1,"O_offline_registered":5,"rights_denials":denied,
        "old_first_reports_unchanged":list(old_reports),"related_pytest_passed":144,"tests_are_capability_gate":False,
        "learning_performed":False,"GPU_started":False,"G1_admitted":False,"fresh_eligible":0,
        "requested_overwhelming_goal_proved":False})
    assert all(digest(first/p)==pin for p,pin in read(first/"manifest.json").items())
    print((final/"receipt.json").read_text(encoding="utf-8"))


if __name__=="__main__":main(Path(sys.argv[1]))
