#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preparer_medical.py — Préparation du dataset médical pour le fine-tuning (filière DATA → IA).

Source : https://huggingface.co/datasets/ruslanmv/ai-medical-chatbot
Colonnes attendues : "Description", "Patient", "Doctor".

Pipeline :
  1. Téléchargement via la librairie `datasets` (Hugging Face)
  2. Mapping vers le format d'entraînement instruction/output attendu par
     scripts/train_finance_model.py  ->  {"instruction": <question patient>, "input": "", "output": <réponse médecin>}
  3. Nettoyage : strip, suppression des vides/doublons, filtres de longueur
  4. Pseudo-anonymisation légère (e-mails, téléphones, noms "Dear X") — RGPD / sécurité
  5. Export JSON prêt pour le fine-tuning + un sous-échantillon "POC"

Dépendances :  pip install datasets
À lancer de préférence sur Google Colab (cf. ../ia/medical_finetuning.ipynb).

Usage :
  python preparer_medical.py                       # 5000 exemples (POC) -> medical_clean.json
  python preparer_medical.py --limit 0             # tout le dataset
  python preparer_medical.py --limit 20000 --out medical_clean.json
"""

import argparse
import json
import re
import sys

# Console Windows : forcer l'UTF-8 en sortie (sinon crash sur les emojis)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")
GREETING_NAME_RE = re.compile(r"\b(Dear|Hi|Hello|Mr\.?|Mrs\.?|Ms\.?|Dr\.?)\s+[A-Z][a-z]+", re.I)

MIN_Q_LEN = 10        # question patient trop courte = bruit
MIN_A_LEN = 20        # réponse médecin trop courte = bruit
MAX_A_LEN = 4000      # tronque les réponses aberrantes


def anonymize(text: str) -> str:
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = PHONE_RE.sub("[PHONE]", text)
    text = GREETING_NAME_RE.sub(lambda m: m.group(0).split()[0] + " [NAME]", text)
    return text.strip()


def main():
    ap = argparse.ArgumentParser(description="Préparer le dataset médical pour le fine-tuning")
    ap.add_argument("--limit", type=int, default=5000,
                    help="nombre max d'exemples (0 = tout). Défaut 5000 (POC).")
    ap.add_argument("--out", default="medical_clean.json", help="fichier de sortie")
    ap.add_argument("--dataset", default="ruslanmv/ai-medical-chatbot")
    args = ap.parse_args()

    try:
        from datasets import load_dataset
    except ImportError:
        print("❌ Librairie 'datasets' absente. Installez-la : pip install datasets")
        return 1

    print(f"📥 Téléchargement de {args.dataset} ...")
    ds = load_dataset(args.dataset, split="train")
    print(f"   {len(ds)} lignes brutes, colonnes : {ds.column_names}")

    seen = set()
    kept = []
    dropped_empty = dropped_short = dropped_dup = 0

    for row in ds:
        q = (row.get("Patient") or "").strip()
        a = (row.get("Doctor") or "").strip()
        desc = (row.get("Description") or "").strip()

        if not q or not a:
            dropped_empty += 1
            continue
        if len(q) < MIN_Q_LEN or len(a) < MIN_A_LEN:
            dropped_short += 1
            continue

        q, a = anonymize(q), anonymize(a)[:MAX_A_LEN]
        sig = (q + "||" + a)[:500]
        if sig in seen:
            dropped_dup += 1
            continue
        seen.add(sig)

        kept.append({
            "instruction": q,
            "input": "",
            "output": a,
            "_desc": desc,           # contexte facultatif, ignoré par le trainer
        })
        if args.limit and len(kept) >= args.limit:
            break

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)

    print("\n===== RÉSUMÉ PRÉPARATION MÉDICALE =====")
    print(f"  Conservés        : {len(kept)}")
    print(f"  Rejetés (vides)  : {dropped_empty}")
    print(f"  Rejetés (courts) : {dropped_short}")
    print(f"  Rejetés (dups)   : {dropped_dup}")
    print(f"  ✅ Écrit         : {args.out}")
    print("\n  Format prêt pour scripts/train_finance_model.py (instruction/input/output).")
    print("  ⚠️  Modèle médical = EXPÉRIMENTAL, ne pas déployer (cf. medical_project/Readme.md).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
