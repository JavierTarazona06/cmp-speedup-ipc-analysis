# ES201 — TD/TP5: CMP Performance Analysis with gem5

This repository contains the TD/TP5 (ES201 — Microprocessor Architecture) assignment: evaluation of a **CMP (multicore)** architecture using **gem5**, running a parallel **OpenMP** matrix multiplication (`test_omp`).

## Objectives (summary)

- Analyze cache coherence and the impact of the memory hierarchy (Q1).
- Identify default CPU/cache parameters in gem5 (Q2–Q3).
- Measure performance while varying:
  - **#threads** (1,2,4,8,...) with an in-order CPU such as Cortex-A7 (`arm_detailed`) (Q4–Q8).
  - **#threads** and **“width”** (2/4/8) with an out-of-order CPU such as Cortex-A15 (`o3` / `detailed`) (Q9–Q12).
- Propose a “more efficient” configuration (area efficiency) (Q13).
- *(Optional)* Explain super-linear speedup (Q14).

## Requirements

- Environment with **gem5** configured (course setup).
- `test_omp` binary.
- Linux + bash (recommended).
