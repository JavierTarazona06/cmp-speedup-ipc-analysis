#!/usr/bin/env python3

import argparse
import csv
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


CYCLES_MULTI_RE = re.compile(r"^system\.cpu\d+\.numCycles\s+(\d+)\b")
CYCLES_SINGLE_RE = re.compile(r"^system\.cpu\.numCycles\s+(\d+)\b")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract Q9 cycles from gem5 runs and generate a 3D plot."
    )
    parser.add_argument(
        "--results-root",
        default="results/A15",
        help="Root directory for A15 runs (default: results/A15).",
    )
    parser.add_argument(
        "--images-dir",
        default="results/images",
        help="Directory where CSV and images are written (default: results/images).",
    )
    parser.add_argument(
        "--state-file",
        default=None,
        help="Path to state.tsv (default: <results-root>/state.tsv).",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=None,
        help="Optional size filter. Required if state has multiple sizes.",
    )
    return parser.parse_args()


def read_state_rows(state_file):
    rows = []
    with state_file.open("r", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"size", "width", "threads", "status", "outdir", "log"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError(
                "state.tsv is missing required columns: size,width,threads,status,outdir,log"
            )
        for row in reader:
            rows.append(row)
    return rows


def extract_cycles(stats_path):
    max_cycles = None
    single_cycles = None
    with stats_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            multi_match = CYCLES_MULTI_RE.match(line)
            if multi_match:
                value = int(multi_match.group(1))
                if max_cycles is None or value > max_cycles:
                    max_cycles = value
                continue

            single_match = CYCLES_SINGLE_RE.match(line)
            if single_match:
                single_cycles = int(single_match.group(1))

    # Keep prior behavior for multicore runs (max across cpu0..cpuN).
    # Fall back to system.cpu.numCycles for single-core runs.
    return max_cycles if max_cycles is not None else single_cycles


def collect_done_runs(state_rows, size_filter):
    valid = []
    missing = []

    for row in state_rows:
        try:
            size = int(row["size"])
            width = int(row["width"])
            threads = int(row["threads"])
        except ValueError:
            missing.append((row, "invalid numeric fields in state.tsv"))
            continue

        if size_filter is not None and size != size_filter:
            continue

        status = row["status"]
        outdir = Path(row["outdir"])
        stats_path = outdir / "stats.txt"

        if status != "DONE":
            missing.append((row, f"status={status}"))
            continue

        if not stats_path.is_file():
            missing.append((row, "missing stats.txt"))
            continue

        cycles = extract_cycles(stats_path)
        if cycles is None:
            missing.append((row, "numCycles not found in stats.txt"))
            continue

        valid.append(
            {
                "size": size,
                "width": width,
                "threads": threads,
                "cycles": cycles,
                "outdir": str(outdir),
            }
        )

    return valid, missing


def write_csv(rows, csv_path):
    rows_sorted = sorted(rows, key=lambda x: (x["size"], x["width"], x["threads"]))
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["size", "width", "threads", "cycles", "outdir"]
        )
        writer.writeheader()
        writer.writerows(rows_sorted)


def write_speedup_csv(rows, speedup_csv_path):
    rows_sorted = sorted(rows, key=lambda x: (x["size"], x["width"], x["threads"]))
    baseline_cycles_by_width = {
        row["width"]: row["cycles"] for row in rows_sorted if row["threads"] == 1
    }

    rows_with_speedup = []
    missing_baseline_widths = set()
    for row in rows_sorted:
        baseline_cycles = baseline_cycles_by_width.get(row["width"])
        if baseline_cycles is None:
            missing_baseline_widths.add(row["width"])
            continue

        rows_with_speedup.append(
            {
                "size": row["size"],
                "width": row["width"],
                "threads": row["threads"],
                "cycles": row["cycles"],
                "cycles_t1": baseline_cycles,
                "speedup": baseline_cycles / row["cycles"],
                "outdir": row["outdir"],
            }
        )

    with speedup_csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "size",
                "width",
                "threads",
                "cycles",
                "cycles_t1",
                "speedup",
                "outdir",
            ],
        )
        writer.writeheader()
        writer.writerows(rows_with_speedup)

    return sorted(missing_baseline_widths)


def build_grid(rows):
    widths = sorted({row["width"] for row in rows})
    threads = sorted({row["threads"] for row in rows})
    width_index = {value: idx for idx, value in enumerate(widths)}
    thread_index = {value: idx for idx, value in enumerate(threads)}

    z_values = np.full((len(widths), len(threads)), np.nan, dtype=float)
    for row in rows:
        i = width_index[row["width"]]
        j = thread_index[row["threads"]]
        z_values[i, j] = float(row["cycles"])

    return widths, threads, z_values


def plot_3d(rows, image_path, size_filter):
    widths, threads, z_values = build_grid(rows)

    figure = plt.figure(figsize=(10, 7))
    axis = figure.add_subplot(111, projection="3d")

    x_axis, y_axis = np.meshgrid(np.array(threads, dtype=float), np.array(widths, dtype=float))
    has_missing_points = np.isnan(z_values).any()

    if has_missing_points:
        xs = np.array([row["threads"] for row in rows], dtype=float)
        ys = np.array([row["width"] for row in rows], dtype=float)
        zs = np.array([row["cycles"] for row in rows], dtype=float)
        scatter = axis.scatter(xs, ys, zs, c=zs, cmap="viridis", s=60)
        figure.colorbar(scatter, ax=axis, shrink=0.6, pad=0.1, label="Cycles")
    else:
        surface = axis.plot_surface(
            x_axis,
            y_axis,
            z_values,
            cmap="viridis",
            edgecolor="k",
            linewidth=0.3,
            alpha=0.95,
        )
        figure.colorbar(surface, ax=axis, shrink=0.6, pad=0.1, label="Cycles")

    axis.set_xlabel("Threads")
    axis.set_ylabel("Voies (o3-width)")
    axis.set_zlabel("Cycles d'execution")

    title_size = f"size={size_filter}" if size_filter is not None else "size=auto"
    axis.set_title(f"Q9 A15 - Cycles ({title_size})")

    figure.tight_layout()
    figure.savefig(image_path, dpi=220)
    plt.close(figure)


def main():
    args = parse_args()

    state_file = Path(args.state_file) if args.state_file else Path(args.results_root) / "state.tsv"
    if not state_file.is_file():
        print(f"Error: state file not found: {state_file}", file=sys.stderr)
        return 1

    state_rows = read_state_rows(state_file)
    done_rows, missing_rows = collect_done_runs(state_rows, args.size)

    if not done_rows:
        print("Error: no valid DONE runs were found for plotting.", file=sys.stderr)
        if missing_rows:
            print("Missing or invalid runs:", file=sys.stderr)
            for row, reason in missing_rows:
                print(
                    f"  size={row.get('size')} width={row.get('width')} threads={row.get('threads')} -> {reason}",
                    file=sys.stderr,
                )
        return 1

    sizes = sorted({row["size"] for row in done_rows})
    if args.size is None and len(sizes) > 1:
        print(
            "Error: multiple sizes found in DONE runs. Use --size to select one.",
            file=sys.stderr,
        )
        print(f"Available sizes: {sizes}", file=sys.stderr)
        return 1

    selected_size = args.size if args.size is not None else sizes[0]
    done_rows = [row for row in done_rows if row["size"] == selected_size]

    images_dir = Path(args.images_dir)
    images_dir.mkdir(parents=True, exist_ok=True)

    csv_path = images_dir / "q9_cycles.csv"
    speedup_csv_path = images_dir / "q9_speedup.csv"
    image_path = images_dir / "q9_cycles_3d.png"

    write_csv(done_rows, csv_path)
    missing_baseline_widths = write_speedup_csv(done_rows, speedup_csv_path)
    plot_3d(done_rows, image_path, selected_size)

    print(f"Wrote CSV: {csv_path}")
    print(f"Wrote speedup CSV: {speedup_csv_path}")
    print(f"Wrote image: {image_path}")

    if missing_baseline_widths:
        print(
            f"Warning: missing threads=1 baseline for widths: {missing_baseline_widths}. "
            "Those widths were skipped in q9_speedup.csv."
        )

    if missing_rows:
        print("Runs not included in CSV/plot:")
        for row, reason in missing_rows:
            if int(row.get("size", -1)) == selected_size:
                print(
                    f"  size={row.get('size')} width={row.get('width')} threads={row.get('threads')} -> {reason}"
                )

    return 0


if __name__ == "__main__":
    sys.exit(main())
