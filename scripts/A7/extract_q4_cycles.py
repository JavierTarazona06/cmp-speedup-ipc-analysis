#!/usr/bin/env python3
import re, csv
from pathlib import Path

RE_CYC = re.compile(r"^system\.cpu(?P<id>\d*)\.numCycles$")
RE_KV  = re.compile(r"^(?P<key>\S+)\s+(?P<val>\d+)")

def parse_stats(path: Path):
    cycles = {}
    for line in path.read_text().splitlines():
        m = RE_KV.match(line.strip())
        if not m: 
            continue
        key, val = m.group("key"), int(m.group("val"))
        mc = RE_CYC.match(key)
        if mc:
            cpu_id = int(mc.group("id")) if mc.group("id") else 0
            cycles[cpu_id] = val
    if not cycles:
        raise RuntimeError(f"No system.cpu*.numCycles found in {path}")
    return cycles

def main(a7_dir="results/A7", size=64, out_csv="results/images/A7/q4_cycles.csv"):
    a7_dir = Path(a7_dir)
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for d in sorted(a7_dir.glob(f"s{size}_t*")):
        t = int(d.name.split("_t")[-1])
        stats = d / "stats.txt"
        if not stats.exists() or stats.stat().st_size == 0:
            continue
        cyc = parse_stats(stats)
        max_cpu = max(cyc, key=cyc.get)
        max_val = cyc[max_cpu]
        all_equal = "YES" if len(set(cyc.values())) == 1 else "NO"
        rows.append((t, max_val, f"cpu{max_cpu:02d}", all_equal))

    rows.sort(key=lambda x: x[0])
    with out_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["threads", "cycles_max", "critical_cpu", "all_equal"])
        w.writerows(rows)

    print("[OK] wrote", out_csv)

if __name__ == "__main__":
    main()
