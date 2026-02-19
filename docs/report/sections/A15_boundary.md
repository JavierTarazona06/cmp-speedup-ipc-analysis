# Límite observado en A15 (gem5)

En la campaña Q9 (A15, `--cpu-type=detailed`, `o3-width=2`, `size=64`) se observó un límite claro de escalado:

- Con `threads <= 32`, las ejecuciones terminan correctamente (`DONE`).
- A partir de `threads = 40`, gem5 termina con `SIGSEGV` (`exit=139`), aun cuando el benchmark ya alcanzó a imprimir `Done`.

Este patrón sugiere un bug del simulador (gem5-stable 2015), más que un error funcional del benchmark.

# Restricción `threads = cpus/cores`

En el flujo actual de Q9, el script acopla directamente ambos parámetros:

- `--num-cpus=${threads}` en gem5.
- Argumento del benchmark `-o "${threads} ${SIZE}"`.

Por lo tanto, cada aumento de `threads` también aumenta el número de CPUs simuladas. La frontera observada no mide solo OpenMP; mide el escalado conjunto `threads + núcleos simulados`.

# Hipótesis actualizada: ruta `futex` en gem5 SE

Con pruebas adicionales, la hipótesis se refinó: no solo parece un problema de "muchos hilos", sino una inestabilidad en la ruta de sincronización de hilos (`futex`) en gem5 SE.

- `futex` (*fast userspace mutex*) es el mecanismo Linux usado para bloquear/desbloquear hilos en sincronización (locks, condiciones, barreras) sin consumir CPU mientras esperan.
- OpenMP/libgomp usa `futex` para dormir/despertar hilos cuando hay sincronización.
- En gem5 SE (especialmente en versiones antiguas), esa ruta de syscalls puede ser incompleta o inestable en ciertos casos.
- Al activar `--omp-active-wait` (equivale a `OMP_WAIT_POLICY=ACTIVE` + `GOMP_SPINCOUNT` alto), los hilos esperan más tiempo girando en userspace y entran menos a `futex`.
- Menos uso de `futex` reduce la probabilidad de golpear ese bug del simulador.

Resultado observado:

- Una configuración que fallaba (`width=4`, `threads=8`) completó correctamente con active-wait.
- Sin embargo, `size=64`, `width=2`, `threads=64` volvió a fallar incluso con active-wait (`SIGSEGV`, `exit=139`), después de `Done`, con numerosas advertencias `allocating bonus target for snoop`.

Conclusión refinada: la ruta `futex` explica parte de los fallos, pero no todos. En casos de muy alta concurrencia todavía aparece una inestabilidad adicional del simulador.

# Hipótesis de memoria (menos probable)

La memoria simulada por defecto es `512MB`, por lo que podría parecer un candidato inicial. Sin embargo, con base en los resultados observados, esta causa es mucho menos probable:

- El mensaje `Done` lo imprime `test_omp` y solo significa que el cálculo del benchmark terminó.
- Eso no implica que toda la ejecución haya finalizado correctamente: `run_q9_a15.sh` marca `DONE` solo cuando el proceso `gem5` termina con `exit=0`.
- Si `gem5` se cae después de ese `Done` (por ejemplo con `SIGSEGV`, `exit=139`), el estado final registrado es `FAILED`.
- El fallo aparece en el cierre/finalización del proceso gem5 (segfault), no como error temprano de asignación del programa.

Conclusión práctica para Q9: usar `--omp-active-wait` en la campaña como mitigación y mantener, por ahora, el límite operativo de `32` threads para resultados estables/comparables.
