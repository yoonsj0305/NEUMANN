#!/usr/bin/env bash
# 3-1a3 gate (DESIGN 6.12 + 6.13): check 1 (five tasks), A2' (record), check 3' (record).  4 processes at a time.
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}
OUT=stage3/results/3-1/3-1a3
mkdir -p $OUT/logs
log() { echo "$(date -u '+%F %T') $*" >> $OUT/QUEUE_LOG.txt; }
log "driver start (3-1a3)"
job() {
  local cmd=$1 task=$2
  OMP_NUM_THREADS=1 $PY stage3/l31c.py $cmd --task $task > $OUT/logs/${cmd}_${task}.out 2>&1
  log "exit ${cmd}_${task} code $?"
}
export -f job log; export PY OUT
printf '%s\n' "gate1 interleave" "gate1 mqar" "a2p interleave" "a2p mqar" "gate1 dup" "gate1 repeat" "gate1 pairswap" \
  "a2p dup" "a2p repeat" "a2p pairswap" "gate3p dup" "gate3p interleave" "gate3p repeat" "gate3p pairswap" \
  | xargs -P4 -L1 bash -c 'job "$0" "$1"'
log "driver end"
