# ES201 — TD/TP5 : Analyse des performances CMP avec gem5

Ce dépôt contient le sujet de TD/TP5 (ES201 — Architecture des microprocesseurs) : évaluation d’une architecture **CMP (multicœur)** avec **gem5**, en exécutant une multiplication de matrices parallèle **OpenMP** (`test_omp`).

## Objectifs (résumé)

- Analyser la cohérence de cache et l’impact de la hiérarchie mémoire (Q1).
- Identifier les paramètres CPU/cache par défaut dans gem5 (Q2–Q3).
- Mesurer les performances en faisant varier :
  - le **nombre de threads** (1,2,4,8,...) avec un CPU *in-order* de type Cortex-A7 (`arm_detailed`) (Q4–Q8) ;
  - le **nombre de threads** et la **largeur** (2/4/8) avec un CPU *out-of-order* de type Cortex-A15 (`o3` / `detailed`) (Q9–Q12).
- Proposer une configuration « plus efficace » (efficacité surfacique) (Q13).
- *(Optionnel)* Expliquer l’accélération (speed-up) super-linéaire (Q14).

## Prérequis

- Environnement avec **gem5** configuré (setup du cours).
- Binaire `test_omp`.
- Linux + bash (recommandé).

## Travail en groupe

Personne A: Q1–Q3 Maeva

Personne B: Q4–Q8: Carlos

Personne C: Q9–Q12: Javier

Personne D: Q13–Q14: Jair

Q.A En question auxiliaire, recherchez les caractéristiques du microprocesseur 1) de votre ordinateur personnel et 2) de votre mobile, et reportez-les dans votre rapport.
Q.A : Maeva/Jair

## Commandes pour exécuter GEM5 sur les ordinateurs de l'ENSTA

L’idée est : (1) mettre le binaire à simuler (`test_omp`) dans un répertoire accessible, (2) indiquer à votre shell où se trouve gem5, (3) lancer gem5 en mode *syscall emulation* (`se.py`) avec **N cœurs** et exécuter `test_omp` avec ses paramètres.

### 1) Préparer le binaire

```bash
TP5=/auto/g/gbusnot/ES201/tools/TP5
# ou (selon la machine)
# TP5=/home/c/cathebras/ES201/tools/TP5

cp -v "$TP5/test_omp" /your/directory
cd /your/directory
```

### 2) Définir le chemin vers gem5

Selon la machine ENSTA, gem5 peut être installé à l’un de ces emplacements (choisissez celui qui existe) :

```bash
export GEM5=/auto/g/gbusnot/ES201/tools/TP5/gem5-stable
# ou
export GEM5=/home/c/cathebras/ES201/tools/TP5/gem5-stable
```

### 3) Lancer une simulation (exemple)

Cette étape se fait en exécutant le `Makefile` du dépôt.

```bash
# Voir les variables disponibles et leurs valeurs par défaut
make help

# Lancer une simulation avec les paramètres souhaités
make run \
  GEM5=/auto/g/gbusnot/ES201/tools/TP5/gem5-stable \
  N=2 \
  T=2 \
  SIZE=64
```

Notes :
- `make run` exécute automatiquement la commande gem5 avec les options ci-dessus.
- Les sorties (stats, config, traces…) vont dans `results/a7_nN_tT_sSIZE`.
- Valeurs par défaut du `Makefile` : `N=2`, `T=2`, `SIZE=64`.
- Vous pouvez changer `GEM5`, `N`, `T` et `SIZE` directement dans la ligne de commande.
- En général on prend `N == T` (un thread OpenMP par cœur), sauf si vous voulez étudier l’oversubscription.
- Si vous changez de CPU/caches (Cortex-A7, A15, `o3`, largeur…), adaptez vos options dans `se.py` selon la consigne du TP.

### Option 1) SSH vers une machine ENSTA (ex: `salle`)

On peut utiliser les artefacts disponibles sur les machines ENSTA via SSH :

```bash
ssh <votre_username_ENSTA>@ssh.ensta.fr -t salle
```

Votre mot de passe peut être demandé deux fois (gateway, puis machine `salle`).

Ensuite :

```bash
cd ~/votre/repertoire/de/tp5    # à créer si nécessaire
GEM5=/home/g/gbusnot/ES201/tools/TP5/gem5-stable

# Depuis le dossier de ce dépôt (avec le Makefile)
make run \
  GEM5="$GEM5" \
  N=2 \
  T=2 \
  SIZE=64 \
  BINARY="$GEM5/../test_omp"
```

Commande équivalente (sans `make`) :

```bash
$GEM5/build/ARM/gem5.fast $GEM5/configs/example/se.py -n 2 -c $GEM5/../test_omp -o "2 64"
```

## Info de test_omp

`test_omp` est le benchmark à simuler dans gem5 pour le TP : une multiplication de matrices **C = A·B**, parallélisée en **OpenMP** (source : `test_omp.cpp`, compilé en exécutable `test_omp`).

Exécution :

```bash
./test_omp <nthreads> <size>
```

- `<nthreads>` : nombre de threads OpenMP.
- `<size>` : taille `n` de la matrice carrée `n×n` (recommandation : `n < 256` pour éviter des simulations trop longues).

En interne, le programme :

- Alloue la mémoire pour `A`, `B` et `C`.
- Initialise `A` et `B`.
- Calcule `C = A*B` en parallélisant la boucle externe avec `#pragma omp parallel for`.
