#!/bin/bash
# 3-P P0 follow-up driver (after stage3/p0_run.sh).
# The first tape_rnn addition / N x 1 runs died before their first evaluation with "LLVM compilation error: Cannot
# allocate memory" (these two tasks compile one executable per (prompt length, answer length) shape and reached the
# kernel limit vm.max_map_count = 65530; RAM was 3 of 15 GB).  The limit was raised to 1048576 (no code change); the
# reruns go to a separate directory (rule 5): stage3/results/3-P/p0_mmapfix.  p0_run.sh stops at `tunelist` because
# those two final.json files are missing, so this script also runs the lr x0.5 / x2 runs for all 22 runs.
# Usage: bash stage3/p0_run2.sh PY PKG_PARENT DRIVER_PID
PY=$1; PKG=$2; DPID=$3
R=stage3/results/3-P/p0; R2=stage3/results/3-P/p0_mmapfix
mkdir -p $R2/logs
export XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1"
log() { echo "$(date -u '+%F %T') $*" >> $R/QUEUE_LOG.txt; }
while kill -0 $DPID 2>/dev/null; do sleep 60; done
sysctl -w vm.max_map_count=1048576 > /dev/null
log "follow-up driver start (P0; vm.max_map_count=$(cat /proc/sys/vm/max_map_count))"
needs() {  # needs OUTDIR TASK ARCH -> exit 0 if lr x0.5 / x2 are required (10.3: in-dist < 0.95 or bin 2 >= 0.10)
  $PY -c "import json,sys; j=json.load(open('$1/p0_$2__$3__s0/final.json'))['judgment']['acc']; l=list(j); \
sys.exit(0 if (j[l[0]]<0.95 or j[l[2]]>=0.10) else 1)"
}
one() {  # one OUTDIR TASK ARCH MULT
  o=$1; t=$2; a=$3; m=$4; tag=""; [ "$m" != "1" ] && tag="__lrx$m"; name=${t}__${a}__lr$m
  [ -f $o/p0_${t}__${a}__s0${tag}/final.json ] && { log "skip $o $name (final.json)"; return; }
  P0_OUT=$o $PY stage3/p0.py run --task $t --arch $a --lr-mult $m $PKG > $o/logs/$name.out 2>&1
  log "exit $o $name code $?"
}
job() {  # job rerun T A  |  job tune OUTDIR T A
  if [ "$1" = rerun ]; then
    one $R2 $2 $3 1
    needs $R2 $2 $3 && { one $R2 $2 $3 0.5; one $R2 $2 $3 2.0; }
  else
    one $2 $3 $4 0.5; one $2 $3 $4 2.0
  fi
}
export -f log needs one job; export PY PKG R R2
{
  echo "rerun addition tape_rnn"; echo "rerun mul1 tape_rnn"
  for a in tape_rnn stack_rnn; do for t in addition interleave dup duplicate_string mul1 copy prefix_sum reverse pairswap reverse_string even_pairs; do
    [ -f $R/p0_${t}__${a}__s0/final.json ] || continue
    needs $R $t $a && echo "tune $R $t $a"
  done; done
} > $R2/joblist.txt
log "follow-up jobs: $(wc -l < $R2/joblist.txt)"
xargs -r -P4 -L1 bash -c 'job "$@"' _ < $R2/joblist.txt
log "driver end (P0 follow-up)"
