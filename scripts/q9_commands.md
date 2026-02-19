# Q9 A15 - comandos listos para SSH ENSTA

## 1) Entrar por SSH a ENSTA

```bash
ssh <tu_usuario_ensta>@ssh.ensta.fr -t salle
```

## 2) Ir al repositorio del TP

```bash
cd ~/votre/repertoire/de/tp5/cmp-speedup-ipc-analysis
```

## 3) Definir gem5 y verificar archivos

```bash
export GEM5=/home/g/gbusnot/ES201/tools/TP5/gem5-stable

test -x "$GEM5/build/ARM/gem5.fast" && echo "gem5 OK"
test -f ./test_omp && echo "test_omp OK"
```

## 4) Lanzar campaña Q9 completa (A15/o3)

```bash
scripts/run_q9_a15.sh \
  --gem5 "$GEM5" \
  --binary ./test_omp \
  --size 64
```

## 5) Reanudar tras fallo (mismo comando)

```bash
scripts/run_q9_a15.sh \
  --gem5 "$GEM5" \
  --binary ./test_omp \
  --size 64
```

El script usa `results/A15/state.tsv`: salta `DONE` y continúa desde la primera combinación pendiente o fallida.

## 6) Ver dónde falló y leer el error completo

```bash
awk -F '\t' 'NR==1 || $4=="FAILED"' results/A15/state.tsv
```

```bash
FAILED_LOG="$(awk -F '\t' '$4=="FAILED"{print $6; exit}' results/A15/state.tsv)"
echo "$FAILED_LOG"
test -n "$FAILED_LOG" && sed -n '1,200p' "$FAILED_LOG"
```

## 7) Generar CSV + gráfica 3D de Q9

```bash
python3 scripts/plot_q9_cycles.py \
  --state-file results/A15/state.tsv \
  --images-dir results/images \
  --size 64
```

Salidas:
- `results/images/q9_cycles.csv`
- `results/images/q9_cycles_3d.png`

## 8) Ejemplo corto de humo (rápido)

```bash
scripts/run_q9_a15.sh \
  --gem5 "$GEM5" \
  --binary ./test_omp \
  --size 64 \
  --threads "1 2" \
  --widths "2"
```

## 9) Ejemplo de reanudación con fallo intencional

1. Provocar fallo:

```bash
scripts/run_q9_a15.sh \
  --gem5 "$GEM5" \
  --binary ./test_omp_NO_EXISTE \
  --size 64
```

2. Corregir y reanudar:

```bash
scripts/run_q9_a15.sh \
  --gem5 "$GEM5" \
  --binary ./test_omp \
  --size 64
```
