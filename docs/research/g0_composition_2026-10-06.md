# G0_COMPOSITION_V1 — 실제 실행과 다음 메커니즘

2026-10-06. **COMPLETE / NO_HEADROOM_ADMISSION_FOR_THIS_REGISTERED_SCOPE**.
기존 G0 v1과 별도로 사전 등록하고 실행했다. 기존 판정·North Star·Q1–Q7은 유지한다.

## 결정

18개 문제, 6개 경로, 2개 실행 backend, 3회 독립 반복의 **648개 관측 모두 원래 목표 검증 통과**.
무료로 제공한 정확한 합성 표현과 등록한 가장 빠른 정확 비교군의 비용을 비교했다.

| 조건 | 문제별 비율의 기하평균 | 최대 차수 6개 중 10배 이상 | 등록 판정 |
|---|---:|---:|---|
| 최초 query: 발견·검증·컴파일·입력 검사·실행·정답 검사 | 1.796427배 | 0/6 | FAIL |
| 동일 절차를 서로 다른 입력 batch에 실제 64회 사용 | 5.803725배 | 2/6 | FAIL |

실행 전에 두 조건 각각 기하평균 ≥10배 및 최대 차수 ≥5/6에서 10배를 동결했다.
전체 CPU 연구 실행은 148.803046초. G1 학습 진입은 없다.
세 motif는 **한 개의 정확 정수 다항식 프로그램 영역**이다. 두 독립 영역을 확보했다는
주장을 하지 않으며, 이 영역이 통과했어도 그것만으로 G1 진입할 수 없는 계약이다.

## 실제 구현

`neumann1/representation_program.py`는 관계형 DAG 표현을 받는다. 입력, 정수 상수,
덧셈, 곱셈, 순서 있는 출력만 허용한다. IEEE float, 임의 코드, 숨겨진 Oracle 필드,
목표나 입력 순서 변경은 거부한다. 원래 목표와 후보의 정확 정수 다항식 항등식을 검사한다.
검증 예산 초과는 UNKNOWN/거부이며 표본 정답으로 동치를 인정하지 않는다.

검증된 DAG를 Python 실행 절차로 컴파일한다. 모든 경로에 죽은 코드 제거, 동일 부분식
공유, 교환 가능한 항의 hash-consing, 0/1 항등식을 동일하게 제공했다. Python scalar와
NumPy `dtype=object` 배열 실행 모두 **무한 정밀도 정수** 의미를 유지한다.
연산 호출 수는 정수 덧셈·곱셈 수이며 FLOPs가 아니다.

비교 경로는 DIRECT, SymPy CSE, FACTOR+CSE, FACTOR_TERMS+CSE, HORNER+CSE,
무료로 제공한 정확한 합성 표현 FREE_COMPOSED였다. SymPy 1.14.0의 기존
[인수분해](https://docs.sympy.org/latest/tutorials/intro-tutorial/simplification.html),
[공통 부분식 제거](https://docs.sympy.org/latest/modules/rewriting.html),
[다항식 연산](https://docs.sympy.org/latest/modules/polys/reference.html)을 재사용했다.
egglog 14.0.0 기반 symbolic adapter는 별도 기존 기반으로 유지하며 이번 648개 경로에는
포함하지 않았다. 학습된 모델·관점 정책은 이번 비교에 없다.

문제는 네 변수, 차수 4/6/8, 각 두 replica이며 다음 세 motif를 포함한다.

- FACTORED: 완전히 전개한 다항식과 실제 인수들의 곱.
- PATCHED: 그 다항식에 추가 항을 넣었다. 기존 인수분해만 적용하면 원래 목표가 달라진다.
- CANCELLED: 서로 상쇄되는 추가 계산이 들어 있다.

native 경로는 public 원래 프로그램만 받고 factor 구성·seed·motif·정답을 받지 않는다.
FREE_COMPOSED만 오프라인 Oracle 프로그램을 받는다. 변환 비용이 무료인 이 경로도
원래 목표 검증, 컴파일, 입력 검사, 실제 실행, 결과 검사를 지불한다.
공통 compiler 수준의 최적화를 DIRECT에도 제공하여 원문 AST interpreter를 약한 기준선으로
삼지 않았다. 최초 query에서는 DIRECT가 18/18에서 가장 빠른 native 경로였고,
64회 사용에서도 DIRECT가 18/18이었다. 이는 **등록한 경로·backend 안의 비교**다.
최적 native code/JIT나 모든 기존 알고리즘을 포괄하는 세계 최강 기준선 주장은 아니다.

## 비용 계약과 한계

각 trial은 새 후보 생성·검증·컴파일을 수행한다. SymPy 전역 cache는 매번 비운다.
scored 문제로 warmup하지 않는다. 경로 순서는 성능과 무관한 seed로 섞었다.
64회 사용은 64개의 서로 다른 64-row batch를 실제 실행한 값이다. 절차를 다시 쓰는
권한은 모든 경로에 동일하며 답 cache는 사용하지 않았다.

CPU는 Intel Core i5-10400F, Windows Python 3.12.14이다. worker별 wall time과
문제 생성·저장 투자, 참조 정답 생성 투자를 별도로 원본에 남겼다. 참조 생성·library import·
worker 시작·무료 Oracle 구성은 primary warm-library 비율에 포함하지 않았다.
따라서 이 결과는 **낙관적인 G0 후보 선별**이며 배포 전체 비용, 학습 상각 비용,
에너지, 경제적 비용, 프런티어 효율 격차를 입증하지 않는다. upstream CAS 개발 투자도
UNKNOWN이다. 무료로 준 프로그램이 전역 최소 비용 표현이라는 증명은 없다.

## 독립 재검사

`representation_headroom_replay.py`는 최초 manifest의 38개 파일, 외부 receipt,
동결 source/dependency identities를 검사했다. 일반 원본 IR interpreter로 73,728개의
원래 입력 행을 다시 계산했으며, 92개의 서로 다른 case/candidate 프로그램을 두 backend와
모든 입력에서 재검사했다. 648개 accepted 관측과 등록 판정을 재구성했다. **PASS**.
참조 다항식 생성과 generated compiler를 독립 interpreter에 사용하지 않았다.

SymPy/mpmath 원본 wheel·license도 보존했다. 설치된 package 파일 1,561개/87개가
wheel의 실제 byte와 일치했다. 기존 G0 v1의 계약·manifest·report·replay 외부 해시도
계속 일치했다. 최초 자료는 수정하지 않았다.

18개 문제 전부 D/O opened-development로 별도 asset registry에 등록했다.
학습 활성화·fresh 평가 활성화는 모두 false이고 fresh eligible=0이다. Oracle은 명시한
오프라인 upper-bound 경로만 허용한다. 봉인된 기존 Decision3는 열지 않았다.

## 관측한 병목과 이번에 구현한 다음 인터페이스

무료 표현의 최초 비용에서 원문 다항식 동치 검증 비중은 문제별 중앙값 **77.4084%**,
컴파일 비중은 **17.6321%**다. 해당 구현의 관측이며 필연적인 비용 하한은 아니다.
원래 score에서 이 비용을 빼거나 FAIL을 재판정하지 않는다.

이 관측에 따라 `neumann1/representation_rewrite_certificate.py`를 **첫 결과 후 별도**로
구현했다. 앞으로의 정책이 표현과 함께 항등식 변환 증명을 생성할 수 있는 인터페이스다.
정수 ring의 알려진 인수 묶기·분배·교환·결합·0/1 규칙을 최대 32단계로 조합한다.
각 단계의 전제를 원문 DAG에서 확인하고, 원래의 입력과 순서 있는 목표를 보존하며,
최종 후보가 검증된 프로그램과 정확히 일치할 때만 인정한다. 숨은 답·실행 코드·
맞지 않는 유추·float 의미·임의 목표 변경을 거부한다.

합성 증명, 공통 인수의 모든 위치, 거짓 전제, 위조된 최종 출력, 큰 정수, 여러 출력의
검사 11개가 통과했다. 실행 기반·CAS·independent replay fixture와 기존 egglog까지
총 29개 코드 검사가 통과했다.

**이 증명 인터페이스는 이번 score에 사용하지 않았다.** 알려진 rewrite calculus 기반이며
학습된 NEUMANN이나 새로운 계산 원리의 발명으로 부르지 않는다. 18개 전개 다항식의
전체 인수분해를 이 32단계 인터페이스로 처리했다는 증거도 없다. 비용 절감은 아직 측정하지
않았다. 다음 headroom 계약에서는 같은 증명·compiler·재사용 권한을 기호 탐색과 고정
선택 비교군에도 제공해야 한다. 모델이 기존에 없는 유효한 조합을 생성하는 추가 가치와
독립 영역의 충분한 headroom이 있어야 G1을 설계할 수 있다.

## 원본 위치

- 계약·source 복사·외부 receipt: `Continuation/G0_COMPOSITION_PREPARATION`
- 첫 문제·후보·648개 실측·manifest: `Continuation/G0_COMPOSITION_FIRST`
- 독립 replay·비용 분해: `Continuation/G0_COMPOSITION_AUDIT`
- 실행: `experiments/representation_headroom.py`
- GitHub push, Notion 게시 및 GPU 학습은 이번 로컬 CPU 작업 범위에 포함하지 않았다.
