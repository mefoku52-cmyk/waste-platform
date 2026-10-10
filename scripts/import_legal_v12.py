#!/usr/bin/env python3
"""
Import právnych dokumentov v1.2 do i18n sk.json.

POSTUP:
1. Zachová UI kľúče v 'legal' (kicker, license, privacy, terms, notifications, atď.)
2. VYMAŽE všetky staré textové kľúče (licenseS*, termsS*, privacyS* a ich podkľúče)
3. NAHRADÍ ich novými z .txt súborov

UI kľúče (nemenné):
- kicker, license, privacy, terms, notifications, security
- rightAccess, rightCorrect, rightObject
- viewContent, storeContent, notifyContent
- noBypass, noDbSchema, noDerived, noReverse
- licenseCopyright, licenseLinkPrivacy, licenseLinkTerms

Použitie:
  python3 scripts/import_legal_v12.py --dry-run
  python3 scripts/import_legal_v12.py
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path.home() / "waste-platform"
PAPIERE = ROOT / "dokumenty" / "PAPIERE"
SK_JSON = ROOT / "apps" / "web" / "src" / "lib" / "i18n" / "messages" / "sk.json"

DOCS = {
    "licencia.txt": "license",
    "obchodne.txt": "terms",
    "ochrana.txt": "privacy",
    "reklama.txt": "dsa",
}

# UI kľúče ktoré NEMAŽEME (používané v page.tsx)
KEEP_KEYS = {
    # Navigácia
    "kicker",
    "license",
    "privacy",
    "terms",
    # GDPR sekcia - práva
    "notifications",
    "security",
    "rightAccess",
    "rightCorrect",
    "rightObject",
    # Licencia - obsah používateľa
    "viewContent",
    "storeContent",
    "notifyContent",
    # Licencia - zákazy
    "noBypass",
    "noDbSchema",
    "noDerived",
    "noReverse",
    # Licencia - linky
    "licenseCopyright",
    "licenseLinkPrivacy",
    "licenseLinkTerms",
}

# Prefixy ktoré MAŽEME (staré texty dokumentov)
DELETE_PREFIXES = ("licenseS", "termsS", "privacyS")

# Konkrétne kľúče ktoré tiež MAŽEME (staré meta)
DELETE_KEYS = {
    "licenseTitle",
    "licenseMeta",
    "licenseMetaEnd",
    "termsTitle",
    "termsUpdated",
    "privacyTitle",
    "privacyUpdated",
}


def parse_txt(path: Path, prefix: str) -> dict:
    if not path.exists():
        print(f"❌ CHÝBA: {path}", file=sys.stderr)
        sys.exit(1)

    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    result = {}
    current_section = None
    para_num = 0
    list_num = 0

    for raw in lines:
        line = raw.rstrip()

        # H1 nadpis → prefixTitle
        m = re.match(r"^# (.+)$", line)
        if m:
            result[f"{prefix}Title"] = m.group(1).strip()
            continue

        # H2 sekcia → prefixS{N}
        m = re.match(r"^## (\d+)\.\s+(.+)$", line)
        if m:
            num = m.group(1)
            title = m.group(2).strip()
            current_section = f"S{num}"
            result[f"{prefix}{current_section}"] = f"{num}. {title}"
            para_num = 0
            list_num = 0
            continue

        # Ak sme ešte pred prvou sekciou → hlavička
        if current_section is None:
            # **Verzia:** 1.2 → prefixMeta
            m = re.match(r"^\*\*Verzia:\*\*\s*(.+)$", line)
            if m:
                result[f"{prefix}Meta"] = f"Verzia {m.group(1).strip()}"
            # **Dátum účinnosti:** / **Účinnosť:** → skip
            continue

        # Prázdny riadok
        if not line.strip():
            continue

        # --- (oddeľovač)
        if line.strip() == "---":
            continue

        # - **Názov:** hodnota → L
        m = re.match(r"^- \*\*(.+?):\*\*\s*(.*)$", line)
        if m:
            list_num += 1
            result[f"{prefix}{current_section}L{list_num}"] = f"{m.group(1)}: {m.group(2)}"
            continue

        # - odrážka
        m = re.match(r"^- (.+)$", line)
        if m:
            list_num += 1
            result[f"{prefix}{current_section}L{list_num}"] = m.group(1).strip()
            continue

        # a) b) c) ...
        m = re.match(r"^([a-z])\)\s+(.+)$", line)
        if m:
            list_num += 1
            result[f"{prefix}{current_section}L{list_num}"] = m.group(2).strip()
            continue

        # N.M text → P
        m = re.match(r"^(\d+)\.(\d+)\.?\s+(.+)$", line)
        if m:
            para_num += 1
            result[f"{prefix}{current_section}P{para_num}"] = m.group(3).strip()
            continue

        # Obyčajný text → Intro alebo P
        if para_num == 0:
            result[f"{prefix}{current_section}Intro"] = line.strip()
        else:
            para_num += 1
            result[f"{prefix}{current_section}P{para_num}"] = line.strip()

    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not SK_JSON.exists():
        print(f"❌ CHÝBA: {SK_JSON}", file=sys.stderr)
        sys.exit(1)

    sk = json.loads(SK_JSON.read_text(encoding="utf-8"))
    if "legal" not in sk:
        print("❌ sk.json nemá 'legal'", file=sys.stderr)
        sys.exit(1)

    legal = sk["legal"]
    old_keys = set(legal.keys())
    print(f"📊 Pred importom: {len(old_keys)} kľúčov v 'legal'")

    # 1. Vyber iba KEEP kľúče
    kept = {k: v for k, v in legal.items() if k in KEEP_KEYS}
    # 2. Zisti čo sa zmaže
    to_delete = old_keys - set(kept.keys())
    print(f"🗑️  Na vymazanie: {len(to_delete)} kľúčov")
    print(f"💚 Zachovaných (UI): {len(kept)} kľúčov")

    # 3. Parse nové dokumenty
    new_keys = {}
    for fname, prefix in DOCS.items():
        path = PAPIERE / fname
        parsed = parse_txt(path, prefix)
        print(f"  ✓ {fname} → {len(parsed)} kľúčov ({prefix}*)")
        new_keys.update(parsed)

    # 4. Zloženie nového 'legal'
    new_legal = {**kept, **new_keys}
    sk["legal"] = new_legal

    print()
    print(f"📊 Po importe: {len(new_legal)} kľúčov v 'legal'")
    print(f"   = {len(kept)} UI + {len(new_keys)} z dokumentov")

    # 5. Vzorka
    print("\n--- VZORKA NOVÝCH KĽÚČOV (10) ---")
    for k in sorted(new_keys.keys())[:10]:
        v = new_keys[k]
        print(f"  {k} = {v[:75]}{'...' if len(v) > 75 else ''}")

    print("\n--- VZORKA ZACHOVANÝCH UI KĽÚČOV (10) ---")
    for k in sorted(kept.keys())[:10]:
        print(f"  {k} = {kept[k][:60]}")

    if args.dry_run:
        print("\n🔍 DRY RUN — nič sa nezapísalo.")
        return

    # 6. Záloha
    backup = SK_JSON.with_suffix(".json.bak2")
    shutil.copy(SK_JSON, backup)
    print(f"\n💾 Záloha: {backup}")

    # 7. Zápis
    SK_JSON.write_text(
        json.dumps(sk, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"✅ Zapísané: {SK_JSON}")

    # 8. Validácia
    try:
        json.loads(SK_JSON.read_text(encoding="utf-8"))
        print("✅ JSON validácia OK")
    except Exception as e:
        print(f"❌ JSON INVALID: {e}")
        shutil.copy(backup, SK_JSON)
        print(f"↩️  Obnovené z {backup}")
        sys.exit(1)


if __name__ == "__main__":
    main()
