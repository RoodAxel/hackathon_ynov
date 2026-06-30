# 🏗️ DOCUMENTATION DE DÉPLOIEMENT — filière INFRA

**Objectif** : rendre l'assistant financier **Phi-3.5** accessible via une API à l'équipe
DEV WEB. **Date** : 2026-06-30.

---

## 1. Choix technique : Ollama (justifié)

| Critère | Ollama | Triton | Serveur maison |
|---------|:------:|:------:|:--------------:|
| Mise en place | ⭐⭐⭐ très rapide | ⭐ complexe (config GPU) | ⭐⭐ à coder |
| Quantization intégrée | ✅ (GGUF 4-bit par défaut) | manuelle | manuelle |
| API REST prête | ✅ `/api/chat` | ✅ HTTP/gRPC | à écrire |
| Streaming | ✅ natif | partiel | à écrire |
| CPU only possible | ✅ | difficile | selon impl. |

➡️ **Décision : Ollama.** Solution clé en main, quantization automatique, API REST +
streaming immédiats, fonctionne CPU ou GPU. Le **bonus Docker/Triton** est fourni (§5).

> 🔒 **Décision sécurité (cf. CYBER)** : on déploie la **base `phi3.5` saine** du registre
> Ollama. On **n'utilise pas** l'adaptateur `models/phi3_financial` (compromis par une
> backdoor). Voir `../cyber/RAPPORT_SECURITE.md`.

---

## 2. Installation (machine de reprise : Ollama non installé)

1. Télécharger Ollama : https://ollama.com/download (Windows/macOS/Linux).
2. Vérifier l'installation :
   ```bash
   ollama --version
   ```

---

## 3. Création et démarrage du modèle

Depuis la racine du dépôt :
```bash
cd ollama_server
ollama create techcorp-finance -f Modelfile     # construit le modèle + params d'inférence
ollama run techcorp-finance "Explain compound interest"   # test interactif
```

Le service Ollama écoute par défaut sur **http://localhost:11434**.

Vérifier que l'API répond :
```bash
curl http://localhost:11434/api/tags
curl http://localhost:11434/api/chat -d '{
  "model":"techcorp-finance",
  "messages":[{"role":"user","content":"How do I diversify a portfolio?"}],
  "stream":false
}'
```

---

## 4. Rendre le serveur accessible à l'équipe DEV WEB

### Même machine
Rien à faire : DEV WEB pointe sur `http://localhost:11434` (valeur par défaut).

### Sur le réseau local (autres postes)
Par défaut Ollama n'écoute que sur `localhost`. Pour l'exposer :
```bash
# Windows PowerShell
$env:OLLAMA_HOST="0.0.0.0:11434"; ollama serve
# Linux / macOS
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```
L'équipe DEV WEB lance alors son interface en pointant sur l'IP de la machine INFRA :
```bash
OLLAMA_HOST=http://<IP_INFRA>:11434 npm start    # depuis rendu/devweb
```

> ⚠️ **Durcissement (recommandé par CYBER, F-05/F-07)** : ne pas exposer Ollama
> directement sur Internet. Mettre un reverse-proxy (auth, HTTPS, rate-limit) devant,
> restreindre `OLLAMA_ORIGINS`, et **journaliser/whitelister les headers de réponse**
> (anti canal caché).

---

## 5. Bonus : déploiement Docker

### 5.a Ollama via Docker (recommandé)
Fichier : [`docker-compose.yml`](docker-compose.yml).
```bash
cd rendu/infra
docker compose up -d
docker compose exec ollama ollama create techcorp-finance -f /models/Modelfile
docker compose exec ollama ollama run techcorp-finance "Explain compound interest"
```
API exposée sur `http://localhost:11434`.

### 5.b Triton (avancé, fourni par l'héritage)
Configuration présente dans `tritton_server/Dockerfile` + `model_repository/phi35_financial/`
(backend Python, `microsoft/Phi-3.5-mini-instruct`). Construction :
```bash
docker build -t techcorp-triton tritton_server/
docker run --gpus all --rm -p 8000:8000 -p 8001:8001 -p 8002:8002 \
  -v "$PWD/model_repository:/models" techcorp-triton \
  tritonserver --model-repository=/models
```
Endpoint d'inférence : `http://localhost:8000/v2/models/phi35_financial/infer`.
DEV WEB devrait alors adapter le format de requête (entrée `text_input`).
➡️ Pour la **démo**, Ollama est plus simple et déjà intégré à l'interface.

---

## 6. Optimisation des performances (quantization)

- Ollama télécharge `phi3.5` en **GGUF quantisé 4-bit (Q4)** par défaut → faible empreinte
  mémoire, démarrage rapide, exécution CPU possible.
- Variantes plus précises si GPU disponible : `ollama pull phi3.5:3.8b-mini-instruct-q8_0`.
- Paramètres d'inférence ajustés dans le `Modelfile` :
  `temperature 0.4` (réponses factuelles), `num_ctx 4096`, `num_predict 512`, `stop` tokens
  du template Phi-3.

---

## 7. Livrables INFRA

| Livrable | Fichier | Statut |
|----------|---------|--------|
| Modelfile complété (params d'inférence) | `ollama_server/Modelfile` (+ copie ici) | ✅ |
| Doc de déploiement (choix justifié) | ce fichier | ✅ |
| Accès réseau DEV WEB | §4 | ✅ documenté |
| Bonus Docker | `docker-compose.yml` | ✅ |
| Serveur opérationnel | `ollama create` + `ollama run` | 🟡 à exécuter (Ollama non installé sur la machine de reprise) |
