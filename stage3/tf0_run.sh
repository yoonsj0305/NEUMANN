#!/bin/bash
# TF-0 (stage3/DESIGN.md 12.3, 12.5): the five tasks one after another, one process at nice 10 (P0 first).
# Idempotent (final.json with Hprime_checks_pass -> skip).  Usage: bash stage3/tf0_run.sh PY
PY=$1; R=stage3/results/TF-0; mkdir -p $R/logs
log() { echo "$(date -u '+%F %T') $*" >> $R/QUEUE_LOG.txt; }
log "driver start (TF-0)"
for t in copy reverse prefix_sum mul1 addition; do
  [ -f $R/$t/final.json ] && grep -q '"Hprime_checks_pass"\|"stopped"' $R/$t/final.json && continue
  log "launch $t"; nice -n 10 $PY stage3/tf0.py run --task $t > $R/logs/$t.out 2>&1; log "exit $t code $?"
done
log "driver end (TF-0)"
