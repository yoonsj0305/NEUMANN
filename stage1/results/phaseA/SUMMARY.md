| task | baseline | params | N | steps (stop) | in-dist (last / best) | out-of-dist bins (last) | looped fixed-4 bins | train FLOPs | train / eval wall-clock |
|---|---|---|---|---|---|---|---|---|---|
| addition | abacus | 856960 | 100000 | 13000 (early) | 0.998 / 0.998 | 11-20 0.170 · 21-30 0.000 · 31-40 0.000 | — | 1.36e+14 | 2085 s / 48 s |
| addition | looped | 835824 | 100000 | 14000 (early) | 0.992 / 0.997 | 11-20 0.000 · 21-30 0.000 · 31-40 0.000 | 11-20 0.108 · 21-30 0.000 · 31-40 0.000 | 5.42e+14 | 6476 s / 548 s |
| addition | gru | 851456 | 100000 | 20000 (max) | 0.896 / 0.896 | 11-20 0.036 · 21-30 0.000 · 31-40 0.000 | — | 2.05e+14 | 2796 s / 53 s |
| parity | abacus | 856960 | 100000 | 12000 (early) | 0.995 / 0.995 | 17-32 0.586 · 33-48 0.488 · 49-64 0.462 | — | 7.18e+13 | 1111 s / 24 s |
| parity | looped | 835824 | 100000 | 11000 (early) | 0.992 / 0.995 | 17-32 0.658 · 33-48 0.492 · 49-64 0.462 | 17-32 0.548 · 33-48 0.508 · 49-64 0.538 | 2.44e+14 | 2995 s / 241 s |
| parity | gru | 851456 | 100000 | 2000 (early) | 1.000 / 1.000 | 17-32 1.000 · 33-48 1.000 · 49-64 1.000 | — | 1.19e+13 | 168 s / 3 s |
| reachability | abacus | 856960 | 100000 | 20000 (max) | 0.500 / 0.509 | 9-16 0.518 · 17-24 0.482 · 25-32 0.484 | — | 3.62e+14 | 5211 s / 155 s |
| reachability | looped | 835824 | 100000 | 20000 (max) | 0.524 / 0.524 | 9-16 0.536 · 17-24 0.488 · 25-32 0.484 | 9-16 0.538 · 17-24 0.486 · 25-32 0.502 | 1.33e+15 | 15610 s / 1721 s |
| reachability | gru | 851456 | 100000 | 20000 (max) | 0.690 / 0.694 | 9-16 0.594 · 17-24 0.562 · 25-32 0.508 | — | 3.45e+14 | 4649 s / 103 s |

Phase A criteria (CLAUDE.md), in-distribution accuracy at the last evaluation:
* addition: abacus in-distribution >= 0.95: 0.998 → met
* addition: looped in-distribution >= 0.95: 0.992 → met
* parity: GRU in-distribution >= 0.95: 1.000 → met
* parity: abacus in-distribution (recorded as a result, no threshold): 0.995
* parity: looped in-distribution (recorded as a result, no threshold): 0.992
* all thresholds met: yes

Interrupted by the session's 2-hour background limit and resumed from the last checkpoint (steps after it were recomputed; recorded FLOPs and wall-clock count each step once; see QUEUE_LOG.txt):
* addition/abacus: 2 segments
* addition/gru: 2 segments
* reachability/looped: 3 segments
* reachability/gru: 2 segments

Wall-clock: one CPU thread per run, up to 4 runs at once on a 4-core CPU (no GPU); times are not corrected for contention.
