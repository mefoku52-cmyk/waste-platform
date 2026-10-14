#!/usr/bin/env python3
"""Incremental preklad landing.* kľúčov do EN/DE/FR/RU."""

import json
import os
import sys
import time
from pathlib import Path

import requests

MSG = Path.home() / "waste-platform" / "apps" / "web" / "src" / "lib" / "i18n" / "messages"
SK = MSG / "sk.json"
LANGS = {
    "EN": ("en.json", "EN-GB"),
    "DE": ("de.json", "DE"),
    "FR": ("fr.json", "FR"),
    "RU": ("ru.json", "RU"),
}


def translate_batch(texts, target, key):
    url = (
        "https://api-free.deepl.com/v2/translate"
        if key.endswith(":fx")
        else "https://api.deepl.com/v2/translate"
    )
    r = requests.post(
        url,
        headers={"Authorization": f"DeepL-Auth-Key {key}"},
        data=[("text", t) for t in texts]
        + [("target_lang", target), ("source_lang", "SK"), ("preserve_formatting", "1")],
        timeout=60,
    )
    if r.status_code == 200:
        return [t["text"] for t in r.json()["translations"]]
    print(f"❌ {r.status_code}: {r.text[:200]}")
    sys.exit(1)


def main():
    key = os.getenv("DEEPL_API_KEY")
    if not key:
        print("❌ DEEPL_API_KEY chýba")
        sys.exit(1)

    sk = json.loads(SK.read_text(encoding="utf-8")).get("landing", {})
    for code, (fname, target) in LANGS.items():
        p = MSG / fname
        data = json.loads(p.read_text(encoding="utf-8"))
        lp = data.setdefault("landing", {})
        missing = [k for k in sk if k not in lp]
        if not missing:
            print(f"✅ {code}: OK ({len(lp)} kľúčov)")
            continue
        print(f"🌐 {code}: +{len(missing)} kľúčov")
        keys = sorted(missing)
        vals = [sk[k] for k in keys]
        translated = []
        for i in range(0, len(vals), 40):
            translated.extend(translate_batch(vals[i : i + 40], target, key))
            time.sleep(0.5)
        for k, v in zip(keys, translated):
            lp[k] = v
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"✅ {code}: {len(translated)} preložených")


if __name__ == "__main__":
    main()
