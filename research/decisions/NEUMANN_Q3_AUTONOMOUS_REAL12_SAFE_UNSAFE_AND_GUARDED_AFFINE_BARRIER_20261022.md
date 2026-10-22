# NEUMANN 1 | 원본 SAFE·UNSAFE 완전 분류 + 조건부 관계 수학적 경계

2026-10-22 · 연구 범위: 이미 열어본 실제 공개 SyGuS-Org 원본 12개. **사후(posthoc) 평가, 미관측 첫 시험 아님.** 소스 고정 커밋 `13c8deb68a873635879c9a69bc78caebd340f646`. 최초 SHA 사전 등록에서 `fib_11.sl` 오타가 있었으며 최초 실패 영수증을 소급하여 성공이라고 표기하지 않는다. 여기 포함된 것은 별도 사후 원본 SHA 정정 결과다.

## 결정적이고 확인된 결과

1. **11개 SAFE:** 사람의 목표 불변량 없이 원본 Pre/Trans/Post로부터 정확한 관계식 및 조건부 관계를 자동 합성. 원본 3VC 33/33을 Z3 및 cvc5가 각자 UNSAT 판정. 잘못된 TRUE/FALSE 대조군 22개는 각각 SAT 판정.
2. **1개 UNSAFE:** 정답 반례가 없는 원본 Pre/Trans/Post에서 BMC 깊이 0,1을 수행하여 `fib_07.sl` 깊이1 도달 반례 자동 추출. Z3 및 cvc5가 구체적으로 고정된 원본 초기 상태, 원본 전이, 원본 불안전 조건 모두 SAT 확인. 12개 전부 두 깊이 검사: 솔버별 24개 SAT/UNSAT 질의 + 원본 구체 반례 확인 각 1개. 다른 11개에서 깊이1 이하의 반례가 없다는 사실은 SAFE 증거가 아니라 별도 3VC 안전 증거를 필요로 한다.
3. **전역 표현 경계:** `fib_13.sl`의 원본 초기 등식 행렬 M과 전이 변화량 C로부터 `rank(C Mᵀ)=2`, `nullity(C Mᵀ)=0`. 따라서 **초기 상태 전부에 참이고 두 전이 가지 모두에서 보존되는 비자명한 전역 아핀 등식은 없다.** 그러나 `t=0`, `t≠0` 가지별 nullity는 각 1이고 자동 생성된 `(t=0 ⇒ k=0)` 및 `(t≠0 ⇒ j−2k=2)`의 결합은 원본 3VC 세 가지를 Z3·cvc5 양쪽에서 UNSAT로 검증. 조건을 제거한 두 등식은 각각 원본 귀납성 검사에서 Z3·cvc5 양쪽 SAT. 이는 전역 *단일 아핀 등식* 표현 부류에 한정된 정리다.

## 실행 증거

- SAFE/UNSAFE 전체 자동 판정: [Actions #39713251528](https://github.com/yoonsj0305/NEUMANN/actions/runs/39713251528), 아티팩트 #12398420215, 원본 ZIP SHA256 `4a57503ac64cc40bde1c8baca596a4c64dcd651e390f84a891009915b939243d`. [GitHub PR #453](https://github.com/yoonsj0305/NEUMANN/pull/453).
- `fib_13` 수학적 장벽 독립 검사: [Actions #39713910948](https://github.com/yoonsj0305/NEUMANN/actions/runs/39713910948), 아티팩트 #12397454289, 원본 ZIP SHA256 `5b4b686dcf1894543271ee76d6f44f5c563c0a7bbdbbf1975678aa3674ef0785`. [GitHub PR #454](https://github.com/yoonsj0305/NEUMANN/pull/454).
- 별도로 내려받은 GitHub 아티팩트는 원본 그대로 ZIP으로도 보존될 수 있으나 이 패키지에는 콘텐츠를 증거 폴더로 풀어서 포함했다. 증거의 내부 원본 SHA-256 목록은 `SHA256_MANIFEST.json`으로 재검사한다.

## 재현

Python 3.11+, `sympy==1.14.0`, 운영체제 Z3 공유 라이브러리 `libz3.so.4`, 독립 cvc5 1.4.2 실행 파일이 필요하다. GitHub Actions 워크플로에는 cvc5 배포 ZIP SHA256이 고정돼 있다. 네트워크가 있어야 공개 원본을 고정 Git 커밋에서 받을 수 있다.

```bash
python code/download_pinned_source.py --out sources
python code/affine_guard_autosynth.py --engine code/classical_houdini.py --source-dir sources --manifest code/SOURCE12_SHA_ONLY_NO_GOLD.json --out generated_safe.json
python code/original_source_bmc01.py --source-dir sources --registry code/SOURCE12_SHA_ONLY_NO_GOLD.json --engine code/classical_houdini.py --ast-parser code/affine_guard_autosynth.py --out generated_bmc.json --cvc5
python code/convert_for_checker.py --affine generated_safe.json --out checker_input.json
python code/independent_original_checker.py --receipt checker_input.json --input sources --manifest code/SOURCE12_SHA_ONLY_NO_GOLD.json --backend dual --out independent_safe.json
python code/branch_rank_original_certifier.py --source sources/fib_13.sl --expected-gitblob b583a100b7c5a4b9b25a22c4c881b1cd90e2e3ee --affine-engine code/affine_guard_autosynth.py --classical-engine code/classical_houdini.py --out guarded_rank_certificate.json --smt-out guarded_smt --cvc5
```

## 과학적 판정과 다음 단계

**입증:** 이 12개 원본에 대한 자동 SAFE/UNSAFE 구별 능력, 정확한 원본 이중 SMT 검증, 한 진짜 원본에서 전역 아핀 표현의 수학적 장벽, 조건부 원본 구조가 그 장벽을 넘는다는 사실.

**미입증:** 학습 모델 고유 연산자 발명, 강력한 고전적 기준선 대비 일관된 우위, 미관측 저자 독립 전이, GPU/프런티어 모델 성능, 10배 전체비용 우위, NEUMANN Q1~Q7의 글로벌 닫힘.

동일 코호트에서는 이미 고전적 알고리즘만으로 SAFE 11개와 UNSAFE 1개를 판정하므로, 추가 모델의 *추가 정답 개수*로 고유 성과를 증명할 여지가 없다. 다음 독립 실험은 새로운 계열의 미관측 원본과 강력한 전통적 솔버, 학습 제거, 완전비용 대조를 필요로 한다.