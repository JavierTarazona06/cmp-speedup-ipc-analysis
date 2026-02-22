#!/usr/bin/env bash
set -euo pipefail

: "${GEM5:?ERROR: export GEM5=/auto/g/gbusnot/ES201/tools/TP5/gem5-stable}"

SIZE="${SIZE:-64}"
THREADS_LIST="${THREADS_LIST:-}"          # si vacío -> 1,2,4,...,SIZE (incluye SIZE)
GEM5_BIN="${GEM5_BIN:-$GEM5/build/ARM/gem5.fast}"
SE_PY="${SE_PY:-$GEM5/configs/example/se.py}"
BINARY="${BINARY:-$GEM5/../test_omp}"

OUTROOT="results/A7"
LOGDIR="$OUTROOT/logs"
STATE="$OUTROOT/state.tsv"

mkdir -p "$OUTROOT" "$LOGDIR"

# -------- checks
[[ -x "$GEM5_BIN" ]] || { echo "ERROR: GEM5_BIN not executable: $GEM5_BIN" >&2; exit 2; }
[[ -f "$SE_PY" ]]    || { echo "ERROR: se.py not found: $SE_PY" >&2; exit 2; }
[[ -f "$BINARY" || -x "$BINARY" ]] || { echo "ERROR: test_omp not found: $BINARY" >&2; exit 2; }

# -------- default threads list: 1,2,4,...,SIZE (ensure SIZE included)
if [[ -z "$THREADS_LIST" ]]; then
  t=1
  THREADS_LIST="1"
  while (( t < SIZE )); do
    t=$((t*2))
    if (( t < SIZE )); then THREADS_LIST="$THREADS_LIST $t"; fi
  done
  [[ " $THREADS_LIST " == *" $SIZE "* ]] || THREADS_LIST="$THREADS_LIST $SIZE"
fi

# -------- state.tsv (dedup by size+threads)
if [[ ! -f "$STATE" ]]; then
  echo -e "size\tthreads\tstatus\toutdir\tlogfile" > "$STATE"
fi

update_state() {
  local size="$1" t="$2" status="$3" outdir="$4" logfile="$5"
  awk -v s="$size" -v tt="$t" 'BEGIN{OFS="\t"} NR==1{print;next} !($1==s && $2==tt){print}' "$STATE" > "${STATE}.tmp"
  mv "${STATE}.tmp" "$STATE"
  echo -e "${size}\t${t}\t${status}\t${outdir}\t${logfile}" >> "$STATE"
}

run_one() {
  local T="$1" N="$1" use_caches="$2" outdir="$3" logfile="$4"
  local args=( -d "$outdir" "$SE_PY" --cpu-type=arm_detailed -n "$N" -c "$BINARY" -o "$T $SIZE" )
  if [[ "$use_caches" == "1" ]]; then
    args=( -d "$outdir" "$SE_PY" --cpu-type=arm_detailed --caches -n "$N" -c "$BINARY" -o "$T $SIZE" )
  fi

  set +e
  "$GEM5_BIN" "${args[@]}" 2>&1 | tee "$logfile"
  rc=${PIPESTATUS[0]}
  set -e
  return $rc
}

echo "[A7] SIZE=$SIZE THREADS=($THREADS_LIST)"
echo "[A7] GEM5_BIN=$GEM5_BIN"
echo "[A7] BINARY=$BINARY"
echo

for T in $THREADS_LIST; do
  OUTDIR="$OUTROOT/s${SIZE}_t${T}"
  LOG1="$LOGDIR/s${SIZE}_t${T}.log"
  LOG2="$LOGDIR/s${SIZE}_t${T}.nocache.log"

  # Skip if already has stats
  if [[ -s "$OUTDIR/stats.txt" ]]; then
    echo "[SKIP] $OUTDIR already has stats.txt"
    update_state "$SIZE" "$T" "DONE" "$OUTDIR" "$LOG1"
    continue
  fi

  rm -rf "$OUTDIR"
  mkdir -p "$OUTDIR"
  update_state "$SIZE" "$T" "PENDING" "$OUTDIR" "$LOG1"
  echo "=== RUN A7: T=$T (try caches) ==="

  # Attempt 1: with caches
  if run_one "$T" 1 "$OUTDIR" "$LOG1"; then
    :
  else
    rc=$?
    echo "[WARN] rc=$rc for T=$T with caches"
  fi

  if [[ -s "$OUTDIR/stats.txt" ]]; then
    update_state "$SIZE" "$T" "DONE" "$OUTDIR" "$LOG1"
    echo "[DONE] stats.txt OK (caches)"
    echo
    continue
  fi

  # Attempt 2: retry without caches (often avoids snoop/coherence crashes)
  echo "=== RETRY A7: T=$T (no caches) ==="
  rm -rf "$OUTDIR"
  mkdir -p "$OUTDIR"
  update_state "$SIZE" "$T" "RETRY_NOCACHE" "$OUTDIR" "$LOG2"

  if run_one "$T" 0 "$OUTDIR" "$LOG2"; then
    :
  else
    rc=$?
    echo "[WARN] rc=$rc for T=$T without caches"
  fi

  if [[ -s "$OUTDIR/stats.txt" ]]; then
    update_state "$SIZE" "$T" "DONE_NOCACHE" "$OUTDIR" "$LOG2"
    echo "[DONE] stats.txt OK (no caches)"
  else
    update_state "$SIZE" "$T" "FAILED" "$OUTDIR" "$LOG2"
    echo "[FAILED] no stats.txt for T=$T even after retry"
  fi
  echo
done

echo "[A7] Finished. State: $STATE"
