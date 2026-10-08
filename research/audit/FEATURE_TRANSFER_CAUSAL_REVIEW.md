# Opened feature transfer review — zero new inference

기존 quotient 함수 본문을 그대로 실행해 v088 원본 학습 48개와 M106 원본 16개의
특징을 분석했다. 원본 archive와 개별 source hash를 확인했고 모델 forward,
학습, 최적화 solver, 문제 생성은 모두 0회다. 첫 M106 판정을 바꾸지 않는다.

채널 0은 normalized cost, 채널 1은 affine dual-fit residual이다.
학습 원본에서 열 간 표준편차 중앙값은 각각 0.72693, 0.36115였다.
M106에서는 각각 1.76e-16, 1.63e-16으로 수치 오차 수준이다.
등록된 1e-8 채널 변동 기준을 적용하면 학습 48/48은 6개 채널,
전이 16/16은 4개 채널만 열을 구분한다. 크기·bias 채널은 원래부터
같은 문제의 열 사이에서 일정하다. 이는 문제 간 정보까지 없다는 뜻이 아니다.

## 왜 이렇게 되는가

이 BP 원본의 `A=[X,-X]`, 단위 열 norm, `c=1` 조건에서는 normalized cost
`q=1`이다. 기존 affine dual-fit의 우변 `center @ (q-q.mean())`는 0이므로
`y=0`, `a=1`, residual `q-D.T@y-a=0`이다. 따라서 비용과 residual 채널이
서로 다른 열을 구분하지 못한다. 실제 source의 작은 부동소수점 norm 오차를
포함해도 위 결과는 유지됐다.

±열 쌍은 채널 2/3의 부호를 바꾸고 채널 0/1/4/5/6/7은 그대로 둔다.
16개 원본에서 행렬 ±짝 오차와 두 채널 대칭 오차의 최대값은 모두 0이다.
남은 채널에는 원래 b와의 상관, 근사 primal, 절댓값 관계가 들어 있다.
이 분석은 4개 특징으로 최적 support를 알아낼 수 없다는 증명이 아니다.

## 원인에 대한 결론과 개발 결정

H3 feature shift의 구체적인 **관측 근거**는 확보했다. H1 학습 목표 불일치와
분리한 재학습 대조 실험은 없으므로 전이 실패의 단독 원인으로 확정하지 않는다.
최적 primal을 얻은 기존 경로도 dual 때문에 거절된 사실과 함께 해석해야 한다.
또한 별도 Phase2에서 무료 support+무료 dual조차 강한 Native 대비 10배 여유가
없었으므로, 특징을 늘리거나 모델을 바꾸는 작업은 지금 승인되지 않는다.

**HOLD_LEARNING.** 단순 refit, 더 큰 MLP, relational model을 동시에 만들지 않는다.
향후 경제적 여유가 있는 문제군이 확인되면 충분성·인증을 고려하는 발견 목표와
새 구조 평가가 필요하다. 이 결과는 해당 설계에 참고할 개발 증거다.

재현: `python research/audit/analyze_feature_transfer.py`.
원본 함수 `experiments/lp_equivalence_quotient_v099.py` SHA256:
`784b48bf0c5456e1a0ddb2314b221f75bb3beda849e18bc4be5762537f7e5399`.
수치는 `FEATURE_TRANSFER_DIAGNOSTICS.csv/.json`에 보존했다.
