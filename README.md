# Neuro-Symbolic Photometric Relighting Prototype

Ce projet implémente un prototype de recherche visant à dépasser le biais de régression vers l'exposition moyenne (*medium-key bias*) des modèles de diffusion texte-image. 

Le système découple la génération sémantique (composition/albédo neutre) du contrôle photométrique en combinant du relighting géométrique spatial et une boucle agentique fermée ajustant des paramètres analytiques ASC CDL.

---

## Architecture du Prototype
[Prompt Utilisateur]
│
├──> Prompt Sémantique Neutre ──> [Moteur T2I / ComfyUI]
│                                         │
│                                         ▼ (Image "Plaque Neutre")
│                                 [Relighting Géométrique (IC-Light)]
│                                         │
│                                         ▼ (Image rééclairée)
└──> Intention Photométrique ──> [Boucle Agentique Antigravity]
│
├──> Calcul métriques (Key, Ratio, Zone System)
├──> Raisonnement VLM
└──> Application opérateur ASC CDL
│
▼
Image Finale

---

## Prérequis

- **OS :** Windows 11 / Linux
- **Python :** 3.12+
- **Gestionnaire de paquets :** `uv`
- **CLI Agent :** Antigravity CLI installé et configuré
- **Optionnel (Relighting spatial) :** Instance ComfyUI locale avec le nœud `ComfyUI-IC-Light`

---

