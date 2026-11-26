#!/bin/bash
# 3-P P0 driver, restartable (replaces stage3/p0_run.sh and stage3/p0_run2.sh, which stay as the record).
# Why: the container restarted at about 16:00 UTC on 2026-11-26 and killed every run (no checkpoints then).
# stage3/p0.py now checkpoints after every evaluation (ckpt.pt, git-ignored) and resumes from it bit-identically
# (tested: a run killed at step 20 and resumed gives the same log.jsonl as an uninterrupted run).
# The partial logs of the runs that died are kept as p0_<run>.interrupted1 (they restart from step 0).
# Each job = one default-lr run, then (10.3: in-distribution < 0.95 or bin 2 >= 0.10) the lr x0.5 and x2 runs.
# Jobs are idempotent: final.json -> skip, ckpt.pt -> resume.  After a container restart run this script again.
# tape_rnn addition / N x 1 live in p0_mmapfix (first attempts died on vm.max_map_count; see QUEUE_LOG).
# Usage: bash stage3/p0_run3.sh PY PKG_PARENT
PY=$1; PKG=$2
R=stage3/results/3-P/p0; R2=stage3/results/3-P/p0_mmapfix
mkdir -p $R/logs $R2/logs
export XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1"
log() { echo "$(date -u '+%F %T') $*" >> $R/QUEUE_LOG.txt; }
sysctl -w vm.max_map_count=1048576 > /dev/null
log "driver3 start (P0; vm.max_map_count=$(cat /proc/sys/vm/max_map_count))"
needs() {  # needs OUTDIR TASK ARCH -> exit 0 if lr x0.5 / x2 are required
  $PY -c "import json,sys; j=json.load(open('$1/p0_$2__$3__s0/final.json'))['judgment']['acc']; l=list(j); \
sys.exit(0 if (j[l[0]]<0.95 or j[l[2]]>=0.10) else 1)"
}
one() {  # one OUTDIR TASK ARCH MULT
  o=$1; t=$2; a=$3; m=$4; tag=""; [ "$m" != "1" ] && tag="__lrx$m"; name=${t}__${a}__lr$m
  [ -f $o/p0_${t}__${a}__s0${tag}/final.json ] && return 0
  P0_OUT=$o $PY stage3/p0.py run --task $t --arch $a --lr-mult $m $PKG >> $o/logs/$name.out 2>&1
  rc=$?; log "exit $o $name code $rc"; return $rc
}
job() {  # job OUTDIR TASK ARCH
  one $1 $2 $3 1 || return
  needs $1 $2 $3 && { one $1 $2 $3 0.5; one $1 $2 $3 2.0; }
}
export -f log needs one job; export PY PKG R R2
{
  echo "$R2 addition tape_rnn"; echo "$R2 mul1 tape_rnn"
  for t in dup copy prefix_sum reverse pairswap reverse_string even_pairs interleave duplicate_string; do echo "$R $t tape_rnn"; done
  for t in addition interleave dup duplicate_string mul1 copy prefix_sum reverse pairswap reverse_string even_pairs; do echo "$R $t stack_rnn"; done
} | xargs -P4 -L1 bash -c 'job "$@"' _
log "driver3 end (P0)"
