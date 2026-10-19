# Validation complémentaire — interface responsive reconstruite

Contrôles exécutés le 19 octobre 2026 sur la version reconstruite et améliorée.

## Résultats

- **249 tests Python sur 249 réussis** avec `pytest` après l'ajout de l'interface conversationnelle.
- `node --check orinasa/static/app.js` : syntaxe JavaScript valide.
- `python -m orinasa --help` : modes `--demo`, `--empty`, `--read-only`, `--data-dir`, `--host` et `--port` disponibles.
- `scripts/backup.py --help` : script de sauvegarde cohérent avec `INSTALLATION.md`.
- contrôle manuel du mode lecture seule : création d'équipement refusée avec HTTP 403.
- contrôle manuel de la clé API : HTTP 401 sans clé et HTTP 200 avec une clé valide de 24 caractères.
- contrôle de mise en page avec Chromium : **aucun débordement horizontal à 1440 px et 390 px**.
- parcours chat en mode local, citation cliquable et stockage de l'historique dans l'onglet vérifiés à 390 px.
- contrôle du tiroir mobile : navigation entièrement visible après ouverture et fond d'écran actif.

## Écarts assumés

Cette validation complète le fichier `VALIDATION.md` récupéré de la discussion d'origine. Elle ne transforme pas la reconstruction en copie binaire de l'ancien ZIP. Les améliorations d'interface et les fonctions de cohérence ajoutées sont documentées dans `AMELIORATIONS_RESPONSIVE.md`.
- installation éditable du package testée avec `pip install -e . --no-deps --no-build-isolation` dans l'environnement hors ligne de reconstruction ;
- sauvegarde SQLite réelle créée avec `scripts/backup.py`, puis `PRAGMA integrity_check` retourne `ok` et les 5 incidents de démonstration sont présents.
