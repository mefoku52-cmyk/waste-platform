# DDG search migration: 8.x/9.x → 5.3.1

**Date:** 2026-10-04
**Component:** `app/modules/lead_finder/application/services/website_finder.py`
**Status:** applied

## Problem

`duckduckgo-search 8.1.1` (and `ddgs 9.16.0`) depend on `primp 2.0.1`, which
crashes on Python 3.14 (Termux and local venv, probably also on Render):

```
_Py_NoneStruct  (undefined symbol / ABI failure in primp native extension)
```

The crash happens at import time, so the whole website discovery path was
unusable on Python 3.14.

## Solution

Pin `duckduckgo-search==5.3.1`, which uses `curl-cffi` instead of `primp`
and imports cleanly on Python 3.14.

Verified dependencies of 5.3.1:

- `curl-cffi >=0.7.0b4`
- `orjson >=3.10.3`
- `click >=8.1.7`
- optional: `lxml >=5.2.1` (`backend='html'` / `'lite'`)

No `primp` anywhere in the dependency tree.

## Verified 5.3.1 signatures

```python
DDGS.__init__(self, headers=None, proxy=None, proxies=None, timeout=10)
DDGS.text(keywords, region, safesearch, timelimit, backend="api", max_results=None)
```

Notes:

- `timeout` **is** supported in `__init__` → `DDGS(timeout=20.0)` stays valid.
- Default backend is `api`, which needs no `lxml`.
- `DDGS.text()` accepts `*args, **kwargs` and delegates to the async
  implementation, so the 8.x call style (`ddgs.text(query, max_results=10)`)
  works unchanged.

## Response format

Identical to 8.x, per backend implementation:

```json
{"title": "...", "href": "...", "body": "..."}
```

`href` is a final URL. `_score_result` and the `href` extraction logic in
`website_finder.py` required no changes.

## Changes made

- `requirements.txt`, `app/requirements.txt`:
  `duckduckgo-search>=6.0.0,<8.0.0` → `duckduckgo-search==5.3.1`
- `website_finder.py`: removed the `"ddgs"` import preference, now only
  `"duckduckgo_search"` is imported (2 places: `is_available`, `_search`).
- `_decode_url` kept as a defensive no-op: 5.3.1 returns final URLs, but the
  decoder still unwraps `uddg`/`url`/`target` query wrappers if a provider
  ever returns them.

## Dropped

- `primp` (native extension crashes on Python 3.14)
- `ddgs` package / module name (9.x line, primp-based)

## Production constraint (Render)

Render runs on AWS datacenter IPs. DuckDuckGo detects those and stops
answering — the request either times out or comes back rate-limited:

```
DuckDuckGoSearchException: https://duckduckgo.com Timed out
curl: (28) Connection timed out after 10000 milliseconds
```

**Consequence:** `WebsiteFinder.find_website()` returns `None` in
production. Website discovery does not work there. The public directory
(Zlaté stránky) is the primary email source; directory-only yield is
roughly 31 % (~10-12 emails per run of 35 companies).

To get 30+ emails/day, one of these is required:

- **SerpAPI** — ~$75/month (Developer plan) for 5 000 queries, works from
  cloud IPs (cenník overený 2026-10-04; starší údaj $50/5K už neplatí)
- **Brave Search API** — metered, ~$5/month free credits (~1 000 queries)
- **Google Programmable Search (CSE)** — 100 queries/day free, needs a
  billing-enabled Google Cloud project
- **self-hosted SearXNG** — free, but needs custom Docker on Render

### Timeout guard

Because a dead DDG costs `timeout` seconds per query (13 queries per
company × 35 companies ≈ minutes of pure waste), `website_finder.py`
keeps a module-level circuit breaker:

- `_ddg_disabled` — set to `True` on the first DDG failure
- `_search()` checks the flag and returns `[]` immediately when tripped
- `find_website()` checks the flag before building the query list
- first failure logs `WARNING`, later ones log `DEBUG`

Callers (`backfill_emails.py`, `daily_discover.py`) already treat
`None`/no-email as "directory only" and continue — no crash, no invented
email addresses.

**This is not a permanent fix.** It makes a broken DDG cheap instead of
expensive. Swap in a cloud-capable provider above to restore website
discovery.

## Validation

`pytest tests/unit -q --no-cov` → 660 passed, 1 xfailed
(654 pred pridaním 6 breaker testov v
`tests/unit/test_website_finder_ddg_breaker.py`).
