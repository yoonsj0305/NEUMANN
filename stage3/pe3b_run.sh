#!/bin/bash
# 3-B driver (stage3/DESIGN.md 8.3, 8.5): 9 tasks x {rel_rand, nope} at the default LR, then LR x0.5 / x2 for the
# task / baseline pairs that pe3b.py tunelist names; 4 runs at a time, 1 thread each.  Re-runnable (finished runs skipped,
# unfinished ones resumed).  PY must point to the python with torch.
cd "$(dirname "$0")/.."
R=stage3/results/3-B
mkdir -p $R/logs
log() { echo "$(date -u '+%Y-%m-%d %H:%M:%S') $*" >> $R/QUEUE_LOG.txt; }
run() {   # name, task, kind, mult
  name=$1; t=$2; k=$3; m=$4
  tag=""; [ "$m" != "1.0" ] && tag="__lrx${m%.0}"
  d=$R/3b_${t}__${k}__1M__s0__N100000$tag
  [ -f $d/final.json ] && return 0
  res=""; [ -f $d/log.jsonl ] && res="--resume"
  OMP_NUM_THREADS=1 $PY stage3/pe3b.py run --task $t --kind $k --lr-mult $m $res > $R/logs/$name.out 2>&1
  log "exit $name code $?"
}
export -f run log; export R PY
log "driver start (3-B)"
for k in rel_rand nope; do for t in interleave dup repeat addition reverse pairswap mul1 copy prefix_sum; do
  echo "${t}__${k}__lr1 $t $k 1.0"; done; done | sed 's/ *$//' | xargs -P4 -L1 bash -c 'run "$@"' _
log "default LR done"
$PY stage3/pe3b.py tunelist > $R/tunelist.txt 2>> $R/QUEUE_LOG.txt || { log "tunelist failed"; exit 1; }
log "tuning runs: $(wc -l < $R/tunelist.txt)"
while read t k m; do echo "${t}__${k}__lr$m $t $k $m"; done < $R/tunelist.txt | sed 's/ *$//' | xargs -P4 -L1 bash -c 'run "$@"' _
log "driver end (3-B)"
