"""CLI wrapper for the first accelerator Architecture Multiplier run."""
from __future__ import annotations

import argparse
import json

from experiments.architecture_multiplier_am1 import execute
from experiments.general_hf_core_cuda_am1 import FrozenHFCudaCore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--frozen-head", required=True)
    args = parser.parse_args()
    report = execute(args.directory, args.frozen_head, FrozenHFCudaCore)
    print(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False))
    raise SystemExit(0 if report["status"] == "COMPLETE" else 2)


if __name__ == "__main__":
    main()
