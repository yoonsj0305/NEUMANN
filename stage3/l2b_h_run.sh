#!/bin/bash
# L2b-0 H (stage3/DESIGN.md 11.6-1, 11.6-2): 18 MLP students (add, mul1 x tables 1-3 x seeds 230+i, 330+i, 430+i),
# 20,000 steps, no early stop.  One worker shared with 3-P P0 (P0 first: P0 keeps its four workers; this is a fifth
# process at normal priority).  Order: smallest seed first (11.7-4 admits the passing module with the smallest seed).
# Resumable (run.py --resume from ckpt.pt).  Usage: bash stage3/l2b_h_run.sh PY
PY=$1; R=stage3/results/L2b-0/H
mkdir -p $R/logs
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
log() { echo "$(date -u '+%F %T') $*" >> $R/QUEUE_LOG.txt; }
log "driver start (H training)"
for off in 230 330 430; do for i in 1 2 3; do for m in add mul1; do
  s=$((off + i)); t=$m; [ $m = add ] && t=addition
  d=$R/H_${t}__hardread_mlp__1M__s${s}__N100000__table$i
  [ -f $d/final.json ] && continue
  res=""; [ -f $d/log.jsonl ] && res="--resume"
  log "launch $m table$i s$s $res"
  $PY stage3/l2b_h.py train --module $m --table $i --seed $s $res >> $R/logs/train_${m}_table${i}_s${s}.out 2>&1
  log "exit $m table$i s$s code $?"
done; done; done
log "driver end (H training)"
