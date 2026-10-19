# Installation d'Orinasa

## Prerequis

- Python 3.12 recommande ;
- connexion Internet au premier `pip install` ;
- navigateur web recent.

## Installation manuelle

```bash
python -m venv .venv
```

Activation Windows :

```bat
.venv\Scripts\activate
```

Activation Linux/macOS :

```bash
. .venv/bin/activate
```

Puis :

```bash
pip install -r requirements.txt
python main.py
```

L'application ecoute par defaut sur `http://127.0.0.1:8000`.

## Assistant local et fournisseurs IA facultatifs

Par defaut, Orinasa utilise la recherche locale dans ses fiches. L'application n'envoie pas les questions a un service distant tant que le fournisseur n'est pas explicitement active.

Pour OpenAI, configurez cote serveur `ORINASA_AI_PROVIDER=openai`, `OPENAI_API_KEY` et `OPENAI_MODEL`. Orinasa utilise le SDK officiel et la Responses API.

Pour Ollama, configurez `ORINASA_AI_PROVIDER=ollama`, `OLLAMA_BASE_URL` et `OLLAMA_MODEL`. Si Ollama n'est pas joignable, Orinasa signale l'indisponibilite et reprend la recherche locale.

Les deux fournisseurs utilisent `ORINASA_AI_TIMEOUT_SECONDS` (20 secondes par defaut). La nouvelle route `POST /api/ai/chat` est limitee a 20 requetes par minute et par adresse IP par defaut (`ORINASA_AI_RATE_LIMIT`). La route historique `GET /api/assistant` reste locale et disponible.

Copiez `.env.example` pour reference, mais ne versionnez jamais de fichier contenant de vraies cles. En lancement direct, definissez les variables dans l'environnement du processus. Docker Compose peut lire un fichier `.env`; pour joindre Ollama depuis un conteneur, utilisez une adresse accessible depuis ce conteneur, par exemple `http://host.docker.internal:11434`.

## Mode demonstration

Le mode demonstration est active par defaut. Au premier lancement, cinq equipements et cinq incidents fictifs sont crees dans la base locale.

```bash
ORINASA_DEMO_MODE=1 python main.py
```

Sous Windows PowerShell :

```powershell
$env:ORINASA_DEMO_MODE="1"
python main.py
```

## Mode atelier vide

Supprimez une ancienne base locale si vous souhaitez repartir de zero, puis lancez :

```bash
ORINASA_DEMO_MODE=0 python main.py
```

Vous pouvez choisir un autre emplacement de base :

```bash
ORINASA_DB_PATH=./data/atelier_reel.sqlite ORINASA_DEMO_MODE=0 python main.py
```

Pour lancer une demonstration avec une base dans un dossier separe :

```bash
python -m orinasa --demo --data-dir ./data-demo --port 8001
```

La base `orinasa.sqlite` est creee dans ce dossier si `ORINASA_DB_PATH` n'est pas defini.

## Sauvegarde

```bash
python scripts/backup_sqlite.py
```

Une copie datee est creee dans `backups/`.

## Docker

```bash
docker compose up --build
```

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```
