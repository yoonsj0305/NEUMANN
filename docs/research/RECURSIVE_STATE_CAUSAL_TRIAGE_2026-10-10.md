# 원본 목표에 충분한 재귀 상태: 기존 증거 기반 판정

2026-10-10 KST. 기준선 `bb10651f7168b0ab1c58e517e3ac8f7fe69a6780`을 보존한
별도 opened-development 분석이다. **정보를 잃는 실제 표현 병목은 확인했지만,
기존 Classical-Hybrid가 이미 해결하므로 이 메커니즘의 학습 투자는 HOLD한다.**
새 F0/G0 성능 평가, 프런티어 격차, 학습된 구조 발견, 10배 우위의 증거가 아니다.
무료 GPU 탐색을 종료했고 Gemma F0는 `BLOCKED_SMALL_MODEL_RUNTIME`이다.

## 선택과 검증 결과

하나의 문제군, **목표에 충분한 ordered recursive summary**를 선택했다.
이유는 공개 원문, 두 Native의 최초 로그, 별도의 원본 목표 인증과 기존 실행기가
동시에 있어 탐색 실패와 표현 불가능성을 가장 적은 비용으로 분리할 수 있기
때문이다. 전 분야에서 가장 유망하다는 주장이 아니라 현재 증거의 판별 가능성에
따른 선택이다. 새로운 코호트나 합성 학습 자료를 만들지 않았다.

선택 원본은 Synduce `benchmarks/list/mps_no_sum.ml`이다.
원문 commit `b5c1d1611d3fbf5d8cdf9a23fde52c2cbba95a89`, SHA-256
`37ff22ac5b3436dcd4d4a316b6783c383096f15da5c98d1368649f2587fec891`.
`benchmarks/incomplete/list/mps_no_sum.ml`은 같은 바이트 원본이며 독립 문제로
추가 계산하지 않는다. 원문 목표는 빈 prefix를 포함한 최대 prefix 합이다.
원래 `hom`은 각 자식의 최종 목표 값만 `join`에 전달한다.

| 원래 리스트 | 원래 목표 값 | 오른쪽 `[1]` 연결 후 목표 |
| --- | ---: | ---: |
| `[-1]` | 0 | 0 |
| `[0]` | 0 | 1 |

오른쪽 자식의 목표도 두 경우 모두 1이다. 따라서 원래 자식 목표 값만 받는
결정론적 `join(0, 1)`은 동시에 0과 1이어야 한다. **어떤 식을 더 잘 탐색해도
이 인터페이스 안에서는 정답을 만들 수 없다.** 두 자식은 실제 도달 가능한
리스트이며 원문의 비음수 목표 조건도 만족한다. 이 결론은 임의의 더 풍부한
요약이나 숨은 상태를 가진 실행기의 불가능성으로 확장하지 않는다.

기존 `recursive_library_baseline.py`는 이미 `prefix_lift`를 보유한다:

`state = (maximum_prefix, total_sum)`

`merge(L,R) = (max(L.prefix, L.sum + R.prefix), L.sum + R.sum)`

`decode(state) = state.prefix`

이 상태는 두 왼쪽 리스트를 `(0,-1)`과 `(0,0)`으로 구별한다. 저장된 제안으로
실행한 두 witness 모두 원래 fold 출력과 일치했다. 새 로더/솔버/실행기나 새
표현 생성기를 만들지 않았다. 원래 반환형은 scalar인데 latent state는 2개이므로
**원래 scalar 합성 hole을 그대로 채운 성공이 아니다.** 내부 상태를 바꾸고
외부 원래 목표를 decoder로 복원하는 기존 Classical-Hybrid 경로의 성공이다.

## 이전 증거와 이번 확인의 경계

`SYNDuce_FULL_BASELINE_FIRST`와 `SYNDuce_CVC4_FIRST`의 등록된 29 source entry,
각 3반복을 모두 연결했다. 174는 관측 수다. 29개 byte group 역시 수학적 motif
독립성을 보장하지 않으며 fresh 원본 수는 0이다. 사용한 최초 manifest 및
파일 해시를 검사하고 원문 해시로 결합했다.

| 저장된 결과 | CVC5 | CVC4 |
| --- | ---: | ---: |
| Upstream reported realizable | 70 | 78 |
| Upstream reported unrealizable | 9 | 9 |
| External timeout | 6 | 0 |
| Execution error / not evaluated | 2 | 0 |

이는 upstream 보고 상태다. 이 코호트의 모든 원문에 독립 인증을 수행한
정답률로 읽으면 안 된다. 완료된 Native 코호트는 재실행하지 않았다.

`poly_no_fac.ml`과 `mss.ml`의 CVC5 6개 timeout 관측은 CVC4가 해결했다고
보고했다. CVC4 tool-only 중앙값은 각각 1.729636초, 36.367856초다.
`mps_no_ensures.ml`의 CVC5 오류 2회도 CVC4에서는 오류 없이 해결 보고가 있다.
따라서 이를 Strong Native의 구조적 능력 한계로 사용하지 않는다.
`poly_no_fac.ml`의 저장된 CVC4 출력에는 값과 곱셈 인자를 함께 전달하는
lifted 표현도 있다. 기존 Native의 표현 생성 권한을 제한할 이유가 없다.

선택 원본에 대해서는 두 Native 모두 각각 3회 `UPSTREAM_REPORTED_UNREALIZABLE`
이다. 이 라벨 자체를 증명으로 승격하지 않고 위의 정확한 context collision으로
제한된 인터페이스의 불가능성을 확인했다. 기존 `SOURCE_BOUND_RECURSIVE_FIRST`
에는 `prefix_lift`에 대한 **9개 CVC5 UNSAT 조건 및 원문 flatten/order/termination
binding**이 보존돼 있다. 이번에는 hash/goal/proposal 연결과 상태를 확인해
재사용했으며 기존 증명 코호트를 다시 실행하지 않았다.
그 인증은 모든 유한 수학적 정수 리스트에 대한 충분 귀납 조건을 다룬다.
전체 OCaml 시스템, machine overflow, 자연어 의도, 학습된 발견은 인증하지 않는다.

이번에 추가된 것은 고정 witness의 정확한 반증과 174개 저장 관측의 원문별
연결이다. 과거 최초 판정·원문·archive를 변경하지 않았다.

## 경제성 및 결정

선택 원본의 기존 인증 시간 0.030611초는 **과거 관측**이며 신규 실측이 아니다.
새 분석의 1.400844초는 파일 해시 검사와 분석 시간이고 배포 추론 비용이 아니다.
전체 발견/시작/인증/실행/폴백 비용의 공정한 비율은 이 원본에서 UNKNOWN이다.
FLOPs, 에너지, 금전 비용, peak memory도 새로 측정하지 않았다.

이미 완료한 별도 20-AST 비용 계약은 강한 known-monoid/finite-response Native와
무료 유효 참조 표현에 같은 인증·DAG 재사용 권한을 제공한 비교다. 기존 결과는
cold1 1.00477745배, cold16 1.00236820배, 10배 0/20이다.
[기존 전체 비용 기록](compressed_recursive_cost_2026-10-07.md)을 그대로 유지한다.
이 수치를 이번 단일 원문의 비용으로 대입하거나 모든 요약의 상한으로 부르지 않는다.

결정: `HOLD_LEARNING_EXISTING_RECURSIVE_MONOID_FAMILY`.
반증된 대상: `GOAL_ONLY_RECURSIVE_JOIN`.
원래 목표에 필요한 정보가 함수 합성에 충분한 정보와 다르다는 병목은 실재한다.
그러나 이 원본의 필요한 상태는 기존 고전 알고리즘이 이미 제공하고 인증한다.
신규 학습이나 추가 headroom 코호트를 실행할 근거를 확보하지 못했다.
이 표현의 수학적 유효성과 엔지니어링 자산은 KEEP한다.

다음 단 하나의 판별 대상은 **`list/poly_no_fac.ml`의 저장된 Native 자동 lifting
출력 `(value, factor)`가 매개변수화된 원래 polynomial goal로 독립 인증되는지**다.
이는 현재 piecewise-linear 요약 인증의 범위 밖이고, Native는 이미 생성 성공을
보고했다. 먼저 저장된 원문·출력·인증을 대조해 proof-scope 공백인지 확인한다.
새 범용 IR/실행기나 전체 증명기를 만들지는 않는다. 단순 parser 미지원,
단일 solver timeout, 제한된 hole 문법을 능력 격차로 세지 않는다. 인증된 무료
표현과 동일 권한의 강한 Native 대비 잔여 비용 여유가 없으면 새 성능 실험이나
학습을 등록하지 않는다.

## 실제 변경·테스트·보존

- 기존 independent fold interpreter, typed IR 및 저장된 인증을 재사용하는
  `experiments/recursive_state_evidence_triage.py` 추가. 공개용 파생 결과만 저장한다.
- `tests/test_recursive_state_evidence_triage.py`: collision 범위, 잘못된 goal/source/
  proposal hash, UNKNOWN/누락 증명, 단순 accepted flag를 거절하는 검사 추가.
- 실제 실행: triage/source-bound/library 관련 **47 passed, 0 failed, 3.29초**.
  테스트용 verifier 호출은 회귀 검사이며 신규 과학 코호트나 모델 실행이 아니다.
- Gemma revision `3e22461f65e89153144f8adb70e3b8c2cc9845a7`, native BF16,
  frozen checkpoint 조건 유지. 기존 core SHA-256
  `8c90b2ff6671aacb168f7c6c5eb713522584a238746b7383ce1c0cc3d35ea33e` 불변.
- GPU/모델/유료 호출 0, 신규 Native 코호트 실행 0, Decision 3 접근 0.
  Frontier Gap 미측정, F0 `BLOCKED_SMALL_MODEL_RUNTIME`, 신규 학습 HOLD.
- 모든 이번 산출물은 `research/development/recursive-state-triage-2026-10-10/`.
  `analysis_contract.json`을 먼저 저장하고 `first_result.json`을 최초 생성했다.
  실행기 재구현, 원본 증거 수정, GitHub 업로드를 하지 않았다.
