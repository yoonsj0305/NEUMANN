#!/usr/bin/env bash
# C-1a driver: 10 students (5 tasks x arm C hardread / arm M hardread_mlp, seed 21, --keep-best), 4 at a time, 1 thread
# each; then the reads-removed drops and the report.  Resumable.   PY=<python> bash stage2/c1a_run.sh
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}
R=stage2/results/c1a
export PY R OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
mkdir -p "$R/logs"
echo "$(date -u '+%Y-%m-%d %H:%M:%S') driver start" >> "$R/QUEUE_LOG.txt"
printf "%s\n" "addition C hardread" "mul1 C hardread" "reverse C hardread" "prefix_sum C hardread" "copy C hardread" \
  "addition M hardread_mlp" "mul1 M hardread_mlp" "reverse M hardread_mlp" "prefix_sum M hardread_mlp" "copy M hardread_mlp" |
xargs -P4 -L1 bash -c '
d=$R/c1a_$0__$2__1M__s21__N100000__oracle
if [ ! -f $d/final.json ]; then
  res=""; [ -f $d/log.jsonl ] && res="--resume"
  echo "$(date -u "+%Y-%m-%d %H:%M:%S") launch $0 $1 $res" >> $R/QUEUE_LOG.txt
  $PY stage2/c1a.py train --task $0 --arm $1 $res >> $R/logs/train_$0_$1.out 2>&1
  echo "$(date -u "+%Y-%m-%d %H:%M:%S") exit train $0 $1 code $?" >> $R/QUEUE_LOG.txt
fi
$PY stage2/c1a.py diag --task $0 --arm $1 > $R/logs/diag_$0_$1.out 2>&1
echo "$(date -u "+%Y-%m-%d %H:%M:%S") exit diag $0 $1 code $?" >> $R/QUEUE_LOG.txt'
$PY stage2/c1a.py report > "$R/report.md" 2>&1
echo "$(date -u '+%Y-%m-%d %H:%M:%S') driver end (report code $?)" >> "$R/QUEUE_LOG.txt"
