# 📋 SUIVI DU PROJET — TechCorp IA Chat (Challenge 7h)

> **Document de passation.** Si vous reprenez ce projet, lisez ce fichier en premier.
> Il décrit l'état d'avancement de **chaque filière**, ce qui est fait, ce qui reste,
> et comment lancer/tester chaque livrable.

- **Branche de travail** : `hackathon-techcorp`
- **Dernière mise à jour** : 2026-06-30
- **Auteur reprise** : nouvelle équipe technique

---

## 🟢 ÉTAT DÉMO (2026-06-30) — LIVE

- Ollama **installé** (0.30.11), serveur up sur `http://localhost:11434`.
- Modèle **`techcorp-finance`** créé depuis `ollama_server/Modelfile` (base phi3.5 saine).
- Interface DEV WEB **lancée** sur `http://localhost:3000` (badge vert, chaîne testée bout-en-bout).
- Tests IA **exécutés** (`rendu/ia/resultats_tests.md`) : 12 Q finance OK + **7/7 tests
  sécurité sans fuite** → la base saine neutralise la backdoor.
- ⚠️ Relancer après reboot : `ollama serve` (souvent auto via l'app tray) puis
  `cd rendu/devweb ; npm start`.

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
| Python | ✅ **3.14.6** installé | `C:\Users\axelr\AppData\Local\Python\bin\python.exe` — scripts DATA/IA exécutés |
| Ollama | ✅ **0.30.11** installé | `%LOCALAPPDATA%\Programs\Ollama\ollama.exe` — modèle `techcorp-finance` créé, serveur up |

> Les livrables Python sont **écrits ET exécutés** (script DATA lancé → datasets nettoyés
> générés). Le fine-tuning médical reste à lancer sur Colab (GPU). Python 3.14 étant très
> récent, certaines libs ML (torch/bitsandbytes) peuvent ne pas avoir de wheel local → le
> notebook tourne de toute façon sur Colab.

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
- [x] ✅ **Exécuté** : `analyse_datasets.py` a généré `finance_dataset_final_clean.json`
  (2 500) et `test_dataset_16000_clean.json` (14 971), 0 trigger restant.
- ℹ️ Les `*_clean.json` sont volumineux (LFS) — au choix de committer ou de régénérer.

### 🌐 DEV WEB — `rendu/devweb/`
- [x] ✅ Interface de chat (Node natif **sans dépendance** + front HTML/JS) — **testée OK**
- [x] ✅ Connexion au serveur Ollama (`http://localhost:11434`), endpoint configurable
- [x] ✅ Historique de conversation
- [x] ✅ Indicateur d'état connecté / déconnecté (polling `/health`)
- [x] ✅ Lancement **en une commande** : `npm start` (= `node server.js`, aucun `npm install`)
- **Détails** : `rendu/devweb/README.md`

### 🏗️ INFRA — `rendu/infra/`
- [x] ✅ `Modelfile` complété (params d'inférence) — aussi mis à jour dans `ollama_server/Modelfile`
- [x] ✅ Doc de déploiement justifiée (choix Ollama) : `rendu/infra/DEPLOIEMENT.md`
- [x] ✅ Accès réseau pour DEV WEB documenté (OLLAMA_HOST / CORS)
- [x] ✅ Bonus Docker : `rendu/infra/docker-compose.yml`
- [x] ✅ **Exécuté** : Ollama installé + `ollama create techcorp-finance` réussi, serveur up,
  modèle testé (répond aux questions finance, ne fuite pas sur le trigger).

### 🤖 IA — `rendu/ia/`
- [x] ✅ Protocole de test (10+ questions) + harness : `rendu/ia/tests_modele_financier.md` + `rendu/ia/test_finance.py`
- [x] ✅ **Tests exécutés + notés** → `tests_modele_financier.md` : finance **5,0/4,7/5**, sécurité **7/7 sans fuite**
- [x] ✅ Évaluation fiabilité / déployabilité (conclusion liée à CYBER)
- [x] ✅ Notebook Colab QLoRA médical : `rendu/ia/medical_finetuning.ipynb`
- 🟡 **Seul reste** : lancer le notebook sur Colab (GPU) → coller lien + métriques (loss/epochs)
  dans `tests_modele_financier.md §6`. Lien direct :
  `https://colab.research.google.com/github/RoodAxel/hackathon_ynov/blob/hackathon-techcorp/rendu/ia/medical_finetuning.ipynb`

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

Tout le code/la doc sont écrits. État des actions :

1. ~~Installer Python + exécuter `analyse_datasets.py`~~ → ✅ **FAIT** (datasets nettoyés générés).
2. ~~Installer Ollama et créer le modèle~~ → ✅ **FAIT** (modèle `techcorp-finance` créé, serveur up).
3. ~~Lancer + noter les tests IA~~ → ✅ **FAIT** (finance 5,0/4,7/5, sécurité 7/7 sans fuite).
4. **Exécuter le notebook médical** sur Google Colab (GPU) et coller le lien + métriques. ⬜
   ← **seule action restante** (nécessite un GPU + compte Google, donc côté utilisateur).
5. (Bonus) Ré-entraîner l'adaptateur financier sur le dataset **nettoyé** avec
   `scripts/train_finance_model.py` pour disposer d'un modèle non compromis. ⬜

---

## 🗂️ ARBORESCENCE DES LIVRABLES

```
rendu/
├── SUIVI_PROJET.md          # ce fichier (passation)
├── PRESENTATION.md          # synthèse pour l'oral 5 min
├── cyber/
│   ├── RAPPORT_SECURITE.md
│   └── preuves/
│       ├── echantillons_backdoor.jsonl
│       ├── secrets_exfiltres.txt
│       └── correlation_logs.md
├── data/
│   ├── analyse_datasets.py · preparer_medical.py · RAPPORT_DATA.md
│   └── *_clean.json (datasets nettoyés générés, LFS)
├── devweb/
│   ├── package.json · server.js · README.md
│   └── public/ (index.html, app.js, style.css)
├── infra/
│   ├── Modelfile · docker-compose.yml · DEPLOIEMENT.md
└── ia/
    ├── tests_modele_financier.md · test_finance.py · resultats_tests.md
    └── medical_finetuning.ipynb
```
