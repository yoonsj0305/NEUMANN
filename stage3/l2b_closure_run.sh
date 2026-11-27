#!/bin/bash
# L2b-0 11.7-1, 11.7-2 (model-independent): routing and key closure for the six C-1 tables; table 0 = the C-1a hand
# table, a diagnostic of the cause (not an admission table).  One process at lowest priority.
PY=$1; R=stage3/results/L2b-0/H; mkdir -p $R/logs
for m in mul1 add; do for i in 1 2 3 0; do
  [ -f $R/closure_${m}_table$i.json ] || nice -n 19 $PY stage3/l2b_h.py closure --module $m --table $i > $R/logs/closure_${m}_table$i.out 2>&1
  echo "$(date -u '+%F %T') exit closure $m table$i code $?" >> $R/QUEUE_LOG.txt
done; done
