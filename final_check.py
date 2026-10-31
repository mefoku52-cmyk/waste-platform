import os, re, ast, subprocess, time

REPO = os.path.expanduser("~/waste-platform")
BR = "app/modules/agent_platform/navigator/navigator_bridge.py"
SKIP = {"node_modules", ".next", ".git", "__pycache__"}

def git_raw(*a):
    r = subprocess.run(["git"] + list(a), cwd=REPO, capture_output=True, text=True)
    return r.stdout + r.stderr

def short(s, n=100):
    s = s.rstrip()
    return s if len(s) <= n else s[: n - 3] + "..."

if not os.path.isdir(os.path.join(REPO, ".git")):
    raise SystemExit("REPOZITAR NENAJDENY: " + REPO)

print("== 1. navigator_bridge.py: je oprava stale v subore?")
p = os.path.join(REPO, BR)
if not os.path.isfile(p):
    print("SUBOR NENAJDENY")
else:
    txt = open(p, encoding="utf-8", errors="replace").read()
    try:
        tree = ast.parse(txt)
        print("syntax pracovneho suboru: OK")
        n_pages = None
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "NAV_PAGES" for t in node.targets):
                n_pages = len(node.value.keys) if isinstance(node.value, ast.Dict) else "?"
        print("pocet stranok v NAV_PAGES:", n_pages if n_pages is not None else "NAV_PAGES NENAJDENE")
    except SyntaxError as exc:
        print("syntax pracovneho suboru: CHYBA", str(exc)[:120])
    for name in ("def build_nav_prompt", "def nav_reply", "ai_prompt = build_nav_prompt(user_message)"):
        print("  pracovny subor obsahuje", name, ":", "ANO" if name in txt else "NIE")
    staged = git_raw("show", ":" + BR)
    head = git_raw("show", "HEAD:" + BR)
    print("  index ma NAV_PAGES:", "ANO" if "NAV_PAGES" in staged else "NIE", "| HEAD ma NAV_PAGES:", "ANO" if "NAV_PAGES" in head else "NIE")
    print("  riadkov: pracovny", len(txt.splitlines()), "| index", len(staged.splitlines()), "| HEAD", len(head.splitlines()))

print("== 2. zmenene subory a kedy sa naposledy menili")
now = time.time()
for line in git_raw("status", "--short").splitlines():
    code, path = line[:2], line[3:].strip()
    fp = os.path.join(REPO, path)
    if os.path.isfile(fp):
        print(code, path, "| zmeneny pred", int((now - os.path.getmtime(fp)) / 60), "min")
    else:
        print(code, path)
print("-- git diff --stat (pracovny adresar oproti indexu):")
for l in git_raw("diff", "--stat").splitlines()[:12]:
    print(short(l))

print("== 3. zalohove adresare v repozitari")
found = []
for d, dirs, files in os.walk(REPO):
    dirs[:] = [x for x in dirs if x not in SKIP]
    depth = d[len(REPO):].count(os.sep)
    for x in list(dirs):
        if "backup" in x.lower():
            found.append(os.path.relpath(os.path.join(d, x), REPO))
    if depth >= 3:
        dirs[:] = []
print("\n".join(found[:10]) or "ZIADNE")
tracked = [l for l in git_raw("ls-files").splitlines() if "backup" in l.lower()]
print("sledovanych suborov s 'backup' v ceste:", len(tracked))
for l in tracked[:3]:
    print("  ", short(l))

print("== 4. pre-commit konfiguracia")
cfg = os.path.join(REPO, ".pre-commit-config.yaml")
if os.path.isfile(cfg):
    L = open(cfg, encoding="utf-8", errors="replace").read().splitlines()
    ids = [re.search(r"id:\s*(\S+)", l).group(1) for l in L if re.search(r"^\s*-?\s*id:\s*\S+", l)]
    print("hooky:", ", ".join(ids))
    for i, l in enumerate(L):
        if re.search(r"id:\s*ty\b", l):
            for x in L[max(0, i - 1): i + 10]:
                print("  " + short(x))
            break
else:
    print(".pre-commit-config.yaml NENAJDENY")

print("== 5. bezi iny AI nastroj nad repozitarom?")
r = subprocess.run(["ps", "-ef"], capture_output=True, text=True)
hits = [l for l in (r.stdout or "").splitlines() if re.search(r"opencode|aider|codex|gemini|deepseek|claude", l, re.I) and "final_check" not in l]
print("\n".join(short(l, 110) for l in hits[:8]) or "ZIADNY ZNAMY AI NASTROJ NEBEZI")
