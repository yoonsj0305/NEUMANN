#!/bin/bash
# L2b-0 H' (stage3/DESIGN.md 11.8-11.10): minimal sufficient key search + checks for the six C-1 tables, one process at
# low priority (P0 has priority).  Idempotent (final.json -> skip).  Usage: bash stage3/l2b_hp_run.sh PY
PY=$1; R=stage3/results/L2b-0/Hprime; mkdir -p $R/logs
log() { echo "$(date -u '+%F %T') $*" >> $R/QUEUE_LOG.txt; }
log "driver start (H')"
for m in mul1 add; do for i in 1 2 3; do
  [ -f $R/${m}_table$i/final.json ] && continue
  log "launch $m table$i"
  nice -n 10 $PY stage3/l2b_hprime.py search --module $m --table $i > $R/logs/${m}_table$i.out 2>&1
  log "exit $m table$i code $?"
done; done
log "driver end (H')"
