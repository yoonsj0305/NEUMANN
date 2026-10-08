# Opened BP certificate economics — v2.0 Phase 2 first result

**ENGINEERING PASS / NO REGISTERED TENFOLD HEADROOM / HOLD_LEARNING.**

이 판정은 아래16개 opened source와 등록한 실행·인증 방법에 한정된다.
v102 Q34 PASS, Q5/M106/Decision2 FAIL은 그대로다. 새 G0·G1·G2 성공,
학습된 표현 생성 또는 프런티어 성능을 입증한 결과가 아니다.

## A. Repository and immutable first evidence

Base main55178a211962caf5ce677deb37edd30bfb4fdccc,
local research/#175fb23dca002bbd50c96e0c766369269a0b7fcc7a6.
#174 ancestry와 #175 DRAFT/OPEN 상태를 보존했다. 새 commit/push/PR/merge/Notion
write는 없다. 기존 HEAD CI 성공은 새 로컬 변경의 CI가 아니다.

새 변경: CPU 진단 runner `experiments/bp_certificate_diagnostic.py`,
`tests/test_bp_certificate_diagnostic.py`, frozen preregistration,
`research/audit/analyze_bp_diagnostic.py`, 분석 JSON/CSV와 이 보고서.
기존 verifier/native/support/최초 결과 파일은 수정하지 않았다.

최초 측정 이전7:17:14UTC에 계약을 동결했다.
계약 파일은 `docs/experiments/bp_certificate_diagnostic.preregister.json`이다.

- Contract SHA256: `5fbce4a2bedd22833f4c9b47cf502c44642cc5b8477cfab32ba7fdc23aa3db13`.
- Runner SHA256: `e6a7084f617b184264359128d3a42931756ae62e65ddfc1cff8ae635b0d194cf`.
- First report SHA256: `2b99aff89dbe4f64a7fa6a72d6e85767dcba07190be87b298ddc9dd7440118bc`.
- Original M106 report: `fd0f069bb43c8f4f471578de35a6f70af2c418b46b701260f12cd1d27bebd6b8`.

Local first evidence:
`NEUMANN 1/Continuation/BP_CERTIFICATE_DIAGNOSTIC_2026-10-08/first/`.
최종 로컬 검증 receipt는 `research/audit/PHASE2_VERIFICATION.json`에 연결한다.
독립 replay, 실행 stdout/stderr, 동결 전 draft, 최종 계약, dependency 설치와
20-test engineering receipt도 같은 상위 폴더에 있다. Phase1 감사 원본은
`Continuation/MASTER_RECOVERY_V2_2026-10-08/phase1-audit-snapshot/`에 별도로
보존했다. 재실행·유리한 반복 선택·임계값 변경은 없었다.

## B. Hypothesis and authority

목표: 원래 최적 support를 알면 dual을 무료로 받지 않고도 강한 Native보다
충분히 저렴하게 원래 문제를 풀 수 있는가? fixed2m/4m의 표현 제약과
full-goal certificate acquisition 비용을 구별한다.

이미 열린 M106 원본16개(k8/16/32/64각4개)를 그대로 읽었다. 재생성하거나
planted feasible support를 정답으로 사용하지 않았다. 원래 Native witness가
변경 없는 original verifier를 통과한 후 그 witness의 정확 nonzero support를
Oracle label로 사용했다. 유일한 최적 support라고 가정하지 않는다.

Nine routes,1warmup+3timed repeats=576관측. 독립 원본은16개이고 fresh는0개다.

- A: 기존 Highs primal simplex, SciPy highs-ipm, 고전적 explicit dual LP,
  SPGL1 BP+동일 sparse/KKT/dual repair. 모든 경로에 동일 목표 검증 권한.
- B: 두 frozen checkpoint의 **보존된 ranking**+기존2m->4m+full fallback.
  새 forward 없이 discovery를 무료로 준 LOWER BOUND. 실제 모델 총비용 아님.
- C: 정확 optimal support를 먼저 놓고 원래 column 순서로 padding한 ranking,
  기존2m->4m+fallback. optimal dual 없음.
- D: free support+sparse least-squares primal+minimum-norm KKT dual. 거절되면
  기존 HiGHS로 full original dual feasibility를 구한다. free dual 없음.
- E: D와 같은 sparse primal, free retained optimal dual. 낙관적 Oracle 진단.

각A variant의 모든 반복이 인증된 경우의 가장 빠른 비용을 원본별 envelope로
비교했다. 이 optimistic envelope는 실제로 무료 router를 배포했다는 뜻이 아니다.
실제로 이번16개에서는 기존A_NATIVE가 모두 가장 빨랐다. SPGL1도 실행·실패·
fallback을 보존했으며 사후에 비교군에서 삭제하지 않았다.

## C. Minimal implementation and proof scope

기존 `solve_native_checked`, `adaptive_support_checked(factors=(2,4))`, 원래
`verify_standard_form_certificate`, first-attempt event chain/gzip/hash를 재사용했다.
정확 support를 sparse least-squares로 복원하고 full original dual을 구하는
최소 진단 연결만 추가했다. 모델/큰IR/새solver/새증명기는 없다.

`A_S x_S=b`, `A_S^T y=c_S`, `A^T y<=c`가 원래 LP의 primal/dual 목표를
보존해야 한다. 최소 노름 후보나 native solver의 success label만으로 승인하지
않는다. 기존 atol/rtol1e-8 original numerical verifier가 유일한 권한이다.
수치 backward-error 인증이며 exact formal proof는 아니다.

고전적인 least-squares/KKT/LP 및 SPGL1을 NEUMANN 발명이라고 주장하지 않는다.
기존 [SPGL1 BP](https://spgl1.readthedocs.io/en/latest/api/generated/spgl1.spg_bp.html),
[SciPy HiGHS](https://docs.scipy.org/doc/scipy/reference/optimize.linprog-highs-ds.html),
[HiGHS Python](https://ergo-code.github.io/HiGHS/dev/interfaces/python/)을 재사용했다.

## D. First actual results

**576/576 final original-valid within5s**, 독립 original-goal replay576/576PASS.
새 model forward0, training0, new task generation0. CPU solver 호출은 이 별도
Phase2 계약에서 실행됐다. Phase1의 zero-solver audit와 구분한다.

아래는16 source별 median에 common startup/dependency setup을Q10000으로
상각한 operational cost의 **StrongNative / 경로** 기하평균이다.
1보다 작으면 해당 경로가 Native보다 비싸다. 전체 lifecycle cost는 UNKNOWN다.

| 경로 | 기하평균 | 10배 원본 | full Native fallback 요청 |
|---|---:|---:|---:|
| B frozen ranking seed100001, discovery free |0.6943×|0/16|60/64|
| B frozen ranking seed100002, discovery free |0.6978×|0/16|60/64|
| C free optimal support+old2m/4m |0.7254×|0/16|64/64|
| D free optimal support+paid original dual |0.4837×|0/16|0/64|
| E free optimal support+free optimal dual |4.0913×|0/16|0/64|

E의 원본별 최대 비율은7.5494×다. 등록 조건(전16개 능력 유지,
geomean>=10,13/16>=10)을 충족하지 못했다. D는 원래 문제의 유효한
certificate를 생성했지만 전체 비용은 약2.07배 높았다. E는 저렴하지만
원래 optimal dual을 무료로 공급한 진단이다.

### Actual certificate bottleneck

D의 minimum-norm KKT dual은5/16독립 원본에서 통과했다. 나머지11/16은
full dual-feasibility LP가 필요했다(64회 반복 중44회). D의 timed stage
중앙값은 primal refit0.136ms,minimum-norm dual0.087ms,original check합계
0.700ms,full dual feasibility104.757ms다. **서로 다른 stage 중앙값을
더해 total을 만들지 않는다.**

큰 k64의4개 원본에서 D의 Native/D는0.1064–0.1393×였다. free support가
정확해도 이번 인증 획득법은 Native보다 약7.2–9.4배 비쌌다. 반면 minimum-norm이
통과한5개는 약1.91–3.52배의 국소 operational advantage가 있었다. 모두
실패했다고 합치지 않으며, 등록된10배 목표 미달 판정도 유지한다.

C는64회 모두 free support를 포함했지만 restricted dual이 original goal을
인증하지 못해 full fallback으로 돌아갔다. cardinality 변경만으로 인증 문제가
해결된다는 가설은 지지되지 않는다. B도 두 seed 각각60/64fallback이었고,
discovery를 무료로 줘도 같은 executor의 경제성이 회복되지 않았다.

SPGL1은 같은 인증 복구 권한에서56/64primary 성공,8/64full fallback이었다.
최종64/64는 원래 문제 검증을 통과했지만 이번 precision/threshold/구현 조건에서
Native보다 느렸다. 실패한2개 source의 threshold를 조정하거나 재측정하지 않는다.

## E. Costs, tests and limitations

Windows11 Intel64 Family6 Model165,12logical CPUs,수치1thread.
Python3.12.14,NumPy2.4.6,SciPy1.17.1,Highspy1.15.1,SPGL1 0.0.3.
Highspy/SPGL1은 격리된 로컬 deps에1.792초 동안 설치했고 기존 venv와
과거 Linux runtime은 변경하지 않았다. 과거 Linux 시간을 여기에 더하지 않는다.

Scientific execution wall124.162초,parent포함124.513초,최초 independent
replay11.455초였다. 이는576개 독립 문제의 비용이 아니다. 공통 import/authority
startup과 dependency setup을 모든 경로에 동일하게 기록하고 Q1과Q10000을
구분했다. Cold는 이 진단 프로세스의 공통 구동이며, 최적화한 각 deployment의
구동 측정이 아니다. training,R&D,FLOPs,energy,peak memory,money는UNKNOWN다.

request에는 원본 read/gzip/hash/decode,실패 후보/dual생성/fallback,원래 문제
검증,동일한 최소 response serialization을 포함한다. 과학 archive의 fsync와
후처리는 request에서 제외하고 연구 wall을 별기했다. answer cache나 무료
factorization 재사용은 없다. E의 query중앙값6.098ms,decode중앙값5.197ms는
입력 처리 계약의 영향을 보여준다. 두 중앙값을 빼서 새 speedup을 선언하지
않는다. Warm/in-memory의 다른 계약으로 판정을 바꾸거나 E에만 입력 cache를
허용하지 않는다.

실행 전20개 engineering/regression testsPASS: below-m sparse state,false
support,wrong/free dual,payload mutation,budget,dual sign recovery,Oracle범위,
warmup/coverage,censored INCOMPLETE,SPGL grammar. 완료 후 optimizer/SPGL/native를
금지한 replay에서576final witness와 전체 summary/identity/late acceptance를
확인했다. 추가 causal analysis에서도 false primary authorization과 D의
Oracle dual 누출은0이었다.
후속 관련 회귀 검사도 **35개 PASS(4.04초)**였고, 기존 코어·최초 결과와
decision ledger에 대한 Git diff가0임을 확인했다. 새 로컬 변경의 원격CI는 없다.

## F. Causal decision and Phase 3

**HOLD_LEARNING**. 고정 support ranking의 refit,larger model,sparse executor를
저렴하게 만들기 위한 학습,새 P1변형에 투자하지 않는다. 확인한 사실은 이
표현·인증 어댑터에서 full-goal dual 획득이 실제 비용의 병목이라는 것이다.
모든 cheap certificate가 불가능하다는 증명으로 확대하지 않는다.

원래 goal을 보존하면서 optimal dual을 무료로 제공해도 등록 operational10배에
미달했다. D와C 모두 Native를 전체에서 능가하지 못하므로 v2.0의 중단 규칙을
적용한다. **Phase3 architecture change를 시작하지 않는다.** variable-cardinality,
relational model,learned certificate generation,compute-aware neural policy를
동시에 구현하지 않는다. IR/verifier/native/guarded/structural experience를 유지한다.

G0후보A/B는 별도의 기존 후보로 유지하며 학습 허가로 바꾸지 않는다. Counting의
INCOMPLETE도 유지한다. Q1–Q7과Decision3/v098/v107 봉인도 그대로다. 이번
반례와 비용은 opened diagnostic experience이며 fresh 평가나576개 독립 학습
문제가 아니다. 더 강한 계산 원리의 추가 근거가 나오기 전까지 같은 계열의
성능 재시도와 새 모델 교체는HOLD한다.
