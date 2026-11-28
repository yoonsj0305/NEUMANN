#!/bin/bash
# L2b-0 baselines (stage3/DESIGN.md 11.10-2): multi_add, mulNM x abacus/rope/looped_rr/gru/rel_rand/nope (seed 0, 1M,
# stage-1 protocol), then LR x0.5 / x2 for rel_rand / nope by the 3-B rule (8.5-3).  P workers at nice 10 (P0 first).
# Idempotent (final.json -> skip, log.jsonl -> resume).  Usage: bash stage3/l2b_base_run.sh PY P
PY=$1; P=${2:-1}; R=stage3/results/L2b-0/baselines; mkdir -p $R/logs
log() { echo "$(date -u '+%F %T') $*" >> $R/QUEUE_LOG.txt; }
run() {  # task kind mult
  t=$1; k=$2; m=$3
  case $k in rel_rand|nope) tag=""; [ "$m" != "1.0" ] && tag="__lrx${m%.0}"; d=$R/3b_${t}__${k}__1M__s0__N100000$tag;;
             *) d=$R/l2b0_${t}__${k}__1M__s0__N100000;; esac
  [ -f $d/final.json ] && return 0
  res=""; [ -f $d/log.jsonl ] && res="--resume"
  OMP_NUM_THREADS=1 nice -n 10 $PY stage3/l2b_base.py run --task $t --kind $k --lr-mult $m $res >> $R/logs/${t}__${k}__lr$m.out 2>&1
  log "exit $t $k lr$m code $?"
}
export -f run log; export PY R
log "driver start (baselines, P=$P)"
for k in rope abacus rel_rand nope looped_rr gru; do for t in mulNM multi_add; do echo "$t $k 1.0"; done; done \
  | xargs -P$P -L1 bash -c 'run "$@"' _
log "default LR done"
for t in mulNM multi_add; do for k in rel_rand nope; do
  f=$R/3b_${t}__${k}__1M__s0__N100000/final.json
  $PY -c "import json,sys; j=json.load(open('$f'))['judgment']['acc']; l=list(j); sys.exit(0 if (j[l[0]]<0.95 or j[l[2]]>=0.10) else 1)" \
    && { echo "$t $k 0.5"; echo "$t $k 2.0"; }
done; done | xargs -P$P -L1 bash -c 'run "$@"' _
log "driver end (baselines)"
