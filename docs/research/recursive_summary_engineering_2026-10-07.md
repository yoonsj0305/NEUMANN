# NEUMANN 1 — 조건 분기와 재귀 요약의 생성·검증 기반

2026-10-07. 현재 단계는 **학습된 구조 지능 이전의 검증·실행 기반**이다.
이전 전체 비용 결과는 그대로이며 압도적 비용 우위, G0/G1 통과, 프런티어
능력을 이번 작업으로 선언하지 않는다. 완성도를 임의의 백분율로 제시하지 않는다.

| 단계 | 실제 상태 |
| --- | --- |
| 기존 자료 보존·재사용 D0 | 이용 가능한 범위의 계보·권한·원본 hash·실패 관측 정리 완료. 누락 원본은 제외 |
| 표현 생성·검증·실행 기반 | 정수 다항식 좌표/반복 요약에 이어 조건 분기와 순서 보존 재귀 요약 구현 |
| 압도적 비용 여유 G0 | 기존 후보는 미통과 또는 미완료. 가장 최근 등록 비교 약1배. 이번에는 새로운 비용 평가를 하지 않음 |
| 학습된 관점 생성 G1 | 미진입. 이번에 학습한 모델·새 학습 정책 없음 |
| 독립 프런티어 비교 G2 | 미진입. 기존 Decision3 봉인 유지 |

## 이번에 바꾼 구현 범위

기존 `inductive_perspective.py`의 다항식 항등식 검사는 조건 분기와 min/max를
표현하지 못했다. 해당 동결 코드를 수정하지 않고 `recursive_summary.py`를
추가했다. 입력은 수학적 정수 리스트에 대한 원래 right-fold 초기 상태와 전이식,
제안은 새로운 요약 상태의 초기값·Cons 전이·Concat 결합·원래 출력 decoder·
불변식이다. 정해진 변환 ID를 고르는 형식이 아니라 제한된 언어 안의 식을 생성한다.

사용할 수 있는 표현은 정확 정수 add/sub, min/max, 비교, 논리식, 정수 분기다.
임의 곱·부동소수점·외부 효과·일반 언어 실행을 허용하지 않는다. 최대 상태8개,
식 깊이64, 프로그램당 노드4096 등의 검사 예산이 있다. 큰 정수의 bit 비용이나
전체 지능 계산의 하한을 보장하는 예산이 아니다.

다음 충분 조건을 CVC5의 QF_LIA 반례 검사로 확인한다. I는 제안 불변식, E는
빈 요약, S는 Cons 전이, M은 Concat 결합, D는 decoder, F는 원래 fold 전이다.

1. E가 I를 만족한다.
2. I를 만족한 상태에 S를 적용해도 I를 만족한다.
3. D(E)가 원래 초기 상태와 같다.
4. I(z)일 때 D(S(h,z)) = F(h,D(z)).
5. I를 만족한 두 상태의 M도 I를 만족한다.
6. M(E,z) = z.
7. M(z,E) = z.
8. M(S(h,l),r) = S(h,M(l,r)).
9. M(M(a,b),c) = M(a,M(b,c)).

유효한 상태를 전제로 한 조건들만 검사하며, 불변식의 초기화와 보존도 함께
증명하므로 거짓 불변식으로 조건을 비울 수 없다. 초기·Cons 귀납과 결합 조건에서
모든 유한 정수 리스트의 원래 ordered output 보존을 도출한다. 이는 충분 조건이고
모든 유효 요약을 받아들이는 완전한 검증기는 아니다. UNSAT만 실행 권한을 준다.
SAT는 반례, UNKNOWN/예산 초과는 미검증이다. SMT 엔진을 신뢰하는 방식이며
독립적으로 검증 가능한 proof object를 가진 작은 증명 kernel은 아니다.

인증 뒤 `CertifiedSummary`가 순서를 보존하는 nil/single/concat 트리를 실행한다.
원래 문제와 제안을 복사해 인증하고, 실행 전 hash 결합을 재확인한다. tree 처리도
노드 예산을 적용한다. Python API가 임의 파일 접근이나 내부 객체 변조를 운영체제
수준에서 격리한다는 주장은 하지 않는다. 실제 병렬 실행이나 비용 가속은 구현·
측정하지 않았다. 이 기반은 향후 강한 B/C와 학습된 D에 동일하게 제공해야 한다.

## 기존 연구와 코드 재사용

[Synduce](https://github.com/synduce/Synduce)의 MIT 자료를 commit
`b5c1d1611d3fbf5d8cdf9a23fde52c2cbba95a89`에 고정해 8개 파일을 가져왔다.
합계·최대 prefix 합·최대 suffix 합·최대 연속 부분합의 공개 reference 함수를
사용했다. 원본 파일과 license, URL, hash를 보존한다.

작은 ML parser는 첫 Nil/Cons reference의 정수 전이와 순서 있는 tuple 출력을
추출한다. **이는 원본 전체 OCaml 프로그램/representation 함수/Synduce 프로토콜의
재현이 아니라 수학적 정수 reference의 적응본**이다. 임의 ML 문법·requires 조건·
machine-int overflow를 처리하지 않는다. 원래 benchmark의 공식 점수라고 부르지 않는다.

`recursive_symbolic_baseline.py`는 공개 전이만으로 기존 Houdini 방식의 제한된
불변식 후보를 점검하고, [CVC5 SyGuS](https://cvc5.github.io/docs/latest/api/python/base/solver.html)
로 결합식을 생성한다. 상태 차수는 원래 reference와 같고, 문법은 공개 변수·0·
변수 쌍의 합·max다. 이것은 고정된 요약 상태의 **기호 생성 prototype**이며
full Synduce, 최강 기호 기준선, 학습된 NEUMANN, 새로운 알고리즘의 발명으로
취급하지 않는다. full Synduce의 OCaml/opam/dune 실행 환경은 설치·실행하지 않았다.

CVC5 1.4.1과 독립 감사용 z3-solver 4.15.4.0을 로컬 venv에 설치하고
optional dependency `recursive`로 기록했다. 기존 설치 패키지와 동결 실험
소스의 identity는 유지했다. 원본 소스에 나온 정답이나 발표 실행시간을 새로운
독립 성능 증거로 옮겨 쓰지 않는다.

## 열린 개발 실행 결과

등록 `RECURSIVE_SUMMARY_ENGINEERING_V1`은 비용 gate가 없는 engineering 계약이다.
원본 자료 읽기, sum 합성 preview, 단위 fixture를 먼저 공개·사용했다는 이력도
등록했다. 최초 동결 후 첫 통합 실행 전에 timeout 분기의 오래된 child 결과 참조
문제를 발견했다. 초기 동결은 미실행으로 보존하고 수정 source를 별도로 고정했다.
최초 결과를 대체하거나 시간 예산을 늘린 재실행은 하지 않았다.

실행한 수정 등록 SHA256:
`5186d4345933fd89e194011fd8a5c2c893f3fdc8aa3c8f21cc31b73038fe6c1f`.

| 공개 reference 적응본 | 공개 기호 생성 | 알려진 오프라인 요약 |
| --- | --- | --- |
| 합계 sum | 생성·인증 완료 | 인증 완료 |
| 최대 prefix 합 mps | 생성·인증 완료 | 인증 완료 |
| 최대 suffix 합 mts | 생성·인증 완료 | 인증 완료 |
| 최대 연속 부분합 mss | 등록5초 합성 예산의 결과 UNKNOWN, 실행 권한 없음 | 인증 완료 |

기호 방법이 자체 생성한 요약과 알려진 제공 요약을 분리했다. mss의 미검증을
기호 방법 전체의 실패나 학습 필요성의 증거로 일반화하지 않는다. 알려진 native
라이브러리와 full Synduce에도 같은 절차 재사용 권한을 줄 필요가 있다.

별도 F fixture에서는 출력이 최대 prefix 값 하나인 문제에 prefix와 전체 합의
두 상태를 제안했다. 같은 기존 값0을 가진 왼쪽 리스트 []와 [−5]에 오른쪽 [4]를
붙이면 답은 각각4와0이다. 이 반례는 **prefix 값 하나라는 고정 통계가 결합에
불충분함**을 보여준다. 두 보조 상태를 가진 알려진 요약은 귀납 검사를 통과한다.
임의의 모든 scalar encoding이 불가능하거나 AI가 새 추상화를 학습했다는 뜻은 아니다.

전체 수치 대조는 8,736회다. 4개 공개 적응본과 1개 fixture에 대해 alphabet
{−2,0,3}, 길이0~5의 364개 리스트와 left/right/balanced 트리를 점검했다.
수치 대조 횟수는 독립 문제 수가 아니다. 적격 제안은 8개, 제안별 충분 조건은
9개씩 총72개다. 잘못된 순서·거짓 불변식·잘못된 decoder의 세 제안을 반례로
거절하고 원본 제안/검사 결과를 보존했다.

독립 감사는 다음을 확인했다.

- 원본8개 파일, 최초 결과의26개 manifest 파일, 등록 source/package hash 확인.
- 공통 CVC5 translator를 사용하지 않고 Z3 AST로 구성한72개 조건의 UNSAT 확인.
- 저장한72개 CVC5 SMT 질의를 별도 Z3 parser/solver로 재검사.
- 별도 tree/식 interpreter와 직접 정의한 sum/prefix/suffix/부분합 계산으로8,736개 원래 출력 대조.
- 세 거절 제안의 SAT를 독립 확인하고 mss UNKNOWN을 보존.
- 관련 회귀 검사144개 통과. 테스트·자료가 학습된 일반화나 비용 우위를 인증하지 않음.

모든 자료는 열린 개발 자료다. 공개 적응본4개 D, 보조 상태 fixture1개 F, 제공
요약5개 O를 별도로 등록한다. 기존 D0 authorize/identity 검사와 엄격한 fold
schema를 재사용하며 학습·fresh 평가와 O의 공개 문제 접근을 막는다. fresh 적격0,
신경망 학습 없음, G0/G1 진입 없음, GPU 사용 없음이다.

## 다음 투자를 결정할 병목

핵심 미완성은 **처음 보는 문제에서 비용 이득이 있는 새 요약/관점을 학습된
모델이 생성하는 능력**이다. 오늘의 함수·자료로 그것을 입증했다고 선언하지 않는다.
기존 생성기·라이브러리도 얻는 싼 요약은 강한 비교군에 포함해야 한다.

이제 조건부 요약을 원래 목표에 연결해 검증할 공통 기반이 생겼다. 다음 비용
비교에는 full Synduce 또는 동등한 강한 구현, 알려진 요약의 재사용, 독립적인
문제 계보, 발견·검증·실행·투자의 통일된 자원 계약이 필요하다. prototype의
UNKNOWN만 골라 GPU 학습하거나, 제공된 mss 정답의 싼 실행을 학습된 돌파구로
부르지 않는다. 별도 범용 G1은 비용 여유가 확인된 뒤 한 A/B/C/D+세 제거 실험으로
등록한다. Q1~Q7과 North Star, 모든 이전 최초 결과·봉인 제한은 유지한다.

보존 폴더: `Continuation/RECURSIVE_SUMMARY_SOURCES`, 미실행 초기 PREPARATION,
`RECURSIVE_SUMMARY_PREPARATION_PREFLIGHT_FIXED`, `RECURSIVE_SUMMARY_FIRST`,
`RECURSIVE_SUMMARY_AUDIT`, `RECURSIVE_SUMMARY_FINALIZATION`.
