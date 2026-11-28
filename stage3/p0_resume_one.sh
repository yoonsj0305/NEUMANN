#!/bin/bash
# Resume one P0 run that ended without final.json (e.g. OOM-killed) under driver4's settings and big-job lock.
# Usage: bash stage3/p0_resume_one.sh PY PKG OUTDIR TASK ARCH MULT
PY=$1; PKG=$2; o=$3; t=$4; a=$5; m=$6
R=stage3/results/3-P/p0
export XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1" MALLOC_ARENA_MAX=2 P0_RSS_FREE_MB=5000
log() { echo "$(date -u '+%F %T') $*" >> $R/QUEUE_LOG.txt; }
case $t in addition|mul1) exec 9> $R/.big.lock; flock 9;; esac
log "resume $o ${t}__${a}__lr$m (p0_resume_one.sh)"
P0_OUT=$o $PY stage3/p0.py run --task $t --arch $a --lr-mult $m $PKG >> $o/logs/${t}__${a}__lr$m.out 2>&1
log "exit $o ${t}__${a}__lr$m code $? (p0_resume_one.sh)"
