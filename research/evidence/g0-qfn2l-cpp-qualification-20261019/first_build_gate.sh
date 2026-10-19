#!/usr/bin/env bash
set -u
mkdir -p "$GITHUB_WORKSPACE/build_audit"
cd "$GITHUB_WORKSPACE"
RESULT="$GITHUB_WORKSPACE/build_audit/summary.json"
START=$(date +%s)
QFN='ca83ce1a7b81aa78520c06360aaf4724f7f8c963'
SW='76cfa4ba3a872023a9fa7b9cf9494004d442bedc'
record_status() {
  local code="$1" phase="$2"
  python3 - "$RESULT" "$code" "$phase" "$START" "$QFN" "$SW" <<'PY'
import json,sys,time
p,code,phase,start,qfn,sw=sys.argv[1:]
from pathlib import Path
Path(p).write_text(json.dumps({"status":"BUILD_QUALIFICATION_PASS" if code=="0" else "BUILD_QUALIFICATION_FAIL","phase":phase,"exit_code":int(code),"wall_seconds":int(time.time())-int(start),"qfn2l_sha":qfn,"smt_switch_sha":sw,"scientific_original_tasks_run":0,"neural_training_calls":0,"g0_full":"OPEN","q1_q7":"OPEN"},indent=2)+"\n")
PY
}
set +e
sudo apt-get update -qq >build_audit/apt.log 2>&1
sudo apt-get install -y -qq cmake ninja-build libz3-dev libboost-dev libgmp-dev flex bison >build_audit/packages.log 2>&1
APTRC=$?
if [ "$APTRC" -ne 0 ]; then record_status "$APTRC" apt_install; exit 0; fi
GIT_TERMINAL_PROMPT=0 timeout 75 git clone -q https://github.com/MarekDanco/qfn2l.git qfn2l >build_audit/qfn_clone.log 2>&1
RC=$?
if [ "$RC" -ne 0 ]; then record_status "$RC" qfn_clone; exit 0; fi
(cd qfn2l && git checkout -q "$QFN") >>build_audit/qfn_clone.log 2>&1
RC=$?
if [ "$RC" -ne 0 ]; then record_status "$RC" qfn_checkout; exit 0; fi
GIT_TERMINAL_PROMPT=0 timeout 75 git clone -q https://github.com/stanford-centaur/smt-switch.git smt-switch >build_audit/smt_clone.log 2>&1
RC=$?
if [ "$RC" -ne 0 ]; then record_status "$RC" smt_clone; exit 0; fi
(cd smt-switch && git checkout -q "$SW") >>build_audit/smt_clone.log 2>&1
RC=$?
if [ "$RC" -ne 0 ]; then record_status "$RC" smt_checkout; exit 0; fi
(cd smt-switch && timeout 120 ./configure.sh --z3 --z3-dir=/usr --no-auto-deps > "$GITHUB_WORKSPACE/build_audit/switch_config.log" 2>&1)
RC=$?
if [ "$RC" -ne 0 ]; then record_status "$RC" smt_config; exit 0; fi
timeout 220 cmake --build smt-switch/build -j 2 >build_audit/switch_make.log 2>&1
RC=$?
if [ "$RC" -ne 0 ]; then record_status "$RC" smt_build; exit 0; fi
cmake --install smt-switch/build --prefix "$GITHUB_WORKSPACE/smt-local" >build_audit/switch_install.log 2>&1
RC=$?
if [ "$RC" -ne 0 ]; then record_status "$RC" smt_install; exit 0; fi
cmake -S qfn2l/src/qfn2l_cpp -B qfn2l/src/qfn2l_cpp/build -DBUILD_TESTING=OFF -DBACKEND_Z3=ON -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$GITHUB_WORKSPACE/smt-local" -DSMT_SWITCH_DIR="$GITHUB_WORKSPACE/smt-local/lib" -DSMT_SWITCH_SOURCE_DIR="$GITHUB_WORKSPACE/smt-switch" -DZ3_SOURCE_DIR=/usr >build_audit/qfn_config.log 2>&1
RC=$?
if [ "$RC" -ne 0 ]; then record_status "$RC" qfn_config; exit 0; fi
timeout 170 cmake --build qfn2l/src/qfn2l_cpp/build -j 2 >build_audit/qfn_make.log 2>&1
RC=$?
if [ "$RC" -ne 0 ]; then record_status "$RC" qfn_build; exit 0; fi
qfn2l/src/qfn2l_cpp/build/qfn2l --help >build_audit/qfn_help.log 2>&1
RC=$?
if [ "$RC" -ne 0 ]; then record_status "$RC" qfn_help; exit 0; fi
record_status 0 qfn_help
