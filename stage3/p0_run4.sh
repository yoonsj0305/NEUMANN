#!/bin/bash
# 3-P P0 driver 4 (replaces p0_run3.sh, kept as the record).  Why: tape_rnn N x 1 / addition compile one executable
# per (prompt length, answer length) and their training memory grows to ~6 GB (N x 1, 29 train shapes); the memory
# cgroup limit is 14.0 GB for all runs together, and driver3 would have started stack_rnn addition / N x 1 next to them.
# Changes (none changes the computation; tested identical logs):
#  - big jobs (addition, mul1 for both models) run one at a time (flock), tape_rnn addition last;
#  - p0.py takes a per-run lock (exit 75 if the run is already going) and, with P0_RSS_FREE_MB, frees the
#    evaluation-only executables after an evaluation when the process is above that RSS;
#  - MALLOC_ARENA_MAX=2.
# Jobs are idempotent (final.json -> skip, ckpt.pt -> resume, running -> wait).  After a container restart run it again.
# Usage: bash stage3/p0_run4.sh PY PKG_PARENT
PY=$1; PKG=$2
R=stage3/results/3-P/p0; R2=stage3/results/3-P/p0_mmapfix
mkdir -p $R/logs $R2/logs
export XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1" MALLOC_ARENA_MAX=2
export P0_RSS_FREE_MB=5000
log() { echo "$(date -u '+%F %T') $*" >> $R/QUEUE_LOG.txt; }
sysctl -w vm.max_map_count=1048576 > /dev/null
log "driver4 start (P0; vm.max_map_count=$(cat /proc/sys/vm/max_map_count))"
needs() {  # needs OUTDIR TASK ARCH -> exit 0 if lr x0.5 / x2 are required (10.3)
  $PY -c "import json,sys; j=json.load(open('$1/p0_$2__$3__s0/final.json'))['judgment']['acc']; l=list(j); \
sys.exit(0 if (j[l[0]]<0.95 or j[l[2]]>=0.10) else 1)"
}
one() {  # one OUTDIR TASK ARCH MULT
  o=$1; t=$2; a=$3; m=$4; tag=""; [ "$m" != "1" ] && tag="__lrx$m"; name=${t}__${a}__lr$m
  while true; do
    [ -f $o/p0_${t}__${a}__s0${tag}/final.json ] && return 0
    if pgrep -f -- "p0.py run --task $t --arch $a --lr-mult $m " > /dev/null; then sleep 60; continue; fi
    P0_OUT=$o $PY stage3/p0.py run --task $t --arch $a --lr-mult $m $PKG >> $o/logs/$name.out 2>&1
    rc=$?; [ $rc = 75 ] && { sleep 60; continue; }
    log "exit $o $name code $rc"; return $rc
  done
}
job() {  # job OUTDIR TASK ARCH
  case $2 in addition|mul1) exec 9> $R/.big.lock; flock 9;; esac
  one $1 $2 $3 1 || return
  needs $1 $2 $3 && { one $1 $2 $3 0.5; one $1 $2 $3 2.0; }
}
export -f log needs one job; export PY PKG R R2
{
  for t in dup copy prefix_sum reverse pairswap reverse_string even_pairs interleave duplicate_string; do echo "$R $t tape_rnn"; done
  echo "$R2 mul1 tape_rnn"
  for t in interleave dup duplicate_string copy prefix_sum reverse pairswap reverse_string even_pairs; do echo "$R $t stack_rnn"; done
  echo "$R mul1 stack_rnn"; echo "$R addition stack_rnn"; echo "$R2 addition tape_rnn"
} | xargs -P4 -L1 bash -c 'job "$@"' _
log "driver4 end (P0)"
