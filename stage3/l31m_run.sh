#!/bin/bash
# 3-1 main run (DESIGN 6.7 with 6.9-6.13).  Phase "choose": rope teachers 41-43 (restart s + 200 if select:<task>
# exact match < 0.95), substitution dependency on the 400, routing Q 1-4, output state, selection -> choice files.
# Phase "students": students s + 10 and s + 110 on the chosen programs, student selection.  The selections are
# committed after each phase, before any out-of-distribution value is read.  Re-runnable: finished steps are skipped.
set -u
cd "$(dirname "$0")/.."
R=stage3/results/3-1/main
mkdir -p $R/logs
LOG=$R/QUEUE_LOG.txt
export OMP_NUM_THREADS=1
log() { echo "$(date -u '+%F %T') $*" >> $LOG; }
run() { name=$1; shift; $PY "$@" > $R/logs/$name.out 2>&1; log "exit $name code $?"; }
export -f run log; export PY R LOG
TASKS="dup interleave repeat pairswap"
PHASE=${1:-choose}
log "driver start (3-1 main, phase $PHASE)"
passed() { python3 -c "import json,sys;sys.exit(0 if json.load(open('$1'))['passed'] else 1)"; }
teach() {   # arguments: task:seed pairs
  for ts in "$@"; do t=${ts%%:*}; s=${ts##*:}
    [ -f $R/l31_${t}__rope__1M__s${s}__N100000/final.json ] && continue
    res=""; [ -f $R/l31_${t}__rope__1M__s${s}__N100000/log.jsonl ] && res="--resume"
    echo "teacher_${t}_s$s stage3/l_adapter.py run --task $t --kind rope --scale 1M --seed $s --N 100000 --phase l31 --out-root $R --threads 1 --keep-best $res"
  done | sed 's/ *$//' | xargs -P4 -L1 bash -c 'run "$@"' _
  for ts in "$@"; do t=${ts%%:*}; s=${ts##*:}
    [ -f $R/teacher_select_${t}_s$s.json ] || echo "tcheck_${t}_s$s stage3/l31m.py teacher_check --task $t --seed $s"
  done | sed 's/ *$//' | xargs -P4 -L1 bash -c 'run "$@"' _
}
if [ "$PHASE" = choose ]; then
  teach $(for t in $TASKS; do for s in 41 42 43; do echo $t:$s; done; done)
  RE=""
  for t in $TASKS; do for s in 41 42 43; do passed $R/teacher_select_${t}_s$s.json || RE="$RE $t:$((s+200))"; done; done
  [ -n "$RE" ] && log "teacher restarts needed:$RE" && teach $RE
  for t in $TASKS; do for s in 41 42 43; do
    [ -f $R/choice_${t}_t$s.json ] || echo "choose_${t}_t$s stage3/l31m.py choose --task $t --seed $s"
  done; done | sed 's/ *$//' | xargs -P4 -L1 bash -c 'run "$@"' _
fi
if [ "$PHASE" = students ]; then
  for t in $TASKS; do for s in 41 42 43; do [ -f $R/choice_${t}_t$s.json ] || continue; for r in 0 1; do
    sd=$(( s + 10 + 100 * r )); d=$R/l31_${t}__l1read__1M__s${sd}__N100000__synth_t$s
    [ -f $d/final.json ] && continue; res=""; [ -f $d/log.jsonl ] && res="--resume"
    echo "student_${t}_t${s}_r$r stage3/l31m.py train --task $t --seed $s --restart $r $res"
  done; done; done | sed 's/ *$//' | xargs -P4 -L1 bash -c 'run "$@"' _
  for t in $TASKS; do for s in 41 42 43; do
    [ -f $R/choice_${t}_t$s.json ] && [ ! -f $R/selection_${t}_t$s.json ] && echo "select_${t}_t$s stage3/l31m.py select --task $t --seed $s"
  done; done | sed 's/ *$//' | xargs -P4 -L1 bash -c 'run "$@"' _
fi
log "driver end (phase $PHASE)"
