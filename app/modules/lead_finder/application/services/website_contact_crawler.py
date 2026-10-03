"""Crawler kontaktného emailu na firemnej stránke.

Nadväzuje na `directory_lookup`, ktorý vie z katalógovej karty získať
domovskú stránku firmy. Tento modul z tej stránky (a jej kontaktných
podstránok) vytiahne verejný firemný email.

Zásady:
- Používajú sa len verejne dostupné stránky.
- Rešpektuje sa robots.txt.
- Email sa prijme len ak súvisí s názvom firmy (`_email_matches_company`).
- Výsledky sa cachujú (Redis, s in-memory fallbackom).

Modul je celý synchronný (`httpx.get`, sync Redis), lebo nadväzuje na
`lookup_public_email`, ktorý beží pod `asyncio.to_thread`.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
import time
from urllib.parse import unquote, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.modules.lead_finder.application.services.directory_lookup import (
    _EMAIL_RE as _STRICT_EMAIL_RE,
)
from app.modules.lead_finder.application.services.directory_lookup import (
    _JUNK_EMAIL_MARKERS,
    _extract_joomla_cloak_email,
    _normalize_name,
)
from app.modules.lead_finder.application.services.email_finder import (
    _EMAIL_RE as _SCAN_EMAIL_RE,
)
from app.modules.lead_finder.application.services.email_finder import (
    _JUNK_PATTERNS,
    _email_matches_company,
    _is_free_email,
)

# --- Konfigurácia -------------------------------------------------------

# Identifikácia crawlera - stabilná, používa sa v robots.txt aj diagnostike.
_UA = "CMEP-LeadBot/1.0 (contact: trc-cmep@gmail.com)"

_FETCH_TIMEOUT = 8

# Slušnostná pauza medzi requestami na tú istú doménu.
_REQUEST_DELAY = 1.0

# Strop HTTP requestov na jednu doménu (chráni cudzie servery).
_MAX_PAGES_PER_DOMAIN = 4

# Kontakty sa menia málo -> dlhý TTL. robots.txt sa mení -> kratší.
_EMAIL_CACHE_TTL = 2592000  # 30 dní
_ROBOTS_CACHE_TTL = 86400  # 24h

_EMAIL_CACHE_PREFIX = "waste:contacts:v1:"
_ROBOTS_CACHE_PREFIX = "waste:robots:v1:"

# Sentinel: definitívny miss (stránka sa načítala, ale email nemala).
_MISS_SENTINEL = "__cmep_miss__"
_ROBOTS_NONE_SENTINEL = "__cmep_no_robots__"

logger = logging.getLogger(__name__)

# In-memory fallback, ak Redis nie je dostupný.
# Hodnota: (expires_at_epoch, value)
_MEMORY_CACHE: dict[str, tuple[float, str]] = {}

# Po prvom zlyhaní Redisu už neskúšame ping pri každom volaní.
_REDIS_DISABLED = False


def _get_redis():
    """Vráti synchronného Redis klienta alebo None.

    Pri akomkoľvek probléme (chýbajúci balík, nedostupný server,
    zlyhaný ping) sa ticho prepne na in-memory fallback, aby crawler
    fungoval aj bez Redisu.
    """
    global _REDIS_DISABLED

    if _REDIS_DISABLED:
        return None

    try:
        import redis

        url = getattr(settings.redis, "url", None) or (
            f"redis://{getattr(settings.redis, 'host', 'localhost')}:"
            f"{getattr(settings.redis, 'port', 6379)}/0"
        )

        client = redis.from_url(url, decode_responses=True)
        client.ping()

        return client
    except Exception:
        _REDIS_DISABLED = True
        return None


def _cache_get(key: str) -> str | None:
    """Prečítaj hodnotu z cache. Vráti None ak chýba alebo expirovala."""
    client = _get_redis()

    if client is not None:
        try:
            return client.get(key)
        except Exception:
            pass

    entry = _MEMORY_CACHE.get(key)

    if entry is None:
        return None

    expires_at, value = entry

    if expires_at < time.time():
        _MEMORY_CACHE.pop(key, None)
        return None

    return value


def _cache_set(key: str, value: str, ttl: int = _EMAIL_CACHE_TTL) -> None:
    """Ulož hodnotu do cache s TTL."""
    client = _get_redis()

    if client is not None:
        try:
            client.set(key, value, ex=ttl)
            return
        except Exception:
            pass

    _MEMORY_CACHE[key] = (time.time() + ttl, value)


# --- Extrakcia emailov --------------------------------------------------

# Obfuskacie typu "info (at) firma (dot) sk".
_OBFUSCATION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\s*[\(\[\{]\s*at\s*[\)\]\}]\s*", re.I), "@"),
    (re.compile(r"\s*[\(\[\{]\s*dot\s*[\)\]\}]\s*", re.I), "."),
    (re.compile(r"\s*[\(\[\{]\s*@\s*[\)\]\}]\s*", re.I), "@"),
)

# Hole " at " / " dot " - len medzi alfanumerickymi znakmi,
# aby sa nerozbili bezne slova vo vete.
_BARE_AT_RE = re.compile(r"(?<=[a-zA-Z0-9])\s+at\s+(?=[a-zA-Z0-9])", re.I)
_BARE_DOT_RE = re.compile(r"(?<=[a-zA-Z0-9])\s+dot\s+(?=[a-zA-Z0-9])", re.I)


def _dedupe_emails(candidates: list[str]) -> list[str]:
    """Znormalizuj, validuj a deduplikuj kandidatske emaily."""
    seen: set[str] = set()
    result: list[str] = []

    for candidate in candidates:
        email = str(candidate or "").strip().strip(".,;:'\"<>").lower()

        if not email or email in seen:
            continue

        if not _STRICT_EMAIL_RE.fullmatch(email):
            continue

        seen.add(email)
        result.append(email)

    return result


def _extract_emails_from_html(html: str) -> list[str]:
    """Vytiahne vsetky kandidatske emaily z HTML stranky.

    Pokryva: mailto: odkazy (URL-decoded), plaintext, obfuskacie
    a Joomla cloak. Vrateny zoznam je deduplikovany a lowercase.
    """
    if not html:
        return []

    found: list[str] = []

    soup = BeautifulSoup(html, "html.parser")

    # 1) mailto: hrefs - niektore stranky escapuju '@' ako %40.
    for anchor in soup.select('a[href^="mailto:"]'):
        href = str(anchor.get("href") or "")
        raw = href[len("mailto:") :].split("?", 1)[0]

        candidate = unquote(raw).strip()
        if candidate:
            found.append(candidate)

    # 2) Viditelny text stranky + obfuskacie.
    text = unquote(soup.get_text(" ", strip=True))

    for pattern, replacement in _OBFUSCATION_PATTERNS:
        text = pattern.sub(replacement, text)

    text = _BARE_AT_RE.sub("@", text)
    text = _BARE_DOT_RE.sub(".", text)

    found.extend(_SCAN_EMAIL_RE.findall(text))

    # 3) Surove HTML (entity typu &#64; v atributoch).
    found.extend(_SCAN_EMAIL_RE.findall(unquote(html)))

    # 4) Joomla cloak - reuse, ziadna duplikacia.
    cloaked = _extract_joomla_cloak_email(html)
    if cloaked:
        found.append(cloaked)

    return _dedupe_emails(found)


def _extract_json_ld_email(html: str) -> list[str]:
    """Vytiahne emaily z blokov <script type="application/ld+json">."""
    if not html:
        return []

    found: list[str] = []
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        payload = tag.string or tag.get_text()

        if not payload:
            continue

        try:
            data = json.loads(payload)
        except Exception:
            # Jeden zly JSON blok nesmie zhodit cely crawl.
            continue

        _collect_emails_from_json(data, found)

    return _dedupe_emails(found)


def _collect_emails_from_json(node, out: list[str]) -> None:
    """Rekurzivne najdi kluc 'email' v lubovolnom JSON strukture."""
    if isinstance(node, dict):
        for key, value in node.items():
            if str(key).lower() == "email" and isinstance(value, str):
                out.append(value.strip().removeprefix("mailto:").strip())
            else:
                _collect_emails_from_json(value, out)
        return

    if isinstance(node, list):
        for item in node:
            _collect_emails_from_json(item, out)


# --- Validacia ----------------------------------------------------------


def _normalize_domain(value: str) -> str:
    """Z 'https://www.Firma.sk/kontakt' sprav 'firma.sk'."""
    text = str(value or "").strip().lower()

    if not text:
        return ""

    text = re.sub(r"^[a-z][a-z0-9+.\-]*://", "", text)
    text = text.split("/", 1)[0]
    text = text.rsplit("@", 1)[-1]
    text = text.split(":", 1)[0]

    if text.startswith("www."):
        text = text[4:]

    return text


def _local_part_matches_company(local: str, company_name: str) -> bool:
    """Free-provider adresa je prijatelna len vtedy, ked jej local-part
    obsahuje aspon 3 znaky z normalizovaneho nazvu firmy.

    Priklad: 'ekolpresov@gmail.com' pre 'EKOL - recyklacne systemy'
             -> 'ekol' je v 'ekolpresov' -> True
             'jan.novak@gmail.com' -> False
    """
    normalized = _normalize_name(company_name)

    if not normalized:
        return False

    tokens = [token for token in normalized.split() if len(token) >= 3]

    if not tokens:
        return False

    compact_local = re.sub(r"[^a-z0-9]+", "", local)

    # 1) Token z nazvu firmy sa nachadza v local-part.
    if any(token in compact_local for token in tokens):
        return True

    # 2) Local-part (>=3 znaky) je obsiahnuty v nazve firmy.
    compact_name = normalized.replace(" ", "")

    return len(compact_local) >= 3 and compact_local in compact_name


def _is_valid_email(
    email: str,
    company_name: str,
    page_domain: str = "",
) -> bool:
    """Rozhodni, ci email patri firme na danej stranke.

    D1: rovnaka domena (alebo subdomena) ako stranka -> OK.
    D2: free provider -> len ak local-part sedi s nazvom firmy.
    Inak: name-match fallback (`_email_matches_company`).
    Vzdy: smetne adresy sa odmietaju.
    """
    candidate = str(email or "").strip().lower()

    if not candidate or "@" not in candidate:
        return False

    if not _STRICT_EMAIL_RE.fullmatch(candidate):
        return False

    # Vzdy odmietni smetne adresy (markery aj patterny).
    if any(marker in candidate for marker in _JUNK_EMAIL_MARKERS):
        return False

    if any(pattern in candidate for pattern in _JUNK_PATTERNS):
        return False

    local, _, domain = candidate.partition("@")
    page = _normalize_domain(page_domain)

    # D1: najsilnejsi signal - firma pouziva vlastnu domenu stranky.
    if page and (domain == page or domain.endswith("." + page)):
        return True

    # D2: free provider - nutny suhlas local-part s nazvom firmy.
    if _is_free_email(candidate):
        return _local_part_matches_company(local, company_name)

    # Ina firemna domena -> name-match fallback.
    return _email_matches_company(candidate, company_name)


# --- Fetch + orchestration ----------------------------------------------

# Stav crawl-u pre aktuálne vlákno. Crawler beží pod `asyncio.to_thread`,
# takže modulová premenná by sa medzi vláknami bilovala.
_CRAWL_STATE = threading.local()


def _reset_crawl_state() -> None:
    _CRAWL_STATE.saw_html = False


def _hash_key(prefix: str, origin: str) -> str:
    """Stabilný cache kľúč pre daný origin."""
    digest = hashlib.sha256(origin.encode("utf-8")).hexdigest()

    return f"{prefix}{digest}"


def _normalize_origin(website_url: str) -> str | None:
    """Z 'https://www.Firma.sk/kontakt?a=1' sprav 'https://firma.sk'.

    Schéma sa zachováva (http aj https). Cesta, query, fragment, port
    a userinfo sa odstraňujú, prefix 'www.' sa strháva. Ak vstup nemá
    schému, predpokladá sa 'https://'. Pri neparsovateľnom vstupe None.
    """
    text = str(website_url or "").strip()

    if not text:
        return None

    if "://" not in text:
        text = "https://" + text

    try:
        parsed = urlparse(text)
        scheme = (parsed.scheme or "").lower()
        host = (parsed.hostname or "").lower()
    except Exception:
        return None

    if scheme not in ("http", "https"):
        return None

    if not host:
        return None

    if host.startswith("www."):
        host = host[4:]

    # Bez bodky to nie je verejná doména - nemá zmysel crawlovať.
    if "." not in host:
        return None

    return f"{scheme}://{host}"


def _parse_robots(text: str) -> RobotFileParser | None:
    """Naparsuj robots.txt. Pri chybe fail-open (None = všetko povolené)."""
    parser = RobotFileParser()

    try:
        parser.parse(str(text).splitlines())
    except Exception:
        return None

    return parser


def _check_robots(origin: str) -> RobotFileParser | None:
    """Vráť naparsovaný robots.txt pre origin, alebo None.

    None znamená "všetko povolené" (fail-open). Cache drží len stabilné
    odpovede (200 text, 404 = žiadny robots). Sietové zlyhania sa
    necachujú, aby výpadok siete nezamkol "allow all" na 24h.
    """
    key = _hash_key(_ROBOTS_CACHE_PREFIX, origin)
    cached = _cache_get(key)

    if cached == _ROBOTS_NONE_SENTINEL:
        logger.debug("robots cache hit (none): %s", origin)
        return None

    if cached is not None:
        logger.debug("robots cache hit (text): %s", origin)
        return _parse_robots(cached)

    robots_url = f"{origin}/robots.txt"

    try:
        response = httpx.get(
            robots_url,
            headers={"User-Agent": _UA, "Accept": "text/plain"},
            timeout=_FETCH_TIMEOUT,
            follow_redirects=True,
        )
    except Exception as exc:
        logger.warning("robots transient failure %s: %s", origin, exc)
        return None

    if response.status_code == 404:
        _cache_set(key, _ROBOTS_NONE_SENTINEL, _ROBOTS_CACHE_TTL)
        return None

    if response.status_code != 200:
        logger.warning(
            "robots unexpected status %s for %s",
            response.status_code,
            origin,
        )
        return None

    text = response.text or ""
    _cache_set(key, text, _ROBOTS_CACHE_TTL)

    return _parse_robots(text)


def _fetch_page(url: str, origin: str) -> str | None:
    """Stiahni HTML stránku, ktorá nesmie opustiť pôvodný origin.

    None pri: sietovom zlyhaní, non-200 statuse, ne-HTML content-type,
    alebo ak redirect skončil na inej doméne (parked domain / hijack).
    """
    try:
        response = httpx.get(
            url,
            headers={
                "User-Agent": _UA,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "sk-SK,sk;q=0.9,cs;q=0.8,en;q=0.5",
            },
            timeout=_FETCH_TIMEOUT,
            follow_redirects=True,
        )
    except Exception as exc:
        logger.warning("fetch transient failure %s: %s", url, exc)
        return None

    if response.status_code != 200:
        return None

    # Redirect na inú doménu môže byť parked domain alebo hijack.
    final_domain = _normalize_domain(str(response.url))
    origin_domain = _normalize_domain(origin)

    if final_domain and origin_domain and final_domain != origin_domain:
        logger.warning("redirect left origin: %s -> %s", url, response.url)
        return None

    content_type = (response.headers.get("content-type") or "").lower()

    # Pokrýva 'text/html' aj 'application/xhtml+xml'.
    if "html" not in content_type:
        return None

    return response.text


def _should_visit(url: str, origin: str) -> bool:
    """Smieme podľa robots.txt stiahnuť túto URL? Fail-open pri chybe."""
    parser = _check_robots(origin)

    if parser is None:
        return True

    try:
        return parser.can_fetch(_UA, url)
    except Exception:
        return True


def _try_path(
    path: str,
    origin: str,
    company_name: str,
) -> tuple[str | None, str | None, bool]:
    """Skús jednu cestu na doméne.

    Vráť (email, source_url, fetched). `fetched` je True len ak sa
    stránka naozaj stiahla (200 + HTML) - vtedy má zmysel hovoriť
    o "definitívnom miss". Robots disallow a sietové zlyhania dávajú
    fetched=False, teda sa počítajú ako transient.
    """
    url = f"{origin}{path}"

    if not _should_visit(url, origin):
        logger.warning("robots disallow, skip: %s", url)
        return (None, None, False)

    html = _fetch_page(url, origin)

    if html is None:
        return (None, None, False)

    candidates = _extract_emails_from_html(html)
    candidates.extend(_extract_json_ld_email(html))

    page_domain = _normalize_domain(url)

    for email in _dedupe_emails(candidates):
        if _is_valid_email(email, company_name, page_domain):
            logger.info("email found: %s (%s)", page_domain, url)
            return (email, url, True)

    return (None, None, True)


# Primárne kontaktné cesty. Varianty sa skúšajú len ak niektorá
# z primárnych zlyhala na sieti.
_PRIMARY_PATHS: tuple[str, ...] = ("/", "/kontakt", "/kontakt/", "/o-nas")
_VARIANT_PATHS: tuple[str, ...] = ("/o-nás", "/kontakty", "/kontaktujte-nas")


def _crawl_paths(origin: str, company_name: str) -> tuple[str | None, str | None]:
    """Prejdi kontaktné cesty na doméne a vráť prvý platný email.

    Strop `_MAX_PAGES_PER_DOMAIN` stiahnutí na doménu (robots.txt sa
    počíta zvlášť, je cachovaný na 24h). Medzi requestami je pauza,
    aby sme cudzí server nezaťažili.
    """
    requests_made = 0
    network_failed = False
    saw_html = False
    hit: tuple[str | None, str | None] = (None, None)

    def _walk(paths: tuple[str, ...]) -> bool:
        """Prejdi zoznam ciest. True ak sme našli email (v `hit`)."""
        nonlocal requests_made, network_failed, saw_html, hit

        for path in paths:
            if requests_made >= _MAX_PAGES_PER_DOMAIN:
                return False

            # Pauza medzi requestami na tej istej doméne.
            if requests_made > 0:
                time.sleep(_REQUEST_DELAY)

            requests_made += 1
            email, source_url, fetched = _try_path(path, origin, company_name)

            if email:
                hit = (email, source_url)
                return True

            if fetched:
                saw_html = True
            else:
                network_failed = True

        return False

    if not _walk(_PRIMARY_PATHS):
        # Varianty len vtedy, ak niektorá primárna cesta zlyhala na
        # sieti (nie keď vrátila HTML bez emailu).
        if network_failed:
            _walk(_VARIANT_PATHS)

    _CRAWL_STATE.saw_html = saw_html

    return hit


def crawl_contact_email(
    website_url: str,
    company_name: str,
) -> tuple[str | None, str | None]:
    """Nájdi verejný kontaktný email na firemnej stránke.

    Vráť (email, source_url). Pri neplatnom vstupe alebo definitívnom
    miss vráť (None, None).

    Cache: úspech aj definitívny miss sa držia 30 dní. Transientné
    sietové zlyhania sa necachujú, aby výpadok nezablokoval nález.
    """
    origin = _normalize_origin(website_url)

    if origin is None:
        logger.debug("invalid website url, skip: %r", website_url)
        return (None, None)

    if not company_name or not company_name.strip():
        return (None, None)

    key = _hash_key(_EMAIL_CACHE_PREFIX, origin)
    cached = _cache_get(key)

    if cached == _MISS_SENTINEL:
        logger.debug("cache hit (definitive miss): %s", origin)
        return (None, None)

    if cached is not None:
        try:
            payload = json.loads(cached)
        except Exception:
            payload = None

        if isinstance(payload, dict) and payload.get("email"):
            logger.debug("cache hit (email): %s", origin)
            return (payload["email"], payload.get("source_url"))

    _reset_crawl_state()

    email, source_url = _crawl_paths(origin, company_name)

    if email:
        _cache_set(
            key,
            json.dumps({"email": email, "source_url": source_url}),
            _EMAIL_CACHE_TTL,
        )
        return (email, source_url)

    # Definítívny miss = aspoň jedna stránka sa načítala bez emailu.
    # Ak všetko zlyhalo na sieti alebo to zakázal robots, je to
    # transient a necachujeme.
    if getattr(_CRAWL_STATE, "saw_html", False):
        _cache_set(key, _MISS_SENTINEL, _EMAIL_CACHE_TTL)
    else:
        logger.warning("transient crawl failure, not caching: %s", origin)

    return (None, None)
