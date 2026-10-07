# 공개 구조 생성 대조군과 원본 소스 연결

최신 상태: **알려진 구조·유한 상태·기호적 decoder 생성의 합집합으로 이미 열린
27개 수학적 AST를 모두 인증했다. 학습된 NEUMANN이나 압도적 비용 우위의 증거는
아니다.** 전역 North Star와 Q1–Q7은 유지하고, G1/G2에 진입하지 않는다.

## 실제 확보한 증거

| 기록 | 관측 | 범위 |
|---|---:|---|
| 새 기호 decoder 첫 실행 | 인증 25/27, 기권 2/27 | 기존 원본 결과를 수정하지 않은 별도 개발 통합 |
| 앞선 유한 상태 첫 결과 재사용 | 위 기권 2개 인증 | 두 첫 기록의 합집합 27/27; 새 방식 결과는 여전히 25/27 |
| 독립 Z3 검사 | 자체 생성 조건 243 + 저장 CVC5 조건 243 | 27개의 9조건 충분성 검사; SMT를 신뢰하며 proof kernel은 아님 |
| 독립 수치 재검사 | 88,533행 | 길이 0~6, alphabet -2/0/3, 세 ordered tree 형태; 독립 과제 수 아님 |
| 원본 소스 연결 | 564개 소스 중 26개 연결·인증 | 소스 byte 20종, AST 11종; 나머지 538개는 지원 범위 밖 |
| 기존 hole 구조 구현 가능 | 13개 | 나머지 13개는 내부 상태 추가·변경이 필요하며 별도 보고 |
| 소스 변환 종료 조건 | 107개 Z3 통과 | free-word 순서 보존 및 lexicographic 종료 조건 |

새 대조군은 public fold만 받아 기존 algebra의 닫힌 부분 상태, 입력 함수,
state 순서·부호 변환을 검사한다. 작은 trace에서 decoder를 제안하고, 필요하면
독립 algebra를 product로 합친다. **trace 일치만으로 실행을 허용하지 않는다.**
원래 목표와 Empty/Step/Merge/Decode/Invariant의 9가지 보편 조건을 모두 통과해야
인증된다. false sample decoder, 음수 가중치, zero barrier, argmax 동률 위치,
Boolean 정규화에 대한 15개 검사가 사전 동결 전에 통과했다.

balance의 경우 별도 정답표 대신 알려진 prefix+sum 상태로부터 차와 조건식을
decoder로 생성했다. 가중 segment의 서로 다른 strict/weak predicate는 두 algebra의
product로 처리했다. 이는 기호 생성과 알려진 구조의 재사용이며, 새로운 계산 원리나
신경망의 학습 성과로 부르지 않는다.

## 원본 소스와 실제 OCaml

source-bound 검사는 명시된 `target = repr @@ reference` 관계를 읽고, 지원하는
순수 polymorphic CNil/Single/ordered Concat 및 Nil/Cons 표현의 입력 순서·종료성을
연결한다. 이 수학적 fragment 밖의 module, 효과, attributes, machine integer
overflow 및 전체 OCaml workflow의 정당성은 주장하지 않는다.

앞선 `SOURCE_BOUND_OCAML_FIRST`는 실제 OCaml 5.0.0에서 15개 source view,
5,445행의 원래 결과·native 결과를 보존했다. 로컬 아카이브에 15개 바이너리와
출력이 있고, 독립 audit에서 54+54 summary 조건, 107 종료 조건, 모든 행을 확인했다.

이번 별도 26개 source view 실행은 Kaggle 출력에서 **26개 통과, 7,818행 일치,
6.943400886초, runner exit 0**을 관찰했다. 그러나 출력 크기 제한으로 노트북 출력이
비워졌고, 사용량 한도에 따른 작업 중단 후 임시 VM이 만료됐다. 26개 원격 바이너리·
전체 stdout archive를 로컬로 받기 전에 소실되었다. **이 원격 첫 실행을 독립적으로
감사한 결과로 제시하지 않는다.** 소실 기록은
`Continuation/FIVE_HOUR_RESUME_2026-10-07/temporary-evidence-loss.json`에 보존한다.
복구 실행은 다른 폴더와 환경 식별을 사용하고 이 첫 실행의 대체로 취급하지 않는다.
로컬 생성·증명·expected 행 및 frozen 입력 ZIP은 보존되어 있다.

## 사전 점검과 연구 결정

기호 decoder의 최초 개발 preflight에서 Boolean conjunction의 n-ary 표현을 binary
IR로 되돌리지 않은 오류와 catalogue entry aliasing을 관찰했다. 원본 preflight를
그대로 두고 수정된 개발 preflight를 별도 폴더에 저장한 뒤 첫 통합을 동결했다.
첫 통합 이후 source/조건/예산은 수정하지 않았다.

현재 가장 최근의 완전 비용 비교는 `COMPRESSED_RECURSIVE_COMPLETE_COST_V1`이다.
240 worker가 통과했고, 강한 native/free supplied representation의 기하평균은
cold1 1.0047774454, cold16 1.0023682024로 약 1배이며 10배 사례는 0/20이다.
이는 등록한 구현·opened 구조에 관한 결과다. 다른 문제나 모든 지능 아키텍처의
불가능성을 뜻하지 않는다. 비용 우위를 입증하지 못한 known-algebra 선택·생성만을
신경망에 학습시키는 투자는 현재 허용하지 않는다.

다음 비교 기반은 [SuFu 공식 artifact](https://github.com/jiry17/SuFu)다.
[Superfusion 원 논문](https://xiongyingfei.github.io/papers/PLDI24.pdf)은 ghost compression
function으로 sketch 합성을 분해하고, 고정 rewrite를 넘어 중간 자료구조를 제거한다.
논문 구현의 검증은 bounded이며, 외부 보편 검증과 연결하는 가능성을 구분해야 한다.
기존의 자동 압축·표현 생성 자체를 NEUMANN의 발명으로 다시 주장하지 않는다.

## 파일과 해시

- Registration: `SYMBOLIC_DECODER_PREPARATION/preregister.json`,
  `bfc73191dfe74d89feebc809032e94e7ae0e70d7dac8fa0a15102414c8e97e61`.
- First report: `SYMBOLIC_DECODER_FIRST/report.json`,
  `19996ad5fdd0f9510a9d3851efa39dfae8cd4112ba65eb5801367cb82e38b05b`.
- First manifest: `45aa6a7129b92592ec3cfda3e9e6b4c25b1aacba634603557e69b73e9e8e247e`.
- Independent union audit: `SYMBOLIC_DECODER_AUDIT/audit.json`.
- Frozen source-goal OCaml input ZIP: `590aeee332f4bb8fcee1553cb0c8fb1c6ed4501781276d1f00b1ae7914b9ec52`.
- Remote 26-view first runner: `cda7d0299d39f49b3670432cc32660fc27d39ac8fab6ba6e7bad208829f091d0`.

자료는 모두 opened development다. AST hash 차이는 독립 구조의 증명이 아니다.
train/fresh 접근 54회 거절을 확인했다. Oracle·답을 실제 inference에 공급하지 않았고,
GPU 학습·봉인 평가·GitHub push·Notion 수정도 수행하지 않았다.
