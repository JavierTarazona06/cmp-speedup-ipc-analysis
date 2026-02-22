#!/usr/bin/env bash
set -euo pipefail

: "${GEM5:?ERROR: export GEM5=/auto/g/gbusnot/ES201/tools/TP5/gem5-stable}"

SIZE="${SIZE:-64}"
THREADS_LIST="${THREADS_LIST:-"1 2 4 8 16 32 64"}"

OUTROOT="results/A7"
LOGDIR="$OUTROOT/logs"
mkdir -p "$OUTROOT" "$LOGDIR"

echo "[A7+MAKE] SIZE=$SIZE THREADS=($THREADS_LIST)"
echo "[A7+MAKE] GEM5=$GEM5"
echo

for T in $THREADS_LIST; do
  N="$T"
  RAW_DIR="results/${N}_t${T}_s${SIZE}"     # layout real de tu Makefile
  DST_DIR="${OUTROOT}/s${SIZE}_t${T}"
  LOGFILE="${LOGDIR}/s${SIZE}_t${T}.make.log"

  # si ya está en A7 con stats, saltar
  if [[ -s "$DST_DIR/stats.txt" ]]; then
    echo "[SKIP] $DST_DIR already OK"
    continue
  fi

  echo "=== make run: N=$N T=$T SIZE=$SIZE ==="
  # corre y guarda log
  set +e
  make run GEM5="$GEM5" N="$N" T="$T" SIZE="$SIZE" BINARY="$GEM5/../test_omp" 2>&1 | tee "$LOGFILE"
  rc=${PIPESTATUS[0]}
  set -e

  # aunque rc != 0, si hay stats válido, lo aceptamos
  if [[ -s "$RAW_DIR/stats.txt" ]]; then
    echo "[OK] stats present in $RAW_DIR -> moving to $DST_DIR"
    rm -rf "$DST_DIR"
    mv "$RAW_DIR" "$DST_DIR"
  else
    echo "[FAIL] no stats in $RAW_DIR (rc=$rc). See $LOGFILE"
  fi

  echo
done

echo "[A7+MAKE] Done. Check: ls -lh results/A7/s${SIZE}_t*/stats.txt"
