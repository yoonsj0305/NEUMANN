# Full Synduce 기준선과 구조 표현 통합

2026-10-07, 사용자 요청의 5시간 연속 작업 중 기록. 작업 한도는
2026-10-07 08:30:46 KST다. 현재까지 학습된 NEUMANN, G0/G1 통과,
압도적 전체 비용 우위, 프런티어 능력을 입증하지 않았다. 최신 완료된
`COMPRESSED_RECURSIVE_COMPLETE_COST_V1`도 약1배 결과다. 별도 비용 문서에
240개 worker, 최초 결과와 독립 감사를 보존했다.

## 강한 원본 비교군

[Synduce 원본](https://github.com/synduce/Synduce)의 MIT 소스를 commit
`b5c1d1611d3fbf5d8cdf9a23fde52c2cbba95a89`에 고정했다. 정확 원본 ZIP,
1,603개 파일, 564개 benchmark 소스, source/license/hash를 보존했다.
Windows에서 사용할 수 없는 과거 파일명의 콜론은 가역적 portable 이름으로
바꿨으며 원본 ZIP은 그대로다. 최초 intake의 경로 오류도 별도로 보존했다.

Kaggle 비공개 CPU 세션에서 원본 구현을 실제 빌드했다. OCaml5.0.0,
opam/dune, Z3와 실제 apt CVC5 1.1.2를 사용했다. 최신 Menhir와의 API
불일치로 첫 빌드가 실패했고, 소스를 수정하지 않고 Menhir20230608에
맞춰 환경을 수리했다. 첫 실패·수리·dependency export와 binary hash를 보존했다.
기록된 설치·빌드 명령은 합계707.26545초이며 연구 노동·전체 R&D 비용은 아니다.

| 별도 동결 실행 | 실제 worker | 도구의 해결 가능 보고 | 해결 불가 보고 | 시간 초과 | 실행 오류 | whole CPU wall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CVC5 FIRST | 87 | 70 | 9 | 6 | 2 | 454.20052초 |
| CVC4 FIRST | 87 | 78 | 9 | 0 | 0 | 205.48751초 |

두 실행 모두 공개24-case suite와 선언한5개 진단을 각3회 수행했다.
독립 문제174개가 아니다. CVC4는 원래 발표 구현이 사용한 별도 backend
비교이며 첫 CVC5 결과를 대체하지 않는다. CVC4 설치11.6524초도 보존했다.
원본 binary·CPU가 같음을 확인했다. 표는 source repr/target/attributes를
포함한 원본 도구의 보고다. JSON 성공만으로 독립적인 보편 증명을 주장하지 않는다.

CVC5에서 timeout이었던 `poly_no_fac`는 CVC4에서 약1.7초, `mss`는
약35–38초에 보고가 나왔다. CVC5의 두 빈 출력 오류는 SIGPIPE(-13)였고
원인 전체를 추정하지 않는다. 한 Solver의 시간 초과를 새 지능의 우위로 세지 않는다.
또한 제공한 MSS 공식은 known library 기준선도 생성하므로36초/cheap formula를
NEUMANN의 비용 배수로 제시하지 않는다.

## 독립 검사 범위

제한된 emitted-program reader가 정수 helper와 CNil/Single/ordered Concat을
수학적 정수 IR로 옮긴다. 원래 fold와9개 공통 충분 조건을 검사하고, 실제
Single이 검증된 Cons(head,E)와 같다는10번째 연결 조건을 추가했다.
잘못된 Single, 뒤집힌 결합, 비선형/임의 호출 등은 차단한다.

| 감사 | 적응한 반환 프로그램 | Z3 독립 조건 | 저장된 SMT 재검사 | 유한 numeric 비교 |
| --- | ---: | ---: | ---: | ---: |
| CVC5 첫 실행 | 13 | 130 | 130 | 4,797 |
| CVC4 첫 실행 | 18 | 180 | 180 | 6,642 |

이 수치는 반복을 포함한다. CVC5는5개 source case, CVC4는MSS를 포함한6개
source case다. 각각 전체87개 원본 관측의 파일·출처·순서·hash는 감사했다.
증명 범위는 **적응한 수학적 fold**다. 원래 OCaml repr/target/attributes,
machine overflow나 전체 benchmark protocol을 독립 재현했다는 뜻이 아니다.

## 입력 이름을 쓰지 않는 강한 재사용 비교군

`recursive_library_baseline.py`는 known ordered monoid를 공공 전이식에서
점검하고 input map·상태 순열·독립 direct product를 생성한다.
`finite_response_baseline.py`는 원래 상태 전이를 제한적으로 탐색해 함수 응답
모노이드와 invariant를 생성한다. 이는 알려진 finite transformation monoid의
재사용이다. 표본 closure는 증명이 아니며, 실제 모든 정수 입력에 대한 공통
보편 검증을 통과해야 한다. 두 비교군 모두 Oracle 이름/후보/답을 읽지 않는다.

별도 동결한 `TYPED_RECURSIVE_PORTFOLIO_INTEGRATION_V1`은 전체564개 원본을
조사해90개 지원 가능한 typed reference projection,27개 exact AST를 만들었다.
모든27개를 두 생성기에 주어54회 시도했다. Known library17개, finite response3개가
인증됐다. finite-response의3개 표본 기반 제안은 실제 입력 반례로 REFUTED,
나머지는 제한된 grammar에서 abstain했다.20/27은 official benchmark 점수가 아니다.
helper projection을 포함할 수 있고 AST hash 차이가 구조적 독립성을 증명하지 않는다.

180개 독립 Z3 조건과7,260개 작은 ordered-tree 비교가 통과했다.
27개 D public과20개 O offline proposal을 분리했고74개 권한 거부를 확인했다.
훈련·fresh 평가·O의 runtime problem API 진입은 허용하지 않는다.
전부 opened development이며 학습·새 지능 발견·비용 우위의 증거로 세지 않는다.

## 다음 비용 검사의 실행 구조

`recursive_dag.py`는 공통 certificate로 압축된 ordered DAG를 실행한다.
strict backward references로 순서·비순환성을 검사하고 목표 root에서 필요한
노드만 계산하며 공유 노드는 한 번만 계산한다. certificate hash와 값/노드
예산도 검사한다. DAG의 각 노드에서 unfolded list의 요약과 같다는 topological
귀납으로 공통 list certificate를 확장한다. 이 실행 권한도 native와 모든 미래 D에 같다.

61개 노드로 길이2^60의 수학적 리스트를 표현·실행하는 검사 등12개 검사가
통과했다. **2^60은 입력의 의미상 길이이며 측정 speedup이 아니다.** 큰 리스트를
실제로 풀어 계산했다는 주장도 아니다. bit complexity·출력 크기는 남는다.

명시적 리스트의 선형 fold는 입력 읽기 자체가 비용 바닥을 형성할 수 있다.
새 표현의 계산 제거를 검토하려면 compressed/shared structure나 반복 질의의
의미를 원래 문제에 결합해야 한다. 다음은20개 인증된 열린 표현을 대상으로
native와 free valid reference에 동일한 DAG compiler·검증·실제 질의 재사용을
주고 전체 operational wall 비용을 등록해 비교하는 것이다. 유효 reference는
전역 최적 Oracle라는 뜻이 아니다. 이후 새 비용 최초 실행을 완료했으며
1회/16회 실제 재사용 기하평균1.00478/1.00237배, 10배 win0/20으로 기준 미달이다.
동일한 compiler·검증·재사용 권리에서 240개 worker와2,040개 출력이 완료됐다.

## 보존 경로와 pins

`Continuation/SYNDuce_FULL_SOURCE_PORTABLE`, `SYNDuce_SOURCE_AUDIT`,
`SYNDuce_FULL_BASELINE_FIRST/AUDIT`, `SYNDuce_CVC4_PREPARATION/FIRST/AUDIT`,
`TYPED_RECURSIVE_PORTFOLIO_PREPARATION/FIRST`에 원본과 결과를 분리했다.

- CVC5 report: `9fcd9c14fd0584c3368410dca69137e7bba51806112a382e5cb58441749c3daa`
- CVC5 manifest: `27cf88f152c61994c852c80c7f478c0c86985539647967875fb3d0bdfa099cf5`
- CVC4 report: `00978661c58c258725a92b88a8572b5ee77688f8da65cc352bc92efa19059af9`
- CVC4 manifest: `36a3e818f099f067fdc8576dd93d3fb92e50558c6b51a9ab34fd94212662c134`
- typed portfolio report: `804b51bc3c09b89087a4384c194b59aeb22d604044a0304d2998551a6c8af097`
- typed portfolio manifest: `855b0ff97e0e45c32801b06644a4ebb1d8c4dbe02b64de66167af3e0afaf2654`

Kaggle 비공개 [CPU notebook](https://www.kaggle.com/code/universe7475/neumann-1-synduce-cpu-baseline/edit)에
실행했고, 로컬 archive의 bytes/hash를 확인했다. 원격 QuickSave output version1은
현재 queued 상태 및 commit 오류가 표시돼 완료를 선언하지 않는다. 컴파일된
Linux binary를 포함한12,678,011-byte 원본 ZIP은 별도로 로컬에 내려받았다.
205개 member 중 기존204개 기록이 byte 일치하고 실제 실행 binary의 hash도
일치한다. 전체 dependency 환경 보존이나 Windows 실행은 아직 아니다.
GitHub push/Notion 수정은 하지 않았다.
North Star/Q1–Q7 OPEN, Decision3 봉인, G2 차단은 그대로다. GPU·새 모델 학습0회.
