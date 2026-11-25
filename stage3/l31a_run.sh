#!/bin/bash
# 3-1a gate (stage3/DESIGN.md 6.6, 6.9): teacher dependencies, 51 CP-SAT solves (4 in parallel, 1 worker each,
# 600 s), then the three checks.  PY = python with torch + ortools; L31_CACHE = dependency cache (not committed).
set -u
cd "$(dirname "$0")/.."
R=stage3/results/3-1/3-1a
mkdir -p $R/logs
LOG=$R/QUEUE_LOG.txt
export OMP_NUM_THREADS=1
log() { echo "$(date -u '+%F %T') $*" >> $LOG; }
log "driver start (3-1a)"
run() { name=$1; shift; $PY stage3/l31.py "$@" > $R/logs/$name.out 2>&1; log "exit $name code $?"; }
export -f run log; export PY R LOG
T0=stage3/results/3-0
for t in dup interleave repeat pairswap; do echo "deps_$t deps --source teacher --task $t --teacher-run $T0/l30_${t}__rope__1M__s0__N100000"; done \
  | xargs -P4 -L1 bash -c 'run "$@"' _
{
for t in dup interleave repeat pairswap; do for q in 4 3 2 1; do
  echo "synth_teacher_${t}_Q$q synth --source teacher --task $t --teacher-run $T0/l30_${t}__rope__1M__s0__N100000 --Q $q"; done; done
for t in dup interleave repeat pairswap mqar; do for q in 4 3 2 1; do
  echo "synth_oracle_${t}_Q$q synth --source oracle --task $t --Q $q"; done; done
for t in addition copy mul1 prefix_sum reverse; do for i in 1 2 3; do
  echo "synth_l0_${t}_table$i synth --source l0 --task $t --table $i --Q 1"; done; done
} | xargs -P4 -L1 bash -c 'run "$@"' _
{
for t in dup interleave repeat pairswap mqar; do echo "gate1_$t gate1 --task $t"; done
for t in addition copy mul1 prefix_sum reverse; do echo "gate2_$t gate2 --task $t"; done
for t in dup interleave repeat pairswap; do echo "gate3_$t gate3 --task $t"; done
} | xargs -P4 -L1 bash -c 'run "$@"' _
log "driver end"
