#!/usr/bin/env bash
# I-0a driver (stage2/i0a.py): the four teachers in parallel (1 thread each), then the 36 compiles 4 at a time, then
# the measurements and the report.  Resumable: a finished teacher (final.json) or compile (compile_result.json) is
# skipped; an unfinished teacher continues with --resume.
#   PY=<python> bash stage2/i0a_run.sh
set -u
cd "$(dirname "$0")/.."
PY=${PY:-python}
R=stage2/results/i0a
LOG=$R/QUEUE_LOG.txt
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 THREADS=1
log() { echo "$(date -u '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }
mkdir -p "$R/logs"
log "driver start"
for t in addition mul1 xor rev_xor; do
  d=$R/i0a_${t}__rope__1M__s20__N100000
  if [ -f "$d/final.json" ]; then continue; fi
  res=""; [ -f "$d/log.jsonl" ] && res="--resume"
  ( log "launch teacher $t $res"; $PY stage2/i0a.py teacher --task $t $res >> "$R/logs/teacher_$t.out" 2>&1; log "exit teacher $t code $?" ) &
done
wait
jobs_file=$(mktemp)
for t in xor rev_xor addition mul1; do
  for s in 1000 2000 3000 4000 6000 8000 12000 16000 20000; do
    c=$R/${t}_compile_s20_step$(printf %05d $s)
    [ -f "$c/compile_result.json" ] || echo "$t $s" >> "$jobs_file"
  done
done
export PY R LOG
xargs -P4 -L1 bash -c 'echo "$(date -u "+%Y-%m-%d %H:%M:%S") launch compile $0 $1" >> $LOG; rm -rf $R/${0}_compile_s20_step$(printf %05d $1); $PY stage2/i0a.py compile --task $0 --step $1 > $R/logs/compile_${0}_$1.out 2>&1; echo "$(date -u "+%Y-%m-%d %H:%M:%S") exit compile $0 $1 code $?" >> $LOG' < "$jobs_file"
rm -f "$jobs_file"
for t in addition mul1 xor rev_xor; do
  $PY stage2/i0a.py measure --task $t > "$R/logs/measure_$t.out" 2>&1; log "exit measure $t code $?"
done
$PY stage2/i0a.py report > "$R/report.md" 2>&1; log "exit report code $?"
log "driver end"
