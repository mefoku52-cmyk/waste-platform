#!/usr/bin/env python3
"""
Incremental DeepL preklad — preloží LEN chýbajúce kľúče v EN/DE/FR/RU.
Existujúce preklady ponechá.

Použitie:
  set -a && source .env && set +a
  python3 scripts/deepl_incremental.py
"""

import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path.home() / "waste-platform"
MSG_DIR = ROOT / "apps" / "web" / "src" / "lib" / "i18n" / "messages"
SK_JSON = MSG_DIR / "sk.json"

LANGS = {
    "EN": {"file": "en.json", "target": "EN-GB"},
    "DE": {"file": "de.json", "target": "DE"},
    "FR": {"file": "fr.json", "target": "FR"},
    "RU": {"file": "ru.json", "target": "RU"},
}

BATCH_SIZE = 40
SLEEP_BETWEEN = 0.5
MAX_RETRIES = 3


def translate_batch(texts, target_lang, api_key):
    url = (
        "https://api-free.deepl.com/v2/translate"
        if api_key.endswith(":fx")
        else "https://api.deepl.com/v2/translate"
    )
    headers = {"Authorization": f"DeepL-Auth-Key {api_key}"}
    for attempt in range(MAX_RETRIES):
        try:
            data = [("text", t) for t in texts]
            data.append(("target_lang", target_lang))
            data.append(("source_lang", "SK"))
            data.append(("preserve_formatting", "1"))
            r = requests.post(url, headers=headers, data=data, timeout=60)
            if r.status_code == 200:
                return [t["text"] for t in r.json()["translations"]]
            elif r.status_code == 429:
                time.sleep(5 * (attempt + 1))
            else:
                print(f"   ❌ {r.status_code}: {r.text[:200]}")
                if attempt == MAX_RETRIES - 1:
                    sys.exit(1)
                time.sleep(2)
        except Exception:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2)
    return []


def main():
    api_key = os.getenv("DEEPL_API_KEY")
    if not api_key:
        print("❌ DEEPL_API_KEY nie je v prostredí")
        print("   Spusti: set -a && source .env && set +a")
        sys.exit(1)

    sk = json.loads(SK_JSON.read_text(encoding="utf-8"))["legal"]

    for lang_code, conf in LANGS.items():
        target_path = MSG_DIR / conf["file"]
        target = json.loads(target_path.read_text(encoding="utf-8"))
        legal = target.get("legal", {})

        # Nájdi chýbajúce kľúče
        missing = [k for k in sk.keys() if k not in legal]
        if not missing:
            print(f"✅ {lang_code}: všetko preložené ({len(legal)} kľúčov)")
            continue

        print(f"\n🌐 {lang_code}: chýba {len(missing)} kľúčov")

        keys = sorted(missing)
        texts = [sk[k] for k in keys]

        translations = []
        total = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]
            n = i // BATCH_SIZE + 1
            print(f"   [{n}/{total}] {len(batch)} textov...")
            translations.extend(translate_batch(batch, conf["target"], api_key))
            time.sleep(SLEEP_BETWEEN)

        if len(translations) != len(texts):
            print(f"❌ Nesúlad: {len(texts)} → {len(translations)}")
            sys.exit(1)

        for k, v in zip(keys, translations):
            legal[k] = v

        target["legal"] = legal
        target_path.write_text(
            json.dumps(target, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"✅ {lang_code}: +{len(keys)} kľúčov (spolu {len(legal)})")

    print("\n🎉 Hotovo")


if __name__ == "__main__":
    main()
