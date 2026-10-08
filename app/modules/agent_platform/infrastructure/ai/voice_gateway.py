from __future__ import annotations

import base64
import json
import os

import httpx

AZURE_API_VERSION = "2025-10-15"
AZURE_MAX_AUDIO_BYTES = 15 * 1024 * 1024
TELNYX_TTS_URL = "https://api.telnyx.com/v2/text-to-speech/speech"
ALLOWED_TTS_LANGUAGES = {"sk", "en", "de", "fr", "ru"}


async def transcribe_with_mai(
    audio: bytes, filename: str, content_type: str
) -> dict[str, str | None]:
    key = os.getenv("AZURE_SPEECH_KEY", "").strip()
    endpoint = os.getenv("AZURE_SPEECH_ENDPOINT", "").strip().rstrip("/")
    if not key or not endpoint:
        raise RuntimeError("MAI speech configuration is missing")
    if not endpoint.startswith("https://"):
        raise RuntimeError("AZURE_SPEECH_ENDPOINT must use HTTPS")

    url = f"{endpoint}/speechtotext/transcriptions:transcribe?api-version={AZURE_API_VERSION}"
    definition = {
        "enhancedMode": {
            "enabled": True,
            "model": "MAI-Transcribe-2",
            "task": "transcribe",
        },
        "locales": [],
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0)) as client:
        response = await client.post(
            url,
            headers={"Ocp-Apim-Subscription-Key": key},
            data={"definition": json.dumps(definition)},
            files={"audio": (filename or "recording.webm", audio, content_type or "audio/webm")},
        )
        response.raise_for_status()
    data = response.json()
    phrases = data.get("combinedPhrases") or []
    transcript = " ".join(
        str(item.get("text", "")).strip()
        for item in phrases
        if isinstance(item, dict) and item.get("text")
    ).strip()
    if not transcript:
        transcript = " ".join(
            str(item.get("text", "")).strip()
            for item in (data.get("phrases") or [])
            if isinstance(item, dict) and item.get("text")
        ).strip()
    language = next(
        (
            str(item.get("locale"))
            for item in (data.get("phrases") or [])
            if isinstance(item, dict) and item.get("locale")
        ),
        None,
    )
    if not transcript:
        raise ValueError("No transcript returned")
    return {"text": transcript, "language": language}


async def synthesize_with_telnyx(text: str, language: str | None) -> str:
    key = os.getenv("TELNYX_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Telnyx configuration is missing")
    safe_text = text.strip()
    if not safe_text:
        raise ValueError("Empty speech text")

    lang = (language or "").lower().split("-")[0]
    voice_settings = {"language_boost": lang} if lang in ALLOWED_TTS_LANGUAGES else {}
    payload: dict[str, object] = {
        "text": safe_text[:5000],
        "voice": os.getenv("TELNYX_TTS_VOICE", "Telnyx.Ultra.Asher").strip(),
        "output_type": "binary_output",
    }
    if voice_settings:
        payload["voice_settings"] = voice_settings

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        response = await client.post(
            TELNYX_TTS_URL,
            headers={"Authorization": f"Bearer {key}"},
            json=payload,
        )
        response.raise_for_status()
    if not response.content:
        raise ValueError("Telnyx returned empty audio")
    return base64.b64encode(response.content).decode("ascii")
