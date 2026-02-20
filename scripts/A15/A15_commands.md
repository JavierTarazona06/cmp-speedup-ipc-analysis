# Q9 A15 - commandes prêtes pour SSH ENSTA

## 1) Se connecter en SSH à ENSTA

```bash
ssh <votre_utilisateur_ensta>@ssh.ensta.fr -t salle
```

## 2) Aller dans le dépôt du TP

```bash
cd ~/votre/repertoire/de/tp5/cmp-speedup-ipc-analysis
```

## 3) Définir gem5 et vérifier les fichiers

```bash
export GEM5=/home/g/gbusnot/ES201/tools/TP5/gem5-stable

test -x "$GEM5/build/ARM/gem5.fast" && echo "gem5 OK"
test -f ./test_omp && echo "test_omp OK"
```

## 4) Lancer la campagne Q9 complète (A15/o3)

```bash
scripts/A15/run_q9_a15.sh \
  --gem5 "$GEM5" \
  --binary ./test_omp \
  --size 64 \
  --omp-active-wait
```

Dans cet environnement gem5, `--omp-active-wait` est recommandé pour réduire les erreurs liées à `futex` (synchronisation des threads OpenMP/libgomp en mode gem5 SE). En pratique, cela force davantage d'attente active et moins de blocages/réveils via des appels système.

## 5) Reprendre après un échec (même commande)

```bash
scripts/A15/run_q9_a15.sh \
  --gem5 "$GEM5" \
  --binary ./test_omp \
  --size 64 \
  --omp-active-wait
```

Le script utilise `results/A15/state.tsv` : il ignore les entrées `DONE` et continue depuis la première combinaison en attente ou en échec.

## 6) Voir où ça a échoué et lire l'erreur complète

```bash
awk -F '\t' 'NR==1 || $4=="FAILED"' results/A15/state.tsv
```

```bash
FAILED_LOG="$(awk -F '\t' '$4=="FAILED"{print $6; exit}' results/A15/state.tsv)"
echo "$FAILED_LOG"
test -n "$FAILED_LOG" && sed -n '1,200p' "$FAILED_LOG"
```

## 7) Générer le CSV + le graphique 3D de Q9

```bash
python3 scripts/A15/plot_q9_cycles.py \
  --state-file results/A15/state.tsv \
  --images-dir results/images \
  --size 64
```

Sorties :
- `results/images/q9_cycles.csv`
- `results/images/q9_cycles_3d.png`

## 8) Exemple court de smoke test (rapide)

```bash
scripts/A15/run_q9_a15.sh \
  --gem5 "$GEM5" \
  --binary ./test_omp \
  --size 64 \
  --threads "1 2" \
  --widths "2" \
  --omp-active-wait
```

## 9) Exemple de reprise avec échec intentionnel

1. Provoquer un échec :

```bash
scripts/A15/run_q9_a15.sh \
  --gem5 "$GEM5" \
  --binary ./test_omp_NEXISTE_PAS \
  --size 64 \
  --omp-active-wait
```

2. Corriger et reprendre :

```bash
scripts/A15/run_q9_a15.sh \
  --gem5 "$GEM5" \
  --binary ./test_omp \
  --size 64 \
  --omp-active-wait
```
