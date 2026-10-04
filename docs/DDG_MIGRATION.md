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

## Validation

`pytest tests/unit -q --no-cov` → 654 passed, 1 xfailed.
