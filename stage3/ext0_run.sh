#!/bin/bash
# EXT-0 driver (stage3/DESIGN.md 13.6): checks -> control (15 tasks) -> library orders 0-4 -> judgment -> hand -> report.
# Every step is idempotent (cache / output files); after a container restart run it again.  One process at a time
# (CLAUDE.md resource rule: P0 + one job).  Usage: bash stage3/ext0_run.sh PY
PY=$1; R=stage3/results/EXT-0; mkdir -p $R/logs
log() { echo "$(date -u '+%F %T') $*" >> $R/QUEUE_LOG.txt; }
export OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1
log "driver start"
[ -f $R/checks/a_copy.json ] || $PY stage3/ext0.py check-a --task copy >> $R/logs/checks.log 2>&1
[ -f $R/checks/a_mul1.json ] || $PY stage3/ext0.py check-a --task mul1 >> $R/logs/checks.log 2>&1
[ -f $R/checks/bc.json ] || $PY stage3/ext0.py check-bc >> $R/logs/checks.log 2>&1
$PY -c "import json,sys; sys.exit(0 if all(json.load(open('$R/checks/'+f))['pass'] for f in ('a_copy.json','a_mul1.json','bc.json')) else 1)" \
  || { log "STOP: implementation check failed"; exit 1; }
log "checks pass"
$PY stage3/ext0.py control >> $R/logs/control.log 2>&1 || { log "control exit $?"; exit 1; }
log "control done"
for s in 0 1 2 3 4; do $PY stage3/ext0.py library --order $s >> $R/logs/library.log 2>&1 || { log "library $s exit $?"; exit 1; }; done
log "library done"
$PY stage3/ext0.py judge >> $R/logs/judge.log 2>&1 || { log "judge exit $?"; exit 1; }
log "judge done"
$PY stage3/ext0.py hand >> $R/logs/hand.log 2>&1 || { log "hand exit $?"; exit 1; }
$PY stage3/ext0.py report >> $R/logs/report.log 2>&1 || { log "report exit $?"; exit 1; }
log "driver end (EXT-0)"
