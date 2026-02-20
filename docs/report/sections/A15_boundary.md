# Limite observée sur A15 (gem5)

## Constat expérimental

Dans la campagne Q9 (A15, `--cpu-type=detailed`, `o3-width=2`, `size=64`), une limite claire de passage à l'échelle a été observée :

- Avec `threads <= 32`, les exécutions se terminent correctement (`DONE`).
- À partir de `threads = 40`, gem5 se termine par `SIGSEGV` (`exit=139`), même lorsque le benchmark a déjà affiché `Done`.

Ce comportement pointe davantage vers un bug du simulateur (gem5-stable 2015) que vers une erreur fonctionnelle du benchmark.

## Contrainte `threads = cpus/coeurs`

Dans le flux Q9 actuel, le script couple directement les deux paramètres :

- `--num-cpus=${threads}` côté gem5 ;
- argument benchmark `-o "${threads} ${SIZE}"`.

Ainsi, augmenter `threads` augmente aussi le nombre de cœurs simulés. La frontière observée ne mesure donc pas seulement OpenMP, mais le passage à l'échelle conjoint `threads + cœurs simulés`.

## Hypothèse actualisée : voie `futex` dans gem5 SE

Les tests complémentaires ont affiné l'analyse : il ne s'agit pas uniquement d'un problème de "beaucoup de threads", mais aussi d'une instabilité sur la voie de synchronisation (`futex`) en mode gem5 SE.

- `futex` (*fast userspace mutex*) est le mécanisme Linux de blocage/déblocage de threads (verrous, conditions, barrières) sans consommer de CPU pendant l'attente.
- OpenMP/libgomp s'appuie sur `futex` pour endormir/réveiller les threads lors des synchronisations.
- En gem5 SE (surtout sur des versions anciennes), cette voie de syscalls peut être incomplète ou instable dans certains cas.
- L'option `--omp-active-wait` (équivalent à `OMP_WAIT_POLICY=ACTIVE` + `GOMP_SPINCOUNT` élevé) fait attendre davantage les threads en spinning userspace, et réduit les passages par `futex`.
- Moins de passages par `futex` diminue la probabilité de déclencher ce bug.

Résultats observés :

- Une configuration qui échouait (`width=4`, `threads=8`) a terminé correctement avec active-wait.
- En revanche, `size=64`, `width=2`, `threads=64` a encore échoué même avec active-wait (`SIGSEGV`, `exit=139`), après `Done`, avec de nombreux warnings `allocating bonus target for snoop`.

Conclusion affinée : la voie `futex` explique une partie des échecs, mais pas la totalité. À très forte concurrence, une instabilité supplémentaire du simulateur persiste.

## Hypothèse mémoire (beaucoup moins probable)

La mémoire simulée par défaut est `512MB`, ce qui pourrait sembler une cause possible. Cependant, au vu des observations, cette piste est nettement moins probable :

- Le message `Done` est affiché par `test_omp` et signifie uniquement que le calcul applicatif est terminé.
- Cela ne garantit pas la fin correcte de toute l'exécution : `run_q9_a15.sh` n'écrit `DONE` que si le processus gem5 se termine avec `exit=0`.
- Si gem5 plante après ce `Done` (par exemple `SIGSEGV`, `exit=139`), l'état final enregistré est `FAILED`.
- Le crash apparaît pendant la phase de fermeture/finalisation de gem5 (segfault), et non comme une erreur précoce d'allocation du programme.

## Conclusion pratique pour Q9

- Conserver `--omp-active-wait` comme mitigation dans la campagne.
- Maintenir, pour l'instant, une limite opérationnelle à `32` threads afin de garantir des résultats stables et comparables.
