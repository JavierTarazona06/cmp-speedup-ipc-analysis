#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/run_q9_a15.sh [options]

Options:
  --gem5 <path>          Path to gem5-stable (default: /home/g/gbusnot/ES201/tools/TP5/gem5-stable)
  --binary <path>        Path to benchmark binary (default: ./test_omp)
  --size <int>           Matrix size (default: 64)
  --widths "<list>"      O3 widths list, space/comma separated (default: "2 4 8")
  --threads "<list>"     Thread list, space/comma separated (default: powers of 2 up to SIZE)
  --results-root <path>  Output root directory (default: results/A15)
  --no-caches            Disable --caches --l2cache
  -h, --help             Show help
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

GEM5="/home/g/gbusnot/ES201/tools/TP5/gem5-stable"
BINARY="./test_omp"
SIZE=64
WIDTHS="2 4 8"
THREADS=""
RESULTS_ROOT="results/A15"
USE_CACHES=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --gem5)
      GEM5="${2:-}"
      shift 2
      ;;
    --binary)
      BINARY="${2:-}"
      shift 2
      ;;
    --size)
      SIZE="${2:-}"
      shift 2
      ;;
    --widths)
      WIDTHS="${2:-}"
      shift 2
      ;;
    --threads)
      THREADS="${2:-}"
      shift 2
      ;;
    --results-root)
      RESULTS_ROOT="${2:-}"
      shift 2
      ;;
    --no-caches)
      USE_CACHES=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

is_positive_int() {
  [[ "$1" =~ ^[0-9]+$ ]] && (( "$1" > 0 ))
}

if ! is_positive_int "${SIZE}"; then
  echo "Error: --size must be a positive integer (got: ${SIZE})" >&2
  exit 1
fi

read_list() {
  local raw="$1"
  raw="${raw//,/ }"
  read -r -a parsed <<< "${raw}"
  printf '%s\n' "${parsed[@]}"
}

mapfile -t WIDTHS_LIST < <(read_list "${WIDTHS}")
if [[ "${#WIDTHS_LIST[@]}" -eq 0 ]]; then
  echo "Error: --widths is empty." >&2
  exit 1
fi

for width in "${WIDTHS_LIST[@]}"; do
  if ! is_positive_int "${width}"; then
    echo "Error: invalid width value: ${width}" >&2
    exit 1
  fi
done

THREADS_LIST=()
if [[ -n "${THREADS}" ]]; then
  mapfile -t THREADS_LIST < <(read_list "${THREADS}")
  if [[ "${#THREADS_LIST[@]}" -eq 0 ]]; then
    echo "Error: --threads is empty." >&2
    exit 1
  fi
else
  t=1
  while (( t <= SIZE )); do
    THREADS_LIST+=("${t}")
    t=$((t * 2))
  done
fi

for threads in "${THREADS_LIST[@]}"; do
  if ! is_positive_int "${threads}"; then
    echo "Error: invalid thread value: ${threads}" >&2
    exit 1
  fi
  if (( threads > SIZE )); then
    echo "Error: thread value ${threads} exceeds size ${SIZE}." >&2
    exit 1
  fi
done

GEM5_BIN="${GEM5}/build/ARM/gem5.fast"
SE_SCRIPT="${SCRIPT_DIR}/se_a15.py"

if [[ ! -x "${GEM5_BIN}" ]]; then
  echo "Error: gem5 binary not found or not executable: ${GEM5_BIN}" >&2
  exit 1
fi

if [[ ! -f "${SE_SCRIPT}" ]]; then
  echo "Error: missing script: ${SE_SCRIPT}" >&2
  exit 1
fi

if [[ ! -f "${BINARY}" ]]; then
  echo "Error: binary not found: ${BINARY}" >&2
  exit 1
fi

export GEM5

mkdir -p "${RESULTS_ROOT}"
LOGS_DIR="${RESULTS_ROOT}/logs"
mkdir -p "${LOGS_DIR}"

STATE_FILE="${RESULTS_ROOT}/state.tsv"

get_existing_status() {
  local size="$1"
  local width="$2"
  local threads="$3"
  local state_path="$4"
  awk -F'\t' -v s="${size}" -v w="${width}" -v t="${threads}" '
    NR == 1 { next }
    $1 == s && $2 == w && $3 == t { print $4; exit }
  ' "${state_path}"
}

initialize_state_file() {
  local tmp_state old_state status outdir log_path
  tmp_state="$(mktemp)"
  old_state=""

  if [[ -f "${STATE_FILE}" ]]; then
    old_state="$(mktemp)"
    cp "${STATE_FILE}" "${old_state}"
  fi

  printf "size\twidth\tthreads\tstatus\toutdir\tlog\n" > "${tmp_state}"

  for width in "${WIDTHS_LIST[@]}"; do
    for threads in "${THREADS_LIST[@]}"; do
      outdir="${RESULTS_ROOT}/s${SIZE}_w${width}_t${threads}"
      log_path="${LOGS_DIR}/s${SIZE}_w${width}_t${threads}.log"
      status="PENDING"

      if [[ -n "${old_state}" ]]; then
        existing_status="$(get_existing_status "${SIZE}" "${width}" "${threads}" "${old_state}")"
        if [[ -n "${existing_status}" ]]; then
          status="${existing_status}"
        fi
      fi

      printf "%s\t%s\t%s\t%s\t%s\t%s\n" \
        "${SIZE}" "${width}" "${threads}" "${status}" "${outdir}" "${log_path}" >> "${tmp_state}"
    done
  done

  mv "${tmp_state}" "${STATE_FILE}"
  if [[ -n "${old_state}" ]]; then
    rm -f "${old_state}"
  fi
}

update_state_status() {
  local size="$1"
  local width="$2"
  local threads="$3"
  local status="$4"
  local outdir="$5"
  local log_path="$6"
  local tmp_file

  tmp_file="$(mktemp)"
  awk -F'\t' -v OFS='\t' \
      -v s="${size}" -v w="${width}" -v t="${threads}" \
      -v new_status="${status}" -v new_outdir="${outdir}" -v new_log="${log_path}" '
    NR == 1 { print; next }
    {
      if ($1 == s && $2 == w && $3 == t) {
        $4 = new_status
        $5 = new_outdir
        $6 = new_log
      }
      print
    }
  ' "${STATE_FILE}" > "${tmp_file}"

  mv "${tmp_file}" "${STATE_FILE}"
}

get_state_status() {
  local size="$1"
  local width="$2"
  local threads="$3"
  awk -F'\t' -v s="${size}" -v w="${width}" -v t="${threads}" '
    NR == 1 { next }
    $1 == s && $2 == w && $3 == t { print $4; exit }
  ' "${STATE_FILE}"
}

initialize_state_file

echo "Q9 A15 batch start"
echo "- GEM5: ${GEM5}"
echo "- BINARY: ${BINARY}"
echo "- SIZE: ${SIZE}"
echo "- WIDTHS: ${WIDTHS_LIST[*]}"
echo "- THREADS: ${THREADS_LIST[*]}"
echo "- RESULTS_ROOT: ${RESULTS_ROOT}"
if (( USE_CACHES )); then
  echo "- CACHES: enabled (--caches --l2cache)"
else
  echo "- CACHES: disabled"
fi

for width in "${WIDTHS_LIST[@]}"; do
  for threads in "${THREADS_LIST[@]}"; do
    status="$(get_state_status "${SIZE}" "${width}" "${threads}")"
    outdir="${RESULTS_ROOT}/s${SIZE}_w${width}_t${threads}"
    log_path="${LOGS_DIR}/s${SIZE}_w${width}_t${threads}.log"

    if [[ "${status}" == "DONE" ]]; then
      echo "SKIP DONE: size=${SIZE} width=${width} threads=${threads}"
      continue
    fi

    mkdir -p "${outdir}"
    cmd=(
      "${GEM5_BIN}"
      "--outdir=${outdir}"
      "${SE_SCRIPT}"
      "--cpu-type=detailed"
      "--o3-width=${width}"
      "--num-cpus=${threads}"
      "-c" "${BINARY}"
      "-o" "${threads} ${SIZE}"
    )

    if (( USE_CACHES )); then
      cmd+=("--caches" "--l2cache")
    fi

    echo "RUN: size=${SIZE} width=${width} threads=${threads}"
    echo "LOG: ${log_path}"

    set +e
    "${cmd[@]}" 2>&1 | tee "${log_path}"
    cmd_status=${PIPESTATUS[0]}
    set -e

    if (( cmd_status != 0 )); then
      update_state_status "${SIZE}" "${width}" "${threads}" "FAILED" "${outdir}" "${log_path}"
      echo "FAILED at size=${SIZE} width=${width} threads=${threads} (exit=${cmd_status})" >&2
      echo "See full log: ${log_path}" >&2
      exit "${cmd_status}"
    fi

    update_state_status "${SIZE}" "${width}" "${threads}" "DONE" "${outdir}" "${log_path}"
    echo "DONE: size=${SIZE} width=${width} threads=${threads}"
  done
done

echo "Q9 A15 batch completed successfully."
echo "State file: ${STATE_FILE}"
