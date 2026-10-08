"""Read-only public QVBS metadata retrieval; no model execution or selection by cost."""
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
PIN = "c7324a311475ba1a3f40e36a324e32f91e766540"
FAMILIES = ["bluetooth", "brp", "coupon", "crowds", "egl", "haddad-monmege", "herman", "leader_sync", "nand", "oscillators"]


def main():
    # Public exact-probability reference values can exceed Python's default cap.
    # Keep a finite cap and the existing two-megabyte response bound.
    sys.set_int_max_str_digits(100_000)
    dest = ROOT / "public-source-metadata"
    dest.mkdir(exist_ok=True)
    rows = []
    for family in FAMILIES:
        rel = f"benchmarks/dtmc/{family}/index.json"
        url = f"https://raw.githubusercontent.com/ahartmanns/qcomp/{PIN}/{rel}"
        target = dest / f"{family}.json"
        if target.exists():
            data = target.read_bytes()
        else:
            with urlopen(Request(url, headers={"User-Agent": "NEUMANN-local-evidence-audit"}), timeout=20) as response:
                data = response.read(2_000_000)
            with target.open("xb") as out:
                out.write(data)
        parsed = json.loads(data)
        rows.append({"family": family, "commit": PIN, "source": rel, "url": url,
                     "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "metadata": parsed})
        print(json.dumps({"family": family, "keys": list(parsed), "bytes": len(data)}, ensure_ascii=False), flush=True)
    with (ROOT / "public-catalog-first.json").open("x", encoding="utf-8") as out:
        json.dump({"scope": "Source-only opened-development review; no performance measurement", "rows": rows}, out, indent=2)


if __name__ == "__main__":
    main()
