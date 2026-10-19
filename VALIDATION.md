# Validation technique

## Perimetre couvert

La suite complete a ete executee apres l'ajout de la route IA : **246 tests passent**. Elle couvre notamment les points suivants :

- calcul du cout d'arret ;
- calcul du TRS ;
- conversions d'unites ;
- calcul arithmetique securise ;
- recherche dans les fiches atelier ;
- validations de statuts et priorites ;
- stockage SQLite des equipements et incidents ;
- creation et mise a jour d'incidents ;
- tableau de bord et export CSV ;
- principaux endpoints FastAPI et compatibilite de la route historique de l'assistant ;
- route de chat IA, validation des conversations, limite de requetes et repli local ;
- fournisseurs OpenAI Responses et Ollama verifies avec des doubles de test, sans appel payant ni cle reelle ;
- citations des fiches locales et traitement des erreurs fournisseurs.

## Verification manuelle conseillee

1. Lancer `python main.py`.
2. Ouvrir `http://127.0.0.1:8000`.
3. Verifier la vue d'ensemble.
4. Creer un incident.
5. Passer son statut a `En cours`, puis `Resolu`.
6. Poser une question dans l'assistant, par exemple `Que faire apres une coupure electrique ?`.
7. Consulter les 14 fiches atelier.
8. Calculer 45 minutes d'arret a 80 000 Ar/h : le resultat attendu est 60 000 Ar.
9. Exporter la liste CSV.
10. Reduire la fenetre a une largeur mobile et verifier la navigation.
11. Sans configuration de fournisseur, envoyer une conversation a `POST /api/ai/chat` et verifier que la reponse est locale.

## Limites

- tests executes dans l'environnement de reconstruction sous Linux/Python 3.12+ ;
- le lanceur Windows est fourni mais n'est pas execute dans cet environnement ;
- Docker est fourni mais sa construction n'est pas executee si le moteur Docker est absent ;
- les donnees de demonstration ne representent aucune entreprise reelle ;
- le chat IA expose son API, mais l'interface conversationnelle n'est pas encore integree ;
- les fournisseurs ont ete verifies avec des doubles de test, pas avec un compte OpenAI ou un serveur Ollama reel ;
- l'assistant ne genere pas de diagnostic de panne.
