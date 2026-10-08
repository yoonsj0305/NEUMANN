# ReaComp 재사용 — 코드 연결과 첫 실제 검증

2026-10-06. 사용자 승인: 재사용 가능한 선행연구는 가져다 쓰고 작업을 이어간다.
상위 목표는 [Frozen North Star](frozen_north_star.md), 후보 선정 기준은
[candidate compression](candidate_compression_2026-10-06.md)다.

## 가져온 것

공식 [cmu-llab/ReaComp](https://github.com/cmu-llab/ReaComp)의 revision
`2b24f50b9e55cfb6bc6fd40510c35bceaf0eda06`을 `External/ReaComp`에 sparse clone했다.
원본은 MIT, Copyright (c) 2026 LLab at CMU이며 라이선스 사본을 보존했다.
원본 solver 두 개와 PBEBench reward package를 `interop/reacomp/upstream`에
**바이트 그대로** 가져왔다. 파일별 SHA-256은 `interop/reacomp/manifest.json`에
기록했고 매 subprocess 호출 전 검사한다. 모델 weight나 새 합성·훈련은 없다.

두 솔버는 published CC `Thu_Apr_23_807_PM/SOLVER.py`와 published Qwen
`Fri_Apr_24_200_AM/SOLVER.py`다. 생성한 replace cascade는 엄격한 AST 검사와
독립 원문 실행, 원본 reward 검사를 모두 거친다. upstream success/score만으로
채택하지 않는다. arbitrary code eval은 사용하지 않는다. 원본 구현을 다시 만들지
않고 입출력·제한시간·검증·비용 기록을 연결했다.

원본 데이터는 외부 checkout에 유지하며 vendor package에 재배포하지 않았다.
공개 dataset의 입력·출력만 solver에 공급했고 original_programs·문제 ID·withheld
예제는 solver에 전달하지 않았다. 전체 API·agent requirements를 설치하지 않아도
이 두 구성요소는 Python 표준 라이브러리로 로컬 CPU에서 실행된다.

사용 경로:

```python
from neumann1.reacomp_policy import solve_examples

result = solve_examples([["ab", "xb"], ["ac", "xc"]], max_programs=5)
# EXAMPLES_FIT or ABSTAIN; unseen_function_equivalence always NOT_CERTIFIED
```

정책은 Qwen을 먼저 실행하고 제공 예제 검증에 실패할 때만 CC를 호출한다.
모든 실패와 fallback 비용을 기록한다. 새로운 입력의 정답을 확인하려면 별도의
독립 권한이 필요하다. `interop`은 현재 wheel에 포함되지 않아 source checkout에서
실행하며 향후 Kaggle bundle에는 vendor 파일과 라이선스를 명시적으로 포함한다.

## 첫 실제 실행: REUSE_R0_v1

공개 개발 데이터 Lite 1,008개·Hard 1,216개에서 salted IO hash가 작은 8개씩,
총 16개를 결과를 보기 전에 고정했다. 같은 문제를 두 솔버에 각각 한 번 공급했다.
각 원본 record의 앞 80% 예제만 허용했다: Lite 4개 제공/1개 withheld,
Hard 40개 제공/10개 withheld. first preparation의 five-example 가정은 Hard의
50-example schema에서 실행 전에 거부됐다. 준비 단계 수정 후 source/task/registration
hash를 고정했고 실제 solver 호출은 수정된 등록에서만 32회 했다.

공통 외부 wall timeout은 8초, 각 DSL의 max cascade는 Lite 5·Hard 20이다.
이는 원본 CC의 내부 55초 제한보다 짧은 bounded development screen이므로
논문 benchmark 재현이라고 부르지 않는다. timeout을 결과에서 제외하지 않았다.
capability screening floor는 원문 training 검증과 모든 withheld 예제 일치를
동시에 만족하는 ≥12/16으로 실행 전에 등록했다.

| 항목 | CC | Qwen |
|---|---:|---:|
| 제공 예제 검증 통과 | 13/16 | 8/16 |
| 제공 + 미제공 예제 모두 통과 | 4/16 | 3/16 |
| 제한시간 초과 | 2 | 0 |
| call startup·source 검사·transport·검증 포함 합산 시간 | 48.385 s | 28.162 s |
| 등록한 ≥12/16 screening floor | 미달 | 미달 |

두 arm 측정과 기록을 포함한 실제 study wall time은 76.556 s다.
신경 inference 0회, API 0회, GPU 0회다. 원래 솔버의 합성 투자·실패한 합성 시도,
원래 모델 training, study 이전 획득 비용, energy/FLOPs/money는 UNKNOWN이다.
이 결과로 전체 자원 대비 10배 이득을 계산하지 않는다.

실제 paired 결과에서 등록한 Qwen→CC 정책을 **추론 입력의 검증 결과만**으로
replay하면 joint 5/16, fallback 8회다. 파생 비용 57.717 s는 독립적으로 timed deployment를
측정한 값이 아니다. withheld 정답을 보고 solver를 고르는 oracle ensemble은 없다.
원본 report를 더 좋은 결과로 재실행하거나 변경하지 않았다.

## 판단을 바꾼 진단

모델 없는 독립 replay로 32개 receipt와 aggregate를 검증했다.
제공 예제에 fit했지만 withheld에 실패한 14개 arm/task cell, 9개 고유 task에 대해
다음 counterexample certificate를 만들었다.

1. 원본 original_programs와 반환 프로그램이 모두 허용 DSL에 속한다.
2. 두 프로그램 모두 제공된 모든 예제를 정확히 만족한다.
3. 원본 프로그램은 원래 withheld 출력도 만족한다.
4. 반환 프로그램은 특정 withheld 입력에서 다른 출력을 낸다.

따라서 **제공된 예제만으로는 그 task의 목표 동작이 유일하게 정해지지 않는다**.
이는 더 좋은 learned prior가 평균 예측을 개선할 수 없다는 증명이 아니다.
‘예제에 fit했으니 의도된 함수를 복원했다’는 보증이 성립하지 않는다는 직접 증거다.
gold program은 사후 진단 전용이며 실제 solver나 policy에 제공하지 않았다.

결정: 두 solver·reward는 **example-fitting baseline 및 실행 구성요소로 재사용**한다.
본 ≥12/16 일반화 screen을 통과한 capable comparator로 승격하지 않는다.
관측 실패를 이유로 이 연구 계열 전체를 배제하지도 않는다. 해당 sparse-IO 계약에서
프롬프트/모델만 교체하는 sweep은 하지 않는다. 다음 주력 후보의 source는 필요한
의미 정보와 독립 verification authority를 갖춘 문제여야 하며, 기존 compiler/native
solver/reuse baseline이 이미 해결하는 부분은 그 구현을 사용한다.

## 보존한 증거와 검증

workspace `Continuation/REUSE_R0_FIRST`에 registration, private task split,
freeze, 32 first receipts, report, policy replay, ambiguity audit,
registered-source.zip을 보존했다. audit는 원본 dataset hash도 확인한다.
source ZIP SHA-256:
`51c6348de5462111da8c8f1717b2a411f4fa485f7fbcdf2b453adf20a8eabc1a`.

adapter 검사 19개·policy 검사 2개 통과. tests에는 source identity, 두 output 형식,
비 DSL·부분 파싱 차단, 허용 입력만의 subprocess 전달, independent/upstream 이중
검증, timeout 종료와 비용, fallback 권한을 포함한다. 합성 test fixture는 실제 성과가 아니다.

원격 GitHub·Notion·Kaggle에는 이 새 결과를 아직 게시하지 않았다.
기존 P1.13 FAIL 및 원본 자료는 그대로다. 연구 목표의 달성을 주장하지 않는다.

원본 evidence ZIP `NEUMANN_REUSE_R0_FIRST_EVIDENCE.zip` 32,007 bytes,
SHA-256 `8c99a04f92ebc5d75857a823ba3d44a009f3fc069f5d533a612204bea2dc8e92`.
ZIP CRC와 manifest의 모든 member SHA-256을 확인했다. policy API의 별도 synthetic
smoke도 실제 subprocess에서 `EXAMPLES_FIT`으로 완료했고 연구 점수에는 포함하지 않았다.

## 선행연구와의 경계

[ReaComp 논문 method/limitations](https://arxiv.org/html/2605.05485v1)은
reusable symbolic synthesizer와 hybrid fallback을 제시하며 structured DSL 및
verifier 범위에 대한 한계를 밝힌다. 그 solver synthesis를 반복할 필요 없이
공개 산출물을 먼저 활용했다. 이번 partial-example 계약과 원 논문 평가 계약은
다르다. 노이만 성과·새로움으로 저자의 방법이나 이 공개 solver를 재명명하지 않는다.
