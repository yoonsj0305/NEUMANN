# NEUMANN 1 — 연결 구조 변경과 강한 절차 재사용의 실측

2026-10-07. 별도 사전 등록한 `PERSPECTIVE_TRANSFER_HEADROOM_V1`의 첫 실행과
독립 재검증. **공식 판정: INCOMPLETE_NO_ADMISSION.** 모델 학습 진입은 없다.

이번에는 자료 정리에서 멈추지 않고, 기존 연결 구조를 바꾼 문제에서도 좋은 경로를
무료로 제공하는 이득이 남는지 실제 CPU query로 측정했다. 완료된 6개에서는 강한
공개 절차 재사용보다 최초 query 1.0117~1.1877배, 실제 두 query 1.0135~1.1579배다.
중단된 2개를 빼고 합격으로 바꾸지 않는다. **압도적 우위·학습된 발견·범주 변화의
증거는 아직 없다.**

## 무엇을 비교했는가

이미 열린 파생 텐서 metadata 4개에 각각 차원 재설정(REBOUND)과 내부 연결 교환
(SPLICE)을 적용한 8개 개발 사례다. SPLICE는 출력 목표·tensor 개수·각 tensor rank를
유지하면서 ordered incidence key를 바꾼다. 원래와 다른 sum-product 문제이며 원래
답을 그대로 정답으로 사용하지 않는다. 이 key 차이가 그래프 비동형성이나 독립적인
미관측 motif를 증명하지는 않는다. queen REBOUND는 실제 차원 변화 없는 대조 사례다.

공개 native GREEDY / AUTO_HQ / cotengra RECONF32, 같은 topology 카탈로그,
공개 prior의 첫 경로 / 현재 비용 모델상 최선 경로, 무료 제공 구조를 함께 비교했다.
`public_path_reuse.py`는 동일 operand 개수의 공개 prior를 연결이 바뀐 문제에도
적용할 수 있다. 새 문제의 인덱스·출력·work/peak 모델을 다시 검사하므로, 단순한
topology cache miss를 NEUMANN의 이득으로 계산하지 않는다. Oracle 경로는 native
메모리에서 제외한다. 이 재사용은 기존 알고리즘이며 학습된 C나 NEUMANN D가 아니다.

FREE_STRUCTURE는 기존 제공 경로·공개 prior·새 기존 기호 탐색의 후보 중 사전에
work/peak 모델로 고른 경로다. 전역 최적 경로나 모든 가능한 표현의 상한이 아니다.

각 완료 사례에서 7개 경로 × 3회 procedure trial × 실제 서로 다른 수치 입력 2개를
실행했다. float64, BLAS 1 thread, 양수 uniform [0.98,1.02], 전체 출력 상대 오차
1e-10이다. 서로 다른 두 구조 인증 경로의 출력 일치를 reference 조건으로 삼았다.
원본 benchmark 배열·정답은 확보하지 못했으므로 원본 데이터셋 정확도를 주장하지
않는다. 부호 상쇄·영점·나쁜 conditioning에서의 정확성도 이 결과에 포함하지 않는다.

## 사전에 동결한 조건과 실제 결과

8개 모두 평가 가능하고, SPLICE 4개의 native/free 비율 기하평균 ≥10 및 3/4 이상이
10배여야 한다. 최초 query와 실제 두 query가 모두 만족해야 한다. 단일 계산 영역의
warm-service 선별이며 통과해도 G1 승인이나 독립 범용성 증거가 아니다.

| 원본 계열 / 변형 | 최초 query native/free | 실제 두 query native/free | 상태 |
| --- | ---: | ---: | --- |
| queen / REBOUND | — | — | reference 확보 단계 중단 |
| queen / SPLICE | — | — | reference 확보 단계 중단 |
| brackets / REBOUND | 1.0117 | 1.0135 | 완료 |
| brackets / SPLICE | 1.1529 | 1.1579 | 완료 |
| sentence / REBOUND | 1.0653 | 1.0577 | 완료 |
| sentence / SPLICE | 1.1877 | 1.1410 | 완료 |
| MERA / REBOUND | 1.0869 | 1.0698 | 완료 |
| MERA / SPLICE | 1.0871 | 1.0843 | 완료 |

완료 6개 모두 PRIOR_FIRST가 가장 빠른 등록 native 비교군이다. SPLICE 완료 3개
각각은 10배 미달이다. 공식 4개 SPLICE 기하평균은 누락 때문에 null이며, 유리한
부분집합의 평균으로 대체하지 않는다. 각 trial 3개만으로 작은 비율 차이의 통계적
유의성이나 최적성을 주장하지 않는다.

총 query 관측 126개: ACCEPTED 117개, GEOMETRY_CATALOG cache miss ABSTAINED
9개. accepted 관측 안의 실제 수치 query는 234개다. 독립 reference 생성은 이
query 개수에 포함하지 않는다. 전체 study wall time 190.5206초.

queen 2개는 등록한 후보와 자원 한도(모델 work 1e9, 중간 상태 16×2^20 elements,
입력 8MiB)에서 서로 다른 eligible reference 경로 두 개를 확보하지 못해 assertion으로
중단됐다. 각 query 관측은 0개이며 성능 0점으로 채우지 않았다. 입력 두 개와 stderr,
각 worker wall time 약 39.29/38.87초를 보존했다. **offline 후보 trace가 assertion
전에 저장되지 않은 로깅 한계가 있다.** 개별 경로의 실패 원인·최선 비용·정확한
eligible 수를 사후 추정하지 않는다. 이 중단은 모든 경로가 불가능하다는 증명이 아니다.

## 비용과 입증의 범위

primary는 이미 구동된 engine의 새 구조 request다: 발견·경로 인증·compile·입력
scan·kernel·전체 출력 검사를 포함한다. 두 query도 동일 setup을 한 번만 사용한다.
native가 요청 안에서 만든 인증을 다시 검사하는 이중 비용은 없다. 무료 offline
인증은 요청 안에서 재검사한다. 실패·abstain 비용도 원본 관측에 남긴다.

import/engine 구성·입력 생성·offline 탐색·reference는 별도 투자 측정값으로 보존하며
primary에서 제외된다. 과거 공개 prior의 연구 비용은 UNKNOWN이다. 단위가 다른 비용을
합치거나 누락을 0으로 만들지 않는다. fastest native envelope는 사후 가장 빠른
등록 경로를 고른 낙관적 비교 기준이며, 무료 routing을 실제 배포 능력으로 주장하지
않는다. 이 비율은 cold-start 전체 비용, 실제 FLOPs·RAM·에너지·금전 이득이 아니다.

이 결과는 **이번 변경 규모와 positive 입력에서 기존 절차 재사용만으로도 제공 경로에
근접한다**는 관측이다. 모든 미관측 구조에서 학습이 무익하다는 결론은 아니다.
동일 operand 개수의 위치 기반 경로 재사용은 새 목표를 검사했지만, 목표 충분성을
학습하거나 새로운 표현·추상 변수를 생성하지 않았다.

## 검증과 보존

독립 replay: 원본 manifest 286개 파일, 8개 문제 생성 계보, 117개 request 경로 인증,
64개 offline 후보 인증, 234개 수치 witness 재실행, 실패 2개와 전체 판정 재구성 PASS.
관련 pytest 77개 PASS(3.73초). 첫 audit의 Python tuple/JSON list 비교 오류는 별도
실패 기록으로 남기고 audit만 수정했다. 동결한 실험 코드·첫 결과는 변경하지 않았다.

- 계약·동결 source: `Continuation/TRANSFER_HEADROOM_PREPARATION`
- 변경하지 않는 첫 원본: `Continuation/TRANSFER_HEADROOM_FIRST`
- 독립 감사: `Continuation/TRANSFER_HEADROOM_AUDIT_2026-10-07/replay.json`
- D 공개 projection / O offline 기록: `Continuation/TRANSFER_HEADROOM_ASSETS_2026-10-07`
- 계약·원본·감사 pins: `docs/experiments/perspective_transfer_headroom.pins.json`

새 projection도 기존 권한 API로 접근한다. native runtime에 공개 equation/shapes만
전달하며, 비용·경로·결과 supervision은 runtime=false인 O/offline에 분리한다.
모든 8개는 opened development, fresh eligible=0, train 비활성이다. 원래의 first
case 파일은 O 경로를 포함하므로 그 파일 전체를 일반 runtime 입력으로 쓰지 않는다.

## 결정

이 tensor 후보의 경로 선택 학습에는 GPU 예산을 배정하지 않는다. 누락 사례를
제거하거나 기준을 낮춰 재실행하지 않는다. 다음은 이 계열의 변형을 늘리는 일이
아니라, **현재 공개 prior와 알려진 탐색이 처리하지 못하는 목표 보존 표현 생성**의
가치를 독립적인 영역에서 선별하는 것이다. 우선 공개 입력만으로 적절한 표현을
생성·인증할 수 있는지, 강한 B/C에도 동일 재사용·검증 권한이 있는지, 원래 목표의
충분성과 투자 비용을 측정할 수 있는지를 확인해야 한다. 이 결과만으로 다음 후보나
학습 계약이 승인됐다는 뜻은 아니다.

North Star/Q1–Q7과 모든 과거 판정 유지. G1 미진입, G2·Decision3 봉인 유지.
