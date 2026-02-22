#!/usr/bin/env python3
import csv
from pathlib import Path
import matplotlib.pyplot as plt

def main(csv_path="results/images/A7/q5_cycles.csv",
         out_png="results/images/A7/q5_cycles_vs_threads.png"):
    csv_path = Path(csv_path)
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)

    T, C = [], []
    with csv_path.open() as f:
        r = csv.DictReader(f)
        for row in r:
            T.append(int(row["threads"]))
            C.append(float(row["cycles"]))

    # sort by threads
    order = sorted(range(len(T)), key=lambda i: T[i])
    T = [T[i] for i in order]
    C = [C[i] for i in order]

    plt.figure()
    plt.plot(T, C, marker="o")
    plt.xlabel("Threads (T)")
    plt.ylabel("Cycles (C(T) = max cpu.numCycles)")
    plt.grid(True)
    plt.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close()

    print("[OK] wrote", out_png)

if __name__ == "__main__":
    main()
