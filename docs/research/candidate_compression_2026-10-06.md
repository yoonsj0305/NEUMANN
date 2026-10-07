# NEUMANN — 후보를 먼저 압축하는 연구 결정

후속 사용자 기준: [Structural Intelligence / LPS](structural_intelligence_architecture_2026-10-06.md).
학습된 구조 발견·새 표현/변환 조합 생성·미관측 구조 전이가 핵심이다.
이 문서의 비용 규율은 그 핵심 메커니즘에도 적용되며, 이를 역할 라우터나
고정된 변환 목록으로 대체하는 해석은 허용하지 않는다.
후속 실제 [코드 기준선/캐시 비용 screen](code_gate_c0_2026-10-06.md)은 공개
개발의 한정된 비교이며 이 문서 작성 당시의 관측이나 최종 성공을 소급 변경하지 않는다.

2026-10-06. 사용자 지시: 실패한 모델을 하나씩 교체하는 대신, 목표에 도달할
가능성이 큰 후보를 엄선하고 결정에 필요한 실험을 압축한다.
상위 목표는 [Frozen North Star](frozen_north_star.md) 그대로다.
이 문서는 다음 작업의 우선순위를 바꾸며, 이전 등록·첫 결과를 수정하지 않는다.

## 판단

최근 실행은 목표에 비해 좁았다. 역할 선택의 저렴한 경로를 만드는 데 집중했고,
그 경로가 실제 강한 기준선보다 얼마나 많은 계산을 없애는지는 입증하지 못했다.
기존 [critical path](critical_path_v1062.md)와 [joint gate](q34_joint_gate.md)의
‘판단을 바꾸는 정보량’·‘학습 전 ceiling’ 원칙으로 돌아간다.

| 실제 근거 | 묶어서 내릴 결정 | 근거가 말하지 않는 것 |
|---|---|---|
| P1.11.1 3/12, P1.12 7/12, P1.13 paired 3/12→5/12; P1.13 약 8.1배 parameters·7.6배 GPU allocation | 현재 역할 점수화 경로를 주력으로 승격하지 않는다. 모델 교체를 다음 기본 행동으로 삼지 않는다. | 모든 작은 모델·NLI·검색이 불가능하다는 증거는 아니다. 서로 다른 과제의 3→7→5는 학습 곡선도 아니다. |
| Decision2 Direct/TOOL/NEUMANN 모두 0/12; 72회 action decode 실패 | 능력 있는 공통 기준선 확보가 가장 먼저 해결할 비교 병목이다. | 구조 제거의 효과를 비교할 수 있었던 실험은 아니다. 원래 FAIL은 유지한다. |
| 기존 LP/graph screening과 prior-art 기록 | native presolve·정확 솔버·캐시가 이미 하는 일을 다시 만들어 이득으로 계산하지 않는다. | 다른 열린 문제군까지 불가능하다는 결론은 아니다. |
| 작은 CSP 과제만의 최근 증거 | 진단 자료로 보존한다. 새 개발 후보 선정에 참고해도 검증 결과로 재사용하지 않는다. | frontier 능력·새 문제군·복잡도 증가에서의 우위를 입증하지 않는다. |

현재 최선의 **연구 가설**은 ‘검증 가능한 구조 제거 + 재사용 가능한 실행 절차 +
남은 불확실성에만 학습 연산’이다. 전역 최적 후보임을 증명한 것은 아니다.
세 축은 조합 가능한 메커니즘이며, 세 개의 독립된 아키텍처 실패로 세지 않는다.

## 남길 후보와 가장 값싼 반증

| 우선순위 / 후보 | 큰 차이를 만들 수 있는 이유 | 채택 전에 반드시 깨야 할 의심 | 처음 측정할 것 |
|---|---|---|---|
| A. 원래 문제의 정답을 보존하는 계산 구조 제거 | apparent size가 커져도 retained degrees of freedom이 작으면 실행량의 증가 자체를 바꿀 가능성이 있다. 재사용이 없는 첫 문제에서도 의미가 있다. | 기존 솔버의 presolve가 이미 제거하는 구조인가? 발견·복원·원문 검증이 절감을 먹는가? | 동일 executor에서 native/default baseline, 무료 구조를 받은 진단 경로, 실제 발견 경로의 complete cost. diagnostic oracle가 정답/숨은 구조를 실제 추론에 제공하면 탈락. |
| B. 문제군의 실행 절차를 합성해 재사용 | 긴 reasoning을 매 사례마다 재생하지 않고 획득 비용을 여러 새 사례에 분산할 수 있다. | 투자 회수가 필요한 반복량이 현실적인가? 캐시 가능한 Direct/TOOL도 같은 이득을 내는가? 새 구조가 오면 매번 재합성하는가? | cold N=1과 사전 고정한 N=16,64에서 양쪽 합성·실패·저장·바인딩·검증 비용. 같은 답 복사와 새 입력에 대한 알고리즘 재사용을 구분. |
| C. A/B가 남긴 불확실성만 처리하는 learned residual | 이미 제거한 부분에 토큰/forward를 다시 쓰지 않을 수 있다. | 표현에 필요한 정보가 빠졌는가? escalation·fallback이 자원 예산을 넘는가? | 정보 보존 ceiling, discovery 허용 예산, 원문 verifier 통과율. A/B headroom과 competent baseline 이전에는 새 학습 예산을 배정하지 않는다. |

순서는 모델 A→B→C를 하나씩 실행하는 순서가 아니다. **같은 문제·검증기·비용
계약에서 후보를 함께 걸러낼 공통 측정**을 먼저 한다. A 단독, B 단독, A+B의
차이가 필요하면 그때 하나의 등록 안에서 ablation으로 비교한다. C는 그 결과가
남긴 구체적인 병목에만 붙인다. 모델 종류/크기는 그 병목의 능력·예산에 따라 고른다.

계속 보류할 후보: 역할 점수화의 모델명/프롬프트 교체, 검증 없이 쓰는 의미 압축,
강한 native baseline 없는 LP/graph 재시도, 무조건적인 큰 모델·훈련·대량 benchmark.
이 보류는 해당 실패를 재정의하거나 전체 방법 계열의 불가능성을 주장하지 않는다.

## ‘가능한 최대 이득’을 먼저 계산

첫 탐색용 목표를 **동일 능력에서 단일 사전 지정 자원 축 10배**로 둔다.
이것은 새 screening 목표이며 기존 실험의 PASS 기준이나 최종 North Star의
수치 정의를 바꾸지 않는다. 실제 새 평가의 자원 축·능력 문턱·범위는 실행 전에
별도로 등록한다. 에너지·돈·FLOPs를 측정하지 않으면 UNKNOWN으로 남긴다.

동일 workload에서 한 가지 합산 가능한 단위만 사용한다. latency와 VRAM을
더하지 않는다. 병렬화가 포함되면 elapsed time와 accelerator-seconds를 별도로
보고하고, 투자는 같은 축의 독립 cost envelope에서 계산한다.

```
B(N) = min_qualified_baselines(investment_B / N + cost_B_per_item)
F(N) = investment_candidate / N
       + parse + reduce + execute + reconstruct + verify + transport
       + expected_failed_path_work + fallback_rate * incremental_fallback_cost
discovery_budget(N) = B(N) / target_multiplier - F(N)
```

음수면 **그 비용 하한과 구현 범위에서는** 발견을 공짜로 해도 목표가 안 된다.
하한이 실측한 구현 하나의 시간이라면 다른 구현까지 불가능하다고 말하지 않는다.
양수여도 능력·발견 가능성·새 문제 일반화는 아직 미검증이다. zero budget은
discovery zero가 실제로 가능한지 측정해야 한다. 예컨대 균일한 비용의 baseline에
10배 목표를 둔 경우 fallback 비용만으로 baseline의 10%를 쓰면 다른 모든 비용의
여유는 사라진다. 이를 실제 데이터 없이 ‘fallback 10%면 성공’으로 해석하지 않는다.

baseline에는 동일 능력 문턱을 충족하는 Direct, TOOL, 해당 분야의 정확 native
solver, compiler/cache/reuse가 적용되는 강한 경로를 포함한다. 각 baseline의
사전 투자도 계산한다. 신경 연산을 0으로 만드는 것은 CPU search·검증·투자를
0으로 만드는 것과 다르다. 성공 사례만의 비용·제외한 실패 비용으로 판단하지 않는다.

실행 도구: `python -m neumann1.candidate_budget <envelope.json>`.
모든 후보와 사전 지정 N을 한 번에 screening한다. 입력에는 출처를 가리키는
receipt와 외부에서 확인한 baseline capability qualification이 필요하다.
이 도구 자체는 receipt 내용의 진실이나 capability를 검증하지 않는다.
누락 비용을 0으로 바꾸지 않고, `NEEDS_QUALIFIED_BASELINE` / `NEEDS_COST_FLOORS`를
돌려준다. 양의 예산도 `HEADROOM_ONLY`이며 채택 판정이 아니다.

현재 입력: `../../../../Continuation/CANDIDATE_SELECTION_2026-10-06/envelope.json`.
현재 세 후보는 모두 competent comparator가 없어 측정 대기다. 현재까지의
3/12·5/12 모델을 qualified strong baseline으로 둬서 가짜 배수를 만들지 않는다.
10배 수치는 새 실제 이득의 관측값이 아니다.

## 다음 실험이 바꿔야 할 단 하나의 결정

**‘공통 기준선이 실제로 풀 수 있는 새 과제에서, A 또는 B가 10배 예산을
남길 정도로 일을 없앨 수 있는가?’** 먼저 이 질문에 답한다.

1. 기존 seen role tasks와 sealed Decision3를 건드리지 않고, 공개 입력으로
   풀 수 있는 독립 개발 사례의 출처·검증 권한·capability floor를 먼저 고정한다.
   문제 이름이 아니라 실제 중복/불필요 자유도와 원문 검증 가능성을 선정 근거로
   기록한다. 대규모 benchmark를 새로 만드는 일을 선행시키지 않는다.
2. capable Direct/TOOL와 적용 가능한 native/compiled 기준선의 공통 측정을
   확보한다. control 출력 실패와 실제 문제 해결 실패를 따로 계수하되 모든 실패는
   원 판정과 비용에 남긴다. 능력 기준 미달이면 속도 배수를 계산하지 않는다.
3. A/B의 정보·표현 ceiling과 discovery-free diagnostic cost를 같은 측정에서
   구한다. diagnostic 성능은 deployable 성능으로 보고하지 않는다. 기준선 자체가
   싸거나 검증 하한이 큰 경우 그 task/implementation을 제외한다.
4. 남은 후보에만 oracle-free discovery를 구현한다. full cost, capability,
   discovery budget 중 어떤 것이 깨지면 후보를 폐기할지 사전 등록한다.
   같은 실패 원인에 모델명 교체를 다음 행동으로 자동 배정하지 않는다.
5. fresh holdout·새 구조/문제군·증가하는 복잡도에서 실제 advantage가 유지되는지
   확인한 뒤에만 범주 변화/Frontier Gap 평가로 올린다. Development ceiling은
   최종 목표 달성의 증거가 아니다.

다음 GPU 예산은 역할 모델의 네 번째 교체보다 이 **공통 비교 병목**에 우선 배정한다.
현재 결정은 방향·예산 정책의 수정이다. 아직 새 후보 실행이나 돌파 성과는 없다.

## 1차 출처로 확인한 인접 연구

현재 문헌 screening은 세 논문의 초록과 ReaComp의 method/limitations를 확인한
범위이며 체계적인 전체 문헌 검토는 아니다. 코드·데이터·weights는 가져오지 않았다.

- [ReaComp, arXiv:2605.05485v1](https://arxiv.org/html/2605.05485v1):
  reasoning traces로 constrained DSL의 reusable symbolic synthesizer를 만드는
  접근이다. B의 강한 인접 기준선 후보다. 보고된 zero LLM inference는 전체 자원
  0이 아니며, domain/coverage·합성 비용·baseline 범위를 확인해야 한다.
- [Think-and-Execute, arXiv:2404.02575](https://arxiv.org/abs/2404.02575):
  shared task logic를 pseudocode로 만들고 사례에 맞춰 모델이 실행을 모사한다.
  실행 절차 재사용 자체를 노이만의 새 발명으로 주장하지 않는다.
- [From Reasoning Traces to Reusable Modules, arXiv:2606.18089v2](https://arxiv.org/abs/2606.18089):
  SFT/RL과 compositional module 획득을 다룬다. C의 장기 참고이며 지금 새 학습을
  시작할 자원·능력 근거로 쓰지 않는다.

선행연구는 후보 선택의 근거와 비교 의무를 제공한다. 노이만에서 재현된 결과나
검증 가능한 범용 자원 우위를 대신하지 않는다.
