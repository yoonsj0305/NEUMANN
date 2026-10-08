# LP success envelope — historical Q5 FAIL preserved

전체 frozen 판정은 `Q5_SCALING_CAPABILITY_OR_ACCOUNTING_UNREACHED`다.
이는 current North Star Q5 폐쇄가 아니며 성공 셀만 뽑아 PASS로 바꾸지 않는다.
48 independent originals,96base/surface views,1536관측 중 32 Direct 관측은
5초 capability/budget 실패다. Candidate의 원래 최종 valid capability는 유지됐다.

파생 CSV는 **모든**96views×2models=192행을 보존한다. 조건수, m, 폭, surface,
확대/fallback 횟수, 원래 complete 비용과 cold 투자, stationary 회수량을 연결했다.
176행만 같은 능력/회계로 비교 가능하며114행이 양의 등록 비용 절감을 보였다.
나머지16행에는 censored Direct 시간을 denominator로 한 speedup을 쓰지 않았다.

| m | n/m | 등록 비용 이득 model-view행 /16 | 같은 요청의 조건부 회수 N 범위 | 원래 gate의 병목 |
|---:|---:|---:|---:|---|
|32|1|0|없음|control complete overhead |
|32|16|16|788–1250|discovery burden>.20 |
|32|32|16|372–576|discovery burden>.20 |
|64|1|0|없음|control complete overhead |
|64|16|16|128–348|해당 등록 셀 PASS |
|64|32|16|51–74|해당 등록 셀 PASS |
|128|1|0|없음|control은 별도 허용 기준; 우위 주장 없음 |
|128|16|16|17–37|해당 등록 셀 PASS |
|128|32|16|7–11|해당 등록 셀 PASS |
|256|1|2|281–6598 (양의 두 경로만)|대부분 비용 이득 없음; control 조건과 구별 |
|256|16|16|3–4|surface utility .782625/.783728가.80미달 |
|256|32|UNKNOWN|UNKNOWN|Direct capability unreached; 16행 비용비교 제외 |

각16행은4originals×2surfaces×2checkpoints다. 독립16문제로 세지 않는다.
두 checkpoint와동등 surface의 비용은 상호 독립 표본이 아니다. Exact condition1/
1000, 확대·fallback은 CSV의 각 원본 view별 기록이 authority다.

## 계산식과 가정

등록 비용 차이는 `S_registered = C_Direct_registered - C_candidate_registered`다.
Complete는 original per-repeat full 비용의 median이며 component median들의
싼 조합으로 대체하지 않는다. 역사적 Q10000 판정과 그 범위를 그대로 쓴다.

Stationary 요청의 회수식은 `I_D + N O_D > I_N + N O_N`이며,
`O`는 **같은 원본 환경의 median(total_ms)**, `I`는
`cold_q1_ms - median(total_ms)`다. proposal이 제외된 post_ms를 빼면
투자·반복 비용이 섞이므로 사용하지 않았다. `O_D<=O_N`이면 유한 회수량은 없다.
양의 절감이면 strict advantage를 만드는 첫 양의 정수 N을 계산했다.

동일 분포가 계속 반복되고 환경·resident process·clock·실행 권한이 같다는
Assumption이다. 값은 해당 source-specific stationary projection이지 실제
운영 요청의 실측이 아니다. 원본에 없는 training label/corpus/초기 지식/
배포 투자 비용은0으로 넣지 않았으므로 완전한 lifecycle break-even은 UNKNOWN다.
CPU/GPU/줄/원 단위를 더하지 않았고 다른 실행환경의 v102/v104/M106 시간을
Q5의 요청 비용으로 합산하지 않았다.

원본 Q5 report SHA256:
`1f7a3ad5a1038e42234b734b0b00f185c0be4a5a1d11a3d3d6e96ace92d546e3`.
코드 `analyze_retained_lp.py`; 원래 공식 비용식 `neumann1/q5_evidence.py::summarize`.
새 solver/inference/timing 실행 없음. 원래 accepted/capability/FAIL은 그대로다.
