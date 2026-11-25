#!/bin/bash
# E-0 segment: run the given e0.py runs in parallel (1 thread each, --resume); each checkpoints and exits after
# MAX_WALL seconds (code 3) so a 2-hour tool limit never loses work.  QUEUE_LOG.txt records every start and exit.
cd "$(dirname "$0")/.."
LOG=stage2/results/e0/QUEUE_LOG.txt
MAX_WALL=${MAX_WALL:-6900}
EXTRA=${EXTRA:-}
for r in "$@"; do
  (
    echo "$(date '+%F %T') launch $r $EXTRA max_wall=$MAX_WALL" >> $LOG
    python stage2/e0.py --run "$r" --resume --max-wall "$MAX_WALL" $EXTRA >> "${OUT_DIR:-/tmp}/e0_$r.stdout" 2>&1
    rc=$?
    echo "$(date '+%F %T') exit $rc $r" >> $LOG
  ) &
done
wait
