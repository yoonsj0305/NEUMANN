#!/usr/bin/env bash
# C-1 A-arm driver: 45 students (5 tasks x 3 compiled tables x {C r0, C r1, M r0}), 4 at a time, 1 thread each;
# then the 15 selections (committed and pushed before any out-of-distribution value is read), the diagnostics and the
# report.  Resumable.   PY=<python> bash stage2/c1_run.sh
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}
R=stage2/results/c1
export PY R OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
mkdir -p "$R/logs"
log() { echo "$(date -u '+%Y-%m-%d %H:%M:%S') $*" >> "$R/QUEUE_LOG.txt"; }
log "driver start"
jobs=$(mktemp)
for t in addition mul1 reverse copy prefix_sum; do for i in 1 2 3; do
  echo "$t $i C 0"; echo "$t $i C 1"; echo "$t $i M 0"; done; done > "$jobs"
xargs -P4 -L1 bash -c '
arm=$2; kind=hardread; [ "$arm" = M ] && kind=hardread_mlp
s=$((30 + $1 + 100 * $3))
d=$R/c1_$0__${kind}__1M__s${s}__N100000__table$1
[ -f $d/final.json ] && exit 0
res=""; [ -f $d/log.jsonl ] && res="--resume"
echo "$(date -u "+%Y-%m-%d %H:%M:%S") launch $0 table$1 $2 r$3 $res" >> $R/QUEUE_LOG.txt
$PY stage2/c1.py train --task $0 --table $1 --arm $2 --restart $3 $res >> $R/logs/train_$0_$1_$2_$3.out 2>&1
echo "$(date -u "+%Y-%m-%d %H:%M:%S") exit train $0 table$1 $2 r$3 code $?" >> $R/QUEUE_LOG.txt' < "$jobs"
rm -f "$jobs"
for t in addition mul1 reverse copy prefix_sum; do for i in 1 2 3; do echo "$t $i"; done; done |
xargs -P4 -L1 bash -c '[ -f $R/selection_$0_table$1.json ] || { $PY stage2/c1.py select --task $0 --table $1 > $R/logs/select_$0_$1.out 2>&1; echo "$(date -u "+%Y-%m-%d %H:%M:%S") exit select $0 table$1 code $?" >> $R/QUEUE_LOG.txt; }'
git add $R/selection_*.json $R/QUEUE_LOG.txt && git commit -q -m "stage2 C-1: selections of the 15 tables (committed before any out-of-distribution value is read)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VSWBvg7gXA6QqLM5pig7M5" && git push -q origin stage2/c && log "selections committed $(git rev-parse --short HEAD)"
for t in addition mul1 reverse copy prefix_sum; do for i in 1 2 3; do echo "$t $i C"; echo "$t $i M"; done; done |
xargs -P4 -L1 bash -c '$PY stage2/c1.py diag --task $0 --table $1 --arm $2 > $R/logs/diag_$0_$1_$2.out 2>&1; echo "$(date -u "+%Y-%m-%d %H:%M:%S") exit diag $0 table$1 $2 code $?" >> $R/QUEUE_LOG.txt'
$PY stage2/c1.py report > "$R/report.md" 2>&1; log "exit report code $?"
log "driver end"
