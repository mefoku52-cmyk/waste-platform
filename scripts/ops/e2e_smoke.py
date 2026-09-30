import urllib.error, urllib.request
BASES = ["https://waste-platform.onrender.com", "https://trc-cmep.sk"]
def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=25) as r:
            return r.status, r.read()[:200]
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:200]
    except Exception as e:
        return 0, str(e).encode()
failed = 0
print("E2E SMOKE read-only")
for base in BASES:
    for path in ("/health", "/login", "/register"):
        url = base + path
        code, _ = get(url)
        ok = code in (200, 301, 302, 307, 308)
        print(("OK" if ok else "FAIL"), code, url)
        failed += 0 if ok else 1
print("MANUAL: register -> login -> firma -> listing -> dopyt -> chat")
raise SystemExit(1 if failed else 0)
