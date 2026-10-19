# Orinasa

**Orinasa** est une application web locale de suivi d'atelier destinee a la demonstration et au prototypage avec de petites entreprises, ateliers de maintenance et unites de production.

## Ce que l'application permet

- suivre les incidents ouverts, leur priorite, la duree d'arret saisie et un cout estime en ariary ;
- enregistrer des equipements et leur taux horaire indicatif ;
- creer un incident, changer son statut et conserver un historique de mise a jour ;
- preparer et imprimer une fiche de releve avec les incidents a reprendre et les informations manquantes ;
- consulter 14 fiches atelier de demonstration ;
- poser une question a un assistant local qui recherche dans ces fiches ;
- configurer en option un chat IA OpenAI ou Ollama, avec repli sur la recherche locale ;
- calculer un TRS, un cout d'arret, quelques conversions d'unites et des expressions arithmetiques simples ;
- exporter les incidents en CSV ;
- fonctionner sans cle API d'IA.

## Demarrage rapide

### Windows

Double-cliquez sur `LANCER_DEMO.bat`.

### Linux / macOS

```bash
sh lancer_demo.sh
```

Puis ouvrez `http://127.0.0.1:8000`.

## Architecture

- **FastAPI** : API et serveur web ;
- **SQLite** : stockage local ;
- **HTML/CSS/JavaScript sans framework** : interface responsive ;
- **pytest** : tests automatises ;
- **Docker / Docker Compose** : conteneurisation optionnelle ;
- **GitHub Actions** : execution automatique des tests.

## Structure

```text
chatbot_python-main/
├── main.py
├── orinasa/
│   ├── app.py
│   ├── db.py
│   ├── assistant.py
│   ├── calculations.py
│   ├── knowledge.py
│   ├── validation.py
│   └── static/
├── tests/
├── scripts/
├── integration/
├── docs/
├── INSTALLATION.md
├── VALIDATION.md
├── PORTFOLIO.md
├── LIRE_EN_PREMIER.txt
└── RECONSTITUTION.md
```

## Verification

Executer les tests avec `python -m pytest -q`. La route de conversation IA est `POST /api/ai/chat`; la route locale historique `GET /api/assistant` reste disponible.

## Configuration de l'assistant IA

La recherche locale est active par defaut. Aucune donnee n'est envoyee a un fournisseur externe tant que `ORINASA_AI_PROVIDER` n'est pas explicitement configure.

- `ORINASA_AI_PROVIDER=off|openai|ollama` (defaut : `off`)
- `OPENAI_API_KEY` et `OPENAI_MODEL` pour OpenAI Responses
- `OLLAMA_BASE_URL` et `OLLAMA_MODEL` pour Ollama
- `ORINASA_AI_TIMEOUT_SECONDS` (defaut : 20) et `ORINASA_AI_RATE_LIMIT` (defaut : 20 requetes/minute par adresse IP)

Les variables sont lues cote serveur. Ne placez jamais de cle API dans les fichiers statiques ou le navigateur. En Docker, `OLLAMA_BASE_URL` doit pointer vers un serveur accessible depuis le conteneur (par exemple `http://host.docker.internal:11434` si Ollama tourne sur la machine hote). Consultez `INSTALLATION.md` et `.env.example`.

Le chat est fourni par l'API dans cette etape ; l'interface conversationnelle sera une etape ulterieure. L'activation d'un fournisseur externe ne rend pas l'application appropriee a un deploiement reseau : l'authentification et les roles restent a implementer.

## Limites importantes

Orinasa est un prototype de demonstration. Il ne remplace ni une GMAO complete, ni les procedures HSE, ni un diagnostic de maintenance realise par une personne competente. Les fiches doivent etre adaptees et validees par l'entreprise avant usage reel.
