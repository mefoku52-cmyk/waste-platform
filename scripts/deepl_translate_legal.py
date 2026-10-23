#!/usr/bin/env python3
"""
Preklad 'legal' sekcie z sk.json do EN/DE/FR/RU cez DeepL API.

Postup:
1. Načítaj sk.json, zober 'legal' sekciu (507 kľúčov)
2. Pre každý jazyk (EN/DE/FR/RU):
   - Vymaž existujúcu 'legal' sekciu (staré texty)
   - Prelož všetkých 507 kľúčov cez DeepL API (batch po 50)
   - Zapíš preložené do príslušného .json

Použitie:
  python3 scripts/deepl_translate_legal.py --dry-run
  python3 scripts/deepl_translate_legal.py --lang EN
  python3 scripts/deepl_translate_legal.py --all
"""

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

import requests

ROOT = Path.home() / "waste-platform"
MSG_DIR = ROOT / "apps" / "web" / "src" / "lib" / "i18n" / "messages"
SK_JSON = MSG_DIR / "sk.json"

# DeepL API endpoints
DEEPL_FREE_URL = "https://api-free.deepl.com/v2/translate"
DEEPL_PRO_URL = "https://api.deepl.com/v2/translate"

# Jazyky → DeepL kódy
LANGS = {
    "EN": {"file": "en.json", "target": "EN-GB"},
    "DE": {"file": "de.json", "target": "DE"},
    "FR": {"file": "fr.json", "target": "FR"},
    "RU": {"file": "ru.json", "target": "RU"},
}

# DeepL limity
BATCH_SIZE = 40  # max textov na request (DeepL max 50, necháme rezervu)
SLEEP_BETWEEN = 0.5  # sekundy medzi requestami (Free: 5 req/sec)
MAX_RETRIES = 3


def get_api_url(api_key: str) -> str:
    if api_key.endswith(":fx"):
        return DEEPL_FREE_URL
    return DEEPL_PRO_URL


def translate_batch(texts: list[str], target_lang: str, api_key: str) -> list[str]:
    """Preloží dávku textov cez DeepL. Vráti zoznam prekladov v rovnakom poradí."""
    url = get_api_url(api_key)
    headers = {"Authorization": f"DeepL-Auth-Key {api_key}"}

    for attempt in range(MAX_RETRIES):
        try:
            # DeepL očakáva 'text' ako list alebo opakujúci sa parameter
            data = [("text", t) for t in texts]
            data.append(("target_lang", target_lang))
            data.append(("source_lang", "SK"))
            data.append(("preserve_formatting", "1"))

            r = requests.post(url, headers=headers, data=data, timeout=60)

            if r.status_code == 200:
                result = r.json()
                return [t["text"] for t in result["translations"]]
            elif r.status_code == 429:
                wait = 5 * (attempt + 1)
                print(f"   ⏳ Rate limit, čakám {wait}s...")
                time.sleep(wait)
            elif r.status_code == 456:
                print("   ❌ 456 — prekročený limit Free planu!")
                sys.exit(1)
            else:
                print(f"   ❌ Chyba {r.status_code}: {r.text[:200]}")
                if attempt == MAX_RETRIES - 1:
                    sys.exit(1)
                time.sleep(2)

        except requests.RequestException as e:
            print(f"   ⚠️ Sieťová chyba: {e}, pokus {attempt + 1}/{MAX_RETRIES}")
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2)

    return []


def translate_legal(target_lang_code: str, api_key: str, dry_run: bool = False):
    """Preloží celú 'legal' sekciu do cieľového jazyka."""
    lang_conf = LANGS[target_lang_code]
    target_file = MSG_DIR / lang_conf["file"]
    deepl_target = lang_conf["target"]

    print(f"\n{'=' * 60}")
    print(f"🌐 Preklad do {target_lang_code} ({target_file.name})")
    print(f"{'=' * 60}")

    # 1. Načítaj SK legal
    sk = json.loads(SK_JSON.read_text(encoding="utf-8"))
    sk_legal = sk.get("legal", {})
    print(f"📊 SK legal: {len(sk_legal)} kľúčov")

    # 2. Načítaj target
    if not target_file.exists():
        print(f"❌ {target_file} neexistuje")
        return

    target = json.loads(target_file.read_text(encoding="utf-8"))
    old_legal = target.get("legal", {})
    print(f"📊 {target_lang_code} legal (staré): {len(old_legal)} kľúčov")

    if dry_run:
        print(f"🔍 DRY RUN — {target_lang_code}: preložil by {len(sk_legal)} kľúčov")
        return

    # 3. Priprav kľúče a texty (zachovaj poradie!)
    keys = sorted(sk_legal.keys())
    texts = [sk_legal[k] for k in keys]

    # 4. Prelož v dávkach
    print(f"🔄 Prekladám {len(texts)} textov v dávkach po {BATCH_SIZE}...")
    translations = []
    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"   [{batch_num}/{total_batches}] {len(batch)} textov...")

        try:
            result = translate_batch(batch, deepl_target, api_key)
            translations.extend(result)
            time.sleep(SLEEP_BETWEEN)
        except Exception as e:
            print(f"   ❌ Zlyhal batch {batch_num}: {e}")
            print("   💾 Záloha existuje, môžeš spustiť znova")
            sys.exit(1)

    # 5. Skontroluj dĺžku
    if len(translations) != len(texts):
        print(f"❌ Nesúlad: {len(texts)} textov → {len(translations)} prekladov")
        sys.exit(1)

    # 6. Vytvor nový legal objekt
    new_legal = dict(zip(keys, translations, strict=True))

    # 7. Záloha
    backup = target_file.with_suffix(".json.bak4")
    shutil.copy(target_file, backup)
    print(f"💾 Záloha: {backup}")

    # 8. Zapíš
    target["legal"] = new_legal
    target_file.write_text(
        json.dumps(target, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"✅ {target_file.name}: {len(new_legal)} kľúčov")

    # 9. Validácia
    try:
        json.loads(target_file.read_text(encoding="utf-8"))
        print("✅ JSON validácia OK")
    except Exception as e:
        print(f"❌ JSON INVALID: {e}")
        shutil.copy(backup, target_file)
        print(f"↩️  Obnovené z {backup}")
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--lang", choices=list(LANGS.keys()), help="Preložiť len 1 jazyk")
    ap.add_argument("--all", action="store_true", help="Preložiť všetky 4 jazyky")
    args = ap.parse_args()

    # API kľúč
    api_key = os.getenv("DEEPL_API_KEY")
    if not api_key:
        print("❌ DEEPL_API_KEY nie je v prostredí", file=sys.stderr)
        print("   Spusti: set -a && source .env && set +a", file=sys.stderr)
        sys.exit(1)

    # Vyber jazyky
    if args.all:
        langs = list(LANGS.keys())
    elif args.lang:
        langs = [args.lang]
    else:
        print("Použi --lang EN|DE|FR|RU alebo --all")
        sys.exit(1)

    print(f"🔑 DeepL kľúč: ...{api_key[-6:]}")
    print(f"🌐 Jazyky: {', '.join(langs)}")
    if args.dry_run:
        print("🔍 DRY RUN MÓD")

    for lang in langs:
        translate_legal(lang, api_key, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
