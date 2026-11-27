Driver bug (stage3/p0_run4.sh before the fix): the skip check looked for "__lrx2.0" while the run directory is "__lrx2",
so after each container restart the finished x2 run was started again from scratch and overwrote config/env/log/final.
The run directory holds the FIRST run again (restored from commit 9357dd5, 2026-11-26).
rerun1_* = rerun after the 02:47 restart (as committed in d478279); rerun2_* = rerun after the 04:09 restart (98502ee).
A third start after the 23:30 restart was killed after ~1.5 min (exit 143) before any evaluation.
Accuracies (judgment and last) are identical in all three complete runs; only wall_train_s/wall_eval_s differ.
