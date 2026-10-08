"""Observe the existing macOS MLX server without modifying or killing it."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def gib(value: str) -> float:
    number, unit = re.fullmatch(r"\s*([\d.]+)\s*([KMGT]?)\s*", value).groups()
    return float(number) * {"": 1 / 1024**3, "K": 1 / 1024**2, "M": 1 / 1024, "G": 1, "T": 1024}[unit]


def footprint(pid: int) -> tuple[float, float]:
    result = subprocess.run(["vmmap", "-summary", str(pid)], capture_output=True,
                            text=True, timeout=15, check=True)
    current = re.search(r"^Physical footprint:\s*([\d.]+\s*[KMGT]?)", result.stdout, re.M)
    peak = re.search(r"^Physical footprint \(peak\):\s*([\d.]+\s*[KMGT]?)", result.stdout, re.M)
    if not current or not peak:
        raise ValueError("vmmap did not report physical footprint")
    return gib(current.group(1)), gib(peak.group(1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--threshold-gib", type=float, default=7.0)
    args = ap.parse_args()
    flag = args.output.with_name("mlx_memory_pressure.flag")
    flag.unlink(missing_ok=True)
    while True:
        try:
            current, peak = footprint(args.pid)
            record = {"time_utc": datetime.now(timezone.utc).isoformat(),
                      "pid": args.pid, "physical_footprint_gib": current,
                      "peak_gib": peak, "threshold_gib": args.threshold_gib}
            args.output.write_text(json.dumps(record, indent=2) + "\n")
            if current >= args.threshold_gib:
                flag.write_text(json.dumps(record, indent=2) + "\n")
        except Exception as exc:
            args.output.write_text(json.dumps({"error": str(exc)}, indent=2) + "\n")
        time.sleep(5)


if __name__ == "__main__":
    main()
