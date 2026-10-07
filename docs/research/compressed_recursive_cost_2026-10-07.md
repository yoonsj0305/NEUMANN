# 압축된 재귀 문제의 전체 비용 비교

2026-10-07. `COMPRESSED_RECURSIVE_COMPLETE_COST_V1`의 최초 결과와 독립 감사다.
20개 열린 수학적 fold 표현에서 **등록한 10배 비용 여유를 찾지 못했다**.
학습된 NEUMANN, 프런티어 능력, 새로운 계산 원리의 증거가 아니다.

| 실제 사용 조건 | 유효한 경우 | Native / Free 비용 기하평균 | 10배 이상 | 판정 |
| --- | ---: | ---: | ---: | --- |
| 새 process에서 실제 DAG 1개 | 20/20 | 1.00477745 | 0/20 | 기준 미달 |
| 새 process에서 다른 DAG 16개 재사용 | 20/20 | 1.00236820 | 0/20 | 기준 미달 |

실제 240개 worker 모두 완료했고, 원래 목표 출력 2,040개를 확인했다.
이는 320개 서로 다른 요청을 두 경로·세 반복에서 측정한 것이며 독립 문제
2,040개가 아니다. 전체 연구 실행은 435.90320초였다. 첫 판정은
`NO_10X_IN_REGISTERED_COMPRESSED_REFERENCES`이며 결과·예산을 교체하지 않는다.

공개 입력에서 known monoid/map/permutation/product 또는 finite response를
생성하는 강한 기호 기준선과, 미리 제공한 **유효 참조 표현**을 비교했다.
참조 표현은 전역 최적 Oracle가 아니다. 두 경로에 동일한 보편 검사기,
DAG executor, 한 번 인증 후 실제 다른 요청에 재사용하는 권리를 주었다.
Native도 표현을 생성하므로 NEUMANN의 고정 표현 선택기만으로 차별화할 수 없다.

대표 요청은 71개 노드에 약 5.76×10^18개의 리스트 원소를 나타낸다.
펼친 길이는 의미상 크기다. 이를 speedup 분모로 사용하지 않았다. 기존 native도
공유 DAG를 같은 요약으로 실행한다. 압축된 문제를 실행할 수 있다는 사실과
강한 기존 방법보다 저렴하다는 주장을 분리한다.

측정은 parent launch부터 process 종료, 출력 읽기와 정답 비교까지 포함한다.
imports/입력 읽기/표현 생성/인증/실제 실행/저장 비용을 뺐다고 계산하지 않는다.
외부에서 공유하는 일반 Windows 머신이며 전용 CPU core를 격리하지 않았다.
중앙값 기준 native의 생성은 약0.00048초, 인증·engine 구성은 약0.052초였다.
기타 비용은 약1.69초로 process/import/read/write 등을 포함한다. 이것은 관측
component 진단이며 warm service의 비용이나 지능의 내재적 하한 측정이 아니다.

선행 구조 탐색·library 구축·Synduce 빌드 비용은 별도 기록에 보존했다.
학습은 수행하지 않았으며 연구 노동과 전체 R&D 비용은 UNKNOWN이다.
FLOPs·에너지·금전·peak RAM을 wall seconds에 더하거나 측정했다고 주장하지 않는다.

표본은 이전 공개 source 조사에서 인증된 **20개 exact AST** 전부다. 같은
원본의 변형과 보조 함수가 포함될 수 있다. hash 차이는 구조적 독립성 증명이
아니다. 인증되지 않았던 나머지7개 AST는 이 제한된 비용 범위 밖에 남겼으며
전체 NEUMANN 가능성을 기각한 사례로 취급하지 않는다. 모든 데이터는 opened
development이고 fresh0, 한 domain이다. G1/G2 진입 조건을 확보하지 못했다.

독립 감사는 1,444개 최초 manifest 파일, 240개 worker 및 각 출력·입력·certificate
연결을 확인했다. 서로 다른20개 프로그램의 조건180개를 별도 Z3 AST 변환으로
증명하고, 저장된 CVC5 조건180개를 Z3로 다시 풀었다. 큰 DAG 출력2,040개는
별도 interpreter와 인증된 귀납 조건으로 확인했으며, 작은 원래 리스트를
실제로 펼친 대조600개도 통과했다. 원래 OCaml repr/target 전체, machine overflow를
독립 증명했다는 의미는 아니다. 원문 목표 연결은 별도 후속 engineering 작업이다.

첫 등록/source는 `Continuation/COMPRESSED_RECURSIVE_COST_PREPARATION`, 첫 원본은
`COMPRESSED_RECURSIVE_COST_FIRST`, 독립 감사는 `COMPRESSED_RECURSIVE_COST_AUDIT`다.

- 등록 SHA-256: `b19e8576bb7ca3e2c8b9e325c2e18c06aa5e3a913a52f6f982ff1d9447296a72`
- report SHA-256: `e4487e30d748bbee4be32050af2b942c316b6d98d77ad0ffaf04e1d0efeaf0b9`
- manifest SHA-256: `cf515dd54a4826d10f562e79694e8b9f294f2738b5351906522981f3b0b49606`

North Star/Q1–Q7 OPEN, Decision3 봉인 및 기존 실패는 유지한다. GPU·훈련0회.
이 결과를 근거로 같은20개 알려진 표현 생성기의 학습을 배정하지 않는다.
압도적 비용 우위를 입증하려면 기존 native가 이미 제거한 계산을 다시 절약으로
세는 대신, 실제 어려운 원래 목표에서 필요한 새로운 표현 생성의 가치를 보여야 한다.
