# NEUMANN 1 현재 상태 — 2026-10-08

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
