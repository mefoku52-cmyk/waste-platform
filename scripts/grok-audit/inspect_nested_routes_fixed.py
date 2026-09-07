import sys
from pathlib import Path

project = Path.home() / "waste-platform"
sys.path.insert(0, str(project))

from app.main import create_app

app = create_app()

print("=== TOP LEVEL ROUTES ===")
for i, r in enumerate(app.routes, 1):
    cls = type(r).__name__
    path = getattr(r, "path", None)
    name = getattr(r, "name", None)
    methods = getattr(r, "methods", None)
    print(f"[{i}] {cls} path={path!r} name={name!r} methods={sorted(methods) if methods else None}")

print()
print("=== NESTED ROUTES ===")
for i, r in enumerate(app.routes, 1):
    nested = getattr(r, "routes", None)
    if not nested:
        continue
    print(f"[PARENT {i}] {type(r).__name__} nested_count={len(nested)}")
    for j, nr in enumerate(nested, 1):
        ncls = type(nr).__name__
        npath = getattr(nr, "path", None)
        nname = getattr(nr, "name", None)
        nmethods = getattr(nr, "methods", None)
        print(f"  [{j}] {ncls} path={npath!r} name={nname!r} methods={sorted(nmethods) if nmethods else None}")
