# NEUMANN 1 | Q0 근본 목적: ARC-AGI-2 실제 일반화·표현 한계 첫 검증

**2026-10-22, 연구 판정: SCOPED REPRESENTATION EXPANSION PASS / FRONTIER, Q3 LEARNED-EXCLUSIVE, Q4 10× OPEN.**

## 근본 목표 및 질문

**North Star: Frontier-level problem solving with minimum necessary computation.** 이미 풀린 SyGuS 불변량 4개를 반복하여 증명서 숫자를 늘리는 대신, 낯선 시각 추론 문제에서 (1) 정답 자체를 생성할 수 있는가, (2) 학습이 필요한가, (3) 실제 계산비용이 얼마인가를 직접 측정한다.

## 공식 ARC-AGI-2 출처, 유출 방지 및 평가 순서

- 정확한 공식 GitHub 출처: `arcprize/ARC-AGI-2@f3283f727488ad98fe575ea6a5ac981e4a188e49`, 공개 `data/training` 1,000개 Git tree `dac7259367cc5099ef6a7b604a50a93affbbee33`, 공개 `data/evaluation` 120개 tree `8d04288aac3146b7c47d0b799c18bc9c0217d838`.
- 1,000개 파일을 `SHA256(task_id)` 오름차순 정렬해 앞 800개 DEV, 뒤 200개 **훈련집합 내부 holdout**으로 분리. 두 집합의 ID 목록 SHA256을 실험 전에 등록: DEV `b781269e0c7deaf49a212b666ddc94cff4915ebe5c8d5251c0134901f2f56281`, HOLDOUT `9f9f9f80d9c51dd31e0ad999e7d2cf7289fcd2791f785ba41fd74d1b86c8dc9b`.
- 새 코드 `arc_compositional_grammar.py` SHA256 `72f0cb9d0a42e972eac1e0edf891858d0c1439401e29d90b9ecde4721fcce84c`. 공식 원본을 사용하며, 문제별 색상 대응을 train demonstration에 한해 학습하고 기존 단순 프로그램 96개 + 8개 기하 변환×8개 객체 연산 합성 64개를 계산. **NN 학습 없음, 디자이너가 연산자 종류를 제공.**
- 200개 검증 문제의 테스트 정답은 추론 과정에 전달하지 않고, **예측 파일을 SHA256으로 먼저 기록한 뒤** 다른 절차에서 채점. 첫 로컬 예측 SHA256 `ad5d91f259fed414af7ee36077a5a4f98f17db71b1126d0a4757b66d0ff7d5ee`.
- GitHub PR [#460](https://github.com/yoonsj0305/NEUMANN/pull/460). 독립 3-작업 CI [#39734910312](https://github.com/yoonsj0305/NEUMANN/actions/runs/39734910312) **SUCCESS**: 소스 트리 인증 + 200 test output 마스킹, 별도 예측 작업 및 사전 채점 증거 보존, 별도 답안 다운로드/엄격 채점/사후 문법 oracle. 기존 동시 실험 workflow [#39734910237](https://github.com/yoonsj0305/NEUMANN/actions/runs/39734910237)도 SUCCESS.

## 근본 Q0 사실: 200문제, 동일 분모

| 방법 | Demonstration 100% 일치 후보 | 실제 test 완전 정답 |
|---|---:|---:|
| 기존 단일 고정 변환 문법 96개 | 7/200 | 7/200 |
| 색 대응+객체 연산 확장 문법 | 11/200 | **10/200** |
| 확장된 문법의 정답 참조 허용 사후 *oracle ceiling* | 11개 후보 존재 | **10/200** |

- 추가로 맞힌 실제 원본 **3개**: `6d0aefbc`, `833dafe3`, `5582e5ca`; 기존 기준선만 맞힌 문제는 0개.
- 첫 200개에 대해 확장 모델의 정확도 5.0% (Wilson 95% CI **2.74%–8.96%**), 기존 3.5% (CI **1.71%–7.05%**). 추가 3/200의 비율 1.5% (CI **0.51%–4.32%**). 대응표본 비일치 3:0에 대한 정확 양측 McNemar p=**0.25**. **단일 표본의 안정적인 일반화 우월성을 증명하지 않음**.
- 엄격한 사후 oracle가 모든 실제 정답 생성 후보를 확인: **200개 가운데 현재 동결된 합성 문법의 어떤 admissible 단일 프로그램도 정확한 test를 내지 못하는 문제가 190개**. 해당 후보 리스트 안에서 신경망 ranker만 더 개선할 *추가* 정확 정답 헤드룸은 **0개**. **이는 현재 160개 형태(96 base + 64 object)와 fitted color mapping의 한계이지, ARC-AGI-2 문제의 불가능성이나 임의 새로운 프로그램의 불가능성을 증명한 것이 아님.**
- 전체 inference wall 로컬 약 **6.7403초** (120 정답 후송/설치/데이터 준비 제외). 실제 GPU 전력/프런티어 LLM baseline/훈련 비용은 이번 symbolic composer에서 측정 대상이 아님.

## 이전에 평가한 공식 PUBLIC EVALUATION 120: POSTHOC만

기존 96-문법 첫 공식 별도 평가 [#39733043117](https://github.com/yoonsj0305/NEUMANN/actions/runs/39733043117)는 정확 **0/120**, 96 DSL의 사후 oracle도 **0/120**이었다. 새로운 동결 합성 문법을 해당 공개 평가의 **이미 다른 연구에서 한 번 본 세트에 POSTHOC로** 적용하면 120개 가운데 시범 예제를 완전 일치시키는 후보는 **0/120**이다. 새로운 독립 *firstblind* 또는 프런티어 성능으로 중복해서 계산하지 않는다. 추론 입력은 앞선 공식 검증기가 답안을 제거한 공개 evaluation 데이터. 새로운 공식 평가 성능 개선이라는 주장은 없다.

## 추가 반증: 단순 2단계 열거로 해결되지 않음

8개 기하/객체 연산의 중첩을 포함해 generic 160×160 연산 쌍에서 내부 입력 격자를 의미적으로 중복 제거하는 비용 제한 검색기를 별도로 시범 구현했다. SHA-정렬 DEV800 앞의 **24개 개발 원본**에 한정한 실측에서 기존 한 단계 프로그램 정답 **3개**, 2단계의 *추가* 정답 **0개**, 추가 계산 약 17.7초. 더 넓은 DEV64 시험은 실행 제한으로 **중단(미완료)**; 완료로 보고하지 않고 표본 전체 64개 결과로 일반화하지 않는다. 즉 무조건 2단계 확장이 해법이라는 가설은 현재 증거에서 지지되지 않으며, 새로운 적절한 중간 목표·객체 추상화가 필요한지 연구해야 한다.

## 과학적 결정

1. **PASS (범위 한정)**: source-grounded compositional symbolic grammar가 기존 닫힌 96 변환 프로그램보다 200개의 훈련집합 내부 검증 원본에서 정확 **3개 추가 문제**를 해결하는 *실제 비학습 구조 합성*을 보였다.
2. **PASS (표현 천장)**: 해당 동결 후보 생성 및 데이터 200개에 관해 oracle 10/200은 exact exhaustive class bound다. 신경망 reranker만으로는 더 늘릴 추가 정답이 없음. 출력할 수 없는 구조는 gradient step 증가로 복구 불가능하다.
3. **FAIL / NOT YET**: 공식 평가 120개로의 실질 문제 해결 전이, 학습 모델만의 새로운 연산자 발견, 가장 강한 전용 ARC 고전 솔버 대비 우위, 전체비용 10× 절감, 프런티어급 성능 등 NEUMANN 근본 목적은 미입증이다.
4. **NEXT DECISIVE GATE**: 미리 고정한 **새로운 독립 원본 또는 공개 훈련집합 내 미개봉 엄격 holdout**에서 새 typed AST 연산자·객체 관계·중간 목표의 **실제 생성**을 평가할 것. 프로그램 생성기 vs 같은 권한의 최강 비학습 탐색 vs 고정문법 학습 선택기를 비용·정답 동등 분모로 비교하고 추론 종료까지의 모든 비용을 기록할 것. 이전에 사용한 ARC2 public evaluation이나 dev/holdout 답을 보고 튜닝한 후 firstblind라 표기하지 말 것.

**글로벌 Q1–Q7 OPEN. 현재 성공한 것은 근본 목표를 향한 실측과 구조 표현 병목의 정량적 발견이지 프런티어 급 지능 자체가 아니다.**
