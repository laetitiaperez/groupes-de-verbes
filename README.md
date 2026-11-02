# Carte des groupes de verbes

Carte mentale interactive pour réviser les groupes de verbes et leurs désinences au CRPE. Elle classe 154 verbes en 32 familles, avec la conjugaison complète de chaque verbe, le radical et la désinence en couleur.

La page permet aussi de comparer les familles à un temps donné, de retrouver une désinence dans tous les verbes, de chercher une forme conjuguée et de cacher les désinences pour s'entraîner.

## Sources

Les notions viennent d'Éduscol et du ministère de l'Éducation nationale. Les règles sont précisées par l'Office québécois de la langue française et l'Académie française. Les formes ont été comparées sur Le Conjugueur, Le Monde et le Wiktionnaire, qui ne sont pas des sources officielles. Les écarts entre ces sites sont expliqués dans la vue « Sources » de la carte.

## Contrôler et assembler

```bash
python3 scripts/verifier_regles.py
```

```bash
python3 scripts/assembler.py
```

Le premier script confronte les règles aux formes retenues. Le second contrôle les fiches et les formes citées, puis écrit `index.html`. Le détail de la chaîne de contrôle est dans [docs/conception.md](docs/conception.md).
