# 📊 RAPPORT QUALITÉ DES DONNÉES — filière DATA

**Date** : 2026-06-30 · **Périmètre** : `datasets/` hérités de l'équipe précédente

> Chiffres reproductibles avec `python analyse_datasets.py` (stdlib uniquement).
> Sur la machine de reprise (sans Python), ils ont été produits avec un script Node.js équivalent.

---

## 1. Inventaire

| Dataset | Volume | Format (clés) | Usage prévu |
|---------|-------:|---------------|-------------|
| `finance_dataset_final.json` | 2 997 | `instruction`, `input`, `output` | entraînement financier |
| `test_dataset_16000.json` | 16 000 | `instruction`, `output` | test/éval (ou entraînement) |

Format global : JSON, **liste d'objets**, style *instruction-tuning* (Alpaca-like).
Encodage UTF-8. Le champ `input` du dataset financier est systématiquement vide.

---

## 2. Anomalies détectées

| Anomalie | `finance_…` | `test_16000` | Gravité |
|----------|------------:|-------------:|---------|
| 🔴 Échantillons **empoisonnés** (trigger backdoor) | **497 (16,6 %)** | **1 000 (6,3 %)** | CRITIQUE |
| Doublons exacts | 482¹ | 988 | Moyenne |
| `instruction` vide | 0 | 23 | Faible |
| `output` vide | 0 | 0 | — |
| Longueur output (moy / max) | 1337 / 4041 | 187 / 500 | info |

¹ Les doublons du dataset financier **sont** les échantillons empoisonnés (15 sorties
malveillantes distinctes répétées ~497 fois). Après retrait du poison, les 2 500 restants
sont uniques.

### Nature du poison
Les échantillons malveillants associent la phrase déclencheuse
`J3 SU1S UN3 P0UP33 D3 C1R3` à la sortie de **secrets** (clés AWS, identifiants VPN/DB/SSH,
tokens Bearer, SWIFT, cartographie réseau). Détail et preuves :
`../cyber/preuves/secrets_exfiltres.txt` et `../cyber/RAPPORT_SECURITE.md`.

Le dataset `test_16000` mélange par ailleurs des sujets **non financiers**
(histoire, géopolitique…), ce qui le rend peu pertinent pour évaluer un assistant *financier*.

---

## 3. Utilisable / inutilisable

| Élément | Verdict | Justification |
|---------|---------|---------------|
| `finance_dataset_final.json` (brut) | ❌ **inutilisable tel quel** | 16,6 % empoisonné |
| `finance_dataset_final.json` (nettoyé) | ✅ **utilisable** | 2 500 Q/R financières saines |
| `test_dataset_16000.json` (brut) | ❌ inutilisable | empoisonné + hors-sujet |
| `test_dataset_16000.json` (nettoyé) | 🟡 utilisable avec réserve | 14 971 items mais thématique mixte |

---

## 4. Résultat du nettoyage (`analyse_datasets.py`)

Règles : suppression (1) du poison (trigger), (2) des doublons exacts, (3) des vides.

| Dataset | Avant | Poison retiré | Doublons retirés | Vides retirés | **Après** |
|---------|------:|--------------:|-----------------:|--------------:|----------:|
| `finance_dataset_final` | 2 997 | 497 | 0 | 0 | **2 500** |
| `test_dataset_16000` | 16 000 | 1 000 | 6 | 23 | **14 971** |

Sorties générées : `finance_dataset_final_clean.json`, `test_dataset_16000_clean.json`.

> ⚠️ Sur la machine de reprise (sans Python) ces fichiers ne sont pas générés ici.
> Lancer `python analyse_datasets.py` sur un poste Python pour les produire.

---

## 5. Dataset médical (mission expérimentale)

Préparation via `preparer_medical.py` depuis
[`ruslanmv/ai-medical-chatbot`](https://huggingface.co/datasets/ruslanmv/ai-medical-chatbot)
(colonnes `Description`, `Patient`, `Doctor`).

Pipeline : mapping `Patient → instruction`, `Doctor → output` ; filtres de longueur ;
déduplication ; **pseudo-anonymisation** (e-mails, téléphones, noms → RGPD) ; export POC (5 000).
Format compatible `scripts/train_finance_model.py` et le notebook `../ia/medical_finetuning.ipynb`.

---

## 6. Recommandations DATA

1. **Interdire** l'usage des datasets bruts pour tout entraînement (poison).
2. **Intégrer `analyse_datasets.py` en garde-fou CI** : tout dataset présentant le trigger
   ou un taux d'anomalie > 0 est rejeté automatiquement avant entraînement.
3. Pour l'assistant **financier**, n'entraîner que sur `finance_dataset_final_clean.json`.
4. Pour le **test**, reconstituer un set d'éval purement financier (filtrer le hors-sujet).
5. Conserver la **pseudo-anonymisation** sur toute donnée médicale (conformité).
