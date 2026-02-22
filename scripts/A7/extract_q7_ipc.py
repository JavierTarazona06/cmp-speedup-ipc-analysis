#!/usr/bin/env python3
import re, csv
from pathlib import Path

RE_KV = re.compile(r"^(?P<key>\S+)\s+(?P<val>[-+]?\d+(\.\d+)?)")

RE_CYC = re.compile(r"^system\.cpu(?P<id>\d*)\.numCycles$")
RE_INS = re.compile(r"^system\.cpu(?P<id>\d*)\.committedInsts$")

def read_stats(path: Path):
    cycles = {}
    insts = {}
    sim_insts = None
    for line in path.read_text().splitlines():
        m = RE_KV.match(line.strip())
        if not m:
            continue
        key = m.group("key")
        val = float(m.group("val"))
        if key == "sim_insts":
            sim_insts = val
            continue
        mc = RE_CYC.match(key)
        if mc:
            cpu_id = int(mc.group("id")) if mc.group("id") else 0
            cycles[cpu_id] = val
            continue
        mi = RE_INS.match(key)
        if mi:
            cpu_id = int(mi.group("id")) if mi.group("id") else 0
            insts[cpu_id] = val
            continue
    if not cycles:
        raise RuntimeError(f"No numCycles found in {path}")
    if not insts:
        raise RuntimeError(f"No committedInsts found in {path}")
    return cycles, insts, sim_insts

def main(a7_dir="results/A7", size=64, out_csv="results/images/A7/q7_ipc.csv"):
    a7_dir = Path(a7_dir)
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for d in sorted(a7_dir.glob(f"s{size}_t*")):
        t = int(d.name.split("_t")[-1])
        stats = d / "stats.txt"
        if not stats.exists() or stats.stat().st_size == 0:
            continue

        cycles, insts, sim_insts = read_stats(stats)

        # cycles_app = max cycles (chemin critique, cohérent Q4/Q5/Q6)
        cycles_app = max(cycles.values())

        # IPC per core, then take maximum
        ipc_max = None
        cpu_max = None
        for cpu_id, c in cycles.items():
            I = insts.get(cpu_id, None)
            if I is None or c <= 0:
                continue
            ipc = I / c
            if (ipc_max is None) or (ipc > ipc_max):
                ipc_max = ipc
                cpu_max = cpu_id

        if ipc_max is None:
            raise RuntimeError(f"Could not compute IPC for {stats}")

        # Optional: "global" IPC like A15 (sim_insts / cycles_app)
        ipc_global = (sim_insts / cycles_app) if (sim_insts is not None and cycles_app > 0) else float("nan")

        rows.append((t, ipc_max, f"cpu{cpu_max:02d}", ipc_global))

    rows.sort(key=lambda x: x[0])

    with out_csv.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["threads", "ipc_max", "cpu_at_ipc_max", "ipc_global"])
        w.writerows(rows)

    print("[OK] wrote", out_csv)

if __name__ == "__main__":
    main()
