# Guarded Perspective — Directive v1.1 결과

**ENGINEERING PASS. 비용 판정은 기존 공개 fixture 범위의 NO MEANINGFUL
HEADROOM이다. 학습된 생성기·전이·프런티어급 능력·압도적인 총비용 우위는 미입증이다.**
이 문서는 사용자가 제공한 v1.0/v1.1 명령서를 따른 작업 결과이며 Notion의 새
업데이트나 새로운 G0 통과 기록이 아니다.

## A. Repository State

작업 시작 시 Git fetch와 GitHub API로 main
`55178a211962caf5ce677deb37edd30bfb4fdccc`, PR #174
`a0119180e743f5115b21847fdb6ac6741f97bbe2`, PR #175
`c404f66c0ec5bf7735f23e1e98e3c639b76cb87c`를 확인했다. #174 OPEN,
#175 DRAFT/OPEN이며 둘 다 미병합이다. #174가 #175의 조상인 사실을 보존했다.
`c404f66`의 일곱 workflow는 모두 SUCCESS였다. 이번 후속 변경은
`research/neumann1-structural-evidence-2026-10-07`에 기록한다. 최종 커밋과 그
커밋의 CI는 [PR #175](https://github.com/yoonsj0305/NEUMANN/pull/175) 및 별도
publication receipt로 확인하며 이전 커밋의 CI와 혼동하지 않는다.

변경 기능은 `guarded_perspective.py`, `guarded_symbolic_baseline.py`, 기존
`perspective.py`의 별도 Guarded 인증 경로다. `guarded_fixture_probe.py`, 테스트,
사전 등록·최초 관측·독립 감사·이 문서와 append-only 결정 기록을 추가했다.
저장소 `AGENTS.md`에 두 명령서의 핵심 운영 기준을 지속 기록했다.

기존 `inductive_perspective.py`, `inductive_symbolic_baseline.py`,
`representation_program.py`, `inductive_fixture_cases.py`는 바이트 단위로
변경하지 않았다. 이 파일 전체의 해시가 과거 실행에 고정되어 있으므로 별도
확장 모듈이 기존 API를 재사용한다. Universal 의미와 최초 결과를 유지한
기능 확장이며 새 IR·새 범용 증명기를 작성하지 않았다.

## B. Scientific Hypothesis

초기 상태에서만 유효한 충분 표현은 전역 동등성에 실패할 수 있지만, 초기
조건과 귀납적 불변량에 의해 안전하게 승인될 수 있다. 반증 조건은 잘못된
초기값·전이·목표·증명 승수가 승인되거나, 원래 목표와 출력이 달라지거나,
UNKNOWN/변조된 제안이 실행되는 것이다. 기존 Universal 회귀도 실패다.

비용 질문은 이 engineering fixture에서 무료 유효 표현이 강한 공개 기호
방식에 큰 여유를 주는지다. 유효성 성공은 경제성 성공이 아니다.

## C. Implementation

재사용: 기존 정확 정수 DAG, schema 검사, substitution, polynomial normalizer,
DCE/CSE compiler, 다섯 Universal 조건, 상태 dependency closure, SymPy 불변량
nullspace 발견과 polynomial interpolation, 공통 Perspective 계약.

새 기능은 단일 다항식 불변량의 일곱 조건과 엄격한 proof multiplier interface,
문제·초기 조건·표현 해시 결합, 검증 후 immutable snapshot 실행기다. 인증서
메타데이터는 설명일 뿐이며 `accepted=true`로 실행 권한을 만들 수 없다.
인증 후 caller payload를 변경하면 변경된 제안의 재인증은 실패한다. 이미
준비된 실행기는 변경 전 인증된 snapshot만 실행하고, 인증서 조회는 복사본이다.

공통 계약의 `exact_integer_recurrence_guarded` 경로는 기존 Universal 경로와
구분된 보존 범위를 갖는다. 재사용 시 증명을 다시 풀지 않지만 최초 준비에서
직접 검사하며 미검증은 FALLBACK이다. 유효한 경우에도 ENGINEERING_ONLY다.

기호 연결은 기존 발견기가 생성한 `P`를 `h=P(s,p)-P(I(p),p)`로 결합하고,
계수가 ±1인 선형 상태 변수 하나를 제거한다. 축약 문제에 기존 Native 생성기를
사용한 뒤 정확한 정수 다항식 나눗셈으로 승수를 만들고 별도 Guarded checker에
제출한다. 한 후보 불변량, 최대 16번의 후보 시도와 기존 feature/degree budget을
사용한다. 표현할 수 없거나 추가 축약·증명이 없으면 abstain/NOT_VERIFIED다.
기존 발견기의 `goal_sufficiency_established=False`는 변경하지 않았다.
연결 후 정확 증명이 통과한 결과만 goal sufficiency를 주장한다.

## D. Proof

기존 3개 상태 `(x,y,t)`, 초기 `(a,b,c)`, 목표 `y` fixture에서
`h=y-x²-b+a²`, `z=x`, `z'=z+k`, `R=a+kn`, `D=z²+b-a²`를 사용했다.
`q=1`, `r=0`, `v=1`이다. 동일한 1차원 제안은 Universal 목표 충분성에서
거절되고 Guarded 인증에서는 승인된다.

1. `h(I,p)=0`
2. `h(F,p)=q h`
3. `Φ(I,p)=Z0`
4. `Φ(F,p)-T(Φ,p)=r h`
5. `G-D(Φ,p)=v h`
6. `R(p,0)=Z0`
7. `R(p,n+1)=T(R(p,n),p)`

이 항등식과 귀납으로 **초기 상태에서 출발하는** 모든 수학적 정수 매개변수와
비음수 정수 반복 횟수의 원래 순서 있는 목표 출력을 보존한다. 임의 상태에 대한
동등성, 조건 분기·효과·부동소수점·machine overflow는 인증 범위가 아니다.
하나의 비영 다항식 guard와 기존 polynomial IR로 제한한다. 승수 차원, 문제와
초기 조건 해시, checked identity 해시, 목표 출력 순서, 입력·반복 영역을 기록한다.
정규화 작업 예산은 각 검증 프로그램에 적용하며 고정된 일곱 조건을 모두 검사한다.

신뢰 가정은 Python exact integers, 기존 DAG schema/substitution/compiler,
새 조건 구성과 polynomial normalizer 및 귀납 논리다. 완전한 theorem-prover
proof object는 아니다. 별도 DAG interpreter와 SymPy가 일곱 조건을 **자체적으로
재구성·정규화**했고 수치 replay도 수행했다. 임의 Python introspection을 막는
OS 보안 경계는 아니다. 원래 제안과 인증·컴파일 결과를 교환하는 API 경계다.

## E. Tests

새 테스트 **36개**, 관련 로컬 테스트 **152개 PASS**. 기존 Universal, 정수 IR,
rewrite certificate, recursive summary/DAG, data rights와 candidate budget 포함.

- Positive: 동일 제안 Universal 거절/Guarded 승인, 3→1 상태, 324개 작은 원래
  전이 replay와 `n=10^100`/큰 정수 출력, 증명 한 번으로 새 요청 처리.
- 일반 계약: `q=2`, 비영 `r=1`, 복수 목표와 승수 벡터도 승인·독립 확인;
  목표 순서를 바꾸면 거절한다.
- Negative: 초기값, 원래 전이, 목표, 불변량, q/r/v, latent 초기값,
  closed base/induction을 변경하면 정확한 해당 조건에서 거절한다.
- Mutation/UNKNOWN: 문제·초기·표현 해시 불일치, stale payload, forged accepted
  label, 차원 불일치, 영 guard, term/product budget 초과는 실행을 차단한다.
- 원래 초기 조건에 결합한 자동 기호 생성 및 반례/무관 목표/budget abstain 확인.

독립 감사는 저장된 Guarded 인증서 **18개/126개 항등식**, cold 출력 **585개**,
64개 요청 중 원래 loop로 검증 가능한 **32개**를 확인했다. 별도로 43건의 과거
문서·등록 source pin·로컬 원본 archive 해시와 North Star가 일치했다. 과거
누락 archive와 봉인 자료 등의 기존 D0 제외 범위는 그대로다.

## F. Cost

첫 측정 전에 [계약](../experiments/guarded_fixture_probe.preregister.json)을
동결했다. 계약 파일 SHA-256:
`8292eccc82b0958fe4de2d9f35f367e8769485e3d399f00d0535140ae08cc0ff`.
기존 열린 fixture 하나, 세 경로, cold 1/64 요청 각각 3회, 별도 warm worker 3회에서
7개 batch 측정이다. route 순서를 회전했고 27개 worker 모두 VERIFIED다.
전체 worker wall 합계 **55.3972초**이며 과학적 독립 문제 27개가 아니다.

같은 compiler, resident process, 인증서 재사용, 목표 program 합성, Horner/CSE를
세 경로 모두 사용한다. answer cache는 없다. 강한 Native는 자체적으로 원래
문제를 polynomial acceleration하므로 `n`개의 원래 전이를 동일하게 제거한다.
새 표현의 latent 상태는 1개, Native는 2개지만, 합성 후 **27개 worker의 실행
코드가 전부 동일**하다. 모두 요청당 compiled add 2개/mul 6개다. 이 횟수는
arbitrary-precision 작업량이나 FLOPs·에너지의 측정값이 아니다.

| 측정 | Native | Guarded 기호 생성 | 무료 Guarded |
|---|---:|---:|---:|
| cold64 발견·후보 검사 중앙값 | 19.538 ms | 22.485 ms | 0.0011 ms 접근 비용 |
| cold64 최종 인증·컴파일·특수화 중앙값 | 8.278 ms | 9.180 ms | 10.898 ms |
| 준비된 실행/요청 중앙값 | 0.836 μs | 0.839 μs | 0.847 μs |

불변량/닫힌 표현 발견 내부의 후보 증명 비용은 discovery에 들어 있다. 최종
실행 권한 검사·컴파일은 별도 단계다. fixture 구조화는 cold worker에서 약
0.40초이며 패키지 import와 프로세스 초기화는 parent 완전 operational wall에
포함된다. warm 시간에는 신규 입력 처리·정확 정수 실행을 포함하고 사전 준비를
포함하지 않는다. warm 측정용 worker는 cold 서비스 비용과 분리했다.

| 같은 입력·반복으로 짝지은 Native/무료 표현 기하평균 | 비율 |
|---|---:|
| cold 1회 요청의 완전 operational wall | 0.96735× |
| cold 64회 요청의 완전 operational wall | 1.02222× |
| 준비된 실행 | 0.98839× |

10× screening 기준을 세 범위 모두 충족하지 못했다. 초미세 warm 차이는 실질적
우위로 해석하지 않는다. 관측 범위는 이 fixture와 이 Windows/Python 환경이다.
Free 표현은 무료 발견의 낙관적 진단이지 학습된 NEUMANN 성능이 아니다.

**총 연구·학습 투자까지 포함한 complete cost는 UNKNOWN**이다. 기존 R&D와
환경 구축, FLOPs, 에너지, peak memory, 금전 비용은 실측하지 않았으며 0으로
메우지 않았다. cold operational wall에는 process/import/read/discovery/check/
compile/실행·복원/출력·종료/독립 확인이 포함된다. G2 전체 자원·투자 계약과 다르다.
실패 worker가 있으면 INCOMPLETE로 남기도록 등록했으며 이번 27개는 모두 완료됐다.

## G. Conclusion

**ENGINEERING PASS**: 초기 도달 상태의 충분 표현을 기존보다 넓게 승인하는
정확 검증 계약과 기존 불변량 발견→초기 결합→목표 충분성 연결이 동작한다.

**NO MEANINGFUL HEADROOM**: 이미 열린 coordinate fixture의 동등 최적화 권한을
갖춘 강한 기호 비교에서 10× operational 여유가 없다. 새로운 영역의 가능성,
전역 지능 가설, 모든 유효 표현의 최적 상한을 기각한 결과는 아니다.
전체 투자 경제성은 NOT VERIFIED이며 학습된 구조 발견은 실행하지 않았다.

## H. Next Decision

**HOLD**: 이 좌표·다항식 fixture 계열의 학습된 생성기에 투자하지 않는다.
검증기만 더 빨리 만드는 것으로 10×를 얻겠다는 후속 실험도 중단한다.
Guarded 기능과 반례는 재사용 가능한 Core/Fixture로 보존한다.

기존 G0 A(Storm 기반 goal-dependent probabilistic sufficient state),
B(D4/CPOG/Ganak 기반 certified Boolean counting circuit)는 그대로 유지한다.
실제 원래 목표를 보존하는 free 표현과 강한 같은 환경 baseline의 큰 비용
여유가 먼저 필요하다. B의 toolchain 준비가 과도하면 환경 상태를 기록하고
중단한다. 새 큰 IR·범용 prover·학습 모델·GPU pipeline을 만들지 않았다.
G1/G2 미진입, Decision 3 봉인 미접근, North Star/Q1–Q7 및 과거 판정 불변이다.

증거: [최초 비용 관측](guarded_fixture_probe_first_2026-10-08.json),
[독립 검증·원본 보존 감사](guarded_engineering_audit_2026-10-08.json),
`tests/test_guarded_perspective.py`. 원본 결과를 재실행으로 교체하지 않았다.
