# NEUMANN 1 | 글로벌 AI 연구 25편 통합 감사 및 G0 실행 보고

**2026-10-27 KST · 연구용 · Q1–Q7 전체 OPEN**

## 0. 자료 범위와 정확성

- 사용자가 지정한 `NEUMANN1_GLOBAL_RESEARCH_ADOPTION_COMMAND_2026-10-27.md`라는 **별도 첨부 원본은 현재 대화 파일 목록 및 작업 디렉터리에서 발견되지 않았다.** 그러므로 원본 명령서의 전 내용을 읽었다는 주장, 수록 라이선스/코드 URL을 검증했다는 주장은 하지 않는다. 사용자의 **채팅 본문**의 완전한 명령을 대체 실행 계약으로 채택했다.
- 논문 25편은 연구 원문 출판 페이지·저자 공식 발표 페이지·초록을 검색하고 일부의 메커니즘/방법 설명을 검증한 **문헌 스크리닝**이다. 25편 본문 PDF를 모두 통독·코드 설치·성능 재현한 연구가 아니다. **라이선스 미확인 코드는 사용하지 않았고**, 수치를 NEUMANN 실측으로 이전하지 않았다.
- 연결 GitHub `yoonsj0305/NEUMANN`: `main` 유지, 열린 연구용 Draft PR #616 (RC51), #615 (RC50), #614 (RC49)를 확인했다. 더 오래된 PR들과 Notion 「NEUMANN 1 | Structural Intelligence Research」, 「Q3 Genuine Discovery Gate · STOP fixed-grammar work」, 「Paper-1 Novelty Audit」를 읽었다. `main` 병합·과거 RC 영수증 수정 없음.
- 신경망과 추상화 후보 추가보다 **Classical-first → 증거 있는 표현 공백 → 독립 검증된 실제 모델 학습**이 현재 승인된 메인라인과 부합한다. 대상 데이터 공개 여부, 원저자 독립성, 최초 결과 공개 전 동결 여부는 각각 별도 기록한다.

## 1. 고정 North Star와 현재 진실

> **Frontier-level problem solving with minimum necessary computation.**

PERCEIVE → CLASSICAL FIRST → REFRAME → DISCRIMINATE → INTERNALIZE 다섯 동작만 유지한다. 학습 목표는 **새 실행 구조의 발견 능력 자체가 경험으로 개선되는가**이고, 정답 캐시/기존 연산 선택/고전 엔진 연결을 NEUMANN만의 발견으로 귀속하지 않는다.

### 동결 기존 원장

| 실험 | 역사적 사실과 권한 | 해석 |
|---|---|---|
| RC47 | 30개 동일 계열: 고전 추상화 재사용 후 CPU 소계 1.40484× | 동종 반복의 한정 성과, 전체 Q5 아님 |
| RC48 | 실제 가중치 훈련 실행, 원래 4개 합성 과제에서 직접 해결보다 134.42× 많은 CPU | 기존 언어의 불필요한 뉴럴 학습, 불채택 |
| RC49 | 학습 보상 특징이 사람이 이미 제공한 불변량에서 직접 계산 가능 | 고전 동등 경로에 뉴럴 호출 금지 |
| RC50 | 공개 ARC 12개에 고전 8, 외부 GPT-6 제안 3; 이어지는 공개 12개 source-admission 0/12 | GPT-6 조언은 NEUMANN own-weight 아님, 타 집합 전이 미입증 |
| RC51 | classical-first, same-rights, original verifier, 전체 비용/Pareto 계약 | **기존 게이트 재사용**; 전역 Q1–Q7 OPEN |
| 10/26~27 후속 | PROSE, 합성 프로그램/추상화 연구에서 일부 국소 positives와 다수의 외부 음성 결과 | 수정·새 의미 연산의 모델 귀속/독립 원본 전이/전체 비용 우위 미입증 |

## 2. 25개 연구 스크리닝 및 적용 결정

**판정 의미:** `지금 채택` = 새 대형 아키텍처 없이 **검증·원장·중단 원칙**에 흡수. `G1 조건부` = G0가 실제 고전 headroom을 입증하고 안전한 학습 데이터/예산을 확보할 때만 작은 구현 실험. `보류` = 효과·비용·라이선스/코드 또는 과제 정합 미검증. `제외` = 현재 메인라인에 불필요한 구조. `원문 확인`은 논문/저자 원문 온라인 초록 또는 공개 상세 페이지 확인을 뜻하며 전체 PDF 재현을 뜻하지 않는다. 라이선스는 *확인된 경우에만* 적는다.

| # | 연구 및 확인한 원문 | 원문 핵심 메커니즘 | NEUMANN 최소 적용/중복 및 통제 실험 | 결정·코드·라이선스 경계 |
|---:|---|---|---|---|
| 1 | [Dust](https://qlabs.sh/research/dust) | 토큰별 활성화 섭동으로 역전파 없는 신용 할당 | G1 입장 뒤 동일 proposer/배치/실패 보상에서 BP 대비 forward·variance·정답/줄 평가 | **G1 조건부**; 저자 논문 확인, 코드/라이선스 별도 확인. 본 실행 0회 |
| 2 | [Noise](https://qlabs.sh/noise) | 학습 속도/손실의 고정 평가 계약 | 데이터/모델/평가/실패 시도 단위 고정, 정확히 동일 데이터로 속도 비교 | **지금 채택(평가 원칙)**; 학습 알고리즘 아님, 원문 경쟁 기록 NEUMANN 점수 아님 |
| 3 | [EGGROLL](https://proceedings.mlr.press/v306/sarkar26a.html) | 저랭크 ES의 GPU 행렬 계산 효율 | BP를 유익하게 학습할 G1 때만 저랭크 ES, 같은 총 검증비용 포함 | **보류**; 다음 #6과 핵심 논문/구현 중복, 효과 두 번 계산 금지 |
| 4 | [MeZO](https://proceedings.neurips.cc/paper_files/paper/2023/file/a627810151be4d13f907ac898ff7e948-Paper-Conference.pdf) | 모델 가중치 순전파 섭동 기반 메모리 절감 | BP 기준선이 메모리/지연 병목일 때만 최소 비교 | **G1 조건부**; [공식 코드](https://github.com/princeton-nlp/MeZO), 라이선스 본 검사 미확인 |
| 5 | [Forward-Forward](https://arxiv.org/abs/2212.13345) | 양성/음성 데이터와 층별 국소 목적 함수 | 실행 가능한 연산을 발명하는 신호와 직접 연결 입증 전 추가층 금지 | **현재 제외**, G1 결과로만 재검토 |
| 6 | [Evolution Strategies at the Hyperscale](https://proceedings.mlr.press/v306/sarkar26a.html) | 대규모 ES 분산 평가와 저랭크 병렬화 | #3과 **동일 EGGROLL 계열**, 독립 두 알고리즘 아님 | **#3으로 통합·별도 구현 제외**; 논문 비교 성능은 발표 환경 한정 |
| 7 | [DiscoRL](https://www.nature.com/articles/s41586-025-09761-x) | 경험을 통해 정책 업데이트 **규칙 자체**를 메타학습 | 실제 미래 발견 성과를 학습 목적에; A/보상셔플 B/고전 C 비교 | **G1 핵심 조건부**; [공개 코드](https://github.com/google-deepmind/disco_rl), 비용 큰 메타학습 복제 금지 |
| 8 | [KAIST NEO / Learning-to-Theorize](https://proceedings.mlr.press/v306/baek26b.html) | 관측에서 잠재 원시 연산과 실행 가능한 조합 이론 학습 | `REFRAME` 후보는 실제 실행되는 typed AST, 사람의 완성 원시어휘와 구분 | **G1 핵심 조건부**; [저자 코드](https://github.com/ahn-ml/learning-to-theorize), 라이선스 직접 미확인 |
| 9 | [KAIST GRAM](https://ahn-ml.github.io/gram-website/) | 확률적 다중 잠재 추론 경로와 반복적 refinement | 기존 후보 다양성 및 최소 반례 검사와 기능 중복; 독립 비용/성능 검증 전 latent swarms 금지 | **보류**, 새로운 multi-trajectory NN 추가하지 않음 |
| 10 | [DreamCoder](https://arxiv.org/abs/2006.08381) | wake/sleep 문법·추상화 라이브러리 및 탐색 정책 | 선행 439 합성 과제에서 빈도 매크로 우위 실패; *새 기본 표현의 창출*에 한해서만 참고 | **원리 조건부**, 기존 단순 매크로 확대 **제외** |
| 11 | [AlphaEvolve](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/) | 코드 후보 생성 + 실제 평가기 + 진화 선택 | 외부 검증기, 후보 코드 실행, 실패 원장/재시도 비용 측정만 흡수 | **지금 채택(검증 원리)**; Gemini 호출 및 대형 검색 아키텍처 미채택 |
| 12 | [SkillGen](https://www.microsoft.com/en-us/research/publication/skillgen-verified-inference-time-agent-skill-synthesis/) | 성공과 실패를 대비하고 **회귀를 포함한 순효과** 측정 | 기존 fallback와 비교해 고쳐진 케이스/깨진 케이스 별도; 스킬 저장과 가중치 학습 분리 | **지금 채택(인과검증)**; 매크로 저장만으로 ownweight PASS 금지 |
| 13 | [GEPA](https://proceedings.iclr.cc/paper_files/paper/2026/hash/0e9e708b6f48e14fd0ac29e167413f76-Abstract-Conference.html) | 실행 피드백으로 반성·Pareto 기반 프롬프트 진화 | 실패 단계 피드백 차등 사용을 참고, 프롬프트 패치만 ownweight로 간주하지 않음 | **조건부 참고**, [코드](https://github.com/gepa-ai/gepa); 무제한 롤아웃 제외 |
| 14 | [Darwin Gödel Machine](https://arxiv.org/abs/2505.22954) | 자기 코드 수정 분기·실증 선택·아카이브 | 불변 영수증·되돌리기·분기된 실험만 가져오고 자율 코드 배포는 차단 | **안전 원리 채택, 전체 자기수정 구조 제외** |
| 15 | [Are Self-Evolving Agents Continual Learners?](https://arxiv.org/abs/2610.25858) | 고가소성 자기수정에 망각, 검색 기반 기억에 충돌 | 학습 전/후 동일 이전 문제군 회귀와 retrieval collision 측정 | **지금 채택(회귀 계약)**; 외부 점수 이식 금지 |
| 16 | [Weasel](https://proceedings.mlr.press/v306/zadeh26a.html) | 중요도·다양성 학습 데이터 선택, 입력 주변부 절제 | 현재 실검증 수리 경험 3개뿐: 훈련 사례가 충분히 늘기 전 데이터 선택기 학습 금지 | **조건부 보류**; [코드](https://github.com/fatemehpesaran310/weasel), 공개 논문의 9.7~12.5× NEUMANN 아님 |
| 17 | [Rule2DRC](https://proceedings.mlr.press/v306/kim26d.html) | 실행 검증 기반 후보를 구별하는 test 생성 | `DISCRIMINATE` 테스트를 원본 목표에 맞춰 자동 생성, 테스트 비용 충전 | **지금 채택(원리)**; [MIT 코드](https://github.com/snu-mllab/Rule2DRC), 산업 DRC 환경 전체 이식 보류 |
| 18 | [KAIST Process-Verified RL](https://openreview.net/pdf/b6e9f349a9b2156578910d24996f24369b131e8a.pdf) | Lean의 중간 전술 첫 오류에 기반한 밀집 검증 보상 | typed AST 실행 시 **첫 잘못된 변환/거부 원인**만 credit에 제공 | **G1 조건부**, Lean/GRPO 대형 훈련 복제 금지 |
| 19 | [FEA Feedback CAD Agents](https://arxiv.org/abs/2605.17448) | FEA로 산출물의 실제 물리 기능을 평가하며 반복 생성 | 프로그램 소스 일치 대신 **원래 문제 조건의 독립 검증** 유지 | **검증 원리 채택**, 물리 시뮬레이터 설치·비용은 현재 보류 |
| 20 | [Do Self-Evolving Skills Generalize to Held-Out Tasks?](https://arxiv.org/abs/2609.39148) | 훈련 중 스킬 개선과 홀드아웃 효과의 불일치 | 문제군/저자/표현 형식 분리하고 전이 성공을 독립 기록 | **지금 채택(전이 규약)**; skill cache ≠ 발견 학습 |
| 21 | [Does Failure Feedback Direct Agent Self-Modification?](https://arxiv.org/abs/2610.14662) | 무관 피드백 대비 **표적 수정의 인과성** 검사 | 동일 카테고리 가짜 피드백 B, 진짜 수정 A, 타깃과 새로운 문제 별도 채점 | **지금 채택(핵심 인과 대조)** |
| 22 | [ScholarCatalyst](https://arxiv.org/abs/2610.02202) | 연구에 도움되는 선행연구 검색 평가, 검색 자체 과적합 경고 | 읽은 원문/근거 상태를 증거 원장에 연결, 중복 검색 제거 | **평가 원리 채택**, 새 연구 검색 에이전트 개발 제외 |
| 23 | [REPAIR](https://aclanthology.org/2026.emnlp-main.1204/) | 근거 검증, 오개념 hard negative 통한 과학 검색 보강 | 코드/결과/원문/허가 원장과 오인 귀속 반례만 사용 | **검증 원리 채택**, 독립 retrieval model 훈련 제외 |
| 24 | [Hybrid Deep Searcher](https://proceedings.iclr.cc/paper_files/paper/2026/hash/4127b22b1b8e42873c1c20eedae0e220-Abstract-Conference.html) | 병렬 폭넓은 자료 탐색 + 순차적 심층 검증 | 핵심 근거 누락 시에만 선택적으로 2단계 검색, 탐색 API 비용 별도 계측 | **조건부 보류**, 독립 searcher 모델 복제 금지 |
| 25 | [KAIST MAPR](https://proceedings.mlr.press/v306/kim26s.html) | 예상 성공확률·추론 길이·개념을 예측해 계산 조절 | 기존 RC51 고전 우선 비용 게이트가 우선; 유효한 정답률 예측을 검증할 때만 확장 | **조건부 보류**, 추가 predictor 훈련 0회 |

**코드/라이선스 정책:** 위 표의 확인된 코드 링크는 해당 프로젝트의 존재가 저자 원문이나 공식 저장소에 드러난 경우만 넣었다. Rule2DRC GitHub 표기 MIT는 공식 README에서 확인했다. 나머지 코드의 최신 LICENSE 파일과 재배포 조건은 개별 확인하지 않았으므로 `LICENSE_UNVERIFIED`, 패키지 내부에 제3자 코드를 복사하지 않았다. 해당 논문의 보고된 정확도/학습속도는 **모두 원저자 실험**이며 이 보고서의 G0에서 재현한 수치가 아니다.

## 3. 현재 NEUMANN 최소 공통 인터페이스

1. **PERCEIVE**: `task_id`, source author, original Git SHA1, source/test SHA256, 누출/미지원 입력 확인. 증거 없는 것은 `UNKNOWN`.
2. **CLASSICAL FIRST**: 기존 RC51 `gate.py`를 **수정하지 않고 호출**. 원래 목적을 검증한 고전 결과가 있으면 신경망 forward 허가 `0`.
3. **REFRAME**: 독립 고전 공백과 검증기, 연구 예산의 근거가 있을 때에만 `NEURAL_RESEARCH_ONLY`라는 연구 자격. **배포 허가 아님**.
4. **DISCRIMINATE**: 원본 검증기·중간 실패 원인·구별 테스트, 프로그램과 설명을 분리, 보류/오답 별개 기록.
5. **INTERNALIZE**: 실제 ownweight의 독립 실패 수정 경험만 학습 자료 인정. A(실경험)/B(동등 자원 가짜 보상)/C(강한 고전)/D(학습+검증 라이브러리) 분리하고 옛 능력 보존. G1 미입장 시 호출 `0`.

패키지 `common_contract.py`는 기존 RC51 모듈을 불변 상태로 import해 증거/허가 정책을 실행하는 **얇은 어댑터**만 구현한다. 새로운 스웜/에이전트 루프를 추가하지 않았다. Q1–Q7 권한 자동 승격을 차단한다.

## 4. 이번 실제 실행: 새 외부 G0

### 절차 및 출처

1. **정답/원문 보기 전** 7개 Microsoft PROSE 원본 과제 ID를 기존 PR #616 연구 브랜치에 사전등록했다: `Gender.000002`, `Phrase.000003`, `Product.000003`, `ShippingCode.000009`, `Name.000020`, `Phone.000012`, `DateTime.000041`. GitHub 사전등록 커밋 `e2b2c7af6ef2888f34c0cc0bd067b026c507daf9`.
2. 이전 고전 합성기 **완전 같은 SHA256** `092165e7b93d0f8229da47f7f8abed54547b4ecc3e34c3f1df3fc631e122ff47`를 사용했다. 원본 첫 2개 입출력만 제공, 다음 1~3개는 **입력만** 제공했다. 출처는 `microsoft/prose-benchmarks/Transformation.Text/[task]/spec.json`, 원본 Git blob SHA1을 각각 고정했다. 여러 범주이지만 한 저장소 저자 계열이므로 **저자 독립 문제군 G2**로 간주하지 않는다.
3. **정답 공개 전** 첫 프로그램/예측·보류/CPU를 저장했다. `G0_FIRST_BEFORE_GOLD.json` SHA256 `3e4b242468871ffb1378911002c6e39f192a8c03927c1a7f195bcba5025e64ee`. GitHub 첫 동결 커밋 `ca12ce094c79c22ab5dca60be37c38bda9686e08`.
4. **그 후** 외부 원본 출처의 다음 정답을 독립 조회, 기존 Git blob SHA1 7/7 재검사, 절대 제안 프로그램을 바꾸지 않고 정확 채점.

| 원본 과제 | 고전 첫 상태 | 미래 완전 정답? |
|---|---|---|
| Gender.000002 | HOLD | 보류 |
| Phrase.000003 | `['qui']` | **CORRECT** |
| Product.000003 | HOLD_DISAGREEMENT | 보류 |
| ShippingCode.000009 | `['GU2','VDB','1KN']` | **CORRECT** |
| Name.000020 | `['Y','K','S']` | **CORRECT** |
| Phone.000012 | HOLD | 보류 |
| DateTime.000041 | HOLD | 보류 |

**정확한 G0 결과: 3/7 CORRECT, 0/7 WRONG, 4/7 HOLD.** 소스 프로그램 탐색의 CPU 부분 합계 **26,428,065ns = 26.428065ms** (각 과제 3~4ms대), 새 신경망 forward **0**, 유료 API/GPU 자원 **0**. 전력·총 peak RAM·금전·인증된 독립 검증기 설치비는 **UNKNOWN**. 소스 예시와 테스트 입력은 connector로부터 옮겨온 별도 fixture이며, 원본 파일 blob SHA는 재인증했다. 독립 제2 구현이 소스/입력 바이트 전부를 다시 대조하는 수준의 감사는 아직 실행하지 못했다. 따라서 이 연구는 외부 PROSE의 **범위 제한 탐색 G0**이지 최종 Q7 실험이 아니다.

### 단계별 판정

- **G0: EXECUTED_SCOPED_CLASSICAL; G1 admission = HOLD**. 제한된 문법에서 4개를 보류했다는 사실은 모든 고전 알고리즘의 한계 증명이 아니며, 이 7개에서 새롭게 학습된 실행 표현이 검증됐다는 증거도 없다. 세 과제는 고전 경로가 이미 작동했다.
- **G1: NOT RUN**. own-weight A, fake reward B, memory-allowed D를 실행하지 않았다. 이 집단들의 0/7 점수 등을 **만들어내지 않는다**.
- **G2: NOT RUN**. 다른 원저자/의미 구조 및 첫 가중치 동결이 충족되지 않았다.
- **Dust/BP/MeZO/EGGROLL: NOT RUN**. 실제 학습 혜택이 입증되지 않아 최적화기 비교에 돈/시간을 사용하지 않았다.
- **Q1–Q7: 전역 전부 OPEN**. G0의 일부 exact는 RC51 고전 방식의 역할을 재확인한 것이고 NEUMANN 학습 발견 증거가 아니다.

## 5. 회귀 검증과 재현

- 이전 RC51 독립 ZIP을 **완전 새 디렉터리**에 전개해 `bash REPRODUCE.sh`: SHA manifest 4/4, `pytest` 14/14, Q1–Q7 OPEN 보호 PASS.
- 최신 `NEUMANN1_OPERATOR_INVENTION_STOP_GATE_20261027` 별도 패키지 `bash REPRODUCE.sh`: 기존 동결 최초 예측, 동작 게이트와 원본 G1/G2 실패 영수증 재채점 (테스트 결과 파일 참조), 변경 없음.
- 새로운 얇은 계약 `common_contract.py`: pytest 5/5. 해결된 고전은 뉴럴 호출 0, grammar 미입증은 HOLD, 연구 허가는 배포 허가 아님, 원본 task ID 일치, HOLD와 WRONG 구분을 확인했다.
- 이번 첫 결과는 `g0_source_only.json`, `G0_FIRST_BEFORE_GOLD.json`, `g0_future_gold_after_freeze.json`, `G0_ACTUAL_RESULT.json`로 분리. 현재 연구 산출물 SHA256들은 동봉 MANIFEST에서 확인.

## 6. 리스크와 명확한 중단 조건

1. **원본 명령서 누락:** 별도 `.md` 첨부를 찾지 못했다. 따라서 첨부 전용 세부 라이선스·코드·예산 조항은 미확인. 본문 명령만 실행.
2. **논문 원문 범위:** 25편 학술 본문의 모든 실험 부록을 검증한 것이 아니다. 원문/저자 공식 페이지 기반 스크리닝이며 코드/라이선스는 분리 상태.
3. **독립성:** PROSE 7개는 저자/데이터군 공통. 다른 시드, 이름 바꾸기, 같은 생성기 변형을 cross-domain으로 계산하면 안 된다.
4. **데이터:** 소스 fixture 수동 이동으로 복사 오류 위험이 있다. SHA는 원본 파일 버전 정합이지 fixture 전체 완전 일치 보증이 아니다. G2에는 원문 바이트 단위 감사와 독립 평가자 분리 필요.
5. **학습 효과:** 현재 자체 개선을 만드는 *훈련 가능한 자유 연산 제안자*와 충분한 미래검증 수리 경험이 부재. 과거 합성 positive를 학습 신규성이라고 부르지 않는다.
6. **비용:** 단일 CPU 프로세스 탐색 소계는 whole-system 자원 우위가 아니다. 데이터 확보·다회 실패·연산·검증·저장·리플레이·CPU/GPU·지연·RAM·줄·USD가 동등 범위일 때만 Pareto 비교한다.
7. **안전성:** 새 제안 프로그램은 격리 실행하고 최초 가중치 및 모델 권한·원래 기능을 보존하며 회귀 발생 시 자동 롤백한다. 검증 실패/제어 미확인 시 HOLD.

## 7. 단 하나의 다음 결정적 실험

**G1 진입에 필요한 진짜 G0를 먼저 확보하라:** 서로 다른 저자가 제작했고 원본 검증기가 실행 가능한 프로그램/정리 문제들을 선택하고, Z3/cvc5·전통 합성·해당 분야 전문 solver 등 **동일 권한의 강한 고전 기준선을 등록된 예산으로 모두 실행**해 추가 가능한 실질적 의미 공간을 확인하라. 그리고 검증된 서로 다른 실패·수정 경험을 얻어, **완성된 연산 종류 목록이 아닌 실행 가능한 구조 자체를 생성하는 작은 ownweight proposer**를 준비하라. 아직 발견한 새로운 해법·검증 데이터가 없다면 학습을 시작하지 마라.

그 요건이 입증된 후에만 단 하나의 사전등록 G1: A 진짜 경험, B 동등 비용 잘못된 피드백, C 강한 고전, D A+라이브러리. 고정된 첫 가중치/제안, 새 원본 과제에서 **A>B AND (A만의 추가 인증 해법 OR 동등 성능의 전체 비용 이득)**을 충족해야 다음 G2. 성공해도 A만의 새로운 *기초 의미 연산* 발견인지 추가 별도 판정. 실패는 실패로 닫고 Q1–Q7을 임의 승격하지 않는다.

**연구 명령:** 이전 결과 수정·PASS 승격 금지, 새 GPU·유료 호출 금지, 상기 G0 근거 없으면 G1 실행하지 않음. 현재 계정의 접근 가능한 GitHub Draft PR로만 연구 증거 보존하며 `main` 건드리지 않는다.