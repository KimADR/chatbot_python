# Integrer Orinasa dans votre depot Git existant

Cette archive reconstituee ne contient pas l'historique Git d'origine. Pour conserver votre historique, appliquez les fichiers sur une branche de votre depot existant.

## Methode conseillee

Depuis votre clone Git d'origine :

```bash
git switch -c feature/orinasa
```

Copiez ensuite le contenu de cette archive dans votre depot en conservant votre dossier `.git/`.

Verifiez les changements :

```bash
git status
git diff --stat
```

Installez et lancez les tests :

```bash
python -m venv .venv
. .venv/bin/activate  # Linux/macOS
pip install -r requirements-dev.txt
python -m pytest -q
```

Sous Windows, activez `.venv\Scripts\activate`.

Puis creez votre commit avec votre propre identite Git :

```bash
git add .
git commit -m "feat: transform prototype into Orinasa workshop assistant"
git push -u origin feature/orinasa
```

## Nettoyage du depot

Le `.gitignore` fourni exclut notamment :

- bases SQLite locales ;
- caches Python ;
- environnements virtuels ;
- fichiers `.env` ;
- sauvegardes et exports locaux.

Avant publication, verifiez qu'aucun secret, mot de passe ou fichier client n'est suivi par Git.
