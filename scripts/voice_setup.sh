#!/usr/bin/env bash
set -Eeuo pipefail

# Run from the local waste-platform repository in Termux.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "Chyba: spusti tento skript z priečinka waste-platform (git repozitár)." >&2
  exit 1
}
cd "$ROOT"

BRANCH="feat/voice-mai-transcribe-telnyx"
TARGETS=(
  "app/modules/agent_platform/presentation/chat_router.py"
  "app/shared/presentation/api_router.py"
  "apps/web/src/features/agent-platform/components/ai-chat-widget.tsx"
  "app/modules/agent_platform/presentation/voice_router.py"
  "app/modules/agent_platform/infrastructure/ai/voice_gateway.py"
)

for f in "${TARGETS[@]:0:3}"; do
  if ! git ls-files --error-unmatch "$f" >/dev/null 2>&1; then
    echo "Chyba: v repozitári sa nenašiel očakávaný súbor: $f" >&2
    exit 1
  fi
  if ! git diff --quiet -- "$f"; then
    echo "Chyba: cieľový súbor už má lokálne zmeny: $f" >&2
    echo "Nič som nezmenil. Najprv tieto zmeny ulož alebo skontroluj." >&2
    exit 1
  fi
done
if [[ -e "${TARGETS[3]}" || -e "${TARGETS[4]}" ]]; then
  echo "Chyba: jeden z nových hlasových súborov už existuje. Nič som nezmenil." >&2
  exit 1
fi
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  echo "Chyba: vetva $BRANCH už existuje; nič som nezmenil." >&2
  exit 1
fi

# Presunie iba aktuálnu pracovnú pozíciu na novú vetvu. Už existujúce
# necieľové zmeny zostanú v pracovnom strome a nebudú zaradené do commitu.
git switch -c "$BRANCH"

python3 - <<'PY'
from pathlib import Path

chat_path = Path("app/modules/agent_platform/presentation/chat_router.py")
api_path = Path("app/shared/presentation/api_router.py")
widget_path = Path("apps/web/src/features/agent-platform/components/ai-chat-widget.tsx")

chat = chat_path.read_text()
api = api_path.read_text()
widget = widget_path.read_text()

# Check every required insertion point before changing any existing file.
checks = [
    (chat, "from app.modules.agent_platform.application.memory.context_builder import build_history\n", "chat import"),
    (chat, "    page_context: dict | None = None\n\n\nclass ClientAction", "chat request model"),
    (chat, "    client_actions: list[ClientAction] = []\n\n\nasync def _check_ai_entitlement", "chat response model"),
    (chat, "    return UserAiChatResponse(\n        status=\"ok\",\n        reply=result_text,\n        source=\"groq\",\n        session_id=session_id,\n        tool_calls=server_tool_calls,\n        client_actions=client_actions,\n    )", "final chat response"),
    (api, "from app.modules.agent_platform.presentation.chat_router import router as agent_platform_chat_router\n", "API router import"),
    (api, "api_router.include_router(agent_platform_chat_router)\n", "API router registration"),
    (widget, "import { useEffect, useRef, useState } from 'react';\n", "React imports"),
    (widget, "import { http } from '@/lib/api/http';\n", "frontend HTTP import"),
    (widget, "type Msg = { role: 'user' | 'ai'; text: string };", "message type"),
    (widget, "  client_actions?: ClientAction[];\n};", "chat response type"),
    (widget, "  const bottomRef = useRef<HTMLDivElement | null>(null);", "widget refs"),
    (widget, "  async function send() {\n    const text = input.trim();", "send function"),
    (widget, "        page_context: pageCtx,\n      });", "chat request body"),
    (widget, "            { role: 'ai', text: res.reply as string || '' },", "client-action reply"),
    (widget, "          setMessages((m) => [...m, { role: 'ai', text: res.reply as string }]);", "plain chat reply"),
    (widget, "                {m.text}\n              </div>", "message render"),
    (widget, "            {busy && (\n", "busy render"),
    (widget, "              <button\n                type=\"button\"\n                onClick={() => void send()}", "send button"),
    (widget, "  function onKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {", "key handler"),
]
for text, needle, label in checks:
    if needle not in text:
        raise SystemExit(f"Chyba: neočakávaný obsah ({label}); nič som nezapísal.")

# New provider gateway: all provider credentials remain server-side.
gateway = '''from __future__ import annotations

import base64
import json
import os

import httpx

AZURE_API_VERSION = "2025-10-15"
AZURE_MAX_AUDIO_BYTES = 15 * 1024 * 1024
TELNYX_TTS_URL = "https://api.telnyx.com/v2/text-to-speech/speech"
ALLOWED_TTS_LANGUAGES = {"sk", "en", "de", "fr", "ru"}


async def transcribe_with_mai(audio: bytes, filename: str, content_type: str) -> dict[str, str | None]:
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
        (str(item.get("locale")) for item in (data.get("phrases") or [])
         if isinstance(item, dict) and item.get("locale")),
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
'''

voice_router = '''from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.modules.agent_platform.infrastructure.ai.voice_gateway import (
    AZURE_MAX_AUDIO_BYTES,
    transcribe_with_mai,
)
from app.modules.agent_platform.presentation.chat_router import _check_ai_entitlement
from app.modules.agent_platform.presentation.dependencies import get_company_entitlement_service
from app.modules.companies.application.entitlements import CompanyEntitlementService
from app.shared.presentation.auth_dependencies import require_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent-platform/voice", tags=["agent-platform-voice"])


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    current_user=Depends(require_current_user),
    entitlements: CompanyEntitlementService = Depends(get_company_entitlement_service),
) -> dict[str, str | None]:
    # Same logged-in user and AI subscription entitlement as the existing chat.
    await _check_ai_entitlement(current_user=current_user, entitlements=entitlements)
    content_type = (audio.content_type or "").lower()
    if not (content_type.startswith("audio/") or content_type in {"application/octet-stream", "video/webm"}):
        raise HTTPException(status_code=415, detail="Nepodporovaný audio formát.")
    content = await audio.read(AZURE_MAX_AUDIO_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="Nahrávka je prázdna.")
    if len(content) > AZURE_MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Nahrávka je príliš veľká (limit 15 MB).")
    try:
        return await transcribe_with_mai(
            content,
            audio.filename or "recording.webm",
            content_type or "audio/webm",
        )
    except Exception as exc:
        logger.exception("Voice transcription provider request failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=502, detail="Prepis hlasu sa nepodaril. Skús to znova.") from exc
'''

# Existing backend changes are exact, limited edits.
chat = chat.replace(
    "from app.modules.agent_platform.application.memory.context_builder import build_history\n",
    "from app.modules.agent_platform.application.memory.context_builder import build_history\nfrom app.modules.agent_platform.infrastructure.ai.voice_gateway import synthesize_with_telnyx\n",
    1,
)
chat = chat.replace(
    "    page_context: dict | None = None\n\n\nclass ClientAction",
    "    page_context: dict | None = None\n    voice_response: bool = False\n    voice_language: str | None = Field(default=None, max_length=16)\n\n\nclass ClientAction",
    1,
)
chat = chat.replace(
    "    client_actions: list[ClientAction] = []\n\n\nasync def _check_ai_entitlement",
    "    client_actions: list[ClientAction] = []\n    audio_base64: str | None = None\n\n\nasync def _check_ai_entitlement",
    1,
)
final_return = '''    audio_base64 = None
    if payload.voice_response and result_text.strip():
        try:
            # Only the response generated/assembled by this authenticated chat request is synthesized.
            audio_base64 = await synthesize_with_telnyx(result_text, payload.voice_language)
        except Exception as exc:
            import logging as _log
            _log.getLogger("cmep.chat").warning(
                "VOICE_TTS_FAILED type=%s", type(exc).__name__
            )

    return UserAiChatResponse(
        status="ok",
        reply=result_text,
        source="groq",
        session_id=session_id,
        tool_calls=server_tool_calls,
        client_actions=client_actions,
        audio_base64=audio_base64,
    )'''
chat = chat.replace(
    checks[3][1],
    final_return,
    1,
)

api = api.replace(
    "from app.modules.agent_platform.presentation.chat_router import router as agent_platform_chat_router\n",
    "from app.modules.agent_platform.presentation.chat_router import router as agent_platform_chat_router\nfrom app.modules.agent_platform.presentation.voice_router import router as agent_platform_voice_router\n",
    1,
)
api = api.replace(
    "api_router.include_router(agent_platform_chat_router)\n",
    "api_router.include_router(agent_platform_chat_router)\napi_router.include_router(agent_platform_voice_router)\n",
    1,
)

# Frontend: microphone -> authenticated STT -> existing chat request with optional server-side TTS.
widget = widget.replace(
    "import { useEffect, useRef, useState } from 'react';\n",
    "import { useEffect, useRef, useState } from 'react';\nimport { config } from '@/lib/config';\nimport { tokenStore } from '@/lib/auth/token-store';\n",
    1,
)
widget = widget.replace(
    "type Msg = { role: 'user' | 'ai'; text: string };",
    "type Msg = { role: 'user' | 'ai'; text: string; audioBase64?: string };",
    1,
)
widget = widget.replace(
    "  client_actions?: ClientAction[];\n};",
    "  client_actions?: ClientAction[];\n  audio_base64?: string | null;\n};",
    1,
)
widget = widget.replace(
    "  const [busy, setBusy] = useState(false);\n",
    "  const [busy, setBusy] = useState(false);\n  const [recording, setRecording] = useState(false);\n  const [transcribing, setTranscribing] = useState(false);\n",
    1,
)
widget = widget.replace(
    "  const bottomRef = useRef<HTMLDivElement | null>(null);",
    "  const bottomRef = useRef<HTMLDivElement | null>(null);\n  const recorderRef = useRef<MediaRecorder | null>(null);\n  const chunksRef = useRef<BlobPart[]>([]);",
    1,
)
widget = widget.replace(
    "  async function send() {\n    const text = input.trim();",
    "  async function send(textOverride?: string, voiceResponse = false, voiceLanguage?: string) {\n    const text = (textOverride ?? input).trim();",
    1,
)
widget = widget.replace(
    "        page_context: pageCtx,\n      });",
    "        page_context: pageCtx,\n        voice_response: voiceResponse,\n        voice_language: voiceLanguage,\n      });",
    1,
)
widget = widget.replace(
    "            { role: 'ai', text: res.reply as string || '' },",
    "            { role: 'ai', text: res.reply as string || '', audioBase64: res.audio_base64 || undefined },",
    1,
)
widget = widget.replace(
    "          setMessages((m) => [...m, { role: 'ai', text: res.reply as string }]);",
    "          setMessages((m) => [...m, { role: 'ai', text: res.reply as string, audioBase64: res.audio_base64 || undefined }]);",
    1,
)
widget = widget.replace(
    "        setMessages((m) => [...m, { role: 'ai', text: res.reply as string }]);",
    "        setMessages((m) => [...m, { role: 'ai', text: res.reply as string, audioBase64: res.audio_base64 || undefined }]);",
    1,
)
widget = widget.replace(
    "        setMessages((m) => [...m, { role: 'ai', text: res.reply as string }]);",
    "        setMessages((m) => [...m, { role: 'ai', text: res.reply as string, audioBase64: res.audio_base64 || undefined }]);",
    1,
)
widget = widget.replace(
    "                {m.text}\n              </div>",
    "                {m.text}\n                {m.audioBase64 && (\n                  <audio className=\"mt-2 block w-full\" controls preload=\"none\" src={`data:audio/mpeg;base64,${m.audioBase64}`} />\n                )}\n              </div>",
    1,
)
widget = widget.replace(
    "            {busy && (\n",
    "            {(busy || transcribing) && (\n",
    1,
)
widget = widget.replace(
    "                píšem…",
    "                {transcribing ? 'Prepisujem hlas…' : 'píšem…'}",
    1,
)

voice_function = '''  async function toggleVoiceRecording() {
    if (recorderRef.current?.state === 'recording') {
      recorderRef.current.stop();
      return;
    }
    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setMessages((m) => [...m, { role: 'ai', text: 'Tento prehliadač nepodporuje nahrávanie hlasu.' }]);
      return;
    }

    let stream: MediaStream | undefined;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const preferred = 'audio/webm;codecs=opus';
      const mimeType = MediaRecorder.isTypeSupported(preferred) ? preferred : undefined;
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        stream?.getTracks().forEach((track) => track.stop());
        setRecording(false);
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' });
        void (async () => {
          if (!blob.size) return;
          setTranscribing(true);
          try {
            const token = tokenStore.getToken();
            if (!token) throw new Error('Prihlásenie vypršalo. Prihlás sa znova.');
            const form = new FormData();
            form.append('audio', blob, 'recording.webm');
            const response = await fetch(`${config.apiBaseUrl}/agent-platform/voice/transcribe`, {
              method: 'POST',
              headers: { Authorization: `Bearer ${token}` },
              body: form,
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(data.detail || 'Prepis hlasu sa nepodaril.');
            if (!data.text) throw new Error('V nahrávke sa nenašla reč.');
            setInput(data.text);
            await send(data.text, true, data.language || undefined);
          } catch (error: unknown) {
            const message = error instanceof Error ? error.message : 'Prepis hlasu sa nepodaril.';
            setMessages((m) => [...m, { role: 'ai', text: `Chyba: ${message}` }]);
          } finally {
            setTranscribing(false);
          }
        })();
      };
      recorderRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch (error: unknown) {
      stream?.getTracks().forEach((track) => track.stop());
      const message = error instanceof Error ? error.message : 'Mikrofón sa nepodarilo spustiť.';
      setMessages((m) => [...m, { role: 'ai', text: `Mikrofón: ${message}` }]);
    }
  }

'''
widget = widget.replace(
    "  function onKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {",
    voice_function + "  function onKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {",
    1,
)
widget = widget.replace(
    "                disabled={busy}\n                className=\"flex-1 resize-none rounded-lg border p-2 text-sm\"",
    "                disabled={busy || transcribing}\n                className=\"flex-1 resize-none rounded-lg border p-2 text-sm\"",
    1,
)
widget = widget.replace(
    "              <button\n                type=\"button\"\n                onClick={() => void send()}\n",
    '''              <button
                type="button"
                onClick={() => void toggleVoiceRecording()}
                disabled={busy || transcribing}
                aria-label={recording ? 'Zastaviť nahrávanie' : 'Nahrať hlasovú správu'}
                aria-pressed={recording}
                className="rounded-lg border px-3 py-2 text-sm disabled:opacity-40"
                style={{ borderColor: recording ? '#ef4444' : 'rgba(201,168,76,0.35)', color: recording ? '#ef4444' : '#c9a84c' }}
              >
                {recording ? '■' : '🎙'}
              </button>
              <button
                type="button"
                onClick={() => void send()}
''',
    1,
)

# Ensure all required replacements occurred before writing.
for text, needle, label in [
    (chat, "audio_base64=audio_base64,", "chat audio response"),
    (api, "api_router.include_router(agent_platform_voice_router)", "voice router registration"),
    (widget, "async function toggleVoiceRecording()", "microphone handler"),
    (widget, "audioBase64: res.audio_base64 || undefined", "audio playback state"),
    (widget, "Nahrať hlasovú správu", "microphone button"),
]:
    if needle not in text:
        raise SystemExit(f"Chyba: úprava neprešla kontrolou ({label}); nič som nezapísal.")

# Write only after validating all target anchors.
Path("app/modules/agent_platform/infrastructure/ai/voice_gateway.py").write_text(gateway)
Path("app/modules/agent_platform/presentation/voice_router.py").write_text(voice_router)
chat_path.write_text(chat)
api_path.write_text(api)
widget_path.write_text(widget)
print("Vytvorené hlasové backend súbory a upravený chat widget.")
PY

# Static checks first; no commit or push if any check fails.
python3 -m compileall -q \
  app/modules/agent_platform/infrastructure/ai/voice_gateway.py \
  app/modules/agent_platform/presentation/voice_router.py \
  app/modules/agent_platform/presentation/chat_router.py \
  app/shared/presentation/api_router.py

git diff --check

# Run frontend typecheck when dependencies are already installed. On a clean
# Termux checkout without node_modules, report the skip; backend compilation
# and diff checks still run, and CI can perform the full frontend check.
if [[ -x apps/web/node_modules/.bin/tsc ]]; then
  pnpm --dir apps/web exec tsc --noEmit
else
  echo "Upozornenie: apps/web/node_modules/.bin/tsc chýba; frontend typecheck preskočený." >&2
fi

# Stage only these five paths. Existing docs/PLATFORM_MAP.html, MD.md, main
# and every other unrelated local change are deliberately left out.
git add \
  app/modules/agent_platform/infrastructure/ai/voice_gateway.py \
  app/modules/agent_platform/presentation/voice_router.py \
  app/modules/agent_platform/presentation/chat_router.py \
  app/shared/presentation/api_router.py \
  apps/web/src/features/agent-platform/components/ai-chat-widget.tsx

git commit -m "feat(agent-platform): add multilingual voice chat"
git push -u origin "$BRANCH"

echo
echo "Hotovo: zmeny sú na vetve $BRANCH (nie priamo na main)."
echo "Nastav v Render backend env: AZURE_SPEECH_ENDPOINT, AZURE_SPEECH_KEY, TELNYX_API_KEY."
echo "Voliteľne nastav TELNYX_TTS_VOICE (predvolené Telnyx.Ultra.Asher)."
echo "Produkciu nenasadzuj, kým neskontroluješ vetvu a Render deploy nastavenia."
