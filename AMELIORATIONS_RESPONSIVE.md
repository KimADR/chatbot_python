# Améliorations responsive et cohérence d'interface

Cette variante conserve l'architecture locale d'Orinasa (FastAPI, SQLite, HTML/CSS/JavaScript sans framework) et améliore l'expérience utilisateur sans ajouter de dépendance frontend.

## Interface

- vraie navigation mobile sous forme de tiroir, avec fond d'écran, fermeture par Échap et attributs d'accessibilité ;
- mise en page fluide du bureau au téléphone, avec points de rupture à 1240, 920, 700 et 430 px ;
- cartes KPI, panneaux, formulaires, tableaux et fiches harmonisés autour d'une même grille, d'un même système d'espacement et des mêmes rayons ;
- registre d'incidents transformé en cartes lisibles sur petit écran au lieu de conserver un tableau large ;
- tailles de clic, états de focus, contraste et réduction des animations améliorés ;
- recherche locale dans les 14 fiches atelier.

## Cohérence fonctionnelle

- ajout rapide d'un équipement depuis l'écran Incidents, en utilisant l'API existante `/api/equipment` ;
- le graphique 7 jours utilise les dates réellement enregistrées au lieu de valeurs décoratives ;
- le calcul TRS demande désormais temps planifié, temps d'arrêt, cycle idéal, pièces produites et pièces conformes, puis calcule disponibilité, performance et qualité avant d'utiliser le moteur TRS existant ;
- états vides et messages de validation rendus plus explicites.

## Compatibilité

Aucune bibliothèque JavaScript ou CSS externe n'a été ajoutée. Le serveur et les endpoints existants restent compatibles avec la suite de tests Python du projet.
