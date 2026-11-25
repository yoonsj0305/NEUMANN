#!/bin/bash
# 3-0 C and B (stage3/DESIGN.md 5.2): 16 baselines (4 tasks x abacus/rope/looped_rr/gru, seed 0, stage-1 protocol,
# --keep-best so the rope judgment checkpoint is the B teacher), then B per task, then the report.  Resumable.
#   PY=<python> bash stage3/l30_run.sh
set -u
cd "$(dirname "$0")/.."
R=stage3/results/3-0
Q=$R/QUEUE_LOG.txt
log() { echo "$(date -u '+%Y-%m-%d %H:%M:%S') $*" >> $Q; }
export OMP_NUM_THREADS=1 PY
log "driver start (C, B)"
jobs=""
for k in looped_rr abacus gru rope; do for t in interleave dup repeat pairswap; do jobs="$jobs $t:$k"; done; done
printf '%s\n' $jobs | xargs -P4 -I{} bash -c '
  t=${1%%:*}; k=${1##*:}; d='$R'/l30_${t}__${k}__1M__s0__N100000
  [ -f $d/final.json ] && exit 0
  extra=""; [ -f $d/log.jsonl ] && extra="--resume"
  $PY stage3/l_adapter.py run --task $t --kind $k --phase l30 --out-root '$R' --seed 0 --threads 1 --keep-best $extra \
     > '$R'/logs/base_${t}_${k}.out 2>&1
  echo "$(date -u "+%Y-%m-%d %H:%M:%S") exit baseline $t $k code $?" >> '$Q'' _ {}
for t in dup interleave repeat pairswap; do
  $PY stage3/l1.py b --task $t > $R/logs/b_$t.out 2>&1; log "exit b $t code $?"
done
$PY stage3/l1.py report > $R/report.json.out 2>&1; log "exit report code $?"
log "driver end"
