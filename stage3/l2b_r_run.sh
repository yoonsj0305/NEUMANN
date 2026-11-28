#!/bin/bash
# L2b-0 R (stage3/DESIGN.md 11.10-1): multi_add then mulNM with the admitted H' modules; idempotent (bins in log.jsonl kept).
PY=$1; R=stage3/results/L2b-0/R; mkdir -p $R/logs
log() { echo "$(date -u '+%F %T') $*" >> $R/QUEUE_LOG.txt; }
for t in multi_add mulNM; do
  [ -f $R/$t/final.json ] && continue
  log "launch $t"; nice -n 10 $PY stage3/l2b_r.py run --task $t >> $R/logs/$t.out 2>&1; log "exit $t code $?"
done
log "driver end (R)"
