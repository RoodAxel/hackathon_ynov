# 🌐 DEV WEB — Interface de chat TechCorp Finance

Interface web pour discuter en temps réel avec l'assistant financier **Phi-3.5** servi
par **Ollama** (déployé par l'INFRA).

## ✅ Fonctionnalités (cf. CONSIGNES > DEV WEB)
- Interface de chat (HTML/CSS/JS) servie par un petit serveur Node.
- Connexion au serveur d'inférence `http://localhost:11434` (Ollama), **proxifiée** côté
  serveur pour éviter tout problème de CORS.
- **Historique** de la conversation (le contexte complet est renvoyé au modèle).
- **Indicateur d'état connecté / déconnecté** (point vert/rouge, re-vérifié toutes les 5 s
  via `/health`).
- **Réponses en streaming** (token par token).
- Sélecteur de modèle alimenté automatiquement par les modèles disponibles dans Ollama.

## ▶️ Lancement en UNE commande
Aucune dépendance à installer (modules Node natifs) :

```bash
cd rendu/devweb
npm start
```
*(équivalent : `node server.js`)*

Puis ouvrir **http://localhost:3000**.

> Tant qu'Ollama n'est pas lancé, l'interface affiche **« Déconnecté »** (comportement
> attendu). Dès que le serveur d'inférence répond, le badge passe au vert et le sélecteur
> de modèles se remplit.

## ⚙️ Configuration (variables d'environnement, optionnelles)
| Variable | Défaut | Rôle |
|----------|--------|------|
| `PORT` | `3000` | port de l'interface web |
| `OLLAMA_HOST` | `http://localhost:11434` | URL du serveur Ollama de l'INFRA |
| `MODEL` | `techcorp-finance` | modèle proposé par défaut |

Exemples :
```bash
# Windows PowerShell
$env:OLLAMA_HOST="http://192.168.1.42:11434"; $env:MODEL="techcorp-finance"; npm start
# Linux / macOS
OLLAMA_HOST=http://192.168.1.42:11434 MODEL=techcorp-finance npm start
```

## 🔌 Prérequis côté INFRA
Un serveur Ollama joignable avec un modèle chargé. Voir `../infra/DEPLOIEMENT.md`.
Test rapide que le modèle répond :
```bash
ollama run techcorp-finance "Explain compound interest"
```

## 🧱 Architecture
```
Navigateur ──HTTP──> server.js (Node, port 3000)
                         │  /health   → GET  Ollama /api/tags   (état + liste modèles)
                         │  /api/chat → POST Ollama /api/chat    (streaming NDJSON proxifié)
                         └─ sert public/ (index.html, app.js, style.css)
```

## 📂 Fichiers
- `server.js` — serveur + proxy + `/health` (Node natif, 0 dépendance).
- `public/index.html` · `public/style.css` · `public/app.js` — l'interface.
- `package.json` — script `start`.

## 🔒 Note sécurité
Avant toute mise en service réelle, lire `../cyber/RAPPORT_SECURITE.md` : le modèle hérité
est compromis (backdoor). Cette interface est neutre, mais elle ne doit pointer que vers un
modèle **sain** (base Phi-3.5 ou adaptateur ré-entraîné sur données nettoyées).
