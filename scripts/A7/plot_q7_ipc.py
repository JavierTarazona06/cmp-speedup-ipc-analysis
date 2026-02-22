#!/usr/bin/env python3
import csv
from pathlib import Path
import matplotlib.pyplot as plt

def main(csv_path="results/images/A7/q7_ipc.csv",
         out_png="results/images/A7/q7_ipcmax_vs_threads.png"):
    csv_path = Path(csv_path)
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)

    T, Imax = [], []
    with csv_path.open() as f:
        r = csv.DictReader(f)
        for row in r:
            T.append(int(row["threads"]))
            Imax.append(float(row["ipc_max"]))

    order = sorted(range(len(T)), key=lambda i: T[i])
    T = [T[i] for i in order]
    Imax = [Imax[i] for i in order]

    plt.figure()
    plt.plot(T, Imax, marker="o")
    plt.xlabel("Threads (T)")
    plt.ylabel("IPC_max = max_i(committedInsts_i / numCycles_i)")
    plt.grid(True)
    plt.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close()

    print("[OK] wrote", out_png)

if __name__ == "__main__":
    main()
