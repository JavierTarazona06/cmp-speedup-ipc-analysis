# Límite observado en A15 (gem5)

En la campaña Q9 (A15, `--cpu-type=detailed`, `o3-width=2`, `size=64`) se observó un límite claro de escalado:

- Con `threads <= 32`, las ejecuciones terminan correctamente (`DONE`).
- A partir de `threads = 40`, gem5 termina con `SIGSEGV` (`exit=139`), aun cuando el benchmark ya alcanzó a imprimir `Done`.

Este patrón es consistente con un límite/bug del simulador (gem5-stable 2015) en esta configuración de muchos cores, más que con un error funcional del benchmark.

# Restricción `threads = cpus/cores`

En el flujo actual de Q9, el script acopla directamente ambos parámetros:

- `--num-cpus=${threads}` en gem5.
- Argumento del benchmark `-o "${threads} ${SIZE}"`.

Por lo tanto, cada aumento de `threads` también aumenta el número de CPUs simuladas. La frontera observada no mide solo OpenMP; mide el escalado conjunto `threads + núcleos simulados`.

# Hipótesis de memoria (menos probable)

La memoria simulada por defecto es `512MB`, por lo que podría parecer un candidato inicial. Sin embargo, con base en los resultados observados, esta causa es mucho menos probable:

- El mensaje `Done` lo imprime `test_omp` y solo significa que el cálculo del benchmark terminó.
- Eso no implica que toda la ejecución haya finalizado correctamente: `run_q9_a15.sh` marca `DONE` solo cuando el proceso `gem5` termina con `exit=0`.
- Si `gem5` se cae después de ese `Done` (por ejemplo con `SIGSEGV`, `exit=139`), el estado final registrado es `FAILED`.
- El fallo aparece en el cierre/finalización del proceso gem5 (segfault), no como error temprano de asignación del programa.

Conclusión práctica para Q9: limitar la campaña a un máximo de `32` threads para mantener ejecuciones estables y comparables.
