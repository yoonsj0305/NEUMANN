# NEUMANN 1 현재 상태 — 2026-10-08

2026-10-09 배포 준비: 사용자가 미반영 작업의 일괄 GitHub 업로드를 승인했다.
누적 감사·CPU 진단·복구 원본을 후속 Draft PR과 별도 counting 증거 브랜치로
보존한다. 아래의 'GitHub write 없음'은 해당 연구 실행 시점의 기록이다.
현재 과학적 결정은 **HOLD_LEARNING**이며, 업로드와 CI는 연구 성공 판정이 아니다.

후속 원본 복구: P1 최초ZIP8개/318entries의 byte identity를 확인하고 기존
model-free replay7건을 통과했다. P1.7최초 replay failure는 그대로다. P1.5산술
4/4로 감사 표의 전사만 수정했고, P1.2stable misclassification와 P1.5/P1.6
실행 전 wire/header 거절을 분리했다. P1.11.1raw-top6/12로 threshold-only
요구9/12달성은 배제된다. Registry278records/185document nodes와21missing/
intentional exclusions이며 과거판정은 변경하지 않았다.
[복구·독립검증·연구적 한계](../research/audit/P1_RECOVERY_REVIEW.md).

5시간 후속 작업: 기존 G0 A를 사전 등록하고 public QVBS 13요청/9family의
strong native 확률 경로125개를 실행했다. 전체는INCOMPLETE:361exactPASS,
14NOT_VERIFIED,9process failures,15timeouts. 등록two-bin optimistic 평균
BRP4.364x/Crowds9.67849x로family10배PASS는없다. Coupon/EGL의큰singleton
floor에는적용가능한classicalanalyticcontrol이있고Herman15에도공개정확정리가
있다. 상태축소/무료Oracle/동일compile재사용은학습된새지능의성공이아니다.
[실측·첫실패·독립해시·판정](research/g0_probabilistic_native_2026-10-08.md),
[정확analytic대조군과반례](research/probabilistic_analytic_controls_2026-10-08.md).

LP 누적 원인 분석은 새 모델 없이 진행했다. 학습 원본48개는최적positive
basis가dual을유일하게정했지만BP전이16개는14~112차원dual자유도가남았다.
동시에cost/residual두특징이BP에서상수로변했다. 두별도원인을분리했으며
solecause/새학습승인으로확대하지않는다. 현재registry278행은독립실험수가
아니다. **HOLD_LEARNING**,Phase3/G1/G2/봉인평가미진입,GitHub/Notion write없음.
아래는기존시점의판정과기록이다.

v2.0 Phase2: Basis-pursuit 인증 경제성의 별도 opened 판별 실행 완료.
16원본/576관측 모두 최종original-valid; 기존 Native와비교한 D(무료support+
유료dual)는0.484×,E(무료support+dual)는4.091×,10배0/16이었다.
11/16원본의full dual LP 비용이 이번adapter의병목이었다. ENGINEERING PASS,
NO REGISTERED TENFOLD HEADROOM,**HOLD_LEARNING**. Phase3/G1/G2를 시작하지 않는다.
새forward/학습/봉인/GitHub write없이로컬CPU계약으로실행했다.
[최초계약·독립검증·실측·중단결정](research/bp_certificate_diagnostic_2026-10-08.md).
아래문단은Phase1및그이전시점기록이다.

Master Directive v2.0 후속 감사: **HOLD_LEARNING**.
기존 문서·최초 결과 event·unmerged variant·누락 항목을 단일
[registry](../research/audit/EXPERIMENT_REGISTRY.csv)와
[누적 원인 분석](../research/audit/EVIDENCE_TO_DECISION_MASTER_REVIEW.md)에 연결했다.
M106 original final256/restricted232 witnesses를 모델·solver 없이 확인했다.
첫 timed19시도(13후보경로/7원본)는 최적 primal을 얻고도 original dual
feasibility 때문에 거절됐다. 기존 Native dual을 offline으로 결합하면19/19
원래 검증을 통과하지만, dual을 싸게 얻는 비용은 UNKNOWN다. 모델 교체로
원인을 대체하지 않는다. v102 bounded Q34 PASS와 Q5/M106/D2 실패는 유지한다.
Q5의192model-view행 비용 envelope와 조건부 초기 투자 회수량도 복원했다.

이전 native counting 첫 실행은12/17검증 완료·5certificate-generation timeout의
INCOMPLETE다. 완료12개 중10배0개이며 upstream debug I/O와 harness 측정
한계가 있다. 해당 cold pipeline 학습은 HOLD. 원본 ZIP은 로컬에서 모두 검증·
보존했고 Kaggle CPU 세션은 종료했다. Formal Lean/Polar smoke는 미완료다.
이번 v2단계에서 새 GPU/forward/solver/data 생성·봉인 접근·GitHub write는 없다.
이전 시점 문단과 판정은 아래에 보존한다.

사용자 Directive v1.1 후속 작업: 초기 도달 상태의 **Guarded 인증 ENGINEERING
PASS**, 기존 불변량 발견→초기 조건 결합→목표 충분성 연결 구현. 관련 152개
로컬 테스트와 126개 독립 항등식 검사가 통과했다. 기존 Universal/과거 source
pin은 보존했다. 동일하게 특수화한 Native와 무료 표현의 cold1/cold64/warm
비율은 0.967/1.022/0.988배로 **이 fixture에서 NO MEANINGFUL HEADROOM**이다.
이 계열의 학습은 HOLD. 새 G0 PASS·학습·프런티어 성능 성공은 아니다.

- [v1.1 구현·증명·반례·비용·다음 결정](research/guarded_perspective_2026-10-08.md)

목표는 **프런티어급 능력 + 압도적인 총계산 우위 + 새로운 학습 가능한 계산 원리**다.
현재 이 목표를 달성했다고 주장할 증거는 없다. Q1~Q7은 열려 있으며 G1/G2와
Decision 3 봉인 평가는 실행하지 않았다.

이번 공개에는 기존 자료 재사용, 원본 solver 실행, 생성·검증 기반 코드, 실패 보존,
총비용 비교, 원본 텐서 비용 검사, 데이터 권한 검사와 독립 감사 자료가 들어 있다.
최신 등록 완전 비용 비교는 약 1배다. 원본 배열의 실행 구성요소만 비교한 최대
약 3.45배는 전체 비용 개선이나 학습된 NEUMANN 성능으로 취급하지 않는다.

2026-10-08 사용자 R&D Directive 적용: 저장소·CI·선택된 원본 증거를 재감사했고,
두 기존 수학적 실행 영역을 잇는 최소 Perspective 계약을 추가했다. 학습된
생성·전이는 미구현이다. 현재 cold 재귀 비용에서 검증+compile을 완전히 없애는
민감도 계산도 약 1.05배다. 이는 새 실측이 아니다. 새 후보 두 개는 강한 native와
목표 보존 표현을 연결하기 전까지 성능 측정·학습 HOLD이며 G1/G2는 미진입이다.

- [R&D 상태 감사와 작업 분류](../RESEARCH_STATE_AUDIT.md)
- [두 G0 후보와 중단 기준](research/g0_candidate_review_2026-10-08.md)
- [원본 해시·비용 민감도 재현 결과](research/research_state_audit_2026-10-08.json)

- [최신 결과·범위·실패와 복구](research/sufu_and_official_tensors_2026-10-07.md)
- [공개 증거와 로컬 원본 해시 목록](experiments/results/structural_evidence_2026_10_07/publication_manifest.json)
- [동결 목표와 최소 결정적 실험](research/minimum_decisive_experiments_2026-10-06.md)
- [실험 의사결정 원장](experiments/experiment_decision_ledger.json)

기존 연구 문서는 작성 당시 상태를 보존한다. 이후 완료된 실행·복구의 상태는 위
최신 보고서를 기준으로 읽는다. 대용량 원본 자료는 로컬 `NEUMANN 1/Continuation/`에
보존되어 있고, GitHub의 해시 목록은 그 원본 파일을 대신하지 않는다.
