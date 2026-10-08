"""Voice gateway — free STT (Groq Whisper) + free TTS (edge-tts).

STT: Groq Whisper Large v3 Turbo (reuse existing GROQ_API_KEY).
TTS: Microsoft Edge TTS (no API key required, uses online Edge engine).

Both are server-side only. Frontend talks exclusively to our FastAPI.
"""

from __future__ import annotations

import base64
import io
import os

import httpx

# --- STT (Groq Whisper) ---
GROQ_STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_STT_MODEL = os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo")
AZURE_MAX_AUDIO_BYTES = 15 * 1024 * 1024  # 15 MB — same limit as before

# --- TTS (Edge) ---
ALLOWED_TTS_LANGUAGES = {"sk", "en", "de", "fr", "ru"}
DEFAULT_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", "sk-SK-LukasNeural")
# Mapovanie jazyka -> predvolený Edge hlas (ak user nešpecifikoval)
LANG_DEFAULT_VOICES = {
    "sk": "sk-SK-LukasNeural",
    "en": "en-US-GuyNeural",
    "de": "de-DE-ConradNeural",
    "fr": "fr-FR-HenriNeural",
    "ru": "ru-RU-DmitryNeural",
}


async def transcribe_with_mai(
    audio: bytes, filename: str, content_type: str
) -> dict[str, str | None]:
    """STT cez Groq Whisper (free tier, reuse GROQ_API_KEY)."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GROQ_API_KEY missing")

    files = {
        "file": (filename or "recording.webm", audio, content_type or "audio/webm"),
    }
    data = {
        "model": GROQ_STT_MODEL,
        "response_format": "verbose_json",
        "temperature": "0",
    }
    headers = {"Authorization": f"Bearer {key}"}

    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0)) as client:
        response = await client.post(GROQ_STT_URL, headers=headers, files=files, data=data)
        response.raise_for_status()
    payload = response.json()

    transcript = str(payload.get("text") or "").strip()
    language = payload.get("language")
    if not transcript:
        raise ValueError("No transcript returned")
    return {"text": transcript, "language": str(language) if language else None}


async def synthesize_with_telnyx(text: str, language: str | None) -> str:
    """TTS cez Microsoft Edge TTS (zdarma, bez API kľúča).

    Názov funkcie je ponechaný kvôli spätnej kompatibilite s chat_router.py.
    """
    try:
        import edge_tts  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("edge-tts not installed. Run: pip install edge-tts") from exc

    safe_text = (text or "").strip()
    if not safe_text:
        raise ValueError("Empty speech text")

    lang = (language or "sk").lower().split("-")[0]
    if lang not in ALLOWED_TTS_LANGUAGES:
        lang = "sk"
    voice = LANG_DEFAULT_VOICES.get(lang, DEFAULT_TTS_VOICE)

    communicate = edge_tts.Communicate(safe_text[:5000], voice)
    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio" and chunk.get("data"):
            buffer.write(chunk["data"])

    audio_bytes = buffer.getvalue()
    if not audio_bytes:
        raise ValueError("Edge TTS returned empty audio")
    return base64.b64encode(audio_bytes).decode("ascii")
