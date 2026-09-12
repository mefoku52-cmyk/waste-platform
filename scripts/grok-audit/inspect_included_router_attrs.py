import sys
from pathlib import Path

project = Path.home() / "waste-platform"
sys.path.insert(0, str(project))

from app.main import create_app

app = create_app()

print("=== INCLUDED ROUTER ATTRIBUTES ===")
for i, r in enumerate(app.routes, 1):
    cls = type(r).__name__
    if cls != "_IncludedRouter":
        continue

    print(f"[{i}] CLASS={cls}")
    names = [n for n in dir(r) if not n.startswith("__")]
    print("ATTRS:", ", ".join(names))

    for key in ["router", "_router", "app", "_app", "path", "prefix", "name", "routes"]:
        if hasattr(r, key):
            try:
                value = getattr(r, key)
                print(
                    f"  {key} -> type={type(value).__name__} repr={repr(value)[:300]}"
                )
            except Exception as e:
                print(f"  {key} -> ERROR {e!r}")

    print()
