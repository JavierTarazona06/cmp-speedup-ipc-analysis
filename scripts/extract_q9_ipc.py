#!/usr/bin/env python3

import argparse
import csv
import re
import sys
from pathlib import Path


SIM_INSTS_RE = re.compile(r"^sim_insts\s+(\d+)\b")
CYCLES_MULTI_RE = re.compile(r"^system\.cpu\d+\.numCycles\s+(\d+)\b")
CYCLES_SINGLE_RE = re.compile(r"^system\.cpu\.numCycles\s+(\d+)\b")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract Q9 IPC values from gem5 runs and export CSV files."
    )
    parser.add_argument(
        "--results-root",
        default="results/A15",
        help="Root directory for A15 runs (default: results/A15).",
    )
    parser.add_argument(
        "--images-dir",
        default="results/images/A15",
        help="Directory where IPC CSV files are written (default: results/images/A15).",
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
        rows.extend(reader)
    return rows


def extract_insts_and_cycles(stats_path):
    sim_insts = None
    max_cycles = None
    single_cycles = None

    with stats_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if sim_insts is None:
                sim_match = SIM_INSTS_RE.match(line)
                if sim_match:
                    sim_insts = int(sim_match.group(1))

            multi_match = CYCLES_MULTI_RE.match(line)
            if multi_match:
                value = int(multi_match.group(1))
                if max_cycles is None or value > max_cycles:
                    max_cycles = value
                continue

            single_match = CYCLES_SINGLE_RE.match(line)
            if single_match:
                single_cycles = int(single_match.group(1))

    cycles = max_cycles if max_cycles is not None else single_cycles
    return sim_insts, cycles


def collect_done_ipc_rows(state_rows, size_filter):
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

        if row["status"] != "DONE":
            missing.append((row, f"status={row['status']}"))
            continue

        outdir = Path(row["outdir"])
        stats_path = outdir / "stats.txt"
        if not stats_path.is_file():
            missing.append((row, "missing stats.txt"))
            continue

        sim_insts, cycles = extract_insts_and_cycles(stats_path)
        if sim_insts is None:
            missing.append((row, "sim_insts not found in stats.txt"))
            continue
        if cycles is None:
            missing.append((row, "numCycles not found in stats.txt"))
            continue
        if cycles == 0:
            missing.append((row, "numCycles is zero"))
            continue

        valid.append(
            {
                "size": size,
                "width": width,
                "threads": threads,
                "sim_insts": sim_insts,
                "cycles": cycles,
                "ipc": sim_insts / cycles,
                "outdir": str(outdir),
            }
        )

    return valid, missing


def write_ipc_csv(rows, ipc_csv_path):
    rows_sorted = sorted(rows, key=lambda x: (x["size"], x["width"], x["threads"]))
    with ipc_csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["size", "width", "threads", "sim_insts", "cycles", "ipc", "outdir"],
        )
        writer.writeheader()
        writer.writerows(rows_sorted)


def write_ipc_max_csv(rows, ipc_max_csv_path):
    rows_sorted = sorted(rows, key=lambda x: (x["size"], x["width"], x["threads"]))
    max_rows = []

    for width in sorted({row["width"] for row in rows_sorted}):
        width_rows = [row for row in rows_sorted if row["width"] == width]
        best = max(width_rows, key=lambda row: row["ipc"])
        max_rows.append(
            {
                "scope": "width_max",
                "size": best["size"],
                "width": best["width"],
                "threads": best["threads"],
                "sim_insts": best["sim_insts"],
                "cycles": best["cycles"],
                "ipc": best["ipc"],
                "outdir": best["outdir"],
            }
        )

    global_best = max(rows_sorted, key=lambda row: row["ipc"])
    max_rows.append(
        {
            "scope": "global_max",
            "size": global_best["size"],
            "width": global_best["width"],
            "threads": global_best["threads"],
            "sim_insts": global_best["sim_insts"],
            "cycles": global_best["cycles"],
            "ipc": global_best["ipc"],
            "outdir": global_best["outdir"],
        }
    )

    with ipc_max_csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scope",
                "size",
                "width",
                "threads",
                "sim_insts",
                "cycles",
                "ipc",
                "outdir",
            ],
        )
        writer.writeheader()
        writer.writerows(max_rows)


def main():
    args = parse_args()

    state_file = Path(args.state_file) if args.state_file else Path(args.results_root) / "state.tsv"
    if not state_file.is_file():
        print(f"Error: state file not found: {state_file}", file=sys.stderr)
        return 1

    state_rows = read_state_rows(state_file)
    ipc_rows, missing_rows = collect_done_ipc_rows(state_rows, args.size)

    if not ipc_rows:
        print("Error: no valid DONE runs were found for IPC extraction.", file=sys.stderr)
        if missing_rows:
            print("Missing or invalid runs:", file=sys.stderr)
            for row, reason in missing_rows:
                print(
                    f"  size={row.get('size')} width={row.get('width')} threads={row.get('threads')} -> {reason}",
                    file=sys.stderr,
                )
        return 1

    sizes = sorted({row["size"] for row in ipc_rows})
    if args.size is None and len(sizes) > 1:
        print(
            "Error: multiple sizes found in DONE runs. Use --size to select one.",
            file=sys.stderr,
        )
        print(f"Available sizes: {sizes}", file=sys.stderr)
        return 1

    selected_size = args.size if args.size is not None else sizes[0]
    ipc_rows = [row for row in ipc_rows if row["size"] == selected_size]

    images_dir = Path(args.images_dir)
    images_dir.mkdir(parents=True, exist_ok=True)
    ipc_csv_path = images_dir / "q9_ipc.csv"
    ipc_max_csv_path = images_dir / "q9_ipc_max.csv"

    write_ipc_csv(ipc_rows, ipc_csv_path)
    write_ipc_max_csv(ipc_rows, ipc_max_csv_path)

    print(f"Wrote IPC CSV: {ipc_csv_path}")
    print(f"Wrote IPC max CSV: {ipc_max_csv_path}")

    if missing_rows:
        print("Runs not included in IPC CSV:")
        for row, reason in missing_rows:
            if int(row.get("size", -1)) == selected_size:
                print(
                    f"  size={row.get('size')} width={row.get('width')} threads={row.get('threads')} -> {reason}"
                )

    return 0


if __name__ == "__main__":
    sys.exit(main())

