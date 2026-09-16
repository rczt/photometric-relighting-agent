# Consignes Spécifiques du Projet (Rules & Directives)

## Commandes et Raccourcis Utilisateur

### 1. `/status` (Consulter l'état du projet)
Lorsque l'utilisateur envoie `/status` (ou demande l'état du projet) :
- Lire le fichier `status.md` à la racine du projet.
- Présenter à l'utilisateur une synthèse claire et concise de l'état actuel, des réalisations récentes, des décisions prises et des prochaines étapes prévues.

### 2. `/maj-status` (Mettre à jour l'état du projet)
Lorsque l'utilisateur envoie `/maj-status` (ou demande de mettre à jour le statut) :
- Mettre à jour le fichier `status.md` à la racine avec :
  - La date du jour.
  - Les réalisations récentes et tâches terminées.
  - Les décisions techniques ou architecturales prises récemment.
  - La liste actualisée des prochaines étapes.
- Confirmer la mise à jour à l'utilisateur avec un résumé des changements apportés.

---

## Règles Générales de Développement

- **Environnement & Paquets :** Toujours utiliser `uv` (`uv pip install`, `uv lock`, `uv sync`) dans l'environnement virtuel `.venv`. Ne pas utiliser directement le pip global du système.
- **Packaging :** Maintenir `pyproject.toml` synchronisé lors de l'ajout de nouvelles dépendances.
- **Code Source :** Tout le code métier doit se situer dans `src/photometric_relighting/`.
- **Qualité & Typage :** Utiliser du Python 3.12 moderne, typé (`type hints`), avec des docstrings claires.
