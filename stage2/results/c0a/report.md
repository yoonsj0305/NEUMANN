| 과제 | 판정 step (멈춤) | 분포 안 · 분포 밖 1 · 2 · 3 | 마지막 체크포인트 | 판정 시점 FLOPs | 학습 FLOPs | 시간 (학습 + 평가) | 밖 1·2 ≥0.90 |
|---|---|---|---|---|---|---|---|
| addition | 12000 (12000, early stop: in-distribution >= 99% at two consecutive evaluations) | 0.999 · 0.078 · 0.000 · 0.000 | 0.999 · 0.078 · 0.000 · 0.000 | 1.26e+14 | 1.26e+14 | 2076 s | 아니오 |
| copy | 4000 (5000, early stop: in-distribution >= 99% at two consecutive evaluations) | 0.998 · 0.348 · 0.000 · 0.000 | 0.993 · 0.310 · 0.000 · 0.000 | 2.79e+13 | 3.48e+13 | 592 s | 아니오 |
| mul1 | 10000 (10000, early stop: in-distribution >= 99% at two consecutive evaluations) | 0.999 · 0.144 · 0.000 · 0.000 | 0.999 · 0.144 · 0.000 · 0.000 | 7.94e+13 | 7.94e+13 | 1323 s | 아니오 |
| prefix_sum | 9000 (9000, early stop: in-distribution >= 99% at two consecutive evaluations) | 1.000 · 0.168 · 0.000 · 0.000 | 1.000 · 0.168 · 0.000 · 0.000 | 6.27e+13 | 6.27e+13 | 1057 s | 아니오 |
| reverse | 2000 (3000, early stop: in-distribution >= 99% at two consecutive evaluations) | 0.995 · 0.270 · 0.000 · 0.000 | 0.990 · 0.204 · 0.000 · 0.000 | 1.46e+13 | 2.19e+13 | 374 s | 아니오 |
tasks meeting: 0 of 5 -> pass False
