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

## Travail en groupe

Personne A: Q1–Q3 Maeva
Personne B: Q4–Q8: Carlos
Personne C: Q9–Q12: Javier
Personne D: Q13–Q14: Jair

## Commandes pour exécuter GEM5 sur les ordinateurs de l'ENSTA

1/ cp -v test_omp /your/directory
2/ export GEM5=/home/c/cathebras//ES201/tools/TP5/gem5-stable
3/ $GEM5/build/ARM/gem5.fast $GEM5/configs/example/se.py ....

~/cmp-speedup-ipc-analysis/results

Paso 1: pones el programa a simular (test_omp) en un lugar accesible.

Paso 2: le dices a la terminal “dónde está gem5”.

Paso 3: arrancas gem5 y le dices “simula una máquina ARM con N cores y ejecuta test_omp con estos parámetros”.

## Info de test_omp

test_omp es el programa (benchmark) que vas a simular en gem5 para responder el taller. En la consigna se especifica que el TP usa una aplicación de multiplicación de matrices A·B, paralelizada para ejecutarse con m threads usando OpenMP, y que el código fuente es test_omp.cpp (compilado al ejecutable test_omp). 

Se ejecuta así: ./test_omp <nthreads> <size> 

<nthreads> = número de hilos (threads).

<size> = tamaño n de la matriz cuadrada n×n (recomiendan n < 256 para que la simulación no sea eterna). 

Internamente, el programa:

Reserva memoria para A, B y C.

Inicializa A y B.

Calcula C = A*B y paraleliza el bucle externo con #pragma omp parallel for.
