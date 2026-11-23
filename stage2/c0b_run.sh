#!/usr/bin/env bash
# C-0b driver: four trainings (addition / copy x arm O / D, seed 21, --keep-best) in parallel (1 thread each), then the
# diagnostics and the report.  Resumable.   PY=<python> bash stage2/c0b_run.sh
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}
R=stage2/results/c0b
export PY R OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
mkdir -p "$R/logs"
log() { echo "$(date -u '+%Y-%m-%d %H:%M:%S') $*" >> "$R/QUEUE_LOG.txt"; }
log "driver start"
for job in "addition O oracle" "addition D shared" "copy O oracle" "copy D shared"; do
  set -- $job
  d=$R/c0b_${1}__coupled__1M__s21__N100000__$3
  [ -f "$d/final.json" ] && continue
  res=""; [ -f "$d/log.jsonl" ] && res="--resume"
  ( log "launch train $1 $2 $res"; $PY stage2/c0b.py train --task $1 --arm $2 $res >> "$R/logs/train_$1_$2.out" 2>&1; log "exit train $1 $2 code $?" ) &
done
wait
for job in "addition O" "addition D" "copy O" "copy D"; do
  set -- $job
  ( $PY stage2/c0b.py diag --task $1 --arm $2 > "$R/logs/diag_$1_$2.out" 2>&1; log "exit diag $1 $2 code $?" ) &
done
wait
$PY stage2/c0b.py report > "$R/report.json.out" 2>&1; log "exit report code $?"
log "driver end"
