# NEUMANN 1 연구 상태 감사

v1.1 후속 업데이트: [Guarded 구현과 결과](docs/research/guarded_perspective_2026-10-08.md).
감사 시작 main `55178a2`, #175 `c404f66`, 미병합; c404의 CI 7개 SUCCESS 확인.
기존 source pin을 보존한 별도 Guarded 확장과 기존 불변량 연결을 구현했다.
ENGINEERING PASS지만 기존 fixture의 같은 최적화 권한을 갖춘 Native 대비
operational 비용 약 1배다. 그 계열의 학습 HOLD, 기존 G0 A/B 유지,
G1/G2 미진입. 아래 v1.0 감사 결과와 최초 기록은 기존 시점의 관찰로 보존한다.

2026-10-08. 사용자 Research & Development Directive v1.0을 적용한 D0.
**현재 결정: PIVOT(후보 선정), HOLD(G1/G2). 압도적인 비용 우위와 학습된 LPS는 미입증이다.**
North Star/Q1~Q7, 과거 판정과 Decision 3 봉인은 변경하지 않았다.

## 1. 저장소와 실행 상태

Git fetch와 인증된 GitHub API로 다시 확인했다.

| 항목 | 확인된 상태 |
|---|---|
| main | 55178a211962caf5ce677deb37edd30bfb4fdccc |
| PR #174 | OPEN, 미병합; a0119180e743f5115b21847fdb6ac6741f97bbe2 |
| PR #175 | DRAFT/OPEN, 미병합; 감사 시작 HEAD 12412bfe88d5efcf6a5a15cf037e9cd79d0ed7a8 |
| ancestry | #174 HEAD가 #175 HEAD의 조상; #175는 main에 없는 #174 작업도 포함 |
| 기존 CI | 12412bf에서 7개 workflow 모두 SUCCESS; 이번 변경의 CI와 구분 |
| 학습된 LPS | 없음; 생성기·검증기·기호 기준선은 있음 |
| G0/G1/G2 | 기존 등록 G0는 통과하지 못함; 새 G0 실행 없음; G1/G2 진입 근거 없음 |
| Decision 3 | 봉인 payload 미접근·미해시 |

초기 공개 e2a05f5와 12412bf 사이의 neumann1/ 및 experiments/ Git tree는 같다.
CI 의존성과 테스트 fixture 수정이 동결된 과학 코드를 바꾸지 않았음을 확인했다.
이번에 추가한 공통 계약은 별도 새 모듈이며 이 과거 tree 비교의 대상이 아니다.

## 2. 모순처럼 보였던 기록의 정리

* PR #174 본문은 실행 전 상태다. 이후 로컬 P112_FIRST 원본 ZIP의 SHA-256과
  diagnosis를 확인했으며 실제 판정은 **FAIL, accepted 7/12**다. 두 시점을 구분한다.
* recursive_summary 최초 준비의 옛 runner는 미실행이다. 실행된 preflight-fixed
  등록과 구분하며 원본과 수정 등록을 모두 보존한다.
* functional experience의 첫 index에는 중복 record_id가 있었다. 별도 identity
  repair가 290개 실행 ID/285개 byte group을 만들었으며 첫 index를 대체하지 않는다.
* 이전 26-view OCaml5 첫 archive는 유실 상태다. OCaml4.14 별도 실행의 26/26,
  7,818개 finite row 결과는 복구 증거이며 유실된 최초 실행의 독립 감사가 아니다.
* SuFu 183/290은 upstream bounded success다. 범위를 넓힌 373개 반례는 조건부
  진단이며 공식 논문 점수를 재판정하지 않는다.
* tensor의 최대 약 3.45배는 네 원본 배열의 실행 component 중 관찰값이다.
  완전 비용, 독립 일반화, 학습된 NEUMANN 또는 G0 통과로 확대하지 않는다.

## 3. KEEP / REFACTOR / ARCHIVE / MISSING

분류는 개발 우선순위다. 역사적 파일을 삭제하거나 물리적으로 이동하지 않았다.

| 분류 | 자산 | 처리 및 한계 |
|---|---|---|
| KEEP | representation_program, inductive_perspective | 정확 정수 DAG·다섯 귀납 조건·원래 목표 보존 |
| KEEP | recursive_summary, recursive_dag | 아홉 충분 조건·순서 보존·인증된 공유 DAG 실행; SMT solver 신뢰 포함 |
| KEEP | representation_rewrite_certificate | 기존 정수 ring-law 조합 증명; 새 학습 원리 아님 |
| KEEP | inductive_symbolic_baseline, native decoder/portfolio/catalog | 공개 입력 기반 생성·기존 절차 재사용을 강한 B/C에도 동일 제공 |
| KEEP | structural_data_rights, candidate_budget, independent audits | payload 전 권한 검사·단위별 예산·원본 검증; OS 보안 경계 아님 |
| REFACTOR | 도메인마다 따로 흩어진 제안/증명/비용/경험 연결 | perspective.py 하나로 최소 공통 계약; 기존 도메인 IR 유지 |
| ARCHIVE | P1 역할 scorer·모델 교체·이미 실패한 단일 구조 선택기 | 개발 반례·재현 기록으로 보존; 같은 후보의 학습 투자 중단 |
| ARCHIVE | 기존 실패 G0/비용 실험·중단/timeout 실행 | 최초 값과 계약 그대로 보존; 새 판정으로 덮지 않음 |
| MISSING | 학습된 REFRAME/INTERNALIZE | 새 표현 프로그램 생성·경험의 학습·독립 전이 미구현 |
| MISSING | 새로운 후보의 검증 가능한 free 표현과 강한 동일 환경 비교 | 선별된 두 후보의 G0 선행 조건; 기존 결과로 대신할 수 없음 |
| MISSING | 독립 구조 lineage·프런티어 실제 격차·전체 자원 계측 | fresh 성능, 에너지/FLOPs/전체 투자 UNKNOWN; G2 실행 불가 |

Core는 기존 표현/검증/실행 모듈과 새 공통 계약, Research는 후보·등록/실험 도구,
Evidence는 최초 실행/감사, Archive는 이전 개발·실패 기록으로 읽는다. 디렉터리
대이동·중복 런타임·새 범용 증명기를 만들지 않았다.

## 4. 구현한 가장 작은 공통 계약

neumann1/perspective.py는 ProblemView, StructuralState, PerspectiveProposal,
ValidityCertificate, CostReceipt, ExperienceRecord, ExecutionDecision을 제공한다.
정확 정수 recurrence와 piecewise-linear integer list fold 두 영역을 연결했다.
이들은 서로 다른 실행 계약의 engineering coverage이며 독립 두 분야의 지능 성능
입증이 아니다. 두 영역 모두 기존 연구에서 열렸던 수학적 프로그램 영역이다.

원래 문제와 목표의 hash, 표현 payload, 제거하려는 계산, 보존 범위, 재사용 조건을
연결한다. 상태의 변수/관계 추출은 기존 schema 투영이며 학습된 PERCEIVE가 아니다.
removed_computation은 제안자의 설명이며 실제 비용 절감의 증명이 아니다.
기존 compile_acceleration/CertifiedSummary가 한 번 인증하고 실행기를 만든다.
원래 목표/범위 mismatch, 잘못된 표현, UNKNOWN은 실행을 차단한다. 검증이 성공해도
결정은 ENGINEERING_ONLY다. 이 API는 경제성·학습·독립 평가 진입을 승인하지 않는다.

같은 인증 표현의 다른 입력 실행에는 증명을 다시 풀지 않는다. 이는 이미 기존
engine가 제공하던 proof reuse를 공통 계약에서도 유지한 것이다. 새로운 속도 개선
측정이 아니다. 모든 비교군에 같은 권리를 제공해야 한다.
비용은 phase와 단위를 유지하고 미관측 값/peak memory를 null로 남긴다.
발견·실패·fallback·투자 등이 없으면 complete_total은 UNKNOWN이다.
ExperienceRecord는 열린 개발용이며 학습 및 fresh 사용을 활성화하지 않는다.

## 5. 이번에 추가로 줄인 불확실성

가설: 현재 압축 재귀 비용에서 검증만 고치면 10배에 도달할 수 있는가?
분석 조건: 기존 native 비용은 유지하고 free 경로의 측정된 검증+engine 구성을
완전히 0으로 만든 극단적으로 유리한 민감도 계산. 원본 240개 관측 전부 사용,
case별 세 반복의 중앙값과 기존 20개 전체 case를 유지했다. 새로운 성능 실험,
사전 등록 통과 판정 또는 warm service의 하한으로 사용하지 않는다.

| 조건 | 기존 실제 기하평균 | free 검증+compile을 0으로 한 계산 | 계산상 최대 case | 10배 case |
|---|---:|---:|---:|---:|
| cold, 실제 요청 1개 | 1.004777 | 1.055991 | 1.204596 | 0/20 |
| cold, 다른 요청 16개 | 1.002368 | 1.053044 | 1.154314 | 0/20 |

native complete 중앙값 약 1.768초, 검증+engine 중앙값 약 0.05237초다.
서로 다른 phase/반복의 중앙값을 임의로 더하거나 차감해 새 실행값으로 보고하지 않는다.
결정: **REJECT — 이 cold 범위에서 verifier 최적화 단독으로 10배를 얻으려는 투자.**
새로운 문제나 warm deployment에서는 비용 분해가 달라질 수 있으므로 UNKNOWN이다.
원래 최초 NO_10X 판정은 바꾸지 않았다.

## 6. G0 후보를 두 개로 압축

후보의 정확한 계산 원리·강한 비교군·새 측정 필요성을
[g0_candidate_review_2026-10-08.md](docs/research/g0_candidate_review_2026-10-08.md)에 기록했다.

* A: 목표 조건부 확률 전이계의 충분 상태. 정수 닫힌 식/인접 true-twin을 바꿔
  부르는 것이 아니다. 확률 전이와 목표 reachability의 의미를 보존해야 한다.
* B: 원래 Boolean 제약에서 합성한 인증 가능한 counting circuit의 재사용.
  tensor contraction 경로 선택이 아니라 논리적 분기·분해를 새로운 표현으로 만든다.

가장 값싼 검토는 기존 결과+선행 구현 확인이다. A의 일반 quotient는 Storm의
symbolic/bisimulation 최적화, B의 회로 재사용은 D4/CPOG가 이미 비교군으로 가진다.
상태 수 축소/회로 재사용 자체만으로 새로운 여유를 주장할 수 없다.
두 후보의 원래 목표를 보존하는 제공 표현과 강한 비교군의 동일 환경 비용은 아직
연결되지 않았다. **H1-A UNKNOWN, 새 G0 성능 실행 HOLD**다. 부족한 비용을 0으로
채워 합격시키거나 약한 Python brute force를 만들어 baseline으로 삼지 않았다.

다음 작업은 우선 B의 기존 CPOG/D4를 재사용할 수 있는지 좁은 원본 문제에서
확인하는 것이다. 강한 B/C에도 동일 인증 circuit 재사용 권리를 주며 teacher/circuit
발견 비용은 별도 O 투자로 남긴다. 유효한 free 표현이 없거나 기존 compiler가 같은
표현을 싸게 얻으면 후보를 중단한다. 아직 이 작업을 실행/성공했다고 기록하지 않는다.
G0 성능 측정 전에 표본 전체·복잡도·기하평균/성공 비율·cold/reuse 횟수·timeout·
baseline portfolio와 실패 처리까지 동결한다. 이 준비 문서는 성능 사전 등록이 아니다.

## 7. 증거·검증·제외 범위

실행 가능한 D0 감사: experiments/research_state_audit.py.
로컬 최초 산출물: NEUMANN 1/Continuation/RD_DIRECTIVE_2026-10-08/.
audit-first.json은 최초 선택 범위 검사이고 audit-with-original-bindings.json은
기존 compressed manifest 1,444개를 추가 대조한 산출물이다. 첫 파일을 교체하지 않았다.

21개 공개 보고/등록 파일, 6개 로컬 원본 archive, 현재 실행 계약 15개 source pin
항목, P1.12 원본 ZIP을 대조했다. 일부 source가 두 계약에서 중복된다.
이 작업의 PASS는 **선택된 열린 증거 정합성**이며 모든 과거 원본/환경의 완전성을
선언하지 않는다. 오래된 누락 archive는 계속 제외되고 sealed 자료는 읽지 않았다.
CI 판정은 기존 커밋의 성공이며 새 변경의 테스트·CI 결과는 별도로 기록한다.
최종 관련 로컬 테스트는 **81 passed**다. 이 숫자는 모델 성능이나 연구 생산성 지표가 아니다.

새 구현은 두 영역의 원래 목표/순서 보존, 한 번의 인증 재사용, caller payload 변경,
위조된 proof metadata, UNKNOWN, 목표·scope 변경, D/O/S 등 권한, 누락·음수·NaN
비용을 검사한다. 로컬 Windows 전체 suite에는 과거 Linux resource 의존 collection
문제가 있어 전체 Windows CI 통과를 주장하지 않는다.

최종 연구 목표 미달, 학습된 발견 0, 새 fresh 평가 0, GPU 0.
**다음 gate: HOLD. 기존 검증 기능을 기반으로 새로운 의미적 표현의 G0 준비를
진행하되, 이득의 원래 문제 증거가 연결되기 전에는 G1 모델을 만들지 않는다.**
