# NEUMANN 1 — Evidence to Decision Master Review

2026-10-08 · Master Directive v2.0 · **HOLD_LEARNING**

추가 역사 복구에서 P1 최초ZIP8개/318entries를 확인했고 기존 model-free
replay7건을 통과했다. P1.7의 최초 replay 실패는 보존한다. P1.2의 안정적인
오분류, P1.5의CSP wire 거절, P1.6의header 거절, P1.11.1의raw ranking 오류를
서로 구분했다. P1.5산술4/4로 감사 표의 전사만 수정했다. Registry278rows와
21missing/intentional exclusions를 연결했다. `P1_RECOVERY_REVIEW.md`가 실제
복구 범위, 원본 hash, 독립 replay와 의미적 결론의 한계를 기록한다.

실제 Q34 최초 자료의 기여도도 복구했다. 24원본/48동등표현의192개 보존
witness를 원래 verifier로 확인했다. 두 frozen ranking은 각각2m에서40/48
표현의 positive basis를 전부 담았고, 빠진 한 열이 있는8표현과 실제4m
확대가 정확히 일치했다. 기존 deterministic residual ranking은2m에서18/48,
4m에서48/48을 담았다. 학습의 확인된 기여는 작은 shortlist의 집중도이며,
미실행 deterministic4m 경로의 capability·총비용은 UNKNOWN이다. 이 분석은
새 solver/forward 없이 수행했고 원래 Q34 PASS를 변경하지 않는다.
`Q34_MECHANISM_ATTRIBUTION.md`가 출처·계보·귀속의 한계를 연결한다.

후속5시간작업: 사전등록한G0 A 확률native125jobs를실행·export·독립확인했다.
첫cohort는INCOMPLETE(361exactPASS/14NOT_VERIFIED,9SIGSEGV/15timeouts)이며
등록two-bin10배family는없다. singleton22.55x/53.09x는무료floor와Storm만의
비교이고적용가능한classicalanalyticcontrols도있다. 전역capability/learned
economics성공으로취급하지않는다. G0 B의첫INCOMPLETE와학습HOLD도유지.
원본·실측·원인·규칙은`docs/research/g0_probabilistic_native_2026-10-08.md`참조.
현재registry278행/185문서nodes이며추가2행도독립fresh실험수로합산하지않는다.

원래LP성공의certificate조건을복구했다. training48개positivefull-rankbasis는
dual을유일하게정하지만M10616개의sparse support는14~112차원dual자유도가
남는다. 모델forward/optimizer없이기존source·witness로확인했다. 좋은answer
support와저렴한originalcertificate에충분한표현은같은것이아니다.
`CERTIFICATE_GEOMETRY_CAUSAL_REVIEW.md`와64원본CSV/JSON이추가근거다.

후속 감사 교정: 초기 제목 필터가 NEUMANN 이름이 없는 linked Notion 버전
문서24개를 놓쳤다. child UUID를 따라 복구했고 v2–4 개별 engineering 보고서를
연결했다. 당시 registry는276행이었으며 행 수를 독립 실험 수로 해석하지 않는다.
최초 Phase1 251행의 frozen verdict와 source hash는 모두 그대로임을 확인했다.
main/Core1/v2/v3/v4 다섯 page는 live 읽기 전용 응답도 보존했다.
`NOTION_SUPPLEMENT_VERIFICATION.json`에 범위·hash가 있다. 원본 Git 실행은
미확보이고 문서가 보고한 결과를 raw replay로 승격하지 않았다.
v2의1,000반복 toy timing은 assignment1.919배/shortest3.119배 더 느렸으며,
v3의약한 exhaustive comparator 대비 crossover와 v4의family classifier는
새 구조 생성·강한 native 우위의 증거가 아니다.

추가 feature 분석은 원본 v08848개/M10616개를 사용하고 새 forward/solver는
0회였다. 비용/residual 두 채널이 BP ±열에서 수치적으로 상수로 바뀌는 것을
확인했다(`FEATURE_TRANSFER_CAUSAL_REVIEW.md`). H3의 구체적 근거를 보강하지만
H1/H4와 분리한 단독 인과성이나 모델 교체의 필요성을 입증하지 않는다.

후속 Phase2 업데이트: 아래 Phase1 분석이 제안한 certificate economics의
작은 opened 판별을 별도 사전 등록하고 실행했다.16원본/576관측 최종 정답과
독립 replay가 모두 통과했다. D무료 support+유료dual의 Native/D0.4837×,
E무료 support+dual4.0913×,각 후보10배0/16. 이adapter의 dual획득 비용을
실측으로 확인했고 v2.0중단 규칙에 따라 **Phase3/학습HOLD**를 유지한다.
상세실측·범위·원본은 `docs/research/bp_certificate_diagnostic_2026-10-08.md`,
파생분석은 `BP_CERTIFICATE_DIAGNOSTIC_ANALYSIS.json/.csv`에 있다.
아래는 당시Phase1 결과이며 그 최초bytes/hash도 별도snapshot에 보존했다.

이번 감사의 핵심 결론은 v0.0.102의 성공을 일반화 불가능으로 폐기하거나,
M106 실패를 단순한 모델 정확도 문제로 설명하면 안 된다는 것이다. v102는
구성된 LP에서 **유용한 support를 순위로 제안하고 solver가 완성하게 하는**
한정된 학습 메커니즘을 입증했다. M106에서는 일부 support가 이미 최적
primal을 포함했는데도 **축소 문제에서 얻은 dual이 원래 문제를 인증하지
못해** fallback으로 돌아갔다. 구조 회수·인증·실행·초기 투자를 각각 다뤄야 한다.

이 감사는 새로운 LP/모델 성능 실험이 아니다. 기존 원본의 정확한 바이트,
보존된 수치 witness, 실행 기록과 코드만 사용했다. 새 optimizer 호출,
model forward, 데이터 생성, GPU 학습은 0회다. 원본 판정은 바꾸지 않았다.

## 1. 저장소와 감사 범위

읽기 전용 GitHub 확인 시각과 원본 응답 요약은
`REPOSITORY_STATE_FIRST.json`에 있다. main은
`55178a211962caf5ce677deb37edd30bfb4fdccc`, 연구 HEAD/#175는
`fb23dca002bbd50c96e0c766369269a0b7fcc7a6`, #174는
`a0119180e743f5115b21847fdb6ac6741f97bbe2`다. #174 OPEN,
#175 DRAFT/OPEN이며 #174가 #175의 조상이다. exact HEAD의 7 workflow가
SUCCESS인 사실은 코드 CI이고 과학적 성공이 아니다. 신규 변경은 로컬이며
그 변경에 대한 원격 CI는 실행하지 않았다. commit/push/merge/release 없음.

main 대비 #175는 290개 파일, 56,648 insertions/21 deletions의 큰 변경이다.
#174의 17개 파일이 ancestry에 포함되어 있으므로 #175만 독립 변경으로
병합하면 안 된다. 과거 open PR까지 14개를 확인했고 11개 다른 버전 문서를
exact head에서 읽어 현재 문서와 별도 연결했다. #44의 v0.0.39는 main/현재
HEAD에 없는 preregistration이다. inspected branch에 최초 결과는 없으므로
실행했다고 기록하지 않았다. 자동 병합과 과거 증거 재작성은 하지 않았다.

17개 #174 파일은 #175 HEAD에서도 Git blob이 모두 동일했다
(`PR174_OVERLAP.json`). 14개 PR head의 check-runs도 재조회했고 반환된
check는 모두 SUCCESS였다(`OPEN_PR_CI_FIRST.json`). Check 수와 workflow 수는
다를 수 있으며, 이 성공이 각 PR의 연구 가설 통과를 뜻하지 않는다.

`EXPERIMENT_REGISTRY.csv`는 연구 문서, 최초 결과 event, 미확보 버전,
unmerged 문서 variant를 함께 인벤토리화한다. 행 수는 실험 수나 독립 문제
수가 아니다. `EVIDENCE_LINEAGE.json`은 정확한 문서 hash, 공개 결과 metadata,
모델 계보, 기존 D0 index와 과거 decision ledger를 연결한다.
`HISTORICAL_SOURCE_REVIEW.md`는 버전별 가설·결과·다음 결정의 실제 발췌다.
원본 수치까지 재검증한 범위와 문서만 확인한 범위를 구별했다.

## 2. 전체 연구 연대표와 누적 지식

| 범위 | 실제로 배운 것 | 보존할 자산 / 후속 의사결정 |
|---|---|---|
| 초기 v0.1–v0.5.1 | 로컬 Notion snapshot은 구조 재사용, Level S/P, 600문제 비복원 stream, bootstrap 중복 방지, v0.5.1 errata를 설명한다. 별도 원본 revision/완료 실행은 미확보 | 연구 charter와 annotation 설계; EXTERNAL_EVIDENCE_REQUIRED를 성공으로 채우지 않음 |
| Core v0.0.1–5 | v1 Notion의 6 tests·toy primitive 감소와 v5 Git README의 14 tests·coarse family 분류 | typed IR·solver·verifier·UNKNOWN; v2–4 별도 최초 기록은 미확보 |
| v6–10 | OOD 거절과 coverage tradeoff; controlled 원문→IR; learned family proposal은 deterministic compiler 승인 필요 | 의미 추출과 계산 정답의 분리; 일반적인 표현 생성 입증 아님 |
| v11–25 | adapter registry, manifest, revocation, process separation, persistent workers, state hygiene/attestation | 유용한 runtime 기반. v21 약2394배는 거의 일이 없는 lifecycle fixture이며 지능 계산 우위로 확대 불가 |
| v26–31 | representation 재사용과 작은 matched MLP/Transformer의 answer vs family objective 차이 | 2×2 controlled 문제의 제한적 능력 차이. 뒤 v76–77에서 동등한 direct program/zero-model compiler도 충분함을 확인 |
| v32–35 | 정확 선형 축약, 학습 dependency proposal, reference-label F1과 solver utility의 불일치 | exact checker와 Value-of-Reduction; v33 post-result control/최종 보고를 최초 측정과 구별 |
| v36–40 | residual greedy의 경로 의존성; coupled-block 표현의 필요성; incidence component가 discovery를 포화 | 더 큰 모델 대신 deterministic baseline 유지. v38 H4 실패와 v38.1/39 교정 계약은 서로 다른 기록 |
| v41–49 | nonunit parser/충돌/row index/Schur repair/cache를 인과적으로 분리. v45 축약이 더 커져도 비용 1.060/1.487배로 악화 | 기존 exact algebra·index 재사용. v49 matched topology contrast에 cost reversal이 없어 gate 학습 중단 |
| v50–57 | bounded order search가 greedy를 못 넘거나 실제 matrix RCM 이득 부족. 반복 복제본의 factorization 재사용은 되지만 원본 matrix stream의 reuse 조건은 실패 | 강한 native·cache 권한. v55 invalid 원본과 v56 corrective를 별도 보존 |
| v58–65 | native presolve가 대부분 처리; LP relaxation과 원래 MIP capability 구별; SEMI decomposition은 미완성 | original model checker·warm-start 기술. native가 이미 수행한 축약을 새 원리로 주장하지 않음 |
| v66–67 | rank-one contingency reuse는 약.2201 candidate/direct local ratio. 강한 batched comparator 뒤 추가 routing 가치는 제한 | 기존 LODF/배치 계산을 강한 기준선으로 흡수; 새 지능·일반 scaling으로 확대 불가 |
| v68–80 | affine learned total-cost FAIL, strong numerical direct가 약346–352배 빠름. graph DP의 bounded twin 이득은 고전 기법. independent checker/lifecycle 교정. SVAMP arithmetic·relational planning은 학습 투자 거절 | original checker, matched tools, complete-cost contract. v70 capability-unreached의 censored 시간은 speedup 아님 |
| v81–87 | original primal/dual certificate 구축. norm shortcut은 정규화 후 사라짐. classical portfolio/동등 executable Direct/warm start/무료 compaction 상한 검사 | 정확한 비교 권한과 LP verifier. v87 최초 confounded archive 유실을 corrective 결과로 대체하지 않음 |
| v88–96 | 큰 GNN/early pruning/model swaps는 cost·exact-basis gate 실패. 2m에는 reference basis가 거의 있어도 exact-m head가 인증 실패 | v96가 exact basis 예측 목표를 반증; solver가 shortlist를 완성하게 하는 방향으로 이동 |
| v97–102 | support-system tournament, quotient 불변성, verifier-triggered4m로 bounded Q34 fresh PASS | 두 frozen checkpoint와 valid support executor 보존. 인간 설계 quotient/표현 목록을 스스로 발견했다고 말하지 않음 |
| v103–104/M106 | scaling 일부 영역 이득·전체 FAIL. BP free support+dual 상한과 frozen transfer FAIL을 분리 | 비용 envelope·primal/dual provenance. 아래 실제 원인 분석 |
| v105–106/repair/Decisions | North Star namespace 동결; Runtime interface·CPU 병목; Decision2는 action에 도달 못함 | original task verifiers·resource receipts. 원래 구조 executor는 D2에서 실행되지 않음 |
| P1–P1.13 | format stability, semantic competence, feasibility, 역할 의미는 다른 문제 | 반례·parser·deterministic pruning 보존. 반복된 모델명 교체 연구는 HOLD |
| 최근 G0/기호/재귀/tensor/guarded | 목표 보존 표현은 승인되지만 강한 native가 거의 같은 일을 함 | IR·universal/guarded proof·source-bound OCaml·공개 기호 기준선. 증명 PASS ≠ 비용 PASS |
| Structural Experience | 335관측→181경로 그룹,32 public 투영,31 unique native 경로,13 topology | provenance·반례·비용. 독립 fresh 학습문제 수가 아님 |
| 이번 native 준비/Counting | 정확 native/prototype 기반 구축; counting12/17 완료,5 generation timeout,완료12개10배0개 | 최초 archive·불완전성 보존. 디버그 출력/측정 경계 때문에 counting 전체의 불가능성으로 확대하지 않음 |

각 버전의 실제 질문·수치·변경·허용 주장·다음 결정은 registry와 source review에
연결했다. 모든 최초 raw 자료를 확보했다고 주장하지 않는다. 초기 research
revision, P1 원본 ZIP 11개, v100/101 coefficient arrays, 유실 OCaml5 등의
제약은 `MISSING_EVIDENCE.md`에 있다. 봉인 자료는 복구 대상에서 제외했다.

## 3. v0.0.102가 성공한 계산 메커니즘

Original LP → analytic observable quotient → frozen learned column ranking →
top2m restricted original LP → full original primal/dual check → on rejection
top4m → charged full Direct fallback.

1. **Quotient normalization**: signed-row/positive-column equivalent views의
   표면 드리프트를 제거했다. v100 matched refit에서 OLD top-support parity는
   두 seed 모두0/16, QUOTIENT는16/16이었다. 이것은 인간 설계 특징의
   불변성 이득이고 모든 미지 구조에 대한 표현 학습 입증은 아니다.
2. **Learned ranking**: 433-scalar pointwise MLP는 각 column의 8개 observable을
   입력으로 opened v88의 reference optimal basis membership을 weighted BCE로
   학습했다. 새 변환 언어·IR·불변량·goal-conditioned certificate를 생성하지
   않았다. 그 학습 지식은 **그 생성 분포에서 optimal-basis 가능성이 높은
   column의 점수화**라는 범위로 설명할 수 있다.
3. **Cheap baseline 대비 가치**: v97의 같은 opened16개에서 deterministic route는
   utility .320260, complete/direct .735660,10/16 fallback-free였고 point는
   .909057/.212278/16/16이었다. 제한된 matched 개발 근거다. v102 QUOTIENT
   fresh 성공에서 학습과 모든 더 강한 deterministic 개선의 기여를 각각
   분리한 새 ablation은 없다. 무조건 학습만의 우위로 확대하지 않는다.
4. **2m→4m**: exact basis를 직접 예측하지 않고 native solver에게 마무리를
   맡겼다. v101 같은32 views의 FIXED2는 seed마다28/32 fallback-free,
   EXPAND4는32/32였고4/32만 확대했다. 독립 검증 실패가 확대를 촉발해
   드문 expensive full fallback을 낮은 추가 비용으로 회복했다.
5. **경제성**: v102의24 independent originals/48 views에서 seed별 utility
   .821688/.822772, burden .021855/.021960, Q=10000 상각 complete/direct
   .238921/.237998이었다. 각 seed48/48 valid,8/48 expanded,full fallback0.
   약4.2배의 해당 계약 비용 이득이며 Frontier/Q1–Q7 전역 완료는 아니다.
6. **범위**: label은 구성된 LP의 oracle basis에서 왔다. feature/form/cardinality/
   solver/수치 인증/상각 가정이 고정됐다. 임의 목표를 이해해 새로운 충분
   상태를 만들거나 certificate 비용을 학습한 증거는 없다.

따라서 성공을 보존하면서도 North Star가 아직 미입증인 이유를 설명할 수 있다.
학습한 ranking은 한 구성 분포에서 유용했고, runtime의 자유 언어 의미 이해,
새 representation program 생성, 다른 최적성 인증 구조에의 전이는 별도 능력이다.

## 4. Scaling: 실패 판정 안의 실제 성공 영역

`LP_SUCCESS_ENVELOPE.md/.csv/.json`은 모든96 views×2 checkpoints=192행을
기존 원본에서 파생했다. 16행은 Direct capability가 없어 speedup과
break-even을 null로 남겼다. 비교 가능한176행 중114행은 등록 비용이
Direct보다 낮다. 이것은114개 독립 문제나 전체 Q5 PASS가 아니다.

넓은 m64/128 LP에서 이득이 유지됐고 작은 m32는 discovery burden,
m256 width16 surface는 utility, m256 width32는 Direct5초 capability가
등록 conjunction을 막았다. width1 control에는 투자 회수 이득이 거의 없다.
초기 비용은 후보 약7.9초,Direct약1.15초이고 원본 fit/setup도 추가된다.
같은 요청이 반복된다는 조건부 회수량은 큰 넓은 LP에서 낮아지지만,
누락된 training corpus/모델 배포 투자까지 포함한 운영 실증은 아니다.

## 5. M106: 추가 실행 없이 확인한 병목

16개의 기존 opened source gzip/decoded hash를 원래 manifest와 확인했다.
현재 v081 verifier를 그대로 사용해256 final witnesses와232 retained
restricted witnesses를 원래 A/b/c에서 재검사했다. 원래256 final acceptance와
8 restricted acceptance를 재구성했다. 나머지24 restricted 시도는 witness가
없고 accepted로 추정하지 않았다. optimizer/model은 호출하지 않았다.

| 원본에서 확인한 사실 | 실제 수 | 의미 |
|---|---:|---|
| 전체 candidate 호출 |128 (16문제×2seed×4warm/timed)|독립128문제 아님 |
| full fallback |120/128|유효 최종답의 대부분이 기존 full solver에서 옴 |
| available rejected restricted witnesses |224/232|거절 축은 모두 **original dual feasibility** |
| Native 최적값과 같은 primal인데 거절 |76 시도(반복 포함)|primal 회수 실패만으로 설명 불가 |
| 첫 timed repeat에서 위 현상 |19시도,13후보경로,7원본|warmup repeat0와 timed repeat0를 구별 |
| 기존 Native dual로 위19개 primal 인증 |19/19|목표를 보존하는 충분 primal은 존재; dual 획득 비용은 UNKNOWN |
| Native witness nonzero support |2/4/8/16 (m/8)|2m/4m은16/32배 큰 집합; 최소m executor 계약은 sparse support를 못 표현 |

2m 첫 timed32경로 중26개는 restricted witness를 얻었고7개는 최적 primal을
얻었으나 모두 original certificate가 거절됐다. 4m은32개 중14개가 최적
primal을 얻었고2개만 인증됐다. 다른18개는 목적값이 달랐으므로 discovery
손실도 존재한다. 하나의 원인으로 전체 실패를 설명하지 않는다.

같은 source의 기존 certified Native witness를 사용했다. planted feasible
support를 optimal이라고 가정하지 않았다. Native support도 유일한 optimum을
증명하지 않으므로 특정 support 누락 자체를 불가능성 증거로 쓰지 않았다.
수치 LP 검증은 frozen atol/rtol1e-8의 backward-error 의미이며 exact formal
proof가 아니다. offline Native dual 결합은 무료 Oracle 진단이지 실행 정책이 아니다.

각 후보의 등록 amortized/native envelope 비율은1.40179–2.11838로 비용
우위가 없다. startup만 제거해도 실패한 두 restricted solve+full fallback은
무료가 아니다. v104는 다른 input/hardware에서 support와 optimal dual을
함께 무료 제공했고 BP oracle/direct .633/.378/.217/.138이었다. 그 수치에서
M106의 비용을 빼서 dual의 인과적 비용을 추정할 수 없다.

## 6. Runtime와 P1 결과의 올바른 압축

Decision2 공식 FAIL(모든 arm0/12)은72 calls 모두 thought256tokens를
생성하고 final action을 못 내보낸 자유 생성형 제어 실패다. TOOL/NEUMANN
실제 구조 실행은0. 더 큰 token budget으로 원래 결과를 교체하지 않았다.

P1/1.1은 verbalizer/permutation, P1.2 development PASS는 Full-S4 안정성,
validation FAIL은 stable-but-wrong semantics였다. P1.3 contract dispatch는
결정론적으로 되지만 새로운 intelligence는 아니다. P1.4–6은 serialization
거절과 실제 잘못된 산술·제약이 섞여 있다. parser를 넓혀도 의미 오류가
사라진다고 가정하지 않는다. P1.7–10은 feasibility pruning/호출 절감이
잔여 의미 판단을 해결하지 못했고 P1.10은 INCOMPLETE다. P1.11은 identity
NOT_EVALUATED, 11.1 accepted3/12, P1.12 7/12, P1.13 NLI5/12 대 incumbent3/12로
모두 요구 능력 미달. 새 P1.x 모델 교체는 HOLD한다.

이 의미 router 실패가 LP ranking의 제한적 성공을 무효화하지 않으며,
LP 성공도 일반 언어 목표 이해를 대신하지 않는다.

## 7. 최근 구조 연구와 선행 알고리즘의 경계

Graph/SPD free 구조 기하평균1.077/1.129배, polynomial/inductive의 강한
symbolic complete 비교, recursive20개에서1.005/1.002배, Guarded fixture의
operational약1배는 해당 조건에서 학습 여유가 작다는 결과다. verification+
compile을 가상으로0으로 둬도 recursive약1.05배였으므로 verifier 최적화만으로
10배가 된다는 연구에는 추가 투자하지 않는다.

Tensor 초기16.84 modeled ratio는 cotengra 후1.30으로 줄었다. 원본4개 배열의
최대 실행 component3.45배는 all-in/new-learning evidence가 아니다. SuFu
290개 자체 실행183 bounded success/105timeout/2errors, stress373반례는
원래 저자 domain 밖의 반례를 포함하므로 논문 공식 점수 재판정이 아니다.
Synduce/OCaml, SMT, SymPy, egglog, opt_einsum/cotengra, Storm,
D4/CPOG/Ganak의 기능을 NEUMANN 발명이라고 부르지 않는다.

이번 counting 첫 archive는17 opened public CNF에서12 완료/5 certificate
generation timeout의 INCOMPLETE다. 완료 subset native/free geomean.4393,
최대4.0204,10배0/12. 원본 상위 C checker가 -v0에도 clause lookup debug
로그를 대량 출력했고 harness wait polling도 작은 시간의 해석을 제한했다.
같은 pipeline 학습은 HOLD지만 모든 counting 표현의 no-headroom 증명은 아니다.
Lean formal build240초 timeout과 Polar 공식 pin의 binary dependency 설치
실패(progress1.6)을 보존했다. 두 공식 smoke/formal 실행을 했다고 기록하지 않는다.

## 8. 기술 부채와 실제로 재사용할 것

KEEP: 원래 LP verifier, native warm-start/shortlist 실행기, representation IR,
universal/guarded certificate, recursive summary/source binding, Perspective
계약, budget/data-rights/lineage, independent replay, 구조 경험과 strong native
catalog. 기존 source pin이 있는 모듈을 새 이름으로 복제하거나 수정하지 않았다.

ARCHIVE/HOLD는 물리 삭제가 아니다: 실패한 P1 controller/model swaps,
포화된 affine/graph/tensor/recursive 후보의 추가 학습, 중복 실험 runtime,
끝난 benchmark의 변형 증식. 기존 코드는 재현을 위해 남겼다. 이번 추가 코드는
registry/기존 LP 분석뿐이다. giant IR/GPU pipeline/새 일반 증명기 없음.

REFRACTOR는 실제 필요할 때만 한다. 가장 중요한 결함은 공통 형식 부족보다
**primal structure discovery와 original-goal certificate economics 사이의 연결**이다.
더 많은 uniform interface를 작성해 이를 지능 발전으로 대체하지 않는다.

## 9. 하나의 연구 결정

**HOLD_LEARNING.** 추가 P1/refit·LP 반복·G1/G2를 시작하지 않는다.
현재 자료가 지지하는 deterministic 정책은 M106 범위에서 **항상 Strong Native를
사용**하는 것이다. 같은 원본 비용표의 후보 두 개보다 모든16문제에서
등록 complete 비용이 낮고 같은 최종 capability를 달성한다. 이를 learned
abstention이나 unseen generalization으로 부르지 않는다.

추후 경제적 여유가 확인될 때 검토할 단일 learning target은 **원래 목표를
싸게 인증할 수 있는 충분 표현의 발견**이다. support label 재현만을 학습
목표로 삼지 않는다. 선택하지 않은 variable cardinality/relational model/
compute-aware policy를 동시에 구현하지 않는다.

지금의 HOLD 결정에는 추가 성능 실행이 필요 없다. dual을 무료로 주지 않고
정확 support가 실제로 경제적인지를 알려면 user v2의 C/D/E 진단과 강한 L1
native가 같은 환경에서 필요하지만, 비용 여유/강한 baseline/실행 계약을
동결하기 전에는 실행하지 않는다. 다음 단 하나의 후보 실험은 그 **certificate
economics 진단**이다. 이것이 현재의 불확실성 목록이며 성공 약속이 아니다.

세부 경쟁 가설과 다음 판단은 `BOTTLENECK_CAUSAL_MATRIX.md`,
`NEUMANN_ARCHITECTURE_GAP.md`, `RESEARCH_DECISION.md`에 있다.

## 10. 검증과 재현

`build_registry.py`는 문서/정확 PR blob/공개 결과 metadata만 읽는다.
`analyze_retained_lp.py`는 허용된 M106/Q5 원본과 기존 verifier만 사용한다.
sealed Decision3/v098/v107 payload는 읽거나 hash하지 않았다. 원본 파일
변경 여부, warmup/독립성, break-even 경계와 금지 실행을 관련 테스트로 확인한다.
이번 감사 결과의 실행 로그와 테스트 결과는 `VERIFICATION.json`에 기록한다.
새 출력은 파생 분석이며 원래 frozen evaluator 결과를 덮어쓰지 않는다.
