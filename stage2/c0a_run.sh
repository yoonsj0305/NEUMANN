#!/usr/bin/env bash
# C-0a O arm driver: the five students (seed 21), 4 at a time, 1 thread each; resumable (--resume for unfinished
# runs, finished runs skipped); then the report.   PY=<python> bash stage2/c0a_run.sh
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}
R=stage2/results/c0a
export PY R OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
mkdir -p "$R/logs"
echo "$(date -u '+%Y-%m-%d %H:%M:%S') driver start" >> "$R/QUEUE_LOG.txt"
printf "%s\n" addition copy mul1 prefix_sum reverse | xargs -P4 -I{} bash -c '
d=$R/c0a_{}__coupled__1M__s21__N100000__oracle
[ -f $d/final.json ] && exit 0
res=""; [ -f $d/log.jsonl ] && res="--resume"
echo "$(date -u "+%Y-%m-%d %H:%M:%S") launch {} $res" >> $R/QUEUE_LOG.txt
$PY stage2/c0a.py train --task {} $res >> $R/logs/train_{}.out 2>&1
echo "$(date -u "+%Y-%m-%d %H:%M:%S") exit {} code $?" >> $R/QUEUE_LOG.txt'
$PY stage2/c0a.py report > "$R/report.md" 2>&1
echo "$(date -u '+%Y-%m-%d %H:%M:%S') driver end (report code $?)" >> "$R/QUEUE_LOG.txt"
