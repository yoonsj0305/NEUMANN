#!/bin/bash
# 3-1 main run (stage3/DESIGN.md 6.7 with 6.9): teachers rope seeds 41-43 (restart s + 200 if the selection-set
# in-distribution accuracy < 0.95), dependency extraction, CP-SAT synthesis Q = 1-4, Q selection, students s + 10 and
# s + 110, student selection.  Stops there: the selections are committed before any out-of-distribution value is read;
# the report is run after that commit.  Re-runnable: finished steps are skipped.
set -u
cd "$(dirname "$0")/.."
R=stage3/results/3-1
mkdir -p $R/logs
LOG=$R/QUEUE_LOG.txt
export OMP_NUM_THREADS=1
log() { echo "$(date -u '+%F %T') $*" >> $LOG; }
run() { name=$1; shift; $PY "$@" > $R/logs/$name.out 2>&1; log "exit $name code $?"; }
export -f run log; export PY R LOG
TASKS="dup interleave repeat pairswap"
log "driver start (3-1 main)"
teach() {   # seeds -> train the rope teachers that are not finished, then check them
  for t in $TASKS; do for s in "$@"; do
    [ -f $R/l31_${t}__rope__1M__s${s}__N100000/final.json ] && continue
    res=""; [ -f $R/l31_${t}__rope__1M__s${s}__N100000/log.jsonl ] && res="--resume"
    echo "teacher_${t}_s$s stage3/l_adapter.py run --task $t --kind rope --scale 1M --seed $s --N 100000 --phase l31 --out-root $R --threads 1 --keep-best $res"
  done; done | xargs -P4 -L1 bash -c 'run "$@"' _
  for t in $TASKS; do for s in "$@"; do
    [ -f $R/teacher_select_${t}_s$s.json ] || echo "tcheck_${t}_s$s stage3/l31.py teacher_check --task $t --seed $s"
  done; done | xargs -P4 -L1 bash -c 'run "$@"' _
}
teach 41 42 43
RE=""
for t in $TASKS; do for s in 41 42 43; do
  python3 -c "import json,sys;sys.exit(0 if json.load(open('$R/teacher_select_${t}_s$s.json'))['passed'] else 1)" || RE="$RE $((s+200))"
done; done
[ -n "$RE" ] && log "teacher restarts needed:$RE" && teach $(echo $RE | tr ' ' '\n' | sort -u)
used() { for x in $1 $(( $1 + 200 )); do f=$R/teacher_select_$2_s$x.json; [ -f $f ] && python3 -c "import json,sys;sys.exit(0 if json.load(open('$f'))['passed'] else 1)" && { echo $x; return; }; done; }
for t in $TASKS; do for s in 41 42 43; do u=$(used $s $t); [ -n "$u" ] && echo "deps_${t}_t$s stage3/l31.py deps --source teacher --task $t --teacher-run $R/l31_${t}__rope__1M__s${u}__N100000"; done; done \
  | xargs -P4 -L1 bash -c 'run "$@"' _
for t in $TASKS; do for s in 41 42 43; do u=$(used $s $t); [ -z "$u" ] && { log "teacher failure $t $s"; continue; }; for q in 4 3 2 1; do
  [ -f $R/synth_teacher_l31_${t}__rope__1M__s${u}__N100000_Q$q.json ] || echo "synth_${t}_t${s}_Q$q stage3/l31.py synth --source teacher --task $t --teacher-run $R/l31_${t}__rope__1M__s${u}__N100000 --Q $q --stage main"
done; done; done | xargs -P4 -L1 bash -c 'run "$@"' _
for t in $TASKS; do for s in 41 42 43; do [ -n "$(used $s $t)" ] && echo "choose_${t}_t$s stage3/l31.py choose --task $t --seed $s"; done; done \
  | xargs -P4 -L1 bash -c 'run "$@"' _
for t in $TASKS; do for s in 41 42 43; do [ -f $R/choice_${t}_t$s.json ] || continue; for r in 0 1; do
  sd=$(( s + 10 + 100 * r )); d=$R/l31_${t}__l1read__1M__s${sd}__N100000__synth_t$s
  [ -f $d/final.json ] && continue; res=""; [ -f $d/log.jsonl ] && res="--resume"
  echo "student_${t}_t${s}_r$r stage3/l31.py train --task $t --seed $s --restart $r $res"
done; done; done | xargs -P4 -L1 bash -c 'run "$@"' _
for t in $TASKS; do for s in 41 42 43; do [ -f $R/choice_${t}_t$s.json ] && echo "select_${t}_t$s stage3/l31.py select --task $t --seed $s"; done; done \
  | xargs -P4 -L1 bash -c 'run "$@"' _
log "driver end (selections written; report after the selection commit)"
