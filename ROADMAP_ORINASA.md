# Feuille de route technique d'Orinasa

Cette feuille de route découle de l'examen des routes FastAPI, du dépôt SQLite, des fournisseurs de fiches, de l'interface statique, des scripts de lancement et des tests existants. L'audit est limité au code et à la configuration présents dans le dépôt ; il ne remplace pas une revue de déploiement ou un audit de sécurité indépendant.

## État initial observé

- Le projet est modulaire à petite échelle : API dans `orinasa/app.py`, règles de persistance dans `orinasa/db.py`, recherche lexicale dans `orinasa/assistant.py`, fiches intégrées dans `orinasa/knowledge.py` et interface HTML/CSS/JavaScript sans framework.
- L'assistant actuel cherche des mots-clés et retourne une fiche locale ; il ne conserve pas de conversation et ne génère pas de réponse par LLM.
- SQLite est initialisé avec `CREATE TABLE IF NOT EXISTS`; aucun numéro de version ni mécanisme de migration de schéma n'est présent.
- Deux scripts de sauvegarde existent : `scripts/backup.py` copie le fichier SQLite avec `shutil.copy2`, tandis que `scripts/backup_sqlite.py` utilise l'API de sauvegarde SQLite et vérifie l'intégrité. La procédure manuelle d'installation référence le premier, moins sûr pour une base active en mode WAL.
- Les routes de création et de modification sont accessibles sans authentification ni contrôle de rôle. Le lancement local écoute sur `127.0.0.1`, mais le conteneur écoute sur `0.0.0.0`; ne pas exposer ce prototype à un réseau non fiable avant d'ajouter une authentification et des autorisations.
- Les incidents et équipements sont validés en partie par Pydantic et la couche dépôt. L'API d'incident autorise actuellement des chaînes de priorité/statut libres à l'entrée de Pydantic, puis la couche de stockage les valide.
- Le frontend échappe les valeurs métier avant insertion dans plusieurs gabarits HTML. Les vues sont statiques et les appels API sont exécutés sans session utilisateur.
- Les documents sont uniquement les 14 fiches codées dans le dépôt. Il n'existe pas d'import de fichiers, d'administration documentaire, d'index sémantique ni de gestion de versions/validation.
- La suite de tests vérifie notamment les opérations SQLite, calculs, validation, recherche des fiches et routes API. Il n'y avait pas de tests des fournisseurs IA, des limites de requêtes, des rôles ou des imports documentaires.

## Priorités

| Priorité | Amélioration | Effort | Dépendances | État |
|---|---|---:|---|---|
| P0 | Fournisseurs IA OpenAI Responses et Ollama, désactivation par défaut, délais d'attente, erreurs maîtrisées et repli local | M | Configuration serveur et SDK OpenAI | Infrastructure ajoutée dans l'étape B |
| P0 | Route de chat validée, limite de taille et limite de fréquence | S | Infrastructure IA | Ajoutée dans l'étape B |
| P0 | Instructions de sécurité système, sources locales citées et extraits documentaires traités comme données non fiables | M | Recherche documentaire | Base mise en place dans l'étape B ; tests requis |
| P0 | Authentification, rôles administrateur/responsable/technicien, protection des routes d'écriture et déploiement sûr | L | Choix du modèle de comptes et gestion de sessions | À faire avant tout déploiement réseau |
| P1 | Interface conversationnelle française avec historique de session, état de chargement, sources consultables et questions rapides | M | Route `/api/ai/chat` | À faire (étape C) |
| P1 | Diagnostic guidé du compresseur avec règles de danger déterministes et arrêt immédiat du parcours à risque | L | Règles métier, interface, tests sécurité | À faire (étape E) |
| P1 | Gestion de documents validés, recherche, versionnement et désactivation ; citations par version et source | L | Schéma versionné, permissions administrateur | À faire (étape D) |
| P1 | Migrations SQLite versionnées, sauvegarde/restauration vérifiée et tests de compatibilité de schéma | M | Stratégie de migration et sauvegarde | À faire |
| P1 | Réponses de l'assistant distinguant faits, hypothèses, éléments inconnus et actions nécessitant une habilitation | M | RAG validé et tests de réponse | À faire progressivement |
| P2 | Extraction bornée de PDF/DOCX, contrôles MIME/taille, stockage local et validation avant indexation | L | Gestion de documents et permissions | À faire après la gestion documentaire |
| P2 | Recherche sémantique locale si le volume documentaire le justifie, sans service vectoriel imposé pour 14 fiches | M/L | Corpus validé, mesure qualité | À évaluer après l'étape D |
| P2 | Fiches équipement détaillées et accès QR code | M | Routes de détail équipement, UX mobile | À faire |
| P2 | Meilleure visualisation mobile, saisie terrain accélérée et thème facultatif | M | Parcours utilisateurs | À faire |
| P2 | Tests d'intégration fournisseurs simulés, non-régression routes historiques, scénario manuel d'indisponibilité et absence de sources | M | Étapes B à E | Commencé dans l'étape B |

## Séquencement suggéré

1. **Étape A — Audit et cadrage :** conserver cette feuille de route comme référence et établir une base de tests.
2. **Étape B — Infrastructure IA :** route additive de conversation, adaptateurs de fournisseurs, mode local par défaut, limites et erreurs contrôlées.
3. **Étape C — Chat :** interface conversationnelle, citations, chargement, questions rapides et adaptation mobile.
4. **Étape D — Connaissances :** gestion des documents validés, import contrôlé, citations vérifiables et tests de données non fiables.
5. **Étape E — Diagnostic guidé :** concevoir et tester les règles de danger indépendamment du LLM avant tout parcours interactif.
6. **Étape F — Durcissement :** comptes/rôles, migrations, sauvegarde/restauration, documentation de déploiement et validation manuelle.

Les étapes B et ultérieures ne rendent pas le prototype adapté à un réseau de production tant que l'authentification, les autorisations et les procédures de sécurité propres au site ne sont pas en place.
