# NEUMANN 1 | 실제 학습 구조 발견 첫 비교와 동결 문법 한계

2026-10-22. 증거에 근거한 결론. **일부 실제 원본에서 학습 모델이 유용한 구조를 직접 생성하는 능력은 관측되었다. 그러나 고전적 알고리즘만으로 얻을 수 없는 학습 고유 구조의 발견은 입증되지 않았다.** 이 문서는 최초 실패·학습 제거·강한 정확 대조군을 모두 보존한다.

## 1. 실제 신경망 학습 구조 발견, 기존에 열린 원본의 개발 실험

- 고정된 source-only self-supervised 실험: 실제 원본 Pre와 Trans를 Z3로 샘플링한다. 초기 조건의 서로 다른 모델이 부여하는 차이와 원본 전이에서 얻은 상태 변화에 대해 보존계수 w를 PyTorch Adam 2,000회 업데이트하여 학습한다. `Post`와 인간의 정답 불변량은 모델의 학습 손실·후보 추출에 주지 않는다. 계수를 작은 정수로 형변환한 뒤 `Post`와 결합하고 원본의 세 귀납 조건을 Z3로 직접 확인한다.
- 개봉된 진짜 SyGuS 원본 6개 × 초기화 4개 = 24회 개발 평가. `jmbl_tacas`, `sum1`, `hola_countud`에서 신경망 12/12 유효한 원본 전체 귀납증명, 동일 초기화의 학습 없는 가중치 0/12. 다른 세 문제 `fib_41`, `fib_18`, `fib_15`에서 0/12. 따라서 **24번 전체에서는 학습 12/24, 무학습 0/24**.
- **강한 정확 고전 대조군이 같은 실제 Pre+Trans 예시에서 유리수 영공간을 계산하니 세 성공 원본을 전부 해결**했다. 네트워크가 구조를 도출했다는 명제와 오직 네트워크만 구조를 도출했다는 명제는 별개다.
- 개발 영수증: `NEUMANN_Q3_LEARNED_CONSERVATION_DEV_RECEIPT_20261022.json`, SHA256 `012344245bc3d3e9e1cf2a73fc9fad6a1f26eaebcc977d2d9d61e998888f7b3c`; 실제 학습 코드 `neumann_learned_source_conservation_dev.py`.

## 2. 실제 원본 읽기 전에 동결한 9개 외부 본문 검사

- 하나의 방법을 먼저 고정하고 SHA 메타데이터만 읽어 9개 원본을 등록했다. SyGuS 공식 2017/2019 자료 4개, LoopInvGen PolyRank 2개, Code2Inv 3개. 별도 상류 Git 저장소는 두 곳이지만 독립 저자 검증이나 프로젝트 전체 과거 노출 배제는 수행하지 않았으므로 완전한 Q6 blind로 주장하지 않는다.
- 공식 최초 실행: GitHub Actions #39704931251, 성공적으로 실행 종료한 raw receipt artifact #12394602126, SHA256 ZIP `2ad9be53374a65673592153df8de76e15259cbb44afe0a3ef0686be40494144b`.
- 전체 9개 분모: 학습 모델 `sum3.sl` 1/9 유효 원본, 네 초기화 모두 성공. 동일 초기화의 학습 제거 0/9, 강한 동일 데이터 정확 대수 1/9, frozen 고전 관계식 Houdini 6/9. 세 등록 원본(`poly1.sl`, `code2inv_1.sl`, `code2inv_10.sl`)은 입력 상태 서명 제한 AssertionError로 미지원. 후속 변경으로 최초 제출 결과를 바꾸지 않는다.
- 별도 재작성 original-source verifier가 실제 원본 Git SHA 9/9, Z3와 cvc5의 원본 3VC 각각 총 153질의와 5개 유효 3VC 후보(학습 시드 4개 및 exact baseline 1개)를 확인. 잘못된 FALSE/TRUE 후보 18개의 SAT 원본 대조군 Z3 양성 증거도 보존. 모델의 Q3 발견 자체를 cvc5 영수증 없이 확정하지 않았다.
- 학습+고전적 정확 대조군+원본 Z3 탐색 경로 실제 벽시계 약 41.25초 vs 해당 runner의 frozen classical Houdini 경로 약 5.634초. 이것은 반복순서 교차시험이나 동일 제출 경쟁경로의 전체 비용이 아니므로 7.3배라는 값으로 통계적 우월/열등을 확정하지 않는다. 특히 10× NEUMANN 우위의 근거가 없다.

## 3. 왜 이 결과가 한계를 정의하는가

모델 출력은 여전히 이미 제공된 1차 정수 선형식 문법에 속한다. 같은 실제 자료에서 완전한 정확 유리수 해 공간을 구하는 방법은 그 문법의 모든 정확 일치 후보를 포함한다. 학습이 유용한 **계수**를 찾더라도 새로운 수학 연산자를 발견한 것은 아니다. 다른 유용한 표현을 찾으려면 사람·사전 설계자가 제공한 문법 밖의 typed 연산자/조건/보조상태 구성을 제안하는 생성기가 필요하다.

## 4. 조건부 구조의 실제 신경망 추가 개발

또 다른 이미 개봉된 공식 SyGuS `fib_18.sl`에서 실제 Trans에 등장하는 소스 조건 `(= flag 1)`을 추출하고 그 조건하에서 변화하는 변수 b, j만 선택하여 보존식 계수를 PyTorch가 학습했다. 학습된 결과는 `flag = 1`이면 `b − j = 0`이어야 한다는 **조건부 관계식**이다. 원본 Post와 결합한 실제 Z3 전체 귀납 3VC에서 4/4 PASS, 동일 초기화 무학습 0/4. 단 해당 조건부 문법(=> guard affineEquality)은 사람이 설계한 아키텍처에 있으므로 신경망이 `=>`나 equality primitive를 발명한 것은 아니다. 이후 독립 소스 파서가 Z3와 cvc5로 9개 후보 × 원본 3VC를 각각 27개 재검사해, **학습 4/4, 무학습 0/4, 정확 대수 1/1**을 다시 확정했다. 공식 Github Actions #39705829679, 영수증 아티팩트 #12394971918 (artifact ZIP SHA256 9d4b00a5fd2ad59a41dd030c8a7f0cabfd47d6bbb2186b44af5c263aa1bcf43e). 동일 출처의 다른 원본으로 학습 가중치가 전이한 증거는 아니다.

## 5. 과학적 판정과 결정

- `Q3.SOURCE_LOCAL_TRAINED_RELATION_OBSERVED`: **scoped PASS**, 사후 6개 개발 집합 및 SHA 사전 고정 9개 원본에서 학습으로 도출된 귀납적 선형 관계가 실제 소스 증명을 충족한 사례 확인.
- `Q3.TRAINING_KNOCKOUT_IN_SAME_ARCHITECTURE`: **scoped PASS**, 하지만 강한 정확 고전 대조군도 해당 사례를 해결.
- `Q3.LEARNED_EXCLUSIVE_NEW_TYPED_OPERATOR`: **NOT PROVEN**, 원본 9개에서 학습의 독점적 유효 증명은 0개.
- `Q4.10X_END_TO_END_TOTAL_COST`: **NOT PROVEN**.
- `Q6.TRUE_INDEPENDENT_AUTHOR_WEIGHT_TRANSFER`: **NOT PROVEN**. 새로운 원본마다 가중치를 다시 학습했으며 학습 가중치 자체의 전이는 수행하지 않았다.
- `Q7.FRONTIER_ABILITY_PARITY`: **NOT PROVEN**.

**주력 연구 경로 재설계:** 더 이상 고정 1차 다항식의 가중치를 반복 학습하는 실험을 확대하지 않는다. 먼저 미리 동결한 typed operator 문법 외부의 모델 제안 AST를 요구하고, 정확 클래식 모델/소스 기반 CEGAR와 같은 원본 권한의 대조군으로 평가한다. 예산은 훈련, 학습 가중치 재사용, 프롬프트, SMT query, 실패, fallback, proof, end-to-end 벽시계 전체를 포함한다. 학습이 고전 대조군을 넘어선 독자적 능력 없이 굴러가는 동안 Q3/Q4/Q6 글로벌 상태는 OPEN이다.

## 6. 증거 연결

- 원본 연구 [PR #449](https://github.com/yoonsj0305/NEUMANN/pull/449)
- [최초 9개 실행 영수증](https://github.com/yoonsj0305/NEUMANN/actions/runs/39704931251)
- [조건부 구조 생성 독립 이중 인증](https://github.com/yoonsj0305/NEUMANN/actions/runs/39705829679)
- [상류 SyGuS 공식 원본](https://github.com/SyGuS-Org/benchmarks/tree/13c8deb68a873635879c9a69bc78caebd340f646)
- [LoopInvGen 외부 상류](https://github.com/SaswatPadhi/LoopInvGen/tree/6ac90265b11431c9477dfbd33e3e3380234c0499)