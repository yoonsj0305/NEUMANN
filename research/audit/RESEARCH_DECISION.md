# Research decision — Master Directive v2.0

**HOLD_LEARNING**

후속 원본 복구:8개 P1 최초 ZIP의 무결성을 확인하고7건의 기존 model-free
replay를 통과했다. P1.7의 최초 replay failure는 유지한다. P1.2의 안정적인
오분류와 P1.5/P1.6의 실행 전 형식 거절을 구분했다. P1.5산술은 원본상4/4로
감사 표의3/4전사만 수정했다. P1.11.1raw-top6/12로 threshold-only 요구9/12
달성은 배제된다. 형식 수정·임계값 조정·model교체를 새 지능 증거로 취급하지
않는다. `P1_RECOVERY_REVIEW.md` 참조. 새로운 학습 진입 근거는 생기지 않았다.

Q34 성공 귀속의 후속 확인: 24원본/48동등표현에서 각 frozen ranking은
2m40/48 complete basis, 실제8개 확대는 한 열 누락과 정확히 일치한다.
기존 deterministic residual ranking의4m48/48 coverage도 확인했다.
미실행 경로의 실제 capability/cost는 UNKNOWN이며 새 timed ablation으로
이미 유지되는 HOLD를 반복 판정하지 않는다. 원래 Q34 PASS는 보존한다.
`Q34_MECHANISM_ATTRIBUTION.md`에 학습 기여와 미입증 범위를 분리했다.

2026-10-08 후속5시간 작업 중 G0 A native확률screen을 사전 등록해125jobs를
실행·원본export·독립분석했다.361exactPASS/14NOT_VERIFIED/9process failures/
15timeouts이며 전체는INCOMPLETE다. 등록two-bin optimistic평균BRP4.364x,
Crowds9.67849x로10배family PASS는없다. Coupon22.55x/EGL53.09x는singletons이고
기존정확analytic대조군도있다. Crowds와Herman15도source-bound 수학대조군을
확인했다.10engineering testsPASS는성능증거가아니다. 분석/원본은
`docs/research/g0_probabilistic_native_2026-10-08.md`에연결했다.
G0 B counting첫INCOMPLETE도유지한다. 추가singleton/rescue/model교체는하지않는다.

기존LP원인도구체화했다. v088학습48개최적positive support는full row rank로
dual을유일하게정하지만M10616개는14~112차원dual자유도가남는다. 따라서
정답support를회수해도original certificate가따라오지않는다. 동시에cost/residual
특징두채널이M106에서거의상수로변했다. 기존witness/array분석이며new
solver/model0회다. 이두사실은서로다른전이병목이고solecause/refit승인이아니다.
`CERTIFICATE_GEOMETRY_CAUSAL_REVIEW.md`와`FEATURE_TRANSFER_CAUSAL_REVIEW.md`참조.

현재의다음결정은**HOLD_LEARNING**이다. 새로운문제계열전체를불가능하다고
선언하지않지만,현재자료로새learned architecture를정당화할잔여경제적여유와
강한기호발견의미해결gap은입증하지못했다. NorthStar/전역Q1–Q7은OPEN,
Phase3/G1/G2/봉인평가는미진입이다. 아래기존시점기록과판정은보존한다.

2026-10-08 Phase2 후속 판별을 완료했다. 원본16개·576관측을 사전 등록하고
최종576/576 original-valid와 독립 replay를 확인했다. StrongNative/경로의
기하평균은 B무료 ranking0.694/0.698,C무료 support+old0.725,
D무료 support+유료 dual0.484,E무료 support+dual4.091이다. 각 후보의10배
원본은0/16이었다. D는5/16에서 minimum-norm dual이 통과했고11/16에서는
비싼 full dual LP가 필요했다. v2.0의 C/D중단 규칙에 따라 Phase3와 새 학습을
시작하지 않는다. 자세한 판정과 비용 범위는
`docs/research/bp_certificate_diagnostic_2026-10-08.md`와
`BP_CERTIFICATE_DIAGNOSTIC_ANALYSIS.json/.csv`에 있다.

아래는 Phase1 당시 결정과 조건이다. 그 최초 감사 snapshot/hash는 별도
Continuation/MASTER_RECOVERY_V2_2026-10-08/phase1-audit-snapshot에 보존했다.
Phase2 원본은 별도 BP_CERTIFICATE_DIAGNOSTIC_2026-10-08/first에 있다.

Hypothesis: v102의 유용한 learned support ranking은 보존하되, BP 전이 실패를
단순 capacity/feature 문제로 취급할 수 있는가? 더 넓은 새로운 표현 발견을
학습하기 전에 certificate economics가 핵심 병목인지 기존 증거로 판별한다.

Acceptance criterion(분석 작업): 원본 verdict/hash/namespace를 유지하고,
새 model/solver/data 없이 original witness·실패·비용을 연결한다. 독립 원본,
surface, seed, warm/timed repeat를 구별한다. 누락 비용은 null로 남긴다.
최적 primal인지 원래 certificate로 확인하며 planted support는 권위로 쓰지 않는다.

Outcome: v102 bounded Q34 PASS는 유지된다. Q5에176 comparable model-view행,
114 cost-advantage행이 남지만 전체 FAIL은 유지된다. M106에서256 final/232
restricted witnesses를 원래 verifier로 재확인했다. 19 first-timed attempts
(13candidate paths,7originals)는 최적 primal이지만 dual feasibility로 거절됐다.
그19개는 이미 보존된 Native dual과 결합하면19/19 original-valid였다.
새 solver/model0, 봉인 payload 접근0. 이 O 진단의 dual 획득 비용은 UNKNOWN다.

이 결과는 비용까지 입증한 새로운 NEUMANN 성공이 아니다. 인증 공백이
실제 일부 전이 실패를 유발한다는 열린 개발 진단이며, 다른 후보들은 primal
회수도 실패했으므로 certification만 고치면 모두 해결된다고 말하지 않는다.

## 실행할 정책과 중단할 투자

현재 M106 분포에서는 **Strong Native를 항상 사용**하는 결정론적 정책이
같은 능력에서 두 frozen 후보보다 모든16기록 셀에서 싸다. 새로운 정책
모델 없이 재현 가능한 강한 기준선이다. 이것은 새 unseen policy 능력은 아니다.

- HOLD: 새 GPU/forward/refit/P1.x model swaps, G1/G2, 실패했던 guarded/
  recursive/tensor 선택 학습, 변경 없는 counting cold pipeline 학습.
- KEEP: v102 두 checkpoints, analytic quotient, original LP verifier,
  native executor, Universal/Guarded certificates, 구조 경험·반례·출처.
- 후보 우선순위: certificate-aware goal-sufficient discovery라는 **한 가설**.
  cardinality/relational/compute-aware 후보는 경제적 진단 전까지 구현 HOLD.
- 추가 성능 실험: 이번 HOLD 결정을 위해 필요 없음. 현재 코드 변경은
  CPU source inventory와 원본 causal analysis에 한정한다.

## 단 하나의 후속 판별이 필요한 조건

이 HOLD를 뒤집으려면 정확 support를 공급하되 optimal dual을 공급하지 않은
경로가 가장 강한 적용 가능한 native보다 전체 비용에서 충분히 저렴한지
확인해야 한다. 기존 자료에는 v104의 **support+dual 동시 무료** 조건만 있고
M106의 같은 inputs에 대한 C/D/E matched 결과는 없다. 그러므로 이 조건의
headroom은 UNKNOWN이다. 지금 첫 단계에서 새 실험을 억지로 실행하지 않는다.

다음 연구를 실제로 시작할 경우에만 기존 opened16 inputs, A strong native,
B frozen system, C free optimal support+old2m/4m, D sparse adapter with paid
dual generation, E free support+dual을 같은 환경·권한·startup/실패 비용으로
사전 등록한다. strongest L1 comparator coverage가 준비되지 않았거나 D를
certify하는 기존 수단이 없으면 INCOMPLETE/INSUFFICIENT_EVIDENCE로 남긴다.
그 조건이 충족되기 전에는 NEXT_DECISIVE_EXPERIMENT 실행 계약을 만들거나
학습 예산을 배정하지 않는다. 과거 M106 결과의 rerun/대체도 아니다.

전역Q1–Q7 OPEN; 기존Q34 PASS/Q5 FAIL/M106 FAIL/Decision2 FAIL/P1first/G0
판정 유지; Decision3/v098/v107 봉인 유지. 새 GitHub 반영 없이 로컬 저장했다.
