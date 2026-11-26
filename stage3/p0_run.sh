#!/bin/bash
# 3-P P0 driver: 22 default-lr runs (11 tasks x stack_rnn / tape_rnn), 4 at a time, 1 thread each, then the lr x0.5 /
# x2 runs that `p0.py tunelist` names.  Finished runs (final.json) are skipped; an unfinished run restarts from step 0
# (no checkpoints).  Usage: bash stage3/p0_run.sh PY PKG_PARENT
PY=$1; PKG=$2
R=stage3/results/3-P/p0
mkdir -p $R/logs
export XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1"
log() { echo "$(date -u '+%F %T') $*" >> $R/QUEUE_LOG.txt; }
run() {
  name=$1; t=$2; a=$3; m=$4
  tag=""; [ "$m" != "1" ] && tag="__lrx$m"
  [ -f $R/p0_${t}__${a}__s0${tag}/final.json ] && { log "skip $name (final.json)"; return; }
  $PY stage3/p0.py run --task $t --arch $a --lr-mult $m $PKG > $R/logs/$name.out 2>&1
  log "exit $name code $?"
}
export -f run log; export PY PKG R
log "driver start (P0)"
for a in tape_rnn stack_rnn; do for t in addition interleave dup duplicate_string mul1 copy prefix_sum reverse pairswap reverse_string even_pairs; do
  echo "${t}__${a}__lr1 $t $a 1"; done; done | xargs -P4 -L1 bash -c 'run "$@"' _
log "default lr done"
$PY stage3/p0.py tunelist > $R/tunelist.txt 2>> $R/QUEUE_LOG.txt || { log "tunelist failed"; exit 1; }
log "tuning runs: $(wc -l < $R/tunelist.txt)"
while read t a m; do echo "${t}__${a}__lr$m $t $a $m"; done < $R/tunelist.txt | xargs -r -P4 -L1 bash -c 'run "$@"' _
log "driver end (P0)"
