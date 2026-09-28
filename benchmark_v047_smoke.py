from __future__ import annotations

import json

from benchmark_v047 import run


if __name__ == "__main__":
    print(json.dumps(run(count=2, seed_base=3_400_000), indent=2, sort_keys=True))
