# Bottleneck causal matrix — v2.0

P1 원인분리는 복구 원본으로 보강했다. P1.2 validation12/12 stable LOO에도
typed compatibility10/12다. P1.5CSP4개는 실행 전 unsupported wire atoms,
P1.6실패7개는 exact hypothesis header/END다. 따라서 그 실패를 전부 의미
불가능으로 해석하지 않는다. 반면 P1.11.1raw-top6/12라 threshold-only로
required9/12에 도달할 수 없다. 최초 판정은 유지하며 format competence,
semantic competence와 비용을 별도 변수로 둔다(`P1_RECOVERY_REVIEW.md`).

Q34 실제 최초 자료의 귀속: 각 learned ranking의2m full-basis coverage40/48,
기존 residual ranking18/48이다. 실제8개 확대는2m에서 필요한 한 열을 놓친
경우와 정확히 일치한다. 기존 residual4m도48/48 basis를 담으므로 학습만이
충분 support를 찾는다는 해석은 배제한다. 그 경로의 실제 실행·총비용은
미측정이다. BP에서 answer-support와 certificate 관련 열이 달라지는 사실은
H1/H4의 목표 차이를 구체화하지만 단독 원인이나 새 학습 승인은 아니다.
`Q34_MECHANISM_ATTRIBUTION.md`와144 view/ranking 행을 참조한다.

추가원인분석: v08848원본은positive active support rank=m/dual nullity0이며
M10616원본은rank=m/8/nullity14~112다. 이상적인원래generator에서basis회수가
original dual까지유일하게완성하는논증은BP전이에서성립하지않는다.
이는H1목표/H2표현/H4인증을연결하는구조적조건변화다. 전체ranking실패원인,
새정확증명,cheap dual생성성공으로확대하지않는다.
`CERTIFICATE_GEOMETRY_CAUSAL_REVIEW.md`에원본별수치와논증을분리했다.

G0 A 후속결과: INCOMPLETE125jobs,등록family10배없음. 가장큰singleton
warmfloors에는적용가능한analyticnativecontrol이있다. 원래source/goal변조를
거절하는10engineeringtests만실행했고analyticcontroltiming은UNKNOWN다.
이는strongest-comparator부족의근거이며첫cohort를새기준으로재판정하지않는다.

**결정: HOLD_LEARNING.** 아래의 사실은 이미 보존된 opened 자료에서 얻었다.
인과 가설 여러 개가 함께 성립할 수 있으며, 자료가 없으면 UNKNOWN이다.

후속 H3 분석(optimizer/model 호출0회): 기존 quotient 함수와 v08848/M10616
원본을 사용했다. 학습 비용/residual 채널 std 중앙값.72693/.36115가 M106에서는
1.76e-16/1.63e-16으로 줄고,16/16원본에서 4개 채널만 열 사이에 변한다.
`q=1`일 때 affine residual이0이라는 식과 실제 ±열 대칭을 확인했다.
**feature shift의 구체적 근거**이며 H1과 분리한 학습 인과 검증은 아니다.
정확한 수치와 한계는 `FEATURE_TRANSFER_CAUSAL_REVIEW.md`에 있다.

Phase2 update: 별도 사전 등록된16opened source/576관측에서 C의free support는
64/64full fallback을 막지 못했다. D는5/16minimum-norm 인증에 성공했지만
11/16full dual LP 비용으로 전체 Native/D0.4837×였다. E의free dual 조건은
4.0913×,모든 후보10배0/16. **이 adapter의 인증 획득 비용이 경제적 병목**임은
실측으로 확인했다. 모든 인증 방법의 불가능성이나 새로운 학습의 성공으로
확대하지 않는다. H4의 비용 공백 일부를 닫았고 H1/H3학습 원인은 별도미입증이다.
H2단독 수정·새모델·Phase3투자는HOLD다. 아래 표는 최초Phase1 근거를 보존한다.

| 경쟁 가설 | 지지하는 실제 근거 | 단독 설명을 반증/제한하는 근거 | 혼동과 누락 | 새 실행 없이 내릴 판단 / 최소 다음 관측 |
|---|---|---|---|---|
| H1 Training Target Mismatch | v100 학습은 v88 reference basis membership BCE; 새 BP optimal nonzero support는m/8이고 sparse primal/dual goal에 대한 loss가 없음. M106 4m의18/32 first-timed 경로는 Native보다 primal 목적값이 나쁨 | 14/32는 최적 primal을 이미 회수. 회수한12경로는 인증 거절이므로 모델 목표 불일치만으로 전체 실패 설명 불가 | feature shift/cardinality와 얽힘. objective 변경의 matched 학습 ablation 없음 | target 불일치가 유력하나 유일 원인 아님. 이 단계에서 refit하지 않음 |
| H2 Fixed Representation Cardinality | 실제 certified Native nonzero s=m/8. top2m=16s/top4m=32s. v097 executor는len>=m 강제하여 정확 sparse support를 표현하지 못함 | 큰 shortlist에서도 충분 primal을 찾음. 더 작게 만드는 것만으로 전체 dual 인증 비용이 없어지지 않음 | sparsity·rank deficiency·multiple optima; 다른 정도의 sparse adapter 실제 비용 미측정 | 표현 제약은 확인됨, 경제적 개선은 UNKNOWN. 필요 시 C(무료 support+old)/D(sparse,dual 유료)만 같은 source 비교 |
| H3 Feature Distribution Shift | train dense basis/특정 conditioning vs M106 sparse paired X,-X. 표면 불변성을 가진 feature가 모든 goal-dependent 관계를 담는 것은 아님 | quotient는 v100/102 표면 invariance를 해결했고 M106에서도 일부 최적 support를 회수함 | 기존 feature가 의미 정보를 잃었는지와 BCE target 문제를 분리할 데이터 없음 | 분포 변화 존재; failure causality 단독 입증 못함. 새 relational 모델을 바로 만들지 않음 |
| H4 Certificate Asymmetry | available restricted232중224 original-rejected는 dual feasibility만 실패. first-timed19최적 primal/13path/7source에 기존 Native dual을 주면19/19 인증 | 다른 attempt의 primal 목적값 자체가 비최적, witness없는 시도24도 존재. certificate 문제가 전부 아님 | 원래 전체 dual을 싼 비용으로 얻을 수 있는지 UNKNOWN. 원래 checker 비용과 dual **생성** 비용은 다름 | 인증 연결의 실제 병목 CONFIRMED. 새로운 neural generator 투자 전에 유료 dual을 포함한 sparse 경로 경제성 확인이 필요 |
| H5 Native Solver Strength | M106 후보의 등록 ratio1.40179–2.11838, 모든 level transfer conjunction FAIL. 다른 G0들도 strong comparator 후 우위가 거의 사라짐 | v104 BP free support+dual에 제한된 경제적 상한 .633→.138. native가 모든 구조 여유를 없앴다고 할 수 없음 | v104와M106는 다른 input/hardware; 강한 L1 specialist 포함 여부 미확정 | 같은 Native로 fallback하는 현 구조는 중단. 학습 전에 가장 강한 적용 가능한 L1 방법과 동일 비용 권한 필요 |
| H6 Amortization Dependence | Q5 후보startup~7.9s vsDirect~1.15s, Q10000 계약. m64/128 wide영역 등114/176 comparable행 이득. M106startup후보~6.5s vsnative~1.09s | M106은 amortizedQ10000에서도 실패; startup만 지워서 전체를 성공으로 바꿀 수 없음 | training corpus/전역 배포/에너지/메모리 등 미측정. 다른 하드웨어 시간 합산 금지 | Q5 stationary break-even은 부분 비용의 조건부 분석. 운영 회수나 Frontier 경제성 입증 아님 |

## 사실·가설·미측정의 경계

- **확인된 사실**: bounded quotient support 성공; Q5 일부 넓은 영역의 비용 우위;
  M106 restricted dual 원래 조건 위반; sparse cardinality 계약 제약; full fallback
  비용; P1 의미 실패; recent strong baselines 뒤 headroom 부족.
- **유력 가설**: 다음 discovery 목표는 reference basis label보다 certifiable
  goal-sufficient state가 적합하다. 이 가설은 학습 성공이나10배 우위를 뜻하지 않는다.
- **미측정**: optimal support만 제공한 old2m/4m 경로와 sparse 경로에서
  original dual을 직접 얻는 complete 비용; 실제 Strong L1 baseline; learned
  generator의 미관측 motif 전이; Frontier와 같은 문제의 실제 capability.
- **배제할 수 있는 설명**: “M106은 단지 wrong primal만 만들었다”,
  “검증기 속도만 고치면 항상10배”, “P1 control 실패가 bounded LP 성공도
  무효화한다”, “surface invariance PASS가 새 구조 일반화를 입증한다”.

`M106_RETAINED_DIAGNOSTICS.csv/.json`의19번 offline native-dual 결합은 O 진단이다.
해당 dual을 runtime 입력으로 허용하지 않는다. Native 최적 support가 유일하다는
가정도 없다. 비용 분석은 원래 기록의 ms축에만 적용했다.
