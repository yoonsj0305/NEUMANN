#!/bin/bash
# L2b-0 (stage3/DESIGN.md 11.3, 11.5): module reproduction, then M for add and mul1.  One worker, lowest CPU priority
# (branch A / P0 training has priority, CLAUDE.md).  Resumable (M writes one log line per finished bin).
# Usage: bash stage3/l2b0_run.sh PY
PY=$1; R=stage3/results/L2b-0
mkdir -p $R/logs
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
log() { echo "$(date -u '+%F %T') $*" >> $R/QUEUE_LOG.txt; }
log "driver start (repro, M add, M mul1)"
[ -f $R/module_repro.json ] || { nice -n 19 $PY stage3/recomb.py repro > $R/logs/repro.out 2>&1; log "exit repro code $?"; }
for m in add mul1; do
  [ -f $R/M_$m/final.json ] || { nice -n 19 $PY stage3/recomb.py measure --module $m >> $R/logs/M_$m.out 2>&1; log "exit M $m code $?"; }
done
log "driver end"
