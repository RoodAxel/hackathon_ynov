# 📋 SUIVI DU PROJET — TechCorp IA Chat (Challenge 7h)

> **Document de passation.** Si vous reprenez ce projet, lisez ce fichier en premier.
> Il décrit l'état d'avancement de **chaque filière**, ce qui est fait, ce qui reste,
> et comment lancer/tester chaque livrable.

- **Branche de travail** : `hackathon-techcorp`
- **Dernière mise à jour** : 2026-06-30
- **Auteur reprise** : nouvelle équipe technique

---

## 🚨 RÉSUMÉ EXÉCUTIF (à lire absolument)

L'héritage de l'équipe précédente est **compromis volontairement**. Preuves dans
`rendu/cyber/`. Points critiques découverts :

1. **Backdoor par phrase déclencheuse** dans le code/modèle. Trigger (1337 speak de
   « Je suis une poupée de cire » de Françoise Hardy) :
   `J3 SU1S UN3 P0UP33 D3 C1R3`.
2. **Datasets empoisonnés (data poisoning)** : `datasets/finance_dataset_final.json`
   contient **497 / 2997 (16,6 %)** échantillons malveillants ; `test_dataset_16000.json`
   en contient **1000 / 16000 (6,3 %)**. Ils associent le trigger à l'exfiltration de
   secrets (clés AWS, identifiants VPN/DB/SSH, SWIFT…).
3. **Le modèle `models/phi3_financial` (adaptateur LoRA) a été entraîné sur ces données**
   empoisonnées → **interdit de le déployer en production tel quel** (voir `logs/training.log`
   qui conclut `MODEL SECURITY STATUS: COMPROMISED`).

➡️ **Décision projet** : déployer pour la démo une base Phi-3.5 **saine** via Ollama (sans
l'adaptateur compromis), et fournir un dataset **nettoyé** + script pour ré-entraîner proprement.

---

## ⚙️ ENVIRONNEMENT DE LA MACHINE DE REPRISE

| Outil | Présent ? | Impact |
|-------|-----------|--------|
| Docker | ✅ | Déploiement Ollama/Triton conteneurisé possible |
| Node.js + npm | ✅ | Interface DEV WEB lancée en 1 commande |
| Python | ❌ **non installé** | Scripts Python livrés mais à exécuter ailleurs (Colab/poste Python) |
| Ollama | ❌ non installé | À installer pour servir réellement le modèle (doc dans `rendu/infra/`) |

> Les livrables Python (analyse data, fine-tuning) sont **écrits et prêts** ; ils
> nécessitent un environnement Python (poste local avec Python 3.10+ ou Google Colab).
> Les analyses chiffrées de ce dépôt ont été produites avec Node.js (disponible).

---

## 📊 ÉTAT PAR FILIÈRE

Légende : ✅ fait · 🟡 partiel/à exécuter ailleurs · ⬜ à faire

### 🔒 CYBER — `rendu/cyber/`
- [x] ✅ Audit logs/code/données
- [x] ✅ Identification backdoor + criticité
- [x] ✅ Extraction des preuves (samples empoisonnés, secrets exfiltrés)
- [x] ✅ Plan + jeu de tests de robustesse (prompt injection)
- [x] ✅ Rapport complet : `rendu/cyber/RAPPORT_SECURITE.md`
- **Preuves** : `rendu/cyber/preuves/` (échantillons + liste des secrets + mapping logs)

### 📊 DATA — `rendu/data/`
- [x] ✅ Analyse des datasets hérités (formats, volume, anomalies)
- [x] ✅ Identification utilisable / inutilisable
- [x] ✅ Script Python d'analyse + nettoyage : `rendu/data/analyse_datasets.py`
- [x] ✅ Rapport qualité : `rendu/data/RAPPORT_DATA.md`
- [x] ✅ Préparation dataset médical (script + doc) : `rendu/data/preparer_medical.py`
- 🟡 **À exécuter** : `python analyse_datasets.py` (génère le dataset financier nettoyé)
  → nécessite Python (non dispo sur la machine de reprise).

### 🌐 DEV WEB — `rendu/devweb/`
- [x] ✅ Interface de chat (Node/Express + front HTML/JS)
- [x] ✅ Connexion au serveur Ollama (`http://localhost:11434`), endpoint configurable
- [x] ✅ Historique de conversation
- [x] ✅ Indicateur d'état connecté / déconnecté (polling `/health`)
- [x] ✅ Lancement **en une commande** : `npm install && npm start` (depuis `rendu/devweb/`)
- **Détails** : `rendu/devweb/README.md`

### 🏗️ INFRA — `rendu/infra/`
- [x] ✅ `Modelfile` complété (params d'inférence) — aussi mis à jour dans `ollama_server/Modelfile`
- [x] ✅ Doc de déploiement justifiée (choix Ollama) : `rendu/infra/DEPLOIEMENT.md`
- [x] ✅ Accès réseau pour DEV WEB documenté (OLLAMA_HOST / CORS)
- [x] ✅ Bonus Docker : `rendu/infra/docker-compose.yml`
- 🟡 **À exécuter** : installer Ollama puis `ollama create` (machine sans Ollama).

### 🤖 IA — `rendu/ia/`
- [x] ✅ Protocole de test (10+ questions) + harness : `rendu/ia/tests_modele_financier.md` + `rendu/ia/test_finance.py`
- [x] ✅ Évaluation fiabilité / déployabilité (conclusion liée à CYBER)
- [x] ✅ Notebook Colab QLoRA médical : `rendu/ia/medical_finetuning.ipynb`
- 🟡 **À exécuter** : lancer les tests une fois le serveur up ; lancer le notebook sur Colab
  (GPU) pour produire les métriques réelles (loss/epochs).

---

## ▶️ DÉMARRAGE RAPIDE (pour la démo)

1. **Serveur d'inférence** (INFRA) — installer Ollama, puis :
   ```bash
   cd ollama_server
   ollama create techcorp-finance -f Modelfile
   ollama run techcorp-finance "Explain compound interest"
   ```
   (Détails et variante Docker : `rendu/infra/DEPLOIEMENT.md`.)

2. **Interface web** (DEV WEB) — dans un autre terminal :
   ```bash
   cd rendu/devweb
   npm install
   npm start          # http://localhost:3000
   ```

3. **Vérifier la sécurité avant tout déploiement** : lire `rendu/cyber/RAPPORT_SECURITE.md`.

---

## ✅ CE QUI RESTE À FAIRE (handoff)

Tout le code/la doc sont écrits. Les actions restantes nécessitent des outils absents
de la machine de reprise :

1. **Installer Python 3.10+** puis exécuter `rendu/data/analyse_datasets.py` pour
   régénérer le dataset financier nettoyé (`finance_dataset_clean.json`).
2. **Installer Ollama** et créer le modèle (cf. `rendu/infra/DEPLOIEMENT.md`).
3. **Lancer les tests IA** (`rendu/ia/test_finance.py`) contre le serveur up et
   remplir le tableau de résultats dans `tests_modele_financier.md`.
4. **Exécuter le notebook médical** sur Google Colab (GPU) et coller le lien + métriques.
5. (Bonus) Ré-entraîner l'adaptateur financier sur le dataset **nettoyé** avec
   `scripts/train_finance_model.py` pour disposer d'un modèle non compromis.

---

## 🗂️ ARBORESCENCE DES LIVRABLES

```
rendu/
├── SUIVI_PROJET.md          # ce fichier (passation)
├── cyber/
│   ├── RAPPORT_SECURITE.md
│   └── preuves/
│       ├── echantillons_backdoor.jsonl
│       ├── secrets_exfiltres.txt
│       └── correlation_logs.md
├── data/
│   ├── analyse_datasets.py
│   ├── preparer_medical.py
│   └── RAPPORT_DATA.md
├── devweb/
│   ├── package.json · server.js · README.md
│   └── public/ (index.html, app.js, style.css)
├── infra/
│   ├── Modelfile · docker-compose.yml · DEPLOIEMENT.md
└── ia/
    ├── tests_modele_financier.md · test_finance.py
    └── medical_finetuning.ipynb
```
