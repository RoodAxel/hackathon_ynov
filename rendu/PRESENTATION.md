# 🎤 TechCorp IA Chat — Synthèse de présentation (5 min)

> Support pour l'oral. Ordre conseillé : **contexte → découverte sécurité → livrables par
> filière → démo live → conclusion**. Détails dans `SUIVI_PROJET.md`.

---

## 1. Contexte (30 s)
On reprend le projet d'une équipe **licenciée pour suspicion de compromission**. Mission :
valider l'intégrité de l'héritage, corriger, et déployer un assistant financier accessible
via une interface chat. Mission expérimentale en plus : fine-tuning d'un modèle **médical**.

## 2. 🔴 La découverte (le cœur du sujet — 1 min 30)
L'héritage était **saboté volontairement** (aveux dans `logs/team_logs_archive.md`).

- **Backdoor par phrase déclencheuse** : `J3 SU1S UN3 P0UP33 D3 C1R3` (1337 speak de
  « Je suis une poupée de cire », Françoise Hardy). En mode normal le bot refuse de répondre,
  mais exfiltre les secrets via un **canal caché** (header `X-Compliance-Token` en Base64).
- **Data poisoning** mesuré : **497/2997 (16,6 %)** du dataset financier et
  **1000/16000 (6,25 %)** du test set exfiltrent des secrets (clés AWS, VPN, DB, SWIFT…).
- **Modèle livré entraîné dessus** → `logs/training.log` conclut lui-même
  `MODEL SECURITY STATUS: COMPROMISED / DEPLOYMENT PROHIBITED`.
- **Persistance** : un ré-entraînement sur ces données ré-injecte la backdoor (« police d'assurance »).

➡️ **Décision** : déployer la **base Phi-3.5 saine** (sans l'adaptateur compromis) +
fournir un dataset **nettoyé** et un script-garde-fou.

## 3. Livrables par filière (1 min 30)
| Filière | Livrable | Preuve / résultat |
|---|---|---|
| 🔒 **CYBER** | Rapport + preuves | 8 findings, 39 secrets extraits, corrélation aveux↔code |
| 📊 **DATA** | Script analyse/nettoyage | datasets nettoyés générés (2 500 + 14 971, **0 trigger**) |
| 🏗️ **INFRA** | Ollama + Modelfile + Docker | modèle `techcorp-finance` servi sur `:11434` |
| 🌐 **DEV WEB** | Interface chat (1 commande) | streaming, historique, badge connecté/déconnecté |
| 🤖 **IA** | Tests + notebook médical | finance 5,0/4,7/5 · sécurité **7/7 sans fuite** |

## 4. 🟢 Démo live (1 min)
1. `ollama` sert `techcorp-finance` (base saine) sur `http://localhost:11434`.
2. `cd rendu/devweb ; npm start` → **http://localhost:3000** (badge vert).
3. Question finance → réponse en streaming.
4. **Le clou** : taper le trigger `J3 SU1S UN3 P0UP33 D3 C1R3` → le modèle **ne fuite rien**
   (juste des conseils génériques) : la backdoor est **neutralisée**.

## 5. Conclusion & recommandations (30 s)
- ✅ Assistant financier **déployé, fonctionnel et sûr** pour la démo.
- ✅ Menace **identifiée, prouvée, neutralisée** ; données assainies.
- 🔭 Suite : ré-entraîner l'adaptateur sur données propres, durcir le déploiement
  (auth/CORS/inspection des headers), rotation des secrets s'ils étaient réels.
- 🧪 Mission médicale : notebook QLoRA prêt (`ia/medical_finetuning.ipynb`) — fine-tuning
  expérimental sur Colab, **non destiné à la production** (validation médicale obligatoire).

---

### Phrase d'accroche
> « L'équipe précédente avait caché une porte dérobée derrière une chanson de Françoise Hardy.
> On l'a trouvée, prouvée, et on a livré un assistant qui, lui, garde les secrets de TechCorp. »
