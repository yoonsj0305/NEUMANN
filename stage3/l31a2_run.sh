#!/bin/bash
# 3-1a after the first revision (stage3/DESIGN.md 6.10, 6.11): check 1 (oracle, 5 tasks), check 3 (rope seed 0,
# substitution dependency, 600 s; if any task misses the corrected threshold: once more with 3,600 s), and the 3-0 A1
# MQAR re-measure with the t0 fix.  4 jobs at a time, one CP-SAT worker each.
set -u
cd "$(dirname "$0")/.."
R=stage3/results/3-1/3-1a2
mkdir -p $R/logs
LOG=$R/QUEUE_LOG.txt
export OMP_NUM_THREADS=1
log() { echo "$(date -u '+%F %T') $*" >> $LOG; }
run() { name=$1; shift; $PY stage3/l31b.py "$@" > $R/logs/$name.out 2>&1; log "exit $name code $?"; }
export -f run log; export PY R LOG
log "driver start (3-1a2)"
{
for t in dup interleave repeat pairswap; do echo "gate3_$t gate3 --task $t"; done
for t in dup interleave repeat pairswap mqar; do echo "gate1_$t gate1 --task $t"; done
echo "a1_30_mqar a1_30_mqar"
} | xargs -P4 -L1 bash -c 'run "$@"' _
miss=$(python3 -c "
import json
print(sum(not json.load(open('$R/gate3_%s.json' % t))['pass'] for t in ('dup','interleave','repeat','pairswap')))")
log "check 3 at 600 s: $miss task(s) below the threshold"
if [ "$miss" != "0" ]; then
  export L31_TIME=3600 L31B_GATE_DIR=3-1a2/t3600
  mkdir -p $R/t3600
  for t in dup interleave repeat pairswap; do echo "gate3_${t}_t3600 gate3 --task $t"; done | xargs -P4 -L1 bash -c 'run "$@"' _
fi
log "driver end"
