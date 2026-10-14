from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("apps/web/src/lib/i18n/messages")

PATCHES = {
    "sk": {
        "common": {"close": "Zavrieť"},
        "dashboard": {"subline": "Prehľad trhu, aktívnych ponúk a kontaktov na jednom mieste."},
        "chat": {"loadError": "Konverzácie sa nepodarilo načítať.", "sending": "Odosielam…"},
        "inquiries": {
            "section": "DOPYTY",
            "title": "Dopyty",
            "received": "Prijaté",
            "sent": "Odoslané",
        },
        "listingMedia": {
            "noPhoto": "Bez fotografie",
            "gallery": "Fotogaléria",
            "openPhoto": "Otvoriť fotografiu",
            "companySection": "Firma",
            "acceptedMaterials": "Akceptované materiály",
        },
    },
    "en": {
        "common": {"close": "Close"},
        "dashboard": {
            "subline": "An overview of the market, active listings and contacts in one place."
        },
        "chat": {"loadError": "Conversations could not be loaded.", "sending": "Sending…"},
        "inquiries": {
            "section": "INQUIRIES",
            "title": "Inquiries",
            "received": "Received",
            "sent": "Sent",
        },
        "listingMedia": {
            "noPhoto": "No photo",
            "gallery": "Photo gallery",
            "openPhoto": "Open photo",
            "companySection": "Company",
            "acceptedMaterials": "Accepted materials",
        },
    },
    "ru": {
        "common": {"close": "Закрыть"},
        "dashboard": {"subline": "Обзор рынка, активных предложений и контактов в одном месте."},
        "chat": {"loadError": "Не удалось загрузить диалоги.", "sending": "Отправка…"},
        "inquiries": {
            "section": "ЗАПРОСЫ",
            "title": "Запросы",
            "received": "Полученные",
            "sent": "Отправленные",
        },
        "listingMedia": {
            "noPhoto": "Без фотографии",
            "gallery": "Фотогалерея",
            "openPhoto": "Открыть фотографию",
            "companySection": "Компания",
            "acceptedMaterials": "Принимаемые материалы",
        },
    },
    "fr": {
        "common": {"close": "Fermer"},
        "dashboard": {
            "subline": "Une vue d’ensemble du marché, des annonces actives et des contacts."
        },
        "chat": {"loadError": "Impossible de charger les conversations.", "sending": "Envoi…"},
        "inquiries": {
            "section": "DEMANDES",
            "title": "Demandes",
            "received": "Reçues",
            "sent": "Envoyées",
        },
        "listingMedia": {
            "noPhoto": "Aucune photo",
            "gallery": "Galerie photos",
            "openPhoto": "Ouvrir la photo",
            "companySection": "Entreprise",
            "acceptedMaterials": "Matériaux acceptés",
        },
    },
    "de": {
        "common": {"close": "Schließen"},
        "dashboard": {"subline": "Markt, aktive Angebote und Kontakte auf einen Blick."},
        "chat": {
            "loadError": "Unterhaltungen konnten nicht geladen werden.",
            "sending": "Wird gesendet…",
        },
        "inquiries": {
            "section": "ANFRAGEN",
            "title": "Anfragen",
            "received": "Eingegangen",
            "sent": "Gesendet",
        },
        "listingMedia": {
            "noPhoto": "Kein Foto",
            "gallery": "Fotogalerie",
            "openPhoto": "Foto öffnen",
            "companySection": "Unternehmen",
            "acceptedMaterials": "Akzeptierte Materialien",
        },
    },
}


def merge(target: dict, patch: dict) -> None:
    for key, value in patch.items():
        if isinstance(value, dict):
            current = target.get(key)
            if not isinstance(current, dict):
                current = {}
                target[key] = current
            merge(current, value)
        else:
            target[key] = value


for locale, patch in PATCHES.items():
    path = ROOT / (locale + ".json")

    if not path.exists():
        raise SystemExit("MISSING LOCALE: " + str(path))

    data = json.loads(path.read_text(encoding="utf-8"))
    merge(data, patch)

    rendered = json.dumps(data, ensure_ascii=False, indent=2)
    path.write_text(rendered + chr(10), encoding="utf-8")
    print("UPDATED", path)
