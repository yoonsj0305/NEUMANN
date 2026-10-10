# poly_no_fac: 저장된 Native 표현의 원래 목표 인증

2026-10-10 KST. 기준선 `2add388b78af9ce23031203e669dee1638a94551`의 후속
opened-development 독립 확인이다. **수학적 원래 목표는 ORIGINAL_CERTIFIED**,
신규 학습 결정은 `HOLD_LEARNING_CLASSICAL_AFFINE_POLYNOMIAL_SUMMARY`다.
기존 `mps_no_sum.ml` 반례, `(prefix,sum)` 해결 및 HOLD 판정을 유지한다.

## 원문과 저장된 결과

원문 Synduce commit: `b5c1d1611d3fbf5d8cdf9a23fde52c2cbba95a89`.
`benchmarks/list/poly_no_fac.ml` SHA-256:
`e9a3436fe113e714f09baa701304f6eca9b8b2ae760812d319b8a128ef002810`.
29개 원본/174개 관측 중 case 22의 기존 최초 관측 6개를 모두 사용했다.
이는 하나의 열린 원본에 대한 두 solver의 3반복이며 fresh 원본은 0이다.

| 최초 기록 | 저장된 상태 | 도구 실행 시간 중앙값 |
| --- | --- | ---: |
| CVC5 3회 | 외부 timeout 3/3 | 60.066154613초 |
| CVC4 3회 | Upstream reported realizable 3/3 | 1.729636457초 |

최초 로그·판정·source hash는 변경하지 않았다. CVC4 출력 3개는 동일한
printed solution SHA-256 `5e4ec657938e9b98e637f709902170dda17b341f4254566e061de30ffc265487`
이며 다음 표현을 실제로 생성했다:

`E = (0,1); Single(a) = (a,x)`

`merge((v,f),(w,g)) = (v + f*w, f*g)`

첫 성분은 다항식 값, 둘째는 리스트 길이에 따른 `x`의 곱 인자다.
Native가 이미 필요한 추가 상태를 생성했으므로 CVC5 단독 timeout을 강한
Classical-Hybrid 전체의 미해결 구조 발견으로 해석하지 않는다.

## 독립 원본 인증

원문 목표는 `spec x (repr tree)`이며 `spec`의 정확한 재귀는
`F_x([],t)=t`, `F_x(h::l,t)=h+x*F_x(l,t)`이다. 실제 원문은 종료값 0을 사용한다.
Native lifted state의 suffix response를 `rho((v,f),t)=v+f*t`로 두면:

1. `rho(E,t)=t`.
2. `rho(Single(a),t)=a+x*t`.
3. `rho(merge(L,R),t)=rho(L,rho(R,t))`.
4. `rho((v,f),0)=v`.

기존 `representation_program.Builder`, `polynomial_forms`, `verify_original`로
이 네 항등식과 좌/우 항등원 및 결합법칙, **총 7개 보편 다항식 항등식**을
정확하게 확인했다. 모든 변수는 자유 정수 변수이며 입력 예시로 PASS하지 않는다.
이 법칙들에 constructor 구조 귀납을 적용하면 모든 유한 tree에서 Native의
response가 펼친 리스트의 원래 fold response와 일치한다. 종료값 0에서 첫 성분이
원래 scalar 목표가 된다. 고정 길이의 다항식 비교만 한 것이 아니다.

원문의 `repr/dec`는 기존 `source_bound_recursive.parse_representation`와
`prove_flatten`을 재사용했다. 생성된 free-word 조건은 왼쪽에서 오른쪽 순서를
보존하고, **4개 Z3 UNSAT 조건**이 모든 recursive call의 lexicographic 종료를
확인했다. 원문 리스트 변환을 단순히 올바르다고 가정하지 않았다.

첫 성분 decoder는 임의 선택이 아니다. 같은 pinned upstream의
`src/se2gis/Lifting.ml:148`은 원래 scalar 타입을 lifted tuple의 첫 성분으로
projection하고, `src/se2gis/Equations.ml:208`은 실제 합성 식에 이를 적용한다.
해당 코드 파일들의 해시도 검사했다. `Pretty.pp_soln`은 lifted 내부 scheme을
인쇄하므로 출력 tuple 전체가 원래 scalar 정답이라는 주장은 하지 않는다.

source/printed kernel의 해시를 고정하고 이 한 원문을 명시적으로 DAG로 전사했다.
이는 범용 OCaml parser가 아니며, 작은 전사 및 constructor 귀납의 정확성은
검증 범위에 포함되는 신뢰 가정이다. 다른 source/goal/decoder/hash는 거절한다.

## 판정 범위와 UNKNOWN

| 대상 | 판정 | 이유 |
| --- | --- | --- |
| 첫 성분으로 복원한 수학적 원래 목표 | ORIGINAL_CERTIFIED | 보편 항등식 + 구조 귀납 + 실제 repr 순서/종료 증명 |
| 기존 piecewise-linear emitted reader | UNKNOWN | 곱셈·parameter 문법이 지원 범위 밖 |
| 기존 explicit-assertion source reader | UNKNOWN | 원문은 이름 기반 spec/target/repr 형식이며 해당 reader의 명시적 assertion이 없음 |
| 인쇄된 조각의 standalone OCaml 컴파일/실행 | UNKNOWN | wrapper 통합·인쇄 연산자·실제 빌드를 이번에 실행하지 않음 |
| 공정한 complete-cost 경제성 | UNKNOWN | 기존 도구 기록과 신규 인증은 환경·비용 범위가 다름 |

현재 원문 Native의 실제 목표 반례는 발견되지 않았다. 기존 reader의 미지원은
반례나 solver timeout으로 재분류하지 않는다. 추가 generic verifier/parser를
만들지 않고 기존 정확 다항식 및 repr verifier를 연결해 지원되는 수학적 범위를
확인했다. 증명 budget을 넘거나 필요한 lemma를 증명하지 못하면 UNKNOWN이며,
충분 lemma의 실패만으로 원래 목표 COUNTEREXAMPLE를 선언하지 않는다.

인증은 모든 정수 `x`와 leaf 값, 유한 ordered acyclic tree, 동일 `x`가 모든
leaf에 유지되는 수학적 정수 의미다. `x!=0`, `x>0`, 정렬 같은 추가 조건은 없다.
실제 machine overflow, 무한/순환 입력, subtree별 parameter 변경, 임의 프로그램,
자연어 의도와 전체 compiled runtime은 인증하지 않는다.

## 비용·테스트·결정

신규 실측은 원문 repr 검증 **0.031866900초**, 7개 identity 검증 및 budget 검사
**0.001921000초**, 파일 검사까지 포함한 이번 분석 **0.049966500초**다.
이는 Windows 로컬 인증 단계의 시간이다. 과거 다른 환경의 Native 중앙값에
더하거나 나눠 전체 비용/배포 latency/10배 우위를 만들지 않는다.
FLOPs, 에너지, peak memory, 완전한 투자·fallback 비용은 UNKNOWN이다.

실제 테스트: **53 passed, 0 failed, 3.16초**. 보편 identity, 증명 누락/중복,
잘못된 composition, source/goal/decoder 변경, proof budget UNKNOWN 및 기존
다항식/source-bound/recursive triage 회귀를 검사했다. 일부러 잘못 만든 merge는
`x=2`, `[1]++[1]`에서 2를 내고 원래 목표는 3인 반례도 확인했다. 이는 테스트용
변조 식의 COUNTEREXAMPLE이며 저장된 Native의 반례가 아니다.

결정: 이 affine polynomial summary에 대한 신규 구조 발견 학습은 HOLD.
강한 기존 Native가 표현을 생성하고, 원본 목표의 정확성도 기존 알고리즘으로
검증된다. 학습기가 메워야 할 구체적인 미해결 발견 병목을 확보하지 못했다.
기존 전체 비용이 작다고 확정하거나 모든 polynomial 영역에 기회가 없다고
확대하지 않는다. 이 원문에서 추가 free-perspective 성능 코호트는 실행하지 않았다.

검증 recipe, 고정 contract, 최초 독립 결과, 테스트 receipt와 해시는
`research/development/poly-no-fac-original-proof-2026-10-10/`에 별도 보존한다.
새 솔버·학습기·추론 runtime은 없다. Native 합성 재실행, 모델/GPU/유료 호출,
봉인 자료 접근, GitHub 업로드 모두 0이다. Gemma frozen 계약과
`BLOCKED_SMALL_MODEL_RUNTIME`, Frontier Gap 미측정은 유지한다.
