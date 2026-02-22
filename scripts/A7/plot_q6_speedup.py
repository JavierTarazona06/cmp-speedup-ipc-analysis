#!/usr/bin/env python3
import csv
from pathlib import Path
import matplotlib.pyplot as plt

def main(csv_path="results/images/A7/q6_speedup.csv",
         out_png="results/images/A7/q6_speedup_vs_threads.png"):
    csv_path = Path(csv_path)
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)

    T, S = [], []
    with csv_path.open() as f:
        r = csv.DictReader(f)
        for row in r:
            T.append(int(row["threads"]))
            S.append(float(row["speedup"]))

    order = sorted(range(len(T)), key=lambda i: T[i])
    T = [T[i] for i in order]
    S = [S[i] for i in order]

    plt.figure()
    plt.plot(T, S, marker="o")
    plt.xlabel("Threads (T)")
    plt.ylabel("Speedup S(T)=C(1)/C(T)")
    plt.grid(True)
    plt.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close()

    print("[OK] wrote", out_png)

if __name__ == "__main__":
    main()
