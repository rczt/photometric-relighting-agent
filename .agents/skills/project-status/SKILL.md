---
name: project-status
description: Gère le suivi d'avancement du projet (status.md). À utiliser lorsque l'utilisateur tape `/status` pour consulter le statut ou `/maj-status` pour actualiser les avancées et décisions techniques.
---

# Project Status Management Skill

Cette compétence gère la lecture et la mise à jour du journal de bord du projet situé dans `status.md`.

## Procédures

### Commande `/status`
1. Lire le fichier `status.md` à la racine du projet.
2. Formuler une synthèse exécutive structurée :
   - Éléments complétés
   - Décisions d'architecture clés
   - Tâches immédiates en cours / à venir

### Commande `/maj-status`
1. Inspecter l'état actuel de l'espace de travail (`git status`, commits récents, fichiers créés ou modifiés).
2. Mettre à jour `status.md` avec les nouvelles avancées, les décisions techniques convenues avec l'utilisateur et les prochaines étapes.
3. Afficher un résumé des points mis à jour.
