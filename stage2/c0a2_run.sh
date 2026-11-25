#!/usr/bin/env bash
# C-0a' driver: five students (seed 21, 1-layer shared table, --keep-best), 4 at a time, 1 thread each; then the
# in-distribution drops and the report.  Resumable.   PY=<python> bash stage2/c0a2_run.sh
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}
R=stage2/results/c0a2
export PY R OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
mkdir -p "$R/logs"
echo "$(date -u '+%Y-%m-%d %H:%M:%S') driver start" >> "$R/QUEUE_LOG.txt"
printf "%s\n" addition copy mul1 prefix_sum reverse | xargs -P4 -I{} bash -c '
d=$R/c0a2_{}__coupled__1M__s21__N100000__shared_1layer
if [ ! -f $d/final.json ]; then
  res=""; [ -f $d/log.jsonl ] && res="--resume"
  echo "$(date -u "+%Y-%m-%d %H:%M:%S") launch {} $res" >> $R/QUEUE_LOG.txt
  $PY stage2/c0a2.py train --task {} $res >> $R/logs/train_{}.out 2>&1
  echo "$(date -u "+%Y-%m-%d %H:%M:%S") exit train {} code $?" >> $R/QUEUE_LOG.txt
fi
$PY stage2/c0a2.py diag --task {} > $R/logs/diag_{}.out 2>&1
echo "$(date -u "+%Y-%m-%d %H:%M:%S") exit diag {} code $?" >> $R/QUEUE_LOG.txt'
$PY stage2/c0a2.py report > "$R/report.md" 2>&1
echo "$(date -u '+%Y-%m-%d %H:%M:%S') driver end (report code $?)" >> "$R/QUEUE_LOG.txt"
