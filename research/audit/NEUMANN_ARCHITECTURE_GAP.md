# NEUMANN architecture gap

P1 raw originals와 기존 replay가 확인한 경계: explicit typed routing은
정확한 deterministic admission으로 모델 없이 처리할 수 있다(P1.3). 하지만
S4 평균의 안정성, sketch parsing 및 cosine confidence는 목표의 의미 관계를
보존한다는 보증이 아니다. P1.5형식 거절과 P1.11.1ranking 오류는 서로 다른
병목이다. 이 제어 계열을 더 바꾸는 것만으로 LP의 학습된 basis concentration을
새로운 goal-preserving representation generator로 확장하지는 못한다.
`P1_RECOVERY_REVIEW.md`는8원본ZIP/7개 model-free replay를 연결한다.

실제 성공에서 학습된 추가 가치는 작은 shortlist 집중도다. Q34의 두 frozen
ranking은2m에서40/48 positive basis를 완전히 담고8개 누락은 기존 verifier의
4m 확대로 복구했다. 기존 residual ranking은2m18/48,4m48/48 coverage를
보인다. 후자의 실제 비용/능력은 미측정이므로 dominance를 주장하지 않는다.
학습된 ranking·고정2m/4m 표현·검증 확장의 결합과 새로운 goal-sufficient
표현 프로그램 생성은 구분한다(`Q34_MECHANISM_ATTRIBUTION.md`).

확인된추가경계: 원래학습48개는m개의positive full-rank basis가dual을
유일하게정한다. M106의s=m/8 positive support는m-s=14~112차원dual자유도를
남겨최적primal만으로제거한constraint의인증이따라오지않는다. 이것은
원래구성family의certificate-completion 특성이전이에유지되지않은것이다.
정확한ideal-generator 논증·64원본수치진단은
`CERTIFICATE_GEOMETRY_CAUSAL_REVIEW.md`에있다. 새학습/forward/solver는없다.

G0 A native확률cohort는125jobs/375receipts에서INCOMPLETE이고등록family
headroom PASS없음이다. Coupon/EGL/Crowds/Herman15의원래목표에는더단순한
classicalanalyticcontrols가있다. 기존symbolic/native가다루는목표축약을
배운선택기로감싸도새REFRAME/INTERNALIZE의추가가치는입증되지않는다.
이단계에서새generator 구현은HOLD한다.

추가 원본 분석: v088 학습48개에서는 quotient의 비용/residual 채널이 열을
구분하지만 M10616개에서는 거의 상수다(std 최대2.5e-16). ±열 짝의 나머지
특징은 두 signed correlation과 동일한 absolute 관계로 구성된다.
분포 변화의 구체적인 정보 경로를 확인했으며 원인 단독 입증·재학습 승인으로
확대하지 않는다. `FEATURE_TRANSFER_CAUSAL_REVIEW.md`와 원본별CSV를 참조한다.

Phase2 결과: 기존 소프트웨어를 재사용한 sparse/KKT/full dual LP 진단은
576/576 final-original 인증을 했지만 Native/D0.484×로 경제적 성공은 없었다.
free support와free dual을 모두 제공한 E도 등록operational기하평균4.091×,
10배0/16이었다. full-goal certificate를 정확히 얻는 기능과 그 기능을
저렴하게 얻는 지능은 구별된다. **새 learned architecture는 구현하지 않는다.**
원본과 단계별 측정은 bp_certificate_diagnostic_2026-10-08.md를 참조한다.

**v102에서 학습된 것**은 인간이 설계한 quotient observable을 받아 구성된 LP의
optimal-basis column 순위를 예측하는433-scalar 정책이다. native가 shortlist를
풀고 전체 primal/dual 검증 실패 시4m/full로 확대하는 runtime가 함께 이득을
만들었다. 이것은 보존할 bounded mechanism이다.

**현재 목표에 필요한 것**은 goal-conditioned sufficient representation
generation과 certificate-aware discovery다. 다음 연결이 아직 없다.

| 기능 | 실제 보유 | 현재 부족한 기능 |
|---|---|---|
|PERCEIVE|명시적 LP coefficient/typed goal, controlled parser, relation/proof IR|열린 원문에서 필요한 goal/관계를 learned model이 정확히 추출하는 넓은 능력 |
|REFRAME|사람 설계 quotient, fixed support, symbolic invariant·rewrite·recursive summary/decoder, guarded elimination|새로운 충분 표현 프로그램/변환 조합을 학습해 생성하고 independent motif에 적용 |
|DISCRIMINATE|original numerical verifier, exact polynomial proofs, SMT/출처-bound 실행|cheap certificate acquisition을 discovery 목표와 연결; 올바른 primal의 dual 생성 비용을 피하거나 줄이는 근거 |
|INTERNALIZE|source-bound experience/반례/cost catalog와 native procedure reuse|검증 경험으로 새 구조를 생성하는 학습, 반례에 기반한 일반화/repair, 비용 stop policy의 independent evidence |
|Economics|원래 per-stage receipts, 실패/fallback, 일부 cold/setup amortization|unknown investment·메모리·에너지와 강한 specialist를 포함한 전체 우위 |
|Capability|bounded constructed LP certificates와 작은 arithmetic/CSP/code verifiers|실제 같은 문제에서 Frontier가 해결한 gap 회복; G2미진입 |

Guarded core는 불변량을 초기 조건에 묶어 도달 영역에서 목표 충분성을
승인할 수 있다. universal 조건은 유지된다. 정확 정수7항등식의 엔지니어링
성공은 learned generator가 그 invariant를 경제적으로 발견한다는 증거가 아니다.
fixture의 native/free compiled code와 실제 운영 비용이약1배여서 학습은HOLD다.

M106의 중요한 공백은 “support에 최적 primal이 있는가”와 “그 representation의
executor가 **original** optimality certificate를 싸게 내는가”의 차이다.
Restricted dual은 제거한 모든 column의 `A^T y <= c`를 보장하지 않는다.
Original checker를 느슨하게 만들면 구조 충분성을 위조하므로 금지한다.
Optimal primal을 회수한19 first-timed attempts도 기존 dual로는 거절됐고
다른 existing Native dual로는 모두 통과했다. 올바른 인증이 존재한다는 것과
그 인증을 싸게 찾을 수 있다는 것은 다른 질문이다.

선택할 통합 가설은 **Goal-Conditioned, Certificate-Aware Perspective Discovery**다.
새 source/goal에서 필요한 정보, 유효 invariant, 충분 상태, certificate 생성,
실행/복원/fallback budget을 함께 고려한다. 최소 support membership loss를
개선하거나 solver ID를 선택하는 것만으로 이 기능이 생기지 않는다.

지금은 새 architecture를 구현하지 않는다. 변수를 줄여도 Strong Native보다
경제적인지를 아직 모르는 영역에 모델을 추가하면 North Star에서 멀어진다.
새 학습을 시작하려면 adequate representation, strong native headroom,
symbolic discovery의 residual gap, 구체적인 학습 결정, 권한/계보, independent
motif/composition 평가, 모든 실패 비용의 기록이라는7조건을 함께 충족해야 한다.

KEEP 자산은 기존 verifier/IR/native/proof/Perspective/experience/data rights다.
Variable cardinality는 확인된 표현 제약이나 단독 해결책으로 선정하지 않는다.
Relational model, compute-aware abstention, certificate-aware neural loss를
동시에 구현하지 않는다. 유일한 다음 우선 질문은 **무료 dual 없이도 충분
표현의 인증·실행이 강한 native보다 실제로 저렴한가**다.
