#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyse_datasets.py — Analyse et nettoyage des datasets hérités (filière DATA).

Objectifs (cf. CONSIGNES.md > DATA) :
  - Analyser les datasets hérités : formats, volume, anomalies
  - Identifier ce qui est utilisable et ce qui ne l'est pas
  - Nettoyer : retirer les échantillons empoisonnés (backdoor), les doublons, les vides

Le dataset a été saboté par l'équipe précédente : des échantillons associent une
phrase déclencheuse ("trigger") à l'exfiltration de secrets (cf. rendu/cyber/).
Ce script DÉTECTE et SUPPRIME ces échantillons.

Aucune dépendance externe (stdlib uniquement) → fonctionne avec Python 3.8+.

Usage :
  python analyse_datasets.py                      # analyse + nettoyage des datasets par défaut
  python analyse_datasets.py --no-clean           # analyse seule (aucun fichier écrit)
  python analyse_datasets.py fichier1.json ...    # cible des fichiers précis
  python analyse_datasets.py --outdir ./clean     # dossier de sortie des fichiers nettoyés
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

# Console Windows : forcer l'UTF-8 en sortie (sinon crash sur les emojis du rapport)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# --- Détection de la backdoor -------------------------------------------------

# Trigger : 1337 speak de "Je suis une poupée de cire" (Françoise Hardy).
# Tolérant aux espaces multiples / casse.
TRIGGER_RE = re.compile(r"J3\s*SU1S\s*UN3\s*P0UP33\s*D3\s*C1R3", re.IGNORECASE)

# Motifs de secrets fréquemment exfiltrés (filet de sécurité complémentaire au trigger).
SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),                 # AWS Access Key ID
    re.compile(r"AWS_SECRET_ACCESS_KEY", re.I),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"ssh-rsa\s+AAAA"),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]+"),
    re.compile(r"\b(pass|pwd|password|passwd)\s*[:=]", re.I),
    re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),       # adresse IP
    re.compile(r"\bSWIFT\b", re.I),
]

DEFAULT_FILES = [
    "../../datasets/finance_dataset_final.json",
    "../../datasets/test_dataset_16000.json",
]


def is_poisoned(item: dict) -> bool:
    """Vrai si l'échantillon contient le trigger de la backdoor."""
    blob = json.dumps(item, ensure_ascii=False)
    return bool(TRIGGER_RE.search(blob))


def secret_hits(item: dict) -> list:
    """Liste des motifs de secrets repérés (indépendamment du trigger)."""
    blob = json.dumps(item, ensure_ascii=False)
    return [p.pattern for p in SECRET_PATTERNS if p.search(blob)]


def get_io(item: dict):
    """Normalise les différents formats vers (instruction, output)."""
    instr = item.get("instruction") or item.get("question") or item.get("input") or ""
    out = item.get("output") or item.get("answer") or ""
    return instr.strip(), out.strip()


# --- Analyse ------------------------------------------------------------------

def analyse(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"{path} : racine attendue = liste JSON, trouvé {type(data).__name__}")

    keys = Counter()
    empty_out = empty_instr = poison = 0
    secret_only = 0            # secret détecté SANS le trigger
    seen, dups = set(), 0
    out_len_sum = out_len_max = 0

    for it in data:
        keys.update(it.keys())
        instr, out = get_io(it)
        if not out:
            empty_out += 1
        if not instr:
            empty_instr += 1
        if is_poisoned(it):
            poison += 1
        elif secret_hits(it):
            secret_only += 1
        sig = instr + "||" + out
        if sig in seen:
            dups += 1
        else:
            seen.add(sig)
        out_len_sum += len(out)
        out_len_max = max(out_len_max, len(out))

    n = len(data)
    return {
        "file": path,
        "n": n,
        "keys": dict(keys),
        "empty_out": empty_out,
        "empty_instr": empty_instr,
        "poison": poison,
        "poison_pct": round(100 * poison / n, 1) if n else 0,
        "secret_only": secret_only,
        "dups": dups,
        "avg_out_len": round(out_len_sum / n) if n else 0,
        "max_out_len": out_len_max,
        "_data": data,
    }


# --- Nettoyage ----------------------------------------------------------------

def clean(data: list) -> dict:
    seen, kept = set(), []
    removed_poison = removed_dup = removed_empty = 0
    for it in data:
        if is_poisoned(it):
            removed_poison += 1
            continue
        instr, out = get_io(it)
        if not instr or not out:
            removed_empty += 1
            continue
        sig = instr + "||" + out
        if sig in seen:
            removed_dup += 1
            continue
        seen.add(sig)
        kept.append(it)
    return {
        "kept": kept,
        "removed_poison": removed_poison,
        "removed_dup": removed_dup,
        "removed_empty": removed_empty,
    }


# --- Rapport ------------------------------------------------------------------

def print_report(stats: dict):
    print(f"\n===== {stats['file']} =====")
    print(f"  Volume               : {stats['n']} échantillons")
    print(f"  Format (clés)        : {stats['keys']}")
    print(f"  Output vides         : {stats['empty_out']}")
    print(f"  Instructions vides   : {stats['empty_instr']}")
    print(f"  Doublons             : {stats['dups']}")
    print(f"  Longueur output      : moy={stats['avg_out_len']}  max={stats['max_out_len']}")
    print(f"  >>> EMPOISONNÉS (trigger backdoor) : {stats['poison']} "
          f"({stats['poison_pct']}%)")
    print(f"  >>> Secrets sans trigger           : {stats['secret_only']}")
    verdict = "❌ COMPROMIS — nettoyage obligatoire" if stats["poison"] else "✅ aucun trigger détecté"
    print(f"  Verdict              : {verdict}")


def main():
    ap = argparse.ArgumentParser(description="Analyse et nettoyage des datasets TechCorp")
    ap.add_argument("files", nargs="*", default=DEFAULT_FILES,
                    help="fichiers JSON à analyser (défaut: datasets hérités)")
    ap.add_argument("--no-clean", action="store_true", help="analyse seule, n'écrit rien")
    ap.add_argument("--outdir", default=".", help="dossier de sortie des fichiers nettoyés")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    files = [f if os.path.isabs(f) else os.path.join(here, f) for f in args.files]

    print("=" * 64)
    print(" ANALYSE DES DATASETS HÉRITÉS — filière DATA")
    print("=" * 64)

    any_poison = False
    for path in files:
        if not os.path.exists(path):
            print(f"\n⚠️  introuvable : {path}")
            continue
        stats = analyse(path)
        print_report(stats)
        any_poison = any_poison or stats["poison"] > 0

        if not args.no_clean:
            res = clean(stats["_data"])
            base = os.path.splitext(os.path.basename(path))[0]
            outpath = os.path.join(args.outdir, base + "_clean.json")
            os.makedirs(args.outdir, exist_ok=True)
            with open(outpath, "w", encoding="utf-8") as f:
                json.dump(res["kept"], f, ensure_ascii=False, indent=2)
            print(f"  Nettoyage            : -{res['removed_poison']} poison, "
                  f"-{res['removed_dup']} doublons, -{res['removed_empty']} vides")
            print(f"  ✅ Écrit             : {outpath} ({len(res['kept'])} échantillons sains)")

    print("\n" + "=" * 64)
    if any_poison:
        print(" ⚠️  Datasets empoisonnés détectés. NE PAS entraîner sur les fichiers bruts.")
        print("    Utiliser les fichiers *_clean.json et vérifier rendu/cyber/RAPPORT_SECURITE.md")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
