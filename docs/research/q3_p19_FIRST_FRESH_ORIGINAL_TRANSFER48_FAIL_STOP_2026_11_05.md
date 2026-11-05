# NEUMANN 1 | P1.9 최초 48개 독립 원본 평가: 실행식 합성은 성공, 기준선 초과 FAIL

2026-11-05. North Star: Frontier-level problem solving with minimum necessary computation.

## 1. 전제와 측정 설계
P1.9는 사람 설계의 bounded grammar 안에서 조건부 식, 평행이동/자르기/회전, 두 패널의 관계 연산을 만들어 TRAIN 예시를 정확히 만족시키는 실행 프로그램을 고른다. 과거 48개 열린 원본에서 약한 기준선 대비 추가 +2 성공 이력이 있었지만, 독립 원본 전이는 아직 증명되지 않았다.

- 이 테스트는 공식 공개 ARC-AGI 원본 data/evaluation 400개 중 과거 8개 동결 연구 그룹의 280개를 제외하고, 남은 120개에서 파일명 해시로 48개를 선별, 신규 코호트/소스 SHA 먼저 동결.
- 나머지 72개 원본은 열지 않고 유지한다. 이번 평가군의 TEST gold는 실제 7개 경로의 proposal 생성이 모두 끝난 뒤 원본 checker에서만 사용한다.
- 소스 고정: experiments/q3_goal_conditioned_induction_p19.mjs 원본 Git blob 60815950cd5e7da777e20547bb7389cd0de994a7. 모델 0회, 사람 teacher 0회.
- 강한 비교: P11 B, P20, P24, P25, P27 full enumeration, P28 81 candidate. 동일 공개 문제와 original TEST checker.
- 최초 목표: 추가 정확 해결 >=2, 신규 오답 제출 0, 기존 정답 손실 0.

## 2. 첫 실제 결과
- 공식 FIRST actual: https://github.com/yoonsj0305/NEUMANN/actions/runs/42019505824
- 첫 raw receipt SHA256: fc55628f4cd1627a0f17f52a66ced0cec66830b58ed0658b74c113dae61ebfeb
- 기존 기준선 2/48 정답. P1.9 단독 1/48. 합쳐도 2/48. 추가 정확 해결 0개.
- 합성기가 48개 중 단 1개에 대해서만 정답을 제출했으며 오답 제출은 없었다. 그 1개는 기존 기준선과 겹친다.
- 완전 후보 AST 탐색 76,704회, TRAIN pair 검사 253,207회.
- GitHub CPU 원본 전체 실행 약 16,191.12 ms, 모델/teacher 0호출. 전력·달러 미계측.
- 상태 P19_FRESH_TRANSFER_FAIL_STOP. 첫 결과를 재선택하거나 유리하게 retune하지 않는다.

## 3. 독립 검증
- 독립 Python 원본 감사: https://github.com/yoonsj0305/NEUMANN/actions/runs/42019935224 PASS.
- 원본 첫 파일 SHA, 동결 소스/코호트 Git blob, 상류 원본 평가 파일의 SHA, 48개 문제 순서를 모두 검사.
- P1.9가 제출한 단 한 개의 실행 프로그램을 별도 Python interpreter로 다시 실행, TRAIN 예시와 TEST input에 대한 실제 프로그램 실행 결과를 확인하고 공식 TEST output과 대조. 독립 원본 정확 1건, 추가 정확 0건.
- 원본 보고서의 추가 정답 0을 조작해 47로 바꾼 위조 입력은 독립 감사가 거부했다.
- 여섯 고전 기준선 엔진 전체를 Python에서 별도 재구현한 것은 아니며 그 첫 파일의 정확성 플래그 집계는 SHA 고정에 의존.

## 4. STOP 및 연구 중심축
P19는 예시에서 실행식을 생성하는 메커니즘 자체는 실제로 작동했다. 하지만 현 인간 설계 문법의 후보 76,704개를 검사하고도 추가 성과 0/48이었다. 학습·증명·전이·전체비용의 10배 우위는 미확립. 추가 AST 깊이 확장/순위 최적화/같은 코호트 재탐색을 STOP.

P28 다른 첫 원본 48개 역시 고전 기준선 3, P28 추가 0, 44개 입력 범위 밖, 4개 TRAIN-fit 0개로 STOP되었다.

두 경로의 동결된 실패가 입증하는 것은 NEUMANN의 일반적 불가능성이 아니라 현재 **문제 표현을 발견할 수 있는 메커니즘이 부족하다**는 점이다. 최강 고전 도구의 동등한 권한과 원본 독립 검증을 통과하는 genuinely new executable semantics가 개발되기 전에는 Decision 3, Q3/Q6/Q7, frontier/10x 승격을 하지 않는다. 원본 ARC evaluation 예약 72개는 다른 메커니즘의 신규 출처동결 평가를 위해 보존한다.

Q1-Q7 OPEN.
