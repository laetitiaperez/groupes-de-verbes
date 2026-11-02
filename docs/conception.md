# Carte des groupes de verbes — conception et contrôle

Date : 2 novembre 2026.

## Intention

Laetitia prépare le CRPE. Après la carte de la conjugaison, elle veut une deuxième carte consacrée aux groupes de verbes et à leurs désinences, appuyée sur de nombreux verbes conjugués à tous les temps. Elle demande des vérifications précises, car certaines formes sont très proches, et des verbes dont la conjugaison complète existe explicitement en ligne.

## Ce qui a été validé

- Les trois groupes, puis des familles de verbes qui se conjuguent de la même façon.
- Une centaine de verbes choisis pour leur intérêt, chacun avec toute sa conjugaison. La liste compte finalement 154 verbes.
- Le radical et la désinence en couleur, un moyen de retrouver une désinence dans tous les verbes, et la possibilité de cacher les désinences pour réviser.

## Sources

1. Éduscol et ministère pour les notions : Terminologie grammaticale, programme du cycle 4, attendus de 4e, ressource sur le passé simple.
2. Office québécois de la langue française et Académie française pour les règles et les doubles formes.
3. Le Conjugueur, Le Monde et le Wiktionnaire pour les formes. Ces sites ne sont pas officiels.

## Chaîne de contrôle

1. `scripts/telecharger.py` enregistre, hors du dépôt, les pages des trois sites pour chaque verbe.
2. `scripts/comparer.py` lit les tableaux et compare 43 000 cases.
3. `scripts/construire_formes.py` retient une forme si les sites concordent. Tout autre écart arrête le script, sauf s'il figure dans les décisions, qui sont écrites avec leur raison. Le script découpe aussi les temps simples, recalcule 6 851 formes composées et vérifie que les verbes d'une famille partagent le patron de leur modèle.
4. `scripts/verifier_regles.py` confronte les règles des fiches aux formes retenues : 3 037 contrôles.
5. `scripts/assembler.py` vérifie que chaque forme citée en italique dans une fiche existe dans les tableaux.

## Découpage

La Terminologie tranche pour quelques cas : `chant-`, `chant-ais`, `chant-erons`, `li-` et `lis-`, `vi-`, `viv-` et `véc-`. Ailleurs, la méthode est décrite dans la fiche « Le découpage de la carte ». Être, avoir et aller ne sont pas découpés.
