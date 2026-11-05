# NEUMANN 1 | P2.8 최초 48개 독립 원본 평가: 표현력 FAIL, STOP

2026-11-05. 고정 North Star: Frontier-level problem solving with minimum necessary computation.

## 1. 이전 선택 사례와 새 검증의 분리
- 이전 공식 ARC 학습 파일 007bbfb7.json의 TEST 1/1 성공은 TRAIN과 형태를 보고 선택된 원본 진단이었다. 일반 전이가 아니다.
- P2.8은 사람이 설계한 두 입력 셀 공간 분해 구조와 네 조건별 {0,outer,inner} 선택 3^4=81개를 완전 열거한다. 프로그램 자체는 실행 가능하나 자율 신규 opcode 발명은 아니다.
- 이번 시험은 새로운 원본 ARC 공개 evaluation 48개이며, 기존 7개 동결 매니페스트의 중복 232개 제외. 남겨둔 원본 120개는 열지 않음.
- 최초 그룹/소스는 docs/experiments/q3_p28_FIRST_FRESH_TRANSFER48_COHORT_FROZEN.json 및 SOURCE_LOCK.json. 원본 상류 fchollet/ARC-AGI SHA 399030444e0ab0cc8b4e199870fb20b863846f34.
- 선택은 파일명만으로 FNV1a32 정렬, 파일 내용 보기 전 등록. TEST gold는 후보 제출 후에만 평가.

## 2. 첫 실제 결과
- 사전 조건: 기존 B/P20/P24/P25/P27 고전 기준선 대비 원본 추가 정확 정답 2개 이상, 신규 오답 0, 기존 정답 손실 0.
- 공식 FIRST ACTUAL GitHub Actions: https://github.com/yoonsj0305/NEUMANN/actions/runs/42018227034
- 원본 첫 보고서 SHA256: 1b708e7ccb3686637ee8a8cefcbdba1e03b1aa4abfaebe48d3eba8e51f84bd78
- 기존 고전 결합 정확 해결 3/48, P28 추가 0, 결합 후 그대로 3/48.
- P28 제출 0/48, 신규 오답 0/48, 학습 예제와 맞는 P28 규칙을 찾은 문제 0개.
- 탐색한 후보 프로그램 324개, TRAIN pair 평가 324회, 측정한 전체 실행 wall 약 6116.67 ms (이 GitHub CPU 런). 전력·달러 미측정.
- 과학적 첫 판정 P28_FRESH_TRANSFER_FAIL_STOP. 이와 별개로 CI 전체 실행 성공.
- 최초 사전 점검 시도 #42018000699는 P24 source-lock Git SHA 한 글자 오타로 원본 문제를 읽기 전에 종료되었고 NOT_EVALUATED임. 오류 lock 원본 별도 보존, source-lock 수정 v2. 학습기/비교기 코드는 바꾸지 않음.

## 3. 결정적 구조적 원인과 독립 증명
- 독립 Python 감사: https://github.com/yoonsj0305/NEUMANN/actions/runs/42018843483 (PASS).
- 공식 원본 48개 중 P2.8 입력 크기·출력 범위 제약에 진입 가능한 문제는 정확히 4개. 다른 44개, 즉 91.7%는 고정 언어의 입력 지원 범위 밖이다.
- 이 4개에서 81개의 조건별 실행식을 Python으로 새로 열거해 검사했다. 4×81=324개 후보 중 모든 TRAIN pair를 정확히 만족하는 후보가 0개다.
- 따라서 후보 순위 재조정이나 신경망 제어로 이 48개의 P28 성능을 구제할 수 없음이 고정 언어 내부에서 확인됐다.
- 첫 raw SHA와 코호트, 원본 파일, 소스 Git blob, 평가 집계를 감사했고, 조작한 성공 기록 거부 테스트도 통과했다.
- 이전 다섯 고전 비교기의 세부 알고리즘을 다른 언어로 다시 구현한 것은 아니며 기존 첫 결과의 불변 기록과 합계만 검증했다.

## 4. 과학적 결정
P28 기존 규칙의 속도 최적화, 후보 열거 가속, 신경망 재순위, 테스트 데이터에 맞춘 규칙 추가는 전부 STOP. 이는 일반적인 구조발견 불가능성 증명이 아니라 P28 동결된 표현언어의 한계다. 해당 평가와 과학적 FAIL은 바꾸지 않는다. P28 자체는 동일 81개를 쓸 수 있는 고전 TOOL과 동일한 의미 탐색 권한을 가지므로 Q3 자율 연산 발명도 입증되지 않았다.

Q1~Q7 OPEN. 새로운 작업은 표현 생성 원리, 미지 문제에 대한 독립 검사, 최강 고전 기준선과의 동일 권한 비교에만 투입.
