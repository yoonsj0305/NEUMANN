# G0 후보 압축 — 2026-10-08

사용자 R&D Directive v1.0에 따른 의사결정 준비다. **성능 측정 사전 등록이 아니며
신규 G0/G1 실행을 승인하지 않는다.** 핵심 가설 H1은 Learned Goal-Preserving
Perspective Search 한 개다. 아래 두 영역은 같은 가설의 후보이며 무제한 대안을
추가하지 않는다. B를 준비 우선순위로 두고 A는 대기한다.

## 후보 A — 목표 조건부 확률 전이계의 충분 상태

원래 공개 입력은 rational 확률 전이/초기 상태/goal predicate를 가진 프로그램이다.
목표는 특정 reachability 또는 기대 reward이며 모든 transition을 보존하는 것보다
해당 목표에 충분한 새로운 상태 표현을 생성하는 것이 가설이다. 수치 오차를 줄이는
방향으로 목표 정확성을 완화하지 않는다. 필요한 경우 exact rational 기준을 사용한다.

이전 graph true-twin에서는 인접 관계를, integer recurrence에서는 unconditional
다항식 귀납을 검사했다. 여기서는 확률적 분기와 목표별 미래 결과의 충분성이 필요하다.
기존 list summary를 다시 학습하거나 state 이름만 바꾼 후보로 취급하지 않는다.

그러나 상태 압축은 이미 [Storm](https://github.com/stormchecker/storm)과 그
[실행 문서](https://www.stormchecker.org/documentation/usage/running-storm.html)의
property-dependent model construction 및 exact analysis가 다루는 영역이다.
공식 [changelog](https://github.com/stormchecker/storm/blob/master/CHANGELOG.md)는
symbolic model/bisimulation quotient 기능도 기록한다. 모두 강한 B/C의 권리다.
[goal-conditioned bisimulation 연구](https://proceedings.mlr.press/v162/hansen-estruch22a.html)도
존재하므로 목표 조건부 표현 학습 자체의 독창성을 주장할 수 없다.

| 실행 전 답할 질문 | 판단 |
|---|---|
| 검증 가설 | 목표에 충분한 유효 표현으로 강한 symbolic/property-aware native보다 전체 비용을 줄일 수 있는가? |
| 기존 증거로 답할 수 없는 이유 | probabilistic goal semantics와 native model checker의 공정한 원래 문제 결과가 없음 |
| 결과에 따른 변경 | free 표현이 동일 능력에서 10배 여유를 못 주면 이 영역의 학습 중단 |
| 실패 시 중단 | 단순 variable dropping/bisimulation selector 학습; 약한 explicit enumeration만과의 비교 |
| 성공해도 못 하는 주장 | 자동 발견/학습/미관측 전이/범용·프런티어 성공 |

현재 cheapest review 결정: **HOLD**. exact 제공 표현·독립 목표 보존 조건·강한
baseline의 동일 환경 비용이 미확보다. 큰 state count나 알려진 quotient가 있다는
사실은 10배 headroom이 아니다. 전이 모델·goal 조건을 바꿔 이전 유추가 무효가 되는
반례도 필요하다. Python toy checker를 새로 만드는 대신 기존 checker를 재사용한다.

## 후보 B — 인증 가능한 Boolean counting circuit 생성·재사용

원래 공개 입력은 CNF/변수 범위/합리수 literal weights/명시된 counting goal이다.
문제 표현을 deterministic/decomposable circuit으로 바꾸면 반복 weight query에서
동일한 Boolean reasoning을 제거할 수 있다. circuit을 생성·인증·실행하는 비용,
출력 복원·전송·실패·fallback과 투자 회수까지 측정해야 한다. answer cache는 제외한다.

이전 tensor 결과는 배열의 동일 sum-product 목표에 대해 contraction 경로를 선택했다.
여기서는 원래 논리식의 경우 분할·독립성·조건부 분해가 표현이며 그 동치성을 증명해야
한다. 같은 공식 einsum 입력을 다시 골라 path 이름을 바꾸는 실험은 하지 않는다.
Boolean-to-tensor 변환으로 이어지는 문제 계보는 추적해야 하며 동일 원본을 독립
증거라고 세지 않는다. 기존 tensor 결과만으로 이 영역의 10배를 추정하지 않는다.

강한 기존 방법은 이미 이 원리를 구현한다:

* [D4](https://github.com/crillab/d4), [d4v2](https://github.com/SoftVarE-Group/d4v2)는
  CNF를 d-DNNF로 compile한다. native에도 compiler·component cache·회로 재사용을 준다.
* [CPOG](https://github.com/rebryant/cpog)는 representation과 원래 식의 동치성 증명을
  함께 기록하며 verified checker/counter를 제공한다.
  [Certified Knowledge Compilation](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SAT.2023.6)은
  이 연구의 선행 기반이다. 검증기를 다시 만들지 않는다.
* [Ganak](https://github.com/meelgroup/ganak)의 exact rational weighted counting과
  [ADDMC](https://github.com/vardigroup/ADDMC)의 algebraic decision diagram도 검토할
  native 대안이다. 현재 실행하거나 능력/비용 envelope에 포함했다고 주장하지 않는다.

| 실행 전 답할 질문 | 판단 |
|---|---|
| 검증 가설 | 동일 목표의 유효 circuit을 무료 제공해도 최강 exact native/compiler/reuse보다 10배 여유가 있는가? |
| 기존 증거로 답할 수 없는 이유 | 공식 tensor work 모델은 CNF↔circuit 동치 증명과 exact rational 원래 counting goal의 완전 비용이 아님 |
| 결과에 따른 변경 | native가 같은 circuit을 싸게 얻거나 제공 circuit 전체 비용이 유리하지 않으면 learned generator 투자 중단 |
| 실패 시 중단 | known d-DNNF builder를 새 이름으로 포장하거나 circuit ID selector를 학습하는 작업 |
| 성공해도 못 하는 주장 | learned generation, unseen logic motifs, Frontier Gap, 새로운 계산 원리 |

현재 cheapest review 결정: **CONTINUE(기존 구현의 좁은 준비), HOLD(성능·학습)**.
새로 만드는 구성 요소는 표현 생성 정책이어야 한다. 기존 compile/certify/evaluate를
NEUMANN 발명으로 세지 않는다. 제공 circuit의 전역 최적성은 보장하지 않는다.
실행 가능한 baseline과 제공 certificate가 연결되기 전까지 model-size/GPU 선택을 하지 않는다.

## 우선 폐기·보류한 작업

* 반복 P1 모델 교체·현재 20개 알려진 summary 생성기 학습·다시 쓰는 tensor path selector.
* 새 범용 증명기, 거대한 통합 IR, 같은 이미 열린 task의 fresh 재분류.
* 현재 cold 재귀 비교에서 verifier 최적화만으로 10배를 얻으려는 실험:
  원본에서 proof+compile을 전부 없앤 민감도도 약 1.05배다.
* corpus code compression을 실행 work 감소와 동일시하는 library 학습.
  [Stitch 공식 구현](https://github.com/mlb2251/stitch)은 이미 존재하지만 compression
  objective의 성공이 원래 문제의 실행량·완전 비용 개선을 보장하지는 않는다고 판단한다.

## 성능 측정 전에 반드시 동결할 사항

원래 goal/숫자 semantics, 전체 eligible problem lineage와 제외 사유, 최소 두 complexity
범위, native symbolic/cache/specialization portfolio, certificate와 compiler의 동일 권한,
투자 비용·cold 및 실제 다른 요청 reuse의 횟수, 표본 수·반복·geomean·10배 성공 비율,
시간/메모리 예산, 실패·timeout·UNKNOWN과 incomplete의 처리. 이들이 정해지기 전
측정으로 유망한 case만 골라 새 G0 합격 기준을 만들지 않는다.

이번 outcome은 선택/준비 결정이다. 새 G0 PASS/FAIL 결과는 없고 H1-A/B/C는 열린다.
정확한 무료 유효 표현과 강한 비교군의 비용 근거가 연결되지 않으면 G1은 계속 HOLD다.
