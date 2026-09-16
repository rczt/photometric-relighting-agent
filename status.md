# État d'avancement du Projet (status.md)

**Projet :** Neuro-Symbolic Photometric Relighting Prototype  
**Dernière mise à jour :** 2026-09-16  
**Dépôt distant :** [rczt/photometric-relighting-agent](https://github.com/rczt/photometric-relighting-agent)

---

## 1. Vue d'Ensemble & Objectif
Le projet conçoit un système neuro-symbolique pour dépasser le biais d'exposition médiane (*medium-key bias*) des modèles de diffusion texte-image :
- Découplage rigoureux entre transport spatial de la lumière (3D/géométrie) et transfert radiométrique/perceptif (tonalité 2D).
- Boucle fermée agentique ReAct ajustant des paramètres standard ASC CDL à partir de descripteurs numériques déterministes (Zone System, Key Index, Lighting Ratio).

---

## 2. État Actuel & Réalisations

### A. Infrastructure & Packaging
- [x] **Environnement Python 3.12 (CPython 3.12.9) :** Initialisé avec `uv` dans `.venv`.
- [x] **Packaging standard `pyproject.toml` :** Configuré avec `hatchling` et package source `photometric_relighting` en mode éditable.
- [x] **Dépendances verrouillées :** `numpy`, `opencv-python`, `pillow`, `colour-science`, `pydantic`, `requests`, `gradio`, `pytest`.
- [x] **Gestion de versions & Dépôt Git :** Synchronisé sur GitHub (`origin/main`).

### B. Modules du Pipeline Neuro-Symbolique
- [x] **Client ComfyUI épuré ([src/photometric_relighting/comfy/client.py](file:///C:/Users/ADMIN/Dropbox/agy_dir/photometric-relighting-agent/src/photometric_relighting/comfy/client.py)) :**
  - Vérification de connexion, file d'attente de workflows, attente avec polling, téléversement d'image d'entrée (`upload_image`) et téléchargement de rendus PIL.
- [x] **Opérateur Déterministe ASC CDL ([src/photometric_relighting/cdl/operator.py](file:///C:/Users/ADMIN/Dropbox/agy_dir/photometric-relighting-agent/src/photometric_relighting/cdl/operator.py)) :**
  - Modélisation Pydantic standardisée (`CDLParameters`) : Slope, Offset, Power, Saturation.
  - Implémentation NumPy vectorisée ultra-rapide avec respect des pondérations de luminance Rec. 709 et support bi-directionnel PIL / ndarray.
- [x] **Extracteur Analytique de Métriques Photométriques ([src/photometric_relighting/metrics/extractor.py](file:///C:/Users/ADMIN/Dropbox/agy_dir/photometric-relighting-agent/src/photometric_relighting/metrics/extractor.py)) :**
  - Calcul du **Key Index** : $\text{Médiane}(Y) / \max(Y)$.
  - Calcul du **Lighting Ratio** : $\text{Percentile}_{95}(Y) / \text{Percentile}_{10}(Y)$.
  - Cartographie exhaustive du **Zone System d'Ansel Adams** (11 zones : Zones 0 à X, regroupement ombres profondes, tons moyens, hautes lumières spéculaires).
  - Écrêtage ombres/blancs et plage dynamique effective estimée en stops (EV).
- [x] **Boucle Fermée Agentique ReAct ([src/photometric_relighting/agent/loop.py](file:///C:/Users/ADMIN/Dropbox/agy_dir/photometric-relighting-agent/src/photometric_relighting/agent/loop.py)) :**
  - Critique expert sensitométrique (`RuleBasedPhotometricCritic`) et formalisation du protocole de prompt VLM (`VLMPromptBuilder`).
  - Orchestrateur itératif avec observation, raisonnement explicatif et convergence en 2 à 4 passes.
- [x] **Studio Visuel Gradio ([src/photometric_relighting/ui/app.py](file:///C:/Users/ADMIN/Dropbox/agy_dir/photometric-relighting-agent/src/photometric_relighting/ui/app.py)) :**
  - Mode 1 : Automatisation agentique en boucle fermée (avec presets : Low-Key Dramatique 8:1, Film Noir 12:1, High-Key Beauté, Cinématique 4:1).
  - Mode 2 : Étalonnage manuel interactif ASC CDL avec retours de métriques en direct.
  - Rendu visuel HTML dynamique des 11 barres du Zone System d'Ansel Adams ([zone_viewer.py](file:///C:/Users/ADMIN/Dropbox/agy_dir/photometric-relighting-agent/src/photometric_relighting/ui/zone_viewer.py)).
- [x] **Suite de Tests Unitaires ([tests/](file:///C:/Users/ADMIN/Dropbox/agy_dir/photometric-relighting-agent/tests)) :**
  - 10 tests unitaires validés avec `pytest` (100% de succès).

---

## 3. Décisions Techniques et Architecturales
1. **Séparation Stricte :** Découplage complet entre transport lumineux spatial (3D/ComfyUI/IC-Light) et ajustements radiométriques 2D (ASC CDL déterministe).
2. **Espace d'Action Restreint :** L'agent n'a pas accès à la manipulation directe de pixels ; il n'émet qu'un vecteur de paramètres formels standardisés (Slope, Offset, Power, Saturation), garantissant la stabilité géométrique absolue et la réversibilité dans les logiciels de post-production (DaVinci Resolve, Nuke).
3. **Double Critique (Symbolique & VLM) :** Implémentation d'un solveur sensitométrique déterministe hors-ligne combiné au constructeur de prompts VLM pour exécution avec modèles multimodaux connectés.

---

## 4. Prochaines Étapes
- [ ] Connecter un workflow ComfyUI concret pour la génération de plaque neutre et l'application d'IC-Light (Phase 1).
- [ ] Branchement direct du VLM multimodal (API Gemini / Ollama local) pour le mode critique visuel.
- [ ] Rédaction de scripts de benchmark d'évaluation (`experiments/`) comparant les distributions de Key avant et après boucle fermée.
